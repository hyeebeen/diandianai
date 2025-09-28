#!/usr/bin/env python3
"""
Redis性能优化模块
专门针对GPS数据的高频读写进行优化
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

import redis.asyncio as redis
from redis.asyncio import Redis
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class GPSPoint:
    """轻量级GPS点数据结构"""
    lat: float
    lng: float
    timestamp: float
    speed: float = 0.0
    direction: float = 0.0

class RedisClusterManager:
    """Redis集群管理器，实现数据分片和负载均衡"""

    def __init__(self, redis_configs: List[Dict]):
        self.redis_clients: List[Redis] = []
        self.client_count = len(redis_configs)

        for config in redis_configs:
            client = redis.Redis(**config)
            self.redis_clients.append(client)

    def _get_shard_index(self, key: str) -> int:
        """基于key的hash值确定分片索引"""
        return hash(key) % self.client_count

    def get_client(self, key: str) -> Redis:
        """根据key获取对应的Redis客户端"""
        index = self._get_shard_index(key)
        return self.redis_clients[index]

    async def close_all(self):
        """关闭所有Redis连接"""
        for client in self.redis_clients:
            await client.close()

class OptimizedGPSCache:
    """优化的GPS数据缓存系统"""

    def __init__(self, redis_client: Redis, cluster_manager: Optional[RedisClusterManager] = None):
        self.redis = redis_client
        self.cluster_manager = cluster_manager

        # 缓存配置
        self.vehicle_ttl = 3600  # 车辆数据TTL(秒)
        self.track_ttl = 7200    # 轨迹数据TTL(秒)
        self.batch_size = 50     # 批处理大小

        # 性能监控
        self.write_count = 0
        self.read_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

        # 批量写入缓冲区
        self.write_buffer: Dict[str, List[GPSPoint]] = {}
        self.last_flush = time.time()
        self.flush_interval = 2.0  # 2秒刷新一次

        # 启动后台刷新任务
        self.flush_task = asyncio.create_task(self._background_flush())

    async def _background_flush(self):
        """后台批量刷新任务"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_write_buffer()
            except Exception as e:
                logger.error(f"Background flush error: {e}")

    async def _flush_write_buffer(self):
        """刷新写入缓冲区"""
        if not self.write_buffer:
            return

        # 使用pipeline批量操作
        pipe = self.redis.pipeline()

        for vehicle_id, gps_points in self.write_buffer.items():
            if not gps_points:
                continue

            # 获取对应的Redis客户端（如果使用集群）
            client = (self.cluster_manager.get_client(vehicle_id)
                     if self.cluster_manager else self.redis)

            # 最新位置数据
            latest_point = gps_points[-1]
            vehicle_key = f"v:{vehicle_id}"

            location_data = {
                'lat': latest_point.lat,
                'lng': latest_point.lng,
                'speed': latest_point.speed,
                'dir': latest_point.direction,
                'ts': latest_point.timestamp
            }

            pipe.hset(vehicle_key, mapping=location_data)
            pipe.expire(vehicle_key, self.vehicle_ttl)

            # 地理位置索引
            geo_key = "geo:vehicles"
            pipe.geoadd(geo_key, latest_point.lng, latest_point.lat, vehicle_id)

            # 轨迹数据 - 使用压缩格式
            track_key = f"t:{vehicle_id}"
            for point in gps_points:
                # 使用紧凑的二进制格式存储轨迹点
                track_data = self._compress_gps_point(point)
                pipe.lpush(track_key, track_data)

            # 保持轨迹点数量限制
            pipe.ltrim(track_key, 0, 199)  # 保留最近200个点
            pipe.expire(track_key, self.track_ttl)

        # 执行批量操作
        await pipe.execute()

        # 清空缓冲区
        total_points = sum(len(points) for points in self.write_buffer.values())
        self.write_buffer.clear()
        self.write_count += total_points

        logger.debug(f"Flushed {total_points} GPS points to Redis")

    def _compress_gps_point(self, point: GPSPoint) -> bytes:
        """压缩GPS点数据为二进制格式"""
        # 使用numpy的高效二进制格式
        data = np.array([point.lat, point.lng, point.timestamp,
                        point.speed, point.direction], dtype=np.float32)
        return data.tobytes()

    def _decompress_gps_point(self, data: bytes) -> GPSPoint:
        """解压缩GPS点数据"""
        arr = np.frombuffer(data, dtype=np.float32)
        return GPSPoint(
            lat=float(arr[0]),
            lng=float(arr[1]),
            timestamp=float(arr[2]),
            speed=float(arr[3]),
            direction=float(arr[4])
        )

    async def cache_gps_point(self, vehicle_id: str, gps_point: GPSPoint):
        """缓存单个GPS点（添加到批处理缓冲区）"""
        if vehicle_id not in self.write_buffer:
            self.write_buffer[vehicle_id] = []

        self.write_buffer[vehicle_id].append(gps_point)

        # 如果缓冲区过大，立即刷新
        if len(self.write_buffer[vehicle_id]) >= self.batch_size:
            await self._flush_write_buffer()

    async def get_vehicle_location(self, vehicle_id: str) -> Optional[Dict]:
        """获取车辆当前位置"""
        self.read_count += 1

        client = (self.cluster_manager.get_client(vehicle_id)
                 if self.cluster_manager else self.redis)

        vehicle_key = f"v:{vehicle_id}"
        data = await client.hgetall(vehicle_key)

        if data:
            self.cache_hits += 1
            return {
                'vehicle_id': vehicle_id,
                'latitude': float(data[b'lat']),
                'longitude': float(data[b'lng']),
                'speed': float(data[b'speed']),
                'direction': float(data[b'dir']),
                'timestamp': float(data[b'ts'])
            }

        self.cache_misses += 1
        return None

    async def get_vehicle_track(self, vehicle_id: str, limit: int = 50) -> List[GPSPoint]:
        """获取车辆轨迹"""
        self.read_count += 1

        client = (self.cluster_manager.get_client(vehicle_id)
                 if self.cluster_manager else self.redis)

        track_key = f"t:{vehicle_id}"
        track_data = await client.lrange(track_key, 0, limit - 1)

        if track_data:
            self.cache_hits += 1
            return [self._decompress_gps_point(data) for data in track_data]

        self.cache_misses += 1
        return []

    async def get_nearby_vehicles(self, lat: float, lng: float,
                                radius_km: float = 10) -> List[Tuple[str, float]]:
        """获取附近车辆（返回车辆ID和距离）"""
        geo_key = "geo:vehicles"

        nearby = await self.redis.georadius(
            geo_key, lng, lat, radius_km,
            unit='km', withdist=True, sort='ASC'
        )

        return [(item[0].decode(), float(item[1])) for item in nearby]

    async def get_vehicle_stats(self, vehicle_ids: List[str]) -> Dict[str, Dict]:
        """批量获取多个车辆的状态"""
        if not vehicle_ids:
            return {}

        # 使用pipeline批量查询
        pipe = self.redis.pipeline()

        for vehicle_id in vehicle_ids:
            vehicle_key = f"v:{vehicle_id}"
            pipe.hgetall(vehicle_key)

        results = await pipe.execute()

        stats = {}
        for i, vehicle_id in enumerate(vehicle_ids):
            data = results[i]
            if data:
                stats[vehicle_id] = {
                    'latitude': float(data[b'lat']),
                    'longitude': float(data[b'lng']),
                    'speed': float(data[b'speed']),
                    'direction': float(data[b'dir']),
                    'timestamp': float(data[b'ts']),
                    'last_update': datetime.fromtimestamp(float(data[b'ts']))
                }

        return stats

    def get_performance_stats(self) -> Dict:
        """获取缓存性能统计"""
        total_reads = self.read_count
        hit_rate = (self.cache_hits / total_reads * 100) if total_reads > 0 else 0

        return {
            'write_count': self.write_count,
            'read_count': self.read_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate_percent': round(hit_rate, 2),
            'buffer_size': sum(len(points) for points in self.write_buffer.values())
        }

    async def cleanup(self):
        """清理资源"""
        # 最后刷新一次缓冲区
        await self._flush_write_buffer()

        # 取消后台任务
        if hasattr(self, 'flush_task'):
            self.flush_task.cancel()

        # 关闭Redis连接
        if self.cluster_manager:
            await self.cluster_manager.close_all()
        else:
            await self.redis.close()

class RedisMemoryOptimizer:
    """Redis内存优化器"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def optimize_memory_usage(self):
        """优化内存使用"""
        try:
            # 执行内存整理
            await self.redis.memory_purge()

            # 获取内存使用统计
            memory_info = await self.redis.memory_stats()

            # 清理过期键
            await self.redis.flushdb(asynchronous=True)

            logger.info(f"Memory optimization completed. Stats: {memory_info}")

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")

    async def get_memory_usage(self) -> Dict:
        """获取内存使用情况"""
        try:
            info = await self.redis.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'memory_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0),
            }
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {}

class RedisConnectionPool:
    """优化的Redis连接池"""

    def __init__(self, redis_configs: List[Dict], pool_size: int = 20):
        self.pools = []
        self.current_pool = 0

        for config in redis_configs:
            pool = redis.ConnectionPool(
                **config,
                max_connections=pool_size,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            self.pools.append(pool)

    def get_redis_client(self) -> Redis:
        """获取Redis客户端（轮询方式）"""
        pool = self.pools[self.current_pool]
        self.current_pool = (self.current_pool + 1) % len(self.pools)
        return Redis(connection_pool=pool)

    async def close_all_pools(self):
        """关闭所有连接池"""
        for pool in self.pools:
            await pool.disconnect()

# 使用示例和配置
REDIS_CLUSTER_CONFIG = [
    {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'decode_responses': False,
        'socket_keepalive': True,
    },
    # 可以添加更多Redis实例进行分片
    # {
    #     'host': 'localhost',
    #     'port': 6380,
    #     'db': 0,
    #     'decode_responses': False,
    #     'socket_keepalive': True,
    # },
]

async def create_optimized_cache(use_cluster: bool = False) -> OptimizedGPSCache:
    """创建优化的GPS缓存实例"""
    if use_cluster and len(REDIS_CLUSTER_CONFIG) > 1:
        cluster_manager = RedisClusterManager(REDIS_CLUSTER_CONFIG)
        redis_client = cluster_manager.redis_clients[0]  # 主客户端
        return OptimizedGPSCache(redis_client, cluster_manager)
    else:
        redis_client = redis.Redis(**REDIS_CLUSTER_CONFIG[0])
        return OptimizedGPSCache(redis_client)