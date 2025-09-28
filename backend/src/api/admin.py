"""
管理员API端点
提供系统管理、AI模型配置、任务监控等管理功能
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.celery_app import celery_app
from api.auth import get_current_user
from models.users import User, UserRole
from models.ai_models import AIModelConfig, AIProvider


# Pydantic models for request/response
class AIModelConfigRequest(BaseModel):
    """AI模型配置请求"""
    name: str = Field(..., description="配置名称")
    provider: AIProvider = Field(..., description="AI服务提供商")
    endpoint: str = Field(..., description="API端点URL")
    api_key: str = Field(..., description="API密钥")
    model: str = Field(..., description="模型名称")
    parameters: Optional[Dict[str, Any]] = Field(None, description="模型参数")
    is_active: bool = Field(True, description="是否激活")


class AIModelConfigResponse(BaseModel):
    """AI模型配置响应"""
    id: str
    name: str
    provider: str
    endpoint: str
    model: str
    parameters: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    task_name: str
    status: str
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SystemStatsResponse(BaseModel):
    """系统统计响应"""
    active_users: int
    total_shipments: int
    active_shipments: int
    pending_tasks: int
    system_health: str
    uptime_hours: float


# 创建路由器
router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)):
    """要求管理员权限"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    获取系统统计信息
    """
    try:
        # 这里应该从数据库查询实际统计数据
        # 简化处理，返回模拟数据

        stats = SystemStatsResponse(
            active_users=25,
            total_shipments=1250,
            active_shipments=180,
            pending_tasks=12,
            system_health="healthy",
            uptime_hours=168.5
        )

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )


@router.get("/ai-models", response_model=List[AIModelConfigResponse])
async def get_ai_model_configs(
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    获取AI模型配置列表
    """
    try:
        # TODO: 从数据库查询AI模型配置
        # 这里返回模拟数据
        configs = [
            AIModelConfigResponse(
                id=str(uuid.uuid4()),
                name="OpenAI GPT-4 生产配置",
                provider="openai",
                endpoint="https://api.openai.com/v1",
                model="gpt-4",
                parameters={"temperature": 0.7, "max_tokens": 2000},
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            AIModelConfigResponse(
                id=str(uuid.uuid4()),
                name="通义千问测试配置",
                provider="qwen",
                endpoint="https://dashscope.aliyuncs.com/api/v1",
                model="qwen-turbo",
                parameters={"temperature": 0.5, "max_tokens": 1500},
                is_active=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]

        return configs

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI model configs: {str(e)}"
        )


@router.post("/ai-models", response_model=AIModelConfigResponse)
async def create_ai_model_config(
    request: AIModelConfigRequest,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    创建AI模型配置
    """
    try:
        # TODO: 实际创建到数据库
        config_id = str(uuid.uuid4())

        return AIModelConfigResponse(
            id=config_id,
            name=request.name,
            provider=request.provider.value,
            endpoint=request.endpoint,
            model=request.model,
            parameters=request.parameters,
            is_active=request.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create AI model config: {str(e)}"
        )


@router.get("/tasks/status")
async def get_task_status(
    task_ids: Optional[str] = Query(None, description="任务ID列表，逗号分隔"),
    limit: int = Query(50, ge=1, le=200, description="限制数量"),
    admin_user: User = Depends(require_admin)
):
    """
    获取Celery任务状态
    """
    try:
        if task_ids:
            # 查询指定任务状态
            ids = [tid.strip() for tid in task_ids.split(",")]
            task_statuses = []

            for task_id in ids:
                task_result = celery_app.AsyncResult(task_id)
                task_status = {
                    "task_id": task_id,
                    "status": task_result.status,
                    "result": task_result.result if task_result.successful() else None,
                    "error": str(task_result.result) if task_result.failed() else None,
                    "started_at": None,  # Celery doesn't provide this by default
                    "completed_at": None
                }
                task_statuses.append(task_status)

            return {"tasks": task_statuses}

        else:
            # 获取活跃任务状态（简化处理）
            inspector = celery_app.control.inspect()
            active_tasks = inspector.active()
            scheduled_tasks = inspector.scheduled()

            return {
                "active_tasks": active_tasks,
                "scheduled_tasks": scheduled_tasks,
                "worker_stats": inspector.stats()
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.post("/tasks/trigger")
async def trigger_manual_task(
    task_name: str = Query(..., description="任务名称"),
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    parameters: Optional[str] = Query(None, description="任务参数JSON"),
    admin_user: User = Depends(require_admin)
):
    """
    手动触发任务
    """
    try:
        import json

        # 解析参数
        task_params = json.loads(parameters) if parameters else {}

        # 根据任务名称调用相应的任务
        if task_name == "cleanup_gps_data":
            from tasks.gps_tasks import cleanup_old_gps_data
            result = cleanup_old_gps_data.delay(
                days_to_keep=task_params.get("days_to_keep", 30)
            )

        elif task_name == "generate_ai_summary":
            from tasks.ai_tasks import generate_daily_summary
            result = generate_daily_summary.delay(tenant_id=tenant_id)

        elif task_name == "send_pending_reminders":
            from tasks.notification_tasks import send_pending_reminders
            result = send_pending_reminders.delay()

        elif task_name == "backup_conversations":
            from tasks.ai_tasks import backup_conversation_data
            if not tenant_id:
                raise HTTPException(400, "tenant_id required for this task")
            result = backup_conversation_data.delay(
                tenant_id=tenant_id,
                backup_days=task_params.get("backup_days", 30)
            )

        else:
            raise HTTPException(400, f"Unknown task: {task_name}")

        return {
            "task_id": result.id,
            "task_name": task_name,
            "status": "triggered",
            "parameters": task_params,
            "triggered_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger task: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    admin_user: User = Depends(require_admin)
):
    """
    取消任务
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)

        return {
            "task_id": task_id,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.get("/logs")
async def get_system_logs(
    level: str = Query("INFO", description="日志级别"),
    hours: int = Query(24, ge=1, le=168, description="获取小时数"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    admin_user: User = Depends(require_admin)
):
    """
    获取系统日志
    """
    try:
        # 这里应该从日志文件或日志系统读取
        # 简化处理，返回模拟日志

        logs = [
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "level": "INFO",
                "module": "tasks.gps_tasks",
                "message": "GPS data processing completed",
                "details": {"processed_count": 1250, "errors": 0}
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                "level": "WARNING",
                "module": "tasks.notification_tasks",
                "message": "SMS sending rate limit reached",
                "details": {"retry_after": 60}
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "level": "INFO",
                "module": "tasks.ai_tasks",
                "message": "Daily summary generated",
                "details": {"tenant_count": 5, "summary_count": 5}
            }
        ]

        return {
            "logs": logs[:limit],
            "total_count": len(logs),
            "query_params": {
                "level": level,
                "hours": hours,
                "limit": limit
            },
            "fetched_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system logs: {str(e)}"
        )


@router.post("/maintenance/mode")
async def toggle_maintenance_mode(
    enabled: bool = Query(..., description="是否启用维护模式"),
    message: Optional[str] = Query(None, description="维护消息"),
    admin_user: User = Depends(require_admin)
):
    """
    切换维护模式
    """
    try:
        # 这里应该设置全局维护标志
        # 可以存储在Redis或配置文件中

        maintenance_config = {
            "enabled": enabled,
            "message": message or "System is under maintenance",
            "started_at": datetime.utcnow().isoformat() if enabled else None,
            "started_by": admin_user.username
        }

        # TODO: 保存到Redis或配置存储

        return {
            "maintenance_mode": maintenance_config,
            "previous_state": not enabled,  # 模拟之前的状态
            "changed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle maintenance mode: {str(e)}"
        )


@router.get("/health/detailed")
async def get_detailed_health_check(
    admin_user: User = Depends(require_admin)
):
    """
    获取详细的系统健康检查
    """
    try:
        # 检查各个组件的健康状态
        health_checks = {
            "database": {"status": "healthy", "response_time_ms": 25},
            "redis": {"status": "healthy", "response_time_ms": 12},
            "celery_workers": {"status": "healthy", "active_workers": 4},
            "external_apis": {
                "g7_api": {"status": "healthy", "last_check": datetime.utcnow().isoformat()},
                "wechat_api": {"status": "healthy", "last_check": datetime.utcnow().isoformat()},
                "sms_service": {"status": "degraded", "last_error": "Rate limit reached"}
            },
            "disk_usage": {"status": "healthy", "usage_percent": 45},
            "memory_usage": {"status": "healthy", "usage_percent": 62},
            "cpu_usage": {"status": "healthy", "usage_percent": 35}
        }

        # 计算总体健康状态
        all_services_healthy = all(
            check.get("status") == "healthy"
            for check in health_checks.values()
            if isinstance(check, dict) and "status" in check
        )

        overall_status = "healthy" if all_services_healthy else "degraded"

        return {
            "overall_status": overall_status,
            "checks": health_checks,
            "checked_at": datetime.utcnow().isoformat(),
            "uptime_seconds": 3600 * 24 * 7  # 模拟7天运行时间
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform health check: {str(e)}"
        )