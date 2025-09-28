"""
集成测试：AI助手交互流程
测试AI助手的完整对话流程，包括意图识别、结构化数据提取、
业务操作执行和多轮对话上下文管理
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import Dict, Any, List
from httpx import AsyncClient

from src.main import app
from src.core.config import get_settings
from src.core.database import get_db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()


class TestAIConversation:
    """AI助手交互流程集成测试"""

    @pytest.fixture
    async def test_tenant_id(self) -> UUID:
        """创建测试租户"""
        return uuid4()

    @pytest.fixture
    async def test_user_id(self) -> UUID:
        """创建测试用户"""
        return uuid4()

    @pytest.fixture
    async def client(self) -> AsyncClient:
        """HTTP客户端"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def auth_headers(self, test_tenant_id: UUID, test_user_id: UUID) -> Dict[str, str]:
        """认证头部"""
        return {
            "Authorization": f"Bearer test-token",
            "X-Tenant-ID": str(test_tenant_id),
            "X-User-ID": str(test_user_id)
        }

    @pytest.fixture
    async def conversation_context(self, test_tenant_id: UUID, test_user_id: UUID) -> Dict[str, Any]:
        """对话上下文"""
        return {
            "tenant_id": str(test_tenant_id),
            "user_id": str(test_user_id),
            "session_id": str(uuid4()),
            "language": "zh-CN",
            "user_preferences": {
                "notification_channels": ["wechat", "sms"],
                "default_pickup_location": "北京市朝阳区建国门外大街1号",
                "company_info": {
                    "name": "测试物流公司",
                    "contact": "张经理",
                    "phone": "13800138000"
                }
            }
        }

    async def test_ai_shipment_creation_conversation(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        conversation_context: Dict[str, Any]
    ):
        """
        测试AI助手创建运单的完整对话流程

        场景：用户通过自然语言描述发货需求，AI助手提取信息并创建运单
        """
        print("开始测试AI助手创建运单对话流程")

        # Step 1: 用户描述发货需求
        print("Step 1: 用户描述发货需求")
        user_message_1 = {
            "message": "我需要从北京发一批货到上海，大概100公斤的电子产品，收货人是李四，电话13800138002",
            "context": conversation_context
        }

        response_1 = await client.post(
            "/api/ai/chat",
            json=user_message_1,
            headers=auth_headers
        )
        assert response_1.status_code == 200

        ai_response_1 = response_1.json()

        # 验证AI理解了用户意图
        assert ai_response_1["intent"] == "create_shipment"
        assert ai_response_1["confidence"] > 0.8

        # 验证AI提取了关键信息
        extracted_data = ai_response_1["extracted_data"]
        assert "北京" in extracted_data["pickup_location"]
        assert "上海" in extracted_data["delivery_location"]
        assert extracted_data["cargo"]["weight"] == 100
        assert "电子产品" in extracted_data["cargo"]["description"]
        assert extracted_data["receiver"]["name"] == "李四"
        assert extracted_data["receiver"]["phone"] == "13800138002"

        # 验证AI询问缺失信息
        assert ai_response_1["need_clarification"] == True
        clarification_needed = ai_response_1["clarification_needed"]
        assert "sender_info" in clarification_needed
        assert "detailed_addresses" in clarification_needed

        print(f"AI响应: {ai_response_1['response']}")

        # Step 2: 用户补充信息
        print("Step 2: 用户补充信息")
        user_message_2 = {
            "message": "发货人是张三，电话13800138001，具体地址：发货地址是北京市朝阳区建国门外大街1号，收货地址是上海市浦东新区陆家嘴环路1000号",
            "context": {
                **conversation_context,
                "previous_extraction": extracted_data,
                "conversation_id": ai_response_1["conversation_id"]
            }
        }

        response_2 = await client.post(
            "/api/ai/chat",
            json=user_message_2,
            headers=auth_headers
        )
        assert response_2.status_code == 200

        ai_response_2 = response_2.json()

        # 验证AI更新了信息
        updated_data = ai_response_2["extracted_data"]
        assert updated_data["sender"]["name"] == "张三"
        assert updated_data["sender"]["phone"] == "13800138001"
        assert "朝阳区建国门外大街1号" in updated_data["sender_address"]["address"]
        assert "浦东新区陆家嘴环路1000号" in updated_data["receiver_address"]["address"]

        # 验证AI准备创建运单
        assert ai_response_2["action_ready"] == True
        assert ai_response_2["proposed_action"]["type"] == "create_shipment"

        print(f"AI响应: {ai_response_2['response']}")

        # Step 3: 用户确认创建
        print("Step 3: 用户确认创建")
        user_message_3 = {
            "message": "好的，请帮我创建这个运单",
            "context": {
                **conversation_context,
                "conversation_id": ai_response_2["conversation_id"],
                "confirmed_action": ai_response_2["proposed_action"]
            }
        }

        response_3 = await client.post(
            "/api/ai/chat",
            json=user_message_3,
            headers=auth_headers
        )
        assert response_3.status_code == 200

        ai_response_3 = response_3.json()

        # 验证运单已创建
        assert ai_response_3["action_executed"] == True
        assert ai_response_3["execution_result"]["success"] == True

        shipment_info = ai_response_3["execution_result"]["shipment"]
        assert shipment_info["id"] is not None
        assert shipment_info["shipment_number"] is not None
        assert shipment_info["status"] == "created"

        print(f"AI响应: {ai_response_3['response']}")
        print(f"创建的运单号: {shipment_info['shipment_number']}")

        # Step 4: 验证运单确实被创建
        print("Step 4: 验证运单确实被创建")
        shipment_id = shipment_info["id"]
        verify_response = await client.get(
            f"/api/shipments/{shipment_id}",
            headers=auth_headers
        )
        assert verify_response.status_code == 200

        shipment_data = verify_response.json()
        assert shipment_data["sender"]["name"] == "张三"
        assert shipment_data["receiver"]["name"] == "李四"
        assert shipment_data["cargo"]["weight"] == 100

        print("✅ AI助手创建运单对话流程测试通过")

    async def test_ai_shipment_query_conversation(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        conversation_context: Dict[str, Any]
    ):
        """
        测试AI助手查询运单状态的对话流程
        """
        print("开始测试AI助手查询运单状态对话流程")

        # 先创建一个测试运单
        test_shipment = {
            "shipment_number": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "sender": {"name": "张三", "phone": "13800138001"},
            "receiver": {"name": "李四", "phone": "13800138002"},
            "cargo": {"description": "测试货物", "weight": 50},
            "status": "in_transit"
        }

        create_response = await client.post(
            "/api/shipments",
            json=test_shipment,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        shipment = create_response.json()

        # 用户查询运单状态
        query_message = {
            "message": f"帮我查一下运单{shipment['shipment_number']}的状态",
            "context": conversation_context
        }

        response = await client.post(
            "/api/ai/chat",
            json=query_message,
            headers=auth_headers
        )
        assert response.status_code == 200

        ai_response = response.json()

        # 验证AI识别了查询意图
        assert ai_response["intent"] == "query_shipment"
        assert ai_response["extracted_data"]["shipment_number"] == shipment["shipment_number"]

        # 验证AI执行了查询
        assert ai_response["action_executed"] == True
        query_result = ai_response["execution_result"]
        assert query_result["success"] == True
        assert query_result["shipment"]["status"] == "in_transit"

        print(f"AI响应: {ai_response['response']}")
        print("✅ AI助手查询运单状态对话流程测试通过")

    async def test_ai_route_optimization_conversation(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        conversation_context: Dict[str, Any]
    ):
        """
        测试AI助手路线优化建议的对话流程
        """
        print("开始测试AI助手路线优化对话流程")

        # 用户请求路线优化
        optimization_message = {
            "message": "我有5个配送点需要优化路线：北京朝阳区、北京海淀区、北京丰台区、北京西城区、北京东城区，从亦庄出发，请帮我安排最优路线",
            "context": conversation_context
        }

        response = await client.post(
            "/api/ai/chat",
            json=optimization_message,
            headers=auth_headers
        )
        assert response.status_code == 200

        ai_response = response.json()

        # 验证AI识别了路线优化意图
        assert ai_response["intent"] == "optimize_route"

        extracted_waypoints = ai_response["extracted_data"]["waypoints"]
        assert len(extracted_waypoints) == 5
        assert ai_response["extracted_data"]["start_location"] == "亦庄"

        # 验证AI提供了优化建议
        assert ai_response["action_executed"] == True
        optimization_result = ai_response["execution_result"]
        assert optimization_result["success"] == True
        assert len(optimization_result["optimized_sequence"]) == 5
        assert optimization_result["total_distance"] > 0
        assert optimization_result["estimated_time"] > 0

        print(f"AI响应: {ai_response['response']}")
        print(f"优化后总距离: {optimization_result['total_distance']}km")
        print("✅ AI助手路线优化对话流程测试通过")

    async def test_ai_multi_turn_conversation(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        conversation_context: Dict[str, Any]
    ):
        """
        测试AI助手多轮对话上下文管理
        """
        print("开始测试AI助手多轮对话上下文管理")

        # 第一轮：用户询问一般问题
        message_1 = {
            "message": "我们公司最近的运单情况怎么样？",
            "context": conversation_context
        }

        response_1 = await client.post(
            "/api/ai/chat",
            json=message_1,
            headers=auth_headers
        )
        assert response_1.status_code == 200
        ai_response_1 = response_1.json()

        conversation_id = ai_response_1["conversation_id"]
        assert ai_response_1["intent"] == "business_summary"

        # 第二轮：基于上下文的追问
        message_2 = {
            "message": "那延误的运单主要是什么原因？",
            "context": {
                **conversation_context,
                "conversation_id": conversation_id
            }
        }

        response_2 = await client.post(
            "/api/ai/chat",
            json=message_2,
            headers=auth_headers
        )
        assert response_2.status_code == 200
        ai_response_2 = response_2.json()

        # 验证AI保持了上下文
        assert ai_response_2["conversation_id"] == conversation_id
        assert ai_response_2["context_understanding"] == True

        # 第三轮：切换话题
        message_3 = {
            "message": "帮我创建一个新运单",
            "context": {
                **conversation_context,
                "conversation_id": conversation_id
            }
        }

        response_3 = await client.post(
            "/api/ai/chat",
            json=message_3,
            headers=auth_headers
        )
        assert response_3.status_code == 200
        ai_response_3 = response_3.json()

        # 验证AI识别了话题切换
        assert ai_response_3["intent"] == "create_shipment"
        assert ai_response_3["topic_switch"] == True

        print("✅ AI助手多轮对话上下文管理测试通过")

    async def test_ai_error_handling_conversation(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        conversation_context: Dict[str, Any]
    ):
        """
        测试AI助手错误处理和异常情况
        """
        print("开始测试AI助手错误处理")

        # 测试模糊的用户输入
        ambiguous_message = {
            "message": "那个东西怎么样了？",
            "context": conversation_context
        }

        response = await client.post(
            "/api/ai/chat",
            json=ambiguous_message,
            headers=auth_headers
        )
        assert response.status_code == 200

        ai_response = response.json()
        assert ai_response["intent"] == "unclear"
        assert ai_response["clarification_requested"] == True
        assert "请提供更多信息" in ai_response["response"]

        # 测试无法处理的请求
        invalid_message = {
            "message": "帮我做饭",
            "context": conversation_context
        }

        response_2 = await client.post(
            "/api/ai/chat",
            json=invalid_message,
            headers=auth_headers
        )
        assert response_2.status_code == 200

        ai_response_2 = response_2.json()
        assert ai_response_2["intent"] == "out_of_scope"
        assert "物流相关" in ai_response_2["response"]

        print("✅ AI助手错误处理测试通过")

    async def test_ai_multilingual_conversation(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        conversation_context: Dict[str, Any]
    ):
        """
        测试AI助手多语言支持
        """
        print("开始测试AI助手多语言支持")

        # 英文输入
        english_context = {
            **conversation_context,
            "language": "en-US"
        }

        english_message = {
            "message": "I need to ship a package from Beijing to Shanghai",
            "context": english_context
        }

        response = await client.post(
            "/api/ai/chat",
            json=english_message,
            headers=auth_headers
        )
        assert response.status_code == 200

        ai_response = response.json()
        assert ai_response["intent"] == "create_shipment"
        assert ai_response["language"] == "en-US"
        # 验证回复是英文
        assert any(word in ai_response["response"].lower() for word in ["help", "shipment", "information"])

        print("✅ AI助手多语言支持测试通过")

    async def test_ai_conversation_analytics(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        conversation_context: Dict[str, Any]
    ):
        """
        测试AI对话分析和统计
        """
        print("开始测试AI对话分析")

        # 进行几轮对话
        messages = [
            "帮我创建运单",
            "查询运单状态",
            "优化配送路线"
        ]

        conversation_id = None
        for message in messages:
            msg_data = {
                "message": message,
                "context": {
                    **conversation_context,
                    "conversation_id": conversation_id
                } if conversation_id else conversation_context
            }

            response = await client.post(
                "/api/ai/chat",
                json=msg_data,
                headers=auth_headers
            )
            assert response.status_code == 200

            ai_response = response.json()
            if not conversation_id:
                conversation_id = ai_response["conversation_id"]

        # 获取对话分析报告
        analytics_response = await client.get(
            f"/api/ai/conversations/{conversation_id}/analytics",
            headers=auth_headers
        )
        assert analytics_response.status_code == 200

        analytics = analytics_response.json()
        assert analytics["total_messages"] >= 3
        assert len(analytics["intent_distribution"]) > 0
        assert analytics["conversation_duration"] > 0
        assert "user_satisfaction" in analytics

        print("✅ AI对话分析测试通过")


if __name__ == "__main__":
    # 运行测试
    import sys

    async def run_tests():
        print("开始AI助手交互流程集成测试...")
        print("注意：需要先启动后端服务和数据库，并配置AI模型API")
        print("请使用: pytest tests/integration/test_ai_conversation.py -v")

    if len(sys.argv) > 1 and sys.argv[1] == "run":
        asyncio.run(run_tests())