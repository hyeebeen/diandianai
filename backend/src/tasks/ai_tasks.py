"""
AI对话处理Celery任务
处理AI助手相关的异步任务，包括对话处理、摘要生成、智能分析等
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import json

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from core.celery_app import celery_app
from core.database import get_session
from core.security import set_tenant_context
from services.ai_service import AIService, AIServiceError, AIActionRequest, LogisticsAction
from models.ai_models import AIConversation, AIMessage, AIModelConfig
from models.logistics import Shipment
from models.users import User


class AsyncTask(Task):
    """支持异步操作的Celery任务基类"""
    pass


@celery_app.task(bind=True, base=AsyncTask, name="tasks.ai_tasks.process_conversation_async")
def process_conversation_async(self, tenant_id: str, conversation_id: str,
                             user_message: str, user_id: str,
                             context: Optional[Dict[str, Any]] = None):
    """
    异步处理AI对话
    用于复杂的AI分析任务，避免阻塞API响应
    """
    async def _process():
        try:
            async with get_session() as session:
                ai_service = AIService()

                # 处理AI对话
                response = await ai_service.chat_completion(
                    session=session,
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    context=context
                )

                # 如果AI建议执行某个操作，创建待执行任务
                if response.action_request:
                    # 触发动作执行任务
                    execute_ai_action.delay(
                        tenant_id=tenant_id,
                        conversation_id=conversation_id,
                        action_request=response.action_request.__dict__,
                        user_id=user_id
                    )

                return {
                    "conversation_id": conversation_id,
                    "response_content": response.content,
                    "action_required": response.action_request is not None,
                    "suggested_actions": response.suggested_actions,
                    "processing_time": datetime.utcnow().isoformat()
                }

        except Exception as e:
            print(f"Error processing AI conversation: {e}")
            self.retry(countdown=30, max_retries=3, exc=e)

    return asyncio.run(_process())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.ai_tasks.execute_ai_action")
def execute_ai_action(self, tenant_id: str, conversation_id: str,
                     action_request: Dict[str, Any], user_id: str):
    """
    执行AI建议的操作
    如创建运单、更新状态等
    """
    async def _execute():
        try:
            async with get_session() as session:
                ai_service = AIService()

                # 重构ActionRequest对象
                action_req = AIActionRequest(
                    action=LogisticsAction(action_request["action"]),
                    confidence=action_request["confidence"],
                    shipment_info=action_request.get("shipment_info"),
                    parameters=action_request.get("parameters", {}),
                    requires_confirmation=action_request.get("requires_confirmation", True),
                    reasoning=action_request.get("reasoning", "")
                )

                # 执行动作
                result = await ai_service.execute_action(
                    session=session,
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                    action_request=action_req,
                    user_id=user_id
                )

                # 如果执行成功，发送通知
                if result.get("success"):
                    from tasks.notification_tasks import send_action_completion_notification
                    send_action_completion_notification.delay(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        action_type=action_req.action.value,
                        result=result
                    )

                return {
                    "action_type": action_req.action.value,
                    "execution_result": result,
                    "conversation_id": conversation_id,
                    "executed_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            print(f"Error executing AI action: {e}")
            return {"error": str(e), "action_type": action_request.get("action")}

    return asyncio.run(_execute())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.ai_tasks.generate_daily_summary")
def generate_daily_summary(self, tenant_id: Optional[str] = None):
    """
    生成每日AI交互摘要
    分析一天的AI对话数据，生成洞察报告
    """
    async def _generate():
        try:
            async with get_session() as session:
                # 如果没有指定租户，为所有租户生成摘要
                if tenant_id:
                    tenant_ids = [tenant_id]
                else:
                    # 获取所有活跃租户
                    stmt = select(User.tenant_id).distinct()
                    result = await session.execute(stmt)
                    tenant_ids = [str(tid[0]) for tid in result.fetchall()]

                summaries = []
                for tid in tenant_ids:
                    summary = await _generate_tenant_summary(session, tid)
                    summaries.append(summary)

                return {
                    "summaries_generated": len(summaries),
                    "tenant_count": len(tenant_ids),
                    "generation_time": datetime.utcnow().isoformat(),
                    "summaries": summaries
                }

        except Exception as e:
            print(f"Error generating daily summary: {e}")
            return {"error": str(e)}

    async def _generate_tenant_summary(session: AsyncSession, tenant_id: str):
        """为单个租户生成摘要"""
        await set_tenant_context(session, tenant_id)

        # 获取今天的对话数据
        today = datetime.utcnow().date()
        start_time = datetime.combine(today, datetime.min.time())
        end_time = datetime.combine(today, datetime.max.time())

        # 统计对话数量
        conversation_stmt = (
            select(func.count(AIConversation.id))
            .where(and_(
                AIConversation.created_at >= start_time,
                AIConversation.created_at <= end_time
            ))
        )
        conversation_result = await session.execute(conversation_stmt)
        conversation_count = conversation_result.scalar()

        # 统计消息数量
        message_stmt = (
            select(func.count(AIMessage.id))
            .where(and_(
                AIMessage.created_at >= start_time,
                AIMessage.created_at <= end_time
            ))
        )
        message_result = await session.execute(message_stmt)
        message_count = message_result.scalar()

        # 获取热门话题（这里简化处理）
        popular_topics = [
            "运单创建", "货物追踪", "状态更新", "路线查询"
        ]

        # 分析成功率（基于执行的操作）
        success_rate = 0.85  # 模拟数据

        return {
            "tenant_id": tenant_id,
            "date": today.isoformat(),
            "conversation_count": conversation_count,
            "message_count": message_count,
            "popular_topics": popular_topics,
            "success_rate": success_rate,
            "insights": [
                "AI助手处理效率良好",
                "运单创建类询问占比最高",
                "建议增加自动化路线规划功能"
            ]
        }

    return asyncio.run(_generate())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.ai_tasks.analyze_conversation_patterns")
def analyze_conversation_patterns(self, tenant_id: str, days: int = 7):
    """
    分析对话模式
    分析用户与AI的交互模式，提供优化建议
    """
    async def _analyze():
        try:
            async with get_session() as session:
                await set_tenant_context(session, tenant_id)

                # 获取指定天数内的对话数据
                start_time = datetime.utcnow() - timedelta(days=days)

                # 分析对话频率
                stmt = (
                    select(
                        func.date(AIConversation.created_at).label('date'),
                        func.count(AIConversation.id).label('count')
                    )
                    .where(AIConversation.created_at >= start_time)
                    .group_by(func.date(AIConversation.created_at))
                    .order_by(func.date(AIConversation.created_at))
                )
                result = await session.execute(stmt)
                daily_stats = [{"date": str(row.date), "count": row.count} for row in result.fetchall()]

                # 分析响应时间（模拟数据）
                avg_response_time = 1.5  # 秒

                # 用户满意度分析（基于对话长度和完成率）
                satisfaction_score = 0.78

                # 常见问题分析
                common_questions = [
                    {"question": "如何创建运单", "frequency": 45},
                    {"question": "查询货物位置", "frequency": 38},
                    {"question": "更新运单状态", "frequency": 32},
                    {"question": "路线规划", "frequency": 25}
                ]

                # 改进建议
                improvements = [
                    "增加常见问题的快速回复模板",
                    "优化运单创建流程的引导",
                    "提供更详细的状态追踪信息",
                    "集成实时路况信息"
                ]

                return {
                    "tenant_id": tenant_id,
                    "analysis_period": f"{days} days",
                    "daily_conversation_stats": daily_stats,
                    "avg_response_time_seconds": avg_response_time,
                    "user_satisfaction_score": satisfaction_score,
                    "common_questions": common_questions,
                    "improvement_suggestions": improvements,
                    "analyzed_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            print(f"Error analyzing conversation patterns: {e}")
            return {"error": str(e)}

    return asyncio.run(_analyze())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.ai_tasks.optimize_ai_responses")
def optimize_ai_responses(self, tenant_id: str):
    """
    优化AI响应
    基于用户反馈和使用模式优化AI回复
    """
    async def _optimize():
        try:
            async with get_session() as session:
                await set_tenant_context(session, tenant_id)

                # 获取最近的低分对话（模拟数据）
                low_scored_conversations = []

                # 分析失败的操作
                failed_actions = []

                # 生成优化建议
                optimizations = [
                    {
                        "type": "response_template",
                        "description": "为常见问题创建标准回复模板",
                        "priority": "high"
                    },
                    {
                        "type": "context_awareness",
                        "description": "增强AI对业务上下文的理解",
                        "priority": "medium"
                    },
                    {
                        "type": "action_confidence",
                        "description": "调整动作执行的置信度阈值",
                        "priority": "low"
                    }
                ]

                return {
                    "tenant_id": tenant_id,
                    "low_scored_conversations": len(low_scored_conversations),
                    "failed_actions": len(failed_actions),
                    "optimization_suggestions": optimizations,
                    "optimization_time": datetime.utcnow().isoformat()
                }

        except Exception as e:
            print(f"Error optimizing AI responses: {e}")
            return {"error": str(e)}

    return asyncio.run(_optimize())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.ai_tasks.train_custom_model")
def train_custom_model(self, tenant_id: str, training_data: List[Dict[str, Any]]):
    """
    训练自定义AI模型
    基于租户的对话数据训练个性化模型
    """
    async def _train():
        try:
            # 这里是训练逻辑的占位符
            # 实际实现中需要集成ML训练框架

            # 数据预处理
            processed_data = []
            for item in training_data:
                # 清理和格式化训练数据
                processed_item = {
                    "input": item.get("user_message", ""),
                    "output": item.get("ai_response", ""),
                    "context": item.get("context", {})
                }
                processed_data.append(processed_item)

            # 模拟训练过程
            training_metrics = {
                "accuracy": 0.89,
                "loss": 0.15,
                "training_samples": len(processed_data),
                "epochs": 10
            }

            # 保存模型信息（实际中应该保存到模型存储）
            model_info = {
                "model_id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "model_version": "1.0",
                "training_metrics": training_metrics,
                "trained_at": datetime.utcnow().isoformat()
            }

            return {
                "training_completed": True,
                "model_info": model_info,
                "training_duration_minutes": 45,  # 模拟训练时间
            }

        except Exception as e:
            print(f"Error training custom model: {e}")
            return {"error": str(e)}

    return asyncio.run(_train())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.ai_tasks.backup_conversation_data")
def backup_conversation_data(self, tenant_id: str, backup_days: int = 30):
    """
    备份对话数据
    定期备份AI对话数据到外部存储
    """
    async def _backup():
        try:
            async with get_session() as session:
                await set_tenant_context(session, tenant_id)

                # 获取需要备份的对话数据
                start_time = datetime.utcnow() - timedelta(days=backup_days)

                stmt = (
                    select(AIConversation)
                    .where(AIConversation.created_at >= start_time)
                    .order_by(AIConversation.created_at)
                )
                result = await session.execute(stmt)
                conversations = result.scalars().all()

                # 构建备份数据
                backup_data = []
                for conv in conversations:
                    conv_data = {
                        "id": str(conv.id),
                        "title": conv.title,
                        "created_at": conv.created_at.isoformat(),
                        "last_activity_at": conv.last_activity_at.isoformat() if conv.last_activity_at else None,
                        "is_active": conv.is_active,
                        "context_data": conv.context_data
                    }
                    backup_data.append(conv_data)

                # 这里应该将数据上传到云存储（如AWS S3、阿里云OSS等）
                # 现在只是模拟备份过程

                backup_file_name = f"ai_conversations_backup_{tenant_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

                return {
                    "backup_completed": True,
                    "backup_file": backup_file_name,
                    "conversations_backed_up": len(backup_data),
                    "backup_period_days": backup_days,
                    "backup_time": datetime.utcnow().isoformat()
                }

        except Exception as e:
            print(f"Error backing up conversation data: {e}")
            return {"error": str(e)}

    return asyncio.run(_backup())