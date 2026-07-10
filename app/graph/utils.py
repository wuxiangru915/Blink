"""
LangGraph 工具函数模块
包含 Checkpointer 初始化等工具函数

LangGraph 1.0+ 语法

PostgreSQL 模式：使用 AsyncPostgresSaver，数据持久化到数据库
降级模式：PostgreSQL 不可用时使用 MemorySaver（数据不持久化，仅供本地开发）
"""

import asyncio
from typing import Union

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# 全局 Checkpointer 实例
_checkpointer: Union[BaseCheckpointSaver, None] = None
# 全局连接池实例
_connection_pool = None
_checkpointer_lock = asyncio.Lock()


async def setup_checkpointer() -> BaseCheckpointSaver:
    """
    设置并初始化 Checkpointer

    优先使用 AsyncPostgresSaver (PostgreSQL 持久化)，
    PostgreSQL 不可用时降级为 MemorySaver (内存模式，仅供本地开发)。

    Returns:
        配置好的 Checkpointer 实例
    """
    global _checkpointer, _connection_pool

    if _checkpointer is not None:
        return _checkpointer

    # 尝试连接 PostgreSQL
    try:
        import psycopg
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool

        logger.info(f"Connecting to PostgreSQL: {settings.postgres_uri.split('@')[-1]}")

        async with await psycopg.AsyncConnection.connect(
            settings.postgres_uri, autocommit=True, connect_timeout=3
        ) as setup_conn:
            temp_checkpointer = AsyncPostgresSaver(setup_conn)
            await temp_checkpointer.setup()
            logger.info("Checkpointer tables created/verified")

        _connection_pool = AsyncConnectionPool(
            conninfo=settings.postgres_uri,
            min_size=1,
            max_size=10,
            open=False,
        )
        await _connection_pool.open()
        _checkpointer = AsyncPostgresSaver(_connection_pool)
        logger.info("PostgreSQL Checkpointer initialized - data will persist")

    except Exception as e:
        logger.warning(f"PostgreSQL unavailable, falling back to MemorySaver: {e}")
        _checkpointer = MemorySaver()
        _connection_pool = None
        logger.warning("Using MemorySaver (in-memory) - data will NOT persist on restart")

    return _checkpointer


async def get_checkpointer() -> BaseCheckpointSaver:
    """
    获取已初始化的 Checkpointer 实例

    Returns:
        Checkpointer 实例 (AsyncPostgresSaver)

    Raises:
        RuntimeError: 如果 Checkpointer 未初始化
    """
    global _checkpointer

    if _checkpointer is not None:
        return _checkpointer

    async with _checkpointer_lock:
        if _checkpointer is not None:
            return _checkpointer
        return await setup_checkpointer()


def get_checkpointer_pool():
    """
    获取全局连接池实例

    Returns:
        AsyncConnectionPool 实例，未初始化或 MemorySaver 模式时返回 None
    """
    return _connection_pool


async def close_checkpointer() -> None:
    """
    关闭 Checkpointer 和连接池

    需要关闭连接池释放资源（PostgreSQL 模式）。
    MemorySaver 模式无需清理。
    """
    global _checkpointer, _connection_pool

    if _connection_pool is not None:
        await _connection_pool.close()
        _connection_pool = None
        logger.info("PostgreSQL connection pool closed")

    _checkpointer = None
    logger.info("Cleaned up")
