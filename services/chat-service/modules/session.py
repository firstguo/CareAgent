"""
会话管理模块 - 多轮对话支持
负责会话生命周期管理、并发安全、超时判断
"""
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel, Field
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = structlog.get_logger()


class MessageData(BaseModel):
    """消息数据模型"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class SessionData(BaseModel):
    """会话数据模型"""
    id: str = Field(alias="_id")
    session_key: str
    user_id: str
    status: str  # "active" or "expired"
    messages: List[MessageData] = []
    created_at: datetime
    last_active: datetime
    expire_at: datetime
    
    class Config:
        populate_by_name = True


class ConcurrentSessionError(Exception):
    """并发会话冲突错误"""
    pass


class SessionManager:
    """会话管理器 - 线程安全"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.sessions = db.sessions
        
        # 超时配置（秒）
        self.timeout_text = int(os.getenv("SESSION_TIMEOUT_TEXT", "10"))
        self.timeout_voice = int(os.getenv("SESSION_TIMEOUT_VOICE", "30"))
        
        # 消息限制
        self.message_limit = int(os.getenv("SESSION_MESSAGE_LIMIT", "50"))
        self.context_limit = int(os.getenv("CONTEXT_HISTORY_LIMIT", "10"))
    
    def _get_timeout(self, input_type: str) -> int:
        """获取超时阈值"""
        if input_type == "voice":
            return self.timeout_voice
        return self.timeout_text
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=1),
        retry=retry_if_exception_type(ConcurrentSessionError),
        reraise=True
    )
    async def get_or_create_session(self, user_id: str, input_type: str = "text") -> Tuple[SessionData, bool]:
        """
        获取或创建会话（并发安全）
        
        Args:
            user_id: 用户ID
            input_type: 输入类型 (text/voice)
        
        Returns:
            (session_data, is_new_session)
        """
        now = datetime.utcnow()
        timeout = timedelta(seconds=self._get_timeout(input_type))
        session_key = f"{user_id}:active"
        
        # Step 1: 尝试查找并更新活跃会话
        session = await self.sessions.find_one_and_update(
            {
                "session_key": session_key,
                "status": "active",
                "last_active": {"$gt": now - timeout}
            },
            {
                "$set": {
                    "last_active": now,
                    "expire_at": now + timedelta(seconds=60)
                }
            },
            return_document=1  # ReturnDocument.AFTER
        )
        
        if session:
            logger.info(
                "session_reused",
                user_id=user_id,
                session_id=session["_id"],
                message_count=len(session.get("messages", []))
            )
            return SessionData(**session), False
        
        # Step 2: 未找到，需要创建新会话
        # 先标记旧会话为 expired
        await self.expire_old_session(session_key)
        
        # 创建新会话
        session_id = f"sess_{user_id}_{int(now.timestamp())}"
        new_session = {
            "_id": session_id,
            "session_key": session_key,
            "user_id": user_id,
            "status": "active",
            "messages": [],
            "created_at": now,
            "last_active": now,
            "expire_at": now + timedelta(seconds=60)
        }
        
        try:
            await self.sessions.insert_one(new_session)
            logger.info(
                "session_created",
                user_id=user_id,
                session_id=session_id,
                timeout=self._get_timeout(input_type)
            )
            return SessionData(**new_session), True
        except DuplicateKeyError:
            # 并发冲突，另一个请求已经创建了
            logger.warning(
                "session_concurrent_conflict",
                user_id=user_id,
                retry=True
            )
            raise ConcurrentSessionError("并发创建冲突，重试")
    
    async def expire_old_session(self, session_key: str):
        """标记旧会话为 expired"""
        result = await self.sessions.update_many(
            {"session_key": session_key, "status": "active"},
            {
                "$set": {
                    "status": "expired",
                    "expired_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(
                "session_expired",
                session_key=session_key,
                count=result.modified_count
            )
    
    async def update_session(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str
    ) -> SessionData:
        """
        更新会话：追加消息并更新 last_active
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            assistant_message: AI回复
        
        Returns:
            更新后的会话数据
        """
        now = datetime.utcnow()
        
        user_msg = MessageData(role="user", content=user_message, timestamp=now)
        assistant_msg = MessageData(role="assistant", content=assistant_message, timestamp=now)
        
        result = await self.sessions.find_one_and_update(
            {"_id": session_id},
            {
                "$set": {
                    "last_active": now,
                    "expire_at": now + timedelta(seconds=60)
                },
                "$push": {
                    "messages": {
                        "$each": [
                            user_msg.dict(),
                            assistant_msg.dict()
                        ],
                        "$slice": -self.message_limit
                    }
                }
            },
            return_document=1
        )
        
        if not result:
            raise ValueError(f"Session not found: {session_id}")
        
        logger.info(
            "session_updated",
            session_id=session_id,
            message_count=len(result.get("messages", []))
        )
        
        return SessionData(**result)
    
    async def get_context_messages(self, session_id: str) -> List[MessageData]:
        """
        获取上下文消息（最近 N 条）
        
        Args:
            session_id: 会话ID
        
        Returns:
            最近的消息列表（用于 LLM 上下文）
        """
        session = await self.sessions.find_one({"_id": session_id})
        
        if not session:
            return []
        
        messages = session.get("messages", [])
        
        # 返回最近 N 条
        return messages[-self.context_limit:]
