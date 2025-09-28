#!/usr/bin/env python3
"""
调试配置加载
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import get_settings

def debug_config():
    """调试配置"""

    print("🔍 调试配置加载...")

    # 检查环境变量
    print(f"环境变量 OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY', 'Not set')}")
    print(f"环境变量 OPENAI_BASE_URL: {os.environ.get('OPENAI_BASE_URL', 'Not set')}")
    print(f"环境变量 OPENAI_DEFAULT_MODEL: {os.environ.get('OPENAI_DEFAULT_MODEL', 'Not set')}")

    # 加载设置
    settings = get_settings()

    print(f"配置 openai_api_key: {settings.openai_api_key}")
    print(f"配置 openai_base_url: {settings.openai_base_url}")
    print(f"配置 openai_default_model: {settings.openai_default_model}")

    # 检查 .env 文件
    env_path = ".env"
    if os.path.exists(env_path):
        print(f"\n📄 读取 .env 文件内容:")
        with open(env_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'OPENAI' in line:
                    print(f"  {line.strip()}")

if __name__ == "__main__":
    debug_config()