/**
 * Connection Status Indicator
 * Shows the status of SSE connections for real-time features
 */

import React from 'react';
import { useSSEStatus } from '@/hooks/useSSE';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';

interface ConnectionStatusProps {
  className?: string;
  showDetails?: boolean;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  className = '',
  showDetails = false
}) => {
  const {
    connectionStatuses,
    totalConnections,
    openConnections,
    overallHealthy
  } = useSSEStatus();

  const getStatusColor = () => {
    if (totalConnections === 0) return 'text-gray-400';
    if (overallHealthy) return 'text-green-500';
    if (openConnections > 0) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getStatusIcon = () => {
    if (totalConnections === 0) {
      return <WifiOff className="h-4 w-4" />;
    }
    if (overallHealthy) {
      return <Wifi className="h-4 w-4" />;
    }
    return <AlertCircle className="h-4 w-4" />;
  };

  const getStatusText = () => {
    if (totalConnections === 0) return '未连接';
    if (overallHealthy) return '连接正常';
    if (openConnections > 0) return '部分连接';
    return '连接异常';
  };

  const getConnectionDetails = () => {
    return Object.entries(connectionStatuses).map(([name, status]) => {
      const displayName = {
        'gps-updates': 'GPS定位',
        'shipment-updates': '运单状态',
        'notifications': '系统通知',
        ...Object.fromEntries(
          Object.keys(connectionStatuses)
            .filter(key => key.startsWith('ai-messages-'))
            .map(key => [key, 'AI对话'])
        )
      }[name] || name;

      const statusText = {
        'open': '正常',
        'connecting': '连接中',
        'closed': '断开'
      }[status] || status;

      const statusColor = {
        'open': 'bg-green-100 text-green-800',
        'connecting': 'bg-yellow-100 text-yellow-800',
        'closed': 'bg-red-100 text-red-800'
      }[status] || 'bg-gray-100 text-gray-800';

      return (
        <div key={name} className="flex justify-between items-center py-1">
          <span className="text-sm text-gray-600">{displayName}</span>
          <Badge variant="outline" className={`text-xs ${statusColor}`}>
            {statusText}
          </Badge>
        </div>
      );
    });
  };

  if (!showDetails) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={`flex items-center space-x-1 ${getStatusColor()} ${className}`}>
              {getStatusIcon()}
              <span className="text-sm font-medium">{getStatusText()}</span>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-2">
              <div className="font-medium">实时连接状态</div>
              <div className="text-sm">
                {totalConnections > 0 ? (
                  <div className="space-y-1">
                    {getConnectionDetails()}
                    <div className="border-t pt-1 mt-2">
                      <span className="text-xs text-gray-500">
                        {openConnections}/{totalConnections} 个连接正常
                      </span>
                    </div>
                  </div>
                ) : (
                  <span className="text-gray-500">暂无活动连接</span>
                )}
              </div>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <div className={`p-3 bg-white rounded-lg border ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900">实时连接状态</h3>
        <div className={`flex items-center space-x-1 ${getStatusColor()}`}>
          {getStatusIcon()}
          <span className="text-sm font-medium">{getStatusText()}</span>
        </div>
      </div>

      {totalConnections > 0 ? (
        <div className="space-y-2">
          {getConnectionDetails()}
          <div className="border-t pt-2 mt-3">
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-500">活动连接</span>
              <Badge variant="outline" className="text-xs">
                {openConnections}/{totalConnections}
              </Badge>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-4">
          <WifiOff className="h-8 w-8 text-gray-300 mx-auto mb-2" />
          <p className="text-sm text-gray-500">暂无活动的实时连接</p>
          <p className="text-xs text-gray-400 mt-1">
            登录后将自动建立连接
          </p>
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;