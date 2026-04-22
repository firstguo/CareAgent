"""
视觉服务模块 - Qwen-VL图像分析
从 vision-service迁移
"""
import os
import base64
import json
import tempfile
import cv2
import numpy as np
from typing import Optional, Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import structlog
import asyncio

logger = structlog.get_logger()

# 通义千问VL配置
DASHSCOPE_API_BASE = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
QWEN_VL_MODEL = os.getenv("QWEN_VL_MODEL", "qwen-vl-max")

# 初始化Qwen-VL
qwen_vl = ChatOpenAI(
    model=QWEN_VL_MODEL,
    openai_api_base=DASHSCOPE_API_BASE,
    openai_api_key=DASHSCOPE_API_KEY,
    temperature=0.1
)

# 风险等级定义
RISK_LEVELS = {
    "critical": "严重风险（跌倒、火灾、危险物品等）",
    "warning": "潜在风险（地面湿滑、光线不足等）",
    "normal": "正常状态"
}


async def analyze_image(image_data: str, user_role: str = "elder", analysis_type: str = "general") -> str:
    """
    分析图像内容
    
    Args:
        image_data: Base64编码的图像数据
        user_role: 用户角色（elder/child）
        analysis_type: 分析类型（general/safety/emotion/activity）
    
    Returns:
        分析结果文本
    """
    if not image_data:
        raise ValueError("未提供图像数据")
    
    try:
        # 构建分析Prompt
        prompts = {
            "general": f"""分析这张图片，重点关注：
1. 图片中有谁？（{user_role}）
2. 人物状态如何？（姿势、表情、活动）
3. 环境是否安全？
4. 有什么需要注意的事项？

请用中文简洁回答。""",
            "safety": f"""分析这张图片的安全性：
1. 是否存在安全隐患？
2. 环境是否适合{user_role}活动？
3. 有哪些安全建议？

请用中文简洁回答。""",
            "emotion": """分析图片中人物的情绪状态：
1. 情绪如何？（开心、平静、焦虑、痛苦等）
2. 身体状态如何？
3. 是否需要关注或帮助？

请用中文简洁回答。""",
            "activity": """分析图片中人物正在进行的活动：
1. 在做什么？
2. 活动是否安全合适？
3. 有什么建议？

请用中文简洁回答。"""
        }
        
        prompt_text = prompts.get(analysis_type, prompts["general"])
        
        # 调用Qwen-VL
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        )
        
        response = qwen_vl.invoke([message])
        result = response.content
        
        logger.info("image_analyzed", analysis_type=analysis_type, result_length=len(result))
        return result
        
    except Exception as e:
        logger.error("analyze_error", error=str(e))
        raise Exception(f"图像分析失败: {str(e)}")


async def detect_danger(image_data: str) -> Dict:
    """
    检测危险场景
    
    Args:
        image_data: Base64编码的图像数据
    
    Returns:
        危险检测结果（包含风险等级、描述、建议等）
    """
    if not image_data:
        raise ValueError("未提供图像数据")
    
    try:
        prompt_text = """你是一个专业的安全风险检测系统。分析这张图片，检测以下危险：

【严重危险】（返回critical）
- 跌倒或摔倒
- 火灾或烟雾
- 危险物品（刀具、药品散落等）
- 人员昏迷或受伤

【潜在风险】（返回warning）
- 地面湿滑
- 光线不足
- 障碍物绊倒风险
- 电器使用不当

【正常】（返回normal）
- 无明显危险

请按以下JSON格式返回：
{
  "risk_level": "critical/warning/normal",
  "risk_description": "风险描述",
  "detected_objects": ["检测到的物体列表"],
  "recommendations": ["建议措施"]
}

只返回JSON，不要其他内容。"""
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        )
        
        response = qwen_vl.invoke([message])
        result = response.content
        
        # 尝试解析JSON
        try:
            # 清理可能的markdown代码块
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("```", 1)[0]
            danger_info = json.loads(result)
        except:
            danger_info = {
                "risk_level": "warning",
                "risk_description": result,
                "detected_objects": [],
                "recommendations": ["建议人工确认"]
            }
        
        logger.info("danger_detected", risk_level=danger_info.get("risk_level"))
        return danger_info
        
    except Exception as e:
        logger.error("danger_detection_error", error=str(e))
        raise Exception(f"危险检测失败: {str(e)}")


async def assess_environment(image_data: str, area_type: str = "living_room") -> Dict:
    """
    评估环境安全性
    
    Args:
        image_data: Base64编码的图像数据
        area_type: 区域类型（bedroom/bathroom/kitchen/living_room/outdoor）
    
    Returns:
        环境评估结果（包含安全评分、问题、建议等）
    """
    if not image_data:
        raise ValueError("未提供图像数据")
    
    try:
        # 区域特定的评估标准
        area_concerns = {
            "bedroom": "床铺整洁度、地面障碍物、夜间照明",
            "bathroom": "地面湿滑、扶手、防滑垫、通风",
            "kitchen": "燃气安全、刀具存放、地面清洁、通风",
            "living_room": "家具摆放、地面障碍物、光线、通道畅通",
            "outdoor": "路面状况、天气、交通、照明"
        }
        
        concern = area_concerns.get(area_type, "整体环境安全")
        
        prompt_text = f"""你是一个环境安全评估专家。评估这个{area_type}的环境安全性。

重点关注：
1. {concern}
2. 是否存在安全隐患？
3. 环境是否适合老年人/小朋友？
4. 有什么改进建议？

请按以下JSON格式返回：
{{
  "area_type": "{area_type}",
  "safety_score": 0-100的分数,
  "safety_level": "优秀/良好/一般/较差",
  "issues": ["发现的问题列表"],
  "recommendations": ["改进建议列表"],
  "environment_status": {{
    "lighting": "充足/一般/不足",
    "cleanliness": "整洁/一般/杂乱",
    "accessibility": "良好/一般/较差"
  }}
}}

只返回JSON，不要其他内容。"""
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        )
        
        response = qwen_vl.invoke([message])
        result = response.content
        
        # 尝试解析JSON
        try:
            # 清理可能的markdown代码块
            if result.startswith("```"):
                result = result.split("\n", 1)[1].rsplit("```", 1)[0]
            env_assessment = json.loads(result)
        except:
            env_assessment = {
                "area_type": area_type,
                "safety_score": 50,
                "safety_level": "一般",
                "issues": ["自动解析失败，需要人工评估"],
                "recommendations": ["建议人工评估环境"],
                "environment_status": {
                    "lighting": "未知",
                    "cleanliness": "未知",
                    "accessibility": "未知"
                }
            }
        
        logger.info("environment_assessed", area_type=area_type, safety_score=env_assessment.get("safety_score"))
        return env_assessment
        
    except Exception as e:
        logger.error("environment_assessment_error", error=str(e))
        raise Exception(f"环境评估失败: {str(e)}")


# ============================================
# 视频处理函数
# ============================================

def extract_frames_uniform(video_path: str, num_frames: int = 5) -> List[str]:
    """
    均匀抽帧
    
    Args:
        video_path: 视频文件路径
        num_frames: 抽取帧数
    
    Returns:
        Base64编码的帧列表
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError("无法打开视频文件")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 计算均匀间隔
    if total_frames <= num_frames:
        # 帧数不足，全部返回
        frame_indices = list(range(total_frames))
    else:
        # 均匀采样
        frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    
    frames_base64 = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        
        if ret:
            # 转译为JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            frames_base64.append(frame_base64)
    
    cap.release()
    return frames_base64


async def detect_danger_video(video_base64: str) -> Dict:
    """
    视频危险检测（摔倒检测）
    
    Args:
        video_base64: Base64编码的视频数据
    
    Returns:
        检测结果，包含风险等级、置信度、时序证据等
    """
    try:
        # 步骤1: 解码视频
        video_bytes = base64.b64decode(video_base64)
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            tmp.write(video_bytes)
            video_path = tmp.name
        
        # 步骤2: 抽帧
        frames = extract_frames_uniform(
            video_path=video_path,
            num_frames=5
        )
        
        if len(frames) < 3:
            raise ValueError(f"视频帧数不足: {len(frames)} < 3")
        
        # 步骤3: 逐帧分析（并行）
        frame_tasks = [detect_danger(frame) for frame in frames]
        frame_results = await asyncio.gather(*frame_tasks)
        
        # 步骤4: 时序推理聚合
        final_result = aggregate_temporal_results(frame_results, frames)
        
        # 清理临时文件
        import os
        os.remove(video_path)
        
        logger.info("video_danger_detected", 
                     risk_level=final_result["risk_level"],
                     confidence=final_result["confidence"])
        
        return final_result
        
    except Exception as e:
        logger.error("video_danger_detection_error", error=str(e))
        raise Exception(f"视频危险检测失败: {str(e)}")


def analyze_temporal_pattern(risk_levels: List[str]) -> str:
    """
    分析时序模式
    
    识别典型摔倒模式：normal → warning → critical → critical
    """
    if len(risk_levels) < 3:
        return "帧数不足，无法分析时序"
    
    # 简化描述
    pattern_map = {
        "normal": "正常站立",
        "warning": "身体倾斜",
        "critical": "倒地"
    }
    
    pattern = "→".join([pattern_map.get(level, level) for level in risk_levels])
    
    # 检测典型摔倒模式
    if risk_levels[-3:].count("critical") >= 2:
        pattern += " [疑似摔倒]"
    
    return pattern


def aggregate_temporal_results(frame_results: List[Dict], frames: List[str]) -> Dict:
    """
    时序推理聚合
    
    分析帧序列的状态变化，判断是否为真正的摔倒
    
    Args:
        frame_results: 每帧的检测结果
        frames: 帧数据列表
    
    Returns:
        聚合结果
    """
    # 提取每帧的风险等级
    risk_levels = [r.get("risk_level", "normal") for r in frame_results]
    
    # 计算置信度
    critical_count = risk_levels.count("critical")
    warning_count = risk_levels.count("warning")
    total_frames = len(risk_levels)
    
    # 时序逻辑判断
    temporal_evidence = analyze_temporal_pattern(risk_levels)
    
    # 最终判定
    if critical_count >= 3:  # 至少3帧检测到critical
        risk_level = "critical"
        confidence = min(0.95, 0.7 + (critical_count / total_frames) * 0.25)
        event_type = "fall_detected"
        alert_level = "immediate" if confidence > 0.9 else "urgent"
    elif critical_count >= 2 or (critical_count >= 1 and warning_count >= 2):
        risk_level = "critical"
        confidence = 0.75
        event_type = "possible_fall"
        alert_level = "urgent"
    elif warning_count >= 3:
        risk_level = "warning"
        confidence = 0.6
        event_type = "uncertain"
        alert_level = "normal"
    else:
        risk_level = "normal"
        confidence = 0.9
        event_type = "safe"
        alert_level = "info"
    
    # 构建建议
    recommendations = generate_recommendations(risk_level, confidence, event_type)
    
    return {
        "risk_level": risk_level,
        "confidence": round(confidence, 2),
        "event_type": event_type,
        "temporal_evidence": temporal_evidence,
        "frame_count": total_frames,
        "alert_level": alert_level,
        "recommendations": recommendations,
        "frame_analysis": frame_results  # 详细帧分析
    }


def generate_recommendations(risk_level: str, confidence: float, event_type: str) -> List[str]:
    """生成建议措施"""
    recommendations = []
    
    if risk_level == "critical" and confidence > 0.9:
        recommendations.extend([
            "🚨 立即联系紧急联系人",
            "建议视频通话确认老人状态",
            "如无人回应，考虑呼叫急救电话",
            "保持通话直到确认安全"
        ])
    elif risk_level == "critical":
        recommendations.extend([
            "⚠️ 可能检测到摔倒",
            "请尽快联系老人确认状态",
            "建议查看实时视频或照片"
        ])
    elif risk_level == "warning":
        recommendations.extend([
            "📋 检测到潜在风险",
            "建议关注老人活动状态",
            "可安排定时检查"
        ])
    else:
        recommendations.append("✅ 未检测到异常，老人状态正常")
    
    return recommendations
