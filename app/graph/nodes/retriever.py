"""
检索节点 — 在写作前检索相关参考内容
作为 writer 节点的前置步骤，为 LLM 提供外部知识上下文
"""

from typing import Any, Dict

from app.core.logger import get_logger
from app.graph.state import AgentState

logger = get_logger(__name__)


async def retrieve_node(state: AgentState) -> Dict[str, Any]:
    """
    检索与选定选题相关的参考文档

    如果 RAG 服务不可用（未安装 chromadb），优雅降级为空列表
    """
    selected_topic = state.get("selected_topic", "")

    if not selected_topic:
        return {"retrieved_docs": [], "status": "retrieve_skipped"}

    try:
        from app.services.rag_service import get_rag_service

        rag = get_rag_service()
        docs = await rag.retrieve(selected_topic, k=3)

        retrieved = [{"content": d.content, "source": d.source, "score": d.score} for d in docs]

        return {
            "retrieved_docs": retrieved,
            "status": "retrieved",
        }
    except ImportError:
        logger.info("RAG dependencies not installed, skipping retrieval")
        return {"retrieved_docs": [], "status": "retrieve_skipped"}
    except Exception as e:
        logger.warning(f"RAG retrieval failed, proceeding without context: {e}")
        return {"retrieved_docs": [], "status": "retrieve_failed"}
