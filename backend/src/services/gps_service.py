"""
GPS追踪服务
处理GPS位置数据的采集、存储和查询
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from core.config import Settings
from core.security import set_tenant_context
from models.gps import GPSLocation, RoutePoint, Geofence, GPSSource
from models.logistics import Shipment
from models.logistics import Vehicle


class GPSServiceError(Exception):
    """GPS服务相关异常"""
    pass


@dataclass
class LocationPoint:
    """位置点数据"""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: datetime = None
    address: Optional[str] = None


@dataclass
class TrackingFilter:
    """GPS追踪筛选条件"""
    shipment_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    time_from: Optional[datetime] = None
    time_to: Optional[datetime] = None
    min_speed: Optional[float] = None
    max_speed: Optional[float] = None


@dataclass
class RouteAnalysis:
    """路线分析结果"""
    total_distance: float  # 总距离(公里)
    total_duration: int    # 总时长(分钟)
    average_speed: float   # 平均速度(km/h)
    max_speed: float      # 最高速度(km/h)
    stop_count: int       # 停车次数
    stop_duration: int    # 停车总时长(分钟)


class GPSService:
    """GPS追踪服务类"""

    def __init__(self):
        pass

    async def record_location(
        self,
        session: AsyncSession,
        tenant_id: str,
        location: LocationPoint,
        shipment_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        source: GPSSource = GPSSource.G7_API,
        device_id: Optional[str] = None,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> GPSLocation:
        """记录GPS位置数据"""
        try:
            await set_tenant_context(session, tenant_id)

            # 创建GPS位置记录
            gps_location = GPSLocation(
                tenant_id=uuid.UUID(tenant_id),
                shipment_id=uuid.UUID(shipment_id) if shipment_id else None,
                vehicle_id=uuid.UUID(vehicle_id) if vehicle_id else None,
                latitude=Decimal(str(location.latitude)),
                longitude=Decimal(str(location.longitude)),
                altitude=Decimal(str(location.altitude)) if location.altitude else None,
                accuracy=Decimal(str(location.accuracy)) if location.accuracy else None,
                gps_time=location.timestamp or datetime.utcnow(),
                speed=Decimal(str(location.speed)) if location.speed else None,
                heading=Decimal(str(location.heading)) if location.heading else None,
                source=source.value,
                device_id=device_id,
                raw_data=raw_data,
                address=location.address,
                is_valid="1",
                is_real_time="1"
            )

            session.add(gps_location)
            await session.commit()
            await session.refresh(gps_location)

            # 如果有关联车辆，更新车辆位置
            if vehicle_id:
                await self._update_vehicle_location(
                    session, vehicle_id, location.latitude, location.longitude
                )

            return gps_location

        except Exception as e:
            await session.rollback()
            raise GPSServiceError(f"Failed to record location: {str(e)}")

    async def get_current_location(
        self,
        session: AsyncSession,
        tenant_id: str,
        shipment_id: Optional[str] = None,
        vehicle_id: Optional[str] = None
    ) -> Optional[GPSLocation]:
        """获取当前位置"""
        try:
            await set_tenant_context(session, tenant_id)

            # 构建查询条件
            conditions = []
            if shipment_id:
                conditions.append(GPSLocation.shipment_id == uuid.UUID(shipment_id))
            if vehicle_id:
                conditions.append(GPSLocation.vehicle_id == uuid.UUID(vehicle_id))

            if not conditions:
                raise GPSServiceError("Must provide either shipment_id or vehicle_id")

            # 获取最新位置
            stmt = (
                select(GPSLocation)
                .where(and_(*conditions))
                .where(GPSLocation.is_valid == "1")
                .order_by(desc(GPSLocation.gps_time))
                .limit(1)
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            raise GPSServiceError(f"Failed to get current location: {str(e)}")

    async def get_tracking_history(
        self,
        session: AsyncSession,
        tenant_id: str,
        filters: Optional[TrackingFilter] = None,
        limit: int = 1000
    ) -> List[GPSLocation]:
        """获取GPS追踪历史"""
        try:
            await set_tenant_context(session, tenant_id)

            # 构建查询
            stmt = select(GPSLocation).where(GPSLocation.is_valid == "1")

            # 应用筛选条件
            if filters:
                conditions = []

                if filters.shipment_id:
                    conditions.append(
                        GPSLocation.shipment_id == uuid.UUID(filters.shipment_id)
                    )

                if filters.vehicle_id:
                    conditions.append(
                        GPSLocation.vehicle_id == uuid.UUID(filters.vehicle_id)
                    )

                if filters.time_from:
                    conditions.append(GPSLocation.gps_time >= filters.time_from)

                if filters.time_to:
                    conditions.append(GPSLocation.gps_time <= filters.time_to)

                if filters.min_speed is not None:
                    conditions.append(GPSLocation.speed >= Decimal(str(filters.min_speed)))

                if filters.max_speed is not None:
                    conditions.append(GPSLocation.speed <= Decimal(str(filters.max_speed)))

                if conditions:
                    stmt = stmt.where(and_(*conditions))

            # 排序和限制
            stmt = stmt.order_by(GPSLocation.gps_time).limit(limit)

            result = await session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            raise GPSServiceError(f"Failed to get tracking history: {str(e)}")

    async def analyze_route(
        self,
        session: AsyncSession,
        tenant_id: str,
        shipment_id: str,
        time_from: Optional[datetime] = None,
        time_to: Optional[datetime] = None
    ) -> RouteAnalysis:
        """分析路线数据"""
        try:
            # 获取GPS追踪历史
            filters = TrackingFilter(
                shipment_id=shipment_id,
                time_from=time_from,
                time_to=time_to
            )

            gps_points = await self.get_tracking_history(
                session=session,
                tenant_id=tenant_id,
                filters=filters
            )

            if len(gps_points) < 2:
                return RouteAnalysis(
                    total_distance=0,
                    total_duration=0,
                    average_speed=0,
                    max_speed=0,
                    stop_count=0,
                    stop_duration=0
                )

            # 计算路线分析数据
            total_distance = 0
            max_speed = 0
            speeds = []
            stop_count = 0
            stop_duration = 0

            for i in range(1, len(gps_points)):
                prev_point = gps_points[i-1]
                curr_point = gps_points[i]

                # 计算距离
                distance = self._calculate_distance(
                    float(prev_point.latitude), float(prev_point.longitude),
                    float(curr_point.latitude), float(curr_point.longitude)
                )
                total_distance += distance

                # 记录速度
                if curr_point.speed:
                    speed = float(curr_point.speed)
                    speeds.append(speed)
                    max_speed = max(max_speed, speed)

                    # 检测停车（速度小于5km/h）
                    if speed < 5:
                        time_diff = (curr_point.gps_time - prev_point.gps_time).total_seconds() / 60
                        if time_diff > 2:  # 停车超过2分钟
                            stop_count += 1
                            stop_duration += int(time_diff)

            # 计算总时长和平均速度
            total_duration = int((gps_points[-1].gps_time - gps_points[0].gps_time).total_seconds() / 60)
            average_speed = sum(speeds) / len(speeds) if speeds else 0

            return RouteAnalysis(
                total_distance=round(total_distance, 2),
                total_duration=total_duration,
                average_speed=round(average_speed, 2),
                max_speed=round(max_speed, 2),
                stop_count=stop_count,
                stop_duration=stop_duration
            )

        except Exception as e:
            raise GPSServiceError(f"Failed to analyze route: {str(e)}")

    async def create_geofence(
        self,
        session: AsyncSession,
        tenant_id: str,
        name: str,
        fence_type: str,
        center_lat: float,
        center_lng: float,
        radius_meters: float,
        description: Optional[str] = None
    ) -> Geofence:
        """创建地理围栏"""
        try:
            await set_tenant_context(session, tenant_id)

            geofence = Geofence(
                tenant_id=uuid.UUID(tenant_id),
                name=name,
                description=description,
                fence_type=fence_type,
                center_latitude=Decimal(str(center_lat)),
                center_longitude=Decimal(str(center_lng)),
                radius_meters=Decimal(str(radius_meters)),
                is_active="1"
            )

            session.add(geofence)
            await session.commit()
            await session.refresh(geofence)

            return geofence

        except Exception as e:
            await session.rollback()
            raise GPSServiceError(f"Failed to create geofence: {str(e)}")

    async def check_geofence_violation(
        self,
        session: AsyncSession,
        tenant_id: str,
        latitude: float,
        longitude: float
    ) -> List[Dict[str, Any]]:
        """检查地理围栏违规"""
        try:
            await set_tenant_context(session, tenant_id)

            # 获取活跃的围栏
            stmt = select(Geofence).where(Geofence.is_active == "1")
            result = await session.execute(stmt)
            geofences = result.scalars().all()

            violations = []
            for fence in geofences:
                if fence.fence_type == "circle":
                    distance = self._calculate_distance(
                        latitude, longitude,
                        float(fence.center_latitude), float(fence.center_longitude)
                    )
                    # 转换为米
                    distance_meters = distance * 1000

                    if distance_meters <= float(fence.radius_meters):
                        violations.append({
                            "fence_id": str(fence.id),
                            "fence_name": fence.name,
                            "violation_type": "inside",
                            "distance_meters": round(distance_meters, 2)
                        })

            return violations

        except Exception as e:
            raise GPSServiceError(f"Failed to check geofence violation: {str(e)}")

    async def get_real_time_tracking(
        self,
        session: AsyncSession,
        tenant_id: str,
        time_window_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """获取实时追踪数据"""
        try:
            await set_tenant_context(session, tenant_id)

            # 获取指定时间窗口内的最新位置
            time_threshold = datetime.utcnow() - timedelta(minutes=time_window_minutes)

            stmt = (
                select(GPSLocation)
                .options(
                    selectinload(GPSLocation.shipment),
                    selectinload(GPSLocation.vehicle)
                )
                .where(GPSLocation.gps_time >= time_threshold)
                .where(GPSLocation.is_valid == "1")
                .where(GPSLocation.is_real_time == "1")
                .order_by(desc(GPSLocation.gps_time))
            )

            result = await session.execute(stmt)
            locations = result.scalars().all()

            # 按运单/车辆分组，取最新位置
            tracking_data = {}
            for loc in locations:
                key = f"shipment_{loc.shipment_id}" if loc.shipment_id else f"vehicle_{loc.vehicle_id}"

                if key not in tracking_data:
                    tracking_data[key] = {
                        "type": "shipment" if loc.shipment_id else "vehicle",
                        "id": str(loc.shipment_id) if loc.shipment_id else str(loc.vehicle_id),
                        "latest_location": {
                            "latitude": float(loc.latitude),
                            "longitude": float(loc.longitude),
                            "speed": float(loc.speed) if loc.speed else None,
                            "heading": float(loc.heading) if loc.heading else None,
                            "timestamp": loc.gps_time.isoformat(),
                            "address": loc.address
                        },
                        "entity_info": {}
                    }

                    # 添加实体信息
                    if loc.shipment:
                        tracking_data[key]["entity_info"] = {
                            "shipment_number": loc.shipment.shipment_number,
                            "customer_name": loc.shipment.customer_name,
                            "status": loc.shipment.status.value
                        }
                    elif loc.vehicle:
                        tracking_data[key]["entity_info"] = {
                            "license_plate": loc.vehicle.license_plate,
                            "driver_name": loc.vehicle.driver_name,
                            "status": loc.vehicle.status
                        }

            return list(tracking_data.values())

        except Exception as e:
            raise GPSServiceError(f"Failed to get real-time tracking: {str(e)}")

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间距离（公里）使用Haversine公式"""
        import math

        # 转换为弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # 地球半径（公里）
        r = 6371

        return c * r

    async def _update_vehicle_location(
        self,
        session: AsyncSession,
        vehicle_id: str,
        latitude: float,
        longitude: float
    ):
        """更新车辆当前位置"""
        try:
            stmt = (
                update(Vehicle)
                .where(Vehicle.id == uuid.UUID(vehicle_id))
                .values(
                    current_coordinates=[longitude, latitude],
                    last_update_time=datetime.utcnow()
                )
            )
            await session.execute(stmt)
            await session.commit()

        except Exception as e:
            # 记录错误但不影响主流程
            print(f"Warning: Failed to update vehicle location: {e}")


# Global GPS service instance
def get_gps_service() -> GPSService:
    """获取GPS服务实例"""
    return GPSService()