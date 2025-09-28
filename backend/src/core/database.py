from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from .config import get_settings

settings = get_settings()

# 创建异步数据库引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    poolclass=NullPool,  # 对于异步使用建议使用NullPool
    pool_pre_ping=True,
    pool_recycle=300,
)

# 创建会话制造器
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """数据库会话上下文管理器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def set_tenant_context(session: AsyncSession, tenant_id: str):
    """设置当前会话的租户上下文"""
    await session.execute(
        f"SET app.current_tenant_id = '{tenant_id}'"
    )


# Alias for compatibility with auth service
get_session = get_db


async def create_tables():
    """创建数据库表"""
    from models.base import Base

    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


def get_engine():
    """获取数据库引擎"""
    return engine