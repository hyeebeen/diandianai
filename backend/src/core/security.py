from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import get_settings
from .database import get_db

settings = get_settings()
security = HTTPBearer()

# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


class MultiTenantMiddleware:
    """多租户中间件"""

    async def __call__(self, request: Request, call_next):
        # 提取租户ID
        tenant_id = await self.extract_tenant_id(request)
        if not tenant_id:
            raise HTTPException(status_code=401, detail="Missing tenant context")

        # 设置请求状态中的租户ID
        request.state.tenant_id = tenant_id

        response = await call_next(request)
        return response

    async def extract_tenant_id(self, request: Request) -> Optional[str]:
        """从请求中提取租户ID"""
        # 从Authorization头中提取JWT token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload.get("tenant_id")
        except JWTError:
            return None


async def get_current_tenant(request: Request) -> str:
    """获取当前请求的租户ID"""
    if hasattr(request.state, "tenant_id"):
        return request.state.tenant_id
    raise HTTPException(status_code=401, detail="Tenant context not found")


async def get_db_with_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    """获取带租户上下文的数据库会话"""
    tenant_id = await get_current_tenant(request)

    # 设置会话级租户上下文
    await db.execute(
        text("SET app.current_tenant_id = :tenant_id"),
        {"tenant_id": tenant_id}
    )

    return db


def create_access_token(data: Dict[str, Any]) -> str:
    """创建访问令牌"""
    import datetime

    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """验证JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def set_tenant_context(session: AsyncSession, tenant_id: str):
    """设置数据库会话的租户上下文"""
    await session.execute(
        text("SET app.current_tenant_id = :tenant_id"),
        {"tenant_id": tenant_id}
    )