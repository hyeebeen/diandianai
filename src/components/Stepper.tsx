import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';
import { StepperStep } from '@/types/logistics';

interface StepperProps {
  steps: StepperStep[];
  currentStep: number;
  className?: string;
}

export function Stepper({ steps, currentStep, className }: StepperProps) {
  return (
    <div className={cn('flex items-center justify-between', className)}>
      {steps.map((step, index) => (
        <div key={step} className="flex items-center flex-1">
          <div className="flex items-center">
            {/* Step Circle */}
            <div className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
              index < currentStep 
                ? 'bg-primary text-primary-foreground' 
                : index === currentStep
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground'
            )}>
              {index < currentStep ? (
                <Check className="h-4 w-4" />
              ) : (
                index + 1
              )}
            </div>

            {/* Step Label */}
            <span className={cn(
              'ml-2 text-sm font-medium',
              index <= currentStep ? 'text-foreground' : 'text-muted-foreground'
            )}>
              {step}
            </span>
          </div>

          {/* Progress Line */}
          {index < steps.length - 1 && (
            <div className="flex-1 mx-4">
              <div className="h-0.5 bg-muted">
                <div 
                  className={cn(
                    'h-full transition-all duration-300',
                    index < currentStep ? 'bg-primary w-full' : 'bg-muted w-0'
                  )}
                />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}