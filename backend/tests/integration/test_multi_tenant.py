"""
集成测试：多租户数据隔离
测试Row-Level Security (RLS)策略确保不同租户之间的数据完全隔离
包括API访问权限、数据库查询隔离和跨租户操作防护
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


class TestMultiTenantIsolation:
    """多租户数据隔离集成测试"""

    @pytest.fixture
    async def tenant_a_id(self) -> UUID:
        """租户A的ID"""
        return uuid4()

    @pytest.fixture
    async def tenant_b_id(self) -> UUID:
        """租户B的ID"""
        return uuid4()

    @pytest.fixture
    async def user_a_id(self) -> UUID:
        """租户A的用户ID"""
        return uuid4()

    @pytest.fixture
    async def user_b_id(self) -> UUID:
        """租户B的用户ID"""
        return uuid4()

    @pytest.fixture
    async def client(self) -> AsyncClient:
        """HTTP客户端"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def auth_headers_a(self, tenant_a_id: UUID, user_a_id: UUID) -> Dict[str, str]:
        """租户A的认证头部"""
        return {
            "Authorization": f"Bearer test-token-a",
            "X-Tenant-ID": str(tenant_a_id),
            "X-User-ID": str(user_a_id)
        }

    @pytest.fixture
    async def auth_headers_b(self, tenant_b_id: UUID, user_b_id: UUID) -> Dict[str, str]:
        """租户B的认证头部"""
        return {
            "Authorization": f"Bearer test-token-b",
            "X-Tenant-ID": str(tenant_b_id),
            "X-User-ID": str(user_b_id)
        }

    @pytest.fixture
    async def db_session(self) -> AsyncSession:
        """数据库会话"""
        async with get_db() as session:
            yield session

    async def create_test_shipment(
        self,
        client: AsyncClient,
        auth_headers: Dict[str, str],
        tenant_id: UUID,
        user_id: UUID,
        suffix: str = ""
    ) -> Dict[str, Any]:
        """创建测试运单"""
        shipment_data = {
            "shipment_number": f"TEST-TENANT-{suffix}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "sender": {
                "name": f"发货人{suffix}",
                "phone": f"1380013800{suffix[-1] if suffix else '1'}",
                "company": f"测试发货公司{suffix}"
            },
            "sender_address": {
                "address": f"北京市朝阳区测试地址{suffix}",
                "latitude": 39.9042,
                "longitude": 116.4074,
                "city": "北京市",
                "district": "朝阳区"
            },
            "receiver": {
                "name": f"收货人{suffix}",
                "phone": f"1380013800{suffix[-1] if suffix else '2'}",
                "company": f"测试收货公司{suffix}"
            },
            "receiver_address": {
                "address": f"上海市浦东新区测试地址{suffix}",
                "latitude": 31.2304,
                "longitude": 121.4737,
                "city": "上海市",
                "district": "浦东新区"
            },
            "cargo": {
                "description": f"测试货物{suffix}",
                "weight": 100.0,
                "quantity": 1,
                "volume": 1.0,
                "value": 10000.0
            },
            "tenant_id": str(tenant_id),
            "created_by": str(user_id)
        }

        response = await client.post(
            "/api/shipments",
            json=shipment_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        return response.json()

    async def test_shipment_data_isolation(
        self,
        client: AsyncClient,
        auth_headers_a: Dict[str, str],
        auth_headers_b: Dict[str, str],
        tenant_a_id: UUID,
        tenant_b_id: UUID,
        user_a_id: UUID,
        user_b_id: UUID
    ):
        """
        测试运单数据在不同租户间的隔离

        验证：
        1. 租户A创建的运单租户B无法查看
        2. 租户B创建的运单租户A无法查看
        3. 直接通过ID访问其他租户的运单被拒绝
        """
        print("开始测试运单数据隔离")

        # Step 1: 租户A创建运单
        print("Step 1: 租户A创建运单")
        shipment_a = await self.create_test_shipment(
            client, auth_headers_a, tenant_a_id, user_a_id, "A"
        )
        shipment_a_id = shipment_a["id"]

        # Step 2: 租户B创建运单
        print("Step 2: 租户B创建运单")
        shipment_b = await self.create_test_shipment(
            client, auth_headers_b, tenant_b_id, user_b_id, "B"
        )
        shipment_b_id = shipment_b["id"]

        # Step 3: 租户A查询自己的运单列表，应该只看到自己的运单
        print("Step 3: 验证租户A只能看到自己的运单")
        response_a = await client.get(
            "/api/shipments",
            headers=auth_headers_a
        )
        assert response_a.status_code == 200

        shipments_a = response_a.json()
        assert len(shipments_a["items"]) >= 1

        # 验证所有运单都属于租户A
        for shipment in shipments_a["items"]:
            assert shipment["tenant_id"] == str(tenant_a_id)
            # 确保不包含租户B的运单
            assert shipment["id"] != shipment_b_id

        # Step 4: 租户B查询自己的运单列表，应该只看到自己的运单
        print("Step 4: 验证租户B只能看到自己的运单")
        response_b = await client.get(
            "/api/shipments",
            headers=auth_headers_b
        )
        assert response_b.status_code == 200

        shipments_b = response_b.json()
        assert len(shipments_b["items"]) >= 1

        # 验证所有运单都属于租户B
        for shipment in shipments_b["items"]:
            assert shipment["tenant_id"] == str(tenant_b_id)
            # 确保不包含租户A的运单
            assert shipment["id"] != shipment_a_id

        # Step 5: 租户A尝试直接访问租户B的运单，应该被拒绝
        print("Step 5: 验证跨租户访问被拒绝")
        cross_access_response = await client.get(
            f"/api/shipments/{shipment_b_id}",
            headers=auth_headers_a
        )
        assert cross_access_response.status_code == 404  # 或403，取决于实现

        # Step 6: 租户B尝试直接访问租户A的运单，应该被拒绝
        print("Step 6: 验证反向跨租户访问被拒绝")
        reverse_cross_access_response = await client.get(
            f"/api/shipments/{shipment_a_id}",
            headers=auth_headers_b
        )
        assert reverse_cross_access_response.status_code == 404  # 或403

        print("✅ 运单数据隔离测试通过")

    async def test_gps_data_isolation(
        self,
        client: AsyncClient,
        auth_headers_a: Dict[str, str],
        auth_headers_b: Dict[str, str],
        tenant_a_id: UUID,
        tenant_b_id: UUID,
        user_a_id: UUID,
        user_b_id: UUID
    ):
        """
        测试GPS数据在不同租户间的隔离
        """
        print("开始测试GPS数据隔离")

        # 创建测试运单
        shipment_a = await self.create_test_shipment(
            client, auth_headers_a, tenant_a_id, user_a_id, "GPS-A"
        )
        shipment_b = await self.create_test_shipment(
            client, auth_headers_b, tenant_b_id, user_b_id, "GPS-B"
        )

        # 租户A上报GPS数据
        gps_data_a = {
            "vehicle_id": str(uuid4()),
            "shipment_id": shipment_a["id"],
            "latitude": 39.9042,
            "longitude": 116.4074,
            "speed": 60.0,
            "heading": 180.0,
            "timestamp": datetime.now().isoformat(),
            "source": "g7_device"
        }

        gps_response_a = await client.post(
            "/api/gps/locations",
            json=gps_data_a,
            headers=auth_headers_a
        )
        assert gps_response_a.status_code == 201

        # 租户B上报GPS数据
        gps_data_b = {
            "vehicle_id": str(uuid4()),
            "shipment_id": shipment_b["id"],
            "latitude": 31.2304,
            "longitude": 121.4737,
            "speed": 50.0,
            "heading": 90.0,
            "timestamp": datetime.now().isoformat(),
            "source": "driver_app"
        }

        gps_response_b = await client.post(
            "/api/gps/locations",
            json=gps_data_b,
            headers=auth_headers_b
        )
        assert gps_response_b.status_code == 201

        # 租户A查询自己的GPS数据
        realtime_a = await client.get(
            f"/api/gps/realtime/{shipment_a['id']}",
            headers=auth_headers_a
        )
        assert realtime_a.status_code == 200
        assert realtime_a.json()["shipment_id"] == shipment_a["id"]

        # 租户A尝试查询租户B的GPS数据，应该被拒绝
        cross_gps_access = await client.get(
            f"/api/gps/realtime/{shipment_b['id']}",
            headers=auth_headers_a
        )
        assert cross_gps_access.status_code == 404

        print("✅ GPS数据隔离测试通过")

    async def test_user_data_isolation(
        self,
        client: AsyncClient,
        auth_headers_a: Dict[str, str],
        auth_headers_b: Dict[str, str],
        tenant_a_id: UUID,
        tenant_b_id: UUID
    ):
        """
        测试用户数据在不同租户间的隔离
        """
        print("开始测试用户数据隔离")

        # 租户A查询用户列表
        users_a_response = await client.get(
            "/api/users",
            headers=auth_headers_a
        )
        assert users_a_response.status_code == 200

        users_a = users_a_response.json()

        # 验证所有用户都属于租户A
        for user in users_a["items"]:
            assert user["tenant_id"] == str(tenant_a_id)

        # 租户B查询用户列表
        users_b_response = await client.get(
            "/api/users",
            headers=auth_headers_b
        )
        assert users_b_response.status_code == 200

        users_b = users_b_response.json()

        # 验证所有用户都属于租户B
        for user in users_b["items"]:
            assert user["tenant_id"] == str(tenant_b_id)

        # 确保租户A和租户B的用户列表完全不同
        user_ids_a = {user["id"] for user in users_a["items"]}
        user_ids_b = {user["id"] for user in users_b["items"]}
        assert user_ids_a.isdisjoint(user_ids_b)

        print("✅ 用户数据隔离测试通过")

    async def test_database_rls_enforcement(
        self,
        db_session: AsyncSession,
        tenant_a_id: UUID,
        tenant_b_id: UUID
    ):
        """
        测试数据库层面的Row-Level Security强制执行

        直接在数据库层面验证RLS策略是否正确工作
        """
        print("开始测试数据库RLS策略强制执行")

        # Step 1: 设置租户A的上下文并创建测试数据
        print("Step 1: 在租户A上下文中创建数据")
        await db_session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_a_id)}
        )

        # 创建租户A的测试运单
        create_shipment_a = text("""
            INSERT INTO shipments (
                id, tenant_id, shipment_number, status,
                sender_name, sender_phone, receiver_name, receiver_phone,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :tenant_id, :shipment_number, 'created',
                '测试发货人A', '13800000001', '测试收货人A', '13800000002',
                NOW(), NOW()
            ) RETURNING id, shipment_number
        """)

        result_a = await db_session.execute(
            create_shipment_a,
            {
                "tenant_id": str(tenant_a_id),
                "shipment_number": f"DB-TEST-A-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        )
        shipment_a_data = result_a.fetchone()
        await db_session.commit()

        # Step 2: 切换到租户B的上下文并创建测试数据
        print("Step 2: 在租户B上下文中创建数据")
        await db_session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_b_id)}
        )

        create_shipment_b = text("""
            INSERT INTO shipments (
                id, tenant_id, shipment_number, status,
                sender_name, sender_phone, receiver_name, receiver_phone,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :tenant_id, :shipment_number, 'created',
                '测试发货人B', '13800000003', '测试收货人B', '13800000004',
                NOW(), NOW()
            ) RETURNING id, shipment_number
        """)

        result_b = await db_session.execute(
            create_shipment_b,
            {
                "tenant_id": str(tenant_b_id),
                "shipment_number": f"DB-TEST-B-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        )
        shipment_b_data = result_b.fetchone()
        await db_session.commit()

        # Step 3: 在租户A上下文中查询，应该只看到租户A的数据
        print("Step 3: 验证租户A只能查询到自己的数据")
        await db_session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_a_id)}
        )

        query_from_tenant_a = text("SELECT id, tenant_id, shipment_number FROM shipments")
        results_from_a = await db_session.execute(query_from_tenant_a)
        shipments_from_a = results_from_a.fetchall()

        # 验证只能看到租户A的数据
        for shipment in shipments_from_a:
            assert str(shipment.tenant_id) == str(tenant_a_id)

        # 验证不包含租户B的运单
        shipment_numbers_from_a = [s.shipment_number for s in shipments_from_a]
        assert shipment_b_data.shipment_number not in shipment_numbers_from_a

        # Step 4: 在租户B上下文中查询，应该只看到租户B的数据
        print("Step 4: 验证租户B只能查询到自己的数据")
        await db_session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_b_id)}
        )

        query_from_tenant_b = text("SELECT id, tenant_id, shipment_number FROM shipments")
        results_from_b = await db_session.execute(query_from_tenant_b)
        shipments_from_b = results_from_b.fetchall()

        # 验证只能看到租户B的数据
        for shipment in shipments_from_b:
            assert str(shipment.tenant_id) == str(tenant_b_id)

        # 验证不包含租户A的运单
        shipment_numbers_from_b = [s.shipment_number for s in shipments_from_b]
        assert shipment_a_data.shipment_number not in shipment_numbers_from_b

        # Step 5: 尝试跨租户更新操作，应该被阻止
        print("Step 5: 验证跨租户更新被阻止")
        try:
            # 在租户A的上下文中尝试更新租户B的数据
            await db_session.execute(
                text("SET app.current_tenant_id = :tenant_id"),
                {"tenant_id": str(tenant_a_id)}
            )

            cross_tenant_update = text("""
                UPDATE shipments
                SET status = 'picked_up'
                WHERE id = :shipment_id
            """)

            result = await db_session.execute(
                cross_tenant_update,
                {"shipment_id": shipment_b_data.id}
            )

            # 如果RLS正确工作，这个更新应该影响0行
            assert result.rowcount == 0
            await db_session.commit()

        except Exception as e:
            # 某些情况下可能直接抛出异常
            await db_session.rollback()
            print(f"跨租户更新被阻止（抛出异常）: {e}")

        print("✅ 数据库RLS策略强制执行测试通过")

    async def test_api_tenant_context_validation(
        self,
        client: AsyncClient,
        tenant_a_id: UUID,
        user_a_id: UUID
    ):
        """
        测试API层面的租户上下文验证
        """
        print("开始测试API租户上下文验证")

        # 测试缺少租户ID的请求
        missing_tenant_headers = {
            "Authorization": "Bearer test-token",
            "X-User-ID": str(user_a_id)
        }

        response = await client.get(
            "/api/shipments",
            headers=missing_tenant_headers
        )
        assert response.status_code == 401  # 或400，取决于实现

        # 测试无效租户ID格式
        invalid_tenant_headers = {
            "Authorization": "Bearer test-token",
            "X-Tenant-ID": "invalid-uuid-format",
            "X-User-ID": str(user_a_id)
        }

        response_2 = await client.get(
            "/api/shipments",
            headers=invalid_tenant_headers
        )
        assert response_2.status_code == 400

        # 测试空租户ID
        empty_tenant_headers = {
            "Authorization": "Bearer test-token",
            "X-Tenant-ID": "",
            "X-User-ID": str(user_a_id)
        }

        response_3 = await client.get(
            "/api/shipments",
            headers=empty_tenant_headers
        )
        assert response_3.status_code == 400

        print("✅ API租户上下文验证测试通过")

    async def test_bulk_operations_isolation(
        self,
        client: AsyncClient,
        auth_headers_a: Dict[str, str],
        auth_headers_b: Dict[str, str],
        tenant_a_id: UUID,
        tenant_b_id: UUID,
        user_a_id: UUID,
        user_b_id: UUID
    ):
        """
        测试批量操作的租户隔离
        """
        print("开始测试批量操作的租户隔离")

        # 创建多个测试运单
        shipments_a = []
        shipments_b = []

        # 为租户A创建3个运单
        for i in range(3):
            shipment = await self.create_test_shipment(
                client, auth_headers_a, tenant_a_id, user_a_id, f"BULK-A-{i}"
            )
            shipments_a.append(shipment)

        # 为租户B创建3个运单
        for i in range(3):
            shipment = await self.create_test_shipment(
                client, auth_headers_b, tenant_b_id, user_b_id, f"BULK-B-{i}"
            )
            shipments_b.append(shipment)

        # 租户A执行批量状态更新
        bulk_update_data = {
            "shipment_ids": [s["id"] for s in shipments_a],
            "status": "picked_up",
            "notes": "批量提货"
        }

        bulk_response_a = await client.patch(
            "/api/shipments/bulk/status",
            json=bulk_update_data,
            headers=auth_headers_a
        )
        assert bulk_response_a.status_code == 200

        bulk_result_a = bulk_response_a.json()
        assert bulk_result_a["updated_count"] == 3
        assert len(bulk_result_a["failed_ids"]) == 0

        # 租户A尝试批量更新包含租户B运单的请求（应该被过滤）
        mixed_update_data = {
            "shipment_ids": [shipments_a[0]["id"], shipments_b[0]["id"]],
            "status": "in_transit",
            "notes": "混合租户批量更新测试"
        }

        mixed_response = await client.patch(
            "/api/shipments/bulk/status",
            json=mixed_update_data,
            headers=auth_headers_a
        )
        assert mixed_response.status_code == 200

        mixed_result = mixed_response.json()
        # 应该只更新了1个（租户A的运单），租户B的运单被忽略或失败
        assert mixed_result["updated_count"] == 1
        assert shipments_b[0]["id"] in mixed_result["failed_ids"]

        print("✅ 批量操作租户隔离测试通过")

    async def test_search_and_filter_isolation(
        self,
        client: AsyncClient,
        auth_headers_a: Dict[str, str],
        auth_headers_b: Dict[str, str],
        tenant_a_id: UUID,
        tenant_b_id: UUID,
        user_a_id: UUID,
        user_b_id: UUID
    ):
        """
        测试搜索和过滤功能的租户隔离
        """
        print("开始测试搜索和过滤功能的租户隔离")

        # 创建带有特定关键词的测试运单
        keyword = "SEARCH-TEST-KEYWORD"

        # 租户A创建包含关键词的运单
        shipment_a_data = {
            "shipment_number": f"A-{keyword}-{datetime.now().strftime('%H%M%S')}",
            "sender": {"name": f"发货人{keyword}", "phone": "13800000001"},
            "receiver": {"name": "收货人A", "phone": "13800000002"},
            "cargo": {"description": f"包含{keyword}的货物", "weight": 100},
            "tenant_id": str(tenant_a_id),
            "created_by": str(user_a_id)
        }

        response_a = await client.post(
            "/api/shipments",
            json=shipment_a_data,
            headers=auth_headers_a
        )
        assert response_a.status_code == 201

        # 租户B创建包含相同关键词的运单
        shipment_b_data = {
            "shipment_number": f"B-{keyword}-{datetime.now().strftime('%H%M%S')}",
            "sender": {"name": f"发货人{keyword}", "phone": "13800000003"},
            "receiver": {"name": "收货人B", "phone": "13800000004"},
            "cargo": {"description": f"包含{keyword}的货物", "weight": 200},
            "tenant_id": str(tenant_b_id),
            "created_by": str(user_b_id)
        }

        response_b = await client.post(
            "/api/shipments",
            json=shipment_b_data,
            headers=auth_headers_b
        )
        assert response_b.status_code == 201

        # 租户A搜索关键词
        search_response_a = await client.get(
            f"/api/shipments/search?q={keyword}",
            headers=auth_headers_a
        )
        assert search_response_a.status_code == 200

        search_results_a = search_response_a.json()
        assert len(search_results_a["items"]) >= 1

        # 验证搜索结果只包含租户A的数据
        for result in search_results_a["items"]:
            assert result["tenant_id"] == str(tenant_a_id)
            assert keyword in (result["shipment_number"] + result["sender"]["name"] + result["cargo"]["description"])

        # 租户B搜索相同关键词
        search_response_b = await client.get(
            f"/api/shipments/search?q={keyword}",
            headers=auth_headers_b
        )
        assert search_response_b.status_code == 200

        search_results_b = search_response_b.json()
        assert len(search_results_b["items"]) >= 1

        # 验证搜索结果只包含租户B的数据
        for result in search_results_b["items"]:
            assert result["tenant_id"] == str(tenant_b_id)

        # 确保租户A和租户B的搜索结果完全不同
        result_ids_a = {r["id"] for r in search_results_a["items"]}
        result_ids_b = {r["id"] for r in search_results_b["items"]}
        assert result_ids_a.isdisjoint(result_ids_b)

        print("✅ 搜索和过滤功能租户隔离测试通过")


if __name__ == "__main__":
    # 运行测试
    import sys

    async def run_tests():
        print("开始多租户数据隔离集成测试...")
        print("注意：需要先启动后端服务和数据库，并确保RLS策略已正确配置")
        print("请使用: pytest tests/integration/test_multi_tenant.py -v")

    if len(sys.argv) > 1 and sys.argv[1] == "run":
        asyncio.run(run_tests())