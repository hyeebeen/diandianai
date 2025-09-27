import { cn } from '@/lib/utils';
import { Load } from '@/types/logistics';
import { Tag } from './Tag';

interface LoadListItemProps {
  load: Load;
  isSelected: boolean;
  onClick: () => void;
}

const statusColors = {
  'unassigned': 'bg-gray-100 text-gray-600',
  'assigned': 'bg-blue-100 text-blue-600', 
  'dispatched': 'bg-orange-100 text-orange-600',
  'in-transit': 'bg-emerald-100 text-emerald-600',
  'at-pickup': 'bg-purple-100 text-purple-600',
  'loaded': 'bg-indigo-100 text-indigo-600',
  'delivered': 'bg-green-100 text-green-600',
};

const statusDots = {
  'unassigned': 'bg-gray-400',
  'assigned': 'bg-blue-500',
  'dispatched': 'bg-orange-500', 
  'in-transit': 'bg-emerald-500',
  'at-pickup': 'bg-purple-500',
  'loaded': 'bg-indigo-500',
  'delivered': 'bg-green-500',
};

const statusLabels = {
  'unassigned': '未分配',
  'assigned': '已分配',
  'dispatched': '已调度',
  'in-transit': '运输中',
  'at-pickup': '取货中',
  'loaded': '已装车',
  'delivered': '已送达',
};

export function LoadListItem({ load, isSelected, onClick }: LoadListItemProps) {
  return (
    <div
      className={cn(
        'p-4 border-b cursor-pointer transition-colors hover:bg-muted/50',
        isSelected && 'bg-muted border-l-2 border-l-primary'
      )}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        {/* Status Dot */}
        <div className={cn(
          'w-2 h-2 rounded-full mt-2 flex-shrink-0',
          statusDots[load.status]
        )} />

        <div className="flex-1 min-w-0">
          {/* Load ID */}
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-sm">{load.id}</span>
          </div>

          {/* Route */}
          <div className="text-sm font-medium text-foreground mb-1">
            {load.origin} → {load.destination}
          </div>

          {/* Status and Badges */}
          <div className="flex items-center gap-2 mb-2">
            <span className={cn(
              'px-2 py-1 rounded-full text-xs font-medium',
              statusColors[load.status]
            )}>
              {statusLabels[load.status]}
            </span>
            {load.badges?.map((badge, index) => (
              <Tag key={index} size="sm" variant="secondary">
                {badge}
              </Tag>
            ))}
          </div>

          {/* Date */}
          <div className="text-xs text-muted-foreground">
            {load.date}
          </div>
        </div>
      </div>
    </div>
  );
}