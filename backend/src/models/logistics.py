from sqlalchemy import Column, String, Enum, Text, DECIMAL, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel


class ShipmentStatus(enum.Enum):
    """运单状态枚举 - 对应前端 LoadStatus"""
    UNASSIGNED = "unassigned"
    ASSIGNED = "assigned"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in-transit"
    AT_PICKUP = "at-pickup"
    LOADED = "loaded"
    DELIVERED = "delivered"


class StopType(enum.Enum):
    """站点类型枚举"""
    PICKUP = "pickup"
    DELIVERY = "delivery"


class Shipment(BaseModel):
    """运单模型 - 对应前端 Load 接口"""
    __tablename__ = "shipments"

    # 业务编号 - 对应前端 Load.id
    shipment_number = Column(String(50), nullable=False, unique=True, index=True)

    # 地址信息 - 对应前端 Load.origin/destination
    pickup_address = Column(Text, nullable=False)
    delivery_address = Column(Text, nullable=False)

    # 状态 - 对应前端 Load.status
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.UNASSIGNED, index=True)

    # 客户信息 - 对应前端 Load.customer/mode/equipment等
    customer_name = Column(String(200), nullable=False)
    transport_mode = Column(String(100))  # 对应前端 Load.mode
    equipment_type = Column(String(100))  # 对应前端 Load.equipment

    # 货物信息 - 对应前端 Load.weight/commodity等
    weight_kg = Column(DECIMAL(10, 2))  # 对应前端 Load.weight (需格式转换)
    commodity_type = Column(String(200))  # 对应前端 Load.commodity
    packing_type = Column(String(100))  # 对应前端 Load.packingType

    # 坐标信息 - 对应前端 Load.pickupCoords/deliveryCoords
    pickup_coordinates = Column(JSON)  # [lng, lat] 格式
    delivery_coordinates = Column(JSON)  # [lng, lat] 格式

    # 备注信息 - 对应前端 Load.notes
    notes = Column(Text)

    # 标签 - 对应前端 Load.badges
    badges = Column(ARRAY(String))

    # 时间信息
    pickup_time = Column(DateTime(timezone=True))
    delivery_time = Column(DateTime(timezone=True))
    estimated_delivery = Column(DateTime(timezone=True))

    # 关联关系
    stops = relationship("ShipmentStop", back_populates="shipment", cascade="all, delete-orphan")
    gps_tracks = relationship("GPSLocation", back_populates="shipment")
    ai_interactions = relationship("AIInteraction", back_populates="shipment")

    def __repr__(self):
        return f"<Shipment(number='{self.shipment_number}', status='{self.status}')>"


class ShipmentStop(BaseModel):
    """运单站点模型 - 对应前端 Stop 接口"""
    __tablename__ = "shipment_stops"

    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)

    # 站点信息 - 对应前端 Stop 字段
    stop_type = Column(Enum(StopType), nullable=False)  # pickup/delivery
    address = Column(Text, nullable=False)
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(String(20))

    # 时间窗口 - 对应前端 Stop.date/timeWindow
    scheduled_date = Column(DateTime(timezone=True))
    time_window_start = Column(String(20))  # 例如: "09:00"
    time_window_end = Column(String(20))    # 例如: "17:00"

    # 坐标 - 对应前端 Stop.coordinates
    coordinates = Column(JSON)  # [lng, lat] 格式

    # 实际到达和离开时间
    actual_arrival = Column(DateTime(timezone=True))
    actual_departure = Column(DateTime(timezone=True))

    # 站点状态
    status = Column(String(50), default="pending")  # pending, arrived, completed

    # 序号
    sequence = Column(String(10), default="1")  # 使用字符串存储数字

    # 关联关系
    shipment = relationship("Shipment", back_populates="stops")

    def __repr__(self):
        return f"<ShipmentStop(type='{self.stop_type}', address='{self.address}')>"


class Vehicle(BaseModel):
    """车辆模型"""
    __tablename__ = "vehicles"

    # 车辆信息
    license_plate = Column(String(20), nullable=False, unique=True, index=True)
    vehicle_type = Column(String(50))  # 车型
    capacity_kg = Column(DECIMAL(10, 2))  # 载重
    driver_name = Column(String(100))
    driver_phone = Column(String(20))

    # 状态
    status = Column(String(50), default="available")  # available, busy, maintenance
    is_active = Column(String(1), default="1")  # 使用字符串存储布尔值

    # 当前位置
    current_coordinates = Column(JSON)  # [lng, lat]
    last_update_time = Column(DateTime(timezone=True))

    # 关联关系
    gps_locations = relationship("GPSLocation", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle(plate='{self.license_plate}', type='{self.vehicle_type}')>"