"""
G7定位API集成模块
提供G7平台GPS设备数据获取和webhook处理功能
基于Diandian项目验证的G7 API集成经验
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import aiohttp
import hmac
import hashlib
import json
import logging
from pydantic import BaseModel, validator
from enum import Enum

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class G7DeviceStatus(str, Enum):
    """G7设备状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    SLEEP = "sleep"
    MAINTENANCE = "maintenance"


class G7AlarmType(str, Enum):
    """G7告警类型枚举"""
    OVERSPEED = "overspeed"
    ROUTE_DEVIATION = "route_deviation"
    LONG_STOP = "long_stop"
    GEOFENCE_IN = "geofence_in"
    GEOFENCE_OUT = "geofence_out"
    POWER_OFF = "power_off"
    EMERGENCY = "emergency"


class G7LocationData(BaseModel):
    """G7位置数据模型"""
    device_id: str
    vehicle_id: str
    latitude: float
    longitude: float
    speed: float
    heading: float
    altitude: Optional[float] = None
    accuracy: float
    timestamp: datetime
    status: G7DeviceStatus
    signal_strength: Optional[int] = None
    battery_level: Optional[int] = None
    mileage: Optional[float] = None

    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @validator('speed')
    def validate_speed(cls, v):
        if v < 0:
            raise ValueError('Speed cannot be negative')
        return v


class G7AlarmData(BaseModel):
    """G7告警数据模型"""
    alarm_id: str
    device_id: str
    vehicle_id: str
    alarm_type: G7AlarmType
    alarm_time: datetime
    location: G7LocationData
    description: str
    severity: str
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None


class G7WebhookPayload(BaseModel):
    """G7 Webhook载荷模型"""
    event_type: str
    timestamp: datetime
    device_id: str
    data: Dict[str, Any]
    signature: str


class G7ApiClient:
    """G7 API客户端"""

    def __init__(self):
        self.base_url = settings.G7_BASE_URL or "https://openapi.g7.com.cn"
        self.api_key = settings.G7_API_KEY
        self.app_secret = settings.G7_APP_SECRET
        self.timeout = aiohttp.ClientTimeout(total=30)

        if not self.api_key or not self.app_secret:
            logger.warning("G7 API credentials not configured")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发起G7 API请求

        Args:
            method: HTTP方法
            endpoint: API端点
            params: 查询参数
            data: 请求体数据

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            Exception: API请求失败
        """
        url = f"{self.base_url}{endpoint}"

        # 生成签名
        timestamp = str(int(datetime.now().timestamp()))
        signature = self._generate_signature(method, endpoint, timestamp, params, data)

        headers = {
            "Content-Type": "application/json",
            "X-G7-Api-Key": self.api_key,
            "X-G7-Timestamp": timestamp,
            "X-G7-Signature": signature
        }

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
            logger.error(f"G7 API request timeout: {method} {url}")
            raise Exception("G7 API request timeout")
        except Exception as e:
            logger.error(f"G7 API request failed: {method} {url}, error: {e}")
            raise

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """处理G7 API响应"""
        response_text = await response.text()

        if response.status != 200:
            logger.error(f"G7 API error: {response.status}, {response_text}")
            raise Exception(f"G7 API error: {response.status}")

        try:
            data = json.loads(response_text)
            if data.get("code") != 0:
                error_msg = data.get("message", "Unknown G7 API error")
                logger.error(f"G7 API business error: {error_msg}")
                raise Exception(f"G7 API error: {error_msg}")

            return data.get("data", {})

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from G7 API: {response_text}")
            raise Exception("Invalid JSON response from G7 API")

    def _generate_signature(
        self,
        method: str,
        endpoint: str,
        timestamp: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成G7 API签名

        Args:
            method: HTTP方法
            endpoint: API端点
            timestamp: 时间戳
            params: 查询参数
            data: 请求体数据

        Returns:
            str: 签名字符串
        """
        # 构建签名字符串
        sign_parts = [
            method.upper(),
            endpoint,
            timestamp,
            self.api_key
        ]

        # 添加查询参数
        if params:
            sorted_params = sorted(params.items())
            param_string = "&".join([f"{k}={v}" for k, v in sorted_params])
            sign_parts.append(param_string)

        # 添加请求体
        if data:
            json_string = json.dumps(data, sort_keys=True, separators=(',', ':'))
            sign_parts.append(json_string)

        # 生成签名
        sign_string = "&".join(sign_parts)
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def get_vehicle_location(self, vehicle_id: str) -> Optional[G7LocationData]:
        """
        获取车辆当前位置

        Args:
            vehicle_id: 车辆ID

        Returns:
            Optional[G7LocationData]: 位置数据，如果获取失败返回None
        """
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/api/v1/vehicle/location",
                params={"vehicle_id": vehicle_id}
            )

            if not response:
                return None

            return G7LocationData(
                device_id=response.get("device_id"),
                vehicle_id=vehicle_id,
                latitude=response.get("latitude"),
                longitude=response.get("longitude"),
                speed=response.get("speed", 0),
                heading=response.get("heading", 0),
                altitude=response.get("altitude"),
                accuracy=response.get("accuracy", 10),
                timestamp=datetime.fromisoformat(response.get("timestamp")),
                status=G7DeviceStatus(response.get("status", "offline")),
                signal_strength=response.get("signal_strength"),
                battery_level=response.get("battery_level"),
                mileage=response.get("mileage")
            )

        except Exception as e:
            logger.error(f"Failed to get vehicle location for {vehicle_id}: {e}")
            return None

    async def get_vehicle_track(
        self,
        vehicle_id: str,
        start_time: datetime,
        end_time: datetime,
        interval: int = 60
    ) -> List[G7LocationData]:
        """
        获取车辆历史轨迹

        Args:
            vehicle_id: 车辆ID
            start_time: 开始时间
            end_time: 结束时间
            interval: 采样间隔(秒)

        Returns:
            List[G7LocationData]: 轨迹点列表
        """
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/api/v1/vehicle/track",
                params={
                    "vehicle_id": vehicle_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "interval": interval
                }
            )

            tracks = response.get("tracks", [])
            location_list = []

            for track in tracks:
                try:
                    location = G7LocationData(
                        device_id=track.get("device_id"),
                        vehicle_id=vehicle_id,
                        latitude=track.get("latitude"),
                        longitude=track.get("longitude"),
                        speed=track.get("speed", 0),
                        heading=track.get("heading", 0),
                        altitude=track.get("altitude"),
                        accuracy=track.get("accuracy", 10),
                        timestamp=datetime.fromisoformat(track.get("timestamp")),
                        status=G7DeviceStatus(track.get("status", "offline")),
                        signal_strength=track.get("signal_strength"),
                        battery_level=track.get("battery_level"),
                        mileage=track.get("mileage")
                    )
                    location_list.append(location)
                except Exception as e:
                    logger.warning(f"Failed to parse track point: {e}")
                    continue

            return location_list

        except Exception as e:
            logger.error(f"Failed to get vehicle track for {vehicle_id}: {e}")
            return []

    async def get_vehicle_alarms(
        self,
        vehicle_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[G7AlarmData]:
        """
        获取车辆告警信息

        Args:
            vehicle_id: 车辆ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            List[G7AlarmData]: 告警列表
        """
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/api/v1/vehicle/alarms",
                params={
                    "vehicle_id": vehicle_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            )

            alarms = response.get("alarms", [])
            alarm_list = []

            for alarm in alarms:
                try:
                    # 解析告警位置信息
                    location_data = alarm.get("location", {})
                    location = G7LocationData(
                        device_id=alarm.get("device_id"),
                        vehicle_id=vehicle_id,
                        latitude=location_data.get("latitude"),
                        longitude=location_data.get("longitude"),
                        speed=location_data.get("speed", 0),
                        heading=location_data.get("heading", 0),
                        altitude=location_data.get("altitude"),
                        accuracy=location_data.get("accuracy", 10),
                        timestamp=datetime.fromisoformat(location_data.get("timestamp")),
                        status=G7DeviceStatus(location_data.get("status", "offline"))
                    )

                    alarm_data = G7AlarmData(
                        alarm_id=alarm.get("alarm_id"),
                        device_id=alarm.get("device_id"),
                        vehicle_id=vehicle_id,
                        alarm_type=G7AlarmType(alarm.get("alarm_type")),
                        alarm_time=datetime.fromisoformat(alarm.get("alarm_time")),
                        location=location,
                        description=alarm.get("description", ""),
                        severity=alarm.get("severity", "medium"),
                        is_resolved=alarm.get("is_resolved", False),
                        resolved_at=datetime.fromisoformat(alarm.get("resolved_at")) if alarm.get("resolved_at") else None
                    )
                    alarm_list.append(alarm_data)

                except Exception as e:
                    logger.warning(f"Failed to parse alarm data: {e}")
                    continue

            return alarm_list

        except Exception as e:
            logger.error(f"Failed to get vehicle alarms for {vehicle_id}: {e}")
            return []

    async def batch_get_vehicle_locations(self, vehicle_ids: List[str]) -> Dict[str, Optional[G7LocationData]]:
        """
        批量获取车辆位置

        Args:
            vehicle_ids: 车辆ID列表

        Returns:
            Dict[str, Optional[G7LocationData]]: 车辆位置字典
        """
        try:
            response = await self._make_request(
                method="POST",
                endpoint="/api/v1/vehicle/batch_location",
                data={"vehicle_ids": vehicle_ids}
            )

            locations = response.get("locations", {})
            result = {}

            for vehicle_id in vehicle_ids:
                location_data = locations.get(vehicle_id)
                if location_data:
                    try:
                        result[vehicle_id] = G7LocationData(
                            device_id=location_data.get("device_id"),
                            vehicle_id=vehicle_id,
                            latitude=location_data.get("latitude"),
                            longitude=location_data.get("longitude"),
                            speed=location_data.get("speed", 0),
                            heading=location_data.get("heading", 0),
                            altitude=location_data.get("altitude"),
                            accuracy=location_data.get("accuracy", 10),
                            timestamp=datetime.fromisoformat(location_data.get("timestamp")),
                            status=G7DeviceStatus(location_data.get("status", "offline")),
                            signal_strength=location_data.get("signal_strength"),
                            battery_level=location_data.get("battery_level"),
                            mileage=location_data.get("mileage")
                        )
                    except Exception as e:
                        logger.warning(f"Failed to parse location for vehicle {vehicle_id}: {e}")
                        result[vehicle_id] = None
                else:
                    result[vehicle_id] = None

            return result

        except Exception as e:
            logger.error(f"Failed to batch get vehicle locations: {e}")
            return {vehicle_id: None for vehicle_id in vehicle_ids}

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        验证G7 Webhook签名

        Args:
            payload: 请求体
            signature: 签名

        Returns:
            bool: 签名是否有效
        """
        try:
            expected_signature = hmac.new(
                self.app_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Failed to verify webhook signature: {e}")
            return False

    async def process_webhook(self, payload: G7WebhookPayload) -> bool:
        """
        处理G7 Webhook事件

        Args:
            payload: Webhook载荷

        Returns:
            bool: 处理是否成功
        """
        try:
            event_type = payload.event_type
            device_id = payload.device_id
            data = payload.data

            logger.info(f"Processing G7 webhook: {event_type} for device {device_id}")

            if event_type == "location_update":
                # 处理位置更新事件
                await self._handle_location_update(device_id, data)
            elif event_type == "alarm_triggered":
                # 处理告警事件
                await self._handle_alarm_triggered(device_id, data)
            elif event_type == "device_status_change":
                # 处理设备状态变化事件
                await self._handle_device_status_change(device_id, data)
            else:
                logger.warning(f"Unknown webhook event type: {event_type}")

            return True

        except Exception as e:
            logger.error(f"Failed to process webhook: {e}")
            return False

    async def _handle_location_update(self, device_id: str, data: Dict[str, Any]):
        """处理位置更新事件"""
        # 这里应该调用GPS服务更新位置数据
        logger.info(f"Location update for device {device_id}: {data}")

    async def _handle_alarm_triggered(self, device_id: str, data: Dict[str, Any]):
        """处理告警触发事件"""
        # 这里应该调用通知服务发送告警
        logger.info(f"Alarm triggered for device {device_id}: {data}")

    async def _handle_device_status_change(self, device_id: str, data: Dict[str, Any]):
        """处理设备状态变化事件"""
        # 这里应该更新设备状态
        logger.info(f"Device status change for {device_id}: {data}")


# 全局G7客户端实例
g7_client = G7ApiClient()