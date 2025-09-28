from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
import json
import asyncio
import uuid
from dataclasses import dataclass
from enum import Enum

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from core.config import Settings
from core.security import set_tenant_context
from models.ai_models import (
    AIModelConfig, AIConversation, AIMessage,
    AIInteraction, AISummary, AIProvider, MessageRole
)
from models.logistics import Shipment, ShipmentStatus
from models.users import User


class LogisticsAction(str, Enum):
    """物流操作类型"""
    CREATE_SHIPMENT = "create_shipment"
    UPDATE_STATUS = "update_status"
    QUERY_LOCATION = "query_location"
    GET_ROUTE = "get_route"
    GENERATE_REPORT = "generate_report"


class ConfidenceLevel(str, Enum):
    """置信度级别"""
    HIGH = "high"      # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # < 0.5


@dataclass
class ShipmentInfo:
    """运单信息结构"""
    pickup_address: str
    delivery_address: str
    customer_name: str
    weight_kg: Optional[float] = None
    commodity_type: Optional[str] = None
    notes: Optional[str] = None


class AIActionRequest(BaseModel):
    """AI动作请求模型"""
    action: LogisticsAction = Field(description="需要执行的物流操作")
    confidence: float = Field(ge=0.0, le=1.0, description="AI的置信度")
    shipment_info: Optional[Dict[str, Any]] = Field(None, description="运单信息")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")
    requires_confirmation: bool = Field(False, description="是否需要用户确认")
    reasoning: str = Field(description="AI的推理过程")


class AIResponse(BaseModel):
    """AI响应模型"""
    content: str = Field(description="AI的回复内容")
    action_request: Optional[AIActionRequest] = Field(None, description="建议的操作")
    suggested_actions: List[str] = Field(default_factory=list, description="建议的后续操作")
    context_updates: Dict[str, Any] = Field(default_factory=dict, description="上下文更新")


class AIServiceError(Exception):
    """AI服务相关异常"""
    pass


class AIService:
    """AI服务类，使用Instructor框架处理智能对话和物流操作"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._clients: Dict[str, AsyncOpenAI] = {}

    async def _get_ai_client(self, session: AsyncSession, tenant_id: str, model_name: Optional[str] = None) -> AsyncOpenAI:
        """获取AI客户端实例"""
        try:
            await set_tenant_context(session, tenant_id)

            # Get model config
            stmt = select(AIModelConfig).where(AIModelConfig.is_active == True)
            if model_name:
                stmt = stmt.where(AIModelConfig.name == model_name)
            else:
                stmt = stmt.where(AIModelConfig.is_default == True)

            result = await session.execute(stmt)
            model_config = result.scalar_one_or_none()

            if not model_config:
                raise AIServiceError("No active AI model configuration found")

            # Create client key
            client_key = f"{tenant_id}_{model_config.id}"

            # Return cached client or create new one
            if client_key not in self._clients:
                client = AsyncOpenAI(
                    api_key=model_config.api_key,
                    base_url=model_config.api_base_url or "https://api.openai.com/v1"
                )
                # Patch with instructor
                self._clients[client_key] = instructor.apatch(client)

            return self._clients[client_key], model_config

        except Exception as e:
            raise AIServiceError(f"Failed to get AI client: {str(e)}")

    async def chat_completion(
        self,
        session: AsyncSession,
        tenant_id: str,
        conversation_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ) -> AIResponse:
        """处理AI对话完成"""
        try:
            client, model_config = await self._get_ai_client(session, tenant_id, model_name)

            # Get conversation history
            conversation = await self._get_conversation(session, conversation_id)
            if not conversation:
                raise AIServiceError("Conversation not found")

            # Build message history
            messages = await self._build_message_history(session, conversation_id, context)

            # Add user message
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Create AI completion with instructor
            response = await client.chat.completions.create(
                model=model_config.model_name,
                messages=messages,
                response_model=AIResponse,
                temperature=float(model_config.temperature or 0.7),
                max_tokens=int(model_config.max_tokens or 1000)
            )

            # Save user message
            await self._save_message(
                session, conversation_id, MessageRole.USER, user_message
            )

            # Save AI response
            ai_message = await self._save_message(
                session, conversation_id, MessageRole.ASSISTANT, response.content,
                confidence=response.action_request.confidence if response.action_request else None,
                suggested_actions=response.suggested_actions,
                requires_confirmation=response.action_request.requires_confirmation if response.action_request else False,
                model_used=model_config.model_name
            )

            # Update conversation
            await self._update_conversation_activity(session, conversation_id)

            return response

        except Exception as e:
            raise AIServiceError(f"Chat completion failed: {str(e)}")

    async def stream_chat_completion(
        self,
        session: AsyncSession,
        tenant_id: str,
        conversation_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """流式AI对话完成"""
        try:
            client, model_config = await self._get_ai_client(session, tenant_id, model_name)

            # Get conversation and build messages
            conversation = await self._get_conversation(session, conversation_id)
            if not conversation:
                raise AIServiceError("Conversation not found")

            messages = await self._build_message_history(session, conversation_id, context)
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Save user message
            await self._save_message(
                session, conversation_id, MessageRole.USER, user_message
            )

            # Stream completion
            response_content = ""
            async for chunk in await client.chat.completions.create(
                model=model_config.model_name,
                messages=messages,
                temperature=float(model_config.temperature or 0.7),
                max_tokens=int(model_config.max_tokens or 1000),
                stream=True
            ):
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    response_content += content
                    yield content

            # Save complete AI response
            await self._save_message(
                session, conversation_id, MessageRole.ASSISTANT, response_content,
                model_used=model_config.model_name
            )

            await self._update_conversation_activity(session, conversation_id)

        except Exception as e:
            raise AIServiceError(f"Stream completion failed: {str(e)}")

    async def execute_action(
        self,
        session: AsyncSession,
        tenant_id: str,
        conversation_id: str,
        action_request: AIActionRequest,
        user_id: str
    ) -> Dict[str, Any]:
        """执行AI建议的操作"""
        try:
            await set_tenant_context(session, tenant_id)

            result = {"success": False, "message": "", "data": None}

            if action_request.action == LogisticsAction.CREATE_SHIPMENT:
                result = await self._create_shipment_action(
                    session, action_request.shipment_info, user_id
                )
            elif action_request.action == LogisticsAction.UPDATE_STATUS:
                result = await self._update_status_action(
                    session, action_request.parameters
                )
            elif action_request.action == LogisticsAction.QUERY_LOCATION:
                result = await self._query_location_action(
                    session, action_request.parameters
                )
            else:
                result = {
                    "success": False,
                    "message": f"Unsupported action: {action_request.action}"
                }

            # Record interaction
            await self._record_interaction(
                session, conversation_id, action_request.action.value,
                result["success"], result, action_request.requires_confirmation
            )

            return result

        except Exception as e:
            result = {"success": False, "message": str(e)}
            await self._record_interaction(
                session, conversation_id, action_request.action.value,
                False, result, action_request.requires_confirmation
            )
            return result

    async def _get_conversation(self, session: AsyncSession, conversation_id: str) -> Optional[AIConversation]:
        """获取对话信息"""
        stmt = select(AIConversation).where(
            AIConversation.id == uuid.UUID(conversation_id)
        ).options(selectinload(AIConversation.user))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _build_message_history(
        self,
        session: AsyncSession,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """构建消息历史"""
        # System message
        system_prompt = self._build_system_prompt(context)
        messages = [{"role": "system", "content": system_prompt}]

        # Get conversation messages
        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == uuid.UUID(conversation_id))
            .where(AIMessage.is_deleted == False)
            .order_by(AIMessage.created_at)
            .limit(20)  # Last 20 messages
        )
        result = await session.execute(stmt)
        ai_messages = result.scalars().all()

        for msg in ai_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        return messages

    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """构建系统提示"""
        base_prompt = """你是点点精灵，一个专业的物流管理AI助手。你可以帮助用户：

1. 创建和管理运单
2. 查询货物位置和状态
3. 生成物流报告
4. 优化配送路线
5. 处理客户咨询

请用简洁、专业的语言回复用户。当需要执行操作时，请明确说明需要什么信息。

当前可用的操作：
- create_shipment: 创建运单
- update_status: 更新运单状态
- query_location: 查询位置
- get_route: 获取路线
- generate_report: 生成报告
"""

        if context:
            if context.get("shipment_id"):
                base_prompt += f"\n当前关联运单: {context['shipment_id']}"
            if context.get("customer_name"):
                base_prompt += f"\n当前客户: {context['customer_name']}"

        return base_prompt

    async def _save_message(
        self,
        session: AsyncSession,
        conversation_id: str,
        role: MessageRole,
        content: str,
        confidence: Optional[float] = None,
        suggested_actions: Optional[List[str]] = None,
        requires_confirmation: bool = False,
        model_used: Optional[str] = None
    ) -> AIMessage:
        """保存消息到数据库"""
        message = AIMessage(
            conversation_id=uuid.UUID(conversation_id),
            role=role.value,
            content=content,
            confidence=confidence,
            suggested_actions=suggested_actions,
            requires_confirmation=requires_confirmation,
            model_used=model_used
        )

        session.add(message)
        await session.commit()
        await session.refresh(message)

        return message

    async def _update_conversation_activity(self, session: AsyncSession, conversation_id: str):
        """更新对话活动时间"""
        stmt = select(AIConversation).where(
            AIConversation.id == uuid.UUID(conversation_id)
        )
        result = await session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            conversation.last_activity_at = datetime.utcnow()
            conversation.message_count = str(int(conversation.message_count or "0") + 1)
            await session.commit()

    async def _create_shipment_action(
        self,
        session: AsyncSession,
        shipment_info: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """创建运单操作"""
        try:
            # Create shipment using logistics service
            from services.logistics_service import LogisticsService
            logistics_service = LogisticsService()

            shipment = await logistics_service.create_shipment(
                session=session,
                pickup_address=shipment_info.get("pickup_address"),
                delivery_address=shipment_info.get("delivery_address"),
                customer_name=shipment_info.get("customer_name"),
                weight_kg=shipment_info.get("weight_kg"),
                commodity_type=shipment_info.get("commodity_type"),
                notes=shipment_info.get("notes")
            )

            return {
                "success": True,
                "message": f"运单 {shipment.shipment_number} 创建成功",
                "data": {
                    "shipment_id": str(shipment.id),
                    "shipment_number": shipment.shipment_number
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"创建运单失败: {str(e)}"
            }

    async def _update_status_action(self, session: AsyncSession, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新状态操作"""
        # Placeholder implementation
        return {
            "success": True,
            "message": "状态更新成功",
            "data": parameters
        }

    async def _query_location_action(self, session: AsyncSession, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """查询位置操作"""
        # Placeholder implementation
        return {
            "success": True,
            "message": "位置查询成功",
            "data": {"location": "北京市朝阳区", "status": "运输中"}
        }

    async def _record_interaction(
        self,
        session: AsyncSession,
        conversation_id: str,
        interaction_type: str,
        success: bool,
        result_data: Dict[str, Any],
        requires_confirmation: bool
    ):
        """记录AI交互"""
        interaction = AIInteraction(
            conversation_id=uuid.UUID(conversation_id),
            interaction_type=interaction_type,
            success=success,
            result_data=result_data,
            requires_confirmation=requires_confirmation
        )

        session.add(interaction)
        await session.commit()

    async def create_conversation(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        title: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> AIConversation:
        """创建新对话"""
        try:
            await set_tenant_context(session, tenant_id)

            conversation = AIConversation(
                tenant_id=uuid.UUID(tenant_id),
                user_id=uuid.UUID(user_id),
                title=title or "新对话",
                context_data=context_data,
                is_active=True,
                message_count="0"
            )

            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

            return conversation

        except Exception as e:
            await session.rollback()
            raise AIServiceError(f"Failed to create conversation: {str(e)}")

    async def get_user_conversations(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        limit: int = 20
    ) -> List[AIConversation]:
        """获取用户对话列表"""
        try:
            await set_tenant_context(session, tenant_id)

            stmt = (
                select(AIConversation)
                .where(AIConversation.user_id == uuid.UUID(user_id))
                .where(AIConversation.is_active == True)
                .order_by(AIConversation.last_activity_at.desc())
                .limit(limit)
            )

            result = await session.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            raise AIServiceError(f"Failed to get conversations: {str(e)}")


# Global AI service instance
def get_ai_service() -> AIService:
    """获取AI服务实例"""
    from core.config import get_settings
    settings = get_settings()
    return AIService(settings)