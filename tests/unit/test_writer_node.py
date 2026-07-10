"""
文章写作节点单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.nodes.writer import write_draft_node
from tests.factories import make_state_with_topics


class TestWriteDraftNode:
    """文章写作节点测试"""

    @pytest.mark.asyncio
    async def test_write_draft_success(self):
        """测试成功生成文章"""
        # Mock LLM 服务
        mock_stream_result = MagicMock()
        mock_stream_result.content = "# 测试文章\n\n这是一篇测试文章内容。"
        mock_stream_result.usage = MagicMock()
        mock_stream_result.usage.input_tokens = 200
        mock_stream_result.usage.output_tokens = 300
        mock_stream_result.usage.total_tokens = 500
        mock_stream_result.usage.model = "gpt-4o"

        mock_llm_service = AsyncMock()
        mock_llm_service.stream_write_draft_with_usage.return_value = mock_stream_result

        with patch("app.graph.nodes.writer.get_llm_service", return_value=mock_llm_service):
            state = make_state_with_topics()
            state["selected_topic"] = "LangGraph 入门指南"
            result = await write_draft_node(state)

        assert result["status"] == "draft_generated"
        assert result["article_content"] == "# 测试文章\n\n这是一篇测试文章内容。"
        assert result["revision_count"] == 0
        assert result["error"] == ""

    @pytest.mark.asyncio
    async def test_write_draft_no_topic(self):
        """测试未选择选题"""
        state = make_state_with_topics()
        state["selected_topic"] = ""

        result = await write_draft_node(state)

        assert result["status"] == "error"
        assert "未选择选题" in result["error"]
        assert result["article_content"] == ""

    @pytest.mark.asyncio
    async def test_write_draft_with_feedback(self):
        """测试有修改意见时生成文章"""
        mock_stream_result = MagicMock()
        mock_stream_result.content = "# 修改后的文章\n\n根据反馈修改的文章。"
        mock_stream_result.usage = MagicMock()
        mock_stream_result.usage.input_tokens = 200
        mock_stream_result.usage.output_tokens = 300
        mock_stream_result.usage.total_tokens = 500
        mock_stream_result.usage.model = "gpt-4o"

        mock_llm_service = AsyncMock()
        mock_llm_service.stream_write_draft_with_usage.return_value = mock_stream_result

        with patch("app.graph.nodes.writer.get_llm_service", return_value=mock_llm_service):
            state = make_state_with_topics()
            state["selected_topic"] = "LangGraph 入门指南"
            state["review_feedback"] = "请增加更多技术细节"
            result = await write_draft_node(state)

        assert result["status"] == "draft_generated"
        assert result["revision_count"] == 1
        mock_llm_service.stream_write_draft_with_usage.assert_called_once_with(
            topic="LangGraph 入门指南", feedback="请增加更多技术细节", revision_count=1, model_config={}
        )

    @pytest.mark.asyncio
    async def test_write_draft_failure(self):
        """测试生成文章失败"""
        mock_llm_service = AsyncMock()
        mock_llm_service.stream_write_draft_with_usage.side_effect = Exception("API 调用失败")

        with patch("app.graph.nodes.writer.get_llm_service", return_value=mock_llm_service):
            state = make_state_with_topics()
            state["selected_topic"] = "LangGraph 入门指南"
            result = await write_draft_node(state)

        assert result["status"] == "error"
        assert "API 调用失败" in result["error"]
        assert result["article_content"] == ""

    @pytest.mark.asyncio
    async def test_write_draft_metrics(self):
        """测试指标记录"""
        mock_stream_result = MagicMock()
        mock_stream_result.content = "# 测试文章"
        mock_stream_result.usage = MagicMock()
        mock_stream_result.usage.input_tokens = 200
        mock_stream_result.usage.output_tokens = 300
        mock_stream_result.usage.total_tokens = 500
        mock_stream_result.usage.model = "gpt-4o"

        mock_llm_service = AsyncMock()
        mock_llm_service.stream_write_draft_with_usage.return_value = mock_stream_result

        with patch("app.graph.nodes.writer.get_llm_service", return_value=mock_llm_service):
            state = make_state_with_topics()
            state["selected_topic"] = "LangGraph 入门指南"
            result = await write_draft_node(state)

        assert "node_metrics" in result
        assert len(result["node_metrics"]) > 0
        metrics = result["node_metrics"][0]
        assert metrics["node_name"] == "write_draft"
        assert metrics["input_tokens"] == 200
        assert metrics["output_tokens"] == 300
