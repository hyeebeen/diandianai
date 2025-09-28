"""
集成测试：完整运单流程
测试从创建运单到交付完成的完整业务流程
包括状态流转、GPS追踪、通知机制等核心功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import Dict, Any, List
from httpx import AsyncClient

from fastapi.testclient import TestClient
from src.main import app
from src.core.config import get_settings
from src.core.database import get_db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()


class TestShipmentWorkflow:
    """完整运单流程集成测试"""

    @pytest.fixture
    async def test_tenant_id(self) -> UUID:
        """创建测试租户"""
        return uuid4()

    @pytest.fixture
    async def test_company_id(self) -> UUID:
        """创建测试公司"""
        return uuid4()

    @pytest.fixture
    async def test_user_id(self) -> UUID:
        """创建测试用户"""
        return uuid4()

    @pytest.fixture
    async def test_vehicle_id(self) -> UUID:
        """创建测试车辆"""
        return uuid4()

    @pytest.fixture
    async def db_session(self) -> AsyncSession:
        """数据库会话"""
        async with get_db() as session:
            yield session

    @pytest.fixture
    async def client(self) -> AsyncClient:
        """HTTP客户端"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def auth_headers(self, test_tenant_id: UUID, test_user_id: UUID) -> Dict[str, str]:
        """认证头部"""
        # 在实际实现中，这里会生成真实的JWT token
        return {
            "Authorization": f"Bearer test-token",
            "X-Tenant-ID": str(test_tenant_id),
            "X-User-ID": str(test_user_id)
        }

    @pytest.fixture
    async def sample_shipment_data(
        self,
        test_tenant_id: UUID,
        test_company_id: UUID,
        test_user_id: UUID
    ) -> Dict[str, Any]:
        """示例运单数据"""
        return {
            "shipment_number": f"TEST-{datetime.now().strftime('%Y%m%d')}-001",
            "sender": {
                "name": "张三",
                "phone": "13800138001",
                "company": "测试发货公司"
            },
            "sender_address": {
                "address": "北京市朝阳区建国门外大街1号",
                "latitude": 39.9042,
                "longitude": 116.4074,
                "city": "北京市",
                "district": "朝阳区"
            },
            "receiver": {
                "name": "李四",
                "phone": "13800138002",
                "company": "测试收货公司"
            },
            "receiver_address": {
                "address": "上海市浦东新区陆家嘴环路1000号",
                "latitude": 31.2304,
                "longitude": 121.4737,
                "city": "上海市",
                "district": "浦东新区"
            },
            "cargo": {
                "description": "测试货物",
                "weight": 100.5,
                "quantity": 10,
                "volume": 2.5,
                "value": 50000.0
            },
            "special_requirements": ["易碎", "保温"],
            "pickup_time": (datetime.now() + timedelta(hours=2)).isoformat(),
            "expected_delivery": (datetime.now() + timedelta(days=2)).isoformat(),
            "tenant_id": str(test_tenant_id),
            "company_id": str(test_company_id),
            "created_by": str(test_user_id)
        }

    async def test_complete_shipment_workflow(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_shipment_data: Dict[str, Any],
        test_vehicle_id: UUID,
        db_session: AsyncSession
    ):
        """
        测试完整的运单流程

        流程步骤：
        1. 创建运单 (CREATED)
        2. 分配车辆和司机
        3. 开始提货 (PICKED_UP)
        4. 运输过程 (IN_TRANSIT) + GPS追踪
        5. 送达完成 (DELIVERED)
        6. 验证通知和日志
        """

        # 设置多租户上下文
        await db_session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": sample_shipment_data["tenant_id"]}
        )

        # Step 1: 创建运单
        print("Step 1: 创建运单")
        create_response = await client.post(
            "/api/shipments",
            json=sample_shipment_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        shipment = create_response.json()
        shipment_id = shipment["id"]

        # 验证初始状态
        assert shipment["status"] == "created"
        assert shipment["shipment_number"] == sample_shipment_data["shipment_number"]
        assert shipment["sender"]["name"] == "张三"
        assert shipment["receiver"]["name"] == "李四"

        # Step 2: 分配车辆和司机
        print("Step 2: 分配车辆和司机")
        assignment_data = {
            "vehicle_id": str(test_vehicle_id),
            "driver_id": str(uuid4()),
            "planned_route": [
                {
                    "sequence": 1,
                    "location": sample_shipment_data["sender_address"],
                    "type": "pickup",
                    "estimated_time": (datetime.now() + timedelta(hours=2)).isoformat()
                },
                {
                    "sequence": 2,
                    "location": sample_shipment_data["receiver_address"],
                    "type": "delivery",
                    "estimated_time": (datetime.now() + timedelta(days=2)).isoformat()
                }
            ]
        }

        assign_response = await client.post(
            f"/api/shipments/{shipment_id}/assign",
            json=assignment_data,
            headers=auth_headers
        )
        assert assign_response.status_code == 200

        # 验证分配结果
        assignment = assign_response.json()
        assert assignment["vehicle_id"] == str(test_vehicle_id)
        assert len(assignment["planned_route"]) == 2

        # Step 3: 开始提货 (状态变更为 PICKED_UP)
        print("Step 3: 开始提货")
        pickup_data = {
            "status": "picked_up",
            "location": sample_shipment_data["sender_address"],
            "timestamp": datetime.now().isoformat(),
            "notes": "货物已提取，状态良好",
            "photo_urls": ["https://example.com/pickup-photo.jpg"]
        }

        pickup_response = await client.patch(
            f"/api/shipments/{shipment_id}/status",
            json=pickup_data,
            headers=auth_headers
        )
        assert pickup_response.status_code == 200

        # 验证状态更新
        status_update = pickup_response.json()
        assert status_update["status"] == "picked_up"
        assert status_update["current_location"] is not None

        # Step 4: 运输过程 (IN_TRANSIT) + GPS追踪
        print("Step 4: 运输过程和GPS追踪")

        # 4a: 更新状态为运输中
        transit_data = {
            "status": "in_transit",
            "timestamp": datetime.now().isoformat(),
            "notes": "开始运输，预计明天送达"
        }

        transit_response = await client.patch(
            f"/api/shipments/{shipment_id}/status",
            json=transit_data,
            headers=auth_headers
        )
        assert transit_response.status_code == 200

        # 4b: 模拟GPS位置更新
        gps_locations = [
            {
                "vehicle_id": str(test_vehicle_id),
                "shipment_id": shipment_id,
                "latitude": 39.9042 + i * 0.01,  # 模拟移动
                "longitude": 116.4074 + i * 0.01,
                "speed": 60.0 + i * 5,
                "heading": 180.0,
                "timestamp": (datetime.now() + timedelta(minutes=i * 30)).isoformat(),
                "source": "g7_device"
            }
            for i in range(5)  # 5个GPS点
        ]

        for gps_data in gps_locations:
            gps_response = await client.post(
                "/api/gps/locations",
                json=gps_data,
                headers=auth_headers
            )
            assert gps_response.status_code == 201

        # 4c: 验证实时GPS数据
        realtime_response = await client.get(
            f"/api/gps/realtime/{shipment_id}",
            headers=auth_headers
        )
        assert realtime_response.status_code == 200
        realtime_data = realtime_response.json()
        assert realtime_data["shipment_id"] == shipment_id
        assert realtime_data["current_location"] is not None
        assert realtime_data["speed"] > 0

        # 4d: 验证路线轨迹
        route_response = await client.get(
            f"/api/gps/route/{shipment_id}",
            headers=auth_headers
        )
        assert route_response.status_code == 200
        route_data = route_response.json()
        assert len(route_data["track_points"]) >= 5
        assert route_data["total_distance"] > 0
        assert route_data["total_duration"] > 0

        # Step 5: 送达完成 (DELIVERED)
        print("Step 5: 送达完成")
        delivery_data = {
            "status": "delivered",
            "location": sample_shipment_data["receiver_address"],
            "timestamp": datetime.now().isoformat(),
            "notes": "货物已安全送达，收货人已签收",
            "recipient_signature": "李四",
            "photo_urls": ["https://example.com/delivery-photo.jpg"],
            "delivery_confirmation": {
                "recipient_name": "李四",
                "recipient_phone": "13800138002",
                "delivery_time": datetime.now().isoformat(),
                "condition": "完好"
            }
        }

        delivery_response = await client.patch(
            f"/api/shipments/{shipment_id}/status",
            json=delivery_data,
            headers=auth_headers
        )
        assert delivery_response.status_code == 200

        # 验证最终状态
        final_status = delivery_response.json()
        assert final_status["status"] == "delivered"
        assert final_status["delivery_confirmation"] is not None

        # Step 6: 验证完整运单信息
        print("Step 6: 验证完整运单信息")
        final_response = await client.get(
            f"/api/shipments/{shipment_id}",
            headers=auth_headers
        )
        assert final_response.status_code == 200

        final_shipment = final_response.json()
        assert final_shipment["id"] == shipment_id
        assert final_shipment["status"] == "delivered"
        assert len(final_shipment["status_history"]) >= 4  # created, picked_up, in_transit, delivered
        assert final_shipment["actual_delivery_time"] is not None
        assert final_shipment["total_distance"] > 0

        # Step 7: 验证通知历史
        print("Step 7: 验证通知历史")
        notifications_response = await client.get(
            f"/api/shipments/{shipment_id}/notifications",
            headers=auth_headers
        )
        assert notifications_response.status_code == 200

        notifications = notifications_response.json()
        assert len(notifications) > 0

        # 应该包含状态变更通知
        notification_types = [notif["type"] for notif in notifications]
        assert "status_update" in notification_types
        assert "delivery_completed" in notification_types

        print("✅ 完整运单流程测试通过")

    async def test_shipment_workflow_with_ai_assistance(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        test_tenant_id: UUID
    ):
        """
        测试AI辅助的运单创建流程
        """
        print("测试AI辅助运单创建")

        # AI助手对话创建运单
        ai_message = {
            "message": "我要发一批货从北京到上海，发货人是张三(13800138001)，收货人是李四(13800138002)，货物是100公斤的电子产品，需要保温运输",
            "context": {
                "tenant_id": str(test_tenant_id),
                "user_preference": {
                    "language": "zh-CN",
                    "notification_channels": ["wechat", "sms"]
                }
            }
        }

        ai_response = await client.post(
            "/api/ai/chat",
            json=ai_message,
            headers=auth_headers
        )
        assert ai_response.status_code == 200

        ai_result = ai_response.json()
        assert ai_result["action_type"] == "create_shipment"
        assert ai_result["extracted_data"] is not None

        # 验证AI提取的运单信息
        extracted = ai_result["extracted_data"]
        assert extracted["sender"]["name"] == "张三"
        assert extracted["sender"]["phone"] == "13800138001"
        assert extracted["receiver"]["name"] == "李四"
        assert extracted["receiver"]["phone"] == "13800138002"
        assert "保温" in extracted["special_requirements"]

        print("✅ AI辅助运单创建测试通过")

    async def test_shipment_workflow_error_handling(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        sample_shipment_data: Dict[str, Any]
    ):
        """
        测试运单流程中的错误处理
        """
        print("测试运单流程错误处理")

        # 创建运单
        create_response = await client.post(
            "/api/shipments",
            json=sample_shipment_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        shipment_id = create_response.json()["id"]

        # 尝试无效的状态转换 (从created直接跳到delivered)
        invalid_transition = {
            "status": "delivered",
            "timestamp": datetime.now().isoformat()
        }

        invalid_response = await client.patch(
            f"/api/shipments/{shipment_id}/status",
            json=invalid_transition,
            headers=auth_headers
        )
        assert invalid_response.status_code == 400

        error = invalid_response.json()
        assert "invalid status transition" in error["detail"].lower()

        # 尝试重复创建相同运单号
        duplicate_response = await client.post(
            "/api/shipments",
            json=sample_shipment_data,
            headers=auth_headers
        )
        assert duplicate_response.status_code == 409

        duplicate_error = duplicate_response.json()
        assert "shipment number already exists" in duplicate_error["detail"].lower()

        print("✅ 错误处理测试通过")

    async def test_shipment_workflow_permissions(
        self,
        client: AsyncClient,
        sample_shipment_data: Dict[str, Any],
        test_tenant_id: UUID
    ):
        """
        测试运单流程的权限控制
        """
        print("测试运单权限控制")

        # 无认证头部
        no_auth_response = await client.post(
            "/api/shipments",
            json=sample_shipment_data
        )
        assert no_auth_response.status_code == 401

        # 错误的租户ID
        wrong_tenant_headers = {
            "Authorization": "Bearer test-token",
            "X-Tenant-ID": str(uuid4()),
            "X-User-ID": str(uuid4())
        }

        wrong_tenant_response = await client.post(
            "/api/shipments",
            json=sample_shipment_data,
            headers=wrong_tenant_headers
        )
        # 应该成功创建，但在其他租户下不可见
        assert wrong_tenant_response.status_code == 201

        # 用原租户验证不可见
        correct_headers = {
            "Authorization": "Bearer test-token",
            "X-Tenant-ID": str(test_tenant_id),
            "X-User-ID": str(uuid4())
        }

        list_response = await client.get(
            "/api/shipments",
            headers=correct_headers
        )
        assert list_response.status_code == 200

        shipments = list_response.json()
        # 不应该看到其他租户的运单
        other_tenant_shipments = [
            s for s in shipments["items"]
            if s["shipment_number"] == sample_shipment_data["shipment_number"]
        ]
        assert len(other_tenant_shipments) == 0

        print("✅ 权限控制测试通过")


if __name__ == "__main__":
    # 运行测试
    import sys
    import asyncio

    async def run_tests():
        test_instance = TestShipmentWorkflow()

        # 模拟测试数据
        test_tenant_id = uuid4()
        test_company_id = uuid4()
        test_user_id = uuid4()
        test_vehicle_id = uuid4()

        print("开始运单流程集成测试...")
        print("注意：需要先启动后端服务和数据库")

        # 这里只是示例，实际测试需要pytest运行
        print("请使用: pytest tests/integration/test_shipment_workflow.py -v")

    if len(sys.argv) > 1 and sys.argv[1] == "run":
        asyncio.run(run_tests())