"""
记忆服务模块 - Mem0 + Milvus
从memory-service迁移
"""
import os
from typing import Optional, List, Dict
from mem0 import Memory
import structlog

logger = structlog.get_logger()

# Mem0配置
memory_client = Memory(
    config={
        "vector_store": {
            "provider": "milvus",
            "config": {
                "host": os.getenv("MILVUS_HOST", "milvus"),
                "port": int(os.getenv("MILVUS_PORT", "19530")),
                "collection_name": os.getenv("MILVUS_COLLECTION_NAME", "careagent_memories")
            }
        }
    }
)


async def add_memory(user_id: str, memory: str, metadata: Optional[Dict] = None) -> Dict:
    """
    添加记忆
    
    Args:
        user_id: 用户ID
        memory: 记忆内容
        metadata: 元数据（可选）
    
    Returns:
        添加结果
    """
    try:
        result = memory_client.add(
            memory,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        logger.info("memory_added", user_id=user_id, memory_length=len(memory))
        return result
        
    except Exception as e:
        logger.error("memory_add_error", error=str(e))
        raise Exception(f"添加记忆失败: {str(e)}")


async def search_memory(user_id: str, query: str, top_k: int = 5) -> List[Dict]:
    """
    搜索记忆
    
    Args:
        user_id: 用户ID
        query: 搜索查询
        top_k: 返回结果数量
    
    Returns:
        相关记忆列表
    """
    try:
        results = memory_client.search(
            query,
            user_id=user_id,
            limit=top_k
        )
        
        logger.info("memory_searched", user_id=user_id, results_count=len(results))
        return results
        
    except Exception as e:
        logger.error("memory_search_error", error=str(e))
        return []


async def update_memory(memory_id: str, memory: str) -> bool:
    """
    更新记忆
    
    Args:
        memory_id: 记忆ID
        memory: 新的记忆内容
    
    Returns:
        是否成功
    """
    try:
        memory_client.update(
            memory_id=memory_id,
            data=memory
        )
        
        logger.info("memory_updated", memory_id=memory_id)
        return True
        
    except Exception as e:
        logger.error("memory_update_error", error=str(e))
        raise Exception(f"更新记忆失败: {str(e)}")


async def delete_memory(memory_id: str) -> bool:
    """
    删除记忆
    
    Args:
        memory_id: 记忆ID
    
    Returns:
        是否成功
    """
    try:
        memory_client.delete(memory_id=memory_id)
        
        logger.info("memory_deleted", memory_id=memory_id)
        return True
        
    except Exception as e:
        logger.error("memory_delete_error", error=str(e))
        raise Exception(f"删除记忆失败: {str(e)}")


async def get_conversation_history(user_id: str) -> List[Dict]:
    """
    获取对话历史
    
    Args:
        user_id: 用户ID
    
    Returns:
        对话历史列表
    """
    try:
        history = memory_client.get_all(user_id=user_id)
        
        logger.info("conversation_history_retrieved", user_id=user_id, count=len(history))
        return history
        
    except Exception as e:
        logger.error("conversation_history_error", error=str(e))
        return []


async def get_user_profile(user_id: str) -> Dict:
    """
    获取用户画像
    
    Args:
        user_id: 用户ID
    
    Returns:
        用户画像信息
    """
    try:
        profile = memory_client.get_user_profile(user_id=user_id)
        
        logger.info("user_profile_retrieved", user_id=user_id)
        return profile
        
    except Exception as e:
        logger.error("user_profile_error", error=str(e))
        return {}


async def retrieve_context(user_id: str, query: str, top_k: int = 3) -> Dict:
    """
    检索上下文 - 为LLM提供相关记忆
    
    Args:
        user_id: 用户ID
        query: 当前查询
        top_k: 返回记忆数量
    
    Returns:
        包含相关记忆的上下文
    """
    try:
        # 搜索相关记忆
        memories = await search_memory(user_id, query, top_k)
        
        # 获取用户画像
        profile = await get_user_profile(user_id)
        
        context = {
            "user_id": user_id,
            "relevant_memories": memories,
            "user_profile": profile,
            "memory_count": len(memories)
        }
        
        logger.info("context_retrieved", user_id=user_id, memory_count=len(memories))
        return context
        
    except Exception as e:
        logger.error("context_retrieval_error", error=str(e))
        return {
            "user_id": user_id,
            "relevant_memories": [],
            "user_profile": {},
            "memory_count": 0
        }
