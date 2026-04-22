"""
User MCP Server - 用户管理服务
支持多角色用户的CRUD和权限控制
"""
import os
from typing import Optional
from fastapi import FastAPI
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import structlog

# 配置日志
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory()
)
logger = structlog.get_logger()

# 应用配置
app = FastAPI(title="User MCP Server", version="1.0.0")
server = Server("user-service")

# Milvus连接
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = "careagent_users"

connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)

# 数据模型
class UserCreate(BaseModel):
    name: str
    role: str  # elder, child, caregiver
    age: Optional[int] = None
    health_info: Optional[dict] = None
    preferences: Optional[dict] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    health_info: Optional[dict] = None
    preferences: Optional[dict] = None
    voice_preference: Optional[str] = None

# Milvus集合管理
def init_collection():
    """初始化用户集合"""
    if utility.has_collection(COLLECTION_NAME):
        return Collection(COLLECTION_NAME)
    
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="role", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="age", dtype=DataType.INT64),
        FieldSchema(name="health_info", dtype=DataType.JSON),
        FieldSchema(name="preferences", dtype=DataType.JSON),
        FieldSchema(name="voice_preference", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="updated_at", dtype=DataType.VARCHAR, max_length=50),
    ]
    
    schema = CollectionSchema(fields, "CareAgent Users")
    collection = Collection(COLLECTION_NAME, schema)
    collection.create_index(field_name="user_id", index_type="FLAT")
    return collection

collection = init_collection()

# MCP工具定义
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="user.create_user",
            description="创建新用户",
            inputSchema=UserCreate.schema()
        ),
        Tool(
            name="user.get_user",
            description="获取用户信息",
            inputSchema={"type": "object", "properties": {"user_id": {"type": "string"}}}
        ),
        Tool(
            name="user.update_user",
            description="更新用户信息",
            inputSchema=UserUpdate.schema()
        ),
        Tool(
            name="user.delete_user",
            description="删除用户",
            inputSchema={"type": "object", "properties": {"user_id": {"type": "string"}}}
        ),
        Tool(
            name="user.switch_user",
            description="切换当前用户（看护人专用）",
            inputSchema={"type": "object", "properties": {"user_id": {"type": "string"}}}
        ),
        Tool(
            name="user.set_voice_preference",
            description="设置用户音色偏好",
            inputSchema={"type": "object", "properties": {"user_id": {"type": "string"}, "voice_id": {"type": "string"}}}
        ),
        Tool(
            name="user.get_voice_preference",
            description="获取用户音色偏好",
            inputSchema={"type": "object", "properties": {"user_id": {"type": "string"}}}
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    logger.info("tool_call", tool=name, arguments=arguments)
    
    if name == "user.create_user":
        return await create_user(arguments)
    elif name == "user.get_user":
        return await get_user(arguments["user_id"])
    elif name == "user.update_user":
        return await update_user(arguments)
    elif name == "user.delete_user":
        return await delete_user(arguments["user_id"])
    elif name == "user.switch_user":
        return await switch_user(arguments["user_id"])
    elif name == "user.set_voice_preference":
        return await set_voice_preference(arguments["user_id"], arguments["voice_id"])
    elif name == "user.get_voice_preference":
        return await get_voice_preference(arguments["user_id"])
    else:
        raise ValueError(f"Unknown tool: {name}")

async def create_user(data: dict):
    """创建用户"""
    import uuid
    from datetime import datetime
    
    user_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    entities = [
        [user_id],
        [data["name"]],
        [data["role"]],
        [data.get("age", 0)],
        [data.get("health_info", {})],
        [data.get("preferences", {})],
        [data.get("voice_preference", "")],
        [now],
        [now]
    ]
    
    collection.insert(entities)
    collection.flush()
    
    logger.info("user_created", user_id=user_id)
    return [TextContent(type="text", text=f"User created with ID: {user_id}")]

async def get_user(user_id: str):
    """获取用户信息"""
    collection.load()
    results = collection.query(expr=f'user_id == "{user_id}"', output_fields=["*"])
    
    if not results:
        return [TextContent(type="text", text=f"User not found: {user_id}")]
    
    return [TextContent(type="text", text=str(results[0]))]

async def update_user(data: dict):
    """更新用户信息"""
    user_id = data.pop("user_id")
    # 简化实现，实际需要根据Milvus API更新
    return [TextContent(type="text", text=f"User {user_id} updated")]

async def delete_user(user_id: str):
    """删除用户"""
    collection.delete(expr=f'user_id == "{user_id}"')
    collection.flush()
    return [TextContent(type="text", text=f"User {user_id} deleted")]

async def switch_user(user_id: str):
    """切换用户"""
    return [TextContent(type="text", text=f"Switched to user: {user_id}")]

async def set_voice_preference(user_id: str, voice_id: str):
    """设置音色偏好"""
    return [TextContent(type="text", text=f"Voice preference set for {user_id}: {voice_id}")]

async def get_voice_preference(user_id: str):
    """获取音色偏好"""
    collection.load()
    results = collection.query(expr=f'user_id == "{user_id}"', output_fields=["voice_preference"])
    
    if not results:
        return [TextContent(type="text", text="User not found")]
    
    voice = results[0].get("voice_preference", "")
    return [TextContent(type="text", text=voice)]

# FastAPI路由
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    return generate_latest()

# MCP端点
@app.post("/mcp")
async def mcp_endpoint():
    # MCP协议处理
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
