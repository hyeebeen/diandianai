/**
 * 认证上下文
 * 提供全局认证状态管理和用户信息
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

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
      // 开发环境：检查是否有测试用户信息
      const token = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('current_user');

      if (token === 'dev-test-token' && storedUser) {
        try {
          const user = JSON.parse(storedUser);
          setUser(user);
          setIsAuthenticated(true);
          console.log('Development mode: Restored test user session');
          return true;
        } catch (error) {
          console.warn('Failed to parse stored test user:', error);
          localStorage.removeItem('access_token');
          localStorage.removeItem('current_user');
        }
      }
      return false;
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      setIsAuthenticated(false);
      return false;
    }
  };

  // 登录
  const login = async (username: string, password: string, tenantId?: string): Promise<void> => {
    try {
      setIsLoading(true);

      // 开发环境：支持测试账号快速登录
      if (username === '13800138000' && password === '8888') {
        console.log('Development mode: Using test account');
        const mockUser = {
          id: 'test-user-1',
          username: '13800138000',
          email: 'test@example.com',
          phone: '13800138000',
          full_name: '测试用户',
          role: 'admin',
          tenant_id: 'test-tenant',
          company_id: 'test-company',
          permissions: ['*'],
          avatar_url: '',
          last_login: new Date().toISOString(),
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        setUser(mockUser);
        setIsAuthenticated(true);

        // 存储到 localStorage 以保持状态
        localStorage.setItem('access_token', 'dev-test-token');
        localStorage.setItem('current_user', JSON.stringify(mockUser));

        setIsLoading(false);
        return;
      }

      // 其他账号在开发环境下抛出错误
      throw new Error('Invalid credentials');
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 登出
  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      localStorage.removeItem('access_token');
      localStorage.removeItem('current_user');
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
      const updatedUser = { ...user, ...updates };
      setUser(updatedUser);
      localStorage.setItem('current_user', JSON.stringify(updatedUser));
    }
  };

  // 检查权限
  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    return user.permissions.includes(permission) || user.permissions.includes('*');
  };

  // 检查角色
  const hasRole = (role: string): boolean => {
    if (!user) return false;
    return user.role === role || user.role === 'admin';
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