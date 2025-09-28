#!/usr/bin/env python3
"""
创建10条真实的测试运单数据
包含完整的发货地址、收货地址、GPS路线等信息
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.logistics import Shipment, ShipmentStatus
from models.gps import GPSLocation
from models.users import User
from core.config import get_settings
import json

# 真实的测试运单数据
TEST_SHIPMENTS = [
    {
        "shipment_number": "DD20250928001",
        "sender_name": "深圳富士康科技集团",
        "sender_phone": "0755-8888-8888",
        "sender_address": "广东省深圳市宝安区西乡街道富士康工业园A区",
        "receiver_name": "上海苹果专卖店",
        "receiver_phone": "021-6666-6666",
        "receiver_address": "上海市浦东新区陆家嘴环路1000号恒生银行大厦1楼",
        "goods_name": "iPhone 15 Pro手机配件",
        "goods_weight": 15.5,
        "goods_volume": 0.8,
        "transport_mode": "陆运",
        "route": [
            {"name": "深圳", "lat": 22.5431, "lng": 114.0579, "time": "2025-09-28 08:00:00"},
            {"name": "广州", "lat": 23.1291, "lng": 113.2644, "time": "2025-09-28 12:30:00"},
            {"name": "武汉", "lat": 30.5928, "lng": 114.3055, "time": "2025-09-29 02:15:00"},
            {"name": "南京", "lat": 32.0603, "lng": 118.7969, "time": "2025-09-29 14:45:00"},
            {"name": "上海", "lat": 31.2304, "lng": 121.4737, "time": "2025-09-30 08:20:00"}
        ]
    },
    {
        "shipment_number": "DD20250928002",
        "sender_name": "北京小米科技有限公司",
        "sender_phone": "010-5555-5555",
        "sender_address": "北京市海淀区清河中街68号华润五彩城购物中心",
        "receiver_name": "广州小米之家",
        "receiver_phone": "020-8888-8888",
        "receiver_address": "广东省广州市天河区天河路208号天河城百货B1楼",
        "goods_name": "小米14手机及智能家居产品",
        "goods_weight": 28.3,
        "goods_volume": 1.5,
        "transport_mode": "陆运",
        "route": [
            {"name": "北京", "lat": 39.9042, "lng": 116.4074, "time": "2025-09-28 09:30:00"},
            {"name": "天津", "lat": 39.3434, "lng": 117.3616, "time": "2025-09-28 13:00:00"},
            {"name": "济南", "lat": 36.6512, "lng": 117.1201, "time": "2025-09-28 20:45:00"},
            {"name": "徐州", "lat": 34.2041, "lng": 117.2839, "time": "2025-09-29 06:30:00"},
            {"name": "武汉", "lat": 30.5928, "lng": 114.3055, "time": "2025-09-29 16:15:00"},
            {"name": "广州", "lat": 23.1291, "lng": 113.2644, "time": "2025-09-30 10:00:00"}
        ]
    },
    {
        "shipment_number": "DD20250928003",
        "sender_name": "杭州阿里巴巴网络技术有限公司",
        "sender_phone": "0571-7777-7777",
        "sender_address": "浙江省杭州市余杭区文一西路969号阿里巴巴西溪园区",
        "receiver_name": "成都天府软件园",
        "receiver_phone": "028-9999-9999",
        "receiver_address": "四川省成都市高新区天府软件园E区6号楼",
        "goods_name": "服务器设备及网络设备",
        "goods_weight": 185.7,
        "goods_volume": 12.3,
        "transport_mode": "陆运",
        "route": [
            {"name": "杭州", "lat": 30.2741, "lng": 120.1551, "time": "2025-09-28 07:45:00"},
            {"name": "南昌", "lat": 28.6820, "lng": 115.8582, "time": "2025-09-28 15:20:00"},
            {"name": "长沙", "lat": 28.2278, "lng": 112.9388, "time": "2025-09-28 22:10:00"},
            {"name": "重庆", "lat": 29.5630, "lng": 106.5516, "time": "2025-09-29 08:40:00"},
            {"name": "成都", "lat": 30.5728, "lng": 104.0668, "time": "2025-09-29 14:30:00"}
        ]
    },
    {
        "shipment_number": "DD20250928004",
        "sender_name": "青岛海尔集团股份有限公司",
        "sender_phone": "0532-1111-1111",
        "sender_address": "山东省青岛市崂山区海尔路1号海尔工业园",
        "receiver_name": "西安苏宁电器",
        "receiver_phone": "029-2222-2222",
        "receiver_address": "陕西省西安市雁塔区长安南路449号丽都商城",
        "goods_name": "海尔冰箱洗衣机空调",
        "goods_weight": 520.8,
        "goods_volume": 25.6,
        "transport_mode": "陆运",
        "route": [
            {"name": "青岛", "lat": 36.0671, "lng": 120.3826, "time": "2025-09-28 06:00:00"},
            {"name": "济南", "lat": 36.6512, "lng": 117.1201, "time": "2025-09-28 11:15:00"},
            {"name": "太原", "lat": 37.8706, "lng": 112.5489, "time": "2025-09-28 18:30:00"},
            {"name": "西安", "lat": 34.3416, "lng": 108.9398, "time": "2025-09-29 03:45:00"}
        ]
    },
    {
        "shipment_number": "DD20250928005",
        "sender_name": "长春一汽集团",
        "sender_phone": "0431-3333-3333",
        "sender_address": "吉林省长春市绿园区创业大街2888号一汽红旗工厂",
        "receiver_name": "海南三亚红旗4S店",
        "receiver_phone": "0898-4444-4444",
        "receiver_address": "海南省三亚市天涯区三亚湾路88号红旗汽车展厅",
        "goods_name": "红旗H9汽车配件",
        "goods_weight": 320.5,
        "goods_volume": 18.9,
        "transport_mode": "陆运+海运",
        "route": [
            {"name": "长春", "lat": 43.8171, "lng": 125.3235, "time": "2025-09-28 10:00:00"},
            {"name": "沈阳", "lat": 41.8057, "lng": 123.4315, "time": "2025-09-28 15:30:00"},
            {"name": "北京", "lat": 39.9042, "lng": 116.4074, "time": "2025-09-29 01:20:00"},
            {"name": "广州", "lat": 23.1291, "lng": 113.2644, "time": "2025-09-29 18:45:00"},
            {"name": "海口", "lat": 20.0444, "lng": 110.1989, "time": "2025-09-30 08:15:00"},
            {"name": "三亚", "lat": 18.2528, "lng": 109.5120, "time": "2025-09-30 12:00:00"}
        ]
    },
    {
        "shipment_number": "DD20250928006",
        "sender_name": "新疆阿克苏纺织工业园",
        "sender_phone": "0997-5555-5555",
        "sender_address": "新疆维吾尔自治区阿克苏地区阿克苏市纺织工业园区",
        "receiver_name": "广州白马服装市场",
        "receiver_phone": "020-7777-7777",
        "receiver_address": "广东省广州市越秀区站南路16号白马服装市场",
        "goods_name": "优质棉花及纺织品",
        "goods_weight": 1250.0,
        "goods_volume": 68.5,
        "transport_mode": "陆运",
        "route": [
            {"name": "阿克苏", "lat": 41.1717, "lng": 80.2648, "time": "2025-09-28 05:30:00"},
            {"name": "乌鲁木齐", "lat": 43.8256, "lng": 87.6168, "time": "2025-09-28 12:45:00"},
            {"name": "兰州", "lat": 36.0611, "lng": 103.8343, "time": "2025-09-29 08:20:00"},
            {"name": "西安", "lat": 34.3416, "lng": 108.9398, "time": "2025-09-29 18:30:00"},
            {"name": "武汉", "lat": 30.5928, "lng": 114.3055, "time": "2025-09-30 06:15:00"},
            {"name": "广州", "lat": 23.1291, "lng": 113.2644, "time": "2025-09-30 16:45:00"}
        ]
    },
    {
        "shipment_number": "DD20250928007",
        "sender_name": "昆明云南白药集团",
        "sender_phone": "0871-6666-6666",
        "sender_address": "云南省昆明市呈贡区云南白药街3686号",
        "receiver_name": "哈尔滨医科大学附属医院",
        "receiver_phone": "0451-8888-8888",
        "receiver_address": "黑龙江省哈尔滨市南岗区邮政街23号",
        "goods_name": "云南白药系列药品",
        "goods_weight": 85.3,
        "goods_volume": 5.2,
        "transport_mode": "空运+陆运",
        "route": [
            {"name": "昆明", "lat": 25.0389, "lng": 102.7180, "time": "2025-09-28 14:00:00"},
            {"name": "重庆", "lat": 29.5630, "lng": 106.5516, "time": "2025-09-28 17:30:00"},
            {"name": "北京", "lat": 39.9042, "lng": 116.4074, "time": "2025-09-28 21:15:00"},
            {"name": "哈尔滨", "lat": 45.8038, "lng": 126.5349, "time": "2025-09-29 08:45:00"}
        ]
    },
    {
        "shipment_number": "DD20250928008",
        "sender_name": "福建泉州安踏体育用品",
        "sender_phone": "0595-9999-9999",
        "sender_address": "福建省泉州市晋江市池店镇安踏工业园",
        "receiver_name": "内蒙古呼和浩特安踏专卖店",
        "receiver_phone": "0471-1234-5678",
        "receiver_address": "内蒙古自治区呼和浩特市赛罕区万达广场2楼安踏专卖店",
        "goods_name": "安踏运动鞋服装",
        "goods_weight": 180.7,
        "goods_volume": 15.8,
        "transport_mode": "陆运",
        "route": [
            {"name": "泉州", "lat": 24.8740, "lng": 118.6751, "time": "2025-09-28 11:20:00"},
            {"name": "南昌", "lat": 28.6820, "lng": 115.8582, "time": "2025-09-28 18:45:00"},
            {"name": "郑州", "lat": 34.7466, "lng": 113.6254, "time": "2025-09-29 03:30:00"},
            {"name": "太原", "lat": 37.8706, "lng": 112.5489, "time": "2025-09-29 10:15:00"},
            {"name": "呼和浩特", "lat": 40.8414, "lng": 111.7519, "time": "2025-09-29 16:40:00"}
        ]
    },
    {
        "shipment_number": "DD20250928009",
        "sender_name": "拉萨高原特产有限公司",
        "sender_phone": "0891-7777-7777",
        "sender_address": "西藏自治区拉萨市城关区北京中路5号民族文化宫",
        "receiver_name": "南京德基广场藏式精品店",
        "receiver_phone": "025-5555-5555",
        "receiver_address": "江苏省南京市玄武区中山路18号德基广场二期3楼",
        "goods_name": "藏红花、虫草、牦牛肉干",
        "goods_weight": 25.8,
        "goods_volume": 2.1,
        "transport_mode": "空运+陆运",
        "route": [
            {"name": "拉萨", "lat": 29.6520, "lng": 91.1721, "time": "2025-09-28 13:45:00"},
            {"name": "成都", "lat": 30.5728, "lng": 104.0668, "time": "2025-09-28 18:20:00"},
            {"name": "武汉", "lat": 30.5928, "lng": 114.3055, "time": "2025-09-29 02:10:00"},
            {"name": "南京", "lat": 32.0603, "lng": 118.7969, "time": "2025-09-29 08:35:00"}
        ]
    },
    {
        "shipment_number": "DD20250928010",
        "sender_name": "厦门金龙客车制造有限公司",
        "sender_phone": "0592-1111-1111",
        "sender_address": "福建省厦门市集美区杏林湾营运中心金龙路89号",
        "receiver_name": "银川公交集团",
        "receiver_phone": "0951-2222-2222",
        "receiver_address": "宁夏回族自治区银川市兴庆区解放东街106号",
        "goods_name": "金龙客车配件及维修工具",
        "goods_weight": 450.2,
        "goods_volume": 28.7,
        "transport_mode": "陆运",
        "route": [
            {"name": "厦门", "lat": 24.4798, "lng": 118.0894, "time": "2025-09-28 08:15:00"},
            {"name": "南昌", "lat": 28.6820, "lng": 115.8582, "time": "2025-09-28 16:40:00"},
            {"name": "武汉", "lat": 30.5928, "lng": 114.3055, "time": "2025-09-28 23:25:00"},
            {"name": "西安", "lat": 34.3416, "lng": 108.9398, "time": "2025-09-29 09:50:00"},
            {"name": "银川", "lat": 38.4872, "lng": 106.2309, "time": "2025-09-29 16:30:00"}
        ]
    }
]

async def create_test_data():
    """创建测试运单数据"""
    try:
        # 连接数据库 - 转换异步URL为同步URL
        settings = get_settings()
        database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        session = SessionLocal()

        # 检查是否有测试用户
        test_user = session.query(User).filter_by(username="13800138000").first()
        if not test_user:
            print("错误: 测试用户不存在，请先通过前端登录创建测试用户")
            return False

        print(f"使用测试用户: {test_user.username} (ID: {test_user.id})")

        # 删除现有测试数据（如果存在）
        session.execute(text("DELETE FROM shipments WHERE shipment_number LIKE 'DD20250928%'"))
        session.commit()
        print("已清理现有测试数据")

        # 创建新的测试运单
        for i, shipment_data in enumerate(TEST_SHIPMENTS, 1):
            print(f"创建运单 {i}/10: {shipment_data['shipment_number']}")

            # 计算状态和时间
            created_at = datetime.now() - timedelta(days=2-i*0.2)
            route_data = shipment_data['route']

            # 根据路线确定当前状态
            current_time = datetime.now()
            current_status = ShipmentStatus.PENDING
            current_location_idx = 0

            for idx, point in enumerate(route_data):
                point_time = datetime.strptime(point['time'], '%Y-%m-%d %H:%M:%S')
                if current_time >= point_time:
                    current_location_idx = idx
                    if idx == 0:
                        current_status = ShipmentStatus.IN_TRANSIT
                    elif idx == len(route_data) - 1:
                        current_status = ShipmentStatus.DELIVERED
                    else:
                        current_status = ShipmentStatus.IN_TRANSIT
                else:
                    break

            # 创建运单 - 使用正确的字段名
            start_point = route_data[0]
            end_point = route_data[-1]

            shipment = Shipment(
                shipment_number=shipment_data['shipment_number'],
                pickup_address=shipment_data['sender_address'],
                delivery_address=shipment_data['receiver_address'],
                customer_name=shipment_data['sender_name'],
                transport_mode=shipment_data['transport_mode'],
                weight_kg=Decimal(str(shipment_data['goods_weight'])),
                commodity_type=shipment_data['goods_name'],
                status=current_status,
                pickup_coordinates=[start_point['lng'], start_point['lat']],
                delivery_coordinates=[end_point['lng'], end_point['lat']],
                notes=f"发货人: {shipment_data['sender_name']} ({shipment_data['sender_phone']})\n收货人: {shipment_data['receiver_name']} ({shipment_data['receiver_phone']})",
                created_by_id=test_user.id,
                tenant_id=test_user.tenant_id,
                created_at=created_at,
                updated_at=datetime.now()
            )

            session.add(shipment)
            session.flush()  # 获取shipment.id

            # 创建GPS轨迹数据
            for idx, point in enumerate(route_data):
                point_time = datetime.strptime(point['time'], '%Y-%m-%d %H:%M:%S')

                # 只添加已经发生的GPS点
                if current_time >= point_time:
                    gps_location = GPSLocation(
                        shipment_id=shipment.id,
                        latitude=Decimal(str(point['lat'])),
                        longitude=Decimal(str(point['lng'])),
                        gps_time=point_time,
                        address=point['name'],
                        city=point['name'],
                        speed=Decimal('60.5'),  # 模拟速度
                        heading=Decimal('90.0'),  # 模拟方向
                        source='manual',
                        is_valid='1',
                        is_real_time='1',
                        tenant_id=test_user.tenant_id,
                        created_at=point_time,
                        updated_at=datetime.now()
                    )
                    session.add(gps_location)

            print(f"  - 状态: {current_status.value}")
            print(f"  - 路线: {shipment_data['route'][0]['name']} → {shipment_data['route'][-1]['name']}")
            print(f"  - 货物: {shipment_data['goods_name']}")

        # 提交所有数据
        session.commit()
        print("\n✅ 成功创建10条测试运单数据！")

        # 验证数据
        count = session.query(Shipment).filter(Shipment.shipment_number.like('DD20250928%')).count()
        print(f"数据库中共有 {count} 条测试运单")

        session.close()
        return True

    except Exception as e:
        print(f"❌ 创建测试数据失败: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

if __name__ == "__main__":
    asyncio.run(create_test_data())