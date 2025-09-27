import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface TagProps {
  children: React.ReactNode;
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md';
  icon?: LucideIcon;
  className?: string;
}

const tagVariants = {
  default: 'bg-muted text-muted-foreground',
  secondary: 'bg-secondary text-secondary-foreground',
  success: 'bg-emerald-100 text-emerald-700',
  warning: 'bg-orange-100 text-orange-700',
  danger: 'bg-red-100 text-red-700',
};

const tagSizes = {
  sm: 'h-6 px-2 text-xs',
  md: 'h-7 px-3 text-sm',
};

export function Tag({ children, variant = 'default', size = 'sm', icon: Icon, className }: TagProps) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1 rounded-full font-medium',
      tagVariants[variant],
      tagSizes[size],
      className
    )}>
      {Icon && <Icon className="h-3 w-3" />}
      {children}
    </span>
  );
}