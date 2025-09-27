import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChatMessage } from '@/types/logistics';
import { useChat } from '@/hooks/useChat';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { MessageBubble } from './MessageBubble';
import { Send, Paperclip } from 'lucide-react';

interface ChatPanelProps {
  messages: ChatMessage[];
  loadId: string;
  className?: string;
}

export function ChatPanel({ messages, loadId, className }: ChatPanelProps) {
  const [inputValue, setInputValue] = useState('');
  const { sendMessage, sending } = useChat(loadId);

  const handleSend = async () => {
    if (inputValue.trim() && !sending) {
      await sendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={cn('w-[380px] bg-card border-l flex flex-col h-full', className)}>
      <Tabs defaultValue="chat" className="flex flex-col h-full">
        <div className="border-b px-4 pt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="chat">聊天</TabsTrigger>
            <TabsTrigger value="summary">摘要</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="chat" className="flex-1 flex flex-col mt-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>

          {/* Input */}
          <div className="border-t p-4">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="flex-shrink-0"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
              
              <div className="flex-1 relative">
                <Input
                  placeholder="询问小智"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="pr-10"
                />
                <Button
                  size="sm"
                  variant="ghost"
                  className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                  onClick={handleSend}
                  disabled={sending}
                >
                  <Send className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="summary" className="flex-1 p-4">
          <div className="text-sm text-muted-foreground">
            运单摘要和关键洞察将在此处显示。
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}