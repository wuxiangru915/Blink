"""
检索节点单元测试
测试 RAG 检索节点的降级逻辑和正常检索
"""

from unittest.mock import AsyncMock, MagicMock, patch


class TestRetrieveNode:
    """测试 retrieve_node 函数"""

    async def test_retrieve_no_rag(self):
        """无 ChromaDB 时降级返回空列表（mock ImportError）"""
        from app.graph.nodes.retriever import retrieve_node

        # 将 rag_service 模块设为 None 触发 ImportError
        with patch.dict("sys.modules", {"app.services.rag_service": None}):
            result = await retrieve_node({"selected_topic": "AI技术"})

        assert result["retrieved_docs"] == []
        assert result["status"] == "retrieve_skipped"

    async def test_retrieve_success(self):
        """正常检索返回文档列表"""
        from app.graph.nodes.retriever import retrieve_node

        # 构造 mock RAG 服务
        mock_rag = AsyncMock()
        doc1 = MagicMock(content="AI技术发展趋势", source="article-001", score=0.9)
        doc2 = MagicMock(content="机器学习入门指南", source="article-002", score=0.8)
        mock_rag.retrieve.return_value = [doc1, doc2]

        # 构造 mock 模块替换真实 rag_service
        mock_module = MagicMock()
        mock_module.get_rag_service = MagicMock(return_value=mock_rag)

        with patch.dict("sys.modules", {"app.services.rag_service": mock_module}):
            result = await retrieve_node({"selected_topic": "AI技术"})

        assert result["status"] == "retrieved"
        assert len(result["retrieved_docs"]) == 2
        assert result["retrieved_docs"][0]["content"] == "AI技术发展趋势"
        assert result["retrieved_docs"][0]["source"] == "article-001"
        assert result["retrieved_docs"][0]["score"] == 0.9

    async def test_retrieve_failure(self):
        """检索异常时返回空列表"""
        from app.graph.nodes.retriever import retrieve_node

        # 构造 mock RAG 服务，retrieve 抛出异常
        mock_rag = AsyncMock()
        mock_rag.retrieve.side_effect = Exception("Connection failed")

        mock_module = MagicMock()
        mock_module.get_rag_service = MagicMock(return_value=mock_rag)

        with patch.dict("sys.modules", {"app.services.rag_service": mock_module}):
            result = await retrieve_node({"selected_topic": "AI技术"})

        assert result["retrieved_docs"] == []
        assert result["status"] == "retrieve_failed"
