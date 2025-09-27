import { useState } from 'react';
import { mockLoads, mockChatMessages } from '@/data/mockData';
import { Load, StepperStep } from '@/types/logistics';
import { Sidebar } from '@/components/Sidebar';
import { LoadList } from '@/components/LoadList';
import { Stepper } from '@/components/Stepper';
import { RouteCard } from '@/components/RouteCard';
import { LoadDetailsCard } from '@/components/LoadDetailsCard';
import { ChatPanel } from '@/components/ChatPanel';
import { Star, StarOff } from 'lucide-react';
import { Button } from '@/components/ui/button';

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
  const [selectedLoadId, setSelectedLoadId] = useState<string>(mockLoads[2].id); // Default to in-transit load
  const [isFavorited, setIsFavorited] = useState(false);
  
  const selectedLoad = mockLoads.find(load => load.id === selectedLoadId);
  
  if (!selectedLoad) {
    return <div>Load not found</div>;
  }

  const currentStep = getStepperProgress(selectedLoad.status);

  return (
    <div className="h-screen bg-background flex">
      {/* Left Sidebar */}
      <Sidebar />
      
      {/* Load List */}
      <LoadList 
        loads={mockLoads}
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
      <ChatPanel messages={mockChatMessages} />
    </div>
  );
};

export default Index;