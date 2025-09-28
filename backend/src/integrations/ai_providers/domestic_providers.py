"""
国产AI模型提供商集成
支持文心一言、通义千问、智谱AI等主流国产大模型
基于官方API实现，提供与OpenAI一致的接口和功能
"""

from typing import List, Dict, Any, Optional, Type, TypeVar, Union
from datetime import datetime
import asyncio
import aiohttp
import hashlib
import hmac
import time
import json
import logging
from pydantic import BaseModel, Field
from enum import Enum

from core.config import get_settings
from integrations.ai_providers.openai_provider import (
    MessageRole, ChatMessage, TokenUsage, AIResponse,
    ShipmentExtractionResult, RouteOptimizationResult,
    BusinessSummaryResult, AlertClassificationResult
)

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar('T', bound=BaseModel)


class WenxinModel(str, Enum):
    """百度文心一言模型枚举"""
    ERNIE_4_0_8K = "completions_pro"
    ERNIE_4_0_TURBO_8K = "ernie-4.0-turbo-8k"
    ERNIE_3_5_8K = "completions"
    ERNIE_LITE = "ernie-lite"
    ERNIE_SPEED = "ernie-speed"


class QwenModel(str, Enum):
    """阿里通义千问模型枚举"""
    QWEN_MAX = "qwen-max"
    QWEN_PLUS = "qwen-plus"
    QWEN_TURBO = "qwen-turbo"
    QWEN_LONG = "qwen-long"


class ZhipuModel(str, Enum):
    """智谱AI模型枚举"""
    GLM_4 = "glm-4"
    GLM_4_FLASH = "glm-4-flash"
    GLM_3_TURBO = "glm-3-turbo"


class WenxinProvider:
    """百度文心一言API提供商"""

    def __init__(self):
        self.api_key = settings.wenxin_api_key
        self.secret_key = settings.wenxin_secret_key
        self.default_model = WenxinModel.ERNIE_3_5_8K
        self.base_url = "https://aip.baidubce.com"
        self.access_token = None
        self.token_expires_at = None

        if not self.api_key or not self.secret_key:
            logger.warning("Wenxin API credentials not configured")

        # Token计费表 (CNY per 1K tokens)
        self.pricing = {
            WenxinModel.ERNIE_4_0_8K: {"input": 0.12, "output": 0.12},
            WenxinModel.ERNIE_4_0_TURBO_8K: {"input": 0.02, "output": 0.06},
            WenxinModel.ERNIE_3_5_8K: {"input": 0.004, "output": 0.008},
            WenxinModel.ERNIE_LITE: {"input": 0.0008, "output": 0.002},
            WenxinModel.ERNIE_SPEED: {"input": 0.0004, "output": 0.0008}
        }

    async def _get_access_token(self) -> str:
        """获取百度API访问令牌"""
        if self.access_token and self.token_expires_at and time.time() < self.token_expires_at:
            return self.access_token

        url = f"{self.base_url}/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get Wenxin access token: {response.status}")

                data = await response.json()
                if "error" in data:
                    raise Exception(f"Wenxin token error: {data['error_description']}")

                self.access_token = data["access_token"]
                self.token_expires_at = time.time() + data["expires_in"] - 300  # 提前5分钟刷新
                return self.access_token

    def _calculate_cost(self, model: WenxinModel, prompt_tokens: int, completion_tokens: int) -> float:
        """计算API调用成本 (CNY)"""
        if model not in self.pricing:
            return 0.0

        pricing = self.pricing[model]
        prompt_cost = (prompt_tokens / 1000) * pricing["input"]
        completion_cost = (completion_tokens / 1000) * pricing["output"]
        return prompt_cost + completion_cost

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[WenxinModel] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Type[T]] = None
    ) -> Union[AIResponse, T]:
        """
        文心一言聊天完成
        """
        if not self.api_key:
            error_msg = "Wenxin API key not configured"
            logger.error(error_msg)
            if response_format:
                return response_format(
                    success=False,
                    error_message=error_msg
                )
            return AIResponse(
                success=False,
                content="",
                model="",
                response_time_ms=0,
                error_message=error_msg
            )

        start_time = datetime.now()
        selected_model = model or self.default_model

        try:
            access_token = await self._get_access_token()
            url = f"{self.base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{selected_model.value}"

            # 转换消息格式 (文心一言要求最后一条必须是user消息)
            wenxin_messages = []
            for msg in messages:
                if msg.role == MessageRole.SYSTEM:
                    # 系统消息转换为第一条用户消息
                    if not wenxin_messages:
                        wenxin_messages.append({"role": "user", "content": msg.content})
                    else:
                        # 如果已有消息，将系统消息合并到第一条用户消息
                        wenxin_messages[0]["content"] = f"{msg.content}\n\n{wenxin_messages[0]['content']}"
                else:
                    wenxin_messages.append({"role": msg.role.value, "content": msg.content})

            # 确保最后一条是用户消息
            if wenxin_messages and wenxin_messages[-1]["role"] != "user":
                wenxin_messages.append({"role": "user", "content": "请继续"})

            payload = {
                "messages": wenxin_messages,
                "temperature": temperature,
                "stream": False
            }

            if max_tokens:
                payload["max_output_tokens"] = max_tokens

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    params={"access_token": access_token},
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Wenxin API error: {response.status}")

                    data = await response.json()

                    if "error_code" in data:
                        raise Exception(f"Wenxin API error: {data['error_msg']}")

                    end_time = datetime.now()
                    response_time_ms = int((end_time - start_time).total_seconds() * 1000)

                    # 计算成本和token使用
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

                    cost = self._calculate_cost(selected_model, prompt_tokens, completion_tokens)

                    token_usage = TokenUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        estimated_cost=cost
                    )

                    content = data.get("result", "")

                    # 如果需要结构化输出，使用简单的JSON解析
                    if response_format and content:
                        try:
                            # 尝试从响应中提取JSON
                            if "{" in content and "}" in content:
                                json_start = content.find("{")
                                json_end = content.rfind("}") + 1
                                json_str = content[json_start:json_end]
                                parsed_data = json.loads(json_str)
                                return response_format(**parsed_data)
                            else:
                                # 如果没有JSON，返回错误
                                return response_format(
                                    success=False,
                                    error_message="无法解析结构化响应"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to parse structured response: {e}")
                            return response_format(
                                success=False,
                                error_message=f"解析响应失败: {e}"
                            )

                    return AIResponse(
                        success=True,
                        content=content,
                        model=selected_model.value,
                        response_time_ms=response_time_ms,
                        token_usage=token_usage
                    )

        except Exception as e:
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            logger.error(f"Wenxin API error: {e}")

            if response_format:
                try:
                    return response_format(
                        success=False,
                        error_message=str(e)
                    )
                except:
                    raise e

            return AIResponse(
                success=False,
                content="",
                model=selected_model.value,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )


class QwenProvider:
    """阿里通义千问API提供商"""

    def __init__(self):
        self.api_key = settings.qwen_api_key
        self.default_model = QwenModel.QWEN_TURBO
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

        if not self.api_key:
            logger.warning("Qwen API key not configured")

        # Token计费表 (CNY per 1K tokens)
        self.pricing = {
            QwenModel.QWEN_MAX: {"input": 0.04, "output": 0.12},
            QwenModel.QWEN_PLUS: {"input": 0.008, "output": 0.024},
            QwenModel.QWEN_TURBO: {"input": 0.003, "output": 0.006},
            QwenModel.QWEN_LONG: {"input": 0.0005, "output": 0.002}
        }

    def _calculate_cost(self, model: QwenModel, prompt_tokens: int, completion_tokens: int) -> float:
        """计算API调用成本 (CNY)"""
        if model not in self.pricing:
            return 0.0

        pricing = self.pricing[model]
        prompt_cost = (prompt_tokens / 1000) * pricing["input"]
        completion_cost = (completion_tokens / 1000) * pricing["output"]
        return prompt_cost + completion_cost

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[QwenModel] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Type[T]] = None
    ) -> Union[AIResponse, T]:
        """
        通义千问聊天完成
        """
        if not self.api_key:
            error_msg = "Qwen API key not configured"
            logger.error(error_msg)
            if response_format:
                return response_format(
                    success=False,
                    error_message=error_msg
                )
            return AIResponse(
                success=False,
                content="",
                model="",
                response_time_ms=0,
                error_message=error_msg
            )

        start_time = datetime.now()
        selected_model = model or self.default_model

        try:
            # 转换消息格式
            qwen_messages = []
            for msg in messages:
                qwen_messages.append({"role": msg.role.value, "content": msg.content})

            payload = {
                "model": selected_model.value,
                "input": {
                    "messages": qwen_messages
                },
                "parameters": {
                    "temperature": temperature,
                    "result_format": "message"
                }
            }

            if max_tokens:
                payload["parameters"]["max_tokens"] = max_tokens

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Qwen API error: {response.status}")

                    data = await response.json()

                    if "code" in data and data["code"] != 200:
                        raise Exception(f"Qwen API error: {data['message']}")

                    end_time = datetime.now()
                    response_time_ms = int((end_time - start_time).total_seconds() * 1000)

                    # 计算成本和token使用
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("input_tokens", 0)
                    completion_tokens = usage.get("output_tokens", 0)
                    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

                    cost = self._calculate_cost(selected_model, prompt_tokens, completion_tokens)

                    token_usage = TokenUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        estimated_cost=cost
                    )

                    content = data["output"]["text"]

                    # 如果需要结构化输出，使用简单的JSON解析
                    if response_format and content:
                        try:
                            if "{" in content and "}" in content:
                                json_start = content.find("{")
                                json_end = content.rfind("}") + 1
                                json_str = content[json_start:json_end]
                                parsed_data = json.loads(json_str)
                                return response_format(**parsed_data)
                            else:
                                return response_format(
                                    success=False,
                                    error_message="无法解析结构化响应"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to parse structured response: {e}")
                            return response_format(
                                success=False,
                                error_message=f"解析响应失败: {e}"
                            )

                    return AIResponse(
                        success=True,
                        content=content,
                        model=selected_model.value,
                        response_time_ms=response_time_ms,
                        token_usage=token_usage
                    )

        except Exception as e:
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            logger.error(f"Qwen API error: {e}")

            if response_format:
                try:
                    return response_format(
                        success=False,
                        error_message=str(e)
                    )
                except:
                    raise e

            return AIResponse(
                success=False,
                content="",
                model=selected_model.value,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )


class ZhipuProvider:
    """智谱AI API提供商"""

    def __init__(self):
        self.api_key = settings.zhipu_api_key
        self.default_model = ZhipuModel.GLM_3_TURBO
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

        if not self.api_key:
            logger.warning("Zhipu API key not configured")

        # Token计费表 (CNY per 1K tokens)
        self.pricing = {
            ZhipuModel.GLM_4: {"input": 0.1, "output": 0.1},
            ZhipuModel.GLM_4_FLASH: {"input": 0.001, "output": 0.001},
            ZhipuModel.GLM_3_TURBO: {"input": 0.005, "output": 0.005}
        }

    def _generate_token(self) -> str:
        """生成智谱AI JWT Token"""
        import jwt
        from datetime import datetime, timedelta

        api_key_parts = self.api_key.split(".")
        if len(api_key_parts) != 2:
            raise ValueError("Invalid Zhipu API key format")

        id, secret = api_key_parts

        payload = {
            "api_key": id,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "timestamp": int(datetime.utcnow().timestamp() * 1000)
        }

        return jwt.encode(payload, secret, algorithm="HS256", headers={"alg": "HS256", "sign_type": "SIGN"})

    def _calculate_cost(self, model: ZhipuModel, prompt_tokens: int, completion_tokens: int) -> float:
        """计算API调用成本 (CNY)"""
        if model not in self.pricing:
            return 0.0

        pricing = self.pricing[model]
        prompt_cost = (prompt_tokens / 1000) * pricing["input"]
        completion_cost = (completion_tokens / 1000) * pricing["output"]
        return prompt_cost + completion_cost

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[ZhipuModel] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Type[T]] = None
    ) -> Union[AIResponse, T]:
        """
        智谱AI聊天完成
        """
        if not self.api_key:
            error_msg = "Zhipu API key not configured"
            logger.error(error_msg)
            if response_format:
                return response_format(
                    success=False,
                    error_message=error_msg
                )
            return AIResponse(
                success=False,
                content="",
                model="",
                response_time_ms=0,
                error_message=error_msg
            )

        start_time = datetime.now()
        selected_model = model or self.default_model

        try:
            token = self._generate_token()

            # 转换消息格式
            zhipu_messages = []
            for msg in messages:
                zhipu_messages.append({"role": msg.role.value, "content": msg.content})

            payload = {
                "model": selected_model.value,
                "messages": zhipu_messages,
                "temperature": temperature,
                "stream": False
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Zhipu API error: {response.status}")

                    data = await response.json()

                    if "error" in data:
                        raise Exception(f"Zhipu API error: {data['error']['message']}")

                    end_time = datetime.now()
                    response_time_ms = int((end_time - start_time).total_seconds() * 1000)

                    # 计算成本和token使用
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

                    cost = self._calculate_cost(selected_model, prompt_tokens, completion_tokens)

                    token_usage = TokenUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        estimated_cost=cost
                    )

                    content = data["choices"][0]["message"]["content"]

                    # 如果需要结构化输出，使用简单的JSON解析
                    if response_format and content:
                        try:
                            if "{" in content and "}" in content:
                                json_start = content.find("{")
                                json_end = content.rfind("}") + 1
                                json_str = content[json_start:json_end]
                                parsed_data = json.loads(json_str)
                                return response_format(**parsed_data)
                            else:
                                return response_format(
                                    success=False,
                                    error_message="无法解析结构化响应"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to parse structured response: {e}")
                            return response_format(
                                success=False,
                                error_message=f"解析响应失败: {e}"
                            )

                    return AIResponse(
                        success=True,
                        content=content,
                        model=selected_model.value,
                        response_time_ms=response_time_ms,
                        token_usage=token_usage
                    )

        except Exception as e:
            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            logger.error(f"Zhipu API error: {e}")

            if response_format:
                try:
                    return response_format(
                        success=False,
                        error_message=str(e)
                    )
                except:
                    raise e

            return AIResponse(
                success=False,
                content="",
                model=selected_model.value,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )


class DomesticAIManager:
    """国产AI模型管理器"""

    def __init__(self):
        self.wenxin_provider = WenxinProvider()
        self.qwen_provider = QwenProvider()
        self.zhipu_provider = ZhipuProvider()

    async def extract_shipment_info(self, user_message: str, provider: str = "wenxin") -> ShipmentExtractionResult:
        """
        从用户消息中提取运单信息

        Args:
            user_message: 用户输入的消息
            provider: AI提供商 (wenxin/qwen/zhipu)

        Returns:
            ShipmentExtractionResult: 提取的运单信息
        """
        system_prompt = """
你是一个物流运单信息提取专家。请从用户消息中提取出运单相关信息，并以JSON格式返回。

要求：
1. 准确识别发件人和收件人信息
2. 提取货物描述、重量、数量等信息
3. 识别特殊要求和时间要求
4. 评估信息提取的置信度 (0-1)

返回格式：
{
    "sender_name": "发件人姓名",
    "sender_phone": "发件人电话",
    "sender_address": "发件地址",
    "receiver_name": "收件人姓名",
    "receiver_phone": "收件人电话",
    "receiver_address": "收件地址",
    "cargo_description": "货物描述",
    "cargo_weight": 重量数值或null,
    "cargo_quantity": 数量或null,
    "special_requirements": ["特殊要求列表"],
    "pickup_time": "提货时间或null",
    "estimated_freight": 预估费用或null,
    "confidence_score": 置信度数值
}
"""

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=user_message)
        ]

        if provider == "wenxin":
            return await self.wenxin_provider.chat_completion(
                messages=messages,
                response_format=ShipmentExtractionResult
            )
        elif provider == "qwen":
            return await self.qwen_provider.chat_completion(
                messages=messages,
                response_format=ShipmentExtractionResult
            )
        elif provider == "zhipu":
            return await self.zhipu_provider.chat_completion(
                messages=messages,
                response_format=ShipmentExtractionResult
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def optimize_route(
        self,
        waypoints: List[Dict[str, Any]],
        vehicle_info: Dict[str, Any],
        provider: str = "qwen"
    ) -> RouteOptimizationResult:
        """
        优化配送路线

        Args:
            waypoints: 配送点信息列表
            vehicle_info: 车辆信息
            provider: AI提供商

        Returns:
            RouteOptimizationResult: 路线优化结果
        """
        system_prompt = """
你是一个物流路线优化专家。请根据配送点信息和车辆信息，提供最优的配送路线方案。

考虑因素：
1. 总里程最短
2. 时间效率最高
3. 油费成本最低
4. 交通状况和限行
5. 配送时间窗口

返回JSON格式的优化结果，包含配送顺序、距离、时间、成本等信息。
"""

        waypoints_text = f"配送点信息：{json.dumps(waypoints, ensure_ascii=False)}"
        vehicle_text = f"车辆信息：{json.dumps(vehicle_info, ensure_ascii=False)}"

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=f"{waypoints_text}\n{vehicle_text}")
        ]

        if provider == "wenxin":
            return await self.wenxin_provider.chat_completion(
                messages=messages,
                response_format=RouteOptimizationResult
            )
        elif provider == "qwen":
            return await self.qwen_provider.chat_completion(
                messages=messages,
                response_format=RouteOptimizationResult
            )
        elif provider == "zhipu":
            return await self.zhipu_provider.chat_completion(
                messages=messages,
                response_format=RouteOptimizationResult
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate_business_summary(
        self,
        data: Dict[str, Any],
        period: str,
        provider: str = "zhipu"
    ) -> BusinessSummaryResult:
        """
        生成业务数据摘要

        Args:
            data: 业务数据
            period: 统计周期
            provider: AI提供商

        Returns:
            BusinessSummaryResult: 业务摘要结果
        """
        system_prompt = """
你是一个物流业务分析专家。请分析提供的业务数据，生成专业的业务摘要报告。

分析内容：
1. 关键指标统计
2. 趋势分析和洞察
3. 问题识别和改进建议
4. 风险预警和提醒

返回JSON格式的分析结果。
"""

        data_text = f"业务数据：{json.dumps(data, ensure_ascii=False)}"
        period_text = f"统计周期：{period}"

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=f"{data_text}\n{period_text}")
        ]

        if provider == "wenxin":
            return await self.wenxin_provider.chat_completion(
                messages=messages,
                response_format=BusinessSummaryResult
            )
        elif provider == "qwen":
            return await self.qwen_provider.chat_completion(
                messages=messages,
                response_format=BusinessSummaryResult
            )
        elif provider == "zhipu":
            return await self.zhipu_provider.chat_completion(
                messages=messages,
                response_format=BusinessSummaryResult
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def classify_alert(
        self,
        alert_data: Dict[str, Any],
        provider: str = "wenxin"
    ) -> AlertClassificationResult:
        """
        分类和处理告警信息

        Args:
            alert_data: 告警数据
            provider: AI提供商

        Returns:
            AlertClassificationResult: 告警分类结果
        """
        system_prompt = """
你是一个智能告警分析专家。请分析告警信息，进行分类和优先级判定。

分析要点：
1. 告警类型识别
2. 严重程度评估
3. 影响范围分析
4. 处理建议制定
5. 自动化处理可能性

返回JSON格式的分类结果。
"""

        alert_text = f"告警信息：{json.dumps(alert_data, ensure_ascii=False)}"

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=alert_text)
        ]

        if provider == "wenxin":
            return await self.wenxin_provider.chat_completion(
                messages=messages,
                response_format=AlertClassificationResult
            )
        elif provider == "qwen":
            return await self.qwen_provider.chat_completion(
                messages=messages,
                response_format=AlertClassificationResult
            )
        elif provider == "zhipu":
            return await self.zhipu_provider.chat_completion(
                messages=messages,
                response_format=AlertClassificationResult
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")


# 全局国产AI管理器实例
domestic_ai_manager = DomesticAIManager()