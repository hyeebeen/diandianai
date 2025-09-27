import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { corsHeaders } from '../_shared/cors.ts'

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { message, loadId } = await req.json()
    
    // Get Kimi API key from secrets
    const kimiApiKey = Deno.env.get('KIMI_API_KEY')
    if (!kimiApiKey) {
      throw new Error('KIMI_API_KEY not configured')
    }

    // Call Kimi API
    const response = await fetch('https://api.moonshot.cn/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${kimiApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'moonshot-v1-8k',
        messages: [
          {
            role: 'system',
            content: `你是一个专业的物流助手小智，负责协助用户处理运单相关事务。你需要：
1. 用友好、专业的语气回答用户关于物流运输的问题
2. 提供运单状态、路线、时间等相关信息
3. 协助解决运输过程中的问题
4. 给出专业的物流建议
当前运单ID: ${loadId}
请用中文回答，保持简洁专业。`
          },
          {
            role: 'user',
            content: message
          }
        ],
        temperature: 0.7,
        max_tokens: 800
      })
    })

    if (!response.ok) {
      throw new Error(`Kimi API error: ${response.status}`)
    }

    const data = await response.json()
    const aiMessage = data.choices[0]?.message?.content || '抱歉，我现在无法处理您的请求，请稍后再试。'

    return new Response(
      JSON.stringify({ 
        message: aiMessage,
        success: true 
      }),
      { 
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        } 
      }
    )

  } catch (error) {
    console.error('Error:', error)
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        success: false 
      }),
      { 
        status: 500,
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        } 
      }
    )
  }
})