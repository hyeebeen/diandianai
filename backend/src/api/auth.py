"""
认证API端点
支持密码登录、微信登录、token刷新等功能
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from services.auth_service import AuthService, get_auth_service, AuthenticationError
from models.users import UserRole


# Pydantic models for request/response
class LoginRequest(BaseModel):
    """登录请求模型"""
    identifier: str  # email or username
    password: str


class WeChatLoginRequest(BaseModel):
    """微信登录请求模型"""
    code: str


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER


class RefreshTokenRequest(BaseModel):
    """刷新token请求模型"""
    refresh_token: str


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    tenant_id: str
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes
    user: UserResponse


class RefreshResponse(BaseModel):
    """刷新token响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class UpdateProfileRequest(BaseModel):
    """更新用户资料请求模型"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str
    new_password: str


# 创建路由器
router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session)
):
    """获取当前认证用户的依赖项"""
    try:
        token = credentials.credentials
        user = await auth_service.get_current_user(session, token, x_tenant_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session)
):
    """
    用户登录
    支持email或username + password登录
    """
    try:
        access_token, refresh_token, user = await auth_service.login_user(
            session=session,
            email=request.identifier,  # 假设使用email作为identifier
            password=request.password,
            tenant_id=x_tenant_id,
            device_info=None  # TODO: 从请求头获取设备信息
        )

        user_response = UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role.value if user.role else "customer",
            is_active=user.is_active,
            is_verified=user.is_verified,
            tenant_id=str(user.tenant_id),
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/login/wechat", response_model=LoginResponse)
async def wechat_login(
    request: WeChatLoginRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session)
):
    """
    微信登录
    使用微信授权码登录
    """
    try:
        access_token, refresh_token, user = await auth_service.authenticate_wechat(
            session=session,
            wechat_code=request.code,
            tenant_id=x_tenant_id
        )

        user_response = UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role.value if user.role else "customer",
            is_active=user.is_active,
            is_verified=user.is_verified,
            tenant_id=str(user.tenant_id),
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response
        )

    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WeChat login not implemented yet"
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session)
):
    """
    用户注册
    创建新用户账号
    """
    try:
        user = await auth_service.create_user(
            session=session,
            tenant_id=x_tenant_id,
            email=request.email,
            password=request.password,
            username=request.username,
            full_name=request.full_name,
            phone=request.phone,
            role=request.role
        )

        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role.value if user.role else "customer",
            is_active=user.is_active,
            is_verified=user.is_verified,
            tenant_id=str(user.tenant_id),
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

    except AuthenticationError as e:
        if "already registered" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session)
):
    """
    刷新访问令牌
    使用refresh token获取新的access token
    """
    try:
        access_token, new_refresh_token = await auth_service.refresh_access_token(
            session=session,
            refresh_token_str=request.refresh_token,
            tenant_id=x_tenant_id
        )

        return RefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh_token
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user = Depends(get_current_user)
):
    """
    获取当前用户资料
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role.value if current_user.role else "customer",
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        tenant_id=str(current_user.tenant_id),
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session)
):
    """
    更新用户资料
    """
    try:
        updated_user = await auth_service.update_user_profile(
            session=session,
            user_id=str(current_user.id),
            tenant_id=x_tenant_id,
            full_name=request.full_name,
            phone=request.phone,
            avatar_url=request.avatar_url
        )

        return UserResponse(
            id=str(updated_user.id),
            username=updated_user.username,
            email=updated_user.email,
            full_name=updated_user.full_name,
            phone=updated_user.phone,
            role=updated_user.role.value if updated_user.role else "customer",
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            tenant_id=str(updated_user.tenant_id),
            created_at=updated_user.created_at,
            last_login_at=updated_user.last_login_at
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session)
):
    """
    修改用户密码
    """
    try:
        success = await auth_service.change_password(
            session=session,
            user_id=str(current_user.id),
            tenant_id=x_tenant_id,
            current_password=request.current_password,
            new_password=request.new_password
        )

        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_session)
):
    """
    用户登出
    撤销refresh token
    """
    try:
        success = await auth_service.logout_user(
            session=session,
            refresh_token_str=request.refresh_token,
            tenant_id=x_tenant_id
        )

        if success:
            return {"message": "Logged out successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logout failed"
            )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )