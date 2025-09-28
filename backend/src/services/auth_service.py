from datetime import datetime, timedelta
from typing import Optional, Tuple
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from core.config import Settings
from core.database import get_session
from core.security import set_tenant_context
from models.users import User, RefreshToken, UserRole
from models.base import Tenant


class AuthenticationError(Exception):
    """Authentication related exceptions"""
    pass


class AuthService:
    """Authentication service for user management and JWT tokens"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.settings.jwt_secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self) -> str:
        """创建刷新令牌"""
        return str(uuid.uuid4())

    def verify_token(self, token: str) -> Optional[dict]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.settings.jwt_secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    async def authenticate_user(self, session: AsyncSession, email: str, password: str, tenant_id: str) -> Optional[User]:
        """用户密码认证"""
        try:
            # Set tenant context first
            await set_tenant_context(session, tenant_id)

            # Find user by email
            stmt = select(User).where(User.email == email).options(selectinload(User.tenant))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            if not self.verify_password(password, user.password_hash):
                return None

            # Check if user is active
            if not user.is_active:
                raise AuthenticationError("User account is disabled")

            return user

        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    async def create_user(
        self,
        session: AsyncSession,
        tenant_id: str,
        email: str,
        password: str,
        username: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        role: UserRole = UserRole.CUSTOMER
    ) -> User:
        """创建新用户"""
        try:
            # Set tenant context
            await set_tenant_context(session, tenant_id)

            # Check if email already exists
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise AuthenticationError("Email already registered")

            # Create new user
            hashed_password = self.get_password_hash(password)
            new_user = User(
                tenant_id=uuid.UUID(tenant_id),
                email=email,
                username=username,
                password_hash=hashed_password,
                full_name=full_name,
                phone=phone,
                role=role,
                is_active=True,
                is_verified=False,
                login_count="0"
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            return new_user

        except Exception as e:
            await session.rollback()
            raise AuthenticationError(f"User creation failed: {str(e)}")

    async def login_user(
        self,
        session: AsyncSession,
        email: str,
        password: str,
        tenant_id: str,
        device_info: Optional[str] = None
    ) -> Tuple[str, str, User]:
        """用户登录，返回访问令牌、刷新令牌和用户信息"""
        try:
            # Authenticate user
            user = await self.authenticate_user(session, email, password, tenant_id)
            if not user:
                raise AuthenticationError("Invalid email or password")

            # Create tokens
            access_token_data = {
                "sub": str(user.id),
                "email": user.email,
                "tenant_id": tenant_id,
                "role": user.role.value if user.role else "customer"
            }
            access_token = self.create_access_token(access_token_data)
            refresh_token_str = self.create_refresh_token()

            # Store refresh token in database
            refresh_token = RefreshToken(
                tenant_id=uuid.UUID(tenant_id),
                token=refresh_token_str,
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
                device_info=device_info
            )
            session.add(refresh_token)

            # Update user login info
            user.last_login_at = datetime.utcnow()
            user.login_count = str(int(user.login_count or "0") + 1)

            await session.commit()

            return access_token, refresh_token_str, user

        except Exception as e:
            await session.rollback()
            raise AuthenticationError(f"Login failed: {str(e)}")

    async def refresh_access_token(
        self,
        session: AsyncSession,
        refresh_token_str: str,
        tenant_id: str
    ) -> Tuple[str, str]:
        """使用刷新令牌获取新的访问令牌"""
        try:
            # Set tenant context
            await set_tenant_context(session, tenant_id)

            # Find refresh token
            stmt = (
                select(RefreshToken)
                .where(RefreshToken.token == refresh_token_str)
                .where(RefreshToken.is_revoked == False)
                .options(selectinload(RefreshToken.user))
            )
            result = await session.execute(stmt)
            refresh_token = result.scalar_one_or_none()

            if not refresh_token:
                raise AuthenticationError("Invalid refresh token")

            # Check if token is expired
            if refresh_token.expires_at < datetime.utcnow():
                raise AuthenticationError("Refresh token expired")

            # Create new access token
            user = refresh_token.user
            access_token_data = {
                "sub": str(user.id),
                "email": user.email,
                "tenant_id": tenant_id,
                "role": user.role.value if user.role else "customer"
            }
            access_token = self.create_access_token(access_token_data)

            # Create new refresh token
            new_refresh_token_str = self.create_refresh_token()

            # Revoke old refresh token
            refresh_token.is_revoked = True

            # Create new refresh token
            new_refresh_token = RefreshToken(
                tenant_id=uuid.UUID(tenant_id),
                token=new_refresh_token_str,
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
                device_info=refresh_token.device_info
            )
            session.add(new_refresh_token)

            await session.commit()

            return access_token, new_refresh_token_str

        except Exception as e:
            await session.rollback()
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

    async def logout_user(
        self,
        session: AsyncSession,
        refresh_token_str: str,
        tenant_id: str
    ) -> bool:
        """用户登出，撤销刷新令牌"""
        try:
            # Set tenant context
            await set_tenant_context(session, tenant_id)

            # Revoke refresh token
            stmt = (
                update(RefreshToken)
                .where(RefreshToken.token == refresh_token_str)
                .where(RefreshToken.is_revoked == False)
                .values(is_revoked=True)
            )
            result = await session.execute(stmt)
            await session.commit()

            return result.rowcount > 0

        except Exception as e:
            await session.rollback()
            raise AuthenticationError(f"Logout failed: {str(e)}")

    async def get_current_user(
        self,
        session: AsyncSession,
        token: str,
        tenant_id: str
    ) -> Optional[User]:
        """根据访问令牌获取当前用户"""
        try:
            # Verify token
            payload = self.verify_token(token)
            if not payload:
                return None

            # Check token type
            if payload.get("type") != "access":
                return None

            # Set tenant context
            await set_tenant_context(session, tenant_id)

            # Get user
            user_id = payload.get("sub")
            if not user_id:
                return None

            stmt = select(User).where(User.id == uuid.UUID(user_id)).options(selectinload(User.tenant))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            return user

        except Exception:
            return None

    async def update_user_profile(
        self,
        session: AsyncSession,
        user_id: str,
        tenant_id: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> User:
        """更新用户资料"""
        try:
            # Set tenant context
            await set_tenant_context(session, tenant_id)

            # Get user
            stmt = select(User).where(User.id == uuid.UUID(user_id))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise AuthenticationError("User not found")

            # Update fields
            if full_name is not None:
                user.full_name = full_name
            if phone is not None:
                user.phone = phone
            if avatar_url is not None:
                user.avatar_url = avatar_url

            await session.commit()
            await session.refresh(user)

            return user

        except Exception as e:
            await session.rollback()
            raise AuthenticationError(f"Profile update failed: {str(e)}")

    async def change_password(
        self,
        session: AsyncSession,
        user_id: str,
        tenant_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """修改用户密码"""
        try:
            # Set tenant context
            await set_tenant_context(session, tenant_id)

            # Get user
            stmt = select(User).where(User.id == uuid.UUID(user_id))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise AuthenticationError("User not found")

            # Verify current password
            if not self.verify_password(current_password, user.password_hash):
                raise AuthenticationError("Current password is incorrect")

            # Update password
            user.password_hash = self.get_password_hash(new_password)

            # Revoke all refresh tokens for this user
            stmt = (
                update(RefreshToken)
                .where(RefreshToken.user_id == user.id)
                .where(RefreshToken.is_revoked == False)
                .values(is_revoked=True)
            )
            await session.execute(stmt)

            await session.commit()

            return True

        except Exception as e:
            await session.rollback()
            raise AuthenticationError(f"Password change failed: {str(e)}")

    # WeChat OAuth integration placeholder
    async def authenticate_wechat(
        self,
        session: AsyncSession,
        wechat_code: str,
        tenant_id: str
    ) -> Tuple[str, str, User]:
        """微信OAuth认证（占位符实现）"""
        # TODO: Implement WeChat OAuth flow
        # 1. Exchange code for access_token and openid
        # 2. Get user info from WeChat API
        # 3. Find or create user account
        # 4. Generate JWT tokens

        raise NotImplementedError("WeChat OAuth authentication not implemented yet")


# Global auth service instance
def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    from core.config import get_settings
    settings = get_settings()
    return AuthService(settings)