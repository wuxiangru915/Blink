"""
视觉内容生成节点单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graph.nodes.visualizer import extract_visuals_node, generate_images_node
from tests.factories import make_state_with_article


class TestExtractVisualsNode:
    """提取视觉要点节点测试"""

    @pytest.mark.asyncio
    async def test_extract_visuals_success(self):
        """测试成功提取视觉要点"""
        mock_usage = MagicMock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 30
        mock_usage.total_tokens = 80
        mock_usage.model = "gpt-4o"

        mock_llm_service = AsyncMock()
        mock_llm_service.extract_visual_points.return_value = (
            ["视觉要点1: 核心架构图", "视觉要点2: 数据流"],
            mock_usage,
        )

        with patch("app.graph.nodes.visualizer.get_llm_service", return_value=mock_llm_service):
            state = make_state_with_article()
            result = await extract_visuals_node(state)

        assert result["status"] == "visuals_extracted"
        assert len(result["visual_points"]) == 2
        assert result["error"] == ""

    @pytest.mark.asyncio
    async def test_extract_visuals_empty_article(self):
        """测试文章内容为空"""
        state = make_state_with_article()
        state["article_content"] = ""

        result = await extract_visuals_node(state)

        assert result["status"] == "error"
        assert "文章内容为空" in result["error"]
        assert result["visual_points"] == []

    @pytest.mark.asyncio
    async def test_extract_visuals_failure(self):
        """测试提取视觉要点失败"""
        mock_llm_service = AsyncMock()
        mock_llm_service.extract_visual_points.side_effect = Exception("API 调用失败")

        with patch("app.graph.nodes.visualizer.get_llm_service", return_value=mock_llm_service):
            state = make_state_with_article()
            result = await extract_visuals_node(state)

        assert result["status"] == "error"
        assert "API 调用失败" in result["error"]
        assert result["visual_points"] == []


class TestGenerateImagesNode:
    """生成配图节点测试"""

    @pytest.mark.asyncio
    async def test_generate_images_success(self):
        """测试成功生成配图"""
        mock_image_service = AsyncMock()
        mock_image_service.generate_images.return_value = [
            "http://localhost:8000/static/images/test1.png",
            "http://localhost:8000/static/images/test2.png",
        ]

        with patch("app.graph.nodes.visualizer.get_image_service", return_value=mock_image_service):
            state = make_state_with_article()
            state["visual_points"] = ["视觉要点1", "视觉要点2"]
            result = await generate_images_node(state)

        assert result["status"] == "completed"
        assert len(result["image_urls"]) == 2
        assert result["error"] == ""

    @pytest.mark.asyncio
    async def test_generate_images_empty_visual_points(self):
        """测试视觉要点为空"""
        state = make_state_with_article()
        state["visual_points"] = []

        result = await generate_images_node(state)

        assert result["status"] == "completed"
        assert result["image_urls"] == []
        assert "视觉要点为空" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_images_partial_failure(self):
        """测试部分配图生成失败"""
        mock_image_service = AsyncMock()
        mock_image_service.generate_images.return_value = [
            "http://localhost:8000/static/images/test1.png",
        ]

        with patch("app.graph.nodes.visualizer.get_image_service", return_value=mock_image_service):
            state = make_state_with_article()
            state["visual_points"] = ["视觉要点1", "视觉要点2"]
            result = await generate_images_node(state)

        assert result["status"] == "completed"
        assert len(result["image_urls"]) == 1
        assert "部分配图生成失败" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_images_all_failure(self):
        """测试全部配图生成失败"""
        mock_image_service = AsyncMock()
        mock_image_service.generate_images.side_effect = Exception("API 调用失败")

        with patch("app.graph.nodes.visualizer.get_image_service", return_value=mock_image_service):
            state = make_state_with_article()
            state["visual_points"] = ["视觉要点1", "视觉要点2"]
            result = await generate_images_node(state)

        assert result["status"] == "completed"
        assert result["image_urls"] == []
        assert "配图生成失败" in result["error"]
