"""
质量评估节点
对 LLM 生成的文章进行多维度自动评分
"""

from typing import Any, Dict

from app.core.logger import get_logger
from app.graph.metrics import LLMUsage, MetricsContext, merge_metrics
from app.graph.state import AgentState
from app.services import get_llm_service

logger = get_logger(__name__)


async def evaluate_node(state: AgentState) -> Dict[str, Any]:
    """评估文章质量"""
    article = state.get("article_content", "")
    topic = state.get("selected_topic", "")

    if not article:
        return {"quality_score": {}, "status": "evaluate_skipped"}

    existing_metrics = state.get("node_metrics", [])

    with MetricsContext("evaluate") as tracker:
        try:
            llm_service = get_llm_service()
            model_config = state.get("model_config", {})
            score, usage = await llm_service.evaluate_article(topic, article, model_config=model_config)

            tracker.set_llm_usage(
                LLMUsage(
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    total_tokens=usage.total_tokens,
                    model=usage.model,
                )
            )

            return {
                "quality_score": {
                    "relevance": score.relevance,
                    "readability": score.readability,
                    "depth": score.depth,
                    "originality": score.originality,
                    "overall": score.overall,
                    "feedback": score.feedback,
                },
                "node_metrics": merge_metrics(existing_metrics, tracker.to_dict()),
                "status": "evaluated",
            }
        except Exception as e:
            logger.warning(f"Quality evaluation failed: {e}")
            return {
                "quality_score": {},
                "node_metrics": merge_metrics(existing_metrics, tracker.to_dict()),
                "status": "evaluate_error",
                "error": str(e),
            }
