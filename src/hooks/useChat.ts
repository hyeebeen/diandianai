import { useState, useEffect } from 'react'
import { supabase } from '@/integrations/supabase/client'
import { ChatMessage } from '@/types/logistics'

export function useChat(loadId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)

  console.log('useChat called with loadId:', loadId);

  const fetchMessages = async () => {
    if (!loadId) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true)
      const { data, error } = await supabase
        .from('chat_messages')
        .select('*')
        .eq('load_id', loadId)
        .order('created_at', { ascending: true })

      if (error) throw error

      const transformedMessages = data.map(msg => ({
        id: msg.id,
        role: msg.role as 'human' | 'agent' | 'system',
        content: msg.content,
        timestamp: msg.timestamp
      }))

      setMessages(transformedMessages)
    } catch (err) {
      console.error('获取聊天记录失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async (content: string) => {
    if (!content.trim()) return

    try {
      setSending(true)

      // 添加用户消息到数据库
      const { error: insertError } = await supabase
        .from('chat_messages')
        .insert({
          load_id: loadId,
          role: 'human',
          content: content.trim(),
          timestamp: new Date().toLocaleTimeString('zh-CN', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })
        })

      if (insertError) throw insertError

      // 调用AI接口
      const { data: aiResponse, error: aiError } = await supabase.functions
        .invoke('chat-ai', {
          body: {
            message: content,
            loadId: loadId
          }
        })

      if (aiError) throw aiError

      // 添加AI回复到数据库
      if (aiResponse.success) {
        const { error: aiInsertError } = await supabase
          .from('chat_messages')
          .insert({
            load_id: loadId,
            role: 'agent',
            content: aiResponse.message,
            timestamp: new Date().toLocaleTimeString('zh-CN', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })
          })

        if (aiInsertError) throw aiInsertError
      }

      // 刷新消息列表
      await fetchMessages()

    } catch (err) {
      console.error('发送消息失败:', err)
      // 可以添加错误提示
    } finally {
      setSending(false)
    }
  }

  useEffect(() => {
    if (loadId) {
      fetchMessages()
    }
  }, [loadId])

  return { messages, loading, sending, sendMessage, refetch: fetchMessages }
}