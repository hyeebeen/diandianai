"""
点点精灵API端点
支持智能对话、任务执行、配置管理等功能
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from services.ai_service import AIService, get_ai_service, AIServiceError, LogisticsAction
from api.auth import get_current_user
from models.users import User
from models.ai_models import AIModelConfig, AIProvider


# Pydantic models for request/response
class ChatRequest(BaseModel):
    """AI聊天请求模型"""
    message: str = Field(..., description="用户消息")
    conversation_id: Optional[str] = Field(None, description="对话ID，新对话为None")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文信息")
    model_name: Optional[str] = Field(None, description="指定AI模型名称")
    stream: bool = Field(False, description="是否流式响应")


class ChatResponse(BaseModel):
    """AI聊天响应模型"""
    id: str = Field(description="消息ID")
    conversation_id: str = Field(description="对话ID")
    message: str = Field(description="AI回复内容")
    role: str = Field(description="消息角色")
    timestamp: datetime = Field(description="时间戳")
    confidence: Optional[float] = Field(None, description="置信度")
    suggested_actions: List[str] = Field(default=[], description="建议的后续操作")
    requires_confirmation: bool = Field(False, description="是否需要确认")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ConversationResponse(BaseModel):
    """对话信息响应模型"""
    id: str
    title: str
    last_message: Optional[str] = None
    last_activity_at: datetime
    message_count: int
    is_active: bool


class ConversationsListResponse(BaseModel):
    """对话列表响应模型"""
    conversations: List[ConversationResponse]
    pagination: Dict[str, Any]


class TaskRequest(BaseModel):
    """AI任务请求模型"""
    action: LogisticsAction = Field(description="需要执行的操作")
    parameters: Dict[str, Any] = Field(description="操作参数")
    conversation_id: Optional[str] = Field(None, description="关联对话ID")
    requires_confirmation: bool = Field(True, description="是否需要用户确认")


class TaskResponse(BaseModel):
    """AI任务响应模型"""
    task_id: str
    action: str
    status: str
    result: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class SummaryResponse(BaseModel):
    """AI摘要响应模型"""
    id: str
    period: str
    start_date: str
    end_date: str
    statistics: Dict[str, Any]
    insights: Dict[str, Any]
    generated_at: datetime
    generated_by: str


class AIConfigRequest(BaseModel):
    """AI配置请求模型"""
    name: str = Field(description="配置名称")
    provider: AIProvider = Field(description="AI服务提供商")
    endpoint: str = Field(description="API端点URL")
    api_key: str = Field(description="API密钥")
    model: str = Field(description="模型名称")
    parameters: Optional[Dict[str, Any]] = Field(None, description="模型参数")
    is_active: bool = Field(True, description="是否激活")


class AIConfigResponse(BaseModel):
    """AI配置响应模型"""
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


# 创建路由器
router = APIRouter()
security = HTTPBearer()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    session: AsyncSession = Depends(get_session)
):
    """
    与点点精灵进行对话
    支持新建对话和继续已有对话
    """
    try:
        tenant_id = str(current_user.tenant_id)
        user_id = str(current_user.id)

        # 如果没有对话ID，创建新对话
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation = await ai_service.create_conversation(
                session=session,
                tenant_id=tenant_id,
                user_id=user_id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
                context_data=request.context
            )
            conversation_id = str(conversation.id)

        # 处理流式响应
        if request.stream:
            async def generate_stream():
                try:
                    async for chunk in ai_service.stream_chat_completion(
                        session=session,
                        tenant_id=tenant_id,
                        conversation_id=conversation_id,
                        user_message=request.message,
                        context=request.context,
                        model_name=request.model_name
                    ):
                        yield f"data: {chunk}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )

        # 常规响应
        ai_response = await ai_service.chat_completion(
            session=session,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            user_message=request.message,
            context=request.context,
            model_name=request.model_name
        )

        # 构建响应
        return ChatResponse(
            id=str(uuid.uuid4()),  # 临时ID，实际应从数据库获取
            conversation_id=conversation_id,
            message=ai_response.content,
            role="assistant",
            timestamp=datetime.utcnow(),
            confidence=ai_response.action_request.confidence if ai_response.action_request else None,
            suggested_actions=ai_response.suggested_actions,
            requires_confirmation=ai_response.action_request.requires_confirmation if ai_response.action_request else False,
            metadata={
                "processing_time": 1.5,  # 实际应计算
                "token_count": 100  # 实际应从AI响应获取
            }
        )

    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/conversations", response_model=ConversationsListResponse)
async def get_conversations(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    session: AsyncSession = Depends(get_session)
):
    """
    获取用户的对话列表
    """
    try:
        tenant_id = str(current_user.tenant_id)
        user_id = str(current_user.id)

        conversations = await ai_service.get_user_conversations(
            session=session,
            tenant_id=tenant_id,
            user_id=user_id,
            limit=limit
        )

        # 转换为响应格式
        conversation_responses = []
        for conv in conversations:
            conversation_responses.append(ConversationResponse(
                id=str(conv.id),
                title=conv.title or "未命名对话",
                last_message=None,  # TODO: 获取最后一条消息
                last_activity_at=conv.last_activity_at or conv.created_at,
                message_count=int(conv.message_count or "0"),
                is_active=conv.is_active
            ))

        # 计算分页信息
        total = len(conversations)  # TODO: 实际应查询总数
        pages = (total + limit - 1) // limit

        return ConversationsListResponse(
            conversations=conversation_responses,
            pagination={
                "page": page,
                "limit": limit,
                "total": total,
                "pages": pages
            }
        )

    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


@router.post("/tasks", response_model=TaskResponse)
async def execute_ai_task(
    request: TaskRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    session: AsyncSession = Depends(get_session)
):
    """
    执行AI建议的任务
    """
    try:
        tenant_id = str(current_user.tenant_id)
        user_id = str(current_user.id)

        # 创建AI动作请求
        from services.ai_service import AIActionRequest
        action_request = AIActionRequest(
            action=request.action,
            confidence=0.8,  # 默认置信度
            shipment_info=request.parameters.get("shipment_info"),
            parameters=request.parameters,
            requires_confirmation=request.requires_confirmation,
            reasoning="User requested action execution"
        )

        # 执行任务
        result = await ai_service.execute_action(
            session=session,
            tenant_id=tenant_id,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            action_request=action_request,
            user_id=user_id
        )

        # 构建响应
        task_id = str(uuid.uuid4())
        status_value = "completed" if result["success"] else "failed"

        return TaskResponse(
            task_id=task_id,
            action=request.action.value,
            status=status_value,
            result=result,
            confidence=action_request.confidence,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


@router.get("/summary", response_model=SummaryResponse)
async def get_ai_summary(
    period: str = Query("weekly", regex="^(daily|weekly|monthly)$", description="摘要周期"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    获取AI交互摘要报告
    """
    try:
        # 计算默认日期范围
        if not start_date or not end_date:
            today = date.today()
            if period == "daily":
                start_date = end_date = today
            elif period == "weekly":
                # 本周
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            else:  # monthly
                # 本月
                start_date = today.replace(day=1)
                next_month = today.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day)

        # TODO: 实现实际的摘要生成逻辑
        # 这里使用模拟数据
        summary_data = {
            "id": str(uuid.uuid4()),
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "statistics": {
                "total_interactions": 45,
                "shipments_created": 8,
                "shipments_completed": 6,
                "average_response_time": 1.8,
                "success_rate": 0.89
            },
            "insights": {
                "key_topics": ["运单创建", "货物追踪", "状态更新"],
                "common_tasks": ["创建北京到上海运单", "查询货物位置"],
                "suggestions": ["建议增加自动回复功能", "优化常见查询流程"],
                "trends": [
                    {
                        "metric": "interactions",
                        "change": 12.5,
                        "direction": "up"
                    }
                ]
            },
            "generated_at": datetime.utcnow(),
            "generated_by": "ai-analyst-v1.0"
        }

        return SummaryResponse(**summary_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


# AI配置管理端点（管理员功能）
@router.get("/config", response_model=List[AIConfigResponse])
async def get_ai_configs(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    获取AI模型配置列表
    普通用户只能看到激活的配置，管理员可以看到所有配置
    """
    try:
        # TODO: 实现配置查询逻辑
        # 这里返回模拟数据
        configs = [
            AIConfigResponse(
                id=str(uuid.uuid4()),
                name="OpenAI GPT-4 生产配置",
                provider="openai",
                endpoint="https://api.openai.com/v1",
                model="gpt-4",
                parameters={"temperature": 0.7, "max_tokens": 2000},
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]

        return configs

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI configs: {str(e)}"
        )


@router.post("/config", response_model=AIConfigResponse)
async def create_ai_config(
    request: AIConfigRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    创建AI模型配置（仅管理员）
    """
    # 检查管理员权限
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    try:
        # TODO: 实现配置创建逻辑
        # 这里返回模拟响应
        config_id = str(uuid.uuid4())

        return AIConfigResponse(
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
            detail=f"Failed to create AI config: {str(e)}"
        )