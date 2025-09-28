#!/usr/bin/env python3
"""
测试运单数据脚本
创建测试运单、GPS数据和业务场景
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime, timedelta
import uuid
import random
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_session
from core.security import set_tenant_context
from models.users import Tenant, User
from models.logistics import Shipment, ShipmentStatus, Vehicle
from models.gps import GPSLocation, GPSSource


# 地址和坐标数据
CITIES_DATA = {
    "北京": {
        "addresses": [
            "北京市朝阳区CBD商务区",
            "北京市海淀区中关村科技园",
            "北京市丰台区南四环物流园",
            "北京市顺义区首都机场货运区"
        ],
        "coordinates": [
            [116.4074, 39.9042],  # CBD
            [116.3119, 39.9830],  # 中关村
            [116.2830, 39.8580],  # 丰台
            [116.6544, 40.0486]   # 顺义
        ]
    },
    "上海": {
        "addresses": [
            "上海市浦东新区陆家嘴金融区",
            "上海市徐汇区漕河泾开发区",
            "上海市嘉定区汽车城",
            "上海市青浦区物流园区"
        ],
        "coordinates": [
            [121.4737, 31.2304],  # 浦东
            [121.4692, 31.1796],  # 徐汇
            [121.2655, 31.3743],  # 嘉定
            [121.1244, 31.1515]   # 青浦
        ]
    },
    "深圳": {
        "addresses": [
            "深圳市福田区深圳中心区",
            "深圳市南山区科技园",
            "深圳市龙岗区坂田华为基地",
            "深圳市宝安区国际机场"
        ],
        "coordinates": [
            [114.0579, 22.5431],  # 福田
            [113.9547, 22.5329],  # 南山
            [114.0640, 22.6253],  # 龙岗
            [113.8206, 22.6390]   # 宝安
        ]
    },
    "广州": {
        "addresses": [
            "广州市天河区珠江新城",
            "广州市黄埔区科学城",
            "广州市白云区机场路",
            "广州市番禺区大学城"
        ],
        "coordinates": [
            [113.3221, 23.1291],  # 天河
            [113.4590, 23.1619],  # 黄埔
            [113.2990, 23.1619],  # 白云
            [113.3945, 23.0515]   # 番禺
        ]
    }
}

# 商品类型
COMMODITY_TYPES = [
    "电子产品", "服装纺织", "食品饮料", "化工原料", "机械设备",
    "汽车配件", "建材五金", "医药用品", "日用百货", "图书文具"
]

# 客户名称
CUSTOMER_NAMES = [
    "华为技术有限公司", "腾讯科技(深圳)有限公司", "阿里巴巴集团",
    "百度在线网络技术(北京)有限公司", "京东物流科技有限公司",
    "美团科技有限公司", "字节跳动科技有限公司", "滴滴出行科技有限公司",
    "小米科技有限公司", "比亚迪股份有限公司", "格力电器股份有限公司",
    "海尔智家股份有限公司", "中国石油化工股份有限公司", "中国建筑集团有限公司"
]


async def create_shipments(session: AsyncSession, tenants: list, vehicles: list):
    """创建测试运单"""
    print("创建运单数据...")

    created_shipments = []
    cities = list(CITIES_DATA.keys())

    for tenant in tenants:
        await set_tenant_context(session, tenant.id)
        print(f"\n  为租户 {tenant.name} 创建运单:")

        # 为每个租户创建20-30个运单
        shipment_count = random.randint(20, 30)

        for i in range(shipment_count):
            # 随机选择起始和目的地城市
            pickup_city = random.choice(cities)
            delivery_city = random.choice([c for c in cities if c != pickup_city])

            pickup_data = CITIES_DATA[pickup_city]
            delivery_data = CITIES_DATA[delivery_city]

            pickup_idx = random.randint(0, len(pickup_data["addresses"]) - 1)
            delivery_idx = random.randint(0, len(delivery_data["addresses"]) - 1)

            # 运单基本信息
            shipment_data = {
                "pickup_address": pickup_data["addresses"][pickup_idx],
                "delivery_address": delivery_data["addresses"][delivery_idx],
                "pickup_coordinates": pickup_data["coordinates"][pickup_idx],
                "delivery_coordinates": delivery_data["coordinates"][delivery_idx],
                "customer_name": random.choice(CUSTOMER_NAMES),
                "weight_kg": round(random.uniform(100, 5000), 1),
                "commodity_type": random.choice(COMMODITY_TYPES),
                "transport_mode": random.choice(["整车运输", "零担运输", "快递运输"]),
                "equipment_type": random.choice(["厢式货车", "平板货车", "冷藏车"]),
                "packing_type": random.choice(["纸箱包装", "木箱包装", "托盘包装", "散装"]),
                "notes": f"测试运单 - {pickup_city}到{delivery_city}",
            }

            # 创建时间在过去7天内随机
            created_time = datetime.utcnow() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            # 随机状态分布
            status_weights = [0.1, 0.2, 0.15, 0.25, 0.15, 0.1, 0.05]  # 各状态权重
            statuses = list(ShipmentStatus)
            status = random.choices(statuses, weights=status_weights)[0]

            # 生成运单号
            shipment_number = f"DD{created_time.strftime('%Y%m%d')}{i+1:04d}"

            shipment = Shipment(
                tenant_id=tenant.id,
                shipment_number=shipment_number,
                pickup_address=shipment_data["pickup_address"],
                delivery_address=shipment_data["delivery_address"],
                pickup_coordinates=shipment_data["pickup_coordinates"],
                delivery_coordinates=shipment_data["delivery_coordinates"],
                customer_name=shipment_data["customer_name"],
                weight_kg=shipment_data["weight_kg"],
                commodity_type=shipment_data["commodity_type"],
                transport_mode=shipment_data["transport_mode"],
                equipment_type=shipment_data["equipment_type"],
                packing_type=shipment_data["packing_type"],
                notes=shipment_data["notes"],
                status=status,
                created_at=created_time
            )

            # 为已分配的运单设置时间
            if status != ShipmentStatus.UNASSIGNED:
                shipment.pickup_time = created_time + timedelta(hours=random.randint(2, 8))

            if status in [ShipmentStatus.LOADED, ShipmentStatus.DELIVERED]:
                shipment.delivery_time = created_time + timedelta(
                    days=random.randint(1, 3),
                    hours=random.randint(8, 16)
                )

            session.add(shipment)
            created_shipments.append(shipment)

        await session.commit()
        print(f"    创建了 {shipment_count} 个运单")

    print(f"✅ 成功创建 {len(created_shipments)} 个运单")
    return created_shipments


async def create_gps_data(session: AsyncSession, shipments: list, vehicles: list):
    """创建GPS追踪数据"""
    print("\n创建GPS追踪数据...")

    created_gps_count = 0

    # 为运输中和已送达的运单创建GPS轨迹
    active_shipments = [
        s for s in shipments
        if s.status in [ShipmentStatus.IN_TRANSIT, ShipmentStatus.DELIVERED, ShipmentStatus.LOADED]
    ]

    for shipment in active_shipments[:15]:  # 限制为前15个运单
        await set_tenant_context(session, shipment.tenant_id)

        if not shipment.pickup_coordinates or not shipment.delivery_coordinates:
            continue

        # 生成从起点到终点的GPS轨迹
        start_coord = shipment.pickup_coordinates
        end_coord = shipment.delivery_coordinates

        # 生成中间轨迹点（模拟路径）
        points_count = random.randint(10, 20)
        base_time = shipment.pickup_time or shipment.created_at

        for i in range(points_count):
            # 线性插值计算中间坐标
            progress = i / (points_count - 1)
            lat = start_coord[1] + (end_coord[1] - start_coord[1]) * progress
            lng = start_coord[0] + (end_coord[0] - start_coord[0]) * progress

            # 添加一些随机偏移使轨迹更真实
            lat += random.uniform(-0.01, 0.01)
            lng += random.uniform(-0.01, 0.01)

            # 计算时间点
            gps_time = base_time + timedelta(
                hours=progress * random.randint(8, 24),
                minutes=random.randint(0, 59)
            )

            # 生成速度（0-80 km/h）
            if progress < 0.1 or progress > 0.9:
                speed = random.uniform(0, 20)  # 起终点速度较低
            else:
                speed = random.uniform(40, 80)  # 中途速度较高

            gps_location = GPSLocation(
                tenant_id=shipment.tenant_id,
                shipment_id=shipment.id,
                latitude=Decimal(str(round(lat, 6))),
                longitude=Decimal(str(round(lng, 6))),
                altitude=Decimal(str(random.randint(10, 100))),
                accuracy=Decimal(str(random.uniform(5, 15))),
                gps_time=gps_time,
                speed=Decimal(str(round(speed, 1))),
                heading=Decimal(str(random.randint(0, 360))),
                source=GPSSource.G7_API.value,
                device_id=f"device_{shipment.id}",
                is_valid="1",
                is_real_time="1"
            )

            session.add(gps_location)
            created_gps_count += 1

        await session.commit()

    print(f"✅ 成功创建 {created_gps_count} 条GPS记录")
    return created_gps_count


async def print_shipment_summary(tenants: list, shipments: list, gps_count: int):
    """打印运单数据摘要"""
    print("\n" + "="*60)
    print("🚛 运单数据创建完成！")
    print("="*60)

    print(f"\n📊 统计信息:")
    print(f"   • 总运单数量: {len(shipments)}")
    print(f"   • GPS记录数量: {gps_count}")

    # 按租户统计运单
    print(f"\n📦 运单分布:")
    for tenant in tenants:
        tenant_shipments = [s for s in shipments if s.tenant_id == tenant.id]
        print(f"   {tenant.name}: {len(tenant_shipments)} 个运单")

    # 按状态统计运单
    print(f"\n📈 状态分布:")
    status_counts = {}
    for shipment in shipments:
        status = shipment.status.value
        status_counts[status] = status_counts.get(status, 0) + 1

    status_names = {
        "unassigned": "未分配",
        "assigned": "已分配",
        "dispatched": "已发车",
        "in_transit": "运输中",
        "at_pickup": "到达取货点",
        "loaded": "已装货",
        "delivered": "已送达"
    }

    for status, count in status_counts.items():
        status_name = status_names.get(status, status)
        percentage = (count / len(shipments)) * 100
        print(f"   {status_name}: {count} 个 ({percentage:.1f}%)")

    # 城市路线统计
    print(f"\n🗺️  热门路线:")
    route_counts = {}
    for shipment in shipments:
        pickup_city = None
        delivery_city = None

        for city, data in CITIES_DATA.items():
            if any(addr in shipment.pickup_address for addr in data["addresses"]):
                pickup_city = city
            if any(addr in shipment.delivery_address for addr in data["addresses"]):
                delivery_city = city

        if pickup_city and delivery_city:
            route = f"{pickup_city} → {delivery_city}"
            route_counts[route] = route_counts.get(route, 0) + 1

    # 显示前5个热门路线
    sorted_routes = sorted(route_counts.items(), key=lambda x: x[1], reverse=True)
    for route, count in sorted_routes[:5]:
        print(f"   {route}: {count} 个运单")

    print(f"\n💡 业务场景:")
    print(f"   • 包含完整的运单生命周期状态")
    print(f"   • 覆盖主要城市间的运输路线")
    print(f"   • 包含真实的GPS轨迹数据")
    print(f"   • 支持多种商品类型和运输方式")
    print(f"   • 可用于前端功能测试和演示")


async def main():
    """主函数"""
    print("🚀 开始创建运单种子数据...")

    try:
        async with get_session() as session:
            # 获取现有租户
            tenants_result = await session.execute(select(Tenant))
            tenants = list(tenants_result.scalars().all())

            if not tenants:
                print("❌ 未找到租户数据，请先运行 seed_data.py 创建基础数据")
                return False

            # 获取现有车辆
            vehicles_result = await session.execute(select(Vehicle))
            vehicles = list(vehicles_result.scalars().all())

            print(f"📋 找到 {len(tenants)} 个租户和 {len(vehicles)} 辆车辆")

            # 创建运单
            shipments = await create_shipments(session, tenants, vehicles)

            # 创建GPS数据
            gps_count = await create_gps_data(session, shipments, vehicles)

            # 打印摘要
            await print_shipment_summary(tenants, shipments, gps_count)

    except Exception as e:
        print(f"❌ 创建运单数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ 运单种子数据创建成功完成！")
    else:
        print("\n❌ 运单种子数据创建失败！")
        sys.exit(1)