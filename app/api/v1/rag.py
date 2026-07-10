"""
RAG 文档管理接口
支持文本文档索引、文件上传索引、检索测试
"""

import asyncio
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.core.logger import get_logger
from app.services import get_rag_service

logger = get_logger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])


# ============== 请求/响应模型 ==============


class IndexDocumentRequest(BaseModel):
    """索引文本文档"""

    content: str = Field(..., description="文档内容", min_length=1)
    source: str = Field("manual", description="来源标识（如文件名、URL）")


class IndexDocumentResponse(BaseModel):
    chunks: int = Field(..., description="分块数量")
    source: str = Field(..., description="来源标识")
    success: bool


class RetrieveRequest(BaseModel):
    query: str = Field(..., description="检索查询", min_length=1)
    k: int = Field(3, description="返回数量", ge=1, le=20)


class RetrievedDocResponse(BaseModel):
    content: str
    source: str
    score: float


class RetrieveResponse(BaseModel):
    query: str
    results: List[RetrievedDocResponse]
    count: int


class CollectionStatsResponse(BaseModel):
    collection: str
    document_count: int
    persist_dir: str


# ============== 端点 ==============


@router.post("/index", response_model=IndexDocumentResponse)
async def index_document(req: IndexDocumentRequest) -> IndexDocumentResponse:
    """
    索引一篇文本文档

    文档会被分块（500字/块，50字重叠）后存入向量数据库，
    供后续写作时检索参考内容。
    """
    try:
        rag = get_rag_service()
        chunks = await rag.index_document(req.content, source=req.source)
        return IndexDocumentResponse(chunks=chunks, source=req.source, success=True)
    except Exception as e:
        logger.error("文档索引失败", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文档索引失败，请稍后重试",
        )


@router.post("/index-file", response_model=IndexDocumentResponse)
async def index_file(
    file: UploadFile = File(..., description="上传文件（.txt / .md）"),
    source: Optional[str] = Form(None, description="来源标识，默认使用文件名"),
) -> IndexDocumentResponse:
    """
    上传文件并索引

    支持 .txt 和 .md 文件，内容会被分块存入向量数据库。
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("txt", "md"):
        raise HTTPException(status_code=400, detail="仅支持 .txt 和 .md 文件")

    try:
        content = await file.read()
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码不是 UTF-8")

    if not text.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")

    try:
        rag = get_rag_service()
        chunks = await rag.index_document(text, source=source or file.filename)
        return IndexDocumentResponse(
            chunks=chunks,
            source=source or file.filename,
            success=True,
        )
    except Exception as e:
        logger.error("文件索引失败", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件索引失败，请稍后重试",
        )


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(req: RetrieveRequest) -> RetrieveResponse:
    """
    检索相关文档（用于测试）

    用选题关键词检索，预览 RAG 会返回哪些参考内容。
    """
    try:
        rag = get_rag_service()
        docs = await rag.retrieve(req.query, k=req.k)
        results = [
            RetrievedDocResponse(content=d.content, source=d.source, score=d.score)
            for d in docs
        ]
        return RetrieveResponse(query=req.query, results=results, count=len(results))
    except Exception as e:
        logger.error("检索失败", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检索失败，请稍后重试",
        )


@router.get("/stats", response_model=CollectionStatsResponse)
async def get_stats() -> CollectionStatsResponse:
    """查看向量库统计信息"""
    try:
        rag = get_rag_service()
        vectorstore = rag._get_vectorstore()
        collection = vectorstore._collection
        count = await asyncio.to_thread(collection.count)
        return CollectionStatsResponse(
            collection=rag.collection_name,
            document_count=count,
            persist_dir=rag.persist_dir,
        )
    except Exception as e:
        logger.error("获取统计失败", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计失败，请稍后重试",
        )


@router.delete("/clear")
async def clear_documents():
    """清空所有已索引的文档"""
    try:
        rag = get_rag_service()
        vectorstore = rag._get_vectorstore()
        collection = vectorstore._collection

        # 获取所有文档的 ID 并删除
        all_docs = await asyncio.to_thread(collection.get)
        if all_docs["ids"]:
            await asyncio.to_thread(collection.delete, ids=all_docs["ids"])

        return {
            "success": True,
            "deleted": len(all_docs["ids"]),
            "message": f"已清空 {len(all_docs['ids'])} 条文档",
        }
    except Exception as e:
        logger.error("清空失败", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清空失败，请稍后重试",
        )
