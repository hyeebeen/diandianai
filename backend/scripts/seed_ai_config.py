#!/usr/bin/env python3
"""
AI模型配置种子数据脚本
创建AI模型配置、对话历史和智能分析数据
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime, timedelta
import uuid
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_session
from core.security import set_tenant_context
from models.users import Tenant, User
from models.ai_models import AIModelConfig, AIProvider, AIConversation, AIMessage


# AI模型配置数据
AI_MODEL_CONFIGS = [
    {
        "name": "OpenAI GPT-4 生产配置",
        "provider": AIProvider.OPENAI,
        "endpoint": "https://api.openai.com/v1",
        "model": "gpt-4",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        },
        "is_active": True,
        "description": "生产环境使用的GPT-4配置，适合复杂物流业务处理"
    },
    {
        "name": "OpenAI GPT-3.5 经济配置",
        "provider": AIProvider.OPENAI,
        "endpoint": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
        "parameters": {
            "temperature": 0.5,
            "max_tokens": 1500,
            "top_p": 0.8
        },
        "is_active": True,
        "description": "经济实用的GPT-3.5配置，适合常规查询和简单任务"
    },
    {
        "name": "通义千问大模型",
        "provider": AIProvider.QWEN,
        "endpoint": "https://dashscope.aliyuncs.com/api/v1",
        "model": "qwen-turbo",
        "parameters": {
            "temperature": 0.6,
            "max_tokens": 1800,
            "top_p": 0.85,
            "repetition_penalty": 1.1
        },
        "is_active": True,
        "description": "阿里云通义千问模型，支持中文物流业务场景"
    },
    {
        "name": "百度文心一言",
        "provider": AIProvider.BAIDU,
        "endpoint": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1",
        "model": "ernie-bot-turbo",
        "parameters": {
            "temperature": 0.8,
            "top_p": 0.7,
            "penalty_score": 1.0
        },
        "is_active": False,
        "description": "百度文心一言模型，备用AI服务配置"
    },
    {
        "name": "智谱GLM模型",
        "provider": AIProvider.ZHIPU,
        "endpoint": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9
        },
        "is_active": False,
        "description": "智谱AI GLM-4模型，支持代码生成和复杂推理"
    }
]

# 示例对话数据
CONVERSATION_TEMPLATES = [
    {
        "title": "运单创建咨询",
        "messages": [
            {"role": "user", "content": "我需要创建一个从北京到上海的运单，货物是电子产品，重量大约500公斤"},
            {"role": "assistant", "content": "好的，我来帮您创建运单。请提供以下信息：\n1. 具体的取货地址和送货地址\n2. 客户名称\n3. 联系电话\n4. 是否需要特殊包装要求"},
            {"role": "user", "content": "取货地址：北京市朝阳区CBD商务区，送货地址：上海市浦东新区陆家嘴金融区，客户是华为技术有限公司，联系电话13800138000"},
            {"role": "assistant", "content": "信息已记录，正在为您创建运单...\n\n运单信息：\n- 运单号：DD20240927001\n- 客户：华为技术有限公司\n- 路线：北京CBD → 上海陆家嘴\n- 货物：电子产品 500kg\n- 预计运费：2800元\n- 预计送达：2天内\n\n是否确认创建？"}
        ]
    },
    {
        "title": "货物追踪查询",
        "messages": [
            {"role": "user", "content": "帮我查询运单号DD20240925003的物流状态"},
            {"role": "assistant", "content": "正在查询运单DD20240925003的状态...\n\n📦 运单信息：\n- 运单号：DD20240925003\n- 当前状态：运输中\n- 当前位置：江苏省苏州市\n- 车辆：苏A12345\n- 司机：张师傅 (13900139000)\n- 预计到达：今天下午3点\n\n实时位置已更新，货物运输正常。"},
            {"role": "user", "content": "预计什么时候能到达目的地？"},
            {"role": "assistant", "content": "根据当前位置和路况分析：\n\n🚛 预计到达时间：今天下午15:30\n📍 剩余距离：约85公里\n⏱️ 预计用时：2小时30分钟\n\n如有延误会及时通知您。需要我帮您联系司机确认吗？"}
        ]
    },
    {
        "title": "运费计算咨询",
        "messages": [
            {"role": "user", "content": "从深圳到北京运输1000公斤的机械设备需要多少运费？"},
            {"role": "assistant", "content": "我来为您计算深圳到北京的运费：\n\n📊 运费计算：\n- 距离：约2100公里\n- 货物：机械设备 1000kg\n- 运输方式：零担运输\n- 基础运费：6.8元/公斤\n- 长途费用：2400元\n- 特殊货物费：300元\n- 保险费用：150元\n\n💰 总计：约9650元\n⏰ 运输时效：3-4天\n\n这是估算价格，具体报价需要确认详细信息。需要我帮您创建询价单吗？"}
        ]
    },
    {
        "title": "车辆调度优化",
        "messages": [
            {"role": "user", "content": "今天有5个运单需要派车，帮我安排一下车辆"},
            {"role": "assistant", "content": "好的，我来帮您分析车辆调度方案：\n\n🚛 可用车辆：\n- 京A12345 (厢式货车, 载重5吨, 位置：海淀区)\n- 京B23456 (平板货车, 载重8吨, 位置：朝阳区)\n- 京C34567 (冷藏车, 载重6吨, 位置：丰台区)\n\n📋 待派运单：请提供运单详情，我将根据距离、载重、货物类型等因素制定最优调度方案。"},
            {"role": "user", "content": "运单都是同城配送，重量都在2-3吨之间，没有特殊要求"},
            {"role": "assistant", "content": "基于您的需求，我推荐以下调度方案：\n\n📍 最优方案：\n1. 京A12345：分配2个运单 (就近原则)\n2. 京B23456：分配2个运单 (载重充足)\n3. 京C34567：分配1个运单 (备用)\n\n💡 优化建议：\n- 按地理位置就近分配，减少空驶\n- 京B车辆载重大，可考虑拼载\n- 预计完成时间：6-8小时\n\n需要我生成详细的派车单吗？"}
        ]
    }
]


async def create_ai_model_configs(session: AsyncSession, tenants: list):
    """创建AI模型配置"""
    print("创建AI模型配置...")

    created_configs = []

    for config_data in AI_MODEL_CONFIGS:
        # 为每个租户创建配置（或创建全局配置）
        # 这里简化为创建全局配置
        tenant_id = tenants[0].id  # 使用第一个租户作为示例

        await set_tenant_context(session, tenant_id)

        # 检查配置是否已存在
        stmt = select(AIModelConfig).where(
            AIModelConfig.name == config_data["name"],
            AIModelConfig.tenant_id == tenant_id
        )
        result = await session.execute(stmt)
        existing_config = result.scalar_one_or_none()

        if existing_config:
            print(f"   配置 {config_data['name']} 已存在，跳过创建")
            continue

        ai_config = AIModelConfig(
            tenant_id=tenant_id,
            name=config_data["name"],
            provider=config_data["provider"],
            endpoint=config_data["endpoint"],
            api_key="your-api-key-here",  # 实际使用时需要真实的API密钥
            model=config_data["model"],
            parameters=config_data["parameters"],
            is_active=config_data["is_active"],
            description=config_data.get("description", "")
        )

        session.add(ai_config)
        created_configs.append(ai_config)
        print(f"   创建配置: {ai_config.name}")

    await session.commit()
    print(f"✅ 成功创建 {len(created_configs)} 个AI模型配置")
    return created_configs


async def create_ai_conversations(session: AsyncSession, tenants: list, users: list):
    """创建AI对话历史"""
    print("\n创建AI对话历史...")

    created_conversations = []
    created_messages = []

    for tenant in tenants:
        await set_tenant_context(session, tenant.id)

        # 获取该租户的用户
        tenant_users = [u for u in users if u.tenant_id == tenant.id]

        if not tenant_users:
            continue

        print(f"  为租户 {tenant.name} 创建对话:")

        # 为每个用户创建3-5个对话
        for user in tenant_users:
            conversation_count = random.randint(3, 5)

            for i in range(conversation_count):
                # 随机选择对话模板
                template = random.choice(CONVERSATION_TEMPLATES)

                # 创建对话时间（过去7天内）
                created_time = datetime.utcnow() - timedelta(
                    days=random.randint(0, 7),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )

                conversation = AIConversation(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    title=template["title"],
                    is_active=random.choice([True, False]),
                    created_at=created_time,
                    last_activity_at=created_time + timedelta(minutes=random.randint(5, 60)),
                    context_data={
                        "user_role": user.role.value,
                        "department": user.department,
                        "session_type": "web"
                    }
                )

                session.add(conversation)
                await session.flush()  # 获取ID
                created_conversations.append(conversation)

                # 创建消息
                for j, message_data in enumerate(template["messages"]):
                    message_time = created_time + timedelta(minutes=j * 2)

                    message = AIMessage(
                        tenant_id=tenant.id,
                        conversation_id=conversation.id,
                        role=message_data["role"],
                        content=message_data["content"],
                        created_at=message_time,
                        metadata={
                            "message_index": j,
                            "processing_time": random.uniform(0.5, 2.0),
                            "token_count": len(message_data["content"].split()) * 1.3
                        }
                    )

                    session.add(message)
                    created_messages.append(message)

        await session.commit()
        print(f"    创建了 {len([c for c in created_conversations if c.tenant_id == tenant.id])} 个对话")

    print(f"✅ 成功创建 {len(created_conversations)} 个对话和 {len(created_messages)} 条消息")
    return created_conversations, created_messages


async def create_ai_analytics_data(session: AsyncSession, tenants: list):
    """创建AI分析数据"""
    print("\n创建AI分析数据...")

    # 这里可以创建一些AI使用统计数据
    # 例如：每日交互次数、成功率、常见问题等

    analytics_data = {}

    for tenant in tenants:
        # 模拟过去30天的数据
        daily_stats = []
        for i in range(30):
            date = datetime.utcnow().date() - timedelta(days=i)
            stats = {
                "date": date.isoformat(),
                "interactions": random.randint(20, 100),
                "successful_actions": random.randint(15, 80),
                "average_response_time": round(random.uniform(0.8, 2.5), 2),
                "user_satisfaction": round(random.uniform(0.7, 0.95), 2)
            }
            daily_stats.append(stats)

        analytics_data[str(tenant.id)] = {
            "tenant_name": tenant.name,
            "daily_stats": daily_stats,
            "common_queries": [
                {"query": "运单创建", "count": random.randint(50, 200)},
                {"query": "货物追踪", "count": random.randint(40, 180)},
                {"query": "运费查询", "count": random.randint(30, 150)},
                {"query": "车辆调度", "count": random.randint(20, 100)},
                {"query": "异常处理", "count": random.randint(10, 80)}
            ],
            "model_usage": {
                "gpt-4": random.randint(100, 300),
                "gpt-3.5-turbo": random.randint(200, 500),
                "qwen-turbo": random.randint(50, 200)
            }
        }

    print(f"✅ 生成了 {len(analytics_data)} 个租户的分析数据")
    return analytics_data


async def print_ai_summary(tenants: list, configs: list, conversations: list, messages: list, analytics: dict):
    """打印AI数据摘要"""
    print("\n" + "="*60)
    print("🤖 AI数据创建完成！")
    print("="*60)

    print(f"\n📊 统计信息:")
    print(f"   • AI模型配置: {len(configs)} 个")
    print(f"   • 对话历史: {len(conversations)} 个")
    print(f"   • 消息记录: {len(messages)} 条")
    print(f"   • 分析数据: {len(analytics)} 个租户")

    print(f"\n🔧 AI模型配置:")
    for config in configs:
        status = "✅ 激活" if config.is_active else "❌ 停用"
        print(f"   • {config.name} ({config.provider.value}) {status}")
        print(f"     模型: {config.model}")
        print(f"     端点: {config.endpoint}")

    print(f"\n💬 对话分布:")
    for tenant in tenants:
        tenant_conversations = [c for c in conversations if c.tenant_id == tenant.id]
        active_count = len([c for c in tenant_conversations if c.is_active])
        print(f"   {tenant.name}: {len(tenant_conversations)} 个对话 (活跃: {active_count})")

    print(f"\n📈 热门查询类型:")
    all_queries = {}
    for tenant_data in analytics.values():
        for query in tenant_data["common_queries"]:
            query_type = query["query"]
            all_queries[query_type] = all_queries.get(query_type, 0) + query["count"]

    sorted_queries = sorted(all_queries.items(), key=lambda x: x[1], reverse=True)
    for query_type, count in sorted_queries[:5]:
        print(f"   {query_type}: {count} 次")

    print(f"\n🎯 AI模型使用情况:")
    all_usage = {}
    for tenant_data in analytics.values():
        for model, usage in tenant_data["model_usage"].items():
            all_usage[model] = all_usage.get(model, 0) + usage

    total_usage = sum(all_usage.values())
    for model, usage in all_usage.items():
        percentage = (usage / total_usage) * 100 if total_usage > 0 else 0
        print(f"   {model}: {usage} 次 ({percentage:.1f}%)")

    print(f"\n💡 功能特点:")
    print(f"   • 支持多AI模型配置和切换")
    print(f"   • 完整的对话历史记录")
    print(f"   • 智能业务场景对话")
    print(f"   • 详细的使用分析数据")
    print(f"   • 支持A/B测试和模型对比")


async def main():
    """主函数"""
    print("🚀 开始创建AI配置种子数据...")

    try:
        async with get_session() as session:
            # 获取现有租户和用户
            tenants_result = await session.execute(select(Tenant))
            tenants = list(tenants_result.scalars().all())

            users_result = await session.execute(select(User))
            users = list(users_result.scalars().all())

            if not tenants:
                print("❌ 未找到租户数据，请先运行 seed_data.py 创建基础数据")
                return False

            print(f"📋 找到 {len(tenants)} 个租户和 {len(users)} 个用户")

            # 创建AI模型配置
            configs = await create_ai_model_configs(session, tenants)

            # 创建对话历史
            conversations, messages = await create_ai_conversations(session, tenants, users)

            # 创建分析数据
            analytics = await create_ai_analytics_data(session, tenants)

            # 打印摘要
            await print_ai_summary(tenants, configs, conversations, messages, analytics)

    except Exception as e:
        print(f"❌ 创建AI配置数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ AI配置种子数据创建成功完成！")
    else:
        print("\n❌ AI配置种子数据创建失败！")
        sys.exit(1)