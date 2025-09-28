# 前后端数据映射指南

**Purpose**: 确保现有前端代码与新后端API的完美集成
**Reference**: 基于 `src/types/logistics.ts` 和 `contracts/` API规范

---

## 🔄 核心数据结构映射

### 1. Load ↔ Shipment 映射

#### 前端接口 (`src/types/logistics.ts`)
```typescript
export interface Load {
  id: string;                    // → shipment_number (业务编号)
  origin: string;                // → pickup_address
  destination: string;           // → delivery_address
  status: LoadStatus;            // → status (enum保持一致)
  date: string;                  // → created_at (格式化)
  badges?: string[];             // → badges (数组直接对应)
  stops: Stop[];                 // → stops (关联表)
  notes: string;                 // → notes
  customer: string;              // → customer_name
  mode: string;                  // → transport_mode
  equipment: string;             // → equipment_type
  weight: string;                // → weight_kg (格式转换)
  commodity: string;             // → commodity_type
  packingType: string;           // → packing_type
  pickupCoords: [number, number]; // → pickup_coordinates (JSON)
  deliveryCoords: [number, number]; // → delivery_coordinates (JSON)
}
```

#### 后端模型 (`backend/src/models/logistics.py`)
```python
class Shipment(BaseModel):
    shipment_number = Column(String(50))      # ← Load.id
    pickup_address = Column(Text)             # ← Load.origin
    delivery_address = Column(Text)           # ← Load.destination
    status = Column(Enum(ShipmentStatus))     # ← Load.status
    created_at = Column(DateTime)             # ← Load.date (转换)
    badges = Column(ARRAY(String))            # ← Load.badges
    notes = Column(Text)                      # ← Load.notes
    customer_name = Column(String(200))       # ← Load.customer
    transport_mode = Column(String(100))      # ← Load.mode
    equipment_type = Column(String(100))      # ← Load.equipment
    weight_kg = Column(DECIMAL(10, 2))        # ← Load.weight (解析)
    commodity_type = Column(String(200))      # ← Load.commodity
    packing_type = Column(String(100))        # ← Load.packingType
    pickup_coordinates = Column(JSON)         # ← Load.pickupCoords
    delivery_coordinates = Column(JSON)       # ← Load.deliveryCoords
```

### 2. ChatMessage ↔ AIMessage 映射

#### 前端接口
```typescript
export interface ChatMessage {
  id: string;                    // → conversation_id + message_id
  role: MessageRole;             // → role ('agent'|'human'|'system')
  content: string;               // → content
  timestamp: string;             // → created_at (ISO格式)
  attachments?: Attachment[];    // → attachments (JSON)
}

export type MessageRole = 'agent' | 'human' | 'system';
```

#### 后端模型
```python
class AIMessage(BaseModel):
    conversation_id = Column(UUID)            # ← ChatMessage.id (部分)
    role = Column(Enum(MessageRole))          # ← ChatMessage.role
    content = Column(Text)                    # ← ChatMessage.content
    created_at = Column(DateTime)             # ← ChatMessage.timestamp
    attachments = Column(JSON)                # ← ChatMessage.attachments
```

---

## 🔧 API响应转换器

### 运单数据转换
```typescript
// src/services/transformers.ts

export const transformShipmentToLoad = (shipment: BackendShipment): Load => {
  return {
    id: shipment.shipment_number,
    origin: shipment.pickup_address,
    destination: shipment.delivery_address,
    status: shipment.status as LoadStatus,
    date: formatDate(shipment.created_at),
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
    stops: (shipment.stops || []).map(transformStopToFrontend),
  };
};

export const transformLoadToShipment = (load: Load): CreateShipmentRequest => {
  return {
    pickup_address: load.origin,
    delivery_address: load.destination,
    customer_name: load.customer,
    transport_mode: load.mode,
    equipment_type: load.equipment,
    weight_kg: parseFloat(load.weight.replace('公斤', '')) || 0,
    commodity_type: load.commodity,
    packing_type: load.packingType,
    pickup_coordinates: load.pickupCoords,
    delivery_coordinates: load.deliveryCoords,
    notes: load.notes,
    badges: load.badges,
  };
};

const formatDate = (isoString: string): string => {
  return new Date(isoString).toLocaleDateString('zh-CN', {
    month: '3月',
    day: '数字'
  });
};
```

### 聊天消息转换
```typescript
export const transformAIMessageToChatMessage = (message: BackendAIMessage): ChatMessage => {
  return {
    id: `${message.conversation_id}-${message.id}`,
    role: message.role as MessageRole,
    content: message.content,
    timestamp: new Date(message.created_at).toISOString(),
    attachments: message.attachments ? JSON.parse(message.attachments) : undefined,
  };
};
```

---

## 🎯 组件更新策略

### 1. LoadList 组件更新 (T074)

#### 当前实现 (使用mockData)
```typescript
// src/components/LoadList.tsx - 当前
import { mockLoads } from '@/data/mockData';

const LoadList = ({ selectedLoadId, onLoadSelect }) => {
  // 直接使用本地数据
  const loads = mockLoads;
  // ...
};
```

#### 更新后实现 (使用真实API)
```typescript
// src/components/LoadList.tsx - 更新后
import { api } from '@/services/api';
import { useQuery } from '@tanstack/react-query';

const LoadList = ({ selectedLoadId, onLoadSelect }) => {
  const { data: loads, isLoading, error } = useQuery({
    queryKey: ['shipments'],
    queryFn: () => api.getShipments(),
    refetchInterval: 30000, // 30秒自动刷新
  });

  if (isLoading) return <div>加载中...</div>;
  if (error) return <div>加载失败: {error.message}</div>;

  // 其余逻辑保持不变
  return (
    <div className="w-[320px] border-r bg-card">
      {/* 现有UI代码完全保留 */}
    </div>
  );
};
```

### 2. RealTimeGPSMap 组件更新 (T073)

#### 当前实现
```typescript
// src/components/RealTimeGPSMap.tsx - 当前
const RealTimeGPSMap = ({ load }) => {
  // 使用静态坐标
  const position = load.pickupCoords;
  // ...
};
```

#### 更新后实现
```typescript
// src/components/RealTimeGPSMap.tsx - 更新后
import { sseService } from '@/services/sse';

const RealTimeGPSMap = ({ load }) => {
  const [currentPosition, setCurrentPosition] = useState(load.pickupCoords);
  const [gpsHistory, setGpsHistory] = useState<[number, number][]>([]);

  useEffect(() => {
    // 订阅实时GPS数据
    sseService.connect(load.id);
    sseService.subscribe('location_update', (data) => {
      setCurrentPosition([data.longitude, data.latitude]);
      setGpsHistory(prev => [...prev, [data.longitude, data.latitude]]);
    });

    return () => {
      sseService.disconnect();
    };
  }, [load.id]);

  // 地图渲染逻辑保持不变，只是数据源改为实时数据
  return (
    <div className="h-[400px] rounded-lg overflow-hidden">
      {/* 现有Leaflet地图代码完全保留，只更新position数据源 */}
    </div>
  );
};
```

### 3. ChatPanel 组件更新 (T072)

#### 当前实现
```typescript
// src/components/ChatPanel.tsx - 当前
import { mockChatMessages } from '@/data/mockData';

const ChatPanel = () => {
  const [messages, setMessages] = useState(mockChatMessages);
  // ...
};
```

#### 更新后实现
```typescript
// src/components/ChatPanel.tsx - 更新后
import { aiAPI } from '@/services/ai-api';

const ChatPanel = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (content: string) => {
    setLoading(true);
    try {
      // 添加用户消息
      const userMessage: ChatMessage = {
        id: generateId(),
        role: 'human',
        content,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, userMessage]);

      // 调用AI API
      const response = await aiAPI.chat(content, messages);

      // 添加AI响应
      const aiMessage: ChatMessage = {
        id: generateId(),
        role: 'agent',
        content: response.content,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('发送消息失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // UI组件完全保留，只更新数据处理逻辑
};
```

---

## 🚀 渐进式集成计划

### 阶段1: API基础连接 (T069-T071)
1. 创建API服务层
2. 添加错误处理和Loading状态
3. 实现基础的数据转换器

### 阶段2: 静态数据替换 (T074)
1. LoadList组件切换到真实API
2. 保留现有UI和交互逻辑
3. 添加错误边界和重试机制

### 阶段3: 实时功能集成 (T073)
1. SSE服务实现
2. GPS地图实时更新
3. 连接状态指示器

### 阶段4: AI功能集成 (T072)
1. AI聊天API集成
2. 聊天历史同步
3. 智能建议功能

---

## ✅ 集成验证清单

### API集成验证
- [ ] 所有API调用返回正确格式数据
- [ ] 错误处理覆盖网络异常、认证失败等场景
- [ ] Loading状态在合适时机显示

### 数据一致性验证
- [ ] 前端Load接口与后端Shipment完全映射
- [ ] 日期格式统一（ISO 8601）
- [ ] 坐标格式一致（[lng, lat]）

### 用户体验验证
- [ ] 现有界面布局完全保持
- [ ] 交互行为无变化
- [ ] 性能无明显下降

### 实时功能验证
- [ ] GPS位置更新及时（10-30秒）
- [ ] SSE连接稳定，支持断线重连
- [ ] 多设备同步正常

这个映射指南确保了前后端的完美对接，同时保护了现有的前端投资！