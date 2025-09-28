/**
 * AI服务模块
 * 提供点点精灵聊天和智能功能
 */

import {
  httpClient,
  ChatRequest,
  ChatResponse
} from './api';
import { ChatMessage } from '@/types/logistics';

export class AIService {
  private static instance: AIService;
  private currentConversationId: string | null = null;

  static getInstance(): AIService {
    if (!AIService.instance) {
      AIService.instance = new AIService();
    }
    return AIService.instance;
  }

  /**
   * 发送聊天消息给点点精灵 (使用简化API)
   */
  async sendMessage(
    message: string,
    context?: {
      session_id?: string;
      user_preferences?: Record<string, any>;
      previous_extraction?: Record<string, any>;
    }
  ): Promise<ChatResponse> {
    // 如果没有对话ID，先创建对话
    if (!this.currentConversationId) {
      const conversation = await this.createConversation({
        context_type: 'general',
        context_id: 'chat',
        metadata: context
      });
      this.currentConversationId = conversation.id;
    }

    // 发送消息到对话
    const response = await httpClient.post(`/api/ai/conversations/${this.currentConversationId}/messages`, {
      content: message,
      message_type: 'text'
    });

    // 转换为ChatResponse格式
    return {
      response: response.response,
      conversation_id: this.currentConversationId,
      timestamp: response.timestamp,
      confidence: 0.9,
      actions: [],
      metadata: {
        model: 'kimi-k2-0711-preview',
        response_time_ms: 0,
        token_usage: {}
      }
    };
  }

  /**
   * 开始新的对话会话
   */
  startNewConversation(): void {
    this.currentConversationId = null;
  }

  /**
   * 获取当前对话ID
   */
  getCurrentConversationId(): string | null {
    return this.currentConversationId;
  }

  /**
   * 创建新的对话
   */
  async createConversation(params: {
    context_type: string;
    context_id: string;
    metadata?: Record<string, any>;
  }): Promise<{ id: string; created_at: string }> {
    const response = await httpClient.post('/api/ai/conversations', params);
    return response;
  }

  /**
   * 发送消息到指定对话 (ChatPanel专用)
   */
  async sendMessageToConversation(
    conversationId: string,
    messageData: {
      content: string;
      message_type: string;
    }
  ): Promise<{
    success: boolean;
    message_id: string;
    response: string;
    timestamp: string;
  }> {
    return httpClient.post(`/api/ai/conversations/${conversationId}/messages`, messageData);
  }

  /**
   * 确认AI提议的操作
   */
  async confirmAction(
    actionId: string,
    confirmed: boolean,
    modifications?: Record<string, any>
  ): Promise<ChatResponse> {
    return httpClient.post(`/api/ai/actions/${actionId}/confirm`, {
      confirmed,
      modifications
    });
  }

  /**
   * 获取对话历史
   */
  async getConversationHistory(
    conversationId?: string,
    params: {
      page?: number;
      per_page?: number;
    } = {}
  ): Promise<{
    conversation_id: string;
    messages: Array<{
      id: string;
      role: 'user' | 'assistant' | 'system';
      content: string;
      timestamp: string;
      metadata?: Record<string, any>;
    }>;
    total: number;
    page: number;
    per_page: number;
  }> {
    const targetId = conversationId || this.currentConversationId;
    if (!targetId) {
      throw new Error('No conversation ID available');
    }

    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.per_page) queryParams.append('per_page', params.per_page.toString());

    const queryString = queryParams.toString();
    const endpoint = `/api/ai/conversations/${targetId}${queryString ? `?${queryString}` : ''}`;

    return httpClient.get(endpoint);
  }

  /**
   * 获取对话分析报告
   */
  async getConversationAnalytics(conversationId?: string): Promise<{
    conversation_id: string;
    total_messages: number;
    user_messages: number;
    assistant_messages: number;
    intent_distribution: Record<string, number>;
    conversation_duration: number;
    user_satisfaction: number | null;
    completion_rate: number;
    action_success_rate: number;
  }> {
    const targetId = conversationId || this.currentConversationId;
    if (!targetId) {
      throw new Error('No conversation ID available');
    }

    return httpClient.get(`/api/ai/conversations/${targetId}/analytics`);
  }

  /**
   * 智能运单信息提取
   */
  async extractShipmentInfo(message: string): Promise<{
    extracted_data: {
      sender_name?: string;
      sender_phone?: string;
      sender_address?: string;
      receiver_name?: string;
      receiver_phone?: string;
      receiver_address?: string;
      cargo_description?: string;
      cargo_weight?: number;
      cargo_quantity?: number;
      special_requirements?: string[];
      pickup_time?: string;
      estimated_freight?: number;
    };
    confidence_score: number;
    missing_fields: string[];
    suggestions: string[];
  }> {
    return httpClient.post('/api/ai/extract/shipment', { message });
  }

  /**
   * 路线优化建议
   */
  async getRouteOptimization(
    waypoints: Array<{
      address: string;
      latitude?: number;
      longitude?: number;
      type?: 'pickup' | 'delivery';
    }>,
    vehicleInfo?: {
      type: string;
      capacity: number;
      fuel_efficiency: number;
    }
  ): Promise<{
    optimized_sequence: number[];
    total_distance: number;
    estimated_time: number;
    fuel_cost: number;
    optimization_score: number;
    suggestions: string[];
    cost_savings: number;
    time_savings: number;
  }> {
    return httpClient.post('/api/ai/optimize/route', {
      waypoints,
      vehicle_info: vehicleInfo
    });
  }

  /**
   * 业务数据分析
   */
  async generateBusinessSummary(
    period: string,
    analysisType: 'daily' | 'weekly' | 'monthly' | 'custom' = 'weekly'
  ): Promise<{
    summary_period: string;
    total_shipments: number;
    completed_shipments: number;
    pending_shipments: number;
    key_metrics: Record<string, any>;
    insights: string[];
    recommendations: string[];
    risk_alerts: string[];
    trend_analysis: {
      growth_rate: number;
      performance_trend: 'improving' | 'stable' | 'declining';
      seasonal_patterns: string[];
    };
  }> {
    return httpClient.post('/api/ai/analysis/business', {
      period,
      analysis_type: analysisType
    });
  }

  /**
   * 异常检测和告警分析
   */
  async analyzeAlert(alertData: {
    type: string;
    severity: string;
    description: string;
    affected_components: string[];
    timestamp: string;
    metadata?: Record<string, any>;
  }): Promise<{
    alert_type: string;
    severity: string;
    priority: number;
    affected_components: string[];
    suggested_actions: string[];
    auto_resolve: boolean;
    escalation_required: boolean;
    similar_incidents: Array<{
      id: string;
      description: string;
      resolution: string;
      effectiveness: number;
    }>;
  }> {
    return httpClient.post('/api/ai/analysis/alert', alertData);
  }

  /**
   * 智能客服问答
   */
  async askQuestion(
    question: string,
    context?: {
      shipment_id?: string;
      order_id?: string;
      customer_id?: string;
    }
  ): Promise<{
    answer: string;
    confidence: number;
    sources: Array<{
      type: 'knowledge_base' | 'api_data' | 'historical_data';
      content: string;
      relevance: number;
    }>;
    suggested_followup: string[];
    escalate_to_human: boolean;
  }> {
    return httpClient.post('/api/ai/qa', {
      question,
      context
    });
  }

  /**
   * 转换ChatResponse为ChatMessage格式（兼容现有组件）
   */
  transformToLegacyMessage(response: ChatResponse): ChatMessage {
    return {
      id: Math.random().toString(36).substr(2, 9),
      role: 'agent',
      content: response.response,
      timestamp: new Date().toLocaleString('zh-CN'),
    };
  }

  /**
   * 转换用户输入为ChatMessage格式
   */
  createUserMessage(content: string): ChatMessage {
    return {
      id: Math.random().toString(36).substr(2, 9),
      role: 'human',
      content,
      timestamp: new Date().toLocaleString('zh-CN'),
    };
  }

  /**
   * 获取点点精灵状态
   */
  async getAIStatus(): Promise<{
    status: 'online' | 'offline' | 'maintenance';
    model_info: {
      primary_model: string;
      fallback_models: string[];
      capabilities: string[];
    };
    performance_metrics: {
      average_response_time: number;
      success_rate: number;
      current_load: number;
    };
    last_updated: string;
  }> {
    return httpClient.get('/api/ai/status');
  }

  /**
   * 设置用户偏好
   */
  async setUserPreferences(preferences: {
    language?: 'zh-CN' | 'en-US';
    notification_channels?: string[];
    response_style?: 'formal' | 'casual' | 'technical';
    auto_confirm_actions?: boolean;
    preferred_units?: 'metric' | 'imperial';
  }): Promise<{
    success: boolean;
    preferences: Record<string, any>;
  }> {
    return httpClient.put('/api/ai/preferences', preferences);
  }

  /**
   * 获取用户偏好
   */
  async getUserPreferences(): Promise<{
    language: string;
    notification_channels: string[];
    response_style: string;
    auto_confirm_actions: boolean;
    preferred_units: string;
  }> {
    return httpClient.get('/api/ai/preferences');
  }

  /**
   * 订阅点点精灵事件 (Server-Sent Events)
   */
  subscribeToAIEvents(
    eventTypes: string[],
    onEvent: (event: {
      type: string;
      data: any;
      timestamp: string;
    }) => void,
    onError?: (error: Error) => void
  ): () => void {
    const eventSource = new EventSource(`/api/ai/events?types=${eventTypes.join(',')}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onEvent(data);
      } catch (error) {
        console.error('Failed to parse AI event:', error);
        onError?.(error as Error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('AI EventSource error:', error);
      onError?.(new Error('EventSource connection error'));
    };

    // 返回取消订阅函数
    return () => {
      eventSource.close();
    };
  }
}

// 导出单例实例
export const aiService = AIService.getInstance();
export default aiService;