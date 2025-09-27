import { Load } from '@/types/logistics';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tag } from './Tag';
import { cn } from '@/lib/utils';

interface LoadDetailsCardProps {
  load: Load;
  className?: string;
}

export function LoadDetailsCard({ load, className }: LoadDetailsCardProps) {
  const details = [
    { label: '客户', value: load.customer },
    { label: '运输方式', value: load.mode },
    { label: '车辆设备', value: load.equipment },
    { label: '重量', value: load.weight },
    { label: '货物类型', value: load.commodity },
    { label: '包装方式', value: load.packingType },
  ];

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-4">
        <CardTitle className="text-lg">运单详情</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-x-8 gap-y-4">
          {details.map((detail, index) => (
            <div key={index} className="space-y-1">
              <div className="text-sm font-medium text-muted-foreground">
                {detail.label}
              </div>
              <div className="text-sm text-foreground">
                {detail.value}
              </div>
            </div>
          ))}
        </div>
        
        {load.notes && (
          <div className="mt-6 pt-4 border-t">
            <div className="text-sm font-medium text-muted-foreground mb-2">
              备注
            </div>
            <div className="text-sm text-foreground leading-relaxed">
              {load.notes}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}