"""
Temporal Activities - 任务活动
每个Activity对应一个可重试的操作
"""
from temporalio import activity
from typing import Dict, Optional
import structlog

logger = structlog.get_logger()


@activity.defn(name="speech_transcribe")
async def speech_transcribe(audio_data: str, sample_rate: int = 16000) -> str:
    """
    语音识别Activity
    
    Args:
        audio_data: Base64音频数据
        sample_rate: 采样率
    
    Returns:
        识别文本
    """
    try:
        from modules.speech import transcribe
        text = await transcribe(audio_data, sample_rate)
        
        activity.logger.info("speech_transcribe_completed", text_length=len(text))
        return text
        
    except Exception as e:
        activity.logger.error("speech_transcribe_failed", error=str(e))
        raise


@activity.defn(name="speech_synthesize")
async def speech_synthesize(text: str, voice_id: str = "zhixiaobai") -> str:
    """
    语音合成Activity
    
    Args:
        text: 要合成的文本
        voice_id: 音色ID
    
    Returns:
        Base64音频数据
    """
    try:
        from modules.speech import synthesize
        audio_base64 = await synthesize(text, voice_id)
        
        activity.logger.info("speech_synthesize_completed", text_length=len(text))
        return audio_base64
        
    except Exception as e:
        activity.logger.error("speech_synthesize_failed", error=str(e))
        raise


@activity.defn(name="vision_analyze")
async def vision_analyze(image_data: str, analysis_type: str = "general", user_role: str = "elder") -> Dict:
    """
    视觉分析Activity
    
    Args:
        image_data: Base64图像数据
        analysis_type: 分析类型
        user_role: 用户角色
    
    Returns:
        分析结果
    """
    try:
        from modules.vision import analyze_image
        result_text = await analyze_image(image_data, user_role, analysis_type)
        
        activity.logger.info("vision_analyze_completed", analysis_type=analysis_type)
        return {"result": result_text, "analysis_type": analysis_type}
        
    except Exception as e:
        activity.logger.error("vision_analyze_failed", error=str(e))
        raise


@activity.defn(name="vision_detect_danger")
async def vision_detect_danger(image_data: str) -> Dict:
    """
    危险检测Activity
    
    Args:
        image_data: Base64图像数据
    
    Returns:
        危险检测结果
    """
    try:
        from modules.vision import detect_danger
        danger_info = await detect_danger(image_data)
        
        activity.logger.info("danger_detection_completed", risk_level=danger_info.get("risk_level"))
        return danger_info
        
    except Exception as e:
        activity.logger.error("danger_detection_failed", error=str(e))
        raise


@activity.defn(name="llm_plan_task")
async def llm_plan_task(context: Dict) -> Dict:
    """
    LLM任务规划Activity
    
    Args:
        context: 上下文（用户意图、视觉结果、历史记忆）
    
    Returns:
        任务计划
    """
    try:
        from modules.llm import generate_plan
        plan = await generate_plan(context)
        
        activity.logger.info("task_plan_generated", steps_count=len(plan.get("steps", [])))
        return plan
        
    except Exception as e:
        activity.logger.error("task_plan_failed", error=str(e))
        raise


@activity.defn(name="llm_chat")
async def llm_chat(message: str, user_id: str, history: Optional[list] = None, model: str = "plus") -> str:
    """
    LLM对话Activity
    
    Args:
        message: 用户消息
        user_id: 用户ID
        history: 对话历史
        model: 模型选择
    
    Returns:
        AI回复
    """
    try:
        from modules.llm import chat
        response = await chat(message, user_id, history, model)
        
        activity.logger.info("llm_chat_completed", response_length=len(response))
        return response
        
    except Exception as e:
        activity.logger.error("llm_chat_failed", error=str(e))
        raise


@activity.defn(name="memory_retrieve")
async def memory_retrieve(user_id: str, query: str, top_k: int = 3) -> Dict:
    """
    记忆检索Activity
    
    Args:
        user_id: 用户ID
        query: 查询文本
        top_k: 返回数量
    
    Returns:
        相关记忆
    """
    try:
        from modules.memory import retrieve_context
        context = await retrieve_context(user_id, query, top_k)
        
        activity.logger.info("memory_retrieved", memory_count=context.get("memory_count", 0))
        return context
        
    except Exception as e:
        activity.logger.error("memory_retrieve_failed", error=str(e))
        raise


@activity.defn(name="memory_store")
async def memory_store(user_id: str, memory: str, metadata: Optional[Dict] = None) -> Dict:
    """
    记忆存储Activity
    
    Args:
        user_id: 用户ID
        memory: 记忆内容
        metadata: 元数据
    
    Returns:
        存储结果
    """
    try:
        from modules.memory import add_memory
        result = await add_memory(user_id, memory, metadata)
        
        activity.logger.info("memory_stored", user_id=user_id)
        return result
        
    except Exception as e:
        activity.logger.error("memory_store_failed", error=str(e))
        raise
