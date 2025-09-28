"""
Celery异步任务应用配置
支持GPS数据处理、AI对话处理、通知发送等后台任务
"""

import os
from celery import Celery
from celery.signals import worker_process_init
from core.config import get_settings

# 获取配置
settings = get_settings()

# 创建Celery应用实例
celery_app = Celery(
    "diandian_logistics",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "tasks.gps_tasks",
        "tasks.ai_tasks",
        "tasks.notification_tasks"
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务路由
    task_routes={
        "tasks.gps_tasks.*": {"queue": "gps"},
        "tasks.ai_tasks.*": {"queue": "ai"},
        "tasks.notification_tasks.*": {"queue": "notifications"},
    },

    # 任务执行配置
    task_always_eager=False,  # 生产环境设为False
    task_eager_propagates=True,
    task_ignore_result=False,
    result_expires=3600,  # 结果保存1小时

    # 工作进程配置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,

    # 任务重试配置
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,

    # 并发控制
    worker_concurrency=4,

    # 任务优先级
    task_inherit_parent_priority=True,
    task_default_priority=5,
    worker_hijack_root_logger=False,

    # 安全配置
    worker_enable_remote_control=False,

    # Beat调度器配置（用于定时任务）
    beat_schedule={
        # GPS数据清理任务 - 每天凌晨2点执行
        'cleanup-old-gps-data': {
            'task': 'tasks.gps_tasks.cleanup_old_gps_data',
            'schedule': 60 * 60 * 24,  # 24小时
            'options': {'queue': 'gps'}
        },

        # 生成AI交互摘要 - 每天早上6点执行
        'generate-daily-ai-summary': {
            'task': 'tasks.ai_tasks.generate_daily_summary',
            'schedule': 60 * 60 * 24,  # 24小时
            'options': {'queue': 'ai'}
        },

        # 发送待办事项提醒 - 每小时执行
        'send-pending-reminders': {
            'task': 'tasks.notification_tasks.send_pending_reminders',
            'schedule': 60 * 60,  # 1小时
            'options': {'queue': 'notifications'}
        },
    },
)

# 错误处理配置
@celery_app.task(bind=True)
def debug_task(self):
    """调试任务"""
    print(f'Request: {self.request!r}')


# 任务失败回调
@celery_app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback):
    """任务失败处理"""
    print(f'Task {task_id} failed: {error}')
    # 这里可以添加失败通知逻辑


# 启动时的钩子函数
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """设置周期性任务"""
    pass


# 工作进程启动钩子
@worker_process_init.connect
def worker_process_init_handler(**kwargs):
    """工作进程初始化"""
    print("Celery worker process initialized")


# 如果直接运行此文件，启动Celery worker
if __name__ == '__main__':
    celery_app.start()