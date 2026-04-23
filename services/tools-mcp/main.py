"""
Tools MCP Server - 工具服务
提供Web搜索和地址查询能力
"""
import os
from typing import Literal
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
import requests
import structlog
import json

structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()

app = FastAPI(title="Tools MCP Server", version="1.0.0")
mcp = FastMCP("tools-mcp")

# ============================================
# 配置
# ============================================

# TAVILY配置
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# AMAP配置
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"

# ============================================
# MCP Tools - 使用 FastMCP 装饰器
# ============================================

@mcp.tool(name="tools.web_search")
async def web_search(
    query: str,
    max_results: int = 5
) -> str:
    """
    互联网信息搜索：使用TAVILY API搜索实时信息
    
    Args:
        query: 搜索关键词
        max_results: 最大结果数量，默认5
    """
    logger.info("tool_call", tool="tools.web_search", query=query)
    
    if not query:
        raise ValueError("搜索关键词不能为空")
    
    if not tavily_client:
        return f"[模拟搜索] TAVILY API未配置，返回模拟结果"
    
    try:
        # 调用TAVILY API
        response = tavily_client.search(
            query=query,
            max_results=max_results
        )
        
        # 格式化结果
        results = []
        for result in response.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0)
            })
        
        result_text = json.dumps(results, ensure_ascii=False, indent=2)
        logger.info("web_search_completed", query=query, results_count=len(results))
        
        return result_text
        
    except Exception as e:
        logger.error("web_search_error", error=str(e))
        return f"搜索失败: {str(e)}"

@mcp.tool(name="tools.location_query")
async def location_query(
    address: str,
    query_type: Literal["geocode", "weather", "nearby"] = "geocode"
) -> str:
    """
    地址信息查询：使用高德地图API查询地理位置、天气等信息
    
    Args:
        address: 地址或地名
        query_type: 查询类型（geocode/weather/nearby）
    """
    logger.info("tool_call", tool="tools.location_query", address=address, query_type=query_type)
    
    if not address:
        raise ValueError("地址不能为空")
    
    if not AMAP_API_KEY:
        return f"[模拟查询] AMAP API未配置，返回模拟结果"
    
    try:
        if query_type == "geocode":
            result = await geocode_address(address)
        elif query_type == "weather":
            result = await get_weather(address)
        else:
            result = {"error": f"不支持的查询类型: {query_type}"}
        
        result_text = json.dumps(result, ensure_ascii=False, indent=2)
        logger.info("location_query_completed", address=address, query_type=query_type)
        
        return result_text
        
    except Exception as e:
        logger.error("location_query_error", error=str(e))
        return f"查询失败: {str(e)}"

# ============================================
# 辅助函数
# ============================================

async def geocode_address(address: str) -> dict:
    """
    地理编码 - 将地址转换为经纬度
    
    Args:
        address: 地址
    
    Returns:
        包含经纬度的信息
    """
    params = {
        "key": AMAP_API_KEY,
        "address": address,
        "output": "json"
    }
    
    response = requests.get(AMAP_GEOCODE_URL, params=params, timeout=10)
    data = response.json()
    
    if data.get("status") == "1" and data.get("count") != "0":
        location = data["geocodes"][0]
        return {
            "address": location.get("formatted_address", address),
            "province": location.get("province", ""),
            "city": location.get("city", ""),
            "district": location.get("district", ""),
            "location": location.get("location", ""),  # 经纬度 "lng,lat"
            "level": location.get("level", "")
        }
    else:
        return {"error": "未找到该地址", "address": address}


async def get_weather(address: str) -> dict:
    """
    查询天气
    
    Args:
        address: 地址
    
    Returns:
        天气信息
    """
    # 先获取城市编码
    geocode = await geocode_address(address)
    
    if "error" in geocode:
        return geocode
    
    # 提取城市
    city = geocode.get("city", "")
    if not city:
        return {"error": "无法确定城市"}
    
    params = {
        "key": AMAP_API_KEY,
        "city": city,
        "extensions": "base",  # base=实况天气, all=预报天气
        "output": "json"
    }
    
    response = requests.get(AMAP_WEATHER_URL, params=params, timeout=10)
    data = response.json()
    
    if data.get("status") == "1" and data.get("lives"):
        weather = data["lives"][0]
        return {
            "city": weather.get("city", ""),
            "weather": weather.get("weather", ""),
            "temperature": weather.get("temperature", ""),
            "wind_direction": weather.get("winddirection", ""),
            "wind_power": weather.get("windpower", ""),
            "humidity": weather.get("humidity", ""),
            "report_time": weather.get("reporttime", "")
        }
    else:
        return {"error": "天气查询失败", "address": address}

# ============================================
# FastAPI端点
# ============================================

app = FastAPI(title="Tools MCP Server", version="1.0.0")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "tools-mcp",
        "tavily_configured": tavily_client is not None,
        "amap_configured": bool(AMAP_API_KEY)
    }

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    return generate_latest()

# 挂载 FastMCP 到 FastAPI
mcp_app = mcp.streamable_http_app()
app.mount("/mcp", mcp_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
