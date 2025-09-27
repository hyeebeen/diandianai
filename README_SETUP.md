# 物流调度控制台 - 后端集成指南

## 已完成的集成内容

✅ **数据库架构** - 运单表 (loads) 和聊天消息表 (chat_messages)  
✅ **AI 聊天功能** - 使用 Kimi K2 模型的边缘函数  
✅ **React Hooks** - useLoads 和 useChat 钩子连接 Supabase  
✅ **界面更新** - 聊天面板支持真实 AI 对话  

## 设置步骤

### 1. 配置 Supabase 项目

1. 在 Supabase 项目设置中获取：
   - 项目 URL
   - anon key

2. 更新 `src/lib/supabase.ts` 文件中的连接信息：
   ```typescript
   const supabaseUrl = 'https://your-project-url.supabase.co'
   const supabaseAnonKey = 'your-anon-key'
   ```

### 2. 创建数据库表

在 Supabase 项目的 SQL 编辑器中运行 `database_schema.sql` 文件中的所有 SQL 语句。

### 3. 配置 AI API 密钥

Kimi API 密钥已通过 Lovable 的密钥管理添加到 Supabase Secrets 中：
- 密钥名称：`KIMI_API_KEY`
- 在 Supabase 项目设置 → Edge Functions → Secrets 中可以看到

### 4. 部署边缘函数

边缘函数 `chat-ai` 已创建在 `supabase/functions/chat-ai/index.ts`，需要部署到 Supabase：

```bash
# 在项目根目录运行
supabase functions deploy chat-ai
```

## 功能说明

### 数据库表结构

**loads 表** - 存储运单信息：
- 基本信息：运单号、起点、终点、状态、日期
- 物流信息：客户、车辆、司机、重量、货物类型  
- 地理信息：取货/送货地址和坐标
- 特殊要求：温控、装卸注意事项

**chat_messages 表** - 存储聊天记录：
- 与运单关联的消息
- 支持用户、AI助手、系统三种角色
- 包含时间戳和内容

### AI 聊天功能

- 使用 Moonshot AI (Kimi) 的 K2 模型
- 专门针对物流场景优化的提示词
- 支持运单相关问题的智能回答
- 自动保存聊天记录到数据库

### React 组件集成

- **useLoads Hook** - 从数据库加载运单数据
- **useChat Hook** - 管理聊天消息和 AI 对话
- **ChatPanel** - 更新后支持真实消息发送
- **Index 页面** - 使用真实数据替代 mock 数据

## 测试建议

1. **数据加载测试** - 确认运单列表正确显示数据库中的数据
2. **AI 对话测试** - 在聊天窗口发送消息，验证 AI 回复
3. **数据持久化测试** - 刷新页面后聊天记录应该保持
4. **运单切换测试** - 切换不同运单时聊天记录应该对应更新

## 故障排除

- 检查 Supabase 连接配置
- 确认数据库表和数据已正确创建
- 验证 KIMI_API_KEY 密钥已正确设置
- 查看浏览器控制台和 Supabase 日志获取错误信息