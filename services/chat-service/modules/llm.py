"""
LLM服务模块 - LangChain + 通义千问
从llm-service迁移
"""
import os
import json
from typing import Optional, List, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import structlog

logger = structlog.get_logger()

# LangChain配置 - 多模型支持
DASHSCOPE_API_BASE = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# 不同场景使用不同模型
llm_turbo = ChatOpenAI(
    model=os.getenv("QWEN_TURBO_MODEL", "qwen-turbo"),
    openai_api_base=DASHSCOPE_API_BASE,
    openai_api_key=DASHSCOPE_API_KEY,
    temperature=0.7
)

llm_plus = ChatOpenAI(
    model=os.getenv("QWEN_PLUS_MODEL", "qwen-plus"),
    openai_api_base=DASHSCOPE_API_BASE,
    openai_api_key=DASHSCOPE_API_KEY,
    temperature=0.7
)

llm_max = ChatOpenAI(
    model=os.getenv("QWEN_MAX_MODEL", "qwen-max"),
    openai_api_base=DASHSCOPE_API_BASE,
    openai_api_key=DASHSCOPE_API_KEY,
    temperature=0.7
)


async def chat(message: str, user_id: Optional[str] = None, history: Optional[List[Dict]] = None, model: str = "plus") -> str:
    """
    对话生成
    
    Args:
        message: 用户消息
        user_id: 用户ID（可选）
        history: 对话历史（可选）
        model: 模型选择（turbo/plus/max）
    
    Returns:
        AI回复文本
    """
    # 选择模型
    llm = {
        "turbo": llm_turbo,
        "plus": llm_plus,
        "max": llm_max
    }.get(model, llm_plus)
    
    try:
        # 构建消息列表
        messages = [
            SystemMessage(content="你是一个贴心的看护助手，帮助照顾老年人和小朋友。请用温暖、简洁的中文回复。")
        ]
        
        # 添加历史对话
        if history:
            for msg in history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # 添加当前消息
        messages.append(HumanMessage(content=message))
        
        # 调用LLM
        response = await llm.ainvoke(messages)
        
        logger.info("chat_success", model=model, message_length=len(message))
        return response.content
        
    except Exception as e:
        logger.error("chat_error", error=str(e))
        raise Exception(f"对话生成失败: {str(e)}")


async def summarize(text: str) -> str:
    """
    文本摘要
    
    Args:
        text: 需要摘要的文本
    
    Returns:
        摘要文本
    """
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个专业的文本摘要助手。请用简洁的中文总结以下内容，保持在50字以内。"),
            ("human", "{text}")
        ])
        
        chain = prompt | llm_turbo
        response = await chain.ainvoke({"text": text})
        
        logger.info("summarize_success", text_length=len(text))
        return response.content
        
    except Exception as e:
        logger.error("summarize_error", error=str(e))
        raise Exception(f"摘要生成失败: {str(e)}")


async def generate_plan(context: Dict) -> Dict:
    """
    任务规划 - LLM根据上下文生成执行计划
    
    Args:
        context: 包含用户意图、视觉分析结果、历史记忆等
    
    Returns:
        任务计划（包含步骤列表）
    """
    try:
        user_intent = context.get("user_intent", "")
        vision_result = context.get("vision_context", {})
        history = context.get("history", {})
        
        prompt = f"""你是一个智能任务规划器。根据以下信息，生成执行计划。

【用户意图】
{user_intent}

【视觉分析结果】
{json.dumps(vision_result, ensure_ascii=False, indent=2)}

【历史记忆】
{json.dumps(history, ensure_ascii=False, indent=2)}

请生成一个JSON格式的任务计划，包含以下步骤：
{{
  "steps": [
    {{
      "name": "步骤名称",
      "action": "具体动作（chat/notify/store_memory等）",
      "input": "步骤输入",
      "depends_on": ["依赖的步骤名称"]
    }}
  ],
  "response_text": "给用户的回复",
  "should_save_schedule": false,
  "schedule": null
}}

只返回JSON，不要其他内容。"""
        
        response = await llm_max.ainvoke([
            HumanMessage(content=prompt)
        ])
        
        # 解析JSON
        result = response.content
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        
        plan = json.loads(result)
        
        logger.info("plan_generated", steps_count=len(plan.get("steps", [])))
        return plan
        
    except Exception as e:
        logger.error("plan_generation_error", error=str(e))
        # 返回默认计划
        return {
            "steps": [
                {
                    "name": "回复用户",
                    "action": "chat",
                    "input": "我理解您的需求，让我来帮助您。",
                    "depends_on": []
                }
            ],
            "response_text": "我理解您的需求，让我来帮助您。",
            "should_save_schedule": False,
            "schedule": None
        }


async def extract_schedule_intent(conversation: str) -> Dict:
    """
    从对话中提取定时任务意图
    
    Args:
        conversation: 对话内容
    
    Returns:
        包含should_save_schedule和schedule信息
    """
    try:
        prompt = f"""分析用户的对话，判断是否有创建定时任务的意图。

如果有，提取以下信息:
- schedule_type: medication_reminder（用药提醒）, care_check（关怀检查）, meal_reminder（就餐提醒）等
- cron_expression: cron表达式 (分 时 日 月 星期)
- message: 提醒内容
- context: 额外上下文（如药物名称）

如果没有定时任务意图，返回 should_save_schedule: false

示例:
用户: "帮我每天早上8点提醒吃药"
返回: {{
  "should_save_schedule": true,
  "schedule": {{
    "type": "medication_reminder",
    "cron": "0 8 * * *",
    "message": "提醒吃药",
    "context": {{"medications": ["药"]}}
  }}
}}

用户: "今天天气怎么样"
返回: {{
  "should_save_schedule": false
}}

当前对话: {conversation}

返回JSON格式。"""
        
        response = await llm_plus.ainvoke([
            HumanMessage(content=prompt)
        ])
        
        # 解析JSON
        result = response.content
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        
        schedule_info = json.loads(result)
        
        logger.info("schedule_intent_extracted", 
                    should_save=schedule_info.get("should_save_schedule", False))
        return schedule_info
        
    except Exception as e:
        logger.error("schedule_intent_extraction_error", error=str(e))
        return {"should_save_schedule": False}
