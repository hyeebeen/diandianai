from sqlalchemy import Column, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import BaseModel, Base


class UserRole(enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    MANAGER = "manager"
    DRIVER = "driver"
    CUSTOMER = "customer"
    DISPATCHER = "dispatcher"


class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"

    username = Column(String(50), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # 用户信息
    full_name = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String(500))

    # 角色和状态
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # 登录信息
    last_login_at = Column(DateTime(timezone=True))
    login_count = Column(String(10), default="0")  # 使用字符串存储数字

    # 外键关系
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # 关联关系
    tenant = relationship("Tenant", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    ai_conversations = relationship("AIConversation", back_populates="user")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role}')>"


class RefreshToken(BaseModel):
    """刷新令牌模型"""
    __tablename__ = "refresh_tokens"

    token = Column(String(500), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    device_info = Column(String(500))  # 设备信息

    # 关联关系
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(user_id='{self.user_id}', expires_at='{self.expires_at}')>"


# 更新Base模型以添加反向关系
from .base import Tenant
Tenant.users = relationship("User", back_populates="tenant")