"""
测试配置 — 共享 fixtures
"""

import os

import pytest

# 在导入 app 之前覆盖环境变量
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("POSTGRES_URI", "postgresql://test:***@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!")
os.environ.setdefault("LLM_API_KEY", "sk-tes...ting")
os.environ.setdefault("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
os.environ.setdefault("LLM_MODEL", "doubao-seed-1-8-251228")
os.environ.setdefault("LLM_MODEL_FAST", "doubao-seed-1-6-flash-250828")
os.environ.setdefault("IMAGE_API_KEY", "test-key")
os.environ.setdefault("IMAGE_BASE_URL", "https://test.example.com")
os.environ.setdefault("IMAGE_MODEL", "test-model")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_CONSOLE", "false")


@pytest.fixture
async def db_session():
    """测试用内存数据库 session"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from app.core.db import Base
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client():
    """异步测试客户端"""
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client):
    """注册并登录，返回 Authorization 头"""
    import uuid
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "TestPassword123!"
    await client.post("/api/v1/auth/register", json={"username": username, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    token = resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}
