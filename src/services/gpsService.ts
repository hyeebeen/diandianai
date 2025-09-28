/**
 * GPS服务模块
 * 提供GPS位置追踪和路线查询功能
 */

import {
  httpClient,
  GPSLocation,
  GPSRealtimeResponse,
  GPSRouteResponse
} from './api';

export class GPSService {
  private static instance: GPSService;

  static getInstance(): GPSService {
    if (!GPSService.instance) {
      GPSService.instance = new GPSService();
    }
    return GPSService.instance;
  }

  /**
   * 获取运单实时GPS位置
   */
  async getRealtimeLocation(shipmentId: string): Promise<GPSRealtimeResponse> {
    return httpClient.get<GPSRealtimeResponse>(`/api/gps/realtime/${shipmentId}`);
  }

  /**
   * 上报GPS位置数据
   */
  async reportLocation(data: {
    vehicle_id: string;
    shipment_id: string;
    latitude: number;
    longitude: number;
    speed: number;
    heading: number;
    timestamp?: string;
    source?: 'g7_device' | 'driver_app' | 'manual';
  }): Promise<GPSLocation> {
    return httpClient.post<GPSLocation>('/api/gps/locations', {
      ...data,
      timestamp: data.timestamp || new Date().toISOString(),
      source: data.source || 'driver_app'
    });
  }

  /**
   * 批量上报GPS位置数据
   */
  async reportBatchLocations(
    locations: Array<{
      vehicle_id: string;
      shipment_id: string;
      latitude: number;
      longitude: number;
      speed: number;
      heading: number;
      timestamp?: string;
      source?: 'g7_device' | 'driver_app' | 'manual';
    }>
  ): Promise<{
    success_count: number;
    failed_count: number;
    failed_items: Array<{ index: number; error: string }>;
  }> {
    const processedLocations = locations.map(loc => ({
      ...loc,
      timestamp: loc.timestamp || new Date().toISOString(),
      source: loc.source || 'driver_app'
    }));

    return httpClient.post('/api/gps/locations/batch', {
      locations: processedLocations
    });
  }

  /**
   * 获取运单路线轨迹
   */
  async getShipmentRoute(
    shipmentId: string,
    params: {
      start_time?: string;
      end_time?: string;
      interval?: number; // 采样间隔(秒)
    } = {}
  ): Promise<GPSRouteResponse> {
    const queryParams = new URLSearchParams();
    if (params.start_time) queryParams.append('start_time', params.start_time);
    if (params.end_time) queryParams.append('end_time', params.end_time);
    if (params.interval) queryParams.append('interval', params.interval.toString());

    const queryString = queryParams.toString();
    const endpoint = `/api/gps/route/${shipmentId}${queryString ? `?${queryString}` : ''}`;

    return httpClient.get<GPSRouteResponse>(endpoint);
  }

  /**
   * 获取车辆历史轨迹
   */
  async getVehicleRoute(
    vehicleId: string,
    params: {
      start_time: string;
      end_time: string;
      interval?: number;
    }
  ): Promise<{
    vehicle_id: string;
    track_points: Array<{
      latitude: number;
      longitude: number;
      speed: number;
      heading: number;
      timestamp: string;
    }>;
    total_distance: number;
    total_duration: number;
    statistics: {
      max_speed: number;
      avg_speed: number;
      stops_count: number;
      moving_time: number;
      idle_time: number;
    };
  }> {
    const queryParams = new URLSearchParams({
      start_time: params.start_time,
      end_time: params.end_time,
    });

    if (params.interval) {
      queryParams.append('interval', params.interval.toString());
    }

    return httpClient.get(`/api/gps/vehicles/${vehicleId}/route?${queryParams.toString()}`);
  }

  /**
   * 获取多个运单的实时位置
   */
  async getBatchRealtimeLocations(shipmentIds: string[]): Promise<{
    locations: Array<GPSRealtimeResponse & { shipment_id: string }>;
    failed_shipments: string[];
  }> {
    return httpClient.post('/api/gps/realtime/batch', {
      shipment_ids: shipmentIds
    });
  }

  /**
   * 获取电子围栏信息
   */
  async getGeofences(): Promise<Array<{
    id: string;
    name: string;
    type: 'circle' | 'polygon';
    coordinates: number[][];
    radius?: number; // 圆形围栏半径(米)
    description?: string;
    active: boolean;
  }>> {
    return httpClient.get('/api/gps/geofences');
  }

  /**
   * 检查车辆是否在电子围栏内
   */
  async checkGeofence(
    vehicleId: string,
    geofenceId: string
  ): Promise<{
    vehicle_id: string;
    geofence_id: string;
    is_inside: boolean;
    distance_to_boundary: number;
    last_check: string;
  }> {
    return httpClient.get(`/api/gps/vehicles/${vehicleId}/geofence/${geofenceId}`);
  }

  /**
   * 计算两点间距离
   */
  async calculateDistance(
    from: { latitude: number; longitude: number },
    to: { latitude: number; longitude: number }
  ): Promise<{
    distance: number; // 距离(公里)
    bearing: number;  // 方向角(度)
    estimated_time: number; // 预估时间(分钟)
  }> {
    return httpClient.post('/api/gps/calculate-distance', {
      from,
      to
    });
  }

  /**
   * 路线优化
   */
  async optimizeRoute(
    waypoints: Array<{
      latitude: number;
      longitude: number;
      address?: string;
      type?: 'pickup' | 'delivery';
      time_window?: {
        start: string;
        end: string;
      };
    }>,
    options: {
      start_location?: { latitude: number; longitude: number };
      vehicle_type?: string;
      optimize_for?: 'distance' | 'time' | 'fuel';
    } = {}
  ): Promise<{
    optimized_sequence: number[];
    total_distance: number;
    estimated_time: number;
    fuel_cost: number;
    optimization_score: number;
    route_geometry: string; // 路线几何数据(polyline)
    turn_by_turn_directions: Array<{
      instruction: string;
      distance: number;
      duration: number;
      maneuver: string;
    }>;
  }> {
    return httpClient.post('/api/gps/optimize-route', {
      waypoints,
      ...options
    });
  }

  /**
   * 获取实时交通信息
   */
  async getTrafficInfo(
    bounds: {
      north: number;
      south: number;
      east: number;
      west: number;
    }
  ): Promise<{
    traffic_incidents: Array<{
      id: string;
      type: 'accident' | 'construction' | 'congestion' | 'road_closure';
      location: { latitude: number; longitude: number };
      description: string;
      severity: 'low' | 'medium' | 'high';
      estimated_delay: number; // 分钟
      start_time: string;
      end_time?: string;
    }>;
    traffic_flow: Array<{
      road_name: string;
      segment_id: string;
      speed: number;
      congestion_level: 'free' | 'light' | 'moderate' | 'heavy' | 'standstill';
      travel_time_ratio: number;
    }>;
  }> {
    return httpClient.post('/api/gps/traffic-info', { bounds });
  }

  /**
   * 订阅实时GPS更新 (WebSocket)
   */
  subscribeToRealtimeUpdates(
    shipmentIds: string[],
    onUpdate: (data: GPSRealtimeResponse) => void,
    onError?: (error: Error) => void
  ): () => void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/gps/ws/realtime`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('GPS WebSocket connected');
      // 订阅指定运单的更新
      ws.send(JSON.stringify({
        action: 'subscribe',
        shipment_ids: shipmentIds
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'location_update') {
          onUpdate(data.payload);
        }
      } catch (error) {
        console.error('Failed to parse GPS WebSocket message:', error);
        onError?.(error as Error);
      }
    };

    ws.onerror = (error) => {
      console.error('GPS WebSocket error:', error);
      onError?.(new Error('WebSocket connection error'));
    };

    ws.onclose = () => {
      console.log('GPS WebSocket disconnected');
    };

    // 返回取消订阅函数
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          action: 'unsubscribe',
          shipment_ids: shipmentIds
        }));
      }
      ws.close();
    };
  }

  /**
   * 获取GPS数据统计
   */
  async getGPSStatistics(params: {
    vehicle_id?: string;
    shipment_id?: string;
    date_from: string;
    date_to: string;
  }): Promise<{
    total_points: number;
    total_distance: number;
    total_driving_time: number;
    max_speed: number;
    avg_speed: number;
    stops_count: number;
    geofence_violations: number;
    data_quality_score: number;
  }> {
    const queryParams = new URLSearchParams({
      date_from: params.date_from,
      date_to: params.date_to,
    });

    if (params.vehicle_id) queryParams.append('vehicle_id', params.vehicle_id);
    if (params.shipment_id) queryParams.append('shipment_id', params.shipment_id);

    return httpClient.get(`/api/gps/statistics?${queryParams.toString()}`);
  }
}

// 导出单例实例
export const gpsService = GPSService.getInstance();
export default gpsService;