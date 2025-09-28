"""
GPS追踪和Server-Sent Events API端点
支持实时GPS追踪、位置记录、路线分析等功能
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from services.gps_service import GPSService, get_gps_service, GPSServiceError, LocationPoint, TrackingFilter
from api.auth import get_current_user
from models.users import User
from models.gps import GPSSource


# Pydantic models for request/response
class RecordLocationRequest(BaseModel):
    """记录位置请求模型"""
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    altitude: Optional[float] = Field(None, description="海拔高度")
    accuracy: Optional[float] = Field(None, description="精度(米)")
    speed: Optional[float] = Field(None, description="速度(km/h)")
    heading: Optional[float] = Field(None, description="方向角(度)")
    timestamp: Optional[datetime] = Field(None, description="GPS时间戳")
    shipment_id: Optional[str] = Field(None, description="关联运单ID")
    vehicle_id: Optional[str] = Field(None, description="关联车辆ID")
    device_id: Optional[str] = Field(None, description="设备ID")
    address: Optional[str] = Field(None, description="地址信息")


class LocationResponse(BaseModel):
    """位置响应模型"""
    id: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: datetime
    address: Optional[str] = None
    shipment_id: Optional[str] = None
    vehicle_id: Optional[str] = None


class TrackingHistoryResponse(BaseModel):
    """追踪历史响应模型"""
    points: List[LocationResponse]
    total_points: int
    time_range: Dict[str, str]


class RouteAnalysisResponse(BaseModel):
    """路线分析响应模型"""
    shipment_id: str
    total_distance_km: float = Field(description="总距离(公里)")
    total_duration_minutes: int = Field(description="总时长(分钟)")
    average_speed_kmh: float = Field(description="平均速度(km/h)")
    max_speed_kmh: float = Field(description="最高速度(km/h)")
    stop_count: int = Field(description="停车次数")
    stop_duration_minutes: int = Field(description="停车总时长(分钟)")
    analysis_period: Dict[str, str]


class GeofenceRequest(BaseModel):
    """创建地理围栏请求模型"""
    name: str = Field(..., description="围栏名称")
    description: Optional[str] = Field(None, description="描述")
    center_latitude: float = Field(..., description="中心点纬度")
    center_longitude: float = Field(..., description="中心点经度")
    radius_meters: float = Field(..., description="半径(米)")


class GeofenceResponse(BaseModel):
    """地理围栏响应模型"""
    id: str
    name: str
    description: Optional[str] = None
    center_latitude: float
    center_longitude: float
    radius_meters: float
    is_active: bool
    created_at: datetime


# 创建路由器
router = APIRouter()


@router.post("/locations", response_model=LocationResponse)
async def record_location(
    request: RecordLocationRequest,
    current_user: User = Depends(get_current_user),
    gps_service: GPSService = Depends(get_gps_service),
    session: AsyncSession = Depends(get_session)
):
    """
    记录GPS位置数据
    """
    try:
        tenant_id = str(current_user.tenant_id)

        # 创建位置点
        location = LocationPoint(
            latitude=request.latitude,
            longitude=request.longitude,
            altitude=request.altitude,
            accuracy=request.accuracy,
            speed=request.speed,
            heading=request.heading,
            timestamp=request.timestamp or datetime.utcnow(),
            address=request.address
        )

        # 记录位置
        gps_location = await gps_service.record_location(
            session=session,
            tenant_id=tenant_id,
            location=location,
            shipment_id=request.shipment_id,
            vehicle_id=request.vehicle_id,
            source=GPSSource.DRIVER_APP,
            device_id=request.device_id
        )

        return LocationResponse(
            id=str(gps_location.id),
            latitude=float(gps_location.latitude),
            longitude=float(gps_location.longitude),
            altitude=float(gps_location.altitude) if gps_location.altitude else None,
            accuracy=float(gps_location.accuracy) if gps_location.accuracy else None,
            speed=float(gps_location.speed) if gps_location.speed else None,
            heading=float(gps_location.heading) if gps_location.heading else None,
            timestamp=gps_location.gps_time,
            address=gps_location.address,
            shipment_id=str(gps_location.shipment_id) if gps_location.shipment_id else None,
            vehicle_id=str(gps_location.vehicle_id) if gps_location.vehicle_id else None
        )

    except GPSServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GPS service error: {str(e)}"
        )


@router.get("/locations/current")
async def get_current_location(
    shipment_id: Optional[str] = Query(None, description="运单ID"),
    vehicle_id: Optional[str] = Query(None, description="车辆ID"),
    current_user: User = Depends(get_current_user),
    gps_service: GPSService = Depends(get_gps_service),
    session: AsyncSession = Depends(get_session)
):
    """
    获取当前位置
    """
    try:
        if not shipment_id and not vehicle_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either shipment_id or vehicle_id"
            )

        tenant_id = str(current_user.tenant_id)

        location = await gps_service.get_current_location(
            session=session,
            tenant_id=tenant_id,
            shipment_id=shipment_id,
            vehicle_id=vehicle_id
        )

        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No location data found"
            )

        return LocationResponse(
            id=str(location.id),
            latitude=float(location.latitude),
            longitude=float(location.longitude),
            altitude=float(location.altitude) if location.altitude else None,
            accuracy=float(location.accuracy) if location.accuracy else None,
            speed=float(location.speed) if location.speed else None,
            heading=float(location.heading) if location.heading else None,
            timestamp=location.gps_time,
            address=location.address,
            shipment_id=str(location.shipment_id) if location.shipment_id else None,
            vehicle_id=str(location.vehicle_id) if location.vehicle_id else None
        )

    except GPSServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GPS service error: {str(e)}"
        )


@router.get("/tracking/history", response_model=TrackingHistoryResponse)
async def get_tracking_history(
    shipment_id: Optional[str] = Query(None, description="运单ID"),
    vehicle_id: Optional[str] = Query(None, description="车辆ID"),
    time_from: Optional[datetime] = Query(None, description="开始时间"),
    time_to: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=5000, description="最大记录数"),
    current_user: User = Depends(get_current_user),
    gps_service: GPSService = Depends(get_gps_service),
    session: AsyncSession = Depends(get_session)
):
    """
    获取GPS追踪历史
    """
    try:
        tenant_id = str(current_user.tenant_id)

        # 构建筛选条件
        filters = TrackingFilter(
            shipment_id=shipment_id,
            vehicle_id=vehicle_id,
            time_from=time_from,
            time_to=time_to
        )

        # 获取追踪历史
        locations = await gps_service.get_tracking_history(
            session=session,
            tenant_id=tenant_id,
            filters=filters,
            limit=limit
        )

        # 转换为响应格式
        points = []
        for loc in locations:
            points.append(LocationResponse(
                id=str(loc.id),
                latitude=float(loc.latitude),
                longitude=float(loc.longitude),
                altitude=float(loc.altitude) if loc.altitude else None,
                accuracy=float(loc.accuracy) if loc.accuracy else None,
                speed=float(loc.speed) if loc.speed else None,
                heading=float(loc.heading) if loc.heading else None,
                timestamp=loc.gps_time,
                address=loc.address,
                shipment_id=str(loc.shipment_id) if loc.shipment_id else None,
                vehicle_id=str(loc.vehicle_id) if loc.vehicle_id else None
            ))

        # 时间范围
        time_range = {}
        if points:
            time_range["from"] = points[0].timestamp.isoformat()
            time_range["to"] = points[-1].timestamp.isoformat()

        return TrackingHistoryResponse(
            points=points,
            total_points=len(points),
            time_range=time_range
        )

    except GPSServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GPS service error: {str(e)}"
        )


@router.get("/tracking/analysis", response_model=RouteAnalysisResponse)
async def analyze_route(
    shipment_id: str = Query(..., description="运单ID"),
    time_from: Optional[datetime] = Query(None, description="分析开始时间"),
    time_to: Optional[datetime] = Query(None, description="分析结束时间"),
    current_user: User = Depends(get_current_user),
    gps_service: GPSService = Depends(get_gps_service),
    session: AsyncSession = Depends(get_session)
):
    """
    分析运单路线数据
    """
    try:
        tenant_id = str(current_user.tenant_id)

        # 如果没有指定时间范围，使用过去24小时
        if not time_from:
            time_from = datetime.utcnow() - timedelta(hours=24)
        if not time_to:
            time_to = datetime.utcnow()

        # 分析路线
        analysis = await gps_service.analyze_route(
            session=session,
            tenant_id=tenant_id,
            shipment_id=shipment_id,
            time_from=time_from,
            time_to=time_to
        )

        return RouteAnalysisResponse(
            shipment_id=shipment_id,
            total_distance_km=analysis.total_distance,
            total_duration_minutes=analysis.total_duration,
            average_speed_kmh=analysis.average_speed,
            max_speed_kmh=analysis.max_speed,
            stop_count=analysis.stop_count,
            stop_duration_minutes=analysis.stop_duration,
            analysis_period={
                "from": time_from.isoformat(),
                "to": time_to.isoformat()
            }
        )

    except GPSServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GPS service error: {str(e)}"
        )


@router.get("/tracking/realtime")
async def stream_realtime_tracking(
    current_user: User = Depends(get_current_user),
    gps_service: GPSService = Depends(get_gps_service),
    session: AsyncSession = Depends(get_session)
):
    """
    实时GPS追踪流 (Server-Sent Events)
    """
    async def generate_tracking_stream():
        tenant_id = str(current_user.tenant_id)

        try:
            while True:
                # 获取实时追踪数据
                tracking_data = await gps_service.get_real_time_tracking(
                    session=session,
                    tenant_id=tenant_id,
                    time_window_minutes=5  # 5分钟窗口
                )

                # 发送SSE格式数据
                data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "tracking_count": len(tracking_data),
                    "tracking_data": tracking_data
                }

                yield f"data: {json.dumps(data, default=str)}\n\n"

                # 等待30秒再次查询
                await asyncio.sleep(30)

        except Exception as e:
            # 发送错误信息
            error_data = {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_tracking_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/geofences", response_model=GeofenceResponse)
async def create_geofence(
    request: GeofenceRequest,
    current_user: User = Depends(get_current_user),
    gps_service: GPSService = Depends(get_gps_service),
    session: AsyncSession = Depends(get_session)
):
    """
    创建地理围栏
    """
    try:
        tenant_id = str(current_user.tenant_id)

        geofence = await gps_service.create_geofence(
            session=session,
            tenant_id=tenant_id,
            name=request.name,
            fence_type="circle",
            center_lat=request.center_latitude,
            center_lng=request.center_longitude,
            radius_meters=request.radius_meters,
            description=request.description
        )

        return GeofenceResponse(
            id=str(geofence.id),
            name=geofence.name,
            description=geofence.description,
            center_latitude=float(geofence.center_latitude),
            center_longitude=float(geofence.center_longitude),
            radius_meters=float(geofence.radius_meters),
            is_active=geofence.is_active == "1",
            created_at=geofence.created_at
        )

    except GPSServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GPS service error: {str(e)}"
        )


@router.post("/geofences/check")
async def check_geofence_violations(
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
    current_user: User = Depends(get_current_user),
    gps_service: GPSService = Depends(get_gps_service),
    session: AsyncSession = Depends(get_session)
):
    """
    检查地理围栏违规
    """
    try:
        tenant_id = str(current_user.tenant_id)

        violations = await gps_service.check_geofence_violation(
            session=session,
            tenant_id=tenant_id,
            latitude=latitude,
            longitude=longitude
        )

        return {
            "check_point": {
                "latitude": latitude,
                "longitude": longitude
            },
            "violations": violations,
            "violation_count": len(violations),
            "checked_at": datetime.utcnow().isoformat()
        }

    except GPSServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GPS service error: {str(e)}"
        )