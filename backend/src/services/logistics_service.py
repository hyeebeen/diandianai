from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload

from core.config import Settings
from core.security import set_tenant_context
from models.logistics import (
    Shipment, ShipmentStop, Vehicle,
    ShipmentStatus, StopType
)
from models.gps import GPSLocation


class LogisticsServiceError(Exception):
    """物流服务相关异常"""
    pass


@dataclass
class ShipmentFilter:
    """运单筛选条件"""
    status: Optional[List[ShipmentStatus]] = None
    customer_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_text: Optional[str] = None


@dataclass
class ShipmentSummary:
    """运单统计摘要"""
    total_count: int
    status_counts: Dict[str, int]
    total_weight: float
    pending_deliveries: int


class LogisticsService:
    """物流业务服务类"""

    def __init__(self):
        pass

    async def create_shipment(
        self,
        session: AsyncSession,
        tenant_id: str,
        pickup_address: str,
        delivery_address: str,
        customer_name: str,
        weight_kg: Optional[float] = None,
        commodity_type: Optional[str] = None,
        transport_mode: Optional[str] = None,
        equipment_type: Optional[str] = None,
        packing_type: Optional[str] = None,
        pickup_coordinates: Optional[List[float]] = None,
        delivery_coordinates: Optional[List[float]] = None,
        notes: Optional[str] = None,
        badges: Optional[List[str]] = None,
        pickup_time: Optional[datetime] = None,
        delivery_time: Optional[datetime] = None
    ) -> Shipment:
        """创建运单"""
        try:
            await set_tenant_context(session, tenant_id)

            # Generate shipment number
            shipment_number = await self._generate_shipment_number(session)

            # Create shipment
            shipment = Shipment(
                tenant_id=uuid.UUID(tenant_id),
                shipment_number=shipment_number,
                pickup_address=pickup_address,
                delivery_address=delivery_address,
                customer_name=customer_name,
                weight_kg=weight_kg,
                commodity_type=commodity_type,
                transport_mode=transport_mode,
                equipment_type=equipment_type,
                packing_type=packing_type,
                pickup_coordinates=pickup_coordinates,
                delivery_coordinates=delivery_coordinates,
                notes=notes,
                badges=badges or [],
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                status=ShipmentStatus.UNASSIGNED
            )

            session.add(shipment)
            await session.commit()
            await session.refresh(shipment)

            # Create default stops
            await self._create_default_stops(session, shipment)

            return shipment

        except Exception as e:
            await session.rollback()
            raise LogisticsServiceError(f"Failed to create shipment: {str(e)}")

    async def update_shipment_status(
        self,
        session: AsyncSession,
        tenant_id: str,
        shipment_id: str,
        new_status: ShipmentStatus,
        notes: Optional[str] = None
    ) -> Shipment:
        """更新运单状态"""
        try:
            await set_tenant_context(session, tenant_id)

            stmt = select(Shipment).where(Shipment.id == uuid.UUID(shipment_id))
            result = await session.execute(stmt)
            shipment = result.scalar_one_or_none()

            if not shipment:
                raise LogisticsServiceError("Shipment not found")

            # Validate status transition
            if not self._is_valid_status_transition(shipment.status, new_status):
                raise LogisticsServiceError(
                    f"Invalid status transition from {shipment.status} to {new_status}"
                )

            # Update status
            old_status = shipment.status
            shipment.status = new_status

            if notes:
                shipment.notes = (shipment.notes or "") + f"\n[{datetime.utcnow()}] {notes}"

            # Update timestamps based on status
            if new_status == ShipmentStatus.DELIVERED:
                shipment.delivery_time = datetime.utcnow()

            await session.commit()
            await session.refresh(shipment)

            # Log status change
            await self._log_status_change(session, shipment_id, old_status, new_status)

            return shipment

        except Exception as e:
            await session.rollback()
            raise LogisticsServiceError(f"Failed to update shipment status: {str(e)}")

    async def get_shipment(
        self,
        session: AsyncSession,
        tenant_id: str,
        shipment_id: str
    ) -> Optional[Shipment]:
        """获取运单详情"""
        try:
            await set_tenant_context(session, tenant_id)

            stmt = (
                select(Shipment)
                .where(Shipment.id == uuid.UUID(shipment_id))
                .options(
                    selectinload(Shipment.stops),
                    selectinload(Shipment.gps_tracks)
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            raise LogisticsServiceError(f"Failed to get shipment: {str(e)}")

    async def get_shipments(
        self,
        session: AsyncSession,
        tenant_id: str,
        filters: Optional[ShipmentFilter] = None,
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[Shipment], int]:
        """获取运单列表"""
        try:
            await set_tenant_context(session, tenant_id)

            # Build query
            stmt = select(Shipment)
            count_stmt = select(func.count(Shipment.id))

            # Apply filters
            if filters:
                conditions = []

                if filters.status:
                    conditions.append(Shipment.status.in_(filters.status))

                if filters.customer_name:
                    conditions.append(
                        Shipment.customer_name.ilike(f"%{filters.customer_name}%")
                    )

                if filters.date_from:
                    conditions.append(Shipment.created_at >= filters.date_from)

                if filters.date_to:
                    conditions.append(Shipment.created_at <= filters.date_to)

                if filters.search_text:
                    search_conditions = or_(
                        Shipment.shipment_number.ilike(f"%{filters.search_text}%"),
                        Shipment.pickup_address.ilike(f"%{filters.search_text}%"),
                        Shipment.delivery_address.ilike(f"%{filters.search_text}%"),
                        Shipment.customer_name.ilike(f"%{filters.search_text}%")
                    )
                    conditions.append(search_conditions)

                if conditions:
                    stmt = stmt.where(and_(*conditions))
                    count_stmt = count_stmt.where(and_(*conditions))

            # Get total count
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar()

            # Get paginated results
            stmt = stmt.order_by(Shipment.created_at.desc()).offset(offset).limit(limit)
            result = await session.execute(stmt)
            shipments = result.scalars().all()

            return list(shipments), total_count

        except Exception as e:
            raise LogisticsServiceError(f"Failed to get shipments: {str(e)}")

    async def get_shipment_summary(
        self,
        session: AsyncSession,
        tenant_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> ShipmentSummary:
        """获取运单统计摘要"""
        try:
            await set_tenant_context(session, tenant_id)

            # Build base query
            conditions = []
            if date_from:
                conditions.append(Shipment.created_at >= date_from)
            if date_to:
                conditions.append(Shipment.created_at <= date_to)

            base_query = select(Shipment)
            if conditions:
                base_query = base_query.where(and_(*conditions))

            # Total count
            count_stmt = select(func.count(Shipment.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar()

            # Status counts
            status_stmt = (
                select(Shipment.status, func.count(Shipment.id))
                .group_by(Shipment.status)
            )
            if conditions:
                status_stmt = status_stmt.where(and_(*conditions))

            status_result = await session.execute(status_stmt)
            status_counts = {status.value: count for status, count in status_result.fetchall()}

            # Total weight
            weight_stmt = select(func.sum(Shipment.weight_kg))
            if conditions:
                weight_stmt = weight_stmt.where(and_(*conditions))
            weight_result = await session.execute(weight_stmt)
            total_weight = weight_result.scalar() or 0.0

            # Pending deliveries
            pending_stmt = select(func.count(Shipment.id)).where(
                Shipment.status.in_([
                    ShipmentStatus.ASSIGNED,
                    ShipmentStatus.DISPATCHED,
                    ShipmentStatus.IN_TRANSIT,
                    ShipmentStatus.AT_PICKUP,
                    ShipmentStatus.LOADED
                ])
            )
            if conditions:
                pending_stmt = pending_stmt.where(and_(*conditions))
            pending_result = await session.execute(pending_stmt)
            pending_deliveries = pending_result.scalar()

            return ShipmentSummary(
                total_count=total_count,
                status_counts=status_counts,
                total_weight=total_weight,
                pending_deliveries=pending_deliveries
            )

        except Exception as e:
            raise LogisticsServiceError(f"Failed to get shipment summary: {str(e)}")

    async def assign_vehicle(
        self,
        session: AsyncSession,
        tenant_id: str,
        shipment_id: str,
        vehicle_id: str
    ) -> Shipment:
        """分配车辆给运单"""
        try:
            await set_tenant_context(session, tenant_id)

            # Get shipment
            shipment = await self.get_shipment(session, tenant_id, shipment_id)
            if not shipment:
                raise LogisticsServiceError("Shipment not found")

            # Get vehicle
            vehicle_stmt = select(Vehicle).where(Vehicle.id == uuid.UUID(vehicle_id))
            vehicle_result = await session.execute(vehicle_stmt)
            vehicle = vehicle_result.scalar_one_or_none()

            if not vehicle:
                raise LogisticsServiceError("Vehicle not found")

            # Check vehicle availability
            if vehicle.status != "available":
                raise LogisticsServiceError("Vehicle is not available")

            # Update shipment status
            if shipment.status == ShipmentStatus.UNASSIGNED:
                shipment.status = ShipmentStatus.ASSIGNED

            # Update vehicle status
            vehicle.status = "busy"

            await session.commit()

            return shipment

        except Exception as e:
            await session.rollback()
            raise LogisticsServiceError(f"Failed to assign vehicle: {str(e)}")

    async def get_shipment_route(
        self,
        session: AsyncSession,
        tenant_id: str,
        shipment_id: str
    ) -> List[Dict[str, Any]]:
        """获取运单路线"""
        try:
            await set_tenant_context(session, tenant_id)

            # Get GPS tracking data
            stmt = (
                select(GPSLocation)
                .where(GPSLocation.shipment_id == uuid.UUID(shipment_id))
                .order_by(GPSLocation.gps_time)
            )
            result = await session.execute(stmt)
            gps_points = result.scalars().all()

            route_data = []
            for point in gps_points:
                route_data.append({
                    "latitude": float(point.latitude),
                    "longitude": float(point.longitude),
                    "timestamp": point.gps_time.isoformat(),
                    "speed": float(point.speed or 0),
                    "address": point.address
                })

            return route_data

        except Exception as e:
            raise LogisticsServiceError(f"Failed to get shipment route: {str(e)}")

    async def _generate_shipment_number(self, session: AsyncSession) -> str:
        """生成运单号"""
        # Get current date
        today = datetime.utcnow().strftime("%Y%m%d")

        # Count shipments created today
        stmt = select(func.count(Shipment.id)).where(
            func.date(Shipment.created_at) == datetime.utcnow().date()
        )
        result = await session.execute(stmt)
        count = result.scalar() + 1

        return f"DD{today}{count:04d}"

    async def _create_default_stops(self, session: AsyncSession, shipment: Shipment):
        """创建默认站点"""
        # Pickup stop
        pickup_stop = ShipmentStop(
            tenant_id=shipment.tenant_id,
            shipment_id=shipment.id,
            stop_type=StopType.PICKUP,
            address=shipment.pickup_address,
            coordinates=shipment.pickup_coordinates,
            scheduled_date=shipment.pickup_time,
            sequence="1"
        )

        # Delivery stop
        delivery_stop = ShipmentStop(
            tenant_id=shipment.tenant_id,
            shipment_id=shipment.id,
            stop_type=StopType.DELIVERY,
            address=shipment.delivery_address,
            coordinates=shipment.delivery_coordinates,
            scheduled_date=shipment.delivery_time,
            sequence="2"
        )

        session.add(pickup_stop)
        session.add(delivery_stop)
        await session.commit()

    def _is_valid_status_transition(
        self,
        current_status: ShipmentStatus,
        new_status: ShipmentStatus
    ) -> bool:
        """验证状态转换是否有效"""
        valid_transitions = {
            ShipmentStatus.UNASSIGNED: [ShipmentStatus.ASSIGNED],
            ShipmentStatus.ASSIGNED: [ShipmentStatus.DISPATCHED, ShipmentStatus.UNASSIGNED],
            ShipmentStatus.DISPATCHED: [ShipmentStatus.IN_TRANSIT, ShipmentStatus.ASSIGNED],
            ShipmentStatus.IN_TRANSIT: [ShipmentStatus.AT_PICKUP, ShipmentStatus.DISPATCHED],
            ShipmentStatus.AT_PICKUP: [ShipmentStatus.LOADED, ShipmentStatus.IN_TRANSIT],
            ShipmentStatus.LOADED: [ShipmentStatus.DELIVERED, ShipmentStatus.IN_TRANSIT],
            ShipmentStatus.DELIVERED: []  # Terminal state
        }

        return new_status in valid_transitions.get(current_status, [])

    async def _log_status_change(
        self,
        session: AsyncSession,
        shipment_id: str,
        old_status: ShipmentStatus,
        new_status: ShipmentStatus
    ):
        """记录状态变更日志"""
        # TODO: Implement status change logging
        # This could be implemented as a separate audit log table
        pass

    # Vehicle management methods

    async def create_vehicle(
        self,
        session: AsyncSession,
        tenant_id: str,
        license_plate: str,
        vehicle_type: Optional[str] = None,
        capacity_kg: Optional[float] = None,
        driver_name: Optional[str] = None,
        driver_phone: Optional[str] = None
    ) -> Vehicle:
        """创建车辆"""
        try:
            await set_tenant_context(session, tenant_id)

            # Check if license plate already exists
            stmt = select(Vehicle).where(Vehicle.license_plate == license_plate)
            result = await session.execute(stmt)
            existing_vehicle = result.scalar_one_or_none()

            if existing_vehicle:
                raise LogisticsServiceError("Vehicle with this license plate already exists")

            vehicle = Vehicle(
                tenant_id=uuid.UUID(tenant_id),
                license_plate=license_plate,
                vehicle_type=vehicle_type,
                capacity_kg=capacity_kg,
                driver_name=driver_name,
                driver_phone=driver_phone,
                status="available",
                is_active="1"
            )

            session.add(vehicle)
            await session.commit()
            await session.refresh(vehicle)

            return vehicle

        except Exception as e:
            await session.rollback()
            raise LogisticsServiceError(f"Failed to create vehicle: {str(e)}")

    async def get_available_vehicles(
        self,
        session: AsyncSession,
        tenant_id: str
    ) -> List[Vehicle]:
        """获取可用车辆列表"""
        try:
            await set_tenant_context(session, tenant_id)

            stmt = (
                select(Vehicle)
                .where(Vehicle.status == "available")
                .where(Vehicle.is_active == "1")
                .order_by(Vehicle.license_plate)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            raise LogisticsServiceError(f"Failed to get available vehicles: {str(e)}")

    async def update_vehicle_location(
        self,
        session: AsyncSession,
        tenant_id: str,
        vehicle_id: str,
        coordinates: List[float]
    ) -> Vehicle:
        """更新车辆位置"""
        try:
            await set_tenant_context(session, tenant_id)

            stmt = select(Vehicle).where(Vehicle.id == uuid.UUID(vehicle_id))
            result = await session.execute(stmt)
            vehicle = result.scalar_one_or_none()

            if not vehicle:
                raise LogisticsServiceError("Vehicle not found")

            vehicle.current_coordinates = coordinates
            vehicle.last_update_time = datetime.utcnow()

            await session.commit()
            await session.refresh(vehicle)

            return vehicle

        except Exception as e:
            await session.rollback()
            raise LogisticsServiceError(f"Failed to update vehicle location: {str(e)}")


# Global logistics service instance
def get_logistics_service() -> LogisticsService:
    """获取物流服务实例"""
    return LogisticsService()