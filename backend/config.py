#!/usr/bin/env python3
"""
配置管理模块
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """系统配置"""

    # 服务配置
    app_name: str = "GPS实时追踪系统"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # 数据库配置
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/diandian_logistics"
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_max_connections: int = 20
    redis_socket_keepalive: bool = True

    # GPS数据处理配置
    gps_batch_size: int = 100
    gps_flush_interval: float = 5.0  # 秒
    gps_expire_time: int = 3600  # Redis过期时间(秒)
    gps_track_history_points: int = 100  # 保留的历史轨迹点数

    # WebSocket配置
    websocket_heartbeat_interval: int = 30  # 心跳间隔(秒)
    max_websocket_connections: int = 1000

    # 性能优化配置
    object_pool_size: int = 1000
    memory_warning_threshold: float = 80.0  # 内存使用警告阈值(%)
    cpu_warning_threshold: float = 80.0     # CPU使用警告阈值(%)

    # 监控配置
    metrics_enabled: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"

    # 安全配置
    allowed_origins: list = ["*"]  # 生产环境应该设置具体的域名
    api_key_header: str = "X-API-Key"
    api_keys: list = []  # 如果需要API密钥验证

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# 全局设置实例
settings = Settings()

# Redis配置优化
REDIS_CONFIG = {
    'host': settings.redis_host,
    'port': settings.redis_port,
    'db': settings.redis_db,
    'password': settings.redis_password,
    'decode_responses': False,
    'max_connections': settings.redis_max_connections,
    'socket_keepalive': settings.redis_socket_keepalive,
    'socket_keepalive_options': {},
    'retry_on_timeout': True,
    'health_check_interval': 30,
}

# 数据库连接配置
DATABASE_CONFIG = {
    'url': settings.database_url,
    'pool_size': settings.db_pool_size,
    'max_overflow': settings.db_max_overflow,
    'pool_timeout': settings.db_pool_timeout,
    'pool_pre_ping': True,
    'echo': settings.debug,
}

# 日志配置
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': settings.log_level,
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'detailed',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/gps_system.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': settings.log_level,
            'propagate': False
        }
    }
}