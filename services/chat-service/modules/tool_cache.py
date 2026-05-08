"""
工具列表缓存管理
从 MCP Gateway 获取可用工具列表，缓存并定时刷新
"""
import os
import time
import httpx
from typing import List, Dict
import structlog

logger = structlog.get_logger()


class ToolCache:
    """工具列表缓存管理器"""

    def __init__(self, refresh_interval: int = 300):
        """
        初始化缓存

        Args:
            refresh_interval: 刷新间隔（秒），默认 5 分钟
        """
        self.tools_list: List[Dict] = []  # 工具信息列表
        self.tools_map: Dict[str, Dict] = {}  # tool_id → 工具信息
        self.last_updated: float = 0
        self.refresh_interval = refresh_interval
        self._gateway_url = os.getenv("MCP_GATEWAY_URL", "http://gateway:4444/mcp")

    async def get_tools(self) -> List[str]:
        """
        获取可用工具名称列表（向后兼容）

        Returns:
            工具名称列表，如 ["tools.web_search", "tools.location_query"]
        """
        now = time.time()
        if now - self.last_updated >= self.refresh_interval:
            await self.refresh()
        return [t["name"] for t in self.tools_list]

    async def get_tools_info(self) -> List[Dict]:
        """
        获取完整工具信息列表

        Returns:
            工具信息列表，每项包含 tool_id, name, description, inputSchema, request_url
        """
        now = time.time()
        if now - self.last_updated >= self.refresh_interval:
            await self.refresh()
        return self.tools_list

    async def get_tool_by_id(self, tool_id: str) -> Dict | None:
        """
        根据 tool_id 获取工具信息

        Args:
            tool_id: 工具 ID

        Returns:
            工具信息字典，不存在时返回 None
        """
        now = time.time()
        if now - self.last_updated >= self.refresh_interval:
            await self.refresh()
        return self.tools_map.get(tool_id)

    async def refresh(self):
        """从 MCP Gateway 刷新工具列表"""
        try:
            logger.info("tool_cache_refresh_start")

            # MCP 协议的 tools/list 请求
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(self._gateway_url, json=payload)
                response.raise_for_status()
                result = response.json()

            # 解析工具列表
            tools_list = []
            tools_map = {}

            for tool in result.get("result", {}).get("tools", []):
                tool_name = tool.get("name", "")
                input_schema = tool.get("inputSchema", {})

                tool_info = {
                    "name": tool_name,
                    "description": tool.get("description", ""),
                    "inputSchema": input_schema,
                    "parameters": input_schema.get("properties", {}),
                    "required_params": input_schema.get("required", []),
                    "request_url": self._gateway_url
                }

                tools_list.append(tool_info)
                tools_map[tool_name] = tool_info

            # 更新缓存
            self.tools_list = tools_list
            self.tools_map = tools_map
            self.last_updated = time.time()

            logger.info(
                "tool_cache_refresh_success",
                tools_count=len(tools_list),
                tools=[t["name"] for t in tools_list]
            )

        except Exception as e:
            logger.error(
                "tool_cache_refresh_failed",
                error=str(e)
            )
            # 保留旧缓存，不中断服务
            if not self.tools_list:
                # 如果从未获取过，使用默认工具列表
                default_tools = [
                    {
                        "tool_id": "web_search",
                        "name": "tools.web_search",
                        "description": "网络搜索工具",
                        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
                        "parameters": {"query": {"type": "string"}},
                        "required_params": ["query"],
                        "request_url": self._gateway_url
                    },
                    {
                        "tool_id": "location_query",
                        "name": "tools.location_query",
                        "description": "位置查询工具",
                        "inputSchema": {"type": "object", "properties": {"location": {"type": "string"}, "city": {"type": "string"}}, "required": ["location"]},
                        "parameters": {"location": {"type": "string"}, "city": {"type": "string"}},
                        "required_params": ["location"],
                        "request_url": self._gateway_url
                    }
                ]
                self.tools_list = default_tools
                self.tools_map = {t["tool_id"]: t for t in default_tools}
                self.last_updated = time.time()
                logger.warning("tool_cache_using_defaults", tools=[t["name"] for t in default_tools])


# 全局实例
tool_cache = ToolCache(refresh_interval=300)  # 5 分钟


async def periodic_tool_refresh():
    """后台定时刷新工具缓存（每 5 分钟）"""
    import asyncio

    while True:
        await asyncio.sleep(300)  # 5 分钟
        await tool_cache.refresh()
