"""
微信API集成模块
支持企业微信消息发送、用户管理、小程序集成等功能
基于Diandian项目验证的微信生态集成经验
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import logging
import hashlib
import time
from pydantic import BaseModel
from enum import Enum

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WeChatMessageType(str, Enum):
    """微信消息类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    TEXTCARD = "textcard"
    NEWS = "news"
    MPNEWS = "mpnews"
    MARKDOWN = "markdown"
    MINIPROGRAM = "miniprogram"
    TEMPLATE = "template"


class WeChatUserInfo(BaseModel):
    """微信用户信息模型"""
    userid: str
    name: str
    department: List[int]
    position: Optional[str] = None
    mobile: Optional[str] = None
    gender: str = "0"  # 0未定义，1男性，2女性
    email: Optional[str] = None
    avatar: Optional[str] = None
    status: int = 1  # 1激活，2禁用，4未激活
    isleader: int = 0  # 是否为部门负责人
    hide_mobile: int = 0  # 是否隐藏手机号
    telephone: Optional[str] = None
    alias: Optional[str] = None
    extattr: Optional[Dict[str, Any]] = None


class WeChatMessage(BaseModel):
    """微信消息模型"""
    touser: Optional[str] = None  # 用户ID列表
    toparty: Optional[str] = None  # 部门ID列表
    totag: Optional[str] = None   # 标签ID列表
    msgtype: WeChatMessageType
    agentid: int
    content: Dict[str, Any]
    safe: int = 0  # 是否保密消息
    enable_id_trans: int = 0  # 是否开启id转译
    enable_duplicate_check: int = 0  # 是否开启重复消息检查
    duplicate_check_interval: int = 1800  # 重复消息检查时间间隔


class WeChatTemplateMessage(BaseModel):
    """微信模板消息模型"""
    touser: str
    template_id: str
    url: Optional[str] = None
    miniprogram: Optional[Dict[str, str]] = None
    data: Dict[str, Dict[str, str]]


class WeChatService:
    """微信服务类"""

    def __init__(self):
        self.corp_id = settings.WECOM_CORP_ID
        self.corp_secret = settings.WECOM_CORP_SECRET
        self.agent_id = settings.WECOM_AGENT_ID
        self.base_url = "https://qyapi.weixin.qq.com/cgi-bin"
        self.timeout = aiohttp.ClientTimeout(total=30)

        # 访问令牌缓存
        self._access_token = None
        self._token_expires_at = None

        if not self.corp_id or not self.corp_secret:
            logger.warning("WeChat credentials not configured")

    async def get_access_token(self) -> str:
        """
        获取企业微信访问令牌

        Returns:
            str: 访问令牌

        Raises:
            Exception: 获取令牌失败
        """
        # 检查缓存的令牌是否有效
        if (self._access_token and self._token_expires_at and
            datetime.now() < self._token_expires_at):
            return self._access_token

        try:
            url = f"{self.base_url}/gettoken"
            params = {
                "corpid": self.corp_id,
                "corpsecret": self.corp_secret
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data.get("errcode") != 0:
                        error_msg = data.get("errmsg", "Unknown error")
                        logger.error(f"Failed to get WeChat access token: {error_msg}")
                        raise Exception(f"WeChat API error: {error_msg}")

                    # 缓存令牌（提前5分钟过期以确保安全）
                    self._access_token = data["access_token"]
                    expires_in = data.get("expires_in", 7200)
                    self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

                    logger.info("WeChat access token refreshed successfully")
                    return self._access_token

        except Exception as e:
            logger.error(f"Failed to get WeChat access token: {e}")
            raise

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        require_token: bool = True
    ) -> Dict[str, Any]:
        """
        发起微信API请求

        Args:
            method: HTTP方法
            endpoint: API端点
            params: 查询参数
            data: 请求体数据
            require_token: 是否需要访问令牌

        Returns:
            Dict[str, Any]: API响应数据
        """
        url = f"{self.base_url}{endpoint}"

        if require_token:
            access_token = await self.get_access_token()
            if params is None:
                params = {}
            params["access_token"] = access_token

        headers = {"Content-Type": "application/json"}

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                if method.upper() == "GET":
                    async with session.get(url, params=params, headers=headers) as response:
                        return await self._handle_response(response)
                elif method.upper() == "POST":
                    async with session.post(url, params=params, json=data, headers=headers) as response:
                        return await self._handle_response(response)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

        except asyncio.TimeoutError:
            logger.error(f"WeChat API request timeout: {method} {url}")
            raise Exception("WeChat API request timeout")
        except Exception as e:
            logger.error(f"WeChat API request failed: {method} {url}, error: {e}")
            raise

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """处理微信API响应"""
        if response.status != 200:
            logger.error(f"WeChat API HTTP error: {response.status}")
            raise Exception(f"WeChat API HTTP error: {response.status}")

        data = await response.json()

        if data.get("errcode") != 0:
            error_msg = data.get("errmsg", "Unknown WeChat API error")
            logger.error(f"WeChat API business error: {error_msg}")
            # 如果是token相关错误，清除缓存的token
            if data.get("errcode") in [40001, 40014, 42001]:
                self._access_token = None
                self._token_expires_at = None
            raise Exception(f"WeChat API error: {error_msg}")

        return data

    async def send_text_message(
        self,
        user_id: str,
        content: str,
        department_id: Optional[str] = None,
        tag_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送文本消息

        Args:
            user_id: 用户ID
            content: 消息内容
            department_id: 部门ID
            tag_id: 标签ID

        Returns:
            Dict[str, Any]: 发送结果
        """
        message_data = {
            "touser": user_id,
            "msgtype": WeChatMessageType.TEXT,
            "agentid": int(self.agent_id),
            "text": {
                "content": content
            }
        }

        if department_id:
            message_data["toparty"] = department_id
        if tag_id:
            message_data["totag"] = tag_id

        return await self._make_request(
            method="POST",
            endpoint="/message/send",
            data=message_data
        )

    async def send_textcard_message(
        self,
        user_id: str,
        title: str,
        description: str,
        url: Optional[str] = None,
        btntxt: str = "详情"
    ) -> Dict[str, Any]:
        """
        发送文本卡片消息

        Args:
            user_id: 用户ID
            title: 卡片标题
            description: 卡片描述
            url: 点击链接
            btntxt: 按钮文字

        Returns:
            Dict[str, Any]: 发送结果
        """
        message_data = {
            "touser": user_id,
            "msgtype": WeChatMessageType.TEXTCARD,
            "agentid": int(self.agent_id),
            "textcard": {
                "title": title,
                "description": description,
                "url": url or "",
                "btntxt": btntxt
            }
        }

        return await self._make_request(
            method="POST",
            endpoint="/message/send",
            data=message_data
        )

    async def send_markdown_message(
        self,
        user_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        发送Markdown消息

        Args:
            user_id: 用户ID
            content: Markdown内容

        Returns:
            Dict[str, Any]: 发送结果
        """
        message_data = {
            "touser": user_id,
            "msgtype": WeChatMessageType.MARKDOWN,
            "agentid": int(self.agent_id),
            "markdown": {
                "content": content
            }
        }

        return await self._make_request(
            method="POST",
            endpoint="/message/send",
            data=message_data
        )

    async def send_template_message(
        self,
        user_id: str,
        template_id: str,
        data: Dict[str, Any],
        url: Optional[str] = None,
        miniprogram: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        发送模板消息

        Args:
            user_id: 用户ID
            template_id: 模板ID
            data: 模板数据
            url: 跳转链接
            miniprogram: 小程序配置

        Returns:
            Dict[str, Any]: 发送结果
        """
        # 转换数据格式为微信要求的格式
        template_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                template_data[key] = value
            else:
                template_data[key] = {"value": str(value)}

        message_data = {
            "touser": user_id,
            "template_id": template_id,
            "data": template_data
        }

        if url:
            message_data["url"] = url
        if miniprogram:
            message_data["miniprogram"] = miniprogram

        return await self._make_request(
            method="POST",
            endpoint="/message/template/send",
            data=message_data
        )

    async def get_user_info(self, user_id: str) -> Optional[WeChatUserInfo]:
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            Optional[WeChatUserInfo]: 用户信息
        """
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/user/get",
                params={"userid": user_id}
            )

            if not response:
                return None

            return WeChatUserInfo(
                userid=response.get("userid"),
                name=response.get("name"),
                department=response.get("department", []),
                position=response.get("position"),
                mobile=response.get("mobile"),
                gender=response.get("gender", "0"),
                email=response.get("email"),
                avatar=response.get("avatar"),
                status=response.get("status", 1),
                isleader=response.get("isleader", 0),
                hide_mobile=response.get("hide_mobile", 0),
                telephone=response.get("telephone"),
                alias=response.get("alias"),
                extattr=response.get("extattr")
            )

        except Exception as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")
            return None

    async def get_department_users(self, department_id: int, fetch_child: bool = False) -> List[WeChatUserInfo]:
        """
        获取部门用户列表

        Args:
            department_id: 部门ID
            fetch_child: 是否获取子部门用户

        Returns:
            List[WeChatUserInfo]: 用户列表
        """
        try:
            params = {
                "department_id": department_id,
                "fetch_child": 1 if fetch_child else 0
            }

            response = await self._make_request(
                method="GET",
                endpoint="/user/list",
                params=params
            )

            users = response.get("userlist", [])
            user_list = []

            for user_data in users:
                try:
                    user = WeChatUserInfo(
                        userid=user_data.get("userid"),
                        name=user_data.get("name"),
                        department=user_data.get("department", []),
                        position=user_data.get("position"),
                        mobile=user_data.get("mobile"),
                        gender=user_data.get("gender", "0"),
                        email=user_data.get("email"),
                        avatar=user_data.get("avatar"),
                        status=user_data.get("status", 1),
                        isleader=user_data.get("isleader", 0),
                        hide_mobile=user_data.get("hide_mobile", 0),
                        telephone=user_data.get("telephone"),
                        alias=user_data.get("alias"),
                        extattr=user_data.get("extattr")
                    )
                    user_list.append(user)
                except Exception as e:
                    logger.warning(f"Failed to parse user data: {e}")
                    continue

            return user_list

        except Exception as e:
            logger.error(f"Failed to get department users for {department_id}: {e}")
            return []

    async def create_user(self, user_info: WeChatUserInfo) -> bool:
        """
        创建用户

        Args:
            user_info: 用户信息

        Returns:
            bool: 创建是否成功
        """
        try:
            user_data = user_info.dict(exclude_none=True)

            await self._make_request(
                method="POST",
                endpoint="/user/create",
                data=user_data
            )

            logger.info(f"WeChat user created successfully: {user_info.userid}")
            return True

        except Exception as e:
            logger.error(f"Failed to create WeChat user {user_info.userid}: {e}")
            return False

    async def update_user(self, user_info: WeChatUserInfo) -> bool:
        """
        更新用户信息

        Args:
            user_info: 用户信息

        Returns:
            bool: 更新是否成功
        """
        try:
            user_data = user_info.dict(exclude_none=True)

            await self._make_request(
                method="POST",
                endpoint="/user/update",
                data=user_data
            )

            logger.info(f"WeChat user updated successfully: {user_info.userid}")
            return True

        except Exception as e:
            logger.error(f"Failed to update WeChat user {user_info.userid}: {e}")
            return False

    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户

        Args:
            user_id: 用户ID

        Returns:
            bool: 删除是否成功
        """
        try:
            await self._make_request(
                method="GET",
                endpoint="/user/delete",
                params={"userid": user_id}
            )

            logger.info(f"WeChat user deleted successfully: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete WeChat user {user_id}: {e}")
            return False

    async def send_shipment_notification(
        self,
        user_id: str,
        shipment_id: str,
        status: str,
        message: str
    ) -> Dict[str, Any]:
        """
        发送运单状态通知

        Args:
            user_id: 用户ID
            shipment_id: 运单ID
            status: 运单状态
            message: 通知消息

        Returns:
            Dict[str, Any]: 发送结果
        """
        title = f"运单状态更新 - {shipment_id}"

        # 使用文本卡片格式发送通知
        return await self.send_textcard_message(
            user_id=user_id,
            title=title,
            description=f"状态：{status}\n{message}",
            btntxt="查看详情"
        )

    async def send_urgent_alert(
        self,
        user_id: str,
        alert_type: str,
        message: str
    ) -> Dict[str, Any]:
        """
        发送紧急告警

        Args:
            user_id: 用户ID
            alert_type: 告警类型
            message: 告警消息

        Returns:
            Dict[str, Any]: 发送结果
        """
        urgent_content = f"🚨 紧急告警 - {alert_type}\n\n{message}\n\n请立即处理！"

        return await self.send_text_message(
            user_id=user_id,
            content=urgent_content
        )

    async def verify_signature(self, signature: str, timestamp: str, nonce: str, echo_str: str) -> str:
        """
        验证微信签名

        Args:
            signature: 微信签名
            timestamp: 时间戳
            nonce: 随机数
            echo_str: 随机字符串

        Returns:
            str: 验证成功返回echo_str，失败返回空字符串
        """
        try:
            token = settings.WECOM_TOKEN or ""
            tmp_list = [token, timestamp, nonce]
            tmp_list.sort()
            tmp_str = "".join(tmp_list)
            tmp_str = hashlib.sha1(tmp_str.encode()).hexdigest()

            if tmp_str == signature:
                return echo_str
            else:
                logger.warning("WeChat signature verification failed")
                return ""

        except Exception as e:
            logger.error(f"Failed to verify WeChat signature: {e}")
            return ""

    async def handle_message_callback(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理微信消息回调

        Args:
            message_data: 消息数据

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            msg_type = message_data.get("MsgType")
            from_user = message_data.get("FromUserName")
            content = message_data.get("Content", "")

            logger.info(f"Received WeChat message: {msg_type} from {from_user}")

            if msg_type == "text":
                # 处理文本消息
                response = await self._handle_text_message(from_user, content)
            elif msg_type == "voice":
                # 处理语音消息
                response = await self._handle_voice_message(from_user, message_data)
            else:
                response = {"type": "text", "content": "消息类型暂不支持"}

            return response

        except Exception as e:
            logger.error(f"Failed to handle WeChat message callback: {e}")
            return {"type": "text", "content": "消息处理失败，请稍后重试"}

    async def _handle_text_message(self, user_id: str, content: str) -> Dict[str, Any]:
        """处理文本消息"""
        # 这里可以集成AI助手处理用户消息
        # 目前返回简单回复
        return {
            "type": "text",
            "content": f"收到您的消息：{content}\n正在为您处理中..."
        }

    async def _handle_voice_message(self, user_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理语音消息"""
        # 这里可以集成语音识别服务
        # 目前返回简单回复
        return {
            "type": "text",
            "content": "收到您的语音消息，正在识别中..."
        }


# 全局微信服务实例
wechat_service = WeChatService()