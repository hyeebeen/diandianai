/**
 * 认证上下文
 * 提供全局认证状态管理和用户信息
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authService } from '@/services/authService';

// 开发环境：定义基本的用户接口，避免导入错误
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

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string, tenantId?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (updates: Partial<User>) => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  checkAuth: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 检查认证状态
  const checkAuth = async (): Promise<boolean> => {
    try {
      // 检查是否存在有效的认证状态
      if (!authService.isAuthenticated()) {
        setUser(null);
        setIsAuthenticated(false);
        return false;
      }

      // 尝试获取当前用户信息
      const user = await authService.getCurrentUser();
      setUser(user);
      setIsAuthenticated(true);
      console.log('Auth restored for user:', user.username);
      return true;
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      setIsAuthenticated(false);
      // 清理失效的认证信息
      await authService.logout();
      return false;
    }
  };

  // 登录
  const login = async (username: string, password: string, tenantId?: string): Promise<void> => {
    try {
      setIsLoading(true);

      // 调用真实的认证服务
      const credentials = {
        identifier: username,  // 后端期望identifier字段
        password: password
      };

      // 首先设置默认租户ID用于登录请求
      const defaultTenantId = tenantId || 'c99fef2a-bb59-4d02-a4e7-b79f6dfaf35c';

      // 确保租户ID在登录请求中传递
      localStorage.setItem('tenant_id', defaultTenantId);

      // 使用特殊的登录方法，确保X-Tenant-ID头被发送
      const loginResponse = await authService.loginWithTenant(credentials, defaultTenantId);

      // 设置用户状态
      setUser(loginResponse.user);
      setIsAuthenticated(true);

      console.log('Login successful:', loginResponse.user);
    } catch (error) {
      console.error('Login failed:', error);
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 登出
  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      await authService.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  };

  // 更新用户信息
  const updateUser = async (updates: Partial<User>): Promise<void> => {
    if (user) {
      try {
        const updatedUser = await authService.updateProfile(updates);
        setUser(updatedUser);
      } catch (error) {
        console.error('Update user failed:', error);
        throw error;
      }
    }
  };

  // 检查权限
  const hasPermission = (permission: string): boolean => {
    return authService.hasPermission(permission);
  };

  // 检查角色
  const hasRole = (role: string): boolean => {
    return authService.hasRole(role);
  };

  // 初始化认证状态
  useEffect(() => {
    const initAuth = async () => {
      try {
        setIsLoading(true);
        console.log('Development mode: Initializing auth context');
        await checkAuth(); // 检查是否有保存的测试用户状态
      } catch (error) {
        console.error('Failed to initialize auth:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // 监听认证状态变化
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'access_token' || e.key === 'current_user') {
        if (e.newValue === null) {
          // Token被清除，执行登出
          setUser(null);
          setIsAuthenticated(false);
        } else {
          // Token发生变化，重新检查认证状态
          checkAuth();
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    updateUser,
    hasPermission,
    hasRole,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;