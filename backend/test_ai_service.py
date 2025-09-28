#!/usr/bin/env python3
"""
测试完整的 AI 服务集成
验证 SimpleChatService 能够正确调用 Kimi K2 API 并提供点点精灵服务
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.simple_chat_service import simple_chat_service
from src.services.context_builder import context_builder, ShipmentContext


async def test_ai_service():
    """测试完整的AI服务"""

    print("🚀 开始测试完整的AI服务集成...")

    # 测试1: 基础聊天功能
    print("\n🧪 测试1: 基础聊天功能")
    try:
        response = await simple_chat_service.chat_with_diandian(
            user_message="你好，我是新用户，请介绍一下你的功能",
            conversation_history=None
        )

        if response["success"]:
            print("✅ 基础聊天测试成功！")
            print(f"📝 响应内容: {response['data']['content']}")
            print(f"⚡ 响应时间: {response['data']['response_time_ms']}ms")
            print(f"🤖 使用模型: {response['data']['model']}")
            if response['data']['token_usage']:
                token_usage = response['data']['token_usage']
                print(f"🎯 Token 使用: {token_usage['total_tokens']} tokens")
        else:
            print(f"❌ 基础聊天测试失败: {response['error']}")

    except Exception as e:
        print(f"❌ 基础聊天测试异常: {str(e)}")

    # 测试2: 带运单上下文的聊天
    print("\n🧪 测试2: 带运单上下文的聊天")
    try:
        # 创建模拟运单上下文
        shipment_context = ShipmentContext(
            shipment_id="123",
            shipment_number="DD202309280001",
            status="in_transit",
            customer_info={
                "name": "张三",
                "phone": "13800138000"
            },
            addresses={
                "pickup": "北京市朝阳区建国门外大街1号",
                "delivery": "上海市浦东新区陆家嘴环路1000号"
            },
            cargo_info={
                "description": "电子产品",
                "weight": 2.5
            },
            timeline=[
                {
                    "timestamp": "2024-09-28T10:00:00",
                    "status": "created",
                    "notes": "运单已创建"
                },
                {
                    "timestamp": "2024-09-28T12:00:00",
                    "status": "picked_up",
                    "notes": "货物已取件"
                },
                {
                    "timestamp": "2024-09-28T15:00:00",
                    "status": "in_transit",
                    "notes": "货物运输中"
                }
            ],
            current_location={
                "address": "江苏省南京市中转仓库"
            },
            estimated_delivery="2024-09-29"
        )

        response = await simple_chat_service.chat_with_diandian(
            user_message="请帮我查看这个运单的状态，预计什么时候能到？",
            shipment_context=shipment_context
        )

        if response["success"]:
            print("✅ 运单上下文聊天测试成功！")
            print(f"📝 响应内容: {response['data']['content']}")
            print(f"⚡ 响应时间: {response['data']['response_time_ms']}ms")
        else:
            print(f"❌ 运单上下文聊天测试失败: {response['error']}")

    except Exception as e:
        print(f"❌ 运单上下文聊天测试异常: {str(e)}")

    # 测试3: 多轮对话
    print("\n🧪 测试3: 多轮对话测试")
    try:
        # 第一轮对话
        conversation_history = []

        response1 = await simple_chat_service.chat_with_diandian(
            user_message="我想寄一个包裹",
            conversation_history=conversation_history
        )

        if response1["success"]:
            conversation_history.append({"role": "user", "content": "我想寄一个包裹"})
            conversation_history.append({"role": "assistant", "content": response1["data"]["content"]})

            # 第二轮对话
            response2 = await simple_chat_service.chat_with_diandian(
                user_message="从北京到上海，大概多少钱？",
                conversation_history=conversation_history
            )

            if response2["success"]:
                print("✅ 多轮对话测试成功！")
                print(f"📝 第一轮响应: {response1['data']['content'][:100]}...")
                print(f"📝 第二轮响应: {response2['data']['content'][:100]}...")
            else:
                print(f"❌ 第二轮对话失败: {response2['error']}")
        else:
            print(f"❌ 第一轮对话失败: {response1['error']}")

    except Exception as e:
        print(f"❌ 多轮对话测试异常: {str(e)}")

    # 测试4: 上下文构建器
    print("\n🧪 测试4: 上下文构建器测试")
    try:
        # 测试系统提示词构建
        system_prompt = context_builder.build_system_prompt()
        print(f"✅ 系统提示词构建成功 (长度: {len(system_prompt)} 字符)")

        # 测试带运单上下文的系统提示词
        system_prompt_with_context = context_builder.build_system_prompt(shipment_context)
        print(f"✅ 带运单上下文的系统提示词构建成功 (长度: {len(system_prompt_with_context)} 字符)")

    except Exception as e:
        print(f"❌ 上下文构建器测试异常: {str(e)}")

    print("\n🎉 AI服务集成测试完成！")


if __name__ == "__main__":
    asyncio.run(test_ai_service())