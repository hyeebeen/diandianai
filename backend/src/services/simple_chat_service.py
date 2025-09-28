"""
简化的AI聊天服务
专为开发环境设计，直接调用Kimi K2 API
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from integrations.ai_providers.openai_provider import OpenAIProvider, OpenAIModel, ChatMessage, MessageRole
from core.config import get_settings
from services.context_builder import context_builder, ShipmentContext
from models.logistics import Shipment


class SimpleChatService:
    """简化的AI聊天服务"""

    def __init__(self):
        self.settings = get_settings()
        self.provider = OpenAIProvider()

    async def chat_with_diandian(
        self,
        user_message: str,
        shipment_context: Optional[ShipmentContext] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """与点点精灵聊天"""

        try:
            # 构建对话上下文
            message_dicts = context_builder.build_conversation_context(
                user_message=user_message,
                shipment_context=shipment_context,
                conversation_history=conversation_history
            )

            # 转换为 ChatMessage 对象
            messages = []
            for msg_dict in message_dicts:
                role = MessageRole(msg_dict["role"])
                content = msg_dict["content"]
                messages.append(ChatMessage(role=role, content=content))

            # 调用AI API
            start_time = datetime.now()

            response = await self.provider.chat_completion(
                messages=messages,
                model=OpenAIModel.KIMI_K2_0711_PREVIEW,
                temperature=0.7,
                max_tokens=1000
            )

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # 构建响应
            chat_response = {
                "id": f"msg_{int(datetime.now().timestamp())}",
                "role": "assistant",
                "content": response.content,
                "timestamp": datetime.now().isoformat(),
                "response_time_ms": int(response_time),
                "model": response.model,
                "token_usage": {
                    "prompt_tokens": response.token_usage.prompt_tokens if response.token_usage else 0,
                    "completion_tokens": response.token_usage.completion_tokens if response.token_usage else 0,
                    "total_tokens": response.token_usage.total_tokens if response.token_usage else 0
                } if response.token_usage else None
            }

            return {
                "success": True,
                "data": chat_response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "id": f"error_{int(datetime.now().timestamp())}",
                    "role": "assistant",
                    "content": f"抱歉，点点精灵暂时无法回应。请稍后再试。错误信息：{str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "error": True
                }
            }

    async def chat_with_shipment_context(
        self,
        user_message: str,
        shipment: Optional[Shipment] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """带运单上下文的聊天"""

        shipment_context = None
        if shipment:
            shipment_context = context_builder.extract_shipment_context(shipment)

        return await self.chat_with_diandian(
            user_message=user_message,
            shipment_context=shipment_context,
            conversation_history=conversation_history
        )


# 全局实例
simple_chat_service = SimpleChatService()