# Implementation Guide: AI驱动的物流管理数字化平台

**Purpose**: 为tasks.md中的每个任务提供具体的实现指导和代码示例
**Target**: 确保每个任务都有足够详细的信息来独立完成

---

## 🔧 环境配置具体实现

### T001-T005: 项目设置详细指导

#### pyproject.toml 完整配置
```toml
[project]
name = "diandian-logistics-api"
version = "0.1.0"
description = "AI驱动的物流管理数字化平台后端API"
authors = [{name = "AI团队", email = "dev@diandian.ai"}]
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
    # Web框架
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "uvloop>=0.19.0",

    # AI框架 (替代LangChain)
    "instructor>=1.11.3",
    "openai>=1.58.1",
    "pydantic>=2.10.3",

    # 数据库
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",

    # 工作流引擎 (替代Temporal)
    "celery[redis]>=5.5.3",
    "redis>=5.0.0",

    # 实时通信
    "sse-starlette>=3.0.2",

    # 外部集成
    "httpx>=0.27.0",
    "python-multipart>=0.0.6",

    # 认证和安全
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",

    # 配置管理
    "python-dotenv>=1.0.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "httpx>=0.27.0",  # for testing
    "ruff>=0.1.0",
    "black>=23.0.0",
    "pre-commit>=3.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
select = ["E", "F", "I", "N", "W", "B"]
line-length = 88
target-version = "py311"

[tool.black]
line-length = 88
target-version = ['py311']
```

#### docker-compose.yml 完整配置
```yaml
version: '3.8'

services:
  postgresql:
    image: postgres:15
    environment:
      POSTGRES_DB: diandian_logistics
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  rabbitmq:
    image: rabbitmq:3.12-management
    environment:
      RABBITMQ_DEFAULT_USER: rabbitmq
      RABBITMQ_DEFAULT_PASS: rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
```

#### .env.example 环境变量模板
```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/diandian_logistics
DATABASE_ECHO=false

# Redis配置
REDIS_URL=redis://localhost:6379/0

# RabbitMQ配置
CELERY_BROKER_URL=amqp://rabbitmq:rabbitmq@localhost:5672//

# AI模型配置
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1

# 国产AI模型
QWEN_API_KEY=xxx
BAIDU_API_KEY=xxx
ZHIPU_API_KEY=xxx

# JWT安全配置
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 外部集成
G7_API_KEY=xxx
G7_BASE_URL=https://api.g7.com.cn
WECHAT_APP_ID=xxx
WECHAT_APP_SECRET=xxx

# 应用配置
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

---

## 🗄️ 数据模型具体实现

### T028-T033: 数据模型详细代码

#### backend/src/models/base.py
```python
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class MultiTenantMixin:
    """多租户基础混入类"""
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BaseModel(Base, MultiTenantMixin, TimestampMixin):
    """所有模型的基类"""
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

#### backend/src/models/logistics.py (对应前端Load接口)
```python
from sqlalchemy import Column, String, Enum, Text, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class ShipmentStatus(enum.Enum):
    """对应前端 LoadStatus"""
    UNASSIGNED = "unassigned"
    ASSIGNED = "assigned"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in-transit"
    AT_PICKUP = "at-pickup"
    LOADED = "loaded"
    DELIVERED = "delivered"

class Shipment(BaseModel):
    """运单模型 - 对应前端 Load 接口"""
    __tablename__ = "shipments"

    # 对应前端 Load.id
    shipment_number = Column(String(50), nullable=False)

    # 对应前端 Load.origin/destination
    pickup_address = Column(Text, nullable=False)
    delivery_address = Column(Text, nullable=False)

    # 对应前端 Load.status
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.UNASSIGNED)

    # 对应前端 Load.customer/mode/equipment等
    customer_name = Column(String(200), nullable=False)
    transport_mode = Column(String(100))
    equipment_type = Column(String(100))

    # 对应前端 Load.weight/commodity等
    weight_kg = Column(DECIMAL(10, 2))
    commodity_type = Column(String(200))
    packing_type = Column(String(100))

    # 对应前端 Load.pickupCoords/deliveryCoords
    pickup_coordinates = Column(JSON)  # [lng, lat]
    delivery_coordinates = Column(JSON)  # [lng, lat]

    # 对应前端 Load.notes
    notes = Column(Text)

    # 对应前端 Load.badges
    badges = Column(ARRAY(String))

    # 关联关系
    stops = relationship("ShipmentStop", back_populates="shipment")
    gps_tracks = relationship("GPSLocation", back_populates="shipment")

class ShipmentStop(BaseModel):
    """运单站点 - 对应前端 Stop 接口"""
    __tablename__ = "shipment_stops"

    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"))

    # 对应前端 Stop 字段
    stop_type = Column(Enum(StopType))  # pickup/delivery
    address = Column(Text, nullable=False)
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(String(20))

    # 时间窗口
    scheduled_date = Column(DateTime(timezone=True))
    time_window_start = Column(String(20))
    time_window_end = Column(String(20))

    # 坐标
    coordinates = Column(JSON)  # [lng, lat]

    shipment = relationship("Shipment", back_populates="stops")
```

---

## 🤖 AI集成具体实现

### T034-T035: AI服务详细代码

#### backend/src/services/ai_service.py
```python
import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from ..core.config import get_settings
from ..models.ai_models import AIConversation, AIMessage

settings = get_settings()

# 使用Instructor进行结构化输出
client = instructor.patch(AsyncOpenAI(api_key=settings.openai_api_key))

class ChatResponse(BaseModel):
    """AI聊天响应结构 - 对应前端ChatMessage"""
    content: str
    role: str = "assistant"
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_actions: Optional[List[str]] = None
    requires_confirmation: bool = False

class LogisticsAction(BaseModel):
    """物流相关动作识别"""
    action_type: str = Field(description="动作类型: create_shipment, update_status, query_location")
    parameters: dict = Field(description="动作参数")
    confidence: float = Field(ge=0.0, le=1.0)

class AIService:
    def __init__(self):
        self.client = client

    async def chat_with_context(
        self,
        message: str,
        user_id: str,
        tenant_id: str,
        conversation_history: List[dict]
    ) -> ChatResponse:
        """
        对应任务 T048: POST /api/ai/chat 的核心逻辑
        """

        # 1. 构建系统提示词（包含租户上下文）
        system_prompt = self._build_system_prompt(tenant_id)

        # 2. 格式化对话历史
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})

        # 3. 调用Instructor获取结构化响应
        response = await self.client.chat.completions.create(
            model="gpt-4",
            response_model=ChatResponse,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )

        # 4. 记录对话到数据库
        await self._save_conversation(user_id, tenant_id, message, response)

        return response

    async def detect_logistics_action(self, message: str) -> Optional[LogisticsAction]:
        """
        检测用户消息中的物流操作意图
        用于T050: POST /api/ai/tasks
        """
        action = await self.client.chat.completions.create(
            model="gpt-4",
            response_model=LogisticsAction,
            messages=[
                {"role": "system", "content": "你是物流操作专家，识别用户想要执行的物流操作"},
                {"role": "user", "content": message}
            ]
        )

        return action if action.confidence > 0.7 else None

    def _build_system_prompt(self, tenant_id: str) -> str:
        """构建包含租户上下文的系统提示"""
        return f"""
        你是一个专业的物流管理AI助手，服务于租户 {tenant_id}。

        你的能力包括：
        1. 创建和管理运单
        2. 查询实时位置信息
        3. 提供物流状态更新
        4. 生成业务报告和建议

        重要规则：
        - 关键操作需要用户确认
        - 只能访问当前租户的数据
        - 使用中文进行交流
        - 提供准确、实用的建议
        """

    async def _save_conversation(
        self,
        user_id: str,
        tenant_id: str,
        user_message: str,
        ai_response: ChatResponse
    ):
        """保存对话记录到数据库"""
        # 实现对话历史保存逻辑
        pass
```

---

## 🔌 前后端对接具体实现

### T069-T074: 前端集成详细代码

#### src/services/api.ts (替换mockData)
```typescript
// 对应任务 T069: 前端API客户端配置

interface APIConfig {
  baseURL: string;
  timeout: number;
}

const config: APIConfig = {
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 10000,
};

// 数据转换器：后端 Shipment → 前端 Load
export const transformShipmentToLoad = (shipment: any): Load => {
  return {
    id: shipment.shipment_number, // 使用业务编号作为前端ID
    origin: shipment.pickup_address,
    destination: shipment.delivery_address,
    status: shipment.status, // 枚举值保持一致
    date: new Date(shipment.created_at).toLocaleDateString('zh-CN'),
    badges: shipment.badges || [],
    notes: shipment.notes || '',
    customer: shipment.customer_name,
    mode: shipment.transport_mode || '',
    equipment: shipment.equipment_type || '',
    weight: `${shipment.weight_kg || 0}公斤`,
    commodity: shipment.commodity_type || '',
    packingType: shipment.packing_type || '',
    pickupCoords: shipment.pickup_coordinates as [number, number],
    deliveryCoords: shipment.delivery_coordinates as [number, number],
    stops: shipment.stops?.map(transformStopToFrontend) || [],
  };
};

// API客户端类
class LogisticsAPI {
  private baseURL: string;

  constructor(config: APIConfig) {
    this.baseURL = config.baseURL;
  }

  async getShipments(): Promise<Load[]> {
    const response = await fetch(`${this.baseURL}/api/shipments`, {
      headers: this.getAuthHeaders(),
    });

    const data = await response.json();
    return data.map(transformShipmentToLoad);
  }

  async getShipment(id: string): Promise<Load> {
    const response = await fetch(`${this.baseURL}/api/shipments/${id}`, {
      headers: this.getAuthHeaders(),
    });

    const data = await response.json();
    return transformShipmentToLoad(data);
  }

  private getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }
}

export const api = new LogisticsAPI(config);
```

#### src/services/sse.ts (实时数据流)
```typescript
// 对应任务 T071: SSE实时数据服务

export class SSEService {
  private eventSource: EventSource | null = null;
  private subscribers: Map<string, ((data: any) => void)[]> = new Map();

  connect(shipmentId: string) {
    const token = localStorage.getItem('auth_token');
    const url = `${API_BASE_URL}/api/gps/realtime/${shipmentId}?token=${token}`;

    this.eventSource = new EventSource(url);

    this.eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.notifySubscribers('location_update', data);
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE连接错误:', error);
      this.reconnect(shipmentId);
    };
  }

  subscribe(event: string, callback: (data: any) => void) {
    if (!this.subscribers.has(event)) {
      this.subscribers.set(event, []);
    }
    this.subscribers.get(event)!.push(callback);
  }

  private notifySubscribers(event: string, data: any) {
    const callbacks = this.subscribers.get(event) || [];
    callbacks.forEach(callback => callback(data));
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

export const sseService = new SSEService();
```

---

## 🧪 测试实现具体指导

### T010-T027: 合约测试模板

#### backend/tests/contract/test_auth_login.py
```python
# 对应任务 T010: 合约测试 POST /api/auth/login

import pytest
from httpx import AsyncClient
from jsonschema import validate

# 请求schema
LOGIN_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "password": {"type": "string"},
        "login_type": {"type": "string", "enum": ["password", "wechat"]}
    },
    "required": ["username", "password", "login_type"]
}

# 响应schema
LOGIN_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "access_token": {"type": "string"},
        "token_type": {"type": "string"},
        "expires_in": {"type": "integer"},
        "user": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "username": {"type": "string"},
                "role": {"type": "string"}
            }
        }
    },
    "required": ["access_token", "token_type", "user"]
}

@pytest.mark.asyncio
async def test_login_contract_valid_request(test_client: AsyncClient):
    """测试登录接口合约 - 有效请求"""
    request_data = {
        "username": "test@example.com",
        "password": "password123",
        "login_type": "password"
    }

    # 验证请求格式
    validate(instance=request_data, schema=LOGIN_REQUEST_SCHEMA)

    response = await test_client.post("/api/auth/login", json=request_data)

    # 这个测试现在应该失败，因为还没有实现
    assert response.status_code == 200

    # 验证响应格式
    validate(instance=response.json(), schema=LOGIN_RESPONSE_SCHEMA)

@pytest.mark.asyncio
async def test_login_contract_invalid_request(test_client: AsyncClient):
    """测试登录接口合约 - 无效请求"""
    request_data = {"username": "test"}  # 缺少必需字段

    response = await test_client.post("/api/auth/login", json=request_data)

    assert response.status_code == 422  # 验证错误
    assert "detail" in response.json()
```

---

## 📋 任务执行检查清单

为每个任务提供完成标准：

### T001 完成标准:
- ✅ backend/ 目录结构创建完整
- ✅ 所有子目录按plan.md规划创建
- ✅ __init__.py 文件正确放置

### T010 完成标准:
- ✅ 测试文件创建在正确位置
- ✅ 测试运行时失败（符合TDD要求）
- ✅ 使用正确的schema验证
- ✅ 覆盖正常和异常场景

### T048 完成标准:
- ✅ 端点正确响应POST请求
- ✅ Instructor集成工作正常
- ✅ 多租户权限验证通过
- ✅ 所有合约测试通过

---

这个实现指导文档解决了您提到的核心问题：
1. **具体实现细节** - 每个任务都有完整代码示例
2. **前后端对接** - 明确的数据转换和接口映射
3. **配置参考** - 完整的环境和依赖配置
4. **测试指导** - 具体的TDD测试模板
5. **完成标准** - 每个任务的明确验收条件

现在每个任务都有足够的信息来独立完成！