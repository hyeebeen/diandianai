import { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { ChatMessage } from '@/types/logistics';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { MessageBubble } from './MessageBubble';
import { Send, Paperclip, Loader2 } from 'lucide-react';
import { aiService } from '@/services/aiService';
import { useAIMessages } from '@/hooks/useSSE';
import { useAuth } from '@/contexts/AuthContext';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ChatPanelProps {
  className?: string;
  shipmentId?: string;
}

export function ChatPanel({ className, shipmentId }: ChatPanelProps) {
  const { user } = useAuth();
  const [inputValue, setInputValue] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // SSE real-time messages
  const {
    messages: sseMessages,
    isTyping,
    connectionStatus,
    isConnected
  } = useAIMessages(conversationId);

  // Initialize conversation
  useEffect(() => {
    const initializeConversation = async () => {
      if (!user) return;

      try {
        const conversation = await aiService.createConversation({
          context_type: 'shipment',
          context_id: shipmentId || 'dashboard',
          metadata: {
            user_id: user.id,
            shipment_id: shipmentId
          }
        });
        setConversationId(conversation.id);

        // Load conversation history
        const history = await aiService.getConversationHistory(conversation.id);
        // Check if history is an array (actual backend format) or has messages property (future format)
        const messages = Array.isArray(history) ? history : (history.messages || []);
        setLocalMessages(messages.map(msg => ({
          id: msg.id,
          content: msg.content,
          sender: (msg.sender || msg.role) === 'user' ? 'user' : 'assistant',
          timestamp: msg.timestamp,
          type: 'text'
        })));
      } catch (error) {
        console.error('Failed to initialize conversation:', error);
        setError('无法初始化聊天对话');
      }
    };

    initializeConversation();
  }, [user, shipmentId]);

  // Merge local messages with SSE messages
  const allMessages = [...localMessages, ...sseMessages.map(sseMsg => ({
    id: sseMsg.message_id,
    content: sseMsg.content,
    sender: sseMsg.role === 'user' ? 'user' : 'assistant',
    timestamp: sseMsg.timestamp,
    type: 'text' as const
  }))];

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [allMessages, isTyping]);

  const handleSend = async () => {
    if (!inputValue.trim() || !conversationId || isLoading) return;

    const messageContent = inputValue;
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Add user message immediately
      const userMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        content: messageContent,
        sender: 'user',
        timestamp: new Date().toISOString(),
        type: 'text'
      };
      setLocalMessages(prev => [...prev, userMessage]);

      // Send message to AI
      await aiService.sendMessageToConversation(conversationId, {
        content: messageContent,
        message_type: 'text'
      });

      // Response will come via SSE
    } catch (error: any) {
      console.error('Failed to send message:', error);
      setError(error.message || '发送消息失败，请重试');

      // Remove the optimistically added message on error
      setLocalMessages(prev => prev.filter(msg => msg.id !== `temp-${Date.now()}`));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const generateSummary = async () => {
    if (!conversationId) return;

    try {
      setIsLoading(true);
      await aiService.sendMessageToConversation(conversationId, {
        content: '请为当前运单生成摘要和关键洞察',
        message_type: 'summary_request'
      });
    } catch (error) {
      console.error('Failed to generate summary:', error);
      setError('生成摘要失败');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={cn('w-[380px] bg-card border-l flex flex-col h-full', className)}>
      <Tabs defaultValue="chat" className="flex flex-col h-full">
        <div className="border-b px-4 pt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="chat" className="relative">
              聊天
              {!isConnected && (
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full" />
              )}
            </TabsTrigger>
            <TabsTrigger value="summary">摘要</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="chat" className="flex-1 flex flex-col mt-0">
          {/* Error Alert */}
          {error && (
            <div className="p-4 pb-0">
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {allMessages.length === 0 && !isLoading ? (
              <div className="text-center text-gray-500 mt-8">
                <div className="text-lg mb-2">👋</div>
                <p className="text-sm">
                  您好！我是点点精灵，您的物流助手。
                  <br />
                  有什么可以帮助您的吗？
                </p>
              </div>
            ) : (
              <>
                {allMessages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}

                {/* Typing Indicator */}
                {isTyping && (
                  <div className="flex items-center space-x-2 text-gray-500">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                    <span className="text-sm">点点精灵正在输入...</span>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t p-4">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="flex-shrink-0"
                disabled={!conversationId}
              >
                <Paperclip className="h-4 w-4" />
              </Button>

              <div className="flex-1 relative">
                <Input
                  placeholder={conversationId ? "询问点点精灵..." : "正在连接..."}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={!conversationId || isLoading}
                  className="pr-10"
                />
                <Button
                  size="sm"
                  variant="ghost"
                  className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                  onClick={handleSend}
                  disabled={!conversationId || isLoading || !inputValue.trim()}
                >
                  {isLoading ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Send className="h-3 w-3" />
                  )}
                </Button>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="summary" className="flex-1 flex flex-col">
          <div className="flex-1 p-4">
            <div className="mb-4">
              <Button
                onClick={generateSummary}
                disabled={!conversationId || isLoading}
                size="sm"
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    生成中...
                  </>
                ) : (
                  '生成运单摘要'
                )}
              </Button>
            </div>

            <div className="text-sm text-muted-foreground">
              运单摘要和关键洞察将在此处显示。
              {shipmentId && (
                <div className="mt-2 text-xs">
                  当前运单: {shipmentId}
                </div>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}