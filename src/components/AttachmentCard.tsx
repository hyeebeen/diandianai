import { cn } from '@/lib/utils';
import { Attachment } from '@/types/logistics';
import { Phone, FileText, Image, Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface AttachmentCardProps {
  attachment: Attachment;
  className?: string;
}

export function AttachmentCard({ attachment, className }: AttachmentCardProps) {
  const getIcon = () => {
    switch (attachment.type) {
      case 'call':
        return <Phone className="h-4 w-4" />;
      case 'document':
        return <FileText className="h-4 w-4" />;
      case 'image':
        return <Image className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getBackgroundColor = () => {
    switch (attachment.type) {
      case 'call':
        return 'bg-blue-50 border-blue-200';
      case 'document':
        return 'bg-gray-50 border-gray-200';
      case 'image':
        return 'bg-purple-50 border-purple-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <Card className={cn('border', getBackgroundColor(), className)}>
      <CardContent className="p-3">
        <div className="flex items-center gap-3">
          <div className={cn(
            'p-2 rounded-lg',
            attachment.type === 'call' ? 'bg-blue-100 text-blue-600' :
            attachment.type === 'document' ? 'bg-gray-100 text-gray-600' :
            'bg-purple-100 text-purple-600'
          )}>
            {getIcon()}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm text-foreground">
              {attachment.name}
            </div>
            
            {attachment.duration && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                <Clock className="h-3 w-3" />
                {attachment.duration}
              </div>
            )}
            
            {attachment.participants && (
              <div className="text-xs text-muted-foreground mt-1">
                {attachment.participants.join(' • ')}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}