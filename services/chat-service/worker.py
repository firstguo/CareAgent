"""
Temporal Worker启动脚本
负责启动Worker并注册Workflows和Activities
"""
import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
import structlog

from workflows.care_task_workflow import CareTaskWorkflow
from activities.task_activities import (
    speech_transcribe,
    speech_synthesize,
    vision_analyze,
    vision_detect_danger,
    llm_plan_task,
    llm_chat,
    memory_retrieve,
    memory_store
)

structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()


async def main():
    """启动Temporal Worker"""
    
    # 从环境变量读取配置
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "careagent-tasks")
    
    logger.info("starting_temporal_worker", 
                host=temporal_host, 
                task_queue=task_queue)
    
    # 创建Temporal Client
    client = await Client.connect(
        temporal_host,
        namespace="default",
    )
    
    # 创建Worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[CareTaskWorkflow],
        activities=[
            speech_transcribe,
            speech_synthesize,
            vision_analyze,
            vision_detect_danger,
            vision_detect_danger_video,
            llm_plan_task,
            llm_chat,
            memory_retrieve,
            memory_store
        ]
    )
    
    logger.info("temporal_worker_started", 
                workflows=["CareTaskWorkflow"],
                activities_count=8)
    
    # 运行Worker（持续监听任务）
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
