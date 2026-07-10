"""
认证 API - 登录与注册
"""


from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_session
from app.core.security import create_access_token, get_password_hash_async, verify_password_async
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============== 请求/响应模型 ==============


class RegisterRequest(BaseModel):
    """注册请求"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class LoginRequest(BaseModel):
    """登录请求"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应"""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token 类型")


class UserInfoResponse(BaseModel):
    """用户信息响应"""

    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")


class MessageResponse(BaseModel):
    """消息响应"""

    message: str = Field(..., description="消息内容")


# ============== API 接口 ==============


@router.post("/register", response_model=MessageResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_async_session)) -> MessageResponse:
    """
    用户注册

    Args:
        request: 包含 username 和 password 的请求体
        db: 数据库会话

    Returns:
        注册成功消息
    """
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == request.username))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    # 创建新用户
    password_hash = await get_password_hash_async(request.password)
    new_user = User(username=request.username, password_hash=password_hash)

    db.add(new_user)
    await db.commit()

    return MessageResponse(message="注册成功")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_async_session)) -> TokenResponse:
    """
    用户登录

    Args:
        request: 包含 username 和 password 的请求体
        db: 数据库会话

    Returns:
        JWT access token
    """
    # 查询用户
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    # 验证用户和密码
    if not user or not await verify_password_async(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建 token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserInfoResponse:
    """
    获取当前登录用户信息

    Args:
        current_user: 当前登录用户

    Returns:
        用户信息
    """
    return UserInfoResponse(id=str(current_user.id), username=current_user.username)
