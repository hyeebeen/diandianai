"""
通知发送Celery任务
处理各种通知发送，包括短信、邮件、微信等渠道
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import json

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from core.celery_app import celery_app
from core.database import get_session
from core.security import set_tenant_context
from core.config import get_settings
from models.logistics import Shipment, ShipmentStatus
from models.users import User


class AsyncTask(Task):
    """支持异步操作的Celery任务基类"""
    pass


@celery_app.task(bind=True, base=AsyncTask, name="tasks.notification_tasks.send_sms_notification")
def send_sms_notification(self, phone_number: str, message: str, tenant_id: str,
                         notification_type: str = "general"):
    """
    发送短信通知
    支持运单状态更新、紧急通知等
    """
    async def _send():
        try:
            settings = get_settings()

            # 这里集成实际的短信服务商API
            # 例如：阿里云短信、腾讯云短信、华为云短信等

            # 模拟短信发送
            print(f"Sending SMS to {phone_number}: {message}")

            # 实际实现示例：
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         "https://sms.aliyuncs.com/",
            #         headers={"Authorization": f"Bearer {settings.aliyun_sms_token}"},
            #         json={
            #             "phone": phone_number,
            #             "message": message,
            #             "template_id": "SMS_123456789"
            #         }
            #     )

            # 记录发送日志
            log_entry = {
                "notification_id": str(uuid.uuid4()),
                "type": "sms",
                "recipient": phone_number,
                "message": message,
                "tenant_id": tenant_id,
                "notification_type": notification_type,
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            }

            return {
                "success": True,
                "notification_log": log_entry,
                "provider": "aliyun_sms"  # 或其他服务商
            }

        except Exception as e:
            print(f"Error sending SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "phone_number": phone_number
            }

    return asyncio.run(_send())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.notification_tasks.send_email_notification")
def send_email_notification(self, email: str, subject: str, content: str,
                           tenant_id: str, template: str = "default"):
    """
    发送邮件通知
    支持HTML模板、附件等
    """
    async def _send():
        try:
            # 这里集成邮件服务
            # 可以使用SMTP、SendGrid、阿里云邮件推送等

            print(f"Sending email to {email}: {subject}")

            # 实际实现示例：
            # import smtplib
            # from email.mime.text import MIMEText
            # from email.mime.multipart import MIMEMultipart
            #
            # msg = MIMEMultipart()
            # msg['From'] = settings.smtp_from_email
            # msg['To'] = email
            # msg['Subject'] = subject
            # msg.attach(MIMEText(content, 'html'))
            #
            # with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            #     server.starttls()
            #     server.login(settings.smtp_username, settings.smtp_password)
            #     server.send_message(msg)

            log_entry = {
                "notification_id": str(uuid.uuid4()),
                "type": "email",
                "recipient": email,
                "subject": subject,
                "tenant_id": tenant_id,
                "template": template,
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            }

            return {
                "success": True,
                "notification_log": log_entry,
                "provider": "smtp"
            }

        except Exception as e:
            print(f"Error sending email: {e}")
            return {
                "success": False,
                "error": str(e),
                "email": email
            }

    return asyncio.run(_send())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.notification_tasks.send_wechat_notification")
def send_wechat_notification(self, openid: str, template_id: str, data: Dict[str, Any],
                            tenant_id: str, notification_type: str = "general"):
    """
    发送微信模板消息
    """
    async def _send():
        try:
            settings = get_settings()

            # 微信模板消息发送
            print(f"Sending WeChat message to {openid} with template {template_id}")

            # 实际实现示例：
            # import httpx
            # access_token = await get_wechat_access_token()
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}",
            #         json={
            #             "touser": openid,
            #             "template_id": template_id,
            #             "data": data
            #         }
            #     )

            log_entry = {
                "notification_id": str(uuid.uuid4()),
                "type": "wechat",
                "recipient": openid,
                "template_id": template_id,
                "data": data,
                "tenant_id": tenant_id,
                "notification_type": notification_type,
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            }

            return {
                "success": True,
                "notification_log": log_entry,
                "provider": "wechat"
            }

        except Exception as e:
            print(f"Error sending WeChat notification: {e}")
            return {
                "success": False,
                "error": str(e),
                "openid": openid
            }

    return asyncio.run(_send())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.notification_tasks.send_shipment_status_update")
def send_shipment_status_update(self, tenant_id: str, shipment_id: str, new_status: str,
                               recipient_contacts: Dict[str, str]):
    """
    发送运单状态更新通知
    支持多渠道发送（短信、邮件、微信）
    """
    async def _send():
        try:
            async with get_session() as session:
                await set_tenant_context(session, tenant_id)

                # 获取运单信息
                stmt = select(Shipment).where(Shipment.id == uuid.UUID(shipment_id))
                result = await session.execute(stmt)
                shipment = result.scalar_one_or_none()

                if not shipment:
                    return {"error": "Shipment not found"}

                # 构建通知内容
                status_text = {
                    "assigned": "已分配车辆",
                    "dispatched": "已发车",
                    "in_transit": "运输中",
                    "delivered": "已送达"
                }.get(new_status, new_status)

                message = f"您的运单 {shipment.shipment_number} 状态已更新为：{status_text}"

                # 多渠道发送通知
                notifications_sent = []

                # 发送短信
                if recipient_contacts.get("phone"):
                    sms_result = send_sms_notification.delay(
                        phone_number=recipient_contacts["phone"],
                        message=message,
                        tenant_id=tenant_id,
                        notification_type="shipment_status"
                    )
                    notifications_sent.append({"type": "sms", "task_id": sms_result.id})

                # 发送邮件
                if recipient_contacts.get("email"):
                    email_subject = f"运单状态更新 - {shipment.shipment_number}"
                    email_content = f"""
                    <h2>运单状态更新通知</h2>
                    <p>运单号：{shipment.shipment_number}</p>
                    <p>客户：{shipment.customer_name}</p>
                    <p>新状态：<strong>{status_text}</strong></p>
                    <p>更新时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    """

                    email_result = send_email_notification.delay(
                        email=recipient_contacts["email"],
                        subject=email_subject,
                        content=email_content,
                        tenant_id=tenant_id,
                        template="shipment_status"
                    )
                    notifications_sent.append({"type": "email", "task_id": email_result.id})

                # 发送微信通知
                if recipient_contacts.get("wechat_openid"):
                    wechat_data = {
                        "first": {"value": "运单状态更新"},
                        "keyword1": {"value": shipment.shipment_number},
                        "keyword2": {"value": status_text},
                        "keyword3": {"value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')},
                        "remark": {"value": "请及时查看运单详情"}
                    }

                    wechat_result = send_wechat_notification.delay(
                        openid=recipient_contacts["wechat_openid"],
                        template_id="SHIPMENT_STATUS_TEMPLATE",
                        data=wechat_data,
                        tenant_id=tenant_id,
                        notification_type="shipment_status"
                    )
                    notifications_sent.append({"type": "wechat", "task_id": wechat_result.id})

                return {
                    "shipment_id": shipment_id,
                    "new_status": new_status,
                    "notifications_sent": notifications_sent,
                    "recipient_contacts": recipient_contacts,
                    "sent_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            print(f"Error sending shipment status update: {e}")
            return {"error": str(e)}

    return asyncio.run(_send())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.notification_tasks.send_geofence_alert")
def send_geofence_alert(self, tenant_id: str, violations: List[Dict[str, Any]],
                       shipment_id: Optional[str] = None, vehicle_id: Optional[str] = None,
                       location: Dict[str, float] = None):
    """
    发送地理围栏违规警报
    """
    async def _send():
        try:
            # 构建警报消息
            alert_message = f"地理围栏违规警报！"
            if shipment_id:
                alert_message += f"运单 {shipment_id[:8]} "
            if vehicle_id:
                alert_message += f"车辆 {vehicle_id[:8]} "

            alert_message += f"在位置 ({location['latitude']}, {location['longitude']}) "
            alert_message += f"触发了 {len(violations)} 个围栏规则。"

            # 获取管理员联系方式（简化处理）
            admin_contacts = {
                "phone": "13800138000",
                "email": "admin@example.com"
            }

            # 发送紧急通知
            notifications_sent = []

            # 短信警报
            sms_result = send_sms_notification.delay(
                phone_number=admin_contacts["phone"],
                message=alert_message,
                tenant_id=tenant_id,
                notification_type="geofence_alert"
            )
            notifications_sent.append({"type": "sms", "task_id": sms_result.id})

            # 邮件详细报告
            email_content = f"""
            <h2>地理围栏违规警报</h2>
            <p><strong>警报时间：</strong>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>位置：</strong>纬度 {location['latitude']}, 经度 {location['longitude']}</p>
            <p><strong>违规详情：</strong></p>
            <ul>
            """
            for violation in violations:
                email_content += f"<li>{violation['fence_name']} - {violation['violation_type']}</li>"

            email_content += """
            </ul>
            <p>请及时处理相关情况。</p>
            """

            email_result = send_email_notification.delay(
                email=admin_contacts["email"],
                subject="地理围栏违规警报",
                content=email_content,
                tenant_id=tenant_id,
                template="geofence_alert"
            )
            notifications_sent.append({"type": "email", "task_id": email_result.id})

            return {
                "alert_type": "geofence_violation",
                "violations": violations,
                "location": location,
                "notifications_sent": notifications_sent,
                "alert_time": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"Error sending geofence alert: {e}")
            return {"error": str(e)}

    return asyncio.run(_send())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.notification_tasks.send_route_alert")
def send_route_alert(self, tenant_id: str, shipment_id: str, alerts: List[Dict[str, Any]],
                    analysis_data: Dict[str, Any]):
    """
    发送路线异常警报
    如超速、长时间停车等
    """
    async def _send():
        try:
            alert_types = [alert["type"] for alert in alerts]
            alert_message = f"运单 {shipment_id[:8]} 路线异常："

            if "speeding" in alert_types:
                alert_message += " 超速行驶"
            if "long_stop" in alert_types:
                alert_message += " 长时间停车"

            # 发送给运营人员
            operational_contacts = {
                "phone": "13900139000",
                "email": "operations@example.com"
            }

            notifications_sent = []

            # 短信通知
            sms_result = send_sms_notification.delay(
                phone_number=operational_contacts["phone"],
                message=alert_message,
                tenant_id=tenant_id,
                notification_type="route_alert"
            )
            notifications_sent.append({"type": "sms", "task_id": sms_result.id})

            return {
                "alert_type": "route_anomaly",
                "shipment_id": shipment_id,
                "alerts": alerts,
                "notifications_sent": notifications_sent,
                "alert_time": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"Error sending route alert: {e}")
            return {"error": str(e)}

    return asyncio.run(_send())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.notification_tasks.send_action_completion_notification")
def send_action_completion_notification(self, tenant_id: str, user_id: str,
                                      action_type: str, result: Dict[str, Any]):
    """
    发送AI动作完成通知
    """
    async def _send():
        try:
            async with get_session() as session:
                await set_tenant_context(session, tenant_id)

                # 获取用户信息
                stmt = select(User).where(User.id == uuid.UUID(user_id))
                user_result = await session.execute(stmt)
                user = user_result.scalar_one_or_none()

                if not user:
                    return {"error": "User not found"}

                # 构建通知消息
                action_names = {
                    "create_shipment": "创建运单",
                    "update_status": "更新状态",
                    "query_location": "查询位置"
                }

                action_name = action_names.get(action_type, action_type)
                message = f"AI助手已成功为您{action_name}"

                if result.get("success"):
                    message += "，请查看相关信息。"
                else:
                    message += f"，但遇到问题：{result.get('message', '未知错误')}"

                # 发送通知
                notifications_sent = []

                # 如果用户有手机号，发送短信
                if hasattr(user, 'phone') and user.phone:
                    sms_result = send_sms_notification.delay(
                        phone_number=user.phone,
                        message=message,
                        tenant_id=tenant_id,
                        notification_type="ai_action_completion"
                    )
                    notifications_sent.append({"type": "sms", "task_id": sms_result.id})

                return {
                    "user_id": user_id,
                    "action_type": action_type,
                    "action_result": result,
                    "notifications_sent": notifications_sent,
                    "notification_time": datetime.utcnow().isoformat()
                }

        except Exception as e:
            print(f"Error sending action completion notification: {e}")
            return {"error": str(e)}

    return asyncio.run(_send())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.notification_tasks.send_pending_reminders")
def send_pending_reminders(self):
    """
    发送待办事项提醒
    定期检查待处理的运单等，发送提醒通知
    """
    async def _send():
        try:
            async with get_session() as session:
                # 查找超过24小时仍未分配的运单
                cutoff_time = datetime.utcnow() - timedelta(hours=24)

                stmt = (
                    select(Shipment)
                    .where(and_(
                        Shipment.status == ShipmentStatus.UNASSIGNED,
                        Shipment.created_at < cutoff_time
                    ))
                )
                result = await session.execute(stmt)
                pending_shipments = result.scalars().all()

                reminders_sent = []

                for shipment in pending_shipments:
                    reminder_message = f"运单 {shipment.shipment_number} 已超过24小时未分配，请及时处理。"

                    # 发送给调度员
                    dispatcher_contacts = {
                        "phone": "13700137000",
                        "email": "dispatcher@example.com"
                    }

                    sms_result = send_sms_notification.delay(
                        phone_number=dispatcher_contacts["phone"],
                        message=reminder_message,
                        tenant_id=str(shipment.tenant_id),
                        notification_type="pending_reminder"
                    )

                    reminders_sent.append({
                        "shipment_id": str(shipment.id),
                        "shipment_number": shipment.shipment_number,
                        "task_id": sms_result.id
                    })

                return {
                    "pending_shipments_count": len(pending_shipments),
                    "reminders_sent": reminders_sent,
                    "check_time": datetime.utcnow().isoformat()
                }

        except Exception as e:
            print(f"Error sending pending reminders: {e}")
            return {"error": str(e)}

    return asyncio.run(_send())