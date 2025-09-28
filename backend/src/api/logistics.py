"""
物流运单API端点
支持运单创建、查询、状态更新等功能
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from services.logistics_service import LogisticsService, get_logistics_service, LogisticsServiceError, ShipmentFilter
from api.auth import get_current_user
from models.users import User
from models.logistics import ShipmentStatus


# Pydantic models for request/response
class CreateShipmentRequest(BaseModel):
    """创建运单请求模型"""
    pickup_address: str = Field(..., description="取货地址")
    delivery_address: str = Field(..., description="送货地址")
    customer_name: str = Field(..., description="客户姓名")
    transport_mode: Optional[str] = Field(None, description="运输方式")
    equipment_type: Optional[str] = Field(None, description="设备类型")
    weight_kg: Optional[float] = Field(None, description="重量(公斤)")
    commodity_type: Optional[str] = Field(None, description="商品类型")
    packing_type: Optional[str] = Field(None, description="包装类型")
    pickup_coordinates: Optional[List[float]] = Field(None, description="取货坐标[经度,纬度]")
    delivery_coordinates: Optional[List[float]] = Field(None, description="送货坐标[经度,纬度]")
    notes: Optional[str] = Field(None, description="备注信息")


class CreateShipmentResponse(BaseModel):
    """创建运单响应模型"""
    id: str = Field(description="运单ID")
    shipment_number: str = Field(description="运单号")
    status: str = Field(description="运单状态")
    created_at: datetime = Field(description="创建时间")
    estimated_delivery: Optional[datetime] = Field(None, description="预计送达时间")


class ShipmentItem(BaseModel):
    """运单列表项模型"""
    id: str
    shipment_number: str
    pickup_address: str
    delivery_address: str
    status: str
    customer_name: str
    weight_kg: Optional[float] = None
    created_at: datetime


class ShipmentListResponse(BaseModel):
    """运单列表响应模型"""
    items: List[ShipmentItem]
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    limit: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")


class ShipmentDetailResponse(BaseModel):
    """运单详情响应模型"""
    id: str
    shipment_number: str
    pickup_address: str
    delivery_address: str
    customer_name: str
    status: str
    transport_mode: Optional[str] = None
    equipment_type: Optional[str] = None
    weight_kg: Optional[float] = None
    commodity_type: Optional[str] = None
    packing_type: Optional[str] = None
    pickup_coordinates: Optional[List[float]] = None
    delivery_coordinates: Optional[List[float]] = None
    notes: Optional[str] = None
    created_at: datetime
    pickup_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None


class UpdateStatusRequest(BaseModel):
    """更新状态请求模型"""
    status: str = Field(..., description="新状态")
    notes: Optional[str] = Field(None, description="备注信息")


class UpdateStatusResponse(BaseModel):
    """更新状态响应模型"""
    id: str
    shipment_number: str
    old_status: str
    new_status: str
    updated_at: datetime


# 创建路由器
router = APIRouter()
security = HTTPBearer()


@router.post("/", response_model=CreateShipmentResponse)
async def create_shipment(
    request: CreateShipmentRequest,
    current_user: User = Depends(get_current_user),
    logistics_service: LogisticsService = Depends(get_logistics_service),
    session: AsyncSession = Depends(get_session)
):
    """
    创建新运单
    """
    try:
        tenant_id = str(current_user.tenant_id)

        # 创建运单
        shipment = await logistics_service.create_shipment(
            session=session,
            tenant_id=tenant_id,
            pickup_address=request.pickup_address,
            delivery_address=request.delivery_address,
            customer_name=request.customer_name,
            transport_mode=request.transport_mode,
            equipment_type=request.equipment_type,
            weight_kg=request.weight_kg,
            commodity_type=request.commodity_type,
            packing_type=request.packing_type,
            pickup_coordinates=request.pickup_coordinates,
            delivery_coordinates=request.delivery_coordinates,
            notes=request.notes
        )

        # 计算预计送达时间（简单逻辑，实际可根据距离和路况计算）
        estimated_delivery = None
        if request.pickup_coordinates and request.delivery_coordinates:
            # 简单估算：每小时50公里，加上2小时缓冲
            from datetime import timedelta
            estimated_delivery = datetime.utcnow() + timedelta(hours=4)

        return CreateShipmentResponse(
            id=str(shipment.id),
            shipment_number=shipment.shipment_number,
            status=shipment.status.value,
            created_at=shipment.created_at,
            estimated_delivery=estimated_delivery
        )

    except LogisticsServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logistics service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/", response_model=ShipmentListResponse)
async def get_shipments(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    customer_name: Optional[str] = Query(None, description="客户姓名筛选"),
    search: Optional[str] = Query(None, description="搜索文本"),
    current_user: User = Depends(get_current_user),
    logistics_service: LogisticsService = Depends(get_logistics_service),
    session: AsyncSession = Depends(get_session)
):
    """
    获取运单列表
    """
    try:
        tenant_id = str(current_user.tenant_id)
        offset = (page - 1) * limit

        # 构建筛选条件
        filters = None
        if status_filter or customer_name or search:
            status_list = None
            if status_filter:
                # 支持多状态筛选，用逗号分隔
                status_names = [s.strip() for s in status_filter.split(",")]
                status_list = []
                for status_name in status_names:
                    try:
                        status_list.append(ShipmentStatus(status_name))
                    except ValueError:
                        pass  # 忽略无效状态

            filters = ShipmentFilter(
                status=status_list,
                customer_name=customer_name,
                search_text=search
            )

        # 获取运单列表
        shipments, total_count = await logistics_service.get_shipments(
            session=session,
            tenant_id=tenant_id,
            filters=filters,
            offset=offset,
            limit=limit
        )

        # 转换为响应格式
        items = []
        for shipment in shipments:
            items.append(ShipmentItem(
                id=str(shipment.id),
                shipment_number=shipment.shipment_number,
                pickup_address=shipment.pickup_address,
                delivery_address=shipment.delivery_address,
                status=shipment.status.value,
                customer_name=shipment.customer_name,
                weight_kg=shipment.weight_kg,
                created_at=shipment.created_at
            ))

        # 计算分页信息
        total_pages = (total_count + limit - 1) // limit

        return ShipmentListResponse(
            items=items,
            total=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages
        )

    except LogisticsServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logistics service error: {str(e)}"
        )


@router.get("/{shipment_id}", response_model=ShipmentDetailResponse)
async def get_shipment_detail(
    shipment_id: str,
    current_user: User = Depends(get_current_user),
    logistics_service: LogisticsService = Depends(get_logistics_service),
    session: AsyncSession = Depends(get_session)
):
    """
    获取运单详情
    """
    try:
        tenant_id = str(current_user.tenant_id)

        # 获取运单
        shipment = await logistics_service.get_shipment(
            session=session,
            tenant_id=tenant_id,
            shipment_id=shipment_id
        )

        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )

        return ShipmentDetailResponse(
            id=str(shipment.id),
            shipment_number=shipment.shipment_number,
            pickup_address=shipment.pickup_address,
            delivery_address=shipment.delivery_address,
            customer_name=shipment.customer_name,
            status=shipment.status.value,
            transport_mode=shipment.transport_mode,
            equipment_type=shipment.equipment_type,
            weight_kg=shipment.weight_kg,
            commodity_type=shipment.commodity_type,
            packing_type=shipment.packing_type,
            pickup_coordinates=shipment.pickup_coordinates,
            delivery_coordinates=shipment.delivery_coordinates,
            notes=shipment.notes,
            created_at=shipment.created_at,
            pickup_time=shipment.pickup_time,
            delivery_time=shipment.delivery_time
        )

    except LogisticsServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logistics service error: {str(e)}"
        )


@router.patch("/{shipment_id}/status", response_model=UpdateStatusResponse)
async def update_shipment_status(
    shipment_id: str,
    request: UpdateStatusRequest,
    current_user: User = Depends(get_current_user),
    logistics_service: LogisticsService = Depends(get_logistics_service),
    session: AsyncSession = Depends(get_session)
):
    """
    更新运单状态
    """
    try:
        tenant_id = str(current_user.tenant_id)

        # 验证状态值
        try:
            new_status = ShipmentStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}"
            )

        # 获取当前运单状态
        shipment = await logistics_service.get_shipment(
            session=session,
            tenant_id=tenant_id,
            shipment_id=shipment_id
        )

        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )

        old_status = shipment.status

        # 更新状态
        updated_shipment = await logistics_service.update_shipment_status(
            session=session,
            tenant_id=tenant_id,
            shipment_id=shipment_id,
            new_status=new_status,
            notes=request.notes
        )

        return UpdateStatusResponse(
            id=str(updated_shipment.id),
            shipment_number=updated_shipment.shipment_number,
            old_status=old_status.value,
            new_status=updated_shipment.status.value,
            updated_at=datetime.utcnow()
        )

    except LogisticsServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logistics service error: {str(e)}"
        )


@router.get("/{shipment_id}/route")
async def get_shipment_route(
    shipment_id: str,
    current_user: User = Depends(get_current_user),
    logistics_service: LogisticsService = Depends(get_logistics_service),
    session: AsyncSession = Depends(get_session)
):
    """
    获取运单路线追踪信息
    """
    try:
        tenant_id = str(current_user.tenant_id)

        # 验证运单存在
        shipment = await logistics_service.get_shipment(
            session=session,
            tenant_id=tenant_id,
            shipment_id=shipment_id
        )

        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipment not found"
            )

        # 获取路线数据
        route_data = await logistics_service.get_shipment_route(
            session=session,
            tenant_id=tenant_id,
            shipment_id=shipment_id
        )

        return {
            "shipment_id": shipment_id,
            "shipment_number": shipment.shipment_number,
            "route_points": route_data,
            "total_points": len(route_data)
        }

    except LogisticsServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logistics service error: {str(e)}"
        )


@router.get("/summary/statistics")
async def get_shipment_statistics(
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    logistics_service: LogisticsService = Depends(get_logistics_service),
    session: AsyncSession = Depends(get_session)
):
    """
    获取运单统计信息
    """
    try:
        tenant_id = str(current_user.tenant_id)

        # 转换日期格式
        date_from_dt = datetime.combine(date_from, datetime.min.time()) if date_from else None
        date_to_dt = datetime.combine(date_to, datetime.max.time()) if date_to else None

        # 获取统计摘要
        summary = await logistics_service.get_shipment_summary(
            session=session,
            tenant_id=tenant_id,
            date_from=date_from_dt,
            date_to=date_to_dt
        )

        return {
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None
            },
            "total_shipments": summary.total_count,
            "status_distribution": summary.status_counts,
            "total_weight_kg": summary.total_weight,
            "pending_deliveries": summary.pending_deliveries,
            "completion_rate": (
                (summary.total_count - summary.pending_deliveries) / summary.total_count * 100
                if summary.total_count > 0 else 0
            )
        }

    except LogisticsServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logistics service error: {str(e)}"
        )