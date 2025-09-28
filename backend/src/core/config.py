from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置类"""

    # 数据库配置
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/diandian_logistics"
    database_echo: bool = False

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # Celery配置
    celery_broker_url: str = "amqp://rabbitmq:rabbitmq@localhost:5672//"

    # AI模型配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.moonshot.cn/v1"  # Kimi K2 API 端点
    openai_default_model: str = "kimi-k2-0711-preview"        # Kimi K2 模型

    # 国产AI模型
    qwen_api_key: str = ""
    wenxin_api_key: str = ""
    wenxin_secret_key: str = ""
    zhipu_api_key: str = ""

    # JWT配置
    jwt_secret_key: str = "your-super-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # 外部集成
    g7_api_key: str = ""
    g7_base_url: str = "https://api.g7.com.cn"
    wechat_app_id: str = ""
    wechat_app_secret: str = ""

    # 应用配置
    environment: str = "development"
    port: int = 8000
    debug: bool = True
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8081"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略额外的环境变量


# 全局设置实例
_settings = None


def get_settings() -> Settings:
    """获取全局设置实例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings