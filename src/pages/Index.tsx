import { useState, useEffect } from 'react';
import { Load, StepperStep } from '@/types/logistics';
import { Sidebar } from '@/components/Sidebar';
import { LoadList } from '@/components/LoadList';
import { Stepper } from '@/components/Stepper';
import { RouteCard } from '@/components/RouteCard';
import { LoadDetailsCard } from '@/components/LoadDetailsCard';
import { ChatPanel } from '@/components/ChatPanel';
import { Star, StarOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { shipmentService } from '@/services/shipmentService';
import { transformShipmentToLoad } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

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
  const { user } = useAuth();
  const [selectedLoadId, setSelectedLoadId] = useState<string | null>(null);
  const [selectedLoad, setSelectedLoad] = useState<Load | null>(null);
  const [isFavorited, setIsFavorited] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Load selected shipment details
  useEffect(() => {
    const loadShipmentDetails = async () => {
      if (!selectedLoadId || !user) return;

      try {
        setIsLoading(true);

        // For development environment, use test endpoint to get shipment details
        if (import.meta.env.DEV || window.location.hostname === 'localhost') {
          const response = await shipmentService.getLoads();
          const load = response.items.find(item => item.id === selectedLoadId);
          if (load) {
            setSelectedLoad(load);
          } else {
            throw new Error(`运单 ${selectedLoadId} 不存在`);
          }
        } else {
          // Production environment: use the normal API
          const shipment = await shipmentService.getShipmentByNumber(selectedLoadId);
          const load = transformShipmentToLoad(shipment);
          setSelectedLoad(load);
        }
      } catch (error) {
        console.error('Failed to load shipment details:', error);
        setSelectedLoad(null);
      } finally {
        setIsLoading(false);
      }
    };

    loadShipmentDetails();
  }, [selectedLoadId, user]);

  const currentStep = selectedLoad ? getStepperProgress(selectedLoad.status) : 0;

  return (
    <div className="h-screen bg-background flex">
      {/* Left Sidebar */}
      <Sidebar />
      
      {/* Load List */}
      <LoadList
        selectedLoadId={selectedLoadId}
        onLoadSelect={setSelectedLoadId}
      />
      
      {/* Main Content */}
      <div className="w-[680px] flex flex-col">
        {selectedLoad ? (
          <>
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
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            {isLoading ? (
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
                <p className="text-gray-500">加载运单详情...</p>
              </div>
            ) : (
              <div className="text-center text-gray-500">
                <div className="text-6xl mb-4">📦</div>
                <h2 className="text-xl font-medium mb-2">选择运单</h2>
                <p className="text-sm">
                  从左侧列表中选择一个运单查看详情
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right Chat Panel */}
      <ChatPanel shipmentId={selectedLoadId || undefined} />
    </div>
  );
};

export default Index;