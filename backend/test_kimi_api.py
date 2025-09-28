#!/usr/bin/env python3
"""
测试 Kimi K2 API 连接
验证 OpenAI Provider 能否正确调用 Kimi K2 API
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.integrations.ai_providers.openai_provider import OpenAIProvider, OpenAIModel, ChatMessage, MessageRole


async def test_kimi_api():
    """测试 Kimi K2 API 连接"""

    print("🚀 开始测试 Kimi K2 API 连接...")

    # 初始化 OpenAI Provider
    provider = OpenAIProvider()

    # 检查配置
    print(f"📋 API Key 配置: {'✅' if provider.api_key else '❌'}")
    print(f"📋 Base URL: {provider.base_url}")
    print(f"📋 默认模型: {provider.default_model}")

    if not provider.api_key:
        print("❌ API Key 未配置，无法继续测试")
        return

    # 准备测试消息
    test_messages = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content="你是点点精灵，一个专业、友好的物流AI助手。请用中文简洁地回复用户。"
        ),
        ChatMessage(
            role=MessageRole.USER,
            content="你好，请介绍一下你自己。"
        )
    ]

    try:
        print("\n🧪 测试基础聊天功能...")

        # 调用 chat_completion
        response = await provider.chat_completion(
            messages=test_messages,
            model=OpenAIModel.KIMI_K2_0711_PREVIEW,
            temperature=0.7,
            max_tokens=200
        )

        if response.success:
            print("✅ API 调用成功！")
            print(f"📝 响应内容: {response.content}")
            print(f"⚡ 响应时间: {response.response_time_ms}ms")
            print(f"🤖 使用模型: {response.model}")

            if response.token_usage:
                print(f"🎯 Token 使用:")
                print(f"   - 输入 tokens: {response.token_usage.prompt_tokens}")
                print(f"   - 输出 tokens: {response.token_usage.completion_tokens}")
                print(f"   - 总计 tokens: {response.token_usage.total_tokens}")
                print(f"   - 预估成本: ${response.token_usage.estimated_cost:.6f}")
        else:
            print(f"❌ API 调用失败: {response.error_message}")
            return False

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

    # 测试简单聊天方法
    try:
        print("\n🧪 测试简单聊天方法...")

        simple_response = await provider.simple_chat("你能帮我查询运单状态吗？")

        if simple_response.success:
            print("✅ 简单聊天方法测试成功！")
            print(f"📝 响应内容: {simple_response.content}")
        else:
            print(f"❌ 简单聊天方法测试失败: {simple_response.error_message}")

    except Exception as e:
        print(f"❌ 简单聊天测试过程中发生错误: {str(e)}")

    print("\n🎉 测试完成！")
    return True


if __name__ == "__main__":
    asyncio.run(test_kimi_api())