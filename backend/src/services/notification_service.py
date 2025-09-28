"""
多渠道通知服务实现
支持微信、短信、电话等多种通知方式，包含重试机制和升级策略
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import logging
from pydantic import BaseModel

from ..core.config import get_settings
from ..integrations.wechat_api import WeChatService
from ..integrations.sms_api import SMSService

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationChannel(str, Enum):
    """通知渠道枚举"""
    WECHAT = "wechat"
    SMS = "sms"
    PHONE = "phone"
    EMAIL = "email"


class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """通知状态"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"


class NotificationRequest(BaseModel):
    """通知请求模型"""
    recipient_id: str
    channels: List[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    content: str
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    retry_count: int = 3
    expire_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationResult(BaseModel):
    """通知结果模型"""
    notification_id: str
    channel: NotificationChannel
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class NotificationService:
    """多渠道通知服务"""

    def __init__(self):
        self.wechat_service = WeChatService()
        self.sms_service = SMSService()

        # 通知渠道优先级 (基于Diandian项目经验)
        self.channel_priority = {
            NotificationPriority.URGENT: [
                NotificationChannel.WECHAT,
                NotificationChannel.PHONE,
                NotificationChannel.SMS
            ],
            NotificationPriority.HIGH: [
                NotificationChannel.WECHAT,
                NotificationChannel.SMS,
                NotificationChannel.PHONE
            ],
            NotificationPriority.NORMAL: [
                NotificationChannel.WECHAT,
                NotificationChannel.SMS
            ],
            NotificationPriority.LOW: [
                NotificationChannel.WECHAT
            ]
        }

        # 重试间隔配置 (秒)
        self.retry_intervals = {
            NotificationChannel.WECHAT: [30, 300, 1800],  # 30秒, 5分钟, 30分钟
            NotificationChannel.SMS: [60, 600, 3600],     # 1分钟, 10分钟, 1小时
            NotificationChannel.PHONE: [300, 1800, 7200], # 5分钟, 30分钟, 2小时
            NotificationChannel.EMAIL: [300, 1800, 7200]  # 5分钟, 30分钟, 2小时
        }

    async def send_notification(self, request: NotificationRequest) -> List[NotificationResult]:
        """
        发送多渠道通知

        Args:
            request: 通知请求

        Returns:
            List[NotificationResult]: 各渠道发送结果
        """
        try:
            # 根据优先级确定发送渠道
            channels_to_send = self._determine_channels(request.channels, request.priority)

            # 并行发送到各个渠道
            tasks = []
            for channel in channels_to_send:
                task = asyncio.create_task(
                    self._send_to_channel(request, channel)
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理异常结果
            notification_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to send notification via {channels_to_send[i]}: {result}")
                    notification_results.append(NotificationResult(
                        notification_id=f"{request.recipient_id}_{channels_to_send[i]}_{datetime.now().timestamp()}",
                        channel=channels_to_send[i],
                        status=NotificationStatus.FAILED,
                        error_message=str(result)
                    ))
                else:
                    notification_results.append(result)

            return notification_results

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise

    async def _send_to_channel(
        self,
        request: NotificationRequest,
        channel: NotificationChannel
    ) -> NotificationResult:
        """
        发送通知到指定渠道

        Args:
            request: 通知请求
            channel: 目标渠道

        Returns:
            NotificationResult: 发送结果
        """
        notification_id = f"{request.recipient_id}_{channel}_{datetime.now().timestamp()}"

        try:
            # 检查是否已过期
            if request.expire_at and datetime.now() > request.expire_at:
                return NotificationResult(
                    notification_id=notification_id,
                    channel=channel,
                    status=NotificationStatus.EXPIRED
                )

            # 根据渠道发送
            if channel == NotificationChannel.WECHAT:
                success = await self._send_wechat(request)
            elif channel == NotificationChannel.SMS:
                success = await self._send_sms(request)
            elif channel == NotificationChannel.PHONE:
                success = await self._send_phone(request)
            elif channel == NotificationChannel.EMAIL:
                success = await self._send_email(request)
            else:
                raise ValueError(f"Unsupported notification channel: {channel}")

            status = NotificationStatus.SENT if success else NotificationStatus.FAILED

            return NotificationResult(
                notification_id=notification_id,
                channel=channel,
                status=status,
                sent_at=datetime.now() if success else None
            )

        except Exception as e:
            logger.error(f"Failed to send notification via {channel}: {e}")
            return NotificationResult(
                notification_id=notification_id,
                channel=channel,
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )

    async def _send_wechat(self, request: NotificationRequest) -> bool:
        """发送微信通知"""
        try:
            # 使用模板消息或普通消息
            if request.template_id and request.template_data:
                result = await self.wechat_service.send_template_message(
                    user_id=request.recipient_id,
                    template_id=request.template_id,
                    data=request.template_data
                )
            else:
                result = await self.wechat_service.send_text_message(
                    user_id=request.recipient_id,
                    content=f"{request.title}\n{request.content}"
                )

            return result.get("errcode", 0) == 0

        except Exception as e:
            logger.error(f"WeChat notification failed: {e}")
            return False

    async def _send_sms(self, request: NotificationRequest) -> bool:
        """发送短信通知"""
        try:
            result = await self.sms_service.send_sms(
                phone_number=request.recipient_id,
                content=f"{request.title}: {request.content}",
                template_id=request.template_id,
                template_params=request.template_data
            )

            return result.get("success", False)

        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
            return False

    async def _send_phone(self, request: NotificationRequest) -> bool:
        """发送电话通知 (语音播报)"""
        try:
            # 这里应该集成语音通话服务
            # 目前返回模拟结果
            logger.info(f"Phone notification to {request.recipient_id}: {request.content}")

            # 模拟异步处理
            await asyncio.sleep(0.1)

            # 实际实现时应该调用电话API
            return True

        except Exception as e:
            logger.error(f"Phone notification failed: {e}")
            return False

    async def _send_email(self, request: NotificationRequest) -> bool:
        """发送邮件通知"""
        try:
            # 这里应该集成邮件服务
            # 目前返回模拟结果
            logger.info(f"Email notification to {request.recipient_id}: {request.title}")

            # 模拟异步处理
            await asyncio.sleep(0.1)

            # 实际实现时应该调用邮件API
            return True

        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False

    def _determine_channels(
        self,
        requested_channels: List[NotificationChannel],
        priority: NotificationPriority
    ) -> List[NotificationChannel]:
        """
        根据优先级确定发送渠道

        Args:
            requested_channels: 请求的渠道列表
            priority: 通知优先级

        Returns:
            List[NotificationChannel]: 实际发送渠道列表
        """
        # 获取该优先级的推荐渠道
        recommended_channels = self.channel_priority.get(priority, [])

        # 取交集，保持推荐渠道的顺序
        final_channels = []
        for channel in recommended_channels:
            if channel in requested_channels:
                final_channels.append(channel)

        # 如果没有交集，使用原始请求的渠道
        if not final_channels:
            final_channels = requested_channels

        return final_channels

    async def send_shipment_notification(
        self,
        user_id: str,
        shipment_id: str,
        status: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> List[NotificationResult]:
        """
        发送运单状态通知

        Args:
            user_id: 用户ID
            shipment_id: 运单ID
            status: 运单状态
            message: 通知消息
            priority: 通知优先级

        Returns:
            List[NotificationResult]: 发送结果
        """
        request = NotificationRequest(
            recipient_id=user_id,
            channels=[NotificationChannel.WECHAT, NotificationChannel.SMS],
            priority=priority,
            title=f"运单状态更新 - {shipment_id}",
            content=message,
            template_id="shipment_status_update",
            template_data={
                "shipment_id": shipment_id,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            },
            metadata={
                "type": "shipment_notification",
                "shipment_id": shipment_id,
                "status": status
            }
        )

        return await self.send_notification(request)

    async def send_urgent_alert(
        self,
        user_id: str,
        alert_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[NotificationResult]:
        """
        发送紧急告警

        Args:
            user_id: 用户ID
            alert_type: 告警类型
            message: 告警消息
            metadata: 额外元数据

        Returns:
            List[NotificationResult]: 发送结果
        """
        request = NotificationRequest(
            recipient_id=user_id,
            channels=[
                NotificationChannel.WECHAT,
                NotificationChannel.PHONE,
                NotificationChannel.SMS
            ],
            priority=NotificationPriority.URGENT,
            title=f"紧急告警 - {alert_type}",
            content=message,
            template_id="urgent_alert",
            template_data={
                "alert_type": alert_type,
                "message": message,
                "timestamp": datetime.now().isoformat()
            },
            retry_count=5,  # 紧急告警增加重试次数
            expire_at=datetime.now() + timedelta(hours=1),  # 1小时后过期
            metadata=metadata or {}
        )

        return await self.send_notification(request)

    async def send_batch_notifications(
        self,
        requests: List[NotificationRequest]
    ) -> List[List[NotificationResult]]:
        """
        批量发送通知

        Args:
            requests: 通知请求列表

        Returns:
            List[List[NotificationResult]]: 批量发送结果
        """
        # 并行处理所有通知请求
        tasks = [
            asyncio.create_task(self.send_notification(request))
            for request in requests
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch notification {i} failed: {result}")
                # 创建失败结果
                failed_result = [NotificationResult(
                    notification_id=f"batch_{i}_failed",
                    channel=NotificationChannel.WECHAT,  # 默认渠道
                    status=NotificationStatus.FAILED,
                    error_message=str(result)
                )]
                final_results.append(failed_result)
            else:
                final_results.append(result)

        return final_results

    async def retry_failed_notification(
        self,
        original_request: NotificationRequest,
        failed_result: NotificationResult
    ) -> NotificationResult:
        """
        重试失败的通知

        Args:
            original_request: 原始通知请求
            failed_result: 失败的通知结果

        Returns:
            NotificationResult: 重试结果
        """
        # 检查重试次数
        if failed_result.retry_count >= original_request.retry_count:
            logger.warning(f"Max retry attempts reached for notification {failed_result.notification_id}")
            return failed_result

        # 计算重试延迟
        channel = failed_result.channel
        retry_intervals = self.retry_intervals.get(channel, [60, 300, 1800])
        retry_index = min(failed_result.retry_count, len(retry_intervals) - 1)
        delay = retry_intervals[retry_index]

        logger.info(f"Retrying notification {failed_result.notification_id} after {delay} seconds")
        await asyncio.sleep(delay)

        # 重试发送
        retry_result = await self._send_to_channel(original_request, channel)
        retry_result.retry_count = failed_result.retry_count + 1

        return retry_result


# 全局通知服务实例
notification_service = NotificationService()