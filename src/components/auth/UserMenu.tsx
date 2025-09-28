/**
 * 用户菜单组件
 * 显示用户信息和操作菜单
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  User,
  Settings,
  LogOut,
  Shield,
  Building,
  Bell,
  HelpCircle,
} from 'lucide-react';

interface UserMenuProps {
  className?: string;
}

export const UserMenu: React.FC<UserMenuProps> = ({ className }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => navigate('/login')}
        className={className}
      >
        登录
      </Button>
    );
  }

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleProfileClick = () => {
    navigate('/profile');
  };

  const handleSettingsClick = () => {
    navigate('/settings');
  };

  const handleTeamClick = () => {
    navigate('/team');
  };

  const handleNotificationsClick = () => {
    navigate('/notifications');
  };

  const handleHelpClick = () => {
    navigate('/help');
  };

  // 获取用户名首字母作为头像
  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // 角色显示名称映射
  const roleDisplayNames: Record<string, string> = {
    admin: '管理员',
    manager: '经理',
    dispatcher: '调度员',
    driver: '司机',
    customer: '客户',
    operator: '操作员',
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className={`relative h-10 w-10 rounded-full ${className}`}
        >
          <Avatar className="h-10 w-10">
            <AvatarImage src={user.avatar_url} alt={user.full_name} />
            <AvatarFallback className="bg-blue-500 text-white">
              {getInitials(user.full_name)}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent className="w-64" align="end" forceMount>
        {/* 用户信息 */}
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-2">
            <div className="flex items-center space-x-2">
              <div className="flex flex-col">
                <p className="text-sm font-medium leading-none">
                  {user.full_name}
                </p>
                <p className="text-xs leading-none text-muted-foreground mt-1">
                  {user.email}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="text-xs">
                {roleDisplayNames[user.role] || user.role}
              </Badge>
              {!user.is_active && (
                <Badge variant="destructive" className="text-xs">
                  已停用
                </Badge>
              )}
            </div>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        {/* 个人中心 */}
        <DropdownMenuItem onClick={handleProfileClick}>
          <User className="mr-2 h-4 w-4" />
          <span>个人中心</span>
        </DropdownMenuItem>

        {/* 通知中心 */}
        <DropdownMenuItem onClick={handleNotificationsClick}>
          <Bell className="mr-2 h-4 w-4" />
          <span>通知中心</span>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* 团队管理 (仅管理员可见) */}
        {(user.role === 'admin' || user.role === 'manager') && (
          <DropdownMenuItem onClick={handleTeamClick}>
            <Building className="mr-2 h-4 w-4" />
            <span>团队管理</span>
          </DropdownMenuItem>
        )}

        {/* 系统设置 */}
        <DropdownMenuItem onClick={handleSettingsClick}>
          <Settings className="mr-2 h-4 w-4" />
          <span>系统设置</span>
        </DropdownMenuItem>

        {/* 权限管理 (仅管理员可见) */}
        {user.role === 'admin' && (
          <DropdownMenuItem onClick={() => navigate('/permissions')}>
            <Shield className="mr-2 h-4 w-4" />
            <span>权限管理</span>
          </DropdownMenuItem>
        )}

        <DropdownMenuSeparator />

        {/* 帮助中心 */}
        <DropdownMenuItem onClick={handleHelpClick}>
          <HelpCircle className="mr-2 h-4 w-4" />
          <span>帮助中心</span>
        </DropdownMenuItem>

        {/* 登出 */}
        <DropdownMenuItem onClick={handleLogout} className="text-red-600">
          <LogOut className="mr-2 h-4 w-4" />
          <span>退出登录</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserMenu;