"""
选题规划节点单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.nodes.planner import plan_topics_node
from tests.factories import make_initial_state


class TestPlanTopicsNode:
    """选题规划节点测试"""

    @pytest.mark.asyncio
    async def test_plan_topics_success(self):
        """测试成功生成选题"""
        # Mock LLM 服务
        mock_topics_response = MagicMock()
        mock_topics_response.topics = [
            MagicMock(title="选题1: AI入门"),
            MagicMock(title="选题2: 机器学习"),
            MagicMock(title="选题3: 深度学习"),
        ]

        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50
        mock_usage.total_tokens = 150
        mock_usage.model = "gpt-4o"

        mock_llm_service = AsyncMock()
        mock_llm_service.plan_topics.return_value = (mock_topics_response, mock_usage)

        with patch("app.graph.nodes.planner.get_llm_service", return_value=mock_llm_service):
            state = make_initial_state("AI技术")
            result = await plan_topics_node(state)

        assert result["status"] == "topics_generated"
        assert len(result["generated_topics"]) == 3
        assert result["generated_topics"][0] == "选题1: AI入门"
        assert result["error"] == ""

    @pytest.mark.asyncio
    async def test_plan_topics_failure(self):
        """测试生成选题失败"""
        mock_llm_service = AsyncMock()
        mock_llm_service.plan_topics.side_effect = Exception("API 调用失败")

        with patch("app.graph.nodes.planner.get_llm_service", return_value=mock_llm_service):
            state = make_initial_state("AI技术")
            result = await plan_topics_node(state)

        assert result["status"] == "error"
        assert "API 调用失败" in result["error"]
        assert result["generated_topics"] == []

    @pytest.mark.asyncio
    async def test_plan_topics_metrics(self):
        """测试指标记录"""
        mock_topics_response = MagicMock()
        mock_topics_response.topics = [MagicMock(title="选题1")]

        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50
        mock_usage.total_tokens = 150
        mock_usage.model = "gpt-4o"

        mock_llm_service = AsyncMock()
        mock_llm_service.plan_topics.return_value = (mock_topics_response, mock_usage)

        with patch("app.graph.nodes.planner.get_llm_service", return_value=mock_llm_service):
            state = make_initial_state("AI技术")
            result = await plan_topics_node(state)

        assert "node_metrics" in result
        assert len(result["node_metrics"]) > 0
        metrics = result["node_metrics"][0]
        assert metrics["node_name"] == "plan_topics"
        assert metrics["input_tokens"] == 100
        assert metrics["output_tokens"] == 50
