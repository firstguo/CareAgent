"""  
User MCP Server - 用户管理服务
支持多角色用户的CRUD和权限控制
"""
import os
import time
from typing import Optional
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from motor.motor_asyncio import AsyncIOMotorClient
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
mcp = FastMCP("user-service")

# MongoDB连接配置
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:admin123@mongodb:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "careagent")
COLLECTION_NAME = "users"

# 全局变量
mongo_client: Optional[AsyncIOMotorClient] = None
db = None
collection = None

def connect_to_mongodb(max_retries=30, retry_interval=2):
    """连接到MongoDB，带重试机制"""
    global mongo_client, db, collection
    
    for attempt in range(max_retries):
        try:
            logger.info("mongodb_connect_attempt", attempt=attempt+1, uri=MONGODB_URI)
            mongo_client = AsyncIOMotorClient(MONGODB_URI)
            db = mongo_client[MONGODB_DB_NAME]
            collection = db[COLLECTION_NAME]
            logger.info("mongodb_connected")
            return True
        except Exception as e:
            logger.warning("mongodb_connect_failed", attempt=attempt+1, error=str(e))
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                logger.error("mongodb_connect_exhausted", max_retries=max_retries)
                raise
    return False

async def init_collection():
    """初始化用户集合，创建索引"""
    # 创建 user_id 唯一索引
    await collection.create_index("user_id", unique=True)
    logger.info("mongodb_indexes_created")

# ============================================
# FastAPI路由
# ============================================

app = FastAPI(title="User MCP Server", version="1.0.0")

@app.on_event("startup")
async def startup():
    """启动时连接MongoDB并初始化集合"""
    global collection
    
    # 连接MongoDB（带重试）
    connect_to_mongodb()
    
    # 初始化集合和索引
    await init_collection()
    logger.info("user_service_started")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    return generate_latest()

# ============================================
# MCP Tools - 使用 FastMCP 装饰器
# ============================================

@mcp.tool(name="user.create_user")
async def create_user(
    name: str,
    role: str,
    age: int = 0,
    health_info: Optional[dict] = None,
    preferences: Optional[dict] = None,
    voice_preference: str = ""
) -> str:
    """创建新用户"""
    import uuid
    from datetime import datetime
    
    logger.info("tool_call", tool="user.create_user", name=name, role=role)
    
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    user_doc = {
        "user_id": user_id,
        "name": name,
        "role": role,
        "age": age,
        "health_info": health_info or {},
        "preferences": preferences or {},
        "voice_preference": voice_preference,
        "created_at": now,
        "updated_at": now
    }
    
    await collection.insert_one(user_doc)
    
    logger.info("user_created", user_id=user_id)
    return f"User created with ID: {user_id}"

@mcp.tool(name="user.get_user")
async def get_user(user_id: str) -> str:
    """获取用户信息"""
    logger.info("tool_call", tool="user.get_user", user_id=user_id)
    
    user = await collection.find_one({"user_id": user_id}, {"_id": 0})
    
    if not user:
        return f"User not found: {user_id}"
    
    return str(user)

@mcp.tool(name="user.update_user")
async def update_user(
    user_id: str,
    name: Optional[str] = None,
    age: Optional[int] = None,
    health_info: Optional[dict] = None,
    preferences: Optional[dict] = None,
    voice_preference: Optional[str] = None
) -> str:
    """更新用户信息"""
    from datetime import datetime
    
    logger.info("tool_call", tool="user.update_user", user_id=user_id)
    
    # 收集需要更新的字段
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if age is not None:
        update_data["age"] = age
    if health_info is not None:
        update_data["health_info"] = health_info
    if preferences is not None:
        update_data["preferences"] = preferences
    if voice_preference is not None:
        update_data["voice_preference"] = voice_preference
    
    if not update_data:
        return f"No fields to update for user {user_id}"
    
    # 添加更新时间
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = await collection.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        return f"User not found: {user_id}"
    
    logger.info("user_updated", user_id=user_id)
    return f"User {user_id} updated successfully"

@mcp.tool(name="user.delete_user")
async def delete_user(user_id: str) -> str:
    """删除用户"""
    logger.info("tool_call", tool="user.delete_user", user_id=user_id)
    
    result = await collection.delete_one({"user_id": user_id})
    
    if result.deleted_count == 0:
        return f"User not found: {user_id}"
    
    logger.info("user_deleted", user_id=user_id)
    return f"User {user_id} deleted"

@mcp.tool(name="user.switch_user")
async def switch_user(user_id: str) -> str:
    """切换当前用户（看护人专用）"""
    logger.info("tool_call", tool="user.switch_user", user_id=user_id)
    
    user = await collection.find_one({"user_id": user_id}, {"_id": 0})
    
    if not user:
        return f"User not found: {user_id}"
    
    logger.info("user_switched", user_id=user_id)
    return f"Switched to user: {user_id} (name: {user['name']}, role: {user['role']})"

@mcp.tool(name="user.set_voice_preference")
async def set_voice_preference(user_id: str, voice_id: str) -> str:
    """设置用户音色偏好"""
    from datetime import datetime
    
    logger.info("tool_call", tool="user.set_voice_preference", user_id=user_id, voice_id=voice_id)
    
    result = await collection.update_one(
        {"user_id": user_id},
        {"$set": {"voice_preference": voice_id, "updated_at": datetime.utcnow().isoformat()}}
    )
    
    if result.matched_count == 0:
        return f"User not found: {user_id}"
    
    logger.info("voice_preference_set", user_id=user_id, voice_id=voice_id)
    return f"Voice preference set for {user_id}: {voice_id}"

@mcp.tool(name="user.get_voice_preference")
async def get_voice_preference(user_id: str) -> str:
    """获取用户音色偏好"""
    logger.info("tool_call", tool="user.get_voice_preference", user_id=user_id)
    
    user = await collection.find_one(
        {"user_id": user_id},
        {"_id": 0, "voice_preference": 1}
    )
    
    if not user:
        return "User not found"
    
    voice = user.get("voice_preference", "")
    return voice

# 挂载 FastMCP 到 FastAPI
mcp_app = mcp.streamable_http_app()
app.mount("/mcp", mcp_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
