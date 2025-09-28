import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useGPSUpdates, useShipmentUpdates } from '@/hooks/useSSE';
import { gpsService } from '@/services/gpsService';
import { useAuth } from '@/contexts/AuthContext';

// 修复 Leaflet 默认图标问题
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface GPSData {
  shipment_id: string;
  latitude: number;
  longitude: number;
  speed?: number;
  heading?: number;
  timestamp: string;
  accuracy?: number;
  altitude?: number;
}

interface VehicleData extends GPSData {
  track: Array<{ lat: number; lng: number; timestamp: string }>;
  status: 'active' | 'inactive' | 'warning';
  lastUpdate: Date;
  vehicle_id?: string;
}

interface RealTimeGPSMapProps {
  selectedShipmentId?: string;
  showTracks?: boolean;
  showSpeed?: boolean;
  maxTrackPoints?: number;
  className?: string;
}

// 自定义车辆图标
const createVehicleIcon = (heading: number = 0, speed: number = 0, status: 'active' | 'inactive' | 'warning') => {
  const color = status === 'active' ? '#22c55e' : status === 'warning' ? '#f59e0b' : '#ef4444';
  const size = speed > 50 ? 20 : speed > 20 ? 16 : 12;

  return L.divIcon({
    html: `
      <div style="
        transform: rotate(${heading}deg);
        width: ${size}px;
        height: ${size}px;
        background-color: ${color};
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          width: 0;
          height: 0;
          border-left: 3px solid transparent;
          border-right: 3px solid transparent;
          border-bottom: 6px solid white;
        "></div>
      </div>
    `,
    className: 'vehicle-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};


// 地图控制组件
const MapController: React.FC<{ vehicles: Map<string, VehicleData> }> = ({ vehicles }) => {
  const map = useMap();

  useEffect(() => {
    if (vehicles.size > 0) {
      const bounds = L.latLngBounds([]);
      vehicles.forEach((vehicle) => {
        bounds.extend([vehicle.latitude, vehicle.longitude]);
      });

      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [20, 20] });
      }
    }
  }, [map, vehicles]);

  return null;
};

// 性能统计组件
const PerformanceStats: React.FC<{
  shipmentCount: number;
  updateRate: number;
  connectionStatus: string;
  lastUpdate: Date | null;
}> = ({ shipmentCount, updateRate, connectionStatus, lastUpdate }) => {
  return (
    <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg z-[1000]">
      <h3 className="font-semibold mb-2">GPS状态</h3>
      <div className="space-y-1 text-sm">
        <div>运单数量: {shipmentCount}</div>
        <div>更新频率: {updateRate.toFixed(1)}/秒</div>
        <div className="flex items-center gap-2">
          连接状态:
          <span className={`w-2 h-2 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' :
            connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
          }`}></span>
          {connectionStatus === 'connected' ? '已连接' :
           connectionStatus === 'connecting' ? '连接中' : '未连接'}
        </div>
        {lastUpdate && (
          <div>最后更新: {lastUpdate.toLocaleTimeString()}</div>
        )}
      </div>
    </div>
  );
};

// 运单列表组件
const ShipmentList: React.FC<{
  shipments: Map<string, VehicleData>;
  onShipmentSelect: (shipmentId: string) => void;
  selectedShipment: string | null;
}> = ({ shipments, onShipmentSelect, selectedShipment }) => {
  return (
    <div className="absolute top-4 left-4 bg-white p-4 rounded-lg shadow-lg z-[1000] max-w-xs">
      <h3 className="font-semibold mb-2">运单GPS</h3>
      <div className="max-h-60 overflow-y-auto">
        {Array.from(shipments.values()).map((shipment) => (
          <div
            key={shipment.shipment_id}
            className={`p-2 rounded cursor-pointer hover:bg-gray-100 ${
              selectedShipment === shipment.shipment_id ? 'bg-blue-100' : ''
            }`}
            onClick={() => onShipmentSelect(shipment.shipment_id)}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-sm">{shipment.shipment_id}</span>
              <span className={`w-2 h-2 rounded-full ${
                shipment.status === 'active' ? 'bg-green-500' :
                shipment.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`}></span>
            </div>
            {shipment.speed && (
              <div className="text-xs text-gray-600">
                速度: {shipment.speed.toFixed(1)} km/h
              </div>
            )}
            <div className="text-xs text-gray-600">
              更新: {new Date(shipment.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const RealTimeGPSMap: React.FC<RealTimeGPSMapProps> = ({
  selectedShipmentId,
  showTracks = true,
  showSpeed = true,
  maxTrackPoints = 50,
  className = '',
}) => {
  const { user } = useAuth();
  const [shipments, setShipments] = useState<Map<string, VehicleData>>(new Map());
  const [selectedShipment, setSelectedShipment] = useState<string | null>(selectedShipmentId || null);
  const [updateRate, setUpdateRate] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const updateCounter = useRef(0);
  const lastRateCalculation = useRef(Date.now());

  // SSE GPS 更新
  const { lastUpdate: gpsUpdate, connectionStatus, isConnected } = useGPSUpdates();

  // 加载初始GPS数据
  useEffect(() => {
    const loadGPSData = async () => {
      if (!user) return;

      try {
        setIsLoading(true);
        const activeShipments = await gpsService.getActiveShipments();

        const shipmentsMap = new Map<string, VehicleData>();

        // 为每个活跃运单获取最新GPS位置
        for (const shipment of activeShipments) {
          try {
            const location = await gpsService.getRealTimeLocation(shipment.id);
            if (location) {
              shipmentsMap.set(shipment.id, {
                shipment_id: shipment.id,
                latitude: location.latitude,
                longitude: location.longitude,
                speed: location.speed || 0,
                heading: location.heading || 0,
                timestamp: location.timestamp,
                accuracy: location.accuracy,
                altitude: location.altitude,
                track: [{
                  lat: location.latitude,
                  lng: location.longitude,
                  timestamp: location.timestamp
                }],
                status: 'active',
                lastUpdate: new Date()
              });
            }
          } catch (error) {
            console.warn(`Failed to load GPS for shipment ${shipment.id}:`, error);
          }
        }

        setShipments(shipmentsMap);
      } catch (error) {
        console.error('Failed to load GPS data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadGPSData();
  }, [user]);

  // 处理实时GPS更新
  useEffect(() => {
    if (gpsUpdate) {
      setShipments((prev) => {
        const newShipments = new Map(prev);
        const existing = newShipments.get(gpsUpdate.shipment_id);

        // 判断运单状态
        const now = new Date();
        const dataTime = new Date(gpsUpdate.timestamp);
        const timeDiff = (now.getTime() - dataTime.getTime()) / 1000;

        let status: 'active' | 'inactive' | 'warning' = 'active';
        if (timeDiff > 120) status = 'inactive'; // 2分钟无更新
        else if (timeDiff > 60) status = 'warning'; // 1分钟警告

        const newTrack = existing?.track || [];

        // 添加新的轨迹点
        newTrack.push({
          lat: gpsUpdate.latitude,
          lng: gpsUpdate.longitude,
          timestamp: gpsUpdate.timestamp,
        });

        // 限制轨迹点数量
        if (newTrack.length > maxTrackPoints) {
          newTrack.splice(0, newTrack.length - maxTrackPoints);
        }

        const shipmentData: VehicleData = {
          shipment_id: gpsUpdate.shipment_id,
          latitude: gpsUpdate.latitude,
          longitude: gpsUpdate.longitude,
          speed: gpsUpdate.speed || 0,
          heading: gpsUpdate.heading || 0,
          timestamp: gpsUpdate.timestamp,
          accuracy: gpsUpdate.accuracy,
          altitude: gpsUpdate.altitude,
          track: newTrack,
          status,
          lastUpdate: now,
        };

        newShipments.set(gpsUpdate.shipment_id, shipmentData);
        return newShipments;
      });

      // 更新频率计算
      updateCounter.current++;
      const now = Date.now();
      if (now - lastRateCalculation.current >= 1000) {
        setUpdateRate(updateCounter.current);
        updateCounter.current = 0;
        lastRateCalculation.current = now;
      }

      setLastUpdate(new Date());
    }
  }, [gpsUpdate, maxTrackPoints]);

  // 定期检查运单状态
  useEffect(() => {
    const interval = setInterval(() => {
      setShipments((prev) => {
        const newShipments = new Map(prev);
        const now = new Date();

        newShipments.forEach((shipment, shipmentId) => {
          const timeDiff = (now.getTime() - shipment.lastUpdate.getTime()) / 1000;

          let newStatus = shipment.status;
          if (timeDiff > 120) newStatus = 'inactive';
          else if (timeDiff > 60) newStatus = 'warning';
          else newStatus = 'active';

          if (newStatus !== shipment.status) {
            newShipments.set(shipmentId, { ...shipment, status: newStatus });
          }
        });

        return newShipments;
      });
    }, 10000); // 每10秒检查一次

    return () => clearInterval(interval);
  }, []);

  // 生成轨迹线颜色
  const getTrackColor = useCallback((shipment: VehicleData) => {
    switch (shipment.status) {
      case 'active': return '#22c55e';
      case 'warning': return '#f59e0b';
      case 'inactive': return '#ef4444';
      default: return '#6b7280';
    }
  }, []);

  // 渲染运单标记
  const shipmentMarkers = useMemo(() => {
    return Array.from(shipments.values()).map((shipment) => (
      <Marker
        key={shipment.shipment_id}
        position={[shipment.latitude, shipment.longitude]}
        icon={createVehicleIcon(shipment.heading || 0, shipment.speed || 0, shipment.status)}
      >
        <Popup>
          <div className="p-2">
            <h3 className="font-semibold">{shipment.shipment_id}</h3>
            <div className="space-y-1 text-sm">
              <div>位置: {shipment.latitude.toFixed(6)}, {shipment.longitude.toFixed(6)}</div>
              {shipment.speed && (
                <div>速度: {shipment.speed.toFixed(1)} km/h</div>
              )}
              {shipment.heading && (
                <div>方向: {shipment.heading.toFixed(0)}°</div>
              )}
              <div>更新时间: {new Date(shipment.timestamp).toLocaleString()}</div>
              {shipment.accuracy && (
                <div>精度: ±{shipment.accuracy}m</div>
              )}
              {shipment.altitude && (
                <div>海拔: {shipment.altitude.toFixed(0)}m</div>
              )}
            </div>
          </div>
        </Popup>
      </Marker>
    ));
  }, [shipments]);

  // 渲染轨迹线
  const trackLines = useMemo(() => {
    if (!showTracks) return [];

    return Array.from(shipments.values()).map((shipment) => {
      if (shipment.track.length < 2) return null;

      const positions = shipment.track.map(point => [point.lat, point.lng] as [number, number]);

      return (
        <Polyline
          key={`track-${shipment.shipment_id}`}
          positions={positions}
          color={getTrackColor(shipment)}
          weight={3}
          opacity={0.7}
        />
      );
    }).filter(Boolean);
  }, [shipments, showTracks, getTrackColor]);

  return (
    <div className={`relative w-full h-full ${className}`}>
      <MapContainer
        center={[39.9042, 116.4074]} // 北京中心
        zoom={10}
        className="w-full h-full"
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapController vehicles={shipments} />

        {shipmentMarkers}
        {trackLines}
      </MapContainer>

      <PerformanceStats
        shipmentCount={shipments.size}
        updateRate={updateRate}
        connectionStatus={connectionStatus}
        lastUpdate={lastUpdate}
      />

      <ShipmentList
        shipments={shipments}
        onShipmentSelect={setSelectedShipment}
        selectedShipment={selectedShipment}
      />

      {isLoading && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[2000]">
          <div className="bg-white p-4 rounded-lg">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
              <p>加载GPS数据...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTimeGPSMap;