"""
Chat Service - 统一的多模态交互服务
整合语音、视觉、LLM、记忆能力，提供REST API和异步任务执行
"""
import os
import asyncio
from typing import Set
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import structlog
from motor.motor_asyncio import AsyncIOMotorClient

# 配置日志
structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()

# FastAPI应用
app = FastAPI(
    title="Chat Service",
    description="统一的多模态交互服务",
    version="1.0.0"
)

# 全局变量
mongo_client: AsyncIOMotorClient
mongo_db = None
background_tasks: Set[asyncio.Task] = set()

# ============================================
# 数据模型
# ============================================

class InputData(BaseModel):
    type: Literal["voice", "text", "image", "video", "multimodal"]
    text: Optional[str] = None
    audio_data: Optional[str] = None
    image_data: Optional[str] = None
    video_data: Optional[str] = None
    context: Optional[dict] = None

class TaskInput(BaseModel):
    user_id: str
    trigger_type: Literal["user_initiated", "scheduled", "event_driven"] = "user_initiated"
    event_type: Optional[str] = None  # "fall_detection", "sensor_triggered", etc.
    input: InputData
    notification: Optional[dict] = None

class TaskStatus(BaseModel):
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    result: Optional[dict] = None
    steps: list = []
    created_at: datetime
    updated_at: datetime

# ============================================
# 生命周期事件
# ============================================

@app.on_event("startup")
async def startup():
    """启动时初始化连接"""
    global mongo_client, mongo_db
    
    # 连接MongoDB
    mongo_client = AsyncIOMotorClient(
        os.getenv("MONGODB_URI", "mongodb://admin:admin123@mongodb:27017")
    )
    mongo_db = mongo_client[os.getenv("MONGODB_DB_NAME", "careagent")]
    
    # 创建 tasks 集合索引
    await mongo_db.tasks.create_index([("user_id", 1), ("created_at", -1)])
    await mongo_db.tasks.create_index([("status", 1)])
    await mongo_db.tasks.create_index([("expire_at", 1)], expireAfterSeconds=0)
    
    # 创建 sessions 集合索引
    await mongo_db.sessions.create_index([("session_key", 1)], unique=True)
    await mongo_db.sessions.create_index([("expire_at", 1)], expireAfterSeconds=0)
    await mongo_db.sessions.create_index([("user_id", 1), ("last_active", -1)])
    
    logger.info("mongodb_connected")
    logger.info("sessions_collection_initialized")
    
    # 初始化工具缓存（任务 1.4）
    from modules.tool_cache import tool_cache, periodic_tool_refresh
    await tool_cache.refresh()
    
    # 启动后台定时刷新任务（任务 1.5）
    asyncio.create_task(periodic_tool_refresh())
    logger.info("tool_cache_initialized")

@app.on_event("shutdown")
async def shutdown():
    """关闭时清理连接和后台任务"""
    # 取消所有后台任务
    if background_tasks:
        logger.info("cancelling_background_tasks", count=len(background_tasks))
        for task in background_tasks:
            task.cancel()
        
        # 等待任务完成（最多30秒）
        try:
            await asyncio.wait_for(
                asyncio.gather(*background_tasks, return_exceptions=True),
                timeout=30
            )
        except asyncio.TimeoutError:
            logger.warning("background_tasks_timeout")
        
        logger.info("background_tasks_cancelled")
    
    if mongo_client:
        mongo_client.close()
        logger.info("mongodb_disconnected")


# ============================================
# REST API端点
# ============================================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "chat-service",
        "mongodb_connected": True
    }

@app.post("/api_planning")
async def api_planning(task_input: TaskInput):
    """
    统一异步入口 - 所有请求都走异步执行
    
    - 生成 task_id
    - 保存到 MongoDB
    - 后台异步执行
    - 立即返回 task_id
    """
    import uuid
    
    # 任务 2.1: 生成 task_id
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    now = datetime.now(datetime.timezone.utc)
    
    # 任务 2.1: 保存任务到 MongoDB
    task_record = {
        "_id": task_id,
        "user_id": task_input.user_id,
        "status": "pending",
        "trigger_type": task_input.trigger_type,
        "event_type": task_input.event_type,
        "input": task_input.input.dict(),
        "notification": task_input.notification,
        "steps": [],
        "result": None,
        "created_at": now,
        "updated_at": now,
        "expire_at": datetime(2026, 5, 22)  # 30天后过期
    }
    
    await mongo_db.tasks.insert_one(task_record)
    
    # 任务 2.2-2.3: 启动异步任务（不等待）
    task_input_dict = {
        "user_id": task_input.user_id,
        "trigger_type": task_input.trigger_type,
        "event_type": task_input.event_type,
        "input": task_input.input.dict()
    }
    
    task = asyncio.create_task(
        execute_task_async(task_id, task_input_dict, mongo_db)
    )
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    
    logger.info("task_submitted", task_id=task_id)
    
    # 任务 2.4: 立即返回
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "任务已提交，正在处理中"
    }


@app.get("/api_task_status/{task_id}")
async def api_task_status(task_id: str):
    """
    查询任务状态（任务 2.5）
    
    - 返回任务执行状态（pending/running/completed/failed）
    - 包含执行步骤详情
    - 包含最终结果（如果完成）
    """
    task = await mongo_db.tasks.find_one({"_id": task_id})
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task["_id"],
        "status": task["status"],
        "trigger_type": task.get("trigger_type"),
        "steps": task.get("steps", []),
        "result": task.get("result"),
        "error": task.get("error"),
        "created_at": task["created_at"],
        "updated_at": task["updated_at"]
    }


async def execute_task_async(task_id: str, task_input: Dict, mongo_db):
    """
    异步执行任务（任务 2.2）
    
    Args:
        task_id: 任务 ID
        task_input: 任务输入
        mongo_db: MongoDB 数据库连接
    """
    from executor import execute_task
    
    try:
        # 1. 更新状态为 running
        await mongo_db.tasks.update_one(
            {"_id": task_id},
            {"$set": {"status": "running", "updated_at": datetime.utcnow()}}
        )
        
        # 2. 执行任务（包含复杂度检测）
        result = await execute_task(task_id, task_input, mongo_db)
        
        # 3. 更新状态为 completed
        await mongo_db.tasks.update_one(
            {"_id": task_id},
            {"$set": {
                "status": "completed",
                "result": result,
                "updated_at": datetime.utcnow()
            }}
        )
        
        logger.info("task_completed", task_id=task_id)
        
    except asyncio.TimeoutError:
        error_msg = "Task timeout"
        logger.error("task_timeout", task_id=task_id)
        await mongo_db.tasks.update_one(
            {"_id": task_id},
            {"$set": {
                "status": "failed",
                "error": error_msg,
                "updated_at": datetime.utcnow()
            }}
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error("task_failed", task_id=task_id, error=error_msg)
        await mongo_db.tasks.update_one(
            {"_id": task_id},
            {"$set": {
                "status": "failed",
                "error": error_msg,
                "updated_at": datetime.utcnow()
            }}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
