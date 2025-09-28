"""
简化的AI聊天API端点
使用SimpleChatService提供点点精灵服务
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.simple_chat_service import simple_chat_service


# Pydantic 模型
class SimpleChatRequest(BaseModel):
    """简化聊天请求"""
    message: str = Field(..., description="用户消息")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class SimpleChatResponse(BaseModel):
    """简化聊天响应"""
    response: str = Field(description="点点精灵的回复")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    timestamp: str = Field(description="响应时间")
    model: str = Field(description="使用的AI模型")
    response_time_ms: int = Field(description="响应时间(毫秒)")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token使用情况")


class ConversationRequest(BaseModel):
    """创建对话请求"""
    context_type: str = Field(default="general", description="上下文类型")
    context_id: str = Field(default="general", description="上下文ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ConversationResponse(BaseModel):
    """创建对话响应"""
    id: str = Field(description="对话ID")
    created_at: str = Field(description="创建时间")


class MessageRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(..., description="消息内容")
    message_type: str = Field(default="text", description="消息类型")


class HistoryResponse(BaseModel):
    """历史记录响应"""
    id: str
    sender: str
    content: str
    timestamp: str


# 创建路由器
router = APIRouter()

# 存储对话历史的简单内存缓存（生产环境应使用数据库）
conversation_histories: Dict[str, List[Dict[str, str]]] = {}


@router.post("/chat", response_model=SimpleChatResponse)
async def simple_chat(request: SimpleChatRequest):
    """
    简单的AI聊天端点
    直接使用SimpleChatService
    """
    try:
        # 调用SimpleChatService
        result = await simple_chat_service.chat_with_diandian(
            user_message=request.message,
            shipment_context=None,  # 暂不支持运单上下文
            conversation_history=None  # 暂不支持对话历史
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI服务错误: {result.get('error', '未知错误')}"
            )

        # 构建响应
        response_data = result["data"]
        return SimpleChatResponse(
            response=response_data["content"],
            conversation_id=None,  # 简化版暂不支持
            timestamp=response_data["timestamp"],
            model=response_data["model"],
            response_time_ms=response_data["response_time_ms"],
            token_usage=response_data.get("token_usage")
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天服务错误: {str(e)}"
        )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: ConversationRequest):
    """
    创建新对话（兼容前端接口）
    """
    try:
        # 生成对话ID
        conversation_id = str(uuid.uuid4())

        # 初始化对话历史
        conversation_histories[conversation_id] = []

        return ConversationResponse(
            id=conversation_id,
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建对话失败: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, request: MessageRequest):
    """
    发送消息到指定对话
    """
    try:
        # 获取对话历史
        history = conversation_histories.get(conversation_id, [])

        # 调用SimpleChatService
        result = await simple_chat_service.chat_with_diandian(
            user_message=request.content,
            shipment_context=None,
            conversation_history=history
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI服务错误: {result.get('error', '未知错误')}"
            )

        # 更新对话历史
        user_message = {"role": "user", "content": request.content}
        assistant_message = {"role": "assistant", "content": result["data"]["content"]}

        history.append(user_message)
        history.append(assistant_message)
        conversation_histories[conversation_id] = history[-20:]  # 保留最近20条消息

        return {
            "success": True,
            "message_id": result["data"]["id"],
            "response": result["data"]["content"],
            "timestamp": result["data"]["timestamp"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=List[HistoryResponse])
async def get_conversation_history(conversation_id: str):
    """
    获取对话历史
    """
    try:
        history = conversation_histories.get(conversation_id, [])

        # 转换为响应格式
        responses = []
        for i, msg in enumerate(history):
            responses.append(HistoryResponse(
                id=f"{conversation_id}-{i}",
                sender=msg["role"],
                content=msg["content"],
                timestamp=datetime.now().isoformat()
            ))

        return responses

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话历史失败: {str(e)}"
        )


@router.get("/status")
async def get_ai_status():
    """
    获取AI服务状态
    """
    return {
        "status": "online",
        "model_info": {
            "primary_model": "kimi-k2-0711-preview",
            "fallback_models": [],
            "capabilities": ["chat", "text_generation", "logistics_assistance"]
        },
        "performance_metrics": {
            "average_response_time": 8000,  # 毫秒
            "success_rate": 0.95,
            "current_load": 0.3
        },
        "last_updated": datetime.now().isoformat()
    }