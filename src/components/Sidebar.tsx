import { cn } from '@/lib/utils';
import {
  Truck,
  Route,
  MapPin,
  Settings,
  BarChart3,
  Menu
} from 'lucide-react';
import { NotificationCenter } from '@/components/notifications/NotificationCenter';
import { ConnectionStatus } from '@/components/common/ConnectionStatus';
import { UserMenu } from '@/components/auth/UserMenu';

interface SidebarProps {
  className?: string;
}

const sidebarItems = [
  { icon: Menu, label: 'Menu', active: false },
  { icon: Truck, label: 'Loads', active: true },
  { icon: Route, label: 'Routes', active: false },
  { icon: MapPin, label: 'Tracking', active: false },
  { icon: Settings, label: 'Settings', active: false },
  { icon: BarChart3, label: 'Analytics', active: false },
];

export function Sidebar({ className }: SidebarProps) {
  return (
    <div className={cn(
      'w-16 bg-[hsl(var(--sidebar-bg))] flex flex-col items-center py-4',
      className
    )}>
      {/* Top Section - User Menu */}
      <div className="mb-4">
        <UserMenu />
      </div>

      {/* Navigation Items */}
      <div className="flex flex-col space-y-2 flex-1">
        {sidebarItems.map((item, index) => (
          <button
            key={index}
            className={cn(
              'w-10 h-10 rounded-lg flex items-center justify-center transition-colors',
              item.active
                ? 'bg-[hsl(var(--sidebar-hover))] text-white'
                : 'text-emerald-100 hover:bg-[hsl(var(--sidebar-hover))] hover:text-white'
            )}
          >
            <item.icon className="h-5 w-5" />
          </button>
        ))}
      </div>

      {/* Bottom Section - Notifications and Status */}
      <div className="flex flex-col space-y-2 mt-4">
        <NotificationCenter />
        <div className="px-1">
          <ConnectionStatus />
        </div>
      </div>
    </div>
  );
}