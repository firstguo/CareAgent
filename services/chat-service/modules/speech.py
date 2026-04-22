"""
语音服务模块 - 阿里云百炼语音模型
使用Fun-ASR录音文件识别（基于Qwen3基座）和CosyVoice v3语音合成
"""
import os
import base64
from typing import Optional, List
import structlog
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
from dashscope.audio.asr import Transcription

logger = structlog.get_logger()

# 阿里云DashScope配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
dashscope.api_key = DASHSCOPE_API_KEY

# 音色列表 - 使用CosyVoice v3支持的音色
VOICE_LIST = [
    {"voice_id": "longxiaochun", "name": "龙小淳", "gender": "female", "language": "zh-CN", "description": "清新女声，适合日常对话"},
    {"voice_id": "longxiaoxia", "name": "龙小夏", "gender": "female", "language": "zh-CN", "description": "温柔女声，适合关怀场景"},
    {"voice_id": "longanyang", "name": "龙安阳", "gender": "male", "language": "zh-CN", "description": "阳光男声，适合播报场景"},
    {"voice_id": "stella", "name": "Stella", "gender": "female", "language": "en-US", "description": "英文女声，适合英语对话"},
]


async def transcribe(audio_data: str, sample_rate: int = 16000, format: str = "wav") -> str:
    """
    语音识别 - 阿里云Fun-ASR录音文件识别（基于Qwen3基座）
    
    Args:
        audio_data: Base64编码的WAV音频数据
        sample_rate: 采样率，默认16000
        format: 音频格式，默认wav
    
    Returns:
        识别文本
    """
    if not audio_data:
        raise ValueError("未提供音频数据")
    
    try:
        # 解码Base64音频
        audio_bytes = base64.b64decode(audio_data)
        
        # 使用临时文件保存音频数据
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        # 调用Fun-ASR转录服务（最新模型，基于Qwen3基座）
        response = Transcription.call(
            model='fun-asr',
            audio_file=temp_audio_path
        )
        
        # 清理临时文件
        import os
        os.unlink(temp_audio_path)
        
        if response.status_code == 200:
            # 提取识别结果
            text = response.output.get('text', '')
            if not text and 'results' in response.output:
                # 从结果中提取文本
                text = ' '.join([r.get('text', '') for r in response.output['results']])
            logger.info("transcribe_success", model="fun-asr", text_length=len(text))
        else:
            raise Exception(f"ASR请求失败: {response.code} - {response.message}")
        
        return text
        
    except Exception as e:
        logger.error("transcribe_error", error=str(e))
        raise Exception(f"识别失败: {str(e)}")


async def synthesize(text: str, voice_id: str = "longxiaochun", sample_rate: int = 16000, format: str = "wav") -> str:
    """
    语音合成 - 阿里云CosyVoice v3 TTS
    
    Args:
        text: 要合成的文本
        voice_id: 音色ID，默认longxiaochun
        sample_rate: 采样率，默认16000
        format: 音频格式，默认wav
    
    Returns:
        Base64编码的音频数据
    """
    if not text:
        raise ValueError("未提供文本")
    
    try:
        # 使用DashScope CosyVoice v3进行语音合成
        synthesizer = SpeechSynthesizer(
            model='cosyvoice-v3-flash',
            voice=voice_id,
            sample_rate=sample_rate,
            format=format
        )
        
        # 调用合成方法，直接返回二进制音频
        audio_data = synthesizer.call(text)
        
        # 返回Base64编码的音频
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        logger.info("synthesize_success", model="cosyvoice-v3-flash", voice_id=voice_id, text_length=len(text))
        return audio_base64
        
    except Exception as e:
        logger.error("synthesize_error", error=str(e))
        raise Exception(f"合成失败: {str(e)}")


async def list_voices() -> List[dict]:
    """
    获取可用音色列表
    
    Returns:
        音色列表
    """
    return VOICE_LIST


def get_aliyun_token():
    """
    获取阿里云Token（使用DashScope API Key）
    
    Returns:
        Token字符串
    """
    # 使用DashScope API Key作为认证
    return DASHSCOPE_API_KEY
