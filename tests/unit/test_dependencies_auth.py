"""
认证依赖单元测试
测试 get_current_user 依赖函数的 token 验证逻辑
"""

from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import create_access_token, get_password_hash
from app.dependencies.auth import get_current_user
from app.models.user import User


class TestGetCurrentUser:
    """测试 get_current_user 函数"""

    async def test_get_current_user_valid_token(self, db_session):
        """有效 token 返回用户"""
        # 创建测试用户
        user = User(username="testuser", password_hash=get_password_hash("Password123!"))
        db_session.add(user)
        await db_session.flush()

        # 创建有效 token
        token = create_access_token(data={"sub": str(user.id)})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        result = await get_current_user(credentials, db_session)

        assert str(result.id) == str(user.id)
        assert result.username == "testuser"

    async def test_get_current_user_invalid_token(self, db_session):
        """无效 token 返回 401"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.here")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)

        assert exc_info.value.status_code == 401

    async def test_get_current_user_expired_token(self, db_session):
        """过期 token 返回 401"""
        # 创建已过期的 token
        token = create_access_token(
            data={"sub": "some-user-id"},
            expires_delta=timedelta(seconds=-1),
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)

        assert exc_info.value.status_code == 401
