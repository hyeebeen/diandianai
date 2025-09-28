# Quickstart Guide: AI驱动的物流管理数字化平台

**技术栈版本**: 基于Diandian项目验证的生产级配置

## 开发环境设置

### 前置条件 (更新)
- **Python 3.11+** (推荐 3.11 获取uvloop最佳性能)
- **uv 0.5.0+** (强制要求，替代pip/poetry)
- **PostgreSQL 15+** (推荐 15版本获取更好的RLS性能)
- **Redis 7+**
- **RabbitMQ 3.12+** (替代Temporal工作流引擎)
- **Docker & Docker Compose**
- **Git**

### 安装uv包管理器
```bash
# 安装uv (必须第一步)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或者使用pip安装
pip install uv

# 验证安装
uv --version  # 应该显示 0.5.0+
```

### 快速项目初始化 (基于uv)
```bash
# 克隆项目
git clone <repository-url>
cd diandianai

# 使用uv初始化Python环境
# uv会自动管理Python版本和虚拟环境
uv venv --python 3.11
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装后端依赖 (比pip快10-100倍)
uv pip install -e ".[dev]"  # 从 pyproject.toml 安装

# 如果没有pyproject.toml，使用requirements.txt
# uv pip install -r requirements.txt

# 初始化服务依赖
docker-compose -f docker-compose.dev.yml up -d

# 运行数据库迁移
alembic upgrade head

# 启动Celery工作者 (新增)
celery -A app.celery worker --loglevel=info

# 在另一个终端启动Celery Beat (定时任务)
celery -A app.celery beat --loglevel=info
```

### pyproject.toml 配置示例
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "diandianai"
version = "0.1.0"
description = "AI驱动的物流管理数字化平台"
requires-python = ">=3.11"
dependencies = [
    # 核心框架 (基于Diandian验证)
    "fastapi==0.104.0",
    "uvicorn[standard]==0.24.0",
    "uvloop==0.19.0",  # 性能关键

    # AI推理 (替代LangChain)
    "instructor==1.11.3",
    "openai==1.58.1",
    "pydantic==2.10.3",

    # 工作流引擎 (替代Temporal)
    "celery[redis]==5.5.3",
    "kombu==5.3.4",

    # 数据库和缓存
    "sqlalchemy==2.0.31",
    "asyncpg==0.29.0",
    "alembic==1.13.1",
    "redis==5.0.8",

    # 实时通信 (替代WebSocket)
    "sse-starlette==3.0.2",

    # 其他工具
    "pydantic-settings==2.5.2",
    "python-multipart==0.0.9",
    "python-jose[cryptography]==3.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.2",
    "pytest-asyncio==0.24.0",
    "httpx==0.27.0",
    "black==24.8.0",
    "ruff==0.6.3",
    "mypy==1.11.1",
]
```

### 环境变量配置 (更新)
```env
# 数据库配置 (多租户支持)
DATABASE_URL="postgresql://user:password@localhost:5432/logistics_db"
REDIS_URL="redis://localhost:6379/0"

# RabbitMQ配置 (替代Temporal)
RABBITMQ_URL="amqp://guest:guest@localhost:5672//"
CELERY_BROKER_URL="pyamqp://guest@localhost:5672//"
CELERY_RESULT_BACKEND="redis://localhost:6379/1"

# JWT配置
JWT_SECRET="your-jwt-secret-key-min-32-chars"
JWT_ALGORITHM="HS256"
JWT_EXPIRES_IN=3600  # 1小时
REFRESH_TOKEN_EXPIRES_IN=604800  # 7天

# AI模型配置 (多模型支持)
# OpenAI
OPENAI_API_KEY="sk-your-openai-api-key"
OPENAI_BASE_URL="https://api.openai.com/v1"
OPENAI_DEFAULT_MODEL="gpt-4o-mini"  # 成本优化

# Claude
CLAUDE_API_KEY="sk-ant-your-claude-api-key"
CLAUDE_BASE_URL="https://api.anthropic.com"

# 国产AI模型 (可选)
WENXIN_API_KEY="your-wenxin-api-key"
ZHIPU_API_KEY="your-zhipu-api-key"

# 企业微信配置 (替代公众号)
WECOM_CORP_ID="your-wecom-corp-id"
WECOM_CORP_SECRET="your-wecom-corp-secret"
WECOM_AGENT_ID="your-wecom-agent-id"

# G7 GPS配置
G7_API_KEY="your-g7-api-key"
G7_BASE_URL="https://openapi.g7.com.cn"
G7_WEBHOOK_SECRET="your-g7-webhook-secret"

# 服务器配置 (性能优化)
PORT=8000
ENVIRONMENT=development
WORKERS=4  # CPU核数
UVLOOP_ENABLED=true  # 启用uvloop
PROCESS_POOL_SIZE=4  # CPU密集任务进程池

# 多租户配置
TENANT_ISOLATION_ENABLED=true
MAX_TENANTS=50
MAX_USERS_PER_TENANT=100

# 数据保留策略 (基于需求简化)
DATA_RETENTION_MONTHS=6
GPS_DATA_RETENTION_MONTHS=3
AI_LOGS_RETENTION_MONTHS=6

# 性能配置
AI_RESPONSE_TIMEOUT=5000  # 5秒
MAX_CONCURRENT_ORDERS=100
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Python环境
PYTHONPATH=/app
PYTHONUNBUFFERED=1
```

## 核心功能验证流程

### 1. 用户认证测试

#### 1.1 启动后端服务 (更新)
```bash
# 启动FastAPI后端 (使用uvloop优化)
source .venv/bin/activate

# 生产模式启动 (推荐)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop uvloop --workers 4

# 或者开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --loop uvloop

# 访问API文档
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

#### 1.2 管理员登录
```bash
# 创建测试管理员用户
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "role": "admin"
  }'

# 管理员登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'

# 保存返回的access_token用于后续请求
export TOKEN="<your-access-token>"
```

#### 1.3 验证JWT认证
```bash
# 获取用户资料
curl -X GET http://localhost:8000/api/auth/profile \
  -H "Authorization: Bearer $TOKEN"

# 期望结果：返回用户详细信息
```

### 2. AI模型配置测试

#### 2.1 配置AI模型 (多模型支持)
```bash
# 创建成本优化的OpenAI配置
curl -X POST http://localhost:8000/api/ai/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenAI GPT-4o Mini 成本优化配置",
    "provider": "openai",
    "endpoint": "https://api.openai.com/v1",
    "apiKey": "sk-your-openai-api-key",
    "model": "gpt-4o-mini",
    "parameters": {
      "temperature": 0.1,
      "maxTokens": 4000
    },
    "taskTypes": ["text_extraction", "customer_service"]
  }'

# 添加Claude配置 (复杂任务)
curl -X POST http://localhost:8000/api/ai/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Claude 3 Sonnet 复杂任务配置",
    "provider": "claude",
    "endpoint": "https://api.anthropic.com",
    "apiKey": "sk-ant-your-claude-key",
    "model": "claude-3-sonnet-20240229",
    "parameters": {
      "temperature": 0.1,
      "maxTokens": 4000
    },
    "taskTypes": ["route_optimization", "complex_analysis"]
  }'

# 验证配置列表
curl -X GET http://localhost:8000/api/ai/config \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.2 测试AI对话 (基于Instructor)
```bash
# AI助手结构化对话测试
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我创建一个从北京到上海的运单，发件人张三 13800138000，收件人李四 13900139000，货物是电子产品",
    "channel": "web",
    "taskType": "shipment_creation"
  }'

# 期望结果 (基于Diandian项目验证)：
# - responseTime < 5000ms (调整为5秒)
# - 返回结构化的ShipmentRequest对象
# - 自动触发Celery工作流
# - 支持多模型路由和成本优化

# 测试连续对话
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "修改运费为800元",
    "channel": "web",
    "sessionId": "previous-session-id"
  }'

# 测试批量AI处理 (新增)
curl -X POST http://localhost:8000/api/ai/batch-process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"message": "查询运单 DD20241001001 状态", "taskType": "shipment_query"},
      {"message": "优化今天的送货路线", "taskType": "route_optimization"}
    ]
  }'
```

### 3. 运单管理测试

#### 3.1 创建运单
```bash
# 创建测试运单
curl -X POST http://localhost:8000/api/shipments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": {
      "name": "张三",
      "phone": "13800138000",
      "company": "北京物流有限公司"
    },
    "senderAddress": {
      "street": "中关村大街1号",
      "city": "北京市",
      "province": "北京市",
      "country": "中国",
      "coordinates": {
        "latitude": 39.9042,
        "longitude": 116.4074
      }
    },
    "receiver": {
      "name": "李四",
      "phone": "13900139000",
      "company": "上海货运公司"
    },
    "receiverAddress": {
      "street": "南京路100号",
      "city": "上海市",
      "province": "上海市",
      "country": "中国",
      "coordinates": {
        "latitude": 31.2304,
        "longitude": 121.4737
      }
    },
    "cargo": {
      "description": "电子产品",
      "weight": 25.5,
      "volume": 0.5,
      "quantity": 10,
      "unit": "箱",
      "value": 5000.00
    },
    "freight": 500.00
  }'

# 保存返回的shipmentId用于后续测试
export SHIPMENT_ID="<your-shipment-id>"
```

#### 3.2 查询运单详情
```bash
# 获取运单详情
curl -X GET http://localhost:8000/api/shipments/$SHIPMENT_ID \
  -H "Authorization: Bearer $TOKEN"

# 期望结果：返回完整的运单信息和状态历史
```

#### 3.3 更新运单状态
```bash
# 更新运单状态为"已提货"
curl -X PATCH http://localhost:8000/api/shipments/$SHIPMENT_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "picked_up",
    "notes": "货物已成功提取",
    "location": {
      "latitude": 39.9042,
      "longitude": 116.4074
    }
  }'
```

### 4. GPS追踪测试

#### 4.1 创建测试车辆
```bash
# 创建测试车辆（需要先实现车辆管理API）
curl -X POST http://localhost:8000/api/vehicles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plateNumber": "京A12345",
    "model": "东风货车",
    "capacity": {
      "maxWeight": 5000,
      "maxVolume": 20
    }
  }'

export VEHICLE_ID="<your-vehicle-id>"
```

#### 4.2 上报GPS位置
```bash
# 模拟GPS设备上报位置
curl -X POST http://localhost:8000/api/gps/locations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicleId": "'$VEHICLE_ID'",
    "coordinates": {
      "latitude": 39.9042,
      "longitude": 116.4074
    },
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")'",
    "speed": 60,
    "heading": 90,
    "accuracy": 5.0,
    "source": "g7_device"
  }'
```

#### 4.3 获取当前位置
```bash
# 获取车辆当前位置
curl -X GET http://localhost:8000/api/gps/vehicles/$VEHICLE_ID/current \
  -H "Authorization: Bearer $TOKEN"

# 期望结果：返回最新的GPS位置和车辆状态
```

### 5. 实时追踪测试 (替代WebSocket)

#### 5.1 Server-Sent Events (SSE) 连接测试
```javascript
// 前端SSE连接测试代码 (更高效)
const eventSource = new EventSource(
  `http://localhost:8000/api/stream/shipment/${shipmentId}?token=${token}`
);

eventSource.onopen = function() {
  console.log('SSE连接已建立');
};

eventSource.addEventListener('status_update', function(event) {
  const data = JSON.parse(event.data);
  console.log('收到运单状态更新:', data);
  // 更新UI显示
});

eventSource.addEventListener('gps_update', function(event) {
  const data = JSON.parse(event.data);
  console.log('收到GPS位置更新:', data);
  // 更新地图上的车辆位置
});

eventSource.onerror = function(error) {
  console.error('SSE错误:', error);
};

// 关闭连接
// eventSource.close();
```

#### 5.2 测试SSE性能
```bash
# 使用curl测试SSE连接
curl -N -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/stream/shipment/$SHIPMENT_ID"

# 期望结果：
# - 连接建立快速 (无WebSocket握手开销)
# - 自动重连支持
# - 企业网络友好 (标准HTTP)
```

### 6. 前端功能测试

#### 6.1 启动前端开发服务器
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 浏览器访问 http://localhost:5173
```

### 7. 工作流引擎测试 (新增)

#### 7.1 Celery工作流测试
```bash
# 测试POD收集工作流 (替代Temporal)
curl -X POST http://localhost:8000/api/workflows/pod-collection \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shipmentId": "'$SHIPMENT_ID'",
    "waitHours": 48,
    "reminderIntervals": [24, 12, 2],
    "escalationRules": {
      "maxRetries": 3,
      "retryInterval": 600
    }
  }'

# 查看任务状态
curl -X GET http://localhost:8000/api/workflows/status/$TASK_ID \
  -H "Authorization: Bearer $TOKEN"

# 期望结果：
# - 任务成功创建并加入Redis队列
# - 48小时后自动触发POD收集
# - 支持任务重试和升级机制
```

#### 7.2 批量GPS数据处理测试
```bash
# 测试批量GPS上报 (性能优化)
curl -X POST http://localhost:8000/api/gps/batch-locations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicleId": "'$VEHICLE_ID'",
    "locations": [
      {
        "coordinates": {"latitude": 39.9042, "longitude": 116.4074},
        "timestamp": "2024-01-01T10:00:00Z",
        "speed": 60,
        "heading": 90
      },
      {
        "coordinates": {"latitude": 39.9142, "longitude": 116.4174},
        "timestamp": "2024-01-01T10:01:00Z",
        "speed": 65,
        "heading": 92
      }
    ],
    "source": "g7_device"
  }'

# 期望结果：
# - 批量处理100个点位延迟 < 100ms
# - 自动触发实时位置更新
# - 支持时间分区存储优化
```

#### 7.3 AI模型路由测试
```bash
# 测试智能模型路由 (成本优化)
curl -X POST http://localhost:8000/api/ai/smart-routing \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我分析这个复杂的多地点送货路线问题",
    "taskComplexity": "high",
    "priority": "normal"
  }'

# 期望结果：
# - 自动选择Claude 3 Sonnet (复杂任务)
# - 简单任务自动路由到GPT-4o Mini (成本优化)
# - 支持预算控制和动态负载均衡
```

### 8. 前端功能测试 (简化)

#### 8.1 启动前端开发服务器
```bash
# 进入前端目录
cd frontend

# 安装依赖 (使用npm或yarn)
npm install
# 或者 yarn install

# 启动开发服务器
npm run dev
# 或者 yarn dev

# 浏览器访问 http://localhost:5173
```

#### 8.2 核心页面功能验证

**登录页面测试：**
1. 访问 http://localhost:5173/login
2. 输入管理员凭据登录
3. 验证JWT token存储
4. 验证自动重定向到仪表板

**运单管理页面测试：**
1. 访问 http://localhost:5173/shipments
2. 验证运单列表加载
3. 测试创建新运单功能
4. 测试运单状态更新
5. 验证搜索和过滤功能

**GPS追踪页面测试：**
1. 访问 http://localhost:5173/tracking
2. 验证地图组件加载
3. 测试实时位置更新
4. 验证历史轨迹回放功能

**AI助手页面测试：**
1. 访问 http://localhost:5173/ai-assistant
2. 测试对话界面
3. 验证响应时间<3秒
4. 测试运单创建集成

### 9. 性能测试 (基于Diandian指标)

#### 9.1 AI响应时间测试 (调整指标)
```bash
# 使用Apache Bench测试AI接口性能
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
   -p ai_request.json -T application/json \
   http://localhost:8000/api/ai/chat

# ai_request.json 内容：
# {"message": "查询运单状态", "channel": "web", "taskType": "shipment_query"}

# 期望结果 (基于Diandian调整)：
# - 简单查询：< 2秒 (GPT-4o Mini)
# - 复杂分析：< 5秒 (Claude 3 Sonnet)
# - 90%请求在SLA范围内
# - 支持语义缓存命中率 > 75%
```

#### 9.2 并发用户测试 (调整规模)
```bash
# 使用wrk测试并发性能
wrk -t12 -c100 -d30s --script=load_test.lua http://localhost:8000/api/shipments

# 期望结果 (基于10-50企业规模)：
# - 支持100并发订单处理
# - 50租户 x 100用户 = 5000总用户
# - 数据库查询延迟 < 50ms
# - uvloop性能提升 3-5x

# 测试多租户隔离性能
wrk -t8 -c50 -d30s \
  -H "X-Tenant-ID: tenant-001" \
  --script=tenant_isolation_test.lua \
  http://localhost:8000/api/shipments
```

### 10. 集成测试场景 (更新)

#### 10.1 完整业务流程测试 (基于新技术栈)
```bash
#!/bin/bash
# end_to_end_test.sh

# 1. 管理员登录并配置AI模型
echo "Step 1: 管理员登录..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier": "admin@example.com", "password": "admin123"}' \
  | jq -r '.accessToken')

# 2. 通过AI助手创建运单 (使用Instructor)
echo "Step 2: AI助手创建运单..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "创建从北京到上海的运单，发件人张三13800138000，收件人李四13900139000", "channel": "web", "taskType": "shipment_creation"}')

# 3. 验证运单创建
echo "Step 3: 验证运单创建..."
SHIPMENT_ID=$(echo $CHAT_RESPONSE | jq -r '.relatedData.shipmentId')

# 4. 分配车辆并开始运输
echo "Step 4: 分配车辆..."
curl -s -X PUT http://localhost:8000/api/shipments/$SHIPMENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vehicleId": "'$VEHICLE_ID'", "status": "picked_up"}'

# 5. 模拟GPS追踪 (批量上报优化)
echo "Step 5: 模拟GPS追踪..."

# 批量创建 GPS 数据
GPS_BATCH='['
for i in {1..10}; do
  LAT=$(echo "39.9042 + $i * 0.01" | bc)
  LNG=$(echo "116.4074 + $i * 0.01" | bc)

  if [ $i -gt 1 ]; then GPS_BATCH+=','; fi
  GPS_BATCH+='{"coordinates": {"latitude": '$LAT', "longitude": '$LNG'}, "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")'", "speed": 60, "heading": 90}'
done
GPS_BATCH+=']'

# 批量上报 GPS 数据
curl -s -X POST http://localhost:8000/api/gps/batch-locations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicleId": "'$VEHICLE_ID'",
    "locations": '$GPS_BATCH',
    "source": "g7_device"
  }'

# 6. 完成运单
echo "Step 6: 完成运单..."
curl -s -X PATCH http://localhost:8000/api/shipments/$SHIPMENT_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "delivered", "notes": "货物已安全送达"}'

# 7. 生成AI摘要
echo "Step 7: 生成AI摘要..."
curl -s -X GET http://localhost:8000/api/ai/summary?period=daily \
  -H "Authorization: Bearer $TOKEN"

echo "端到端测试完成！"
```

### 11. 故障测试场景 (扩展)

#### 9.1 GPS信号丢失测试
```bash
# 模拟GPS信号丢失情况
curl -X GET http://localhost:8000/api/gps/vehicles/$VEHICLE_ID/current \
  -H "Authorization: Bearer $TOKEN"

# 期望结果：显示最后已知位置和时间戳
```

#### 11.2 AI模型故障测试 (多模型容错)
```bash
# 配置错误的AI API密钥
curl -X POST http://localhost:8000/api/ai/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "错误配置",
    "provider": "openai",
    "apiKey": "invalid-key",
    "model": "gpt-4o-mini",
    "taskTypes": ["text_extraction"]
  }'

# 测试AI对话容错
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "测试消息", "channel": "web", "taskType": "text_extraction"}'

# 期望结果：
# - 自动切换到备用模型 (Claude 3 Sonnet)
# - 记录失败日志但不中断服务
# - 支持熔断器模式避免级联失败

# 测试Celery任务失败重试
echo "Step: 测试Celery重试机制..."
curl -X POST http://localhost:8000/api/workflows/test-retry \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"taskType": "email_notification", "failureMode": "api_timeout"}'

# 期望结果：3次重试后升级给管理员
```

### 10. 数据验证

#### 10.1 数据保留策略验证
```sql
-- 连接PostgreSQL数据库验证数据保留策略
SELECT
  table_name,
  COUNT(*) as record_count,
  MIN(created_at) as oldest_record,
  MAX(created_at) as newest_record
FROM (
  SELECT 'shipments' as table_name, created_at FROM shipments
  UNION ALL
  SELECT 'ai_interactions' as table_name, created_at FROM ai_interactions
  UNION ALL
  SELECT 'gps_locations' as table_name, created_at FROM gps_locations
) AS all_records
GROUP BY table_name;

-- 期望结果：数据符合1-3年保留策略
```

### 11. 监控和日志验证

#### 11.1 检查应用日志
```bash
# 查看应用日志
docker-compose logs -f app

# 验证日志格式和内容
# 期望看到：
# - 结构化JSON日志
# - 性能指标记录
# - 错误堆栈信息
# - 安全事件记录
```

#### 12.2 检查性能指标 (简化监控)
```bash
# 查看内置性能指标
curl http://localhost:8000/api/metrics \
  -H "Authorization: Bearer $TOKEN"

# 期望看到 (基于Diandian简化监控)：
# - AI响应时间统计 (P50, P95, P99)
# - 数据库连接池状态
# - Celery任务队列长度
# - 租户级别使用情况
# - 内存和CPU使用率

# 查看实时日志 (结构化格式)
tail -f logs/app.log | jq .

# 期望看到：
# - 统一的JSON日志格式
# - tenant_id字段用于隔离追踪
# - 性能指标和业务事件记录
```

## 成功标准

### 功能完整性 (更新指标)
- ✅ 所有API端点正常响应
- ✅ 前端页面正确渲染和交互
- ✅ AI助手响应时间<5秒 (基于Diandian调整)
- ✅ SSE实时推送功能正常 (替代WebSocket)
- ✅ 多租户数据隔离正确
- ✅ Celery工作流执行正常
- ✅ 数据正确存储和检索

### 性能指标 (调整规模)
- ✅ 支持100并发订单处理 (基于业务需求)
- ✅ 支持50租户并发访问 (10-50企业规模)
- ✅ 数据库查询响应时间<50ms (多租户优化)
- ✅ SSE连接稳定性 > 99.9%
- ✅ uvloop性能提升 3-5x 验证
- ✅ 批量GPS处理 100点/批次 < 100ms

### 安全合规
- ✅ JWT认证机制正常
- ✅ HTTPS加密通信
- ✅ 敏感数据加密存储
- ✅ 访问控制正确实施

### 数据一致性 (多租户升级)
- ✅ 租户数据隔离完全无跨访问
- ✅ 运单状态变更正确记录
- ✅ GPS轨迹数据完整 (批量处理)
- ✅ AI交互历史准确 (结构化存储)
- ✅ Celery任务状态跟踪准确
- ✅ 业务摘要数据正确

### 技术栈验证
- ✅ uv包管理器 10-100x 性能提升
- ✅ Instructor 替代 LangChain 成功
- ✅ Celery 替代 Temporal 成功
- ✅ SSE 替代 WebSocket 成功
- ✅ Row-Level 多租户架构稳定
- ✅ PostgreSQL RLS 性能可接受

---

## 总结

完成以上所有测试场景并达到成功标准，即表示**AI驱动的物流管理数字化平台**已准备就绪，可以进入生产环境部署。

该快速开始指南基于**Diandian项目的成功经验**，采用经过验证的技术栈和架构决策，确保了项目的技术可行性和性能表现。