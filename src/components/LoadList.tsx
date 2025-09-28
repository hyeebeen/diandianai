import { useState, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Load } from '@/types/logistics';
import { LoadListItem } from './LoadListItem';
import { Search, Filter, RefreshCw, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { shipmentService } from '@/services/shipmentService';
import { useShipmentUpdates } from '@/hooks/useSSE';
import { useAuth } from '@/contexts/AuthContext';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface LoadListProps {
  selectedLoadId?: string;
  onLoadSelect: (loadId: string) => void;
  className?: string;
}

type FilterStatus = 'all' | 'pending' | 'assigned' | 'in-transit' | 'delivered' | 'cancelled';

export function LoadList({ selectedLoadId, onLoadSelect, className }: LoadListProps) {
  const { user } = useAuth();
  const [loads, setLoads] = useState<Load[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0
  });

  // SSE shipment updates
  const { lastUpdate: shipmentUpdate, connectionStatus, isConnected } = useShipmentUpdates();

  // Load shipments from API
  const loadShipments = async (resetPagination = false) => {
    if (!user) return;

    try {
      setIsLoading(true);
      setError(null);

      const page = resetPagination ? 1 : pagination.page;
      const params = {
        page,
        page_size: pagination.pageSize,
        search: searchQuery.trim() || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      };

      const response = await shipmentService.getLoads(params);

      setLoads(resetPagination ? response.items : [
        ...(resetPagination ? [] : loads),
        ...response.items
      ]);

      setPagination({
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: Math.ceil(response.total / response.page_size)
      });

    } catch (error: any) {
      console.error('Failed to load shipments:', error);
      setError(error.message || '加载运单失败');
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadShipments(true);
  }, [user, statusFilter]);

  // Handle search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      loadShipments(true);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Handle real-time updates
  useEffect(() => {
    if (shipmentUpdate) {
      setLoads(prevLoads => {
        const updatedLoads = [...prevLoads];
        const index = updatedLoads.findIndex(load => load.id === shipmentUpdate.shipment_id);

        if (index !== -1) {
          // Update existing shipment
          updatedLoads[index] = {
            ...updatedLoads[index],
            status: shipmentUpdate.status as any,
            lastUpdate: new Date(shipmentUpdate.timestamp),
            notes: shipmentUpdate.notes
          };

          if (shipmentUpdate.location) {
            updatedLoads[index].currentLocation = shipmentUpdate.location;
          }
        } else {
          // Refresh list if this is a new shipment
          loadShipments(true);
        }

        return updatedLoads;
      });
    }
  }, [shipmentUpdate]);

  const filteredLoads = useMemo(() => {
    return loads.filter(load => {
      const matchesSearch = !searchQuery.trim() ||
        load.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        load.origin.toLowerCase().includes(searchQuery.toLowerCase()) ||
        load.destination.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = statusFilter === 'all' || load.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [loads, searchQuery, statusFilter]);

  const handleRefresh = () => {
    loadShipments(true);
  };

  const loadMore = () => {
    if (pagination.page < pagination.totalPages && !isLoading) {
      setPagination(prev => ({ ...prev, page: prev.page + 1 }));
      loadShipments(false);
    }
  };

  return (
    <div className={cn('w-[340px] bg-card border-r flex flex-col', className)}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">运单</h2>
          <div className="flex items-center gap-2">
            <div className="text-sm text-muted-foreground">
              {pagination.total > 0 ?
                `${Math.min((pagination.page - 1) * pagination.pageSize + 1, pagination.total)}-${Math.min(pagination.page * pagination.pageSize, pagination.total)} / ${pagination.total}` :
                '0'
              }
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
              className="h-6 w-6 p-0"
            >
              {isLoading ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <RefreshCw className="h-3 w-3" />
              )}
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索运单..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as FilterStatus)}>
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="状态筛选" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="pending">待分配</SelectItem>
              <SelectItem value="assigned">已分配</SelectItem>
              <SelectItem value="in-transit">运输中</SelectItem>
              <SelectItem value="delivered">已送达</SelectItem>
              <SelectItem value="cancelled">已取消</SelectItem>
            </SelectContent>
          </Select>

          {!isConnected && (
            <Badge variant="destructive" className="text-xs">
              离线
            </Badge>
          )}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 pb-0">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Load List */}
      <div className="flex-1 overflow-y-auto">
        {filteredLoads.length === 0 && !isLoading ? (
          <div className="p-8 text-center text-gray-500">
            <div className="text-lg mb-2">📋</div>
            <p className="text-sm">
              {loads.length === 0 ? '暂无运单数据' : '没有符合条件的运单'}
            </p>
            {searchQuery && (
              <p className="text-xs mt-1 text-gray-400">
                尝试调整搜索条件
              </p>
            )}
          </div>
        ) : (
          <>
            {filteredLoads.map((load) => (
              <LoadListItem
                key={load.id}
                load={load}
                isSelected={selectedLoadId === load.id}
                onClick={() => onLoadSelect(load.id)}
              />
            ))}

            {/* Load More Button */}
            {pagination.page < pagination.totalPages && (
              <div className="p-4">
                <Button
                  variant="outline"
                  onClick={loadMore}
                  disabled={isLoading}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      加载中...
                    </>
                  ) : (
                    `加载更多 (${filteredLoads.length}/${pagination.total})`
                  )}
                </Button>
              </div>
            )}

            {/* Loading Indicator */}
            {isLoading && filteredLoads.length === 0 && (
              <div className="p-8 text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-blue-600" />
                <p className="text-sm text-gray-500">加载运单数据...</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}