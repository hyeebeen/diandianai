# Data Model: AI驱动的物流管理数字化平台

## 多租户架构设计 (基于Diandian项目验证)

### Row-Level安全隔离方案
**架构选择**: Row-Level Security (RLS) + tenant_id字段
**适用场景**: 10-50家企业，每家10-100用户的中小型物流公司
**技术决策**: 避免Schema级隔离的复杂度，使用PostgreSQL原生RLS功能

```sql
-- 多租户策略实现
-- 1. 为所有业务表添加tenant_id字段
-- 2. 启用Row Level Security
-- 3. 创建安全策略确保数据隔离

-- 示例：运单表的多租户配置
CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,  -- 租户隔离字段
    shipment_number VARCHAR(50) NOT NULL,
    -- ... 其他字段
    CONSTRAINT unique_shipment_per_tenant UNIQUE (tenant_id, shipment_number)
);

-- 启用行级安全
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;

-- 创建隔离策略
CREATE POLICY tenant_isolation ON shipments
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- 性能优化：复合索引
CREATE INDEX idx_shipments_tenant_performance
ON shipments (tenant_id, status, created_at);

-- 外键约束确保租户一致性
ALTER TABLE shipments
ADD CONSTRAINT fk_shipments_tenant
FOREIGN KEY (tenant_id) REFERENCES companies(id);
```

### 数据库连接管理
**连接策略**: 单一数据库实例 + 应用层租户切换
**会话管理**: 每个HTTP请求设置tenant_id上下文

```python
# 多租户中间件实现
from fastapi import Request, HTTPException
from sqlalchemy import text

class MultiTenantMiddleware:
    async def __call__(self, request: Request, call_next):
        tenant_id = self.extract_tenant_id(request)
        if not tenant_id:
            raise HTTPException(401, "Missing tenant context")

        # 设置会话级租户上下文
        async with get_db() as db:
            await db.execute(
                text("SET app.current_tenant_id = :tenant_id"),
                {"tenant_id": str(tenant_id)}
            )

            response = await call_next(request)
            return response

    def extract_tenant_id(self, request: Request) -> str:
        # 从JWT token或请求头中提取tenant_id
        token = request.headers.get("Authorization")
        return decode_jwt_tenant(token)
```

### 跨租户查询控制
**数据隔离**: 所有查询自动添加tenant_id过滤
**性能优化**: 分区表 + 租户索引优化

```sql
-- GPS数据的分区策略（高频写入表）
CREATE TABLE gps_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    vehicle_id UUID NOT NULL,
    coordinates POINT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
) PARTITION BY HASH (tenant_id);

-- 为每个租户创建分区
CREATE TABLE gps_locations_p0 PARTITION OF gps_locations
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE gps_locations_p1 PARTITION OF gps_locations
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
```

---

## 核心实体

### User (用户)
```python
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "admin"                    # 系统管理员
    COMPANY_ADMIN = "company_admin"    # 公司管理员
    DISPATCHER = "dispatcher"          # 调度员
    DRIVER = "driver"                  # 司机
    CUSTOMER = "customer"              # 客户

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    wechat_id = Column(String(100), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)  # 多租户隔离
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)  # 向后兼容
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tenant = relationship("Company", foreign_keys=[tenant_id], back_populates="tenant_users")
    company = relationship("Company", foreign_keys=[company_id], back_populates="users")
    shipments = relationship("Shipment", back_populates="created_by_user")
```

### Company (公司)
```python
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(String(500), nullable=False)
    contact = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, nullable=True)  # 存储公司配置JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系 (多租户)
    tenant_users = relationship("User", foreign_keys="User.tenant_id", back_populates="tenant")
    tenant_shipments = relationship("Shipment", foreign_keys="Shipment.tenant_id", back_populates="tenant")
    tenant_vehicles = relationship("Vehicle", foreign_keys="Vehicle.tenant_id", back_populates="tenant")

    # 关系 (向后兼容)
    users = relationship("User", foreign_keys="User.company_id", back_populates="company")
    shipments = relationship("Shipment", foreign_keys="Shipment.company_id", back_populates="company")
    vehicles = relationship("Vehicle", foreign_keys="Vehicle.company_id", back_populates="company")

# Pydantic模型用于API数据验证
from pydantic import BaseModel
from typing import List, Optional

class CompanySettings(BaseModel):
    time_zone: str = "Asia/Shanghai"    # 时区
    currency: str = "CNY"               # 货币单位
    language: str = "zh-CN"             # 默认语言
    features: List[str] = []            # 启用的功能

class CompanyCreate(BaseModel):
    name: str
    code: str
    address: str
    contact: str
    phone: str
    settings: Optional[CompanySettings] = None
```

### AIModelConfig (AI模型配置)
```typescript
interface AIModelConfig {
  id: string                   // UUID主键
  name: string                 // 配置名称
  provider: AIProvider         // AI服务提供商
  endpoint: string             // API端点
  apiKey: string               // API密钥 (加密存储)
  model: string                // 模型名称
  parameters: AIParameters     // 模型参数
  isActive: boolean            // 是否激活
  tenantId: string             // 租户ID (必填，多租户隔离)
  companyId?: string           // 所属公司 (null为全局配置，向后兼容)
  createdBy: string            // 创建人ID
  createdAt: Date              // 创建时间
  updatedAt: Date              // 更新时间
}

enum AIProvider {
  OPENAI = 'openai',
  CLAUDE = 'claude',
  WENXIN = 'wenxin',           // 百度文心一言
  ZHIPU = 'zhipu',             // 智谱AI
  TONGYI = 'tongyi'            // 阿里通义千问
}

interface AIParameters {
  temperature: number          // 温度参数
  maxTokens: number           // 最大token数
  topP?: number               // top-p参数
  frequencyPenalty?: number   // 频率惩罚
  presencePenalty?: number    // 存在惩罚
}
```

### Shipment (运单)
```typescript
interface Shipment {
  id: string                   // UUID主键
  shipmentNumber: string       // 运单号 (unique)
  status: ShipmentStatus       // 运单状态

  // 发货信息
  sender: ContactInfo          // 发货方信息
  senderAddress: Address       // 发货地址

  // 收货信息
  receiver: ContactInfo        // 收货方信息
  receiverAddress: Address     // 收货地址

  // 货物信息
  cargo: CargoInfo             // 货物详情

  // 运输信息
  driverId?: string           // 司机ID
  vehicleId?: string          // 车辆ID
  routeId?: string            // 路线ID

  // 时间信息
  pickupTime?: Date           // 提货时间
  estimatedDeliveryTime?: Date // 预计送达时间
  actualDeliveryTime?: Date   // 实际送达时间

  // 费用信息
  freight: number             // 运费
  currency: string            // 货币单位

  // 关联信息
  tenantId: string            // 租户ID (多租户隔离)
  companyId: string           // 所属公司
  createdBy: string           // 创建人
  aiInteractionId?: string    // 关联的AI交互记录

  // 元数据
  createdAt: Date             // 创建时间
  updatedAt: Date             // 更新时间
}

enum ShipmentStatus {
  CREATED = 'created',         // 已创建
  PICKED_UP = 'picked_up',     // 已提货
  IN_TRANSIT = 'in_transit',   // 运输中
  DELIVERED = 'delivered',     // 已送达
  CANCELLED = 'cancelled'      // 已取消
}

interface ContactInfo {
  name: string                 // 联系人姓名
  phone: string                // 联系电话
  company?: string             // 公司名称
}

interface Address {
  street: string               // 街道地址
  city: string                 // 城市
  province: string             // 省份
  postalCode?: string          // 邮政编码
  country: string              // 国家
  coordinates?: GeoCoordinates // 地理坐标
}

interface GeoCoordinates {
  latitude: number             // 纬度
  longitude: number            // 经度
}

interface CargoInfo {
  description: string          // 货物描述
  weight: number               // 重量 (kg)
  volume?: number              // 体积 (m³)
  quantity: number             // 数量
  unit: string                 // 单位
  value?: number               // 货值
  specialRequirements?: string[] // 特殊要求
}
```

### Vehicle (车辆)
```typescript
interface Vehicle {
  id: string                   // UUID主键
  plateNumber: string          // 车牌号 (unique)
  model: string                // 车型
  driverId?: string            // 当前司机ID
  capacity: VehicleCapacity    // 载重信息
  status: VehicleStatus        // 车辆状态
  gpsDeviceId?: string         // GPS设备ID
  tenantId: string             // 租户ID (多租户隔离)
  companyId: string            // 所属公司
  createdAt: Date              // 创建时间
  updatedAt: Date              // 更新时间
}

interface VehicleCapacity {
  maxWeight: number            // 最大载重 (kg)
  maxVolume: number            // 最大容积 (m³)
}

enum VehicleStatus {
  AVAILABLE = 'available',     // 可用
  IN_USE = 'in_use',          // 使用中
  MAINTENANCE = 'maintenance', // 维护中
  OFFLINE = 'offline'         // 离线
}
```

### Route (运输路线)
```typescript
interface Route {
  id: string                   // UUID主键
  shipmentId: string           // 运单ID
  startLocation: GeoCoordinates // 起点坐标
  endLocation: GeoCoordinates  // 终点坐标
  plannedPath?: GeoCoordinates[] // 计划路径
  actualPath: RoutePoint[]     // 实际轨迹
  totalDistance?: number       // 总距离 (km)
  estimatedDuration?: number   // 预计耗时 (分钟)
  actualDuration?: number      // 实际耗时 (分钟)
  status: RouteStatus          // 路线状态
  createdAt: Date              // 创建时间
  updatedAt: Date              // 更新时间
}

interface RoutePoint {
  coordinates: GeoCoordinates  // 坐标点
  timestamp: Date              // 时间戳
  speed?: number               // 速度 (km/h)
  heading?: number             // 方向角 (度)
  source: GPSSource            // 数据来源
}

enum GPSSource {
  G7_DEVICE = 'g7_device',     // G7设备
  DRIVER_APP = 'driver_app',   // 司机小程序
  MANUAL = 'manual'            // 手动输入
}

enum RouteStatus {
  PLANNED = 'planned',         // 已规划
  ACTIVE = 'active',           // 进行中
  COMPLETED = 'completed',     // 已完成
  PAUSED = 'paused'           // 已暂停
}
```

### GPSLocation (GPS位置数据)
```typescript
interface GPSLocation {
  id: string                   // UUID主键
  tenantId: string             // 租户ID (多租户隔离，性能关键)
  vehicleId: string            // 车辆ID
  coordinates: GeoCoordinates  // 坐标
  timestamp: Date              // 时间戳
  speed: number                // 速度 (km/h)
  heading: number              // 方向角 (度)
  altitude?: number            // 海拔 (m)
  accuracy: number             // 精度 (m)
  source: GPSSource            // 数据来源
  rawData?: any               // 原始数据
  createdAt: Date              // 创建时间
}
```

### AIInteraction (AI交互记录)
```typescript
interface AIInteraction {
  id: string                   // UUID主键
  tenantId: string             // 租户ID (多租户隔离)
  sessionId: string            // 会话ID
  userId: string               // 用户ID
  channel: CommunicationChannel // 沟通渠道

  // 消息内容
  userMessage: string          // 用户消息
  aiResponse: string           // AI响应
  context?: any               // 上下文信息

  // 处理信息
  modelConfigId: string        // 使用的AI模型配置
  responseTime: number         // 响应时间 (ms)
  tokenUsage?: TokenUsage      // Token使用情况

  // 业务关联
  relatedShipmentId?: string   // 关联运单ID
  actionTaken?: string         // 执行的操作

  // 元数据
  createdAt: Date              // 创建时间
}

enum CommunicationChannel {
  WECHAT = 'wechat',           // 微信
  PHONE = 'phone',             // 电话
  SMS = 'sms',                 // 短信
  WEB = 'web'                  // 网页
}

interface TokenUsage {
  promptTokens: number         // 输入token数
  completionTokens: number     // 输出token数
  totalTokens: number          // 总token数
}
```

### BusinessSummary (业务摘要)
```typescript
interface BusinessSummary {
  id: string                   // UUID主键
  tenantId: string             // 租户ID (多租户隔离)
  userId: string               // 用户ID
  period: SummaryPeriod        // 摘要周期
  startDate: Date              // 开始日期
  endDate: Date                // 结束日期

  // 统计数据
  totalInteractions: number    // 总交互次数
  shipmentsCreated: number     // 创建的运单数
  shipmentsCompleted: number   // 完成的运单数
  totalRevenue?: number        // 总收入

  // AI助手活动
  keyTopics: string[]          // 主要话题
  commonTasks: string[]        // 常见任务
  suggestions: string[]        // AI建议

  // 生成信息
  generatedBy: string          // 生成者 (AI模型)
  generatedAt: Date            // 生成时间

  // 元数据
  createdAt: Date              // 创建时间
}

enum SummaryPeriod {
  DAILY = 'daily',             // 日报
  WEEKLY = 'weekly',           // 周报
  MONTHLY = 'monthly'          // 月报
}
```

### SystemLog (系统日志)
```typescript
interface SystemLog {
  id: string                   // UUID主键
  level: LogLevel              // 日志级别
  message: string              // 日志消息
  category: LogCategory        // 日志分类

  // 上下文信息
  tenantId?: string            // 租户ID (多租户隔离)
  userId?: string              // 相关用户ID
  companyId?: string           // 相关公司ID
  sessionId?: string           // 会话ID
  ipAddress?: string           // IP地址
  userAgent?: string           // 用户代理

  // 详细信息
  details?: any               // 详细数据
  errorStack?: string         // 错误堆栈
  duration?: number           // 耗时 (ms)

  // 元数据
  timestamp: Date             // 时间戳
  hostname: string            // 主机名
  service: string             // 服务名
}

enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  DEBUG = 'debug'
}

enum LogCategory {
  AUTH = 'auth',               // 认证
  API = 'api',                 // API调用
  AI = 'ai',                   // AI交互
  GPS = 'gps',                 // GPS数据
  BUSINESS = 'business',       // 业务操作
  SYSTEM = 'system'            // 系统事件
}
```

## 数据关系

### 主要关联关系 (多租户架构)
1. **Company** (租户) ←→ **User**: 一对多关系，每个用户属于一个租户
2. **Company** (租户) ←→ **Shipment**: 一对多关系，所有运单按租户隔离
3. **Company** (租户) ←→ **Vehicle**: 一对多关系，车辆资源按租户管理
4. **Shipment** ←→ **User**: 多对一关系，运单由用户创建 (同租户内)
5. **Shipment** ←→ **Vehicle**: 多对一关系，运单分配给车辆 (同租户内)
6. **Shipment** ←→ **Route**: 一对一关系，运单对应一条路线
7. **Vehicle** ←→ **GPSLocation**: 一对多关系，车辆轨迹数据 (租户隔离)
8. **AIInteraction** ←→ **Shipment**: 多对一关系，AI交互可能创建运单 (同租户内)
9. **BusinessSummary** ←→ **User**: 多对一关系，为用户生成摘要 (租户隔离)

### 状态转换规则
1. **Shipment状态流转**: CREATED → PICKED_UP → IN_TRANSIT → DELIVERED
2. **Route状态流转**: PLANNED → ACTIVE → COMPLETED
3. **Vehicle状态流转**: AVAILABLE ↔ IN_USE ↔ MAINTENANCE ↔ OFFLINE

### 数据验证规则 (多租户升级)
1. **运单号**在同一租户内唯一 (替代全局唯一，提升性能)
2. **车牌号**在同一租户内唯一 (符合实际业务场景)
3. **GPS坐标**必须在有效范围内 (-90 ≤ lat ≤ 90, -180 ≤ lng ≤ 180)
4. **AI响应时间**必须 < 5000ms (基于Diandian项目调整)
5. **租户数据隔离**：所有查询必须包含tenant_id过滤
6. **数据保留期**: 6个月 (基于需求简化，后续可扩展)
7. **跨租户操作禁止**：系统层面确保无跨租户数据访问

### 索引策略 (多租户优化)
1. **主键索引**: 所有表的id字段
2. **租户隔离索引**: 所有业务表必须有 (tenant_id, created_at) 复合索引
3. **唯一约束索引**: (tenant_id, shipmentNumber), (tenant_id, plateNumber)
4. **性能关键索引**:
   - `CREATE INDEX idx_shipments_tenant_status ON shipments (tenant_id, status, created_at);`
   - `CREATE INDEX idx_gps_tenant_vehicle ON gps_locations (tenant_id, vehicle_id, timestamp);`
   - `CREATE INDEX idx_ai_interactions_tenant_user ON ai_interactions (tenant_id, user_id, created_at);`
5. **地理索引**: coordinates字段使用GiST索引 + 租户过滤
6. **全文索引**: (tenant_id, tsvector(消息内容)) 组合索引
7. **分区表索引**: GPS和日志表按tenant_id进行哈希分区
8. **租户级别统计索引**: 支持按租户维度的业务分析和报表生成

### 多租户数据迁移策略

**现有数据升级路径**:
```sql
-- 阶段1：添加tenant_id字段
ALTER TABLE users ADD COLUMN tenant_id UUID;
ALTER TABLE shipments ADD COLUMN tenant_id UUID;
ALTER TABLE vehicles ADD COLUMN tenant_id UUID;

-- 阶段2：填充tenant_id数据 (基于现有company_id)
UPDATE users SET tenant_id = company_id WHERE company_id IS NOT NULL;
UPDATE shipments SET tenant_id = company_id WHERE company_id IS NOT NULL;
UPDATE vehicles SET tenant_id = company_id WHERE company_id IS NOT NULL;

-- 阶段3：设置非空约束
ALTER TABLE users ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE shipments ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE vehicles ALTER COLUMN tenant_id SET NOT NULL;

-- 阶段4：创建索引和约束
CREATE INDEX CONCURRENTLY idx_users_tenant_performance ON users (tenant_id, created_at);
CREATE INDEX CONCURRENTLY idx_shipments_tenant_performance ON shipments (tenant_id, status, created_at);
CREATE INDEX CONCURRENTLY idx_vehicles_tenant_performance ON vehicles (tenant_id, status);

-- 阶段5：启用RLS策略
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_users ON users USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
CREATE POLICY tenant_isolation_shipments ON shipments USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
CREATE POLICY tenant_isolation_vehicles ON vehicles USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

**性能评估**:
- 单租户查询延迟: < 5ms (索引优化后)
- 多租户并发: 支持50租户 x 100用户 = 5000并发访问
- 数据增长: 每租户每月100万记录，3年内性能稳定
- RLS开销: 索引优化后 < 1% 额外性能损耗