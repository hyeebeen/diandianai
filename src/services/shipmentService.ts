/**
 * 运单服务模块
 * 提供运单相关的API调用功能
 */

import {
  httpClient,
  ShipmentCreateRequest,
  ShipmentResponse,
  PaginatedResponse,
  SearchParams,
  transformShipmentToLoad
} from './api';
import { Load } from '@/types/logistics';

export class ShipmentService {
  private static instance: ShipmentService;

  static getInstance(): ShipmentService {
    if (!ShipmentService.instance) {
      ShipmentService.instance = new ShipmentService();
    }
    return ShipmentService.instance;
  }

  /**
   * 获取运单列表
   */
  async getShipments(params: SearchParams = {}): Promise<PaginatedResponse<ShipmentResponse>> {
    // 开发环境：使用无需认证的测试端点
    if (import.meta.env.DEV || window.location.hostname === 'localhost') {
      try {
        const response = await httpClient.get<{count: number, shipments: any[]}>(
          '/api/test/shipments'
        );

        // 测试端点已返回标准ShipmentResponse格式，直接使用
        return {
          data: response.shipments,
          pagination: {
            page: 1,
            per_page: response.count,
            total: response.count,
            total_pages: 1
          }
        };
      } catch (error) {
        console.error('Failed to load test data:', error);
        // 如果测试端点失败，返回空数据
        return {
          data: [],
          pagination: {
            page: 1,
            per_page: 20,
            total: 0,
            total_pages: 0
          }
        };
      }
    }

    // 生产环境：使用正常的认证端点
    const queryParams = new URLSearchParams();

    // 添加分页参数
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.per_page) queryParams.append('per_page', params.per_page.toString());
    if (params.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params.sort_order) queryParams.append('sort_order', params.sort_order);

    // 添加搜索参数
    if (params.q) queryParams.append('q', params.q);
    if (params.status) queryParams.append('status', params.status);
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);

    const queryString = queryParams.toString();
    const endpoint = `/api/shipments${queryString ? `?${queryString}` : ''}`;

    return httpClient.get<PaginatedResponse<ShipmentResponse>>(endpoint);
  }

  /**
   * 获取运单列表并转换为Load格式（兼容现有组件）
   */
  async getLoads(params: SearchParams = {}): Promise<{items: Load[], page: number, page_size: number, total: number}> {
    const response = await this.getShipments(params);
    return {
      items: response.data.map(transformShipmentToLoad),
      page: response.pagination.page,
      page_size: response.pagination.per_page,
      total: response.pagination.total
    };
  }

  /**
   * 根据ID获取运单详情
   */
  async getShipment(id: string): Promise<ShipmentResponse> {
    return httpClient.get<ShipmentResponse>(`/api/shipments/${id}`);
  }

  /**
   * 创建新运单
   */
  async createShipment(data: ShipmentCreateRequest): Promise<ShipmentResponse> {
    return httpClient.post<ShipmentResponse>('/api/shipments', data);
  }

  /**
   * 更新运单状态
   */
  async updateShipmentStatus(
    id: string,
    data: {
      status: string;
      location?: {
        latitude: number;
        longitude: number;
        address?: string;
      };
      timestamp?: string;
      notes?: string;
      photo_urls?: string[];
    }
  ): Promise<ShipmentResponse> {
    return httpClient.patch<ShipmentResponse>(`/api/shipments/${id}/status`, data);
  }

  /**
   * 分配车辆和司机
   */
  async assignShipment(
    id: string,
    data: {
      vehicle_id: string;
      driver_id: string;
      planned_route?: Array<{
        sequence: number;
        location: {
          latitude: number;
          longitude: number;
          address: string;
        };
        type: 'pickup' | 'delivery';
        estimated_time: string;
      }>;
    }
  ): Promise<{
    success: boolean;
    vehicle_id: string;
    driver_id: string;
    planned_route: any[];
  }> {
    return httpClient.post(`/api/shipments/${id}/assign`, data);
  }

  /**
   * 搜索运单
   */
  async searchShipments(query: string, params: SearchParams = {}): Promise<PaginatedResponse<ShipmentResponse>> {
    return this.getShipments({
      ...params,
      q: query
    });
  }

  /**
   * 批量更新运单状态
   */
  async bulkUpdateStatus(
    shipmentIds: string[],
    status: string,
    notes?: string
  ): Promise<{
    updated_count: number;
    failed_ids: string[];
  }> {
    return httpClient.patch('/api/shipments/bulk/status', {
      shipment_ids: shipmentIds,
      status,
      notes
    });
  }

  /**
   * 获取运单通知历史
   */
  async getShipmentNotifications(id: string): Promise<Array<{
    id: string;
    type: string;
    channel: string;
    content: string;
    sent_at: string;
    status: string;
  }>> {
    return httpClient.get(`/api/shipments/${id}/notifications`);
  }

  /**
   * 根据运单号查询运单
   */
  async getShipmentByNumber(shipmentNumber: string): Promise<ShipmentResponse> {
    const response = await this.searchShipments(shipmentNumber);
    const shipment = response.data.find(s => s.shipment_number === shipmentNumber);

    if (!shipment) {
      throw new Error(`运单号 ${shipmentNumber} 不存在`);
    }

    return shipment;
  }

  /**
   * 获取运单统计信息
   */
  async getShipmentStats(params: {
    date_from?: string;
    date_to?: string;
  } = {}): Promise<{
    total_shipments: number;
    completed_shipments: number;
    pending_shipments: number;
    in_transit_shipments: number;
    delayed_shipments: number;
    completion_rate: number;
    average_delivery_time: number;
    revenue: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);

    const queryString = queryParams.toString();
    const endpoint = `/api/shipments/stats${queryString ? `?${queryString}` : ''}`;

    return httpClient.get(endpoint);
  }

  /**
   * 获取运单状态变更历史
   */
  async getShipmentHistory(id: string): Promise<Array<{
    id: string;
    status: string;
    timestamp: string;
    notes?: string;
    location?: {
      latitude: number;
      longitude: number;
      address?: string;
    };
    updated_by: {
      id: string;
      name: string;
      role: string;
    };
  }>> {
    return httpClient.get(`/api/shipments/${id}/history`);
  }
}

// 导出单例实例
export const shipmentService = ShipmentService.getInstance();
export default shipmentService;