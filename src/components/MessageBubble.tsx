import { cn } from '@/lib/utils';
import { ChatMessage } from '@/types/logistics';
import { AttachmentCard } from './AttachmentCard';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Bot, User, Settings } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isSystem = message.role === 'system';
  const isAgent = message.role === 'agent';
  const isHuman = message.role === 'human';

  // Don't render system messages with attachments differently
  if (message.attachments && message.attachments.length > 0) {
    return (
      <div className="space-y-2">
        {message.attachments.map((attachment) => (
          <AttachmentCard key={attachment.id} attachment={attachment} />
        ))}
      </div>
    );
  }

  if (isSystem) {
    return (
      <div className="flex items-start gap-3">
        <Avatar className="h-6 w-6 mt-0.5">
          <AvatarFallback className="bg-emerald-100 text-emerald-600">
            <Settings className="h-3 w-3" />
          </AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <div className="bg-emerald-50 text-emerald-800 rounded-lg p-3 text-sm">
            {message.content}
          </div>
          {message.timestamp && (
            <div className="text-xs text-muted-foreground mt-1">
              {message.timestamp}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      'flex gap-3',
      isHuman ? 'justify-end' : 'justify-start'
    )}>
      {!isHuman && (
        <Avatar className="h-6 w-6 mt-0.5">
          <AvatarFallback className="bg-blue-100 text-blue-600">
            <Bot className="h-3 w-3" />
          </AvatarFallback>
        </Avatar>
      )}
      
      <div className={cn(
        'max-w-[80%] space-y-1',
        isHuman ? 'items-end' : 'items-start'
      )}>
        <div className={cn(
          'rounded-lg p-3 text-sm',
          isHuman 
            ? 'bg-primary text-primary-foreground ml-auto' 
            : 'bg-muted text-muted-foreground'
        )}>
          {message.content}
        </div>
        
        {message.timestamp && (
          <div className={cn(
            'text-xs text-muted-foreground',
            isHuman ? 'text-right' : 'text-left'
          )}>
            {message.timestamp}
          </div>
        )}
      </div>
      
      {isHuman && (
        <Avatar className="h-6 w-6 mt-0.5">
          <AvatarFallback className="bg-gray-100 text-gray-600">
            <User className="h-3 w-3" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}