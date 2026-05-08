""" 
任务执行器 - 异步任务执行逻辑
替代原 Temporal Workflows + Activities
"""
import os
import asyncio
import json
from typing import Dict, Optional, List
from datetime import datetime
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = structlog.get_logger()

# 视频检测模板回复
VIDEO_RESPONSE_TEMPLATES = {
    "safe": "视频已记录，一切正常",
    "warning": "检测到潜在风险，请注意安全",
    "critical": "检测到摔倒，已通知紧急联系人"
}

# 自然表达映射表
REMINDER_TEXT_MAP = {
    "medication_reminder": "该吃药了！",
    "meal_reminder": "吃饭时间到了，记得按时用餐",
    "care_check": "该做健康检查了",
    "custom": None  # 使用 message 字段
}

# MCP Gateway 已注册的工具白名单
REGISTERED_TOOLS = {"tools.web_search", "tools.location_query"}

# 任务 4.1: 动态超时配置
TIMEOUT_CONFIG = {
    "single": 30,    # 单任务：30秒（简单问答）
    "multi": 120,    # 多任务：120秒（需要工具调用）
    "video": 180     # 视频检测：180秒（视频处理最耗时）
}


async def detect_task_complexity(user_message: str) -> Dict:
    """
    判定任务复杂度（任务 3.1-3.5，简化版）
    
    使用 LLM 分析用户消息，判定是单任务还是多任务。
    优化：不需要传入 tools 信息，只判定任务类型
    
    Args:
        user_message: 用户消息
    
    Returns:
        {
            "task_type": "single" | "multi",
            "steps": ["step1", "step2", ...]  # 执行步骤
        }
    """
    import time
    start_time = time.time()
    
    try:
        from modules.llm import llm_plus
        
        prompt = f"""你是一个智能任务分析器。分析用户的消息，判断是简单任务还是复杂任务。

【判定标准】
- 单任务（single）：简单问答、问候、单一问题，不需要调用外部工具
  例如："你好"、"今天天气怎么样"、"讲个笑话"
  
- 多任务（multi）：需要多个步骤、需要查询外部信息、需要调用工具
  例如："帮我查一下北京的天气，并推荐附近的药店"、"搜索今天的新闻，然后告诉我哪些与健康相关"

【用户消息】
{user_message}

请返回 JSON 格式：
{{
  "task_type": "single" 或 "multi",
  "steps": ["步骤1", "步骤2"]  // 简要描述执行步骤
}}

只返回 JSON，不要其他内容。"""
        
        response = await llm_plus.ainvoke([
            HumanMessage(content=prompt)
        ])
        
        # 解析 JSON
        result = response.content
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        
        complexity_info = json.loads(result)
        
        # 验证返回值
        task_type = complexity_info.get("task_type", "single")
        if task_type not in ["single", "multi"]:
            task_type = "single"
        
        steps = complexity_info.get("steps", [])
        if not isinstance(steps, list):
            steps = []
        
        duration = time.time() - start_time
        
        logger.info(
            "task_complexity_detected",
            task_type=task_type,
            steps_count=len(steps),
            duration=round(duration, 2)
        )
        
        return {
            "task_type": task_type,
            "steps": steps
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "task_complexity_detection_failed",
            error=str(e),
            duration=round(duration, 2),
            fallback="single"
        )
        # 任务 3.4: 判定失败时使用默认值
        return {
            "task_type": "single",
            "steps": []
        }


def get_natural_reminder_text(schedule_type: str, message: str) -> str:
    """
    获取自然表达的提醒文本
    
    Args:
        schedule_type: 定时任务类型
        message: 原始消息
    
    Returns:
        自然表达的提醒文本
    """
    if schedule_type in REMINDER_TEXT_MAP and REMINDER_TEXT_MAP[schedule_type]:
        return REMINDER_TEXT_MAP[schedule_type]
    return message


def generate_tool_key(tool_name: str, args: Dict) -> str:
    """
    生成工具调用的唯一键（任务 3.1）
    
    Args:
        tool_name: 工具名称
        args: 工具参数
    
    Returns:
        唯一键字符串
    """
    return f"{tool_name}:{json.dumps(args, sort_keys=True)}"


async def execute_tool_call(tool_call: Dict) -> Dict:
    """
    执行单个工具调用（任务 5.1-5.5）
    
    Args:
        tool_call: 工具调用信息 {"name": "tools.xxx", "args": {...}}
    
    Returns:
        工具调用结果
    """
    import time
    import httpx
    from tenacity import retry, stop_after_attempt, wait_exponential
    
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})
    
    logger.info(
        "tool_call_started",
        tool_name=tool_name,
        args=tool_args
    )
    
    start_time = time.time()
    
    # 任务 5.2-5.3: 超时处理和重试机制
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def call_mcp_gateway():
        """调用 MCP Gateway 的工具接口"""
        # MCP Gateway 地址（从环境变量读取）
        gateway_url = os.getenv("MCP_GATEWAY_URL", "http://gateway:4444/mcp")
        
        # 构造 MCP 工具调用请求
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": tool_args
            },
            "id": 1
        }
        
        # 任务 5.2: 超时处理（默认 10 秒）
        timeout = int(os.getenv("TOOL_CALL_TIMEOUT", "10"))
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(gateway_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # 提取工具调用结果
            if "result" in result:
                return result["result"]
            elif "error" in result:
                raise Exception(f"MCP Gateway error: {result['error']}")
            else:
                raise Exception(f"Unexpected response: {result}")
    
    try:
        # 执行工具调用
        result = await call_mcp_gateway()
        duration = time.time() - start_time
        
        logger.info(
            "tool_call_completed",
            tool_name=tool_name,
            duration=round(duration, 2),
            success=True
        )
        
        return {
            "success": True,
            "result": result,
            "tool_name": tool_name,
            "duration": duration
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "tool_call_failed",
            tool_name=tool_name,
            error=str(e),
            duration=round(duration, 2)
        )
        
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name,
            "duration": duration
        }


async def execute_chat_flow(task_id: str, task_input: Dict, mongo_db):
    """
    执行任务（使用优化的意图识别和工具调用）
    
    Args:
        task_id: 任务 ID
        task_input: 任务输入
        mongo_db: MongoDB 数据库连接
    
    Returns:
        任务执行结果
    """
    import time
    from modules.session import SessionManager
    from modules.llm import generate_plan, extract_schedule_intent, llm_plus
    from modules.speech import synthesize
    from modules.tool_cache import tool_cache
    from modules.intent_recognition import (
        IntentRecognizer,
        ParameterExtractor,
        TaskDecomposer,
        LoopValidator
    )
    
    start_time = time.time()
    # 0. 语音识别处理
    input_data = task_input.get("input", {})
    input_type = input_data.get("type", "text")
    if input_type == "voice" and input_data.get("audio_data"):
        from modules.speech import transcribe
        audio_data = input_data.get("audio_data", "")
        transcribed_text = await transcribe(audio_data)
        input_data["text"] = transcribed_text
        logger.info("voice_transcribed", task_id=task_id, text_length=len(transcribed_text))


    # 1. 获取用户消息
    user_message = task_input.get("input", {}).get("text", "")
    user_id = task_input.get("user_id", "")
    
    if not user_message:
        raise ValueError("Message is required")
    

    # 2. 任务分解（参考 GenerateTaskHub.gen_root_task）
    task_decomposer = TaskDecomposer(llm_plus)
    decomposition = await task_decomposer.decompose_task(user_message)
    is_single_task = decomposition.get("is_single_task", True)
    sub_tasks = decomposition.get("sub_tasks", [])
    
    task_type = "single" if is_single_task else "multi"
    
    # 任务 4.2: 根据任务类型获取超时时间
    timeout = TIMEOUT_CONFIG.get(task_type, 60)
    logger.info(
        "task_timeout_set",
        task_id=task_id,
        task_type=task_type,
        timeout=timeout,
        subtasks_count=len(sub_tasks)
    )
    
    # 3. 获取可用工具列表（从缓存）
    available_tools = await tool_cache.get_tools()
    logger.info(
        "available_tools_loaded",
        task_id=task_id,
        tools_count=len(available_tools)
    )
    
    # 4. 获取或创建会话
    session_manager = SessionManager(mongo_db)
    session_data, is_new = await session_manager.get_or_create_session(user_id, "text")
    
    # 5. 意图识别和工具选择（参考 ApiSelectionHub）
    intent_recognizer = IntentRecognizer(llm_plus)
    intent_result = await intent_recognizer.recognize_intent(user_message, available_tools)
    
    # 检测注入攻击
    if intent_result.get("is_injection"):
        logger.warning("injection_attack_detected", task_id=task_id, query=user_message)
        raise ValueError("提示注入攻击检测")
    
    selected_tools = intent_result.get("selected_tools", [])
    
    # 6. 执行工具调用链（参考 ApiPlanningHub.apis_planning）
    tool_results = []
    api_chain = []  # 工具调用链，用于循环检测
    parameter_extractor = ParameterExtractor(llm_plus)
    
    if selected_tools:
        for tool_info in selected_tools:
            tool_name = tool_info.get("name", "")
            tool_params = tool_info.get("params", {})
            missing_params = tool_info.get("missing_params", [])
            
            # 6.1 检测缺失参数并尝试补齐（参考 supplement_parameters）
            if missing_params:
                logger.info(
                    "missing_params_detected",
                    task_id=task_id,
                    tool=tool_name,
                    missing=missing_params
                )
                # TODO: 实现参数补齐逻辑（可以后续扩展）
                # 目前直接跳过缺失参数的工具调用
                continue
            
            # 6.2 执行工具调用
            tool_call = {"name": tool_name, "args": tool_params}
            result = await execute_tool_call(tool_call)
            
            # 6.3 记录调用链（用于循环检测）
            api_chain.append({
                "tool_name": tool_name,
                "params": tool_params,
                "result": result.get("result"),
                "success": result.get("success", False)
            })
            
            # 6.4 循环检测（参考 loop_validate）
            if not LoopValidator.validate(api_chain):
                logger.warning(
                    "loop_call_detected",
                    task_id=task_id,
                    tool=tool_name
                )
                break
            
            tool_results.append(result)
    
    # 7. 构建 LLM 消息数组（整合工具调用结果）
    session_messages = session_data.messages[-10:] if session_data.messages else []
    
    messages = [
        SystemMessage(content="你是一个贴心的看护助手，帮助照顾老年人和小朋友。请用温暖、简洁的中文回复。")
    ]
    
    # 添加 session 历史消息
    for msg in session_messages:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))
    
    # 添加工具调用结果到上下文（参考 ToolSummaryHub.tool_summary）
    if tool_results:
        successful_tools = [tr for tr in tool_results if tr.get("success")]
        if successful_tools:
            tool_context = "\n".join([
                f"【工具 {tr['tool_name']} 查询结果】\n{json.dumps(tr.get('result', {}), ensure_ascii=False)}"
                for tr in successful_tools
            ])
            messages.append(HumanMessage(content=f"【工具查询结果】\n{tool_context}"))
            messages.append(AIMessage(content="好的，我已经获取了相关信息。"))
    
    # 8. 添加当前用户消息
    messages.append(HumanMessage(content=user_message))
    
    # 9. 调用 LLM 生成回复（参考 generate_plan）
    response = await llm_plus.ainvoke(messages)
    assistant_message = response.content
    
    # 10. 更新 session
    await session_manager.update_session(
        session_data.id,
        user_message,
        assistant_message
    )
    
    # 11. 检测定时任务意图
    schedule_info = await extract_schedule_intent(user_message)
    
    # 12. 生成 TTS 语音
    try:
        audio_confirm = await synthesize(assistant_message)
    except Exception as e:
        logger.error("audio_confirm_generation_error", error=str(e))
        audio_confirm = None
    
    # 13. 处理定时任务
    audio_reminder = None
    schedule_result = None
    
    if schedule_info.get("should_save_schedule"):
        schedule = schedule_info.get("schedule", {})
        schedule_type = schedule.get("type", "custom")
        message = schedule.get("message", "")
        
        reminder_text = get_natural_reminder_text(schedule_type, message)
        
        try:
            audio_reminder = await synthesize(reminder_text)
        except Exception as e:
            logger.error("audio_reminder_generation_error", error=str(e))
            audio_reminder = None
        
        schedule_result = {
            "cron": schedule.get("cron"),
            "message": message,
            "type": schedule_type,
            "audio_reminder": audio_reminder,
            "context": schedule.get("context", {})
        }
    
    # 14. 构建结果（增强版，包含意图识别信息）
    total_duration = time.time() - start_time
    result = {
        "session_id": session_data.id,
        "response": assistant_message,
        "audio_confirm": audio_confirm,
        "audio_reminder": audio_reminder,
        "is_new_session": is_new,
        "message_count": len(session_data.messages) + 2,
        "schedule": schedule_result,
        "task_type": task_type,
        "intent": intent_result.get("intent", ""),
        "intent_confidence": intent_result.get("confidence", 0),
        "tool_stats": {
            "total_selected": len(selected_tools),
            "total_executed": len(tool_results),
            "successful": len([tr for tr in tool_results if tr.get("success")])
        },
        "api_chain": api_chain,
        "duration": round(total_duration, 2)
    }
    
    logger.info(
        "task_execution_completed",
        task_id=task_id,
        task_type=task_type,
        intent=intent_result.get("intent"),
        tools_executed=len(tool_results),
        duration=round(total_duration, 2)
    )
    
    return result


async def update_task_status(
    mongo_db,
    task_id: str,
    status: str,
    result: Optional[Dict] = None,
    error: Optional[str] = None,
    steps: Optional[list] = None
):
    """
    更新任务状态
    
    Args:
        mongo_db: MongoDB 数据库连接
        task_id: 任务 ID
        status: 任务状态 (pending/running/completed/failed)
        result: 任务执行结果
        error: 错误信息
        steps: 执行步骤列表
    """
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    
    if result is not None:
        update_data["result"] = result
    
    if error is not None:
        update_data["error"] = error
    
    if steps is not None:
        update_data["steps"] = steps
    
    await mongo_db.tasks.update_one(
        {"_id": task_id},
        {"$set": update_data}
    )
    
    logger.info("task_status_updated", task_id=task_id, status=status)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def call_llm_with_retry(llm_func, *args, **kwargs):
    """
    LLM 调用（带重试）
    
    Args:
        llm_func: LLM 函数
        *args, **kwargs: 函数参数
    
    Returns:
        LLM 响应
    """
    return await llm_func(*args, **kwargs)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def call_vision_with_retry(vision_func, *args, **kwargs):
    """
    视觉 API 调用（带重试）
    
    Args:
        vision_func: 视觉函数
        *args, **kwargs: 函数参数
    
    Returns:
        视觉分析结果
    """
    return await vision_func(*args, **kwargs)


async def execute_task(task_id: str, task_input: Dict, mongo_db):
    """
    任务执行主入口
    
    Args:
        task_id: 任务 ID
        task_input: 任务输入
        mongo_db: MongoDB 数据库连接
    """
    logger.info("task_execution_started", task_id=task_id)
    
    try:
        # 更新状态为 running
        await update_task_status(mongo_db, task_id, "running")
        
        trigger_type = task_input.get("trigger_type", "user_initiated")
        event_type = task_input.get("event_type")
        
        # 根据触发类型分发到不同执行逻辑
        if trigger_type == "event_driven" and event_type == "fall_detection":
            result = await execute_fall_detection(task_id, task_input, mongo_db)
        else:
            result = await execute_chat_flow(task_id, task_input, mongo_db)
        
        # 更新状态为 completed
        await update_task_status(mongo_db, task_id, "completed", result=result)
        
        logger.info("task_execution_completed", task_id=task_id)
        
    except asyncio.TimeoutError:
        error_msg = "Task timeout (60s)"
        logger.error("task_timeout", task_id=task_id)
        await update_task_status(mongo_db, task_id, "failed", error=error_msg)
        
    except Exception as e:
        error_msg = str(e)
        logger.error("task_execution_failed", task_id=task_id, error=error_msg)
        await update_task_status(mongo_db, task_id, "failed", error=error_msg)


async def execute_chat_flow(task_id: str, task_input: Dict, mongo_db):
    """
    执行对话流程（迁移原 CareTaskWorkflow 逻辑）
    
    Args:
        task_id: 任务 ID
        task_input: 任务输入
        mongo_db: MongoDB 数据库连接
    
    Returns:
        对话结果
    """
    logger.info("chat_flow_started", task_id=task_id)
    
    steps = []
    user_id = task_input.get("user_id", "")
    trigger_type = task_input.get("trigger_type", "user_initiated")
    input_data = task_input.get("input", {})
    
    # Phase 1: 输入处理
    input_type = input_data.get("type", "text")
    user_text = input_data.get("text", "")

    # 如果是语音输入，先转文字
    if input_type == "voice" and input_data.get("audio_data"):
        from modules.speech import transcribe
        audio_data = input_data.get("audio_data", "")
        user_text = await transcribe(audio_data)
        logger.info("voice_transcribed_in_chat_flow", task_id=task_id, text_length=len(user_text))
        input_data["text"] = user_text

    steps.append({"step": "input_processing", "status": "completed"})
    
    # Phase 2: 记忆检索
    logger.info("phase2_memory_retrieval_started", task_id=task_id)
    from modules.memory import retrieve_memories
    memory_context = await call_llm_with_retry(
        retrieve_memories,
        user_id,
        user_text,
        5
    )
    steps.append({"step": "memory_retrieval", "status": "completed", "memory_count": memory_context.get("memory_count", 0)})
    
    # Phase 3: LLM 任务规划
    logger.info("phase3_task_planning_started", task_id=task_id)
    from modules.llm import generate_plan
    
    planning_context = {
        "user_intent": user_text,
        "history": memory_context,
        "trigger_type": trigger_type
    }
    
    plan = await call_llm_with_retry(generate_plan, planning_context)
    steps.append({"step": "task_planning", "status": "completed", "steps_count": len(plan.get("steps", []))})
    
    # Phase 4: LLM 对话生成
    logger.info("phase4_chat_generation_started", task_id=task_id)
    from modules.llm import generate_chat_response
    
    chat_context = {
        "user_text": user_text,
        "plan": plan,
        "memory_context": memory_context
    }
    
    chat_response = await call_llm_with_retry(generate_chat_response, chat_context)
    steps.append({"step": "chat_generation", "status": "completed"})
    
    # Phase 5: 记忆存储
    logger.info("phase5_memory_storage_started", task_id=task_id)
    from modules.memory import store_memory
    
    await call_llm_with_retry(
        store_memory,
        user_id,
        user_text,
        chat_response.get("text_response", "")
    )
    steps.append({"step": "memory_storage", "status": "completed"})
    
    # 构建最终结果
    result = {
        "task_id": task_id,
        "user_id": user_id,
        "steps_executed": steps,
        "final_response": chat_response.get("text_response", ""),
        "audio_response": chat_response.get("audio_response"),
        "should_save_schedule": chat_response.get("should_save_schedule", False),
        "schedule": chat_response.get("schedule")
    }
    
    logger.info("chat_flow_completed", task_id=task_id)
    return result


async def execute_fall_detection(task_id: str, task_input: Dict, mongo_db):
    """
    执行摔倒检测流程（迁移原 VideoFallDetectionWorkflow 逻辑）
    
    Args:
        task_id: 任务 ID
        task_input: 任务输入
        mongo_db: MongoDB 数据库连接
    
    Returns:
        摔倒检测结果
    """
    logger.info("fall_detection_started", task_id=task_id)
    
    steps = []
    user_id = task_input.get("user_id", "")
    input_data = task_input.get("input", {})
    video_data = input_data.get("video_data", "")
    
    # Phase 1: 视频危险检测
    logger.info("phase1_video_detection_started", task_id=task_id)
    from modules.vision import detect_danger_video
    
    detection_result = await call_vision_with_retry(detect_danger_video, video_data)
    steps.append({
        "step": "video_danger_detection",
        "status": "completed",
        "risk_level": detection_result.get("risk_level"),
        "confidence": detection_result.get("confidence")
    })
    
    # Phase 2: 生成模板回复 + TTS 语音
    risk_level = detection_result.get("risk_level", "safe")
    response_text = VIDEO_RESPONSE_TEMPLATES.get(risk_level, "视频已记录")
    
    # 调用 TTS 生成语音
    from modules.speech import synthesize
    try:
        audio_base64 = await synthesize(response_text)
        logger.info("fall_detection_tts_generated", risk_level=risk_level)
    except Exception as e:
        logger.error("fall_detection_tts_error", error=str(e))
        audio_base64 = None
    
    # 如果检测到危险，触发警报
    alert_triggered = risk_level == "critical"
    if alert_triggered:
        logger.warning("fall_detection_alert_triggered", task_id=task_id)
        # TODO: 实现紧急通知逻辑
    
    # 构建最终结果（不存储 session）
    result = {
        "status": "recorded",
        "result": detection_result,
        "response": response_text,
        "audio": audio_base64,
        "alert_triggered": alert_triggered,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(
        "fall_detection_completed",
        task_id=task_id,
        risk_level=risk_level,
        confidence=detection_result.get("confidence"),
        alert_triggered=alert_triggered
    )
    
    return result


async def execute_conversation(
    user_id: str,
    user_message: str,
    session_data,
    mongo_db,
    input_type: str = "text"
) -> Dict:
    """
    执行多轮对话流程（任务 4.1-4.5）
    
    Args:
        user_id: 用户ID
        user_message: 用户消息
        session_data: 会话数据 (SessionData)
        mongo_db: MongoDB 数据库连接
        input_type: 输入类型 (text/voice)
    
    Returns:
        对话结果
    """
    import time
    
    logger.info("conversation_started", user_id=user_id, session_id=session_data.id)
    
    # 任务 4.1: 集成任务复杂度检测
    start_time = time.time()
    complexity = await detect_task_complexity(user_message)
    task_type = complexity.get("task_type", "single")
    
    # 任务 4.4: 记录执行路径选择
    logger.info(
        "execution_path_selected",
        task_type=task_type,
        user_id=user_id
    )
    
    # 根据任务类型选择执行路径（任务 4.2-4.3）
    if task_type == "single":
        # 单任务快速路径：直接调用 LLM 生成回复
        result = await execute_simple_conversation(
            user_id, user_message, session_data, mongo_db, input_type
        )
    else:
        # 多任务完整路径：工具调用 + 多步骤执行
        result = await execute_complex_task(
            user_id, user_message, session_data, mongo_db, input_type, complexity
        )
    
    # 任务 4.5: 记录性能监控日志
    total_duration = time.time() - start_time
    logger.info(
        "conversation_completed",
        user_id=user_id,
        session_id=session_data.id,
        task_type=task_type,
        total_duration=round(total_duration, 2)
    )
    
    return result


async def execute_simple_conversation(
    user_id: str,
    user_message: str,
    session_data,
    mongo_db,
    input_type: str = "text"
) -> Dict:
    """
    单任务快速路径：直接调用 LLM 生成回复（任务 4.2）
    
    Args:
        user_id: 用户ID
        user_message: 用户消息
        session_data: 会话数据
        mongo_db: MongoDB 数据库连接
        input_type: 输入类型
    
    Returns:
        对话结果
    """
    # Phase 1: 构建双层上下文（简化版，不检索长期记忆）
    session_messages = session_data.messages[-10:] if session_data.messages else []
    
    # Phase 2: 构建 LLM 消息数组
    messages = [
        SystemMessage(content="你是一个贴心的看护助手，帮助照顾老年人和小朋友。请用温暖、简洁的中文回复。")
    ]
    
    # 添加 session 历史消息（不包含 mem0 记忆，加快速度）
    for msg in session_messages:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))
    
    # 添加当前用户消息
    messages.append(HumanMessage(content=user_message))
    
    # Phase 3: 调用 LLM
    from modules.llm import llm_plus
    response = await llm_plus.ainvoke(messages)
    assistant_message = response.content
    
    # Phase 4: 更新 session
    from modules.session import SessionManager
    session_manager = SessionManager(mongo_db)
    
    await session_manager.update_session(
        session_data.id,
        user_message,
        assistant_message
    )
    
    # Phase 5: 检测定时任务意图（简化：不检测，加快速度）
    schedule_info = {"should_save_schedule": False}
    
    # Phase 6: 生成语音（仅 audio_confirm）
    from modules.speech import synthesize
    
    try:
        audio_confirm = await synthesize(assistant_message)
    except Exception as e:
        logger.error("audio_confirm_generation_error", error=str(e))
        audio_confirm = None
    
    # 构建结果
    result = {
        "session_id": session_data.id,
        "response": assistant_message,
        "audio_confirm": audio_confirm,
        "audio_reminder": None,
        "is_new_session": len(session_data.messages) == 0,
        "message_count": len(session_data.messages) + 2,
        "schedule": None
    }
    
    return result


async def execute_complex_task(
    user_id: str,
    user_message: str,
    session_data,
    mongo_db,
    input_type: str = "text",
    complexity: Optional[Dict] = None
) -> Dict:
    """
    多任务完整路径：工具调用 + 多步骤执行（任务 4.3）
    
    Args:
        user_id: 用户ID
        user_message: 用户消息
        session_data: 会话数据
        mongo_db: MongoDB 数据库连接
        input_type: 输入类型
        complexity: 任务复杂度信息
    
    Returns:
        对话结果
    """
    # Phase 1: 构建双层上下文（完整版）
    session_messages = session_data.messages[-10:] if session_data.messages else []
    
    # 从 mem0 检索长期记忆
    from modules.memory import search_memory
    mem0_memories = await search_memory(user_id, user_message, top_k=3)
    
    # Phase 2: 构建 LLM 消息数组
    messages = [
        SystemMessage(content="你是一个贴心的看护助手，帮助照顾老年人和小朋友。请用温暖、简洁的中文回复。")
    ]
    
    # 添加 mem0 记忆
    if mem0_memories:
        memory_text = "\n".join([
            f"用户信息: {mem.get('memory', '')}"
            for mem in mem0_memories[:3]
        ])
        messages.append(HumanMessage(content=memory_text))
        messages.append(AIMessage(content="好的，我已经了解了用户的信息。"))
    
    # 添加 session 历史消息
    for msg in session_messages:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))
    
    # Phase 3: 任务规划（包含工具调用判定）
    from modules.llm import generate_plan
    
    planning_context = {
        "user_intent": user_message,
        "history": {"memories": mem0_memories},
        "trigger_type": "user_initiated"
    }
    available_tools = models.tools.get_available_tools()
    plan = await generate_plan(planning_context, available_tools)
    tools_to_call = plan.get("tools", [])
    
    # Phase 4: 执行工具调用（任务 3.2-3.5: 去重机制）
    executed_tools = set()  # 已执行的工具集合
    tool_results = []
    
    for tool_call in tools_to_call:
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        
        # 任务 3.1: 生成唯一键
        tool_key = generate_tool_key(tool_name, tool_args)
        
        # 任务 3.3: 检测重复调用
        if tool_key in executed_tools:
            logger.info(
                "duplicate_tool_call_skipped",
                tool_name=tool_name,
                args=tool_args
            )
            # 任务 3.4: 复用第一次的结果（这里从 tool_results 中查找）
            for prev_result in tool_results:
                if prev_result.get("tool_key") == tool_key:
                    tool_results.append({
                        **prev_result,
                        "reused": True  # 任务 3.5: 标记复用
                    })
                    break
            continue
        
        # 执行工具调用（任务 5.1-5.5）
        result = await execute_tool_call(tool_call)
        result["tool_key"] = tool_key
        result["reused"] = False
        tool_results.append(result)
        
        # 添加到已执行集合
        executed_tools.add(tool_key)
    
    # Phase 5: 整合工具调用结果到 LLM 上下文（任务 5.5）
    if tool_results:
        tool_context = "\n".join([
            f"工具 {tr['tool_name']} 结果: {json.dumps(tr.get('result', {}), ensure_ascii=False)}"
            for tr in tool_results if tr.get("success")
        ])
        messages.append(HumanMessage(content=f"【工具查询结果】\n{tool_context}"))
        messages.append(AIMessage(content="好的，我已经获取了相关信息。"))
    
    # 添加当前用户消息
    messages.append(HumanMessage(content=user_message))
    
    # Phase 6: 调用 LLM 生成回复（带工具结果）
    from modules.llm import llm_plus
    response = await llm_plus.ainvoke(messages)
    assistant_message = response.content
    
    # Phase 7: 更新 session
    from modules.session import SessionManager
    session_manager = SessionManager(mongo_db)
    
    await session_manager.update_session(
        session_data.id,
        user_message,
        assistant_message
    )
    
    # Phase 8: 检测定时任务意图
    from modules.llm import extract_schedule_intent
    schedule_info = await extract_schedule_intent(user_message)
    
    # Phase 9: 生成双语音
    from modules.speech import synthesize
    
    try:
        audio_confirm = await synthesize(assistant_message)
    except Exception as e:
        logger.error("audio_confirm_generation_error", error=str(e))
        audio_confirm = None
    
    # 如果有定时任务，生成 audio_reminder
    audio_reminder = None
    schedule_result = None
    
    if schedule_info.get("should_save_schedule"):
        schedule = schedule_info.get("schedule", {})
        schedule_type = schedule.get("type", "custom")
        message = schedule.get("message", "")
        
        # 使用自然表达映射
        reminder_text = get_natural_reminder_text(schedule_type, message)
        
        try:
            audio_reminder = await synthesize(reminder_text)
            logger.info("audio_reminder_generated", text=reminder_text)
        except Exception as e:
            logger.error("audio_reminder_generation_error", error=str(e))
            audio_reminder = None
        
        # 构建 schedule 对象（包含 audio_reminder）
        schedule_result = {
            "cron": schedule.get("cron"),
            "message": message,
            "type": schedule_type,
            "audio_reminder": audio_reminder,
            "context": schedule.get("context", {})
        }
    
    # 构建结果（任务 6.1-6.5: 添加统计信息）
    result = {
        "session_id": session_data.id,
        "response": assistant_message,
        "audio_confirm": audio_confirm,
        "audio_reminder": audio_reminder,
        "is_new_session": len(session_data.messages) == 0,
        "message_count": len(session_data.messages) + 2,
        "schedule": schedule_result,
        # 任务 6.2: 工具调用统计
        "tool_stats": {
            "total_calls": len(tools_to_call),
            "executed_calls": len(executed_tools),
            "skipped_duplicates": len(tools_to_call) - len(executed_tools)
        }
    }
    
    logger.info(
        "complex_task_completed",
        user_id=user_id,
        session_id=session_data.id,
        tools_executed=len(executed_tools),
        tools_skipped=len(tools_to_call) - len(executed_tools)
    )
    
    return result
