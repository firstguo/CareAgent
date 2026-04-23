"""
Temporal Workflow - 任务编排
实现多步骤DAG工作流
"""
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, Optional, List
from datetime import timedelta
import structlog

# 导入Activities
with workflow.unsafe.imports_passed_through():
    from activities.task_activities import (
        vision_detect_danger_video,
        llm_plan_task,
        llm_chat,
        memory_retrieve,
        memory_store
    )

logger = structlog.get_logger()


@workflow.defn(name="CareTaskWorkflow")
class CareTaskWorkflow:
    """
    看护任务工作流
    编排多步骤任务：语音识别→视觉分析→LLM规划→执行→记忆存储
    """
    
    @workflow.run
    async def run(self, task_input: Dict) -> Dict:
        """
        执行工作流
        
        Args:
            task_input: 任务输入（包含user_id、trigger_type、input数据等）
        
        Returns:
            任务执行结果
        """
        workflow.logger.info("workflow_started", task_id=task_input.get("task_id"))
        
        user_id = task_input.get("user_id", "")
        trigger_type = task_input.get("trigger_type", "user_initiated")
        input_data = task_input.get("input", {})
        
        # 初始化结果
        workflow_result = {
            "task_id": task_input.get("task_id"),
            "user_id": user_id,
            "steps_executed": [],
            "final_response": "",
            "audio_response": None,
            "should_save_schedule": False,
            "schedule": None
        }
        
        try:
            # ==================== Phase 1: 输入处理 ====================
            # 直接使用文本输入
            
            user_text = input_data.get("text", "")
            
            # ==================== Phase 2: 记忆检索 ====================
            # 与输入处理并行（如果有历史查询需求）
            workflow.logger.info("phase2_memory_retrieval_started")
            
            memory_context = await workflow.execute_activity(
                memory_retrieve,
                args=[user_id, user_text, 5],
                start_to_close_timeout=timedelta(seconds=20),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            workflow_result["steps_executed"].append("memory_retrieval")
            workflow.logger.info("phase2_memory_retrieval_completed", 
                               memory_count=memory_context.get("memory_count", 0))
            
            # ==================== Phase 3: LLM任务规划 ====================
            workflow.logger.info("phase3_task_planning_started")
            
            # 构建上下文
            planning_context = {
                "user_intent": user_text,
                "history": memory_context,
                "trigger_type": trigger_type
            }
            
            plan = await workflow.execute_activity(
                llm_plan_task,
                args=[planning_context],
                start_to_close_timeout=timedelta(seconds=45),
                retry_policy=RetryPolicy(maximum_attempts=1)  # LLM规划不重试
            )
            
            workflow_result["steps_executed"].append("task_planning")
            workflow.logger.info("phase3_task_planning_completed", 
                               steps_count=len(plan.get("steps", [])))
            
            # ==================== Phase 4: 执行计划 ====================
            workflow.logger.info("phase4_plan_execution_started")
            
            for step in plan.get("steps", []):
                step_name = step.get("name", "unknown")
                action = step.get("action", "")
                step_input = step.get("input", "")
                
                workflow.logger.info("executing_step", step_name=step_name, action=action)
                
                # 根据action类型执行
                if action == "chat":
                    response = await workflow.execute_activity(
                        llm_chat,
                        args=[step_input, user_id],
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(maximum_attempts=2)
                    )
                    workflow_result["final_response"] = response
                    
                elif action == "notify":
                    # TODO: 通知功能（需要实现其他通知方式）
                    workflow.logger.info("notify_action_not_implemented", message=step_input)
                    workflow_result["final_response"] = step_input
                    
                elif action == "store_memory":
                    # 存储记忆
                    await workflow.execute_activity(
                        memory_store,
                        args=[user_id, step_input, {"trigger_type": trigger_type}],
                        start_to_close_timeout=timedelta(seconds=20),
                        retry_policy=RetryPolicy(maximum_attempts=2)
                    )
                
                workflow_result["steps_executed"].append(f"execute_{step_name}")
            
            # ==================== Phase 5: 后处理 ====================
            # 检查是否有定时任务意图
            if plan.get("should_save_schedule"):
                workflow_result["should_save_schedule"] = True
                workflow_result["schedule"] = plan.get("schedule")
                workflow.logger.info("schedule_intent_detected", 
                                   schedule_type=plan.get("schedule", {}).get("type"))
            
            workflow.logger.info("workflow_completed", 
                               steps_executed=workflow_result["steps_executed"])
            
            return workflow_result
            
        except Exception as e:
            workflow.logger.error("workflow_failed", error=str(e))
            return {
                "task_id": task_input.get("task_id"),
                "user_id": user_id,
                "steps_executed": workflow_result["steps_executed"],
                "final_response": f"抱歉，处理您的请求时遇到错误：{str(e)}",
                "audio_response": None,
                "error": str(e),
                "should_save_schedule": False,
                "schedule": None
            }


@workflow.defn(name="VideoFallDetectionWorkflow")
class VideoFallDetectionWorkflow:
    """视频摔倒检测工作流"""
    
    @workflow.run
    async def run(self, workflow_input: Dict) -> Dict:
        """
        执行视频摔倒检测
        
        Args:
            workflow_input: {
                "task_id": "...",
                "user_id": "...",
                "video_data": "...",
                "sensor_info": {...}
            }
        """
        workflow.logger.info("video_fall_detection_started", 
                            task_id=workflow_input["task_id"])
        
        try:
            # 执行视频危险检测
            detection_result = await workflow.execute_activity(
                vision_detect_danger_video,
                args=[workflow_input["video_data"]],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            workflow.logger.info("video_fall_detection_completed",
                                risk_level=detection_result["risk_level"],
                                confidence=detection_result["confidence"])
            
            from datetime import datetime
            return {
                "task_id": workflow_input["task_id"],
                "user_id": workflow_input["user_id"],
                "result": detection_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            workflow.logger.error("video_fall_detection_failed", error=str(e))
            raise
