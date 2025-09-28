/**
 * Notification Center component
 * Displays real-time notifications from SSE
 */

import React from 'react';
import { useNotifications } from '@/hooks/useSSE';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Bell,
  BellRing,
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle,
  Trash2,
  ExternalLink
} from 'lucide-react';
import { NotificationUpdate } from '@/services/sseService';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface NotificationItemProps {
  notification: NotificationUpdate;
  onAction?: (url: string) => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({ notification, onAction }) => {
  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'info':
      default:
        return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  const getPriorityColor = () => {
    switch (notification.priority) {
      case 'high':
        return 'border-l-red-500';
      case 'medium':
        return 'border-l-yellow-500';
      case 'low':
      default:
        return 'border-l-blue-500';
    }
  };

  const timeAgo = formatDistanceToNow(new Date(notification.timestamp), {
    addSuffix: true,
    locale: zhCN
  });

  return (
    <div className={`p-3 border-l-2 ${getPriorityColor()} hover:bg-gray-50 transition-colors`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-0.5">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <h4 className="text-sm font-medium text-gray-900 truncate">
              {notification.title}
            </h4>
            <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
              {timeAgo}
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1 line-clamp-2">
            {notification.message}
          </p>
          {notification.action_url && (
            <button
              onClick={() => onAction?.(notification.action_url!)}
              className="text-xs text-blue-600 hover:text-blue-800 mt-2 flex items-center gap-1"
            >
              查看详情
              <ExternalLink className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

interface NotificationCenterProps {
  className?: string;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({ className }) => {
  const {
    notifications,
    unreadCount,
    connectionStatus,
    isConnected,
    markAsRead,
    clearNotifications
  } = useNotifications();

  const handleActionClick = (url: string) => {
    // Navigate to the action URL
    window.open(url, '_blank');
  };

  const handleDropdownOpen = () => {
    // Mark notifications as read when opened
    if (unreadCount > 0) {
      markAsRead();
    }
  };

  const getConnectionIcon = () => {
    if (!isConnected) {
      return <Bell className="h-5 w-5 text-gray-400" />;
    }
    return unreadCount > 0 ?
      <BellRing className="h-5 w-5 text-blue-600" /> :
      <Bell className="h-5 w-5 text-gray-700" />;
  };

  return (
    <DropdownMenu onOpenChange={(open) => open && handleDropdownOpen()}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={`relative ${className}`}
          disabled={!isConnected}
        >
          {getConnectionIcon()}
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent className="w-80" align="end" forceMount>
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>通知中心</span>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs text-gray-500">
              {isConnected ? '已连接' : '连接中断'}
            </span>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        {notifications.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <Bell className="h-8 w-8 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">暂无通知</p>
          </div>
        ) : (
          <>
            <ScrollArea className="h-96">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onAction={handleActionClick}
                />
              ))}
            </ScrollArea>

            <DropdownMenuSeparator />

            <div className="p-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={clearNotifications}
                className="w-full justify-start text-gray-600"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                清空所有通知
              </Button>
            </div>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default NotificationCenter;