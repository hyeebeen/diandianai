"""
短信服务集成模块
支持多家短信服务商，包括阿里云、腾讯云、华为云等
提供短信发送、模板管理、发送状态查询等功能
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import logging
import hashlib
import hmac
import base64
import uuid
from pydantic import BaseModel
from enum import Enum

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SMSProvider(str, Enum):
    """短信服务商枚举"""
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    HUAWEI = "huawei"
    YUNPIAN = "yunpian"
    MOCK = "mock"  # 测试用


class SMSStatus(str, Enum):
    """短信状态枚举"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SMSTemplate(BaseModel):
    """短信模板模型"""
    template_id: str
    provider: SMSProvider
    content: str
    params: List[str]
    type: str  # 验证码、通知、营销等
    is_active: bool = True


class SMSMessage(BaseModel):
    """短信消息模型"""
    phone_number: str
    content: str
    template_id: Optional[str] = None
    template_params: Optional[Dict[str, str]] = None
    provider: SMSProvider = SMSProvider.ALIYUN
    priority: int = 1  # 1-5，数字越大优先级越高
    scheduled_time: Optional[datetime] = None
    callback_url: Optional[str] = None


class SMSResult(BaseModel):
    """短信发送结果模型"""
    message_id: str
    phone_number: str
    status: SMSStatus
    provider: SMSProvider
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    cost: Optional[float] = None  # 发送费用


class AliyunSMSClient:
    """阿里云短信客户端"""

    def __init__(self):
        self.access_key_id = settings.ALIYUN_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_ACCESS_KEY_SECRET
        self.endpoint = "https://dysmsapi.aliyuncs.com"
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def send_sms(
        self,
        phone_number: str,
        sign_name: str,
        template_code: str,
        template_param: Optional[str] = None
    ) -> Dict[str, Any]:
        """发送阿里云短信"""
        try:
            # 构建请求参数
            params = {
                "Action": "SendSms",
                "Version": "2017-05-25",
                "RegionId": "cn-hangzhou",
                "PhoneNumbers": phone_number,
                "SignName": sign_name,
                "TemplateCode": template_code,
                "Format": "JSON",
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "SignatureMethod": "HMAC-SHA1",
                "SignatureVersion": "1.0",
                "SignatureNonce": str(uuid.uuid4()),
                "AccessKeyId": self.access_key_id
            }

            if template_param:
                params["TemplateParam"] = template_param

            # 生成签名
            signature = self._generate_signature(params)
            params["Signature"] = signature

            # 发送请求
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.endpoint, data=params) as response:
                    result = await response.json()
                    return result

        except Exception as e:
            logger.error(f"Aliyun SMS send failed: {e}")
            return {"Code": "ERROR", "Message": str(e)}

    def _generate_signature(self, params: Dict[str, str]) -> str:
        """生成阿里云API签名"""
        # 排序参数
        sorted_params = sorted(params.items())

        # 构建查询字符串
        query_string = "&".join([f"{k}={self._percent_encode(str(v))}" for k, v in sorted_params])

        # 构建签名字符串
        string_to_sign = f"POST&{self._percent_encode('/')}&{self._percent_encode(query_string)}"

        # 计算签名
        key = f"{self.access_key_secret}&"
        signature = hmac.new(
            key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()

        return base64.b64encode(signature).decode('utf-8')

    def _percent_encode(self, value: str) -> str:
        """URL编码"""
        import urllib.parse
        return urllib.parse.quote(value, safe='')


class TencentSMSClient:
    """腾讯云短信客户端"""

    def __init__(self):
        self.secret_id = settings.TENCENT_SECRET_ID
        self.secret_key = settings.TENCENT_SECRET_KEY
        self.endpoint = "https://sms.tencentcloudapi.com"
        self.service = "sms"
        self.version = "2021-01-11"
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def send_sms(
        self,
        phone_numbers: List[str],
        template_id: str,
        template_params: Optional[List[str]] = None,
        sms_sdk_app_id: str = "",
        sign_name: str = ""
    ) -> Dict[str, Any]:
        """发送腾讯云短信"""
        try:
            # 构建请求体
            payload = {
                "PhoneNumberSet": phone_numbers,
                "SmsSdkAppId": sms_sdk_app_id,
                "TemplateId": template_id,
                "SignName": sign_name
            }

            if template_params:
                payload["TemplateParamSet"] = template_params

            # 生成签名
            headers = self._generate_headers(json.dumps(payload))

            # 发送请求
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.endpoint,
                    headers=headers,
                    data=json.dumps(payload)
                ) as response:
                    result = await response.json()
                    return result

        except Exception as e:
            logger.error(f"Tencent SMS send failed: {e}")
            return {"Response": {"Error": {"Code": "ERROR", "Message": str(e)}}}

    def _generate_headers(self, payload: str) -> Dict[str, str]:
        """生成腾讯云API请求头"""
        timestamp = str(int(datetime.now().timestamp()))
        date = datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d')

        # 构建规范请求串
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        canonical_headers = f"content-type:application/json; charset=utf-8\nhost:sms.tencentcloudapi.com\n"
        signed_headers = "content-type;host"
        hashed_request_payload = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        canonical_request = f"{http_request_method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{hashed_request_payload}"

        # 拼接待签名字符串
        algorithm = "TC3-HMAC-SHA256"
        credential_scope = f"{date}/{self.service}/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"

        # 计算签名
        secret_date = hmac.new(
            f"TC3{self.secret_key}".encode('utf-8'),
            date.encode('utf-8'),
            hashlib.sha256
        ).digest()
        secret_service = hmac.new(secret_date, self.service.encode('utf-8'), hashlib.sha256).digest()
        secret_signing = hmac.new(secret_service, "tc3_request".encode('utf-8'), hashlib.sha256).digest()
        signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        # 拼接Authorization
        authorization = f"{algorithm} Credential={self.secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

        return {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": "sms.tencentcloudapi.com",
            "X-TC-Action": "SendSms",
            "X-TC-Timestamp": timestamp,
            "X-TC-Version": self.version
        }


class MockSMSClient:
    """模拟短信客户端（用于测试）"""

    async def send_sms(self, phone_number: str, content: str, **kwargs) -> Dict[str, Any]:
        """模拟发送短信"""
        logger.info(f"Mock SMS to {phone_number}: {content}")

        # 模拟网络延迟
        await asyncio.sleep(0.1)

        # 模拟成功和失败情况
        if phone_number.endswith("0000"):
            return {"code": "FAILED", "message": "Invalid phone number"}
        else:
            return {
                "code": "OK",
                "message": "Success",
                "message_id": f"mock_{uuid.uuid4().hex[:16]}"
            }


class SMSService:
    """短信服务主类"""

    def __init__(self):
        self.default_provider = SMSProvider(settings.SMS_DEFAULT_PROVIDER or "mock")

        # 初始化各个客户端
        self.aliyun_client = AliyunSMSClient()
        self.tencent_client = TencentSMSClient()
        self.mock_client = MockSMSClient()

        # 模板配置
        self.templates = {
            "verification_code": SMSTemplate(
                template_id="SMS_123456789",
                provider=SMSProvider.ALIYUN,
                content="您的验证码是：{code}，请在5分钟内使用。",
                params=["code"],
                type="verification"
            ),
            "shipment_status_update": SMSTemplate(
                template_id="SMS_987654321",
                provider=SMSProvider.ALIYUN,
                content="您的运单{shipment_id}状态已更新为{status}，详情：{message}",
                params=["shipment_id", "status", "message"],
                type="notification"
            ),
            "urgent_alert": SMSTemplate(
                template_id="SMS_111222333",
                provider=SMSProvider.ALIYUN,
                content="紧急告警：{alert_type}，{message}，请立即处理！",
                params=["alert_type", "message"],
                type="alert"
            )
        }

    async def send_sms(
        self,
        phone_number: str,
        content: str,
        template_id: Optional[str] = None,
        template_params: Optional[Dict[str, str]] = None,
        provider: Optional[SMSProvider] = None
    ) -> SMSResult:
        """
        发送短信

        Args:
            phone_number: 手机号码
            content: 短信内容
            template_id: 模板ID
            template_params: 模板参数
            provider: 指定服务商

        Returns:
            SMSResult: 发送结果
        """
        if not self._validate_phone_number(phone_number):
            return SMSResult(
                message_id="",
                phone_number=phone_number,
                status=SMSStatus.FAILED,
                provider=provider or self.default_provider,
                error_code="INVALID_PHONE",
                error_message="Invalid phone number format"
            )

        # 选择服务商
        sms_provider = provider or self.default_provider

        try:
            # 根据服务商发送短信
            if sms_provider == SMSProvider.ALIYUN:
                result = await self._send_via_aliyun(phone_number, content, template_id, template_params)
            elif sms_provider == SMSProvider.TENCENT:
                result = await self._send_via_tencent(phone_number, content, template_id, template_params)
            elif sms_provider == SMSProvider.MOCK:
                result = await self._send_via_mock(phone_number, content)
            else:
                raise ValueError(f"Unsupported SMS provider: {sms_provider}")

            return result

        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return SMSResult(
                message_id="",
                phone_number=phone_number,
                status=SMSStatus.FAILED,
                provider=sms_provider,
                error_code="SEND_FAILED",
                error_message=str(e)
            )

    async def _send_via_aliyun(
        self,
        phone_number: str,
        content: str,
        template_id: Optional[str] = None,
        template_params: Optional[Dict[str, str]] = None
    ) -> SMSResult:
        """通过阿里云发送短信"""
        sign_name = settings.ALIYUN_SMS_SIGN_NAME or "物流平台"
        template_code = template_id or settings.ALIYUN_SMS_TEMPLATE_CODE

        # 转换模板参数格式
        template_param = None
        if template_params:
            template_param = json.dumps(template_params)

        result = await self.aliyun_client.send_sms(
            phone_number=phone_number,
            sign_name=sign_name,
            template_code=template_code,
            template_param=template_param
        )

        if result.get("Code") == "OK":
            return SMSResult(
                message_id=result.get("BizId", ""),
                phone_number=phone_number,
                status=SMSStatus.SENT,
                provider=SMSProvider.ALIYUN,
                sent_at=datetime.now()
            )
        else:
            return SMSResult(
                message_id="",
                phone_number=phone_number,
                status=SMSStatus.FAILED,
                provider=SMSProvider.ALIYUN,
                error_code=result.get("Code"),
                error_message=result.get("Message")
            )

    async def _send_via_tencent(
        self,
        phone_number: str,
        content: str,
        template_id: Optional[str] = None,
        template_params: Optional[Dict[str, str]] = None
    ) -> SMSResult:
        """通过腾讯云发送短信"""
        # 格式化手机号（腾讯云需要+86前缀）
        if not phone_number.startswith("+86"):
            phone_number = f"+86{phone_number}"

        template_params_list = []
        if template_params:
            template_params_list = list(template_params.values())

        result = await self.tencent_client.send_sms(
            phone_numbers=[phone_number],
            template_id=template_id or settings.TENCENT_SMS_TEMPLATE_ID,
            template_params=template_params_list,
            sms_sdk_app_id=settings.TENCENT_SMS_SDK_APP_ID,
            sign_name=settings.TENCENT_SMS_SIGN_NAME or "物流平台"
        )

        response = result.get("Response", {})
        if "Error" not in response:
            send_status_set = response.get("SendStatusSet", [])
            if send_status_set and send_status_set[0].get("Code") == "Ok":
                return SMSResult(
                    message_id=send_status_set[0].get("SerialNo", ""),
                    phone_number=phone_number.replace("+86", ""),
                    status=SMSStatus.SENT,
                    provider=SMSProvider.TENCENT,
                    sent_at=datetime.now()
                )

        error = response.get("Error", {})
        return SMSResult(
            message_id="",
            phone_number=phone_number.replace("+86", ""),
            status=SMSStatus.FAILED,
            provider=SMSProvider.TENCENT,
            error_code=error.get("Code"),
            error_message=error.get("Message")
        )

    async def _send_via_mock(self, phone_number: str, content: str) -> SMSResult:
        """通过模拟客户端发送短信"""
        result = await self.mock_client.send_sms(phone_number, content)

        if result.get("code") == "OK":
            return SMSResult(
                message_id=result.get("message_id", ""),
                phone_number=phone_number,
                status=SMSStatus.SENT,
                provider=SMSProvider.MOCK,
                sent_at=datetime.now()
            )
        else:
            return SMSResult(
                message_id="",
                phone_number=phone_number,
                status=SMSStatus.FAILED,
                provider=SMSProvider.MOCK,
                error_code="MOCK_ERROR",
                error_message=result.get("message", "Mock send failed")
            )

    def _validate_phone_number(self, phone_number: str) -> bool:
        """验证手机号码格式"""
        import re

        # 移除可能的+86前缀和空格
        clean_phone = phone_number.replace("+86", "").replace(" ", "").replace("-", "")

        # 验证中国大陆手机号格式
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, clean_phone))

    async def send_verification_code(self, phone_number: str, code: str) -> SMSResult:
        """
        发送验证码短信

        Args:
            phone_number: 手机号码
            code: 验证码

        Returns:
            SMSResult: 发送结果
        """
        return await self.send_sms(
            phone_number=phone_number,
            content=f"您的验证码是：{code}，请在5分钟内使用。",
            template_id="verification_code",
            template_params={"code": code}
        )

    async def send_shipment_notification(
        self,
        phone_number: str,
        shipment_id: str,
        status: str,
        message: str
    ) -> SMSResult:
        """
        发送运单状态通知短信

        Args:
            phone_number: 手机号码
            shipment_id: 运单ID
            status: 运单状态
            message: 通知消息

        Returns:
            SMSResult: 发送结果
        """
        return await self.send_sms(
            phone_number=phone_number,
            content=f"您的运单{shipment_id}状态已更新为{status}，详情：{message}",
            template_id="shipment_status_update",
            template_params={
                "shipment_id": shipment_id,
                "status": status,
                "message": message
            }
        )

    async def send_urgent_alert(
        self,
        phone_number: str,
        alert_type: str,
        message: str
    ) -> SMSResult:
        """
        发送紧急告警短信

        Args:
            phone_number: 手机号码
            alert_type: 告警类型
            message: 告警消息

        Returns:
            SMSResult: 发送结果
        """
        return await self.send_sms(
            phone_number=phone_number,
            content=f"紧急告警：{alert_type}，{message}，请立即处理！",
            template_id="urgent_alert",
            template_params={
                "alert_type": alert_type,
                "message": message
            }
        )

    async def batch_send_sms(self, messages: List[SMSMessage]) -> List[SMSResult]:
        """
        批量发送短信

        Args:
            messages: 短信消息列表

        Returns:
            List[SMSResult]: 发送结果列表
        """
        # 并行发送所有短信
        tasks = [
            asyncio.create_task(
                self.send_sms(
                    phone_number=msg.phone_number,
                    content=msg.content,
                    template_id=msg.template_id,
                    template_params=msg.template_params,
                    provider=msg.provider
                )
            )
            for msg in messages
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch SMS {i} failed: {result}")
                final_results.append(SMSResult(
                    message_id="",
                    phone_number=messages[i].phone_number,
                    status=SMSStatus.FAILED,
                    provider=messages[i].provider,
                    error_code="BATCH_ERROR",
                    error_message=str(result)
                ))
            else:
                final_results.append(result)

        return final_results

    async def query_sms_status(self, message_id: str, provider: SMSProvider) -> SMSStatus:
        """
        查询短信状态

        Args:
            message_id: 消息ID
            provider: 服务商

        Returns:
            SMSStatus: 短信状态
        """
        try:
            # 这里应该调用各服务商的状态查询API
            # 目前返回模拟状态
            if provider == SMSProvider.MOCK:
                return SMSStatus.DELIVERED

            # 实际实现时需要调用相应的API
            return SMSStatus.UNKNOWN

        except Exception as e:
            logger.error(f"Failed to query SMS status: {e}")
            return SMSStatus.UNKNOWN


# 全局短信服务实例
sms_service = SMSService()