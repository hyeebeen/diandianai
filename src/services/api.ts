/**
 * 统一API客户端配置
 * 替换mockData，提供与后端API的实际集成
 * 支持认证、错误处理、请求拦截等功能
 */

import { Load, ChatMessage } from '@/types/logistics';

// API配置
const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// 错误类型定义
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// 认证令牌管理
class TokenManager {
  private static instance: TokenManager;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private tenantId: string | null = null;

  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  setTokens(accessToken: string, refreshToken: string, tenantId: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    this.tenantId = tenantId;

    // 存储到localStorage
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('tenant_id', tenantId);
  }

  getAccessToken(): string | null {
    if (!this.accessToken) {
      this.accessToken = localStorage.getItem('access_token');
    }
    return this.accessToken;
  }

  getTenantId(): string | null {
    if (!this.tenantId) {
      this.tenantId = localStorage.getItem('tenant_id');
    }
    return this.tenantId;
  }

  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.tenantId = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('tenant_id');
  }

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
}

// HTTP客户端类
class HttpClient {
  private tokenManager = TokenManager.getInstance();

  async request<T>(
    endpoint: string,
    options: RequestInit & {
      retries?: number;
      skipAuth?: boolean;
    } = {}
  ): Promise<T> {
    const {
      retries = API_CONFIG.RETRY_ATTEMPTS,
      skipAuth = false,
      ...requestOptions
    } = options;

    const url = `${API_CONFIG.BASE_URL}${endpoint}`;

    // 构建请求头
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((requestOptions.headers as Record<string, string>) || {}),
    };

    // 添加认证头
    if (!skipAuth && this.tokenManager.isAuthenticated()) {
      const token = this.tokenManager.getAccessToken();
      const tenantId = this.tokenManager.getTenantId();

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      if (tenantId) {
        headers['X-Tenant-ID'] = tenantId;
      }
    }

    const requestConfig: RequestInit = {
      ...requestOptions,
      headers,
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);

      const response = await fetch(url, {
        ...requestConfig,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // 处理HTTP错误
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        let errorDetails: any = null;

        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorData.detail || errorMessage;
          errorDetails = errorData;
        } catch {
          // 忽略JSON解析错误，使用默认错误消息
        }

        // 401错误时清除令牌
        if (response.status === 401) {
          this.tokenManager.clearTokens();
          // 可以在这里触发重定向到登录页
          window.location.href = '/login';
        }

        throw new ApiError(errorMessage, response.status, errorDetails?.code, errorDetails);
      }

      // 解析响应
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        return await response.json();
      } else {
        return (await response.text()) as unknown as T;
      }

    } catch (error) {
      // 网络错误重试逻辑
      if (retries > 0 && !(error instanceof ApiError)) {
        console.warn(`Request failed, retrying... (${API_CONFIG.RETRY_ATTEMPTS - retries + 1}/${API_CONFIG.RETRY_ATTEMPTS})`);
        await new Promise(resolve => setTimeout(resolve, API_CONFIG.RETRY_DELAY));
        return this.request<T>(endpoint, { ...options, retries: retries - 1 });
      }

      throw error;
    }
  }

  // GET请求
  async get<T>(endpoint: string, options?: RequestInit & { skipAuth?: boolean }): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  // POST请求
  async post<T>(endpoint: string, data?: any, options?: RequestInit & { skipAuth?: boolean }): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // PUT请求
  async put<T>(endpoint: string, data?: any, options?: RequestInit & { skipAuth?: boolean }): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // PATCH请求
  async patch<T>(endpoint: string, data?: any, options?: RequestInit & { skipAuth?: boolean }): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // DELETE请求
  async delete<T>(endpoint: string, options?: RequestInit & { skipAuth?: boolean }): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// 全局HTTP客户端实例
export const httpClient = new HttpClient();
export const tokenManager = TokenManager.getInstance();

// API响应类型定义
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  code?: string;
  timestamp?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// 分页查询参数
export interface PaginationParams {
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// 查询参数类型
export interface SearchParams extends PaginationParams {
  q?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
}

// 运单API类型定义
export interface ShipmentCreateRequest {
  shipment_number?: string;
  sender: {
    name: string;
    phone: string;
    company?: string;
  };
  sender_address: {
    address: string;
    latitude: number;
    longitude: number;
    city: string;
    district: string;
  };
  receiver: {
    name: string;
    phone: string;
    company?: string;
  };
  receiver_address: {
    address: string;
    latitude: number;
    longitude: number;
    city: string;
    district: string;
  };
  cargo: {
    description: string;
    weight: number;
    quantity: number;
    volume?: number;
    value?: number;
  };
  special_requirements?: string[];
  pickup_time?: string;
  expected_delivery?: string;
}

export interface ShipmentResponse {
  id: string;
  shipment_number: string;
  status: string;
  sender: {
    name: string;
    phone: string;
    company?: string;
  };
  sender_address: {
    address: string;
    latitude: number;
    longitude: number;
    city: string;
    district: string;
  };
  receiver: {
    name: string;
    phone: string;
    company?: string;
  };
  receiver_address: {
    address: string;
    latitude: number;
    longitude: number;
    city: string;
    district: string;
  };
  cargo: {
    description: string;
    weight: number;
    quantity: number;
    volume?: number;
    value?: number;
  };
  special_requirements: string[];
  created_at: string;
  updated_at: string;
  current_location?: {
    latitude: number;
    longitude: number;
    address?: string;
    timestamp: string;
  };
  status_history: Array<{
    status: string;
    timestamp: string;
    notes?: string;
    location?: {
      latitude: number;
      longitude: number;
      address?: string;
    };
  }>;
}

// GPS数据类型定义
export interface GPSLocation {
  id: string;
  vehicle_id: string;
  shipment_id: string;
  latitude: number;
  longitude: number;
  speed: number;
  heading: number;
  timestamp: string;
  source: 'g7_device' | 'driver_app' | 'manual';
}

export interface GPSRealtimeResponse {
  shipment_id: string;
  current_location: {
    latitude: number;
    longitude: number;
    address?: string;
    speed: number;
    heading: number;
    timestamp: string;
  };
  vehicle_id?: string;
  device_status: string;
  last_update: string;
}

export interface GPSRouteResponse {
  shipment_id: string;
  track_points: Array<{
    latitude: number;
    longitude: number;
    speed: number;
    timestamp: string;
  }>;
  total_distance: number;
  total_duration: number;
  statistics: {
    max_speed: number;
    avg_speed: number;
    stops_count: number;
    moving_time: number;
  };
}

// AI聊天API类型定义
export interface ChatRequest {
  message: string;
  context?: {
    session_id?: string;
    conversation_id?: string;
    user_preferences?: Record<string, any>;
    previous_extraction?: Record<string, any>;
  };
}

export interface ChatResponse {
  response: string;
  intent: string;
  confidence: number;
  conversation_id: string;
  extracted_data?: Record<string, any>;
  need_clarification?: boolean;
  clarification_needed?: string[];
  action_ready?: boolean;
  proposed_action?: {
    type: string;
    data: Record<string, any>;
  };
  action_executed?: boolean;
  execution_result?: Record<string, any>;
}

// 数据转换工具函数
export function transformShipmentToLoad(shipment: ShipmentResponse): Load {
  return {
    id: shipment.shipment_number,
    origin: `${shipment.sender_address.city}`,
    destination: `${shipment.receiver_address.city}`,
    status: transformStatus(shipment.status),
    date: new Date(shipment.created_at).toLocaleDateString('zh-CN'),
    customer: shipment.sender.company || shipment.sender.name,
    mode: '整车运输', // 默认值，可以根据cargo信息调整
    equipment: determineEquipment(shipment.cargo),
    weight: `${shipment.cargo.weight}公斤`,
    commodity: shipment.cargo.description,
    packingType: '托盘', // 默认值
    notes: shipment.special_requirements.join('；'),
    pickupCoords: [shipment.sender_address.latitude, shipment.sender_address.longitude],
    deliveryCoords: [shipment.receiver_address.latitude, shipment.receiver_address.longitude],
    stops: [
      {
        id: '1',
        type: 'pickup',
        address: shipment.sender_address.address,
        city: shipment.sender_address.city,
        state: shipment.sender_address.city, // 简化处理
        zipCode: '000000', // 默认值
        date: new Date(shipment.created_at).toLocaleDateString('zh-CN'),
        timeWindow: '上午9点 - 下午5点', // 默认值
        coordinates: [shipment.sender_address.latitude, shipment.sender_address.longitude]
      },
      {
        id: '2',
        type: 'delivery',
        address: shipment.receiver_address.address,
        city: shipment.receiver_address.city,
        state: shipment.receiver_address.city,
        zipCode: '000000',
        date: new Date(shipment.created_at).toLocaleDateString('zh-CN'),
        timeWindow: '上午9点 - 下午5点',
        coordinates: [shipment.receiver_address.latitude, shipment.receiver_address.longitude]
      }
    ]
  };
}

function transformStatus(status: string): Load['status'] {
  const statusMap: Record<string, Load['status']> = {
    'created': 'unassigned',
    'assigned': 'assigned',
    'picked_up': 'dispatched',
    'in_transit': 'in-transit',
    'at_pickup': 'at-pickup',
    'loaded': 'loaded',
    'delivered': 'delivered'
  };

  return statusMap[status] || 'unassigned';
}

function determineEquipment(cargo: ShipmentResponse['cargo']): string {
  if (cargo.weight > 15000) {
    return '厢式货车 13米';
  } else if (cargo.weight > 8000) {
    return '厢式货车 9米';
  } else {
    return '厢式货车 6米';
  }
}

export default httpClient;