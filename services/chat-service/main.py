"""
Chat Service - 统一的多模态交互服务
整合语音、视觉、LLM、记忆能力，提供REST API和Temporal工作流编排
"""
import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import structlog
from motor.motor_asyncio import AsyncIOMotorClient
from temporalio.client import Client
from temporalio.worker import Worker

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
temporal_client: Client
mongo_client: AsyncIOMotorClient
mongo_db = None
temporal_worker: Worker
worker_task: asyncio.Task

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
    input: InputData
    notification: Optional[dict] = None

class TaskResult(BaseModel):
    text_response: str
    audio_response: Optional[str] = None
    should_save_schedule: bool = False
    schedule: Optional[dict] = None

class TaskStatus(BaseModel):
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    result: Optional[dict] = None
    steps: list = []
    created_at: datetime
    updated_at: datetime

class EventTriggerInput(BaseModel):
    """事件触发输入"""
    user_id: str
    trigger_type: Literal["event_driven"] = "event_driven"
    event_type: str  # "sensor_triggered", "manual_check", etc.
    video_data: str  # Base64编码的视频
    sensor_info: Optional[dict] = None  # 传感器信息

# ============================================
# 生命周期事件
# ============================================

@app.on_event("startup")
async def startup():
    """启动时初始化连接和Temporal Worker"""
    global temporal_client, mongo_client, mongo_db, temporal_worker, worker_task
    
    # 连接Temporal
    temporal_client = await Client.connect(
        os.getenv("TEMPORAL_HOST", "temporal:7233"),
        namespace=os.getenv("TEMPORAL_NAMESPACE", "default")
    )
    logger.info("temporal_connected")
    
    # 连接MongoDB
    mongo_client = AsyncIOMotorClient(
        os.getenv("MONGODB_URI", "mongodb://admin:admin123@mongodb:27017")
    )
    mongo_db = mongo_client[os.getenv("MONGODB_DB_NAME", "careagent")]
    
    # 创建索引
    await mongo_db.tasks.create_index([("user_id", 1), ("created_at", -1)])
    await mongo_db.tasks.create_index([("status", 1)])
    await mongo_db.tasks.create_index([("expire_at", 1)], expireAfterSeconds=0)
    
    logger.info("mongodb_connected")
    
    # 启动Temporal Worker
    await start_temporal_worker()

@app.on_event("shutdown")
async def shutdown():
    """关闭时清理连接和Worker"""
    # 停止Temporal Worker
    if temporal_worker:
        logger.info("stopping_temporal_worker")
        temporal_worker.stop()
        if worker_task:
            await worker_task
        logger.info("temporal_worker_stopped")
    
    if mongo_client:
        mongo_client.close()
        logger.info("mongodb_disconnected")

async def start_temporal_worker():
    """启动Temporal Worker"""
    global temporal_worker, worker_task
    
    # 导入Workflows和Activities
    from workflows.care_task_workflow import CareTaskWorkflow
    from activities.task_activities import (
        vision_detect_danger_video,
        llm_plan_task,
        llm_chat,
        memory_retrieve,
        memory_store
    )
    
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "careagent-tasks")
    
    # 创建Worker
    temporal_worker = Worker(
        temporal_client,
        task_queue=task_queue,
        workflows=[CareTaskWorkflow],
        activities=[
            vision_detect_danger_video,
            llm_plan_task,
            llm_chat,
            memory_retrieve,
            memory_store
        ]
    )
    
    logger.info("temporal_worker_started",
                workflows=["CareTaskWorkflow"],
                activities_count=5,
                task_queue=task_queue)
    
    # 在后台运行Worker
    worker_task = asyncio.create_task(temporal_worker.run())
    
    logger.info("temporal_worker_running")

# ============================================
# REST API端点
# ============================================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "chat-service",
        "temporal_connected": True,
        "mongodb_connected": True
    }

@app.post("/api_planning")
async def api_planning(task_input: TaskInput):
    """
    提交任务，异步执行，返回task_id
    
    - 接收多模态输入（语音、文本、图像）
    - 启动Temporal Workflow异步执行
    - 立即返回task_id供后续查询
    """
    import uuid
    from datetime import timedelta
    
    # 生成task_id
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()
    
    # 创建任务记录
    task_record = {
        "_id": task_id,
        "user_id": task_input.user_id,
        "status": "pending",
        "trigger_type": task_input.trigger_type,
        "input": task_input.input.dict(),
        "notification": task_input.notification,
        "steps": [],
        "result": None,
        "created_at": now,
        "updated_at": now,
        "expire_at": datetime(2026, 5, 22)  # 30天后过期
    }
    
    # 保存到MongoDB
    await mongo_db.tasks.insert_one(task_record)
    
    try:
        # 启动Temporal Workflow
        handle = await temporal_client.start_workflow(
            "CareTaskWorkflow",
            args=[{
                "task_id": task_id,
                "user_id": task_input.user_id,
                "trigger_type": task_input.trigger_type,
                "input": task_input.input.dict()
            }],
            id=task_id,
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "careagent-tasks")
        )
        
        # 更新任务状态为running
        await mongo_db.tasks.update_one(
            {"_id": task_id},
            {"$set": {"status": "running", "temporal_workflow_id": handle.id}}
        )
        
        logger.info("workflow_started", task_id=task_id, workflow_id=handle.id)
        
    except Exception as e:
        logger.error("workflow_start_failed", task_id=task_id, error=str(e))
        # 更新为failed
        await mongo_db.tasks.update_one(
            {"_id": task_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=f"启动工作流失败: {str(e)}")
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "任务已提交，正在处理中"
    }

@app.get("/api_task_status/{task_id}")
async def api_task_status(task_id: str):
    """
    查询任务状态
    
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
        "created_at": task["created_at"],
        "updated_at": task["updated_at"]
    }

@app.post("/api_event_trigger")
async def event_trigger(event_input: EventTriggerInput):
    """
    事件触发视频分析
    
    - 接收前端录制的视频
    - 启动视频摔倒检测Workflow
    - 返回task_id供查询
    """
    import uuid
    from datetime import datetime
    
    task_id = f"fall_detect_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()
    
    # 创建任务记录
    task_record = {
        "_id": task_id,
        "user_id": event_input.user_id,
        "status": "pending",
        "trigger_type": "event_driven",
        "event_type": event_input.event_type,
        "input": {
            "type": "video",
            "video_data": event_input.video_data,
            "sensor_info": event_input.sensor_info
        },
        "steps": [],
        "result": None,
        "created_at": now,
        "updated_at": now,
        "expire_at": datetime(2026, 5, 22)
    }
    
    await mongo_db.tasks.insert_one(task_record)
    
    try:
        # 启动视频检测Workflow
        handle = await temporal_client.start_workflow(
            "VideoFallDetectionWorkflow",
            args=[{
                "task_id": task_id,
                "user_id": event_input.user_id,
                "video_data": event_input.video_data,
                "sensor_info": event_input.sensor_info
            }],
            id=task_id,
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "careagent-tasks")
        )
        
        # 更新状态
        await mongo_db.tasks.update_one(
            {"_id": task_id},
            {"$set": {"status": "running", "updated_at": now}}
        )
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "视频分析中，请等待结果"
        }
        
    except Exception as e:
        logger.error("workflow_start_failed", error=str(e))
        await mongo_db.tasks.update_one(
            {"_id": task_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "updated_at": now
            }}
        )
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
