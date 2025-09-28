/**
 * 服务模块统一导出
 * 提供所有API服务的集中访问点
 */

// 基础API客户端
export {
  httpClient,
  tokenManager,
  ApiError,
  type ApiResponse,
  type PaginatedResponse,
  type PaginationParams,
  type SearchParams
} from './api';

// 认证服务
export {
  authService,
  AuthService,
  type User,
  type LoginRequest,
  type LoginResponse,
  type RegisterRequest
} from './authService';

// 运单服务
export {
  shipmentService,
  ShipmentService,
  type ShipmentCreateRequest,
  type ShipmentResponse
} from './shipmentService';

// GPS服务
export {
  gpsService,
  GPSService,
  type GPSLocation,
  type GPSRealtimeResponse,
  type GPSRouteResponse
} from './gpsService';

// AI服务
export {
  aiService,
  AIService,
  type ChatRequest,
  type ChatResponse
} from './aiService';

// 数据转换工具
export { transformShipmentToLoad } from './api';

/**
 * 服务管理器类
 * 提供服务初始化和配置管理
 */
export class ServiceManager {
  private static instance: ServiceManager;
  private initialized = false;

  static getInstance(): ServiceManager {
    if (!ServiceManager.instance) {
      ServiceManager.instance = new ServiceManager();
    }
    return ServiceManager.instance;
  }

  /**
   * 初始化所有服务
   */
  async initialize(config?: {
    baseUrl?: string;
    timeout?: number;
    retryAttempts?: number;
  }): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      // 开发环境：完全跳过后端API调用
      if (import.meta.env.DEV) {
        console.log('Development mode: Skipping service initialization');
        this.initialized = true;
        return;
      }

      // 生产环境：正常初始化
      console.log('Initializing services...');

      // 检查认证状态
      if (tokenManager.isAuthenticated()) {
        try {
          await authService.getCurrentUser();
          console.log('User authentication verified');
        } catch (error) {
          console.warn('Failed to verify user authentication:', error);
          // 清除过期的认证信息
          tokenManager.clearTokens();
        }
      }

      this.initialized = true;
      console.log('Services initialized successfully');
    } catch (error) {
      console.error('Failed to initialize services:', error);
      throw error;
    }
  }

  /**
   * 检查服务是否已初始化
   */
  isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * 重置所有服务
   */
  reset(): void {
    tokenManager.clearTokens();
    this.initialized = false;
  }

  /**
   * 获取服务健康状态
   */
  async getHealthStatus(): Promise<{
    api: boolean;
    auth: boolean;
    gps: boolean;
    ai: boolean;
    overall: boolean;
  }> {
    const status = {
      api: false,
      auth: false,
      gps: false,
      ai: false,
      overall: false
    };

    try {
      // 检查API连接
      await httpClient.get('/api/health', { skipAuth: true });
      status.api = true;
    } catch (error) {
      console.warn('API health check failed:', error);
    }

    try {
      // 检查认证服务
      if (tokenManager.isAuthenticated()) {
        await authService.getCurrentUser();
        status.auth = true;
      } else {
        status.auth = true; // 未认证也算正常状态
      }
    } catch (error) {
      console.warn('Auth health check failed:', error);
    }

    try {
      // 检查AI服务
      const aiStatus = await aiService.getAIStatus();
      status.ai = aiStatus.status === 'online';
    } catch (error) {
      console.warn('AI health check failed:', error);
    }

    // GPS服务健康检查比较复杂，这里简化处理
    status.gps = status.api;

    // 整体状态
    status.overall = status.api && status.auth;

    return status;
  }
}

// 导出服务管理器实例
export const serviceManager = ServiceManager.getInstance();

// 默认导出所有服务
export default {
  auth: authService,
  shipment: shipmentService,
  gps: gpsService,
  ai: aiService,
  http: httpClient,
  token: tokenManager,
  manager: serviceManager
};