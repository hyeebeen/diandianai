#!/usr/bin/env python3
"""
租户和用户种子数据脚本
创建测试租户、用户和基础数据
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_session, get_engine
from core.security import get_password_hash
from models.users import User, Tenant, UserRole
from models.logistics import Vehicle


async def create_tenants(session: AsyncSession):
    """创建测试租户"""
    print("创建租户数据...")

    tenants_data = [
        {
            "name": "顺丰物流科技",
            "domain": "sf-logistics.com",
            "industry": "logistics",
            "region": "华南",
            "contact_email": "admin@sf-logistics.com",
            "contact_phone": "400-111-1111",
            "address": "深圳市福田区梅林路顺丰大厦"
        },
        {
            "name": "中通快递",
            "domain": "zto-express.com",
            "industry": "express",
            "region": "华东",
            "contact_email": "admin@zto-express.com",
            "contact_phone": "400-222-2222",
            "address": "上海市青浦区华新镇中通快递总部"
        },
        {
            "name": "德邦物流",
            "domain": "deppon.com",
            "industry": "freight",
            "region": "华北",
            "contact_email": "admin@deppon.com",
            "contact_phone": "400-333-3333",
            "address": "北京市朝阳区德邦物流园"
        }
    ]

    created_tenants = []
    for tenant_data in tenants_data:
        # 检查租户是否已存在
        stmt = select(Tenant).where(Tenant.domain == tenant_data["domain"])
        result = await session.execute(stmt)
        existing_tenant = result.scalar_one_or_none()

        if existing_tenant:
            print(f"   租户 {tenant_data['name']} 已存在，跳过创建")
            created_tenants.append(existing_tenant)
            continue

        tenant = Tenant(
            name=tenant_data["name"],
            domain=tenant_data["domain"],
            industry=tenant_data["industry"],
            region=tenant_data["region"],
            contact_email=tenant_data["contact_email"],
            contact_phone=tenant_data["contact_phone"],
            address=tenant_data["address"],
            is_active="1"
        )

        session.add(tenant)
        await session.flush()  # 获取ID但不提交
        created_tenants.append(tenant)
        print(f"   创建租户: {tenant.name} (ID: {tenant.id})")

    await session.commit()
    print(f"✅ 成功创建 {len(created_tenants)} 个租户")
    return created_tenants


async def create_users(session: AsyncSession, tenants: list):
    """创建测试用户"""
    print("\n创建用户数据...")

    # 为每个租户创建管理员和普通用户
    created_users = []

    for tenant in tenants:
        # 管理员用户
        admin_data = {
            "username": f"admin_{tenant.domain.split('.')[0]}",
            "email": f"admin@{tenant.domain}",
            "full_name": f"{tenant.name}管理员",
            "role": UserRole.ADMIN,
            "phone": f"138{str(tenant.id)[-8:]}",
            "department": "管理部",
            "is_active": "1"
        }

        # 检查用户是否已存在
        stmt = select(User).where(
            User.username == admin_data["username"],
            User.tenant_id == tenant.id
        )
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            admin_user = User(
                tenant_id=tenant.id,
                username=admin_data["username"],
                email=admin_data["email"],
                full_name=admin_data["full_name"],
                hashed_password=get_password_hash("admin123"),
                role=admin_data["role"],
                phone=admin_data["phone"],
                department=admin_data["department"],
                is_active=admin_data["is_active"]
            )

            session.add(admin_user)
            created_users.append(admin_user)
            print(f"   创建管理员: {admin_user.username} @ {tenant.name}")

        # 调度员用户
        dispatcher_data = {
            "username": f"dispatcher_{tenant.domain.split('.')[0]}",
            "email": f"dispatcher@{tenant.domain}",
            "full_name": f"{tenant.name}调度员",
            "role": UserRole.DISPATCHER,
            "phone": f"139{str(tenant.id)[-8:]}",
            "department": "调度部",
            "is_active": "1"
        }

        stmt = select(User).where(
            User.username == dispatcher_data["username"],
            User.tenant_id == tenant.id
        )
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            dispatcher_user = User(
                tenant_id=tenant.id,
                username=dispatcher_data["username"],
                email=dispatcher_data["email"],
                full_name=dispatcher_data["full_name"],
                hashed_password=get_password_hash("dispatcher123"),
                role=dispatcher_data["role"],
                phone=dispatcher_data["phone"],
                department=dispatcher_data["department"],
                is_active=dispatcher_data["is_active"]
            )

            session.add(dispatcher_user)
            created_users.append(dispatcher_user)
            print(f"   创建调度员: {dispatcher_user.username} @ {tenant.name}")

        # 司机用户
        driver_data = {
            "username": f"driver_{tenant.domain.split('.')[0]}",
            "email": f"driver@{tenant.domain}",
            "full_name": f"{tenant.name}司机",
            "role": UserRole.DRIVER,
            "phone": f"137{str(tenant.id)[-8:]}",
            "department": "运输部",
            "is_active": "1"
        }

        stmt = select(User).where(
            User.username == driver_data["username"],
            User.tenant_id == tenant.id
        )
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            driver_user = User(
                tenant_id=tenant.id,
                username=driver_data["username"],
                email=driver_data["email"],
                full_name=driver_data["full_name"],
                hashed_password=get_password_hash("driver123"),
                role=driver_data["role"],
                phone=driver_data["phone"],
                department=driver_data["department"],
                is_active=driver_data["is_active"]
            )

            session.add(driver_user)
            created_users.append(driver_user)
            print(f"   创建司机: {driver_user.username} @ {tenant.name}")

    await session.commit()
    print(f"✅ 成功创建 {len(created_users)} 个用户")
    return created_users


async def create_vehicles(session: AsyncSession, tenants: list):
    """创建测试车辆"""
    print("\n创建车辆数据...")

    created_vehicles = []
    vehicle_plates = [
        "京A12345", "京B23456", "京C34567",
        "沪A12345", "沪B23456", "沪C34567",
        "粤A12345", "粤B23456", "粤C34567"
    ]

    vehicle_types = ["厢式货车", "平板货车", "冷藏车"]

    for i, tenant in enumerate(tenants):
        for j in range(3):  # 每个租户3辆车
            plate_index = i * 3 + j
            if plate_index >= len(vehicle_plates):
                break

            vehicle_data = {
                "license_plate": vehicle_plates[plate_index],
                "vehicle_type": vehicle_types[j % len(vehicle_types)],
                "capacity_kg": [5000, 8000, 10000][j],
                "driver_name": f"司机{plate_index + 1}",
                "driver_phone": f"1380000{plate_index:04d}",
                "status": "available",
                "is_active": "1"
            }

            # 检查车辆是否已存在
            stmt = select(Vehicle).where(
                Vehicle.license_plate == vehicle_data["license_plate"],
                Vehicle.tenant_id == tenant.id
            )
            result = await session.execute(stmt)
            existing_vehicle = result.scalar_one_or_none()

            if existing_vehicle:
                print(f"   车辆 {vehicle_data['license_plate']} 已存在，跳过创建")
                continue

            vehicle = Vehicle(
                tenant_id=tenant.id,
                license_plate=vehicle_data["license_plate"],
                vehicle_type=vehicle_data["vehicle_type"],
                capacity_kg=vehicle_data["capacity_kg"],
                driver_name=vehicle_data["driver_name"],
                driver_phone=vehicle_data["driver_phone"],
                status=vehicle_data["status"],
                is_active=vehicle_data["is_active"]
            )

            session.add(vehicle)
            created_vehicles.append(vehicle)
            print(f"   创建车辆: {vehicle.license_plate} @ {tenant.name}")

    await session.commit()
    print(f"✅ 成功创建 {len(created_vehicles)} 辆车辆")
    return created_vehicles


async def print_summary(tenants: list, users: list, vehicles: list):
    """打印创建结果摘要"""
    print("\n" + "="*60)
    print("🎉 种子数据创建完成！")
    print("="*60)

    print(f"\n📊 统计信息:")
    print(f"   • 租户数量: {len(tenants)}")
    print(f"   • 用户数量: {len(users)}")
    print(f"   • 车辆数量: {len(vehicles)}")

    print(f"\n🏢 租户信息:")
    for tenant in tenants:
        print(f"   • {tenant.name} ({tenant.domain})")
        print(f"     ID: {tenant.id}")
        print(f"     行业: {tenant.industry} | 地区: {tenant.region}")
        print(f"     联系: {tenant.contact_email}")

    print(f"\n👥 用户信息 (用户名 / 密码):")
    for tenant in tenants:
        domain_prefix = tenant.domain.split('.')[0]
        print(f"   {tenant.name}:")
        print(f"     • admin_{domain_prefix} / admin123 (管理员)")
        print(f"     • dispatcher_{domain_prefix} / dispatcher123 (调度员)")
        print(f"     • driver_{domain_prefix} / driver123 (司机)")

    print(f"\n🚛 车辆信息:")
    vehicle_count_by_tenant = {}
    for vehicle in vehicles:
        tenant_name = next(t.name for t in tenants if t.id == vehicle.tenant_id)
        if tenant_name not in vehicle_count_by_tenant:
            vehicle_count_by_tenant[tenant_name] = []
        vehicle_count_by_tenant[tenant_name].append(vehicle.license_plate)

    for tenant_name, plates in vehicle_count_by_tenant.items():
        print(f"   {tenant_name}: {', '.join(plates)}")

    print(f"\n💡 使用提示:")
    print(f"   1. 使用以上用户名和密码登录系统")
    print(f"   2. 每个租户的数据完全隔离")
    print(f"   3. 管理员可以访问所有功能")
    print(f"   4. 调度员可以管理运单和车辆")
    print(f"   5. 司机可以查看和更新运单状态")


async def main():
    """主函数"""
    print("🚀 开始创建种子数据...")
    print("⚠️  注意: 此脚本会创建测试数据，请确保在测试环境中运行")

    try:
        async with get_session() as session:
            # 创建租户
            tenants = await create_tenants(session)

            # 创建用户
            users = await create_users(session, tenants)

            # 创建车辆
            vehicles = await create_vehicles(session, tenants)

            # 打印摘要
            await print_summary(tenants, users, vehicles)

    except Exception as e:
        print(f"❌ 创建种子数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ 种子数据创建成功完成！")
    else:
        print("\n❌ 种子数据创建失败！")
        sys.exit(1)