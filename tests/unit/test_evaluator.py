"""
质量评估节点单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.nodes.evaluator import evaluate_node
from tests.factories import make_initial_state, make_state_with_article


class TestEvaluateNode:
    """质量评估节点测试"""

    @pytest.mark.asyncio
    async def test_evaluate_success(self):
        """测试成功评估文章"""
        mock_score = MagicMock()
        mock_score.relevance = 8
        mock_score.readability = 7
        mock_score.depth = 6
        mock_score.originality = 7
        mock_score.overall = 7.0
        mock_score.feedback = "整体不错，可以加深技术细节"

        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 80
        mock_usage.total_tokens = 180
        mock_usage.model = "gpt-4o"

        mock_llm_service = AsyncMock()
        mock_llm_service.evaluate_article.return_value = (mock_score, mock_usage)

        with patch("app.graph.nodes.evaluator.get_llm_service", return_value=mock_llm_service):
            state = make_state_with_article()
            result = await evaluate_node(state)

        assert result["status"] == "evaluated"
        assert "quality_score" in result
        score = result["quality_score"]
        assert score["relevance"] == 8
        assert score["readability"] == 7
        assert score["depth"] == 6
        assert score["originality"] == 7
        assert score["overall"] == 7.0
        assert score["feedback"] == "整体不错，可以加深技术细节"

    @pytest.mark.asyncio
    async def test_evaluate_empty_article(self):
        """测试空文章应跳过评估"""
        state = make_initial_state()
        result = await evaluate_node(state)

        assert result["status"] == "evaluate_skipped"
        assert result["quality_score"] == {}

    @pytest.mark.asyncio
    async def test_evaluate_failure(self):
        """测试评估失败"""
        mock_llm_service = AsyncMock()
        mock_llm_service.evaluate_article.side_effect = Exception("API 调用失败")

        with patch("app.graph.nodes.evaluator.get_llm_service", return_value=mock_llm_service):
            state = make_state_with_article()
            result = await evaluate_node(state)

        assert result["status"] == "evaluate_error"
        assert "API 调用失败" in result["error"]

    @pytest.mark.asyncio
    async def test_evaluate_metrics(self):
        """测试指标记录"""
        mock_score = MagicMock()
        mock_score.relevance = 8
        mock_score.readability = 7
        mock_score.depth = 6
        mock_score.originality = 7
        mock_score.overall = 7.0
        mock_score.feedback = "测试反馈"

        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 80
        mock_usage.total_tokens = 180
        mock_usage.model = "gpt-4o"

        mock_llm_service = AsyncMock()
        mock_llm_service.evaluate_article.return_value = (mock_score, mock_usage)

        with patch("app.graph.nodes.evaluator.get_llm_service", return_value=mock_llm_service):
            state = make_state_with_article()
            result = await evaluate_node(state)

        assert "node_metrics" in result
        assert len(result["node_metrics"]) > 0
        metrics = result["node_metrics"][0]
        assert metrics["node_name"] == "evaluate"
        assert metrics["input_tokens"] == 100
        assert metrics["output_tokens"] == 80
