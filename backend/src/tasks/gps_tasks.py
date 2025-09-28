"""
GPS数据处理Celery任务
处理GPS位置数据的异步任务，包括数据清理、分析、地理围栏检测等
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
import uuid

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func

from core.celery_app import celery_app
from core.database import get_session
from core.security import set_tenant_context
from services.gps_service import GPSService, LocationPoint, GPSServiceError
from models.gps import GPSLocation, Geofence, GPSSource
from models.logistics import Shipment


class AsyncTask(Task):
    """支持异步操作的Celery任务基类"""

    def apply_async(self, args=None, kwargs=None, **options):
        # 确保任务在事件循环中运行
        return super().apply_async(args, kwargs, **options)


@celery_app.task(bind=True, base=AsyncTask, name="tasks.gps_tasks.process_gps_batch")
def process_gps_batch(self, tenant_id: str, gps_data_list: List[Dict[str, Any]]):
    """
    批量处理GPS数据
    用于处理来自G7等外部系统的大批量GPS数据
    """
    async def _process():
        try:
            async with get_session() as session:
                gps_service = GPSService()
                processed_count = 0
                error_count = 0

                for gps_data in gps_data_list:
                    try:
                        # 解析GPS数据
                        location = LocationPoint(
                            latitude=float(gps_data['latitude']),
                            longitude=float(gps_data['longitude']),
                            altitude=gps_data.get('altitude'),
                            speed=gps_data.get('speed'),
                            heading=gps_data.get('heading'),
                            timestamp=datetime.fromisoformat(gps_data['timestamp']),
                            address=gps_data.get('address')
                        )

                        # 记录位置
                        await gps_service.record_location(
                            session=session,
                            tenant_id=tenant_id,
                            location=location,
                            shipment_id=gps_data.get('shipment_id'),
                            vehicle_id=gps_data.get('vehicle_id'),
                            source=GPSSource.G7_API,
                            device_id=gps_data.get('device_id'),
                            raw_data=gps_data
                        )

                        processed_count += 1

                    except Exception as e:
                        error_count += 1
                        print(f"Error processing GPS data: {e}")

                return {
                    "processed_count": processed_count,
                    "error_count": error_count,
                    "total_count": len(gps_data_list)
                }

        except Exception as e:
            self.retry(countdown=60, max_retries=3, exc=e)

    return asyncio.run(_process())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.gps_tasks.cleanup_old_gps_data")
def cleanup_old_gps_data(self, days_to_keep: int = 30):
    """
    清理过期的GPS数据
    默认保留30天的数据
    """
    async def _cleanup():
        try:
            async with get_session() as session:
                # 计算清理截止日期
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

                # 删除过期数据
                stmt = delete(GPSLocation).where(
                    GPSLocation.gps_time < cutoff_date
                )
                result = await session.execute(stmt)
                await session.commit()

                deleted_count = result.rowcount
                print(f"Cleaned up {deleted_count} old GPS records older than {days_to_keep} days")

                return {"deleted_count": deleted_count, "cutoff_date": cutoff_date.isoformat()}

        except Exception as e:
            print(f"Error cleaning up GPS data: {e}")
            return {"error": str(e)}

    return asyncio.run(_cleanup())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.gps_tasks.check_geofence_violations")
def check_geofence_violations(self, tenant_id: str, latitude: float, longitude: float,
                             shipment_id: Optional[str] = None, vehicle_id: Optional[str] = None):
    """
    检查地理围栏违规
    当GPS位置更新时触发此任务检查是否违反地理围栏
    """
    async def _check():
        try:
            async with get_session() as session:
                gps_service = GPSService()

                # 检查围栏违规
                violations = await gps_service.check_geofence_violation(
                    session=session,
                    tenant_id=tenant_id,
                    latitude=latitude,
                    longitude=longitude
                )

                # 如果有违规，触发通知任务
                if violations:
                    from tasks.notification_tasks import send_geofence_alert
                    send_geofence_alert.delay(
                        tenant_id=tenant_id,
                        violations=violations,
                        shipment_id=shipment_id,
                        vehicle_id=vehicle_id,
                        location={"latitude": latitude, "longitude": longitude}
                    )

                return {
                    "violations": violations,
                    "violation_count": len(violations),
                    "location": {"latitude": latitude, "longitude": longitude}
                }

        except Exception as e:
            print(f"Error checking geofence violations: {e}")
            return {"error": str(e)}

    return asyncio.run(_check())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.gps_tasks.analyze_route_performance")
def analyze_route_performance(self, tenant_id: str, shipment_id: str,
                             time_from: Optional[str] = None, time_to: Optional[str] = None):
    """
    分析运单路线性能
    计算距离、速度、停留时间等指标
    """
    async def _analyze():
        try:
            async with get_session() as session:
                gps_service = GPSService()

                # 解析时间参数
                time_from_dt = datetime.fromisoformat(time_from) if time_from else None
                time_to_dt = datetime.fromisoformat(time_to) if time_to else None

                # 分析路线
                analysis = await gps_service.analyze_route(
                    session=session,
                    tenant_id=tenant_id,
                    shipment_id=shipment_id,
                    time_from=time_from_dt,
                    time_to=time_to_dt
                )

                # 检查异常情况并触发警报
                alerts = []
                if analysis.max_speed > 120:  # 超速警报
                    alerts.append({
                        "type": "speeding",
                        "max_speed": analysis.max_speed,
                        "threshold": 120
                    })

                if analysis.stop_duration > 180:  # 长时间停车警报(超过3小时)
                    alerts.append({
                        "type": "long_stop",
                        "stop_duration": analysis.stop_duration,
                        "threshold": 180
                    })

                # 如果有警报，发送通知
                if alerts:
                    from tasks.notification_tasks import send_route_alert
                    send_route_alert.delay(
                        tenant_id=tenant_id,
                        shipment_id=shipment_id,
                        alerts=alerts,
                        analysis_data=analysis.__dict__
                    )

                return {
                    "analysis": analysis.__dict__,
                    "alerts": alerts,
                    "shipment_id": shipment_id
                }

        except Exception as e:
            print(f"Error analyzing route performance: {e}")
            return {"error": str(e)}

    return asyncio.run(_analyze())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.gps_tasks.generate_route_optimization")
def generate_route_optimization(self, tenant_id: str, vehicle_id: str,
                               destination_points: List[Dict[str, Any]]):
    """
    生成路线优化建议
    基于历史GPS数据和交通状况优化路线
    """
    async def _optimize():
        try:
            async with get_session() as session:
                # 获取车辆当前位置
                gps_service = GPSService()
                current_location = await gps_service.get_current_location(
                    session=session,
                    tenant_id=tenant_id,
                    vehicle_id=vehicle_id
                )

                if not current_location:
                    return {"error": "No current location found for vehicle"}

                # 简单的路线优化算法（实际项目中可以集成高德、百度等地图API）
                start_point = {
                    "latitude": float(current_location.latitude),
                    "longitude": float(current_location.longitude)
                }

                # 计算到各点的直线距离（实际应该用路径距离）
                distances = []
                for i, point in enumerate(destination_points):
                    distance = gps_service._calculate_distance(
                        start_point["latitude"], start_point["longitude"],
                        point["latitude"], point["longitude"]
                    )
                    distances.append({"index": i, "distance": distance, "point": point})

                # 按距离排序（简单优化）
                optimized_route = sorted(distances, key=lambda x: x["distance"])

                # 计算总距离和预估时间
                total_distance = sum(d["distance"] for d in optimized_route)
                estimated_time = total_distance / 50 * 60  # 假设平均50km/h，转换为分钟

                return {
                    "vehicle_id": vehicle_id,
                    "start_point": start_point,
                    "optimized_route": optimized_route,
                    "total_distance_km": round(total_distance, 2),
                    "estimated_time_minutes": round(estimated_time, 0),
                    "optimization_time": datetime.utcnow().isoformat()
                }

        except Exception as e:
            print(f"Error generating route optimization: {e}")
            return {"error": str(e)}

    return asyncio.run(_optimize())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.gps_tasks.sync_external_gps")
def sync_external_gps(self, tenant_id: str, sync_hours: int = 1):
    """
    同步外部GPS数据（如G7平台）
    定期从外部系统拉取GPS数据并存储
    """
    async def _sync():
        try:
            # 这里应该调用外部API获取GPS数据
            # 示例：从G7 API获取数据

            # 模拟外部API数据
            external_data = []

            # 实际实现中，这里会调用G7或其他GPS服务商的API
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.get(f"{g7_api_url}/vehicles/locations",
            #                               headers={"Authorization": f"Bearer {g7_token}"})
            #     external_data = response.json()["data"]

            if external_data:
                # 触发批量处理任务
                process_gps_batch.delay(tenant_id, external_data)

            return {
                "sync_time": datetime.utcnow().isoformat(),
                "records_found": len(external_data),
                "sync_hours": sync_hours
            }

        except Exception as e:
            print(f"Error syncing external GPS data: {e}")
            return {"error": str(e)}

    return asyncio.run(_sync())


@celery_app.task(bind=True, base=AsyncTask, name="tasks.gps_tasks.update_shipment_eta")
def update_shipment_eta(self, tenant_id: str, shipment_id: str):
    """
    更新运单预计到达时间(ETA)
    基于当前位置和历史数据计算到达时间
    """
    async def _update_eta():
        try:
            async with get_session() as session:
                await set_tenant_context(session, tenant_id)

                # 获取运单信息
                stmt = select(Shipment).where(Shipment.id == uuid.UUID(shipment_id))
                result = await session.execute(stmt)
                shipment = result.scalar_one_or_none()

                if not shipment:
                    return {"error": "Shipment not found"}

                # 获取当前GPS位置
                gps_service = GPSService()
                current_location = await gps_service.get_current_location(
                    session=session,
                    tenant_id=tenant_id,
                    shipment_id=shipment_id
                )

                if not current_location:
                    return {"error": "No current location found"}

                # 计算到目的地的距离
                if shipment.delivery_coordinates:
                    distance = gps_service._calculate_distance(
                        float(current_location.latitude),
                        float(current_location.longitude),
                        shipment.delivery_coordinates[1],  # 纬度
                        shipment.delivery_coordinates[0]   # 经度
                    )

                    # 基于历史速度计算ETA（简化算法）
                    avg_speed = 50  # 默认50km/h
                    if current_location.speed:
                        avg_speed = max(float(current_location.speed), 30)  # 最低30km/h

                    eta_hours = distance / avg_speed
                    eta = datetime.utcnow() + timedelta(hours=eta_hours)

                    # 更新运单ETA（这里需要在Shipment模型中添加estimated_arrival字段）
                    # shipment.estimated_arrival = eta
                    # await session.commit()

                    return {
                        "shipment_id": shipment_id,
                        "current_location": {
                            "latitude": float(current_location.latitude),
                            "longitude": float(current_location.longitude)
                        },
                        "destination": shipment.delivery_coordinates,
                        "distance_km": round(distance, 2),
                        "estimated_arrival": eta.isoformat(),
                        "calculation_time": datetime.utcnow().isoformat()
                    }

                else:
                    return {"error": "No delivery coordinates found for shipment"}

        except Exception as e:
            print(f"Error updating shipment ETA: {e}")
            return {"error": str(e)}

    return asyncio.run(_update_eta())