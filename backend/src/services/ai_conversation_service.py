"""
AI对话服务

管理AI对话会话、消息发送、文件分析等功能
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
import uuid
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from core.config import Settings
from core.security import set_tenant_context
from models.ai_models import (
    AIConversation, AIMessage, FileAttachment,
    MessageRole, ContextType, MessageType, FileProcessingStatus
)
from models.users import User
from services.ai_service import AIService
# from services.file_processing_service import FileProcessingService


class AIConversationError(Exception):
    """AI对话服务相关异常"""
    pass


class AIConversationService:
    """AI对话服务类"""

    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service or self._create_ai_service()
        # self.file_service = FileProcessingService()

    def _create_ai_service(self) -> AIService:
        """创建AI服务实例"""
        from core.config import get_settings
        settings = get_settings()
        return AIService(settings)

    async def create_conversation(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        title: str,
        context_type: ContextType = ContextType.GENERAL,
        context_data: Optional[Dict[str, Any]] = None
    ) -> AIConversation:
        """创建新的AI对话会话"""
        try:
            await set_tenant_context(session, tenant_id)

            conversation = AIConversation(
                tenant_id=uuid.UUID(tenant_id),
                user_id=uuid.UUID(user_id),
                title=title,
                context_type=context_type,
                context_data=context_data or {},
                is_active=True,
                message_count=0
            )

            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

            return conversation

        except Exception as e:
            await session.rollback()
            raise AIConversationError(f"Failed to create conversation: {str(e)}")

    async def get_user_conversations(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """获取用户的对话列表"""
        try:
            await set_tenant_context(session, tenant_id)

            # 构建查询条件
            conditions = [AIConversation.user_id == uuid.UUID(user_id)]
            if is_active is not None:
                conditions.append(AIConversation.is_active == is_active)

            # 获取总数
            count_stmt = select(func.count(AIConversation.id)).where(and_(*conditions))
            total_result = await session.execute(count_stmt)
            total = total_result.scalar()

            # 获取对话列表
            stmt = select(AIConversation).where(
                and_(*conditions)
            ).order_by(
                desc(AIConversation.last_activity_at)
            ).limit(limit).offset(offset)

            result = await session.execute(stmt)
            conversations = result.scalars().all()

            # 格式化返回数据
            conversation_list = []
            for conv in conversations:
                conversation_list.append({
                    "id": str(conv.id),
                    "title": conv.title,
                    "context_type": conv.context_type.value,
                    "message_count": conv.message_count,
                    "is_active": conv.is_active,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                    "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None
                })

            return {
                "conversations": conversation_list,
                "total": total,
                "has_more": offset + len(conversations) < total
            }

        except Exception as e:
            raise AIConversationError(f"Failed to get conversations: {str(e)}")

    async def get_conversation(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        conversation_id: str
    ) -> Optional[AIConversation]:
        """获取指定对话"""
        try:
            await set_tenant_context(session, tenant_id)

            stmt = select(AIConversation).where(
                and_(
                    AIConversation.id == uuid.UUID(conversation_id),
                    AIConversation.user_id == uuid.UUID(user_id)
                )
            ).options(
                selectinload(AIConversation.messages),
                selectinload(AIConversation.file_attachments)
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            raise AIConversationError(f"Failed to get conversation: {str(e)}")

    async def send_message(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        message_content: str,
        uploaded_files: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """发送消息到AI对话"""
        try:
            await set_tenant_context(session, tenant_id)

            # 验证对话归属
            conversation = await self.get_conversation(
                session, tenant_id, user_id, conversation_id
            )
            if not conversation:
                raise AIConversationError("Conversation not found")

            # 处理文件上传
            file_attachments = []
            if uploaded_files:
                for file_data in uploaded_files:
                    file_attachment = await self.file_service.upload_file(
                        session=session,
                        tenant_id=tenant_id,
                        conversation_id=conversation_id,
                        file=file_data["file"],
                        filename=file_data["filename"],
                        mime_type=file_data["mime_type"]
                    )
                    file_attachments.append(file_attachment)

            # 确定消息类型
            message_type = MessageType.FILE_ANALYSIS if file_attachments else MessageType.TEXT

            # 创建用户消息
            user_message = AIMessage(
                tenant_id=uuid.UUID(tenant_id),
                conversation_id=uuid.UUID(conversation_id),
                role=MessageRole.USER,
                content=message_content,
                message_type=message_type,
                file_attachments=[str(fa.id) for fa in file_attachments] if file_attachments else None
            )

            session.add(user_message)
            await session.flush()  # 确保user_message有ID

            # 为文件附件关联消息ID
            for file_attachment in file_attachments:
                file_attachment.message_id = user_message.id

            # 准备AI对话上下文
            context = await self._build_conversation_context(
                session, conversation, file_attachments
            )

            # 调用AI服务生成回复
            if stream:
                # 流式响应
                ai_response_content = ""
                async for chunk in self.ai_service.chat_stream(
                    message_content, context, file_attachments
                ):
                    ai_response_content += chunk
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "user_message_id": str(user_message.id)
                    }
            else:
                # 普通响应
                ai_response_content = await self.ai_service.chat_with_file_analysis(
                    message_content, context, file_attachments
                )

            # 创建AI回复消息
            ai_message = AIMessage(
                tenant_id=uuid.UUID(tenant_id),
                conversation_id=uuid.UUID(conversation_id),
                role=MessageRole.ASSISTANT,
                content=ai_response_content,
                message_type=message_type,
                model_used="kimi-k2",  # 从配置获取
                file_attachments=[str(fa.id) for fa in file_attachments] if file_attachments else None
            )

            session.add(ai_message)

            # 更新对话统计
            conversation.message_count += 2  # 用户消息 + AI回复
            conversation.last_message_at = datetime.utcnow()
            conversation.last_activity_at = datetime.utcnow()

            await session.commit()
            await session.refresh(user_message)
            await session.refresh(ai_message)

            if stream:
                # 流式响应的最终消息
                yield {
                    "type": "complete",
                    "user_message": self._format_message(user_message),
                    "ai_response": self._format_message(ai_message),
                    "uploaded_files": [self._format_file_attachment(fa) for fa in file_attachments]
                }
            else:
                # 普通响应
                yield {
                    "user_message": self._format_message(user_message),
                    "ai_response": self._format_message(ai_message),
                    "uploaded_files": [self._format_file_attachment(fa) for fa in file_attachments]
                }

        except Exception as e:
            await session.rollback()
            raise AIConversationError(f"Failed to send message: {str(e)}")

    async def _build_conversation_context(
        self,
        session: AsyncSession,
        conversation: AIConversation,
        file_attachments: List[FileAttachment]
    ) -> Dict[str, Any]:
        """构建AI对话上下文"""
        # 获取最近的消息历史
        stmt = select(AIMessage).where(
            AIMessage.conversation_id == conversation.id
        ).order_by(desc(AIMessage.created_at)).limit(10)

        result = await session.execute(stmt)
        recent_messages = result.scalars().all()

        # 构建上下文
        context = {
            "conversation_type": conversation.context_type.value,
            "conversation_data": conversation.context_data,
            "message_history": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in reversed(recent_messages)  # 按时间正序
            ],
            "file_contents": []
        }

        # 添加文件内容到上下文
        for file_attachment in file_attachments:
            if file_attachment.processing_status == FileProcessingStatus.COMPLETED:
                context["file_contents"].append({
                    "filename": file_attachment.original_filename,
                    "content": file_attachment.extracted_content,
                    "mime_type": file_attachment.mime_type
                })

        return context

    def _format_message(self, message: AIMessage) -> Dict[str, Any]:
        """格式化消息对象"""
        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "role": message.role.value,
            "content": message.content,
            "message_type": message.message_type.value,
            "created_at": message.created_at.isoformat(),
            "file_attachments": message.file_attachments or []
        }

    def _format_file_attachment(self, file_attachment: FileAttachment) -> Dict[str, Any]:
        """格式化文件附件对象"""
        return {
            "id": str(file_attachment.id),
            "original_filename": file_attachment.original_filename,
            "mime_type": file_attachment.mime_type,
            "file_size": file_attachment.file_size,
            "processing_status": file_attachment.processing_status.value
        }

    async def delete_conversation(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        conversation_id: str
    ) -> bool:
        """删除对话"""
        try:
            await set_tenant_context(session, tenant_id)

            # 验证对话归属
            conversation = await self.get_conversation(
                session, tenant_id, user_id, conversation_id
            )
            if not conversation:
                return False

            # 删除关联的文件
            for file_attachment in conversation.file_attachments:
                await self.file_service.delete_file(
                    session, tenant_id, str(file_attachment.id)
                )

            # 删除对话（级联删除消息）
            await session.delete(conversation)
            await session.commit()

            return True

        except Exception as e:
            await session.rollback()
            raise AIConversationError(f"Failed to delete conversation: {str(e)}")

    async def update_conversation(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[AIConversation]:
        """更新对话信息"""
        try:
            await set_tenant_context(session, tenant_id)

            # 验证对话归属
            conversation = await self.get_conversation(
                session, tenant_id, user_id, conversation_id
            )
            if not conversation:
                return None

            # 更新字段
            if title is not None:
                conversation.title = title
            if is_active is not None:
                conversation.is_active = is_active

            conversation.last_activity_at = datetime.utcnow()

            await session.commit()
            await session.refresh(conversation)

            return conversation

        except Exception as e:
            await session.rollback()
            raise AIConversationError(f"Failed to update conversation: {str(e)}")


# 全局AI对话服务实例
def get_ai_conversation_service() -> AIConversationService:
    """获取AI对话服务实例"""
    # 使用正确的依赖注入创建AI服务
    from services.ai_service import get_ai_service
    ai_service = get_ai_service()
    return AIConversationService(ai_service=ai_service)