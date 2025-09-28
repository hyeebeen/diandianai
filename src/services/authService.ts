/**
 * 认证服务模块
 * 提供用户认证、授权和会话管理功能
 */

import { httpClient, tokenManager } from './api';

export interface User {
  id: string;
  username: string;
  email: string;
  phone?: string;
  full_name: string;
  role: string;
  tenant_id: string;
  company_id: string;
  permissions: string[];
  avatar_url?: string;
  last_login?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
  tenant_id?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  company_name: string;
  invite_code?: string;
}

export interface PasswordResetRequest {
  email: string;
  tenant_id?: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
}

export class AuthService {
  private static instance: AuthService;
  private currentUser: User | null = null;

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await httpClient.post<LoginResponse>(
      '/api/auth/login',
      credentials,
      { skipAuth: true }
    );

    // 存储认证信息
    tokenManager.setTokens(
      response.access_token,
      response.refresh_token,
      response.user.tenant_id
    );

    this.currentUser = response.user;

    // 存储用户信息到localStorage
    localStorage.setItem('current_user', JSON.stringify(response.user));

    return response;
  }

  /**
   * 用户注册
   */
  async register(userData: RegisterRequest): Promise<{
    success: boolean;
    message: string;
    user?: User;
    requires_verification?: boolean;
  }> {
    return httpClient.post('/api/auth/register', userData, { skipAuth: true });
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    try {
      await httpClient.post('/api/auth/logout');
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      // 清除本地存储的认证信息
      tokenManager.clearTokens();
      this.currentUser = null;
      localStorage.removeItem('current_user');
    }
  }

  /**
   * 刷新访问令牌
   */
  async refreshToken(): Promise<{
    access_token: string;
    expires_in: number;
  }> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await httpClient.post<{
      access_token: string;
      expires_in: number;
    }>('/api/auth/refresh', {
      refresh_token: refreshToken
    }, { skipAuth: true });

    // 更新访问令牌
    const tenantId = tokenManager.getTenantId();
    if (tenantId) {
      tokenManager.setTokens(response.access_token, refreshToken, tenantId);
    }

    return response;
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    if (this.currentUser) {
      return this.currentUser;
    }

    // 尝试从localStorage恢复
    const storedUser = localStorage.getItem('current_user');
    if (storedUser) {
      try {
        this.currentUser = JSON.parse(storedUser);
        return this.currentUser!;
      } catch (error) {
        console.warn('Failed to parse stored user data:', error);
      }
    }

    // 从服务器获取最新用户信息
    const user = await httpClient.get<User>('/api/auth/me');
    this.currentUser = user;
    localStorage.setItem('current_user', JSON.stringify(user));

    return user;
  }

  /**
   * 更新用户资料
   */
  async updateProfile(updates: {
    full_name?: string;
    email?: string;
    phone?: string;
    avatar_url?: string;
  }): Promise<User> {
    const updatedUser = await httpClient.put<User>('/api/auth/profile', updates);
    this.currentUser = updatedUser;
    localStorage.setItem('current_user', JSON.stringify(updatedUser));
    return updatedUser;
  }

  /**
   * 修改密码
   */
  async changePassword(data: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }): Promise<{
    success: boolean;
    message: string;
  }> {
    return httpClient.post('/api/auth/change-password', data);
  }

  /**
   * 请求密码重置
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<{
    success: boolean;
    message: string;
  }> {
    return httpClient.post('/api/auth/password-reset', data, { skipAuth: true });
  }

  /**
   * 确认密码重置
   */
  async confirmPasswordReset(data: PasswordResetConfirmRequest): Promise<{
    success: boolean;
    message: string;
  }> {
    return httpClient.post('/api/auth/password-reset/confirm', data, { skipAuth: true });
  }

  /**
   * 检查用户权限
   */
  hasPermission(permission: string): boolean {
    if (!this.currentUser) {
      return false;
    }

    return this.currentUser.permissions.includes(permission) ||
           this.currentUser.permissions.includes('*'); // 超级管理员权限
  }

  /**
   * 检查用户角色
   */
  hasRole(role: string): boolean {
    if (!this.currentUser) {
      return false;
    }

    return this.currentUser.role === role || this.currentUser.role === 'admin';
  }

  /**
   * 检查是否已认证
   */
  isAuthenticated(): boolean {
    return tokenManager.isAuthenticated() && this.currentUser !== null;
  }

  /**
   * 获取用户租户信息
   */
  async getTenantInfo(): Promise<{
    id: string;
    name: string;
    plan: string;
    status: 'active' | 'suspended' | 'trial';
    features: string[];
    limits: {
      max_users: number;
      max_shipments: number;
      max_vehicles: number;
    };
    usage: {
      current_users: number;
      current_shipments: number;
      current_vehicles: number;
    };
    billing_info?: {
      next_billing_date: string;
      amount: number;
      currency: string;
    };
  }> {
    return httpClient.get('/api/auth/tenant');
  }

  /**
   * 获取公司信息
   */
  async getCompanyInfo(): Promise<{
    id: string;
    name: string;
    address: string;
    phone: string;
    email: string;
    website?: string;
    industry: string;
    size: string;
    settings: {
      timezone: string;
      currency: string;
      date_format: string;
      notification_preferences: Record<string, boolean>;
    };
  }> {
    return httpClient.get('/api/auth/company');
  }

  /**
   * 邀请新用户
   */
  async inviteUser(data: {
    email: string;
    role: string;
    permissions?: string[];
    send_email?: boolean;
  }): Promise<{
    success: boolean;
    message: string;
    invite_code?: string;
    invite_url?: string;
  }> {
    return httpClient.post('/api/auth/invite', data);
  }

  /**
   * 获取团队成员列表
   */
  async getTeamMembers(params: {
    page?: number;
    per_page?: number;
    role?: string;
    status?: 'active' | 'inactive' | 'pending';
  } = {}): Promise<{
    users: User[];
    total: number;
    page: number;
    per_page: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.per_page) queryParams.append('per_page', params.per_page.toString());
    if (params.role) queryParams.append('role', params.role);
    if (params.status) queryParams.append('status', params.status);

    const queryString = queryParams.toString();
    const endpoint = `/api/auth/team${queryString ? `?${queryString}` : ''}`;

    return httpClient.get(endpoint);
  }

  /**
   * 更新团队成员角色和权限
   */
  async updateTeamMember(userId: string, updates: {
    role?: string;
    permissions?: string[];
    is_active?: boolean;
  }): Promise<User> {
    return httpClient.put(`/api/auth/team/${userId}`, updates);
  }

  /**
   * 删除团队成员
   */
  async removeTeamMember(userId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    return httpClient.delete(`/api/auth/team/${userId}`);
  }

  /**
   * 验证邀请码
   */
  async validateInviteCode(inviteCode: string): Promise<{
    valid: boolean;
    company_name?: string;
    inviter_name?: string;
    role?: string;
    expires_at?: string;
  }> {
    return httpClient.get(`/api/auth/invite/validate/${inviteCode}`, { skipAuth: true });
  }

  /**
   * 通过邀请码注册
   */
  async registerWithInvite(data: {
    invite_code: string;
    username: string;
    password: string;
    full_name: string;
    phone?: string;
  }): Promise<LoginResponse> {
    const response = await httpClient.post<LoginResponse>(
      '/api/auth/register/invite',
      data,
      { skipAuth: true }
    );

    // 存储认证信息
    tokenManager.setTokens(
      response.access_token,
      response.refresh_token,
      response.user.tenant_id
    );

    this.currentUser = response.user;
    localStorage.setItem('current_user', JSON.stringify(response.user));

    return response;
  }

  /**
   * 获取登录历史
   */
  async getLoginHistory(params: {
    page?: number;
    per_page?: number;
    date_from?: string;
    date_to?: string;
  } = {}): Promise<{
    history: Array<{
      id: string;
      login_time: string;
      ip_address: string;
      user_agent: string;
      location?: string;
      success: boolean;
      failure_reason?: string;
    }>;
    total: number;
    page: number;
    per_page: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.per_page) queryParams.append('per_page', params.per_page.toString());
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);

    const queryString = queryParams.toString();
    const endpoint = `/api/auth/login-history${queryString ? `?${queryString}` : ''}`;

    return httpClient.get(endpoint);
  }

  /**
   * 启用双因子认证
   */
  async enableTwoFactor(): Promise<{
    qr_code_url: string;
    secret_key: string;
    backup_codes: string[];
  }> {
    return httpClient.post('/api/auth/2fa/enable');
  }

  /**
   * 确认双因子认证设置
   */
  async confirmTwoFactor(code: string): Promise<{
    success: boolean;
    message: string;
  }> {
    return httpClient.post('/api/auth/2fa/confirm', { code });
  }

  /**
   * 禁用双因子认证
   */
  async disableTwoFactor(password: string): Promise<{
    success: boolean;
    message: string;
  }> {
    return httpClient.post('/api/auth/2fa/disable', { password });
  }
}

// 导出单例实例
export const authService = AuthService.getInstance();
export default authService;