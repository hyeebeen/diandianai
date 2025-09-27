import { useState, useEffect } from 'react';
import { mockLoads } from '@/data/mockData';
import { StepperStep } from '@/types/logistics';
// import { useLoads } from '@/hooks/useLoads';
// import { useChat } from '@/hooks/useChat';
import { Sidebar } from '@/components/Sidebar';
import { LoadList } from '@/components/LoadList';
import { Stepper } from '@/components/Stepper';
import { RouteCard } from '@/components/RouteCard';
import { LoadDetailsCard } from '@/components/LoadDetailsCard';
import { ChatPanel } from '@/components/ChatPanel';
import { Star, StarOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import React from 'react';

const stepperSteps: StepperStep[] = ['任务分配', '取货', '运输中', '送货'];

const getStepperProgress = (status: string): number => {
  switch (status) {
    case 'unassigned':
      return 0;
    case 'assigned':
      return 0;
    case 'dispatched':
      return 1;
    case 'in-transit':
      return 2;
    case 'at-pickup':
      return 1;
    case 'loaded':
      return 2;
    case 'delivered':
      return 3;
    default:
      return 0;
  }
};

const Index = () => {
  // 暂时使用 mock 数据，直到 Supabase 配置完成
  const loads = mockLoads;
  const loading = false;
  const [selectedLoadId, setSelectedLoadId] = useState<string>(mockLoads[2].id);
  const [isFavorited, setIsFavorited] = useState(false);
  
  const selectedLoad = loads.find(load => load.id === selectedLoadId);
  
  // 暂时使用 mock 消息数据
  const messages = [
    { id: '1', role: 'system' as const, content: '运单已分配，正在等待Supabase配置', timestamp: '10:00' },
    { id: '2', role: 'agent' as const, content: '请先配置Supabase连接，然后就可以使用真实的AI聊天功能了', timestamp: '10:01' }
  ];
  
  if (loading) {
    return <div className="h-screen bg-background flex items-center justify-center">
      <div className="text-muted-foreground">加载中...</div>
    </div>;
  }

  if (!selectedLoad) {
    return <div className="h-screen bg-background flex items-center justify-center">
      <div className="text-muted-foreground">运单未找到</div>
    </div>;
  }

  const currentStep = getStepperProgress(selectedLoad.status);

  return (
    <div className="h-screen bg-background flex">
      {/* Left Sidebar */}
      <Sidebar />
      
      {/* Load List */}
      <LoadList 
        loads={loads}
        selectedLoadId={selectedLoadId}
        onLoadSelect={setSelectedLoadId}
      />
      
      {/* Main Content */}
      <div className="w-[680px] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b bg-card">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold">{selectedLoad.id}</h1>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsFavorited(!isFavorited)}
            >
              {isFavorited ? (
                <Star className="h-4 w-4 fill-current text-yellow-500" />
              ) : (
                <StarOff className="h-4 w-4" />
              )}
            </Button>
          </div>
          
          {/* Stepper */}
          <Stepper 
            steps={stepperSteps} 
            currentStep={currentStep}
          />
        </div>
        
        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <RouteCard load={selectedLoad} />
          <LoadDetailsCard load={selectedLoad} />
        </div>
      </div>
      
      {/* Right Chat Panel */}
      <ChatPanel messages={messages} loadId={selectedLoadId} />
    </div>
  );
};

export default Index;