"""
安全模块单元测试
测试 JWT 认证与密码处理
"""

from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHash:
    """密码哈希测试"""

    def test_hash_password(self):
        """测试密码哈希生成"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert hashed.startswith("$argon2") or hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        """测试正确密码验证"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """测试错误密码验证"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes(self):
        """测试相同密码生成不同哈希（salt 不同）"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # argon2 使用随机 salt，所以哈希应该不同
        assert hash1 != hash2


class TestJWTToken:
    """JWT Token 测试"""

    def test_create_and_decode_token(self):
        """测试创建和解码 token"""
        data = {"sub": "user123"}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert "exp" in decoded

    def test_token_with_custom_expiry(self):
        """测试自定义过期时间"""
        data = {"sub": "user123"}
        expires = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires)

        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"

    def test_invalid_token(self):
        """测试无效 token"""
        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_expired_token(self):
        """测试过期 token"""
        data = {"sub": "user123"}
        # 创建已过期的 token
        expires = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires)

        result = decode_access_token(token)
        assert result is None

    def test_token_contains_data(self):
        """测试 token 包含自定义数据"""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"
