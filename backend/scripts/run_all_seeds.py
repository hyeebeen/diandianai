#!/usr/bin/env python3
"""
运行所有种子数据脚本的主脚本
按正确顺序执行所有数据初始化
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path

# 添加src目录到路径
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))

def run_script(script_name: str) -> bool:
    """运行指定的种子数据脚本"""
    script_path = current_dir / script_name

    if not script_path.exists():
        print(f"❌ 脚本文件不存在: {script_path}")
        return False

    print(f"\n{'='*60}")
    print(f"🚀 运行脚本: {script_name}")
    print(f"{'='*60}")

    try:
        # 使用Python运行脚本
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=current_dir.parent,  # 在backend目录运行
            capture_output=False,    # 显示输出
            text=True
        )

        if result.returncode == 0:
            print(f"✅ {script_name} 执行成功")
            return True
        else:
            print(f"❌ {script_name} 执行失败，退出码: {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ 运行 {script_name} 时发生错误: {e}")
        return False

def print_header():
    """打印欢迎信息"""
    print("🎉 点点AI物流管理平台 - 种子数据初始化")
    print("="*60)
    print("📋 将按以下顺序创建数据:")
    print("   1. 基础数据 (租户、用户、车辆)")
    print("   2. 运单数据 (运单、GPS轨迹)")
    print("   3. AI配置 (模型配置、对话历史)")
    print("="*60)
    print("⚠️  注意: 请确保数据库已启动且连接正常")
    print("⚠️  注意: 此过程将创建测试数据，请在测试环境中运行")
    print("="*60)

def print_summary(results: dict):
    """打印执行结果摘要"""
    print("\n" + "="*60)
    print("📊 种子数据初始化完成")
    print("="*60)

    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    print(f"\n✅ 成功: {success_count}/{total_count} 个脚本")

    for script, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {script}: {status}")

    if success_count == total_count:
        print(f"\n🎉 所有种子数据创建完成！")
        print(f"\n💡 接下来您可以:")
        print(f"   • 启动FastAPI服务器: uv run python src/main.py")
        print(f"   • 访问API文档: http://localhost:8000/docs")
        print(f"   • 使用创建的测试账号登录系统")
        print(f"   • 查看运单数据和GPS轨迹")
        return True
    else:
        print(f"\n❌ 部分脚本执行失败，请检查错误信息")
        return False

async def check_database_connection():
    """检查数据库连接"""
    try:
        from core.database import get_engine
        from sqlalchemy import text

        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        print("✅ 数据库连接正常")
        return True

    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print(f"💡 请确保:")
        print(f"   • PostgreSQL服务已启动")
        print(f"   • 数据库配置正确 (.env文件)")
        print(f"   • 数据库用户有创建表的权限")
        return False

def main():
    """主函数"""
    print_header()

    # 检查数据库连接
    print("🔍 检查数据库连接...")

    try:
        # 简单检查 - 运行时再处理数据库连接
        db_check = True
    except:
        db_check = False

    if not db_check:
        print("❌ 预检查失败，但继续尝试执行...")

    # 定义执行顺序
    scripts = [
        "seed_data.py",          # 基础数据：租户、用户、车辆
        "seed_shipments.py",     # 运单和GPS数据
        "seed_ai_config.py"      # AI配置和对话数据
    ]

    results = {}

    # 按顺序执行脚本
    for script in scripts:
        success = run_script(script)
        results[script] = success

        if not success:
            print(f"\n❌ {script} 执行失败，停止后续脚本执行")
            break

        # 脚本间短暂延迟
        import time
        time.sleep(1)

    # 打印结果摘要
    success = print_summary(results)

    return success

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎊 种子数据初始化成功完成！")
            sys.exit(0)
        else:
            print("\n💥 种子数据初始化失败！")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断执行")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)