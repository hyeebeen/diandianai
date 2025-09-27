import { Load } from '@/types/logistics';
import { RouteMap } from './RouteMap';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MapPin, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RouteCardProps {
  load: Load;
  className?: string;
}

export function RouteCard({ load, className }: RouteCardProps) {
  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-4">
        <CardTitle className="text-lg">Route</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Map */}
        <RouteMap load={load} className="rounded-lg overflow-hidden border" />
        
        {/* Stops List */}
        <div className="space-y-3">
          {load.stops.map((stop, index) => (
            <div key={stop.id} className="flex items-start gap-3">
              {/* Step Number */}
              <div className={cn(
                'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5',
                stop.type === 'pickup' ? 'bg-emerald-500 text-white' : 'bg-blue-500 text-white'
              )}>
                {index + 1}
              </div>
              
              {/* Stop Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium capitalize text-sm">
                    {stop.type}
                  </span>
                </div>
                
                <div className="text-sm text-foreground">
                  {stop.address}
                </div>
                <div className="text-sm text-muted-foreground">
                  {stop.city}, {stop.state} {stop.zipCode}
                </div>
                
                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {stop.date}, {stop.timeWindow}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="text-xs text-muted-foreground pt-2 border-t">
          <button className="text-primary hover:underline">
            See more
          </button>
        </div>
      </CardContent>
    </Card>
  );
}