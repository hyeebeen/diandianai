# Supabase 配置指南

## 当前状态

✅ **页面已修复** - 现在使用 mock 数据正常显示  
🔧 **待配置** - Supabase 数据库连接和 AI 聊天功能  

## 配置步骤

### 1. 获取 Supabase 项目信息

1. 登录到您的 [Supabase 仪表板](https://supabase.com/dashboard)
2. 选择您的项目（或创建新项目）
3. 在项目设置中找到 API 配置：
   - 项目 URL（格式：`https://xxx.supabase.co`）
   - anon public key（以 `eyJ...` 开头的长字符串）

### 2. 更新连接配置

在 `src/lib/supabase.ts` 文件中，将第3-4行的占位符替换为您的真实信息：

```typescript
// 替换这些占位符：
const supabaseUrl = 'https://your-project.supabase.co'  // ← 替换为您的项目URL
const supabaseAnonKey = 'your-anon-key'                // ← 替换为您的anon key
```

### 3. 创建数据库表

在 Supabase 项目的 SQL 编辑器中执行 `database_schema.sql` 文件中的所有 SQL 语句。

### 4. 启用真实数据连接

配置完成后，在 `src/pages/Index.tsx` 中：
- 取消注释第4-5行的 import 语句
- 注释第2行的 mockLoads import
- 恢复 useLoads 和 useChat hooks 的使用

### 5. 配置 AI 聊天功能

1. 确保 KIMI_API_KEY 已在 Supabase Secrets 中设置
2. 部署边缘函数：
   ```bash
   supabase functions deploy chat-ai
   ```

## 验证配置

配置完成后，您应该能够：
- 看到数据库中的真实运单数据
- 在聊天窗口与 AI 助手对话
- 切换运单时聊天记录正确更新

## 当前的临时状态

- 页面使用 mock 数据正常显示
- 聊天功能暂时禁用（显示配置提示）
- 所有 UI 组件和交互都正常工作

需要帮助配置 Supabase？我可以协助您完成每个步骤！