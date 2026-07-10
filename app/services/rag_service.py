"""
RAG 检索增强服务
使用 ChromaDB 作为向量存储，支持文档索引和检索

依赖：pip install -e ".[rag]"
"""

import asyncio
import os
import threading
from dataclasses import dataclass
from typing import List, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedDoc:
    """检索到的文档"""

    content: str
    source: str
    score: float


class RAGService:
    """RAG 检索服务"""

    def __init__(self, collection_name: str = "reference_articles", persist_dir: str = "./data/chromadb"):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self._embeddings = None
        self._vectorstore = None
        self._text_splitter = None

    @property
    def text_splitter(self):
        if self._text_splitter is None:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "],
            )
        return self._text_splitter

    @property
    def embeddings(self):
        if self._embeddings is None:
            from langchain_openai import OpenAIEmbeddings

            self._embeddings = OpenAIEmbeddings(
                model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
                openai_api_key=os.getenv("EMBEDDING_API_KEY"),
                openai_api_base=os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1"),
            )
        return self._embeddings

    def _get_vectorstore(self):
        if self._vectorstore is None:
            import chromadb
            from langchain_chroma import Chroma

            client = chromadb.PersistentClient(path=self.persist_dir)
            self._vectorstore = Chroma(
                client=client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )
        return self._vectorstore

    async def index_document(self, content: str, source: str = "manual") -> int:
        """索引一篇文档，返回分块数"""
        chunks = self.text_splitter.split_text(content)
        if not chunks:
            return 0

        metadatas = [{"source": source, "chunk_idx": i} for i in range(len(chunks))]
        vectorstore = self._get_vectorstore()
        await asyncio.to_thread(vectorstore.add_texts, texts=chunks, metadatas=metadatas)

        logger.info(f"Indexed document: {source}, {len(chunks)} chunks")
        return len(chunks)

    async def retrieve(self, query: str, k: int = 3) -> List[RetrievedDoc]:
        """检索与 query 最相关的 k 篇文档"""
        try:
            vectorstore = self._get_vectorstore()
            results = await asyncio.to_thread(vectorstore.similarity_search_with_score, query, k=k)

            docs = [
                RetrievedDoc(
                    content=doc.page_content,
                    source=doc.metadata.get("source", "unknown"),
                    score=score,
                )
                for doc, score in results
            ]

            logger.info(f"Retrieved {len(docs)} docs for query: {query[:50]}...")
            return docs
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []


_rag_service: Optional[RAGService] = None
_rag_lock = threading.Lock()


def get_rag_service() -> RAGService:
    """获取全局 RAG 服务实例"""
    global _rag_service
    if _rag_service is None:
        with _rag_lock:
            if _rag_service is None:
                _rag_service = RAGService()
    return _rag_service
