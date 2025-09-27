import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Load } from '@/types/logistics';
import { LoadListItem } from './LoadListItem';
import { Search, Filter } from 'lucide-react';
import { Input } from '@/components/ui/input';

interface LoadListProps {
  loads: Load[];
  selectedLoadId?: string;
  onLoadSelect: (loadId: string) => void;
  className?: string;
}

export function LoadList({ loads, selectedLoadId, onLoadSelect, className }: LoadListProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredLoads = loads.filter(load => 
    load.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    load.origin.toLowerCase().includes(searchQuery.toLowerCase()) ||
    load.destination.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className={cn('w-[340px] bg-card border-r flex flex-col', className)}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Loads</h2>
          <div className="text-sm text-muted-foreground">
            1-10 of 123
          </div>
        </div>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Type to search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-9"
          />
          <Filter className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        </div>
      </div>

      {/* Load List */}
      <div className="flex-1 overflow-y-auto">
        {filteredLoads.map((load) => (
          <LoadListItem
            key={load.id}
            load={load}
            isSelected={selectedLoadId === load.id}
            onClick={() => onLoadSelect(load.id)}
          />
        ))}
      </div>
    </div>
  );
}