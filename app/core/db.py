"""
数据库连接模块
配置 SQLAlchemy AsyncSession
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# 创建异步引擎（SQLite 不支持连接池参数）
_is_sqlite = settings.async_database_url.startswith("sqlite")
engine_kwargs = {"echo": settings.debug}
if not _is_sqlite:
    engine_kwargs.update(pool_pre_ping=True, pool_size=5, max_overflow=10)
engine = create_async_engine(settings.async_database_url, **engine_kwargs)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明基类
Base = declarative_base()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话
    用于 FastAPI 依赖注入
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化数据库（创建表）
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def close_db() -> None:
    """
    关闭数据库连接
    """
    await engine.dispose()
    logger.info("Database connection closed")
