"""
FastAPI应用主程序
AI驱动的物流管理数字化平台
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 添加src目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import get_settings
from core.database import create_tables, get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    settings = get_settings()
    print(f"🚀 Starting FastAPI application")
    print(f"📊 Environment: {settings.environment}")
    print(f"🗄️  Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'Not configured'}")

    # 创建数据库表
    try:
        await create_tables()
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

    yield

    # 关闭时
    print("🛑 Shutting down FastAPI application")


# 创建FastAPI应用
def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    settings = get_settings()

    app = FastAPI(
        title="AI驱动的物流管理数字化平台",
        description="基于FastAPI + Instructor + Celery的智能物流管理系统",
        version="0.1.0",
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url="/redoc" if settings.environment == "development" else None,
        lifespan=lifespan
    )

    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    register_routes(app)

    # 注册异常处理器
    register_exception_handlers(app)

    return app


def register_routes(app: FastAPI):
    """注册所有路由"""
    settings = get_settings()  # 获取设置实例

    # 导入已实现的路由
    from api.auth import router as auth_router
    from api.ai import router as ai_router
    from api.simple_ai import router as simple_ai_router
    from api.logistics import router as logistics_router
    from api.sse import router as sse_router
    from api.admin import router as admin_router

    # 注册已实现的路由
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(ai_router, prefix="/api/ai", tags=["AI Assistant"])
    app.include_router(simple_ai_router, prefix="/api/ai", tags=["Simple AI Chat"])  # 简化AI服务
    app.include_router(logistics_router, prefix="/api/shipments", tags=["Logistics"])
    app.include_router(sse_router, prefix="/api/gps", tags=["GPS & Tracking"])
    app.include_router(admin_router, prefix="/api/admin", tags=["Administration"])

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "service": "diandian-logistics-api",
            "version": "0.1.0"
        }

    @app.get("/")
    async def root():
        """根端点"""
        return {
            "message": "AI驱动的物流管理数字化平台 API",
            "docs": "/docs",
            "health": "/health"
        }

    # 开发环境测试端点 - 不需要认证
    if settings.environment == "development":
        @app.get("/api/test/shipments")
        async def test_shipments():
            """测试端点 - 获取运单数据（无需认证）"""
            from core.database import get_session
            from models.logistics import Shipment
            from sqlalchemy import select

            async for session in get_session():
                try:
                    # 查询运单数据
                    stmt = select(Shipment).limit(10)
                    result = await session.execute(stmt)
                    shipments = result.scalars().all()

                    return {
                        "count": len(shipments),
                        "shipments": [
                            {
                                "id": str(shipment.id),
                                "shipment_number": shipment.shipment_number,
                                "status": shipment.status.value if shipment.status else "pending",
                                "sender": {
                                    "name": shipment.customer_name or "发货人",
                                    "phone": "13800138000",
                                    "company": shipment.customer_name or "发货公司"
                                },
                                "sender_address": {
                                    "address": shipment.pickup_address or "发货地址",
                                    "latitude": 22.5431 if shipment.pickup_address and "深圳" in shipment.pickup_address else
                                               31.2304 if shipment.pickup_address and "上海" in shipment.pickup_address else
                                               39.9042 if shipment.pickup_address and "北京" in shipment.pickup_address else
                                               23.1291 if shipment.pickup_address and "广州" in shipment.pickup_address else 22.5431,
                                    "longitude": 114.0579 if shipment.pickup_address and "深圳" in shipment.pickup_address else
                                                121.4737 if shipment.pickup_address and "上海" in shipment.pickup_address else
                                                116.4074 if shipment.pickup_address and "北京" in shipment.pickup_address else
                                                113.2644 if shipment.pickup_address and "广州" in shipment.pickup_address else 114.0579,
                                    "city": "深圳" if shipment.pickup_address and "深圳" in shipment.pickup_address else
                                           "上海" if shipment.pickup_address and "上海" in shipment.pickup_address else
                                           "北京" if shipment.pickup_address and "北京" in shipment.pickup_address else
                                           "广州" if shipment.pickup_address and "广州" in shipment.pickup_address else "深圳",
                                    "district": "宝安区" if shipment.pickup_address and "深圳" in shipment.pickup_address else
                                               "浦东新区" if shipment.pickup_address and "上海" in shipment.pickup_address else
                                               "朝阳区" if shipment.pickup_address and "北京" in shipment.pickup_address else
                                               "天河区" if shipment.pickup_address and "广州" in shipment.pickup_address else "宝安区"
                                },
                                "receiver": {
                                    "name": "收货人",
                                    "phone": "13900139000",
                                    "company": "收货公司"
                                },
                                "receiver_address": {
                                    "address": shipment.delivery_address or "收货地址",
                                    "latitude": 31.2304 if shipment.delivery_address and "上海" in shipment.delivery_address else
                                               22.5431 if shipment.delivery_address and "深圳" in shipment.delivery_address else
                                               39.9042 if shipment.delivery_address and "北京" in shipment.delivery_address else
                                               23.1291 if shipment.delivery_address and "广州" in shipment.delivery_address else 31.2304,
                                    "longitude": 121.4737 if shipment.delivery_address and "上海" in shipment.delivery_address else
                                                114.0579 if shipment.delivery_address and "深圳" in shipment.delivery_address else
                                                116.4074 if shipment.delivery_address and "北京" in shipment.delivery_address else
                                                113.2644 if shipment.delivery_address and "广州" in shipment.delivery_address else 121.4737,
                                    "city": "上海" if shipment.delivery_address and "上海" in shipment.delivery_address else
                                           "深圳" if shipment.delivery_address and "深圳" in shipment.delivery_address else
                                           "北京" if shipment.delivery_address and "北京" in shipment.delivery_address else
                                           "广州" if shipment.delivery_address and "广州" in shipment.delivery_address else "上海",
                                    "district": "浦东新区" if shipment.delivery_address and "上海" in shipment.delivery_address else
                                               "宝安区" if shipment.delivery_address and "深圳" in shipment.delivery_address else
                                               "朝阳区" if shipment.delivery_address and "北京" in shipment.delivery_address else
                                               "天河区" if shipment.delivery_address and "广州" in shipment.delivery_address else "浦东新区"
                                },
                                "cargo": {
                                    "description": shipment.commodity_type or "货物",
                                    "weight": float(shipment.weight_kg) if shipment.weight_kg else 10.0,
                                    "quantity": 1,
                                    "volume": 1.0,
                                    "value": 1000.0
                                },
                                "special_requirements": [],
                                "created_at": shipment.created_at.isoformat() if shipment.created_at else "2025-01-01T00:00:00",
                                "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else "2025-01-01T00:00:00",
                                "current_location": None,
                                "status_history": []
                            }
                            for shipment in shipments
                        ]
                    }
                except Exception as e:
                    return {"error": str(e), "count": 0, "shipments": []}


def register_exception_handlers(app: FastAPI):
    """注册异常处理器"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """HTTP异常处理"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": f"HTTP_{exc.status_code}",
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """请求验证异常处理"""
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed",
                "code": "VALIDATION_ERROR",
                "errors": exc.errors(),
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理"""
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "code": "INTERNAL_ERROR",
                "path": str(request.url.path)
            }
        )


# 创建应用实例
app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_level="info"
    )