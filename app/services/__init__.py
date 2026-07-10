"""
服务模块 - 提供 LLM 和图片生成服务
"""

from app.services.image_service import image_service
from app.services.llm_service import LLMUsageInfo, StreamResult, TopicsResponse, llm_service


def get_llm_service():
    """获取 LLM 服务实例"""
    return llm_service


def get_image_service():
    """获取图片服务实例"""
    return image_service


def get_rag_service():
    """获取 RAG 服务实例"""
    from app.services.rag_service import get_rag_service as _get

    return _get()
