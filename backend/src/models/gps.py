from sqlalchemy import Column, String, DECIMAL, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class GPSSource(enum.Enum):
    """GPS数据来源"""
    G7_API = "g7_api"
    DRIVER_APP = "driver_app"
    MANUAL = "manual"


class GPSLocation(BaseModel):
    """GPS位置数据模型"""
    __tablename__ = "gps_locations"

    # 关联的运单和车辆
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True)

    # 位置信息
    latitude = Column(DECIMAL(10, 8), nullable=False)  # 纬度，精确到8位小数
    longitude = Column(DECIMAL(11, 8), nullable=False)  # 经度，精确到8位小数
    altitude = Column(DECIMAL(8, 2))  # 海拔高度（米）
    accuracy = Column(DECIMAL(6, 2))  # 精度（米）

    # 时间戳
    gps_time = Column(DateTime(timezone=True), nullable=False)  # GPS设备时间
    server_time = Column(DateTime(timezone=True), server_default=func.now())  # 服务器接收时间

    # 运动信息
    speed = Column(DECIMAL(5, 2))  # 速度（km/h）
    heading = Column(DECIMAL(5, 2))  # 方向角（度，0-360）

    # 数据来源
    source = Column(String(20), default=GPSSource.G7_API.value)  # 数据来源
    device_id = Column(String(50))  # 设备ID
    raw_data = Column(JSON)  # 原始GPS数据

    # 地址信息（可选，通过逆地理编码获得）
    address = Column(Text)
    city = Column(String(100))
    district = Column(String(100))

    # 状态标识
    is_valid = Column(String(1), default="1")  # 数据是否有效
    is_real_time = Column(String(1), default="1")  # 是否实时数据

    # 关联关系
    shipment = relationship("Shipment", back_populates="gps_tracks")
    vehicle = relationship("Vehicle", back_populates="gps_locations")

    def __repr__(self):
        return f"<GPSLocation(lat={self.latitude}, lng={self.longitude}, time={self.gps_time})>"


class RoutePoint(BaseModel):
    """路线关键点模型"""
    __tablename__ = "route_points"

    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)

    # 点信息
    point_type = Column(String(20), nullable=False)  # start, waypoint, end, checkpoint
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    name = Column(String(200))  # 点名称
    address = Column(Text)

    # 时间信息
    planned_time = Column(DateTime(timezone=True))  # 计划到达时间
    actual_time = Column(DateTime(timezone=True))   # 实际到达时间

    # 序号
    sequence = Column(String(10), nullable=False)  # 使用字符串存储数字

    # 状态
    status = Column(String(20), default="pending")  # pending, reached, passed

    # 关联关系
    shipment = relationship("Shipment")

    def __repr__(self):
        return f"<RoutePoint(type='{self.point_type}', name='{self.name}')>"


class Geofence(BaseModel):
    """地理围栏模型"""
    __tablename__ = "geofences"

    name = Column(String(200), nullable=False)
    description = Column(Text)

    # 围栏类型
    fence_type = Column(String(20), default="circle")  # circle, polygon

    # 中心点（用于圆形围栏）
    center_latitude = Column(DECIMAL(10, 8))
    center_longitude = Column(DECIMAL(11, 8))
    radius_meters = Column(DECIMAL(8, 2))  # 半径（米）

    # 多边形数据（用于多边形围栏）
    polygon_data = Column(JSON)  # 存储多边形顶点坐标

    # 状态
    is_active = Column(String(1), default="1")

    def __repr__(self):
        return f"<Geofence(name='{self.name}', type='{self.fence_type}')>"