"""
RAG 服务单元测试
测试文本分块和基本逻辑（不测试真实向量检索）
"""



class TestRAGServiceChunking:
    """测试文本分块逻辑"""

    def test_text_splitter_initialization(self):
        from app.services.rag_service import RAGService

        service = RAGService()
        splitter = service.text_splitter
        assert splitter is not None
        assert splitter._chunk_size == 500

    def test_text_splitter_splits_long_text(self):
        from app.services.rag_service import RAGService

        service = RAGService()
        long_text = "这是一段测试文本。" * 100  # 900 字符
        chunks = service.text_splitter.split_text(long_text)
        assert len(chunks) > 1

    def test_text_splitter_keeps_short_text(self):
        from app.services.rag_service import RAGService

        service = RAGService()
        short_text = "这是一段短文本。"
        chunks = service.text_splitter.split_text(short_text)
        assert len(chunks) == 1


class TestRetrievedDoc:
    """测试数据结构"""

    def test_retrieved_doc_fields(self):
        from app.services.rag_service import RetrievedDoc

        doc = RetrievedDoc(content="test content", source="test.md", score=0.95)
        assert doc.content == "test content"
        assert doc.source == "test.md"
        assert doc.score == 0.95
