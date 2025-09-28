#!/usr/bin/env python3
"""
数据库优化模块
专门处理GPS数据的高效批量写入和查询优化
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from contextlib import asynccontextmanager

import asyncpg
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text, Index, func
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class GPSBatchData:
    """GPS批量数据结构"""
    vehicle_id: str
    latitude: float
    longitude: float
    speed: float
    direction: float
    timestamp: datetime
    accuracy: float = 5.0

class DatabaseConfig:
    """数据库配置和优化参数"""

    # 连接池配置
    POOL_SIZE = 20
    MAX_OVERFLOW = 30
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600

    # 批量处理配置
    BATCH_SIZE = 500
    MAX_BATCH_SIZE = 2000
    FLUSH_INTERVAL = 3.0  # 秒

    # 分区配置
    PARTITION_INTERVAL = 'day'  # 按天分区
    PARTITION_RETENTION_DAYS = 30  # 保留30天数据

    # 索引配置
    INDEX_CONCURRENTLY = True

class AsyncBatchProcessor:
    """异步批量处理器"""

    def __init__(self, engine, batch_size: int = 500, flush_interval: float = 3.0):
        self.engine = engine
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # 批量缓冲区
        self.batch_buffer: List[Dict[str, Any]] = []
        self.lock = asyncio.Lock()

        # 统计信息
        self.total_processed = 0
        self.batch_count = 0
        self.last_flush_time = time.time()
        self.processing_times: List[float] = []

        # 后台任务
        self.flush_task = None
        self.running = True

    async def start(self):
        """启动后台刷新任务"""
        self.flush_task = asyncio.create_task(self._background_flush())
        logger.info("Batch processor started")

    async def stop(self):
        """停止处理器并刷新剩余数据"""
        self.running = False

        if self.flush_task:
            self.flush_task.cancel()

        # 最后刷新一次
        await self._flush_batch()
        logger.info(f"Batch processor stopped. Total processed: {self.total_processed}")

    async def add_gps_data(self, gps_data: GPSBatchData):
        """添加GPS数据到批处理队列"""
        async with self.lock:
            self.batch_buffer.append({
                'vehicle_id': gps_data.vehicle_id,
                'latitude': gps_data.latitude,
                'longitude': gps_data.longitude,
                'speed': gps_data.speed,
                'direction': gps_data.direction,
                'timestamp': gps_data.timestamp,
                'accuracy': gps_data.accuracy,
                'geom': f'POINT({gps_data.longitude} {gps_data.latitude})'
            })

            # 如果缓冲区满了，立即刷新
            if len(self.batch_buffer) >= self.batch_size:
                await self._flush_batch()

    async def _background_flush(self):
        """后台定期刷新任务"""
        while self.running:
            try:
                await asyncio.sleep(self.flush_interval)

                current_time = time.time()
                if (current_time - self.last_flush_time >= self.flush_interval and
                    self.batch_buffer):
                    await self._flush_batch()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background flush error: {e}")

    async def _flush_batch(self):
        """刷新批处理缓冲区"""
        if not self.batch_buffer:
            return

        start_time = time.time()
        batch_data = self.batch_buffer.copy()
        self.batch_buffer.clear()

        try:
            await self._execute_batch_insert(batch_data)

            # 更新统计信息
            process_time = time.time() - start_time
            self.processing_times.append(process_time)
            self.total_processed += len(batch_data)
            self.batch_count += 1
            self.last_flush_time = time.time()

            # 保持处理时间历史不超过100条
            if len(self.processing_times) > 100:
                self.processing_times = self.processing_times[-100:]

            logger.debug(f"Flushed {len(batch_data)} records in {process_time:.3f}s")

        except Exception as e:
            logger.error(f"Batch flush failed: {e}")
            # 可以选择重试或者记录到失败队列
            raise

    async def _execute_batch_insert(self, batch_data: List[Dict[str, Any]]):
        """执行批量插入"""
        if not batch_data:
            return

        async with AsyncSession(self.engine) as session:
            try:
                # 使用 PostgreSQL 的 COPY 或者 INSERT ... ON CONFLICT
                # 这里使用 INSERT ... ON CONFLICT DO UPDATE 实现高效的 upsert

                stmt = text("""
                    INSERT INTO gps_locations_partitioned
                    (vehicle_id, latitude, longitude, speed, direction, timestamp, accuracy, geom)
                    VALUES (:vehicle_id, :latitude, :longitude, :speed, :direction, :timestamp, :accuracy, ST_GeomFromText(:geom, 4326))
                    ON CONFLICT (vehicle_id, timestamp)
                    DO UPDATE SET
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        speed = EXCLUDED.speed,
                        direction = EXCLUDED.direction,
                        accuracy = EXCLUDED.accuracy,
                        geom = EXCLUDED.geom
                """)

                await session.execute(stmt, batch_data)
                await session.commit()

            except Exception as e:
                await session.rollback()
                raise e

    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        avg_process_time = (np.mean(self.processing_times)
                          if self.processing_times else 0)

        return {
            'total_processed': self.total_processed,
            'batch_count': self.batch_count,
            'buffer_size': len(self.batch_buffer),
            'avg_processing_time': round(avg_process_time, 3),
            'processing_rate': (self.total_processed /
                              (time.time() - self.last_flush_time + 1)),
        }

class PostgreSQLOptimizer:
    """PostgreSQL数据库优化器"""

    def __init__(self, engine):
        self.engine = engine

    async def create_optimized_tables(self):
        """创建优化的表结构"""

        # 主GPS数据表（分区表）
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS gps_locations_partitioned (
            vehicle_id VARCHAR(50) NOT NULL,
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            speed DOUBLE PRECISION DEFAULT 0,
            direction DOUBLE PRECISION DEFAULT 0,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            accuracy DOUBLE PRECISION DEFAULT 5,
            geom GEOMETRY(POINT, 4326),
            CONSTRAINT pk_gps_locations PRIMARY KEY (vehicle_id, timestamp)
        ) PARTITION BY RANGE (timestamp);
        """

        # 创建索引
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_gps_vehicle_time ON gps_locations_partitioned (vehicle_id, timestamp DESC);",
            "CREATE INDEX IF NOT EXISTS idx_gps_timestamp ON gps_locations_partitioned (timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_gps_geom ON gps_locations_partitioned USING GIST (geom);",
            "CREATE INDEX IF NOT EXISTS idx_gps_speed ON gps_locations_partitioned (speed) WHERE speed > 0;",
        ]

        async with self.engine.begin() as conn:
            await conn.execute(text(create_table_sql))

            for index_sql in indexes_sql:
                try:
                    await conn.execute(text(index_sql))
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")

    async def create_daily_partitions(self, days_ahead: int = 7):
        """创建未来几天的分区"""
        base_date = datetime.now().date()

        async with self.engine.begin() as conn:
            for i in range(-1, days_ahead + 1):  # 包括昨天到未来几天
                partition_date = base_date + timedelta(days=i)
                next_date = partition_date + timedelta(days=1)

                partition_name = f"gps_locations_{partition_date.strftime('%Y%m%d')}"

                create_partition_sql = f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF gps_locations_partitioned
                FOR VALUES FROM ('{partition_date}') TO ('{next_date}');
                """

                try:
                    await conn.execute(text(create_partition_sql))
                    logger.debug(f"Created partition: {partition_name}")
                except Exception as e:
                    logger.warning(f"Partition creation warning for {partition_name}: {e}")

    async def cleanup_old_partitions(self, retention_days: int = 30):
        """清理旧的分区数据"""
        cutoff_date = datetime.now().date() - timedelta(days=retention_days)

        # 查找需要删除的分区
        find_partitions_sql = f"""
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE tablename LIKE 'gps_locations_%'
        AND tablename < 'gps_locations_{cutoff_date.strftime('%Y%m%d')}'
        ORDER BY tablename;
        """

        async with self.engine.begin() as conn:
            result = await conn.execute(text(find_partitions_sql))
            partitions_to_drop = result.fetchall()

            for partition in partitions_to_drop:
                table_name = partition[1]
                drop_sql = f"DROP TABLE IF EXISTS {table_name};"

                try:
                    await conn.execute(text(drop_sql))
                    logger.info(f"Dropped old partition: {table_name}")
                except Exception as e:
                    logger.error(f"Failed to drop partition {table_name}: {e}")

    async def optimize_database(self):
        """执行数据库优化操作"""
        optimize_sqls = [
            "VACUUM ANALYZE gps_locations_partitioned;",
            "REINDEX TABLE gps_locations_partitioned;",
            "UPDATE pg_stat_statements_reset();",  # 重置查询统计
        ]

        async with self.engine.begin() as conn:
            for sql in optimize_sqls:
                try:
                    await conn.execute(text(sql))
                    logger.info(f"Executed optimization: {sql}")
                except Exception as e:
                    logger.warning(f"Optimization warning: {e}")

class GPSQueryOptimizer:
    """GPS查询优化器"""

    def __init__(self, engine):
        self.engine = engine

    async def get_vehicle_track(self, vehicle_id: str,
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None,
                              limit: int = 1000) -> List[Dict[str, Any]]:
        """优化的车辆轨迹查询"""

        if not start_time:
            start_time = datetime.now() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now()

        query_sql = """
        SELECT vehicle_id, latitude, longitude, speed, direction, timestamp, accuracy
        FROM gps_locations_partitioned
        WHERE vehicle_id = :vehicle_id
        AND timestamp BETWEEN :start_time AND :end_time
        ORDER BY timestamp DESC
        LIMIT :limit;
        """

        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                text(query_sql),
                {
                    'vehicle_id': vehicle_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    'limit': limit
                }
            )

            return [dict(row._mapping) for row in result]

    async def get_vehicles_in_area(self,
                                 center_lat: float,
                                 center_lng: float,
                                 radius_meters: float = 1000,
                                 time_window_minutes: int = 30) -> List[Dict[str, Any]]:
        """获取指定区域内的车辆"""

        since_time = datetime.now() - timedelta(minutes=time_window_minutes)

        # 使用PostGIS进行地理查询
        query_sql = """
        WITH recent_positions AS (
            SELECT DISTINCT ON (vehicle_id)
                vehicle_id, latitude, longitude, speed, direction, timestamp, accuracy,
                ST_Distance(
                    geom,
                    ST_SetSRID(ST_MakePoint(:center_lng, :center_lat), 4326)
                ) as distance_meters
            FROM gps_locations_partitioned
            WHERE timestamp >= :since_time
            AND ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(:center_lng, :center_lat), 4326)::geography,
                :radius_meters
            )
            ORDER BY vehicle_id, timestamp DESC
        )
        SELECT * FROM recent_positions
        WHERE distance_meters <= :radius_meters
        ORDER BY distance_meters;
        """

        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                text(query_sql),
                {
                    'center_lat': center_lat,
                    'center_lng': center_lng,
                    'radius_meters': radius_meters,
                    'since_time': since_time
                }
            )

            return [dict(row._mapping) for row in result]

    async def get_vehicle_statistics(self,
                                   vehicle_ids: List[str],
                                   time_window_hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """批量获取车辆统计信息"""

        since_time = datetime.now() - timedelta(hours=time_window_hours)

        query_sql = """
        SELECT
            vehicle_id,
            COUNT(*) as point_count,
            AVG(speed) as avg_speed,
            MAX(speed) as max_speed,
            MIN(timestamp) as first_update,
            MAX(timestamp) as last_update,
            ST_Distance(
                ST_MakePoint(MIN(longitude), MIN(latitude)),
                ST_MakePoint(MAX(longitude), MAX(latitude))
            )::geography / 1000 as distance_km
        FROM gps_locations_partitioned
        WHERE vehicle_id = ANY(:vehicle_ids)
        AND timestamp >= :since_time
        GROUP BY vehicle_id;
        """

        async with AsyncSession(self.engine) as session:
            result = await session.execute(
                text(query_sql),
                {
                    'vehicle_ids': vehicle_ids,
                    'since_time': since_time
                }
            )

            stats = {}
            for row in result:
                stats[row.vehicle_id] = {
                    'point_count': row.point_count,
                    'avg_speed': float(row.avg_speed) if row.avg_speed else 0,
                    'max_speed': float(row.max_speed) if row.max_speed else 0,
                    'first_update': row.first_update,
                    'last_update': row.last_update,
                    'distance_km': float(row.distance_km) if row.distance_km else 0
                }

            return stats

class DatabaseManager:
    """数据库管理器，整合所有优化功能"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.batch_processor = None
        self.optimizer = None
        self.query_optimizer = None

    async def initialize(self):
        """初始化数据库连接和优化器"""
        self.engine = create_async_engine(
            self.database_url,
            pool_size=DatabaseConfig.POOL_SIZE,
            max_overflow=DatabaseConfig.MAX_OVERFLOW,
            pool_timeout=DatabaseConfig.POOL_TIMEOUT,
            pool_recycle=DatabaseConfig.POOL_RECYCLE,
            pool_pre_ping=True,
            echo=False
        )

        self.batch_processor = AsyncBatchProcessor(
            self.engine,
            batch_size=DatabaseConfig.BATCH_SIZE,
            flush_interval=DatabaseConfig.FLUSH_INTERVAL
        )

        self.optimizer = PostgreSQLOptimizer(self.engine)
        self.query_optimizer = GPSQueryOptimizer(self.engine)

        # 创建表和分区
        await self.optimizer.create_optimized_tables()
        await self.optimizer.create_daily_partitions()

        # 启动批处理器
        await self.batch_processor.start()

        logger.info("Database manager initialized successfully")

    async def close(self):
        """关闭数据库连接"""
        if self.batch_processor:
            await self.batch_processor.stop()

        if self.engine:
            await self.engine.dispose()

        logger.info("Database manager closed")

    async def add_gps_data(self, gps_data: GPSBatchData):
        """添加GPS数据"""
        if self.batch_processor:
            await self.batch_processor.add_gps_data(gps_data)

    async def maintenance_task(self):
        """数据库维护任务"""
        while True:
            try:
                # 每天执行一次维护
                await asyncio.sleep(86400)  # 24小时

                # 创建新分区
                await self.optimizer.create_daily_partitions()

                # 清理旧分区
                await self.optimizer.cleanup_old_partitions()

                # 数据库优化
                await self.optimizer.optimize_database()

                logger.info("Daily maintenance completed")

            except Exception as e:
                logger.error(f"Maintenance task error: {e}")

# 使用示例
async def example_usage():
    """使用示例"""
    DATABASE_URL = "postgresql+asyncpg://user:password@localhost/gps_db"

    # 创建数据库管理器
    db_manager = DatabaseManager(DATABASE_URL)
    await db_manager.initialize()

    try:
        # 添加GPS数据
        gps_data = GPSBatchData(
            vehicle_id="vehicle_001",
            latitude=39.9042,
            longitude=116.4074,
            speed=60.5,
            direction=270,
            timestamp=datetime.now()
        )

        await db_manager.add_gps_data(gps_data)

        # 查询车辆轨迹
        track = await db_manager.query_optimizer.get_vehicle_track("vehicle_001")
        print(f"Vehicle track: {len(track)} points")

        # 获取统计信息
        stats = db_manager.batch_processor.get_stats()
        print(f"Processing stats: {stats}")

    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(example_usage())