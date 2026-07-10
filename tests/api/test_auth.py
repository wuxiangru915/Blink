"""
认证 API 端点测试
测试注册、登录、获取用户信息等接口
"""

import pytest

from app.core.db import get_async_session
from app.main import app


@pytest.fixture(autouse=True)
async def override_db(db_session):
    """覆盖数据库依赖，使用内存 SQLite"""

    async def get_session_override():
        yield db_session

    app.dependency_overrides[get_async_session] = get_session_override
    yield
    app.dependency_overrides.clear()


class TestAuthRegister:
    """测试注册接口 POST /api/v1/auth/register"""

    async def test_register_success(self, client):
        """注册成功返回 200"""
        resp = await client.post(
            "/api/v1/auth/register",
            json={"username": "newuser123", "password": "Password123!"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "注册成功"

    async def test_register_duplicate(self, client):
        """重复用户名返回 400"""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "dupuser", "password": "Password123!"},
        )
        resp = await client.post(
            "/api/v1/auth/register",
            json={"username": "dupuser", "password": "Password123!"},
        )
        assert resp.status_code == 400


class TestAuthLogin:
    """测试登录接口 POST /api/v1/auth/login"""

    async def test_login_success(self, client):
        """登录成功返回 access_token"""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "loginuser", "password": "Password123!"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "loginuser", "password": "Password123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        """错误密码返回 401"""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "wrongpwuser", "password": "Password123!"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "wrongpwuser", "password": "WrongPassword!"},
        )
        assert resp.status_code == 401


class TestAuthMe:
    """测试获取当前用户信息 GET /api/v1/auth/me"""

    async def test_get_current_user(self, client, auth_headers):
        """带 token 获取用户信息"""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "username" in data

    async def test_get_current_user_no_token(self, client):
        """无 token 返回 401"""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401
