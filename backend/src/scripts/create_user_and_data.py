#!/usr/bin/env python3
"""
创建测试用户和运单数据
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.logistics import Shipment, ShipmentStatus
from models.gps import GPSLocation
from models.users import User, UserRole
from models.base import Tenant
from core.config import get_settings
import hashlib

def hash_password(password: str) -> str:
    # 简单的SHA256哈希用于测试
    return hashlib.sha256(password.encode()).hexdigest()

async def create_test_user_and_data():
    """创建测试用户和运单数据"""
    try:
        # 连接数据库
        settings = get_settings()
        database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        session = SessionLocal()

        # 先创建租户
        test_tenant = session.query(Tenant).filter_by(code="test-tenant").first()
        if not test_tenant:
            print("创建测试租户...")
            test_tenant = Tenant(
                id=uuid.uuid4(),
                name="测试公司",
                code="test-tenant",
                is_active="1"
            )
            session.add(test_tenant)
            session.commit()
            print(f"✅ 测试租户创建成功: {test_tenant.name}")
        else:
            print(f"✅ 测试租户已存在: {test_tenant.name}")

        # 创建测试用户
        test_user = session.query(User).filter_by(username="13800138000").first()
        if not test_user:
            print("创建测试用户...")
            test_user = User(
                id=uuid.uuid4(),
                username="13800138000",
                email="test@example.com",
                phone="13800138000",
                full_name="测试用户",
                role=UserRole.ADMIN,
                tenant_id=test_tenant.id,
                password_hash=hash_password("8888"),
                is_active=True,
                is_verified=True,
                login_count="0",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(test_user)
            session.commit()
            print(f"✅ 测试用户创建成功: {test_user.username}")
        else:
            print(f"✅ 测试用户已存在: {test_user.username}")

        # 简化的测试运单数据
        test_shipments = [
            {
                "shipment_number": "DD20250928001",
                "pickup_address": "广东省深圳市宝安区西乡街道富士康工业园A区",
                "delivery_address": "上海市浦东新区陆家嘴环路1000号恒生银行大厦1楼",
                "customer_name": "深圳富士康科技集团",
                "commodity_type": "iPhone 15 Pro手机配件",
                "weight_kg": 15.5,
                "transport_mode": "陆运",
                "pickup_coords": [114.0579, 22.5431],
                "delivery_coords": [121.4737, 31.2304],
                "status": ShipmentStatus.IN_TRANSIT
            },
            {
                "shipment_number": "DD20250928002",
                "pickup_address": "北京市海淀区清河中街68号华润五彩城购物中心",
                "delivery_address": "广东省广州市天河区天河路208号天河城百货B1楼",
                "customer_name": "北京小米科技有限公司",
                "commodity_type": "小米14手机及智能家居产品",
                "weight_kg": 28.3,
                "transport_mode": "陆运",
                "pickup_coords": [116.4074, 39.9042],
                "delivery_coords": [113.2644, 23.1291],
                "status": ShipmentStatus.IN_TRANSIT
            },
            {
                "shipment_number": "DD20250928003",
                "pickup_address": "浙江省杭州市余杭区文一西路969号阿里巴巴西溪园区",
                "delivery_address": "四川省成都市高新区天府软件园E区6号楼",
                "customer_name": "杭州阿里巴巴网络技术有限公司",
                "commodity_type": "服务器设备及网络设备",
                "weight_kg": 185.7,
                "transport_mode": "陆运",
                "pickup_coords": [120.1551, 30.2741],
                "delivery_coords": [104.0668, 30.5728],
                "status": ShipmentStatus.DELIVERED
            },
            {
                "shipment_number": "DD20250928004",
                "pickup_address": "山东省青岛市崂山区海尔路1号海尔工业园",
                "delivery_address": "陕西省西安市雁塔区长安南路449号丽都商城",
                "customer_name": "青岛海尔集团股份有限公司",
                "commodity_type": "海尔冰箱洗衣机空调",
                "weight_kg": 520.8,
                "transport_mode": "陆运",
                "pickup_coords": [120.3826, 36.0671],
                "delivery_coords": [108.9398, 34.3416],
                "status": ShipmentStatus.IN_TRANSIT
            },
            {
                "shipment_number": "DD20250928005",
                "pickup_address": "吉林省长春市绿园区创业大街2888号一汽红旗工厂",
                "delivery_address": "海南省三亚市天涯区三亚湾路88号红旗汽车展厅",
                "customer_name": "长春一汽集团",
                "commodity_type": "红旗H9汽车配件",
                "weight_kg": 320.5,
                "transport_mode": "陆运+海运",
                "pickup_coords": [125.3235, 43.8171],
                "delivery_coords": [109.5120, 18.2528],
                "status": ShipmentStatus.ASSIGNED
            },
            {
                "shipment_number": "DD20250928006",
                "pickup_address": "新疆维吾尔自治区阿克苏地区阿克苏市纺织工业园区",
                "delivery_address": "广东省广州市越秀区站南路16号白马服装市场",
                "customer_name": "新疆阿克苏纺织工业园",
                "commodity_type": "优质棉花及纺织品",
                "weight_kg": 1250.0,
                "transport_mode": "陆运",
                "pickup_coords": [80.2648, 41.1717],
                "delivery_coords": [113.2644, 23.1291],
                "status": ShipmentStatus.IN_TRANSIT
            },
            {
                "shipment_number": "DD20250928007",
                "pickup_address": "云南省昆明市呈贡区云南白药街3686号",
                "delivery_address": "黑龙江省哈尔滨市南岗区邮政街23号",
                "customer_name": "昆明云南白药集团",
                "commodity_type": "云南白药系列药品",
                "weight_kg": 85.3,
                "transport_mode": "空运+陆运",
                "pickup_coords": [102.7180, 25.0389],
                "delivery_coords": [126.5349, 45.8038],
                "status": ShipmentStatus.DELIVERED
            },
            {
                "shipment_number": "DD20250928008",
                "pickup_address": "福建省泉州市晋江市池店镇安踏工业园",
                "delivery_address": "内蒙古自治区呼和浩特市赛罕区万达广场2楼安踏专卖店",
                "customer_name": "福建泉州安踏体育用品",
                "commodity_type": "安踏运动鞋服装",
                "weight_kg": 180.7,
                "transport_mode": "陆运",
                "pickup_coords": [118.6751, 24.8740],
                "delivery_coords": [111.7519, 40.8414],
                "status": ShipmentStatus.IN_TRANSIT
            },
            {
                "shipment_number": "DD20250928009",
                "pickup_address": "西藏自治区拉萨市城关区北京中路5号民族文化宫",
                "delivery_address": "江苏省南京市玄武区中山路18号德基广场二期3楼",
                "customer_name": "拉萨高原特产有限公司",
                "commodity_type": "藏红花、虫草、牦牛肉干",
                "weight_kg": 25.8,
                "transport_mode": "空运+陆运",
                "pickup_coords": [91.1721, 29.6520],
                "delivery_coords": [118.7969, 32.0603],
                "status": ShipmentStatus.DISPATCHED
            },
            {
                "shipment_number": "DD20250928010",
                "pickup_address": "福建省厦门市集美区杏林湾营运中心金龙路89号",
                "delivery_address": "宁夏回族自治区银川市兴庆区解放东街106号",
                "customer_name": "厦门金龙客车制造有限公司",
                "commodity_type": "金龙客车配件及维修工具",
                "weight_kg": 450.2,
                "transport_mode": "陆运",
                "pickup_coords": [118.0894, 24.4798],
                "delivery_coords": [106.2309, 38.4872],
                "status": ShipmentStatus.UNASSIGNED
            }
        ]

        # 删除现有测试数据
        session.execute(text("DELETE FROM gps_locations WHERE shipment_id IN (SELECT id FROM shipments WHERE shipment_number LIKE 'DD20250928%')"))
        session.execute(text("DELETE FROM shipments WHERE shipment_number LIKE 'DD20250928%'"))
        session.commit()
        print("已清理现有测试数据")

        # 创建运单数据
        for i, shipment_data in enumerate(test_shipments, 1):
            print(f"创建运单 {i}/10: {shipment_data['shipment_number']}")

            created_at = datetime.now() - timedelta(days=2-i*0.2)

            shipment = Shipment(
                shipment_number=shipment_data['shipment_number'],
                pickup_address=shipment_data['pickup_address'],
                delivery_address=shipment_data['delivery_address'],
                customer_name=shipment_data['customer_name'],
                transport_mode=shipment_data['transport_mode'],
                weight_kg=Decimal(str(shipment_data['weight_kg'])),
                commodity_type=shipment_data['commodity_type'],
                status=shipment_data['status'],
                pickup_coordinates=shipment_data['pickup_coords'],
                delivery_coordinates=shipment_data['delivery_coords'],
                notes=f"货物重量: {shipment_data['weight_kg']}kg",
                tenant_id=test_user.tenant_id
            )

            session.add(shipment)
            session.flush()

            # 为部分运单添加GPS轨迹
            if shipment_data['status'] in [ShipmentStatus.IN_TRANSIT, ShipmentStatus.DELIVERED]:
                # 添加起点GPS数据
                pickup_gps = GPSLocation(
                    shipment_id=shipment.id,
                    latitude=Decimal(str(shipment_data['pickup_coords'][1])),
                    longitude=Decimal(str(shipment_data['pickup_coords'][0])),
                    gps_time=created_at + timedelta(hours=1),
                    address=shipment_data['pickup_address'][:50] + "...",
                    speed=Decimal('0.0'),
                    heading=Decimal('0.0'),
                    source='manual',
                    is_valid='1',
                    is_real_time='1',
                    tenant_id=test_user.tenant_id
                )
                session.add(pickup_gps)

                # 如果已交付，添加终点GPS数据
                if shipment_data['status'] == ShipmentStatus.DELIVERED:
                    delivery_gps = GPSLocation(
                        shipment_id=shipment.id,
                        latitude=Decimal(str(shipment_data['delivery_coords'][1])),
                        longitude=Decimal(str(shipment_data['delivery_coords'][0])),
                        gps_time=created_at + timedelta(days=1),
                        address=shipment_data['delivery_address'][:50] + "...",
                        speed=Decimal('0.0'),
                        heading=Decimal('0.0'),
                        source='manual',
                        is_valid='1',
                        is_real_time='1',
                        tenant_id=test_user.tenant_id
                    )
                    session.add(delivery_gps)

            print(f"  - 状态: {shipment_data['status'].value}")
            print(f"  - 货物: {shipment_data['commodity_type']}")

        # 提交所有数据
        session.commit()
        print("\n✅ 成功创建测试用户和10条运单数据！")

        # 验证数据
        shipment_count = session.query(Shipment).filter(Shipment.shipment_number.like('DD20250928%')).count()
        gps_count = session.query(GPSLocation).filter(GPSLocation.shipment_id.in_(
            session.query(Shipment.id).filter(Shipment.shipment_number.like('DD20250928%'))
        )).count()

        print(f"数据库中共有 {shipment_count} 条测试运单")
        print(f"数据库中共有 {gps_count} 条GPS轨迹数据")

        session.close()
        return True

    except Exception as e:
        print(f"❌ 创建测试数据失败: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_test_user_and_data())