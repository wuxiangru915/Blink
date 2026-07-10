"""
RAG API 端点测试
使用 mock 避免依赖 ChromaDB
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_rag_service():
    """Mock RAG 服务"""
    mock = AsyncMock()

    # index_document 返回分块数
    mock.index_document.return_value = 3

    # retrieve 返回模拟文档
    doc1 = MagicMock(content="AI 技术发展趋势", source="article-001", score=0.85)
    doc2 = MagicMock(content="机器学习入门指南", source="article-002", score=0.72)
    mock.retrieve.return_value = [doc1, doc2]

    return mock


class TestRAGIndexEndpoint:
    """测试 POST /api/v1/rag/index"""

    @pytest.mark.asyncio
    async def test_index_document_success(self, mock_rag_service):
        with patch("app.api.v1.rag.get_rag_service", return_value=mock_rag_service):
            from app.api.v1.rag import index_document, IndexDocumentRequest

            req = IndexDocumentRequest(content="这是一篇测试文章", source="test.md")
            result = await index_document(req)

            assert result.success is True
            assert result.chunks == 3
            assert result.source == "test.md"
            mock_rag_service.index_document.assert_called_once_with("这是一篇测试文章", source="test.md")

    @pytest.mark.asyncio
    async def test_index_document_default_source(self, mock_rag_service):
        with patch("app.api.v1.rag.get_rag_service", return_value=mock_rag_service):
            from app.api.v1.rag import index_document, IndexDocumentRequest

            req = IndexDocumentRequest(content="测试内容")
            result = await index_document(req)

            assert result.source == "manual"


class TestRAGRetrieveEndpoint:
    """测试 POST /api/v1/rag/retrieve"""

    @pytest.mark.asyncio
    async def test_retrieve_success(self, mock_rag_service):
        with patch("app.api.v1.rag.get_rag_service", return_value=mock_rag_service):
            from app.api.v1.rag import retrieve_documents, RetrieveRequest

            req = RetrieveRequest(query="AI技术", k=3)
            result = await retrieve_documents(req)

            assert result.count == 2
            assert result.query == "AI技术"
            assert result.results[0].content == "AI 技术发展趋势"
            assert result.results[0].score == 0.85
            mock_rag_service.retrieve.assert_called_once_with("AI技术", k=3)

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self, mock_rag_service):
        mock_rag_service.retrieve.return_value = []
        with patch("app.api.v1.rag.get_rag_service", return_value=mock_rag_service):
            from app.api.v1.rag import retrieve_documents, RetrieveRequest

            req = RetrieveRequest(query="不存在的查询")
            result = await retrieve_documents(req)

            assert result.count == 0
            assert result.results == []


class TestRAGStatsEndpoint:
    """测试 GET /api/v1/rag/stats"""

    @pytest.mark.asyncio
    async def test_stats_success(self):
        mock_rag = MagicMock()
        mock_vectorstore = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42
        mock_vectorstore._collection = mock_collection
        mock_rag._get_vectorstore.return_value = mock_vectorstore
        mock_rag.collection_name = "reference_articles"
        mock_rag.persist_dir = "./data/chromadb"

        with patch("app.api.v1.rag.get_rag_service", return_value=mock_rag):
            from app.api.v1.rag import get_stats

            result = await get_stats()

            assert result.collection == "reference_articles"
            assert result.document_count == 42
            assert result.persist_dir == "./data/chromadb"
