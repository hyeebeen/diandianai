# Tasks: AI驱动的物流管理数字化平台

**Input**: Design documents from `/specs/001-ai-ai-ai/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## 执行概览

基于现有前端React应用和设计文档，实现完整的后端API服务，支持AI助手、物流管理、实时GPS追踪等功能。

**技术栈**: FastAPI + Instructor + Celery + PostgreSQL + Row-Level Security多租户
**现有前端**: React 18 + TypeScript + shadcn-ui (src/ 目录，完全实现)
**新增后端**: backend/ 目录结构

## Format: `[ID] [P?] Description`
- **[P]**: 可并行执行（不同文件，无依赖）
- 包含具体文件路径

---

## Phase 3.1: 项目设置和环境配置

- [x] T001 创建后端项目结构 backend/ 目录和子目录架构
  **📋 详细指导**: `implementation-guide.md#T001完成标准`
- [x] T002 初始化Python项目：pyproject.toml配置uv包管理器和依赖
  **📋 详细指导**: `implementation-guide.md#pyproject.toml完整配置`
- [x] T003 [P] 配置代码质量工具：ruff、black、pre-commit hooks
  **📋 详细指导**: `implementation-guide.md#pyproject.toml完整配置` (工具配置部分)
- [x] T004 [P] 设置Docker开发环境：docker-compose.yml (PostgreSQL + Redis + RabbitMQ)
  **📋 详细指导**: `implementation-guide.md#docker-compose.yml完整配置`
- [x] T005 [P] 配置环境变量模板：.env.example 和 backend/src/core/config.py
  **📋 详细指导**: `implementation-guide.md#.env.example环境变量模板`

## Phase 3.2: 数据库和多租户基础设施

- [x] T006 PostgreSQL数据库设置：初始化脚本和Row-Level Security配置
- [x] T007 [P] 多租户基础模型 backend/src/models/base.py (BaseModel + tenant_id)
  **📋 详细指导**: `implementation-guide.md#backend/src/models/base.py`
- [x] T008 [P] 数据库连接层 backend/src/core/database.py (SQLAlchemy + asyncpg)
  **📋 详细指导**: `data-model.md#多租户架构设计` + `implementation-guide.md`
- [x] T009 [P] 租户中间件 backend/src/core/security.py (RLS策略和tenant_id注入)
  **📋 详细指导**: `data-model.md#跨租户查询控制` + `implementation-guide.md`

## Phase 3.3: 合约测试优先 (TDD) ⚠️ 必须在实现前完成

**关键**: 这些测试必须编写并失败，然后才能进行任何实现

### 认证API合约测试
- [x] T010 [P] 合约测试 POST /api/auth/login in backend/tests/contract/test_auth_login.py
  **📋 详细指导**: `implementation-guide.md#backend/tests/contract/test_auth_login.py` + `contracts/auth-api.yaml`
- [x] T011 [P] 合约测试 POST /api/auth/register in backend/tests/contract/test_auth_register.py
  **📋 参考**: T010测试模板 + `contracts/auth-api.yaml`
- [x] T012 [P] 合约测试 GET /api/auth/me in backend/tests/contract/test_auth_profile.py
  **📋 参考**: T010测试模板 + `contracts/auth-api.yaml`
- [x] T013 [P] 合约测试 POST /api/auth/refresh in backend/tests/contract/test_auth_refresh.py
  **📋 参考**: T010测试模板 + `contracts/auth-api.yaml`

### AI助手API合约测试
- [x] T014 [P] 合约测试 POST /api/ai/chat in backend/tests/contract/test_ai_chat.py
- [x] T015 [P] 合约测试 GET /api/ai/conversations in backend/tests/contract/test_ai_conversations.py
- [x] T016 [P] 合约测试 POST /api/ai/tasks in backend/tests/contract/test_ai_tasks.py
- [x] T017 [P] 合约测试 GET /api/ai/summary in backend/tests/contract/test_ai_summary.py

### 运单API合约测试
- [x] T018 [P] 合约测试 POST /api/shipments in backend/tests/contract/test_shipments_create.py
- [x] T019 [P] 合约测试 GET /api/shipments in backend/tests/contract/test_shipments_list.py
- [x] T020 [P] 合约测试 GET /api/shipments/{id} in backend/tests/contract/test_shipments_detail.py
- [x] T021 [P] 合约测试 PUT /api/shipments/{id}/status in backend/tests/contract/test_shipments_status.py

### GPS追踪API合约测试
- [x] T022 [P] 合约测试 GET /api/gps/realtime/{shipment_id} in backend/tests/contract/test_gps_realtime.py
- [x] T023 [P] 合约测试 POST /api/gps/locations in backend/tests/contract/test_gps_locations.py
- [x] T024 [P] 合约测试 GET /api/gps/route/{shipment_id} in backend/tests/contract/test_gps_route.py

### 集成测试
- [x] T025 [P] 集成测试：完整运单流程 in backend/tests/integration/test_shipment_workflow.py
- [x] T026 [P] 集成测试：AI助手交互流程 in backend/tests/integration/test_ai_conversation.py
- [x] T027 [P] 集成测试：多租户数据隔离 in backend/tests/integration/test_multi_tenant.py

## Phase 3.4: 数据模型实现 (在测试失败后)

- [x] T028 [P] 用户和认证模型 backend/src/models/users.py
- [x] T029 [P] AI配置和交互模型 backend/src/models/ai_models.py
- [x] T030 [P] 运单和物流模型 backend/src/models/logistics.py
  **📋 详细指导**: `implementation-guide.md#backend/src/models/logistics.py` + `frontend-backend-mapping.md#Load↔Shipment映射`
- [x] T031 [P] GPS和位置模型 backend/src/models/gps.py
  **📋 参考**: `data-model.md#核心实体` + T030模型模板
- [x] T032 [P] 业务摘要模型 backend/src/models/summaries.py
- [x] T033 数据库迁移脚本和关系定义 backend/alembic/

## Phase 3.5: 服务层实现

- [x] T034 [P] 认证服务 backend/src/services/auth_service.py (JWT + 多租户)
- [x] T035 [P] AI助手核心服务 backend/src/services/ai_service.py (Instructor集成)
  **📋 详细指导**: `implementation-guide.md#backend/src/services/ai_service.py` + `research.md#AI推理框架选择`
- [x] T036 [P] 运单管理服务 backend/src/services/logistics_service.py
  **📋 参考**: T035服务模板 + `data-model.md#核心实体`
- [x] T037 [P] GPS追踪服务 backend/src/services/gps_service.py
- [x] T038 [P] 多渠道通知服务 backend/src/services/notification_service.py

## Phase 3.6: 外部集成服务

- [x] T039 [P] G7定位API集成 backend/src/integrations/g7_api.py
- [x] T040 [P] 微信API集成 backend/src/integrations/wechat_api.py
- [x] T041 [P] 短信服务集成 backend/src/integrations/sms_api.py
- [x] T042 [P] AI模型提供商接口 backend/src/integrations/ai_providers/openai_provider.py
- [x] T043 [P] 国产AI模型集成 backend/src/integrations/ai_providers/domestic_providers.py

## Phase 3.7: API端点实现

### 认证端点
- [x] T044 POST /api/auth/login 端点实现 backend/src/api/auth.py
- [x] T045 POST /api/auth/register 端点实现 (修改 backend/src/api/auth.py)
- [x] T046 GET /api/auth/me 端点实现 (修改 backend/src/api/auth.py)
- [x] T047 POST /api/auth/refresh 端点实现 (修改 backend/src/api/auth.py)

### AI助手端点
- [x] T048 POST /api/ai/chat 端点实现 backend/src/api/ai.py
- [x] T049 GET /api/ai/conversations 端点实现 (修改 backend/src/api/ai.py)
- [x] T050 POST /api/ai/tasks 端点实现 (修改 backend/src/api/ai.py)
- [x] T051 GET /api/ai/summary 端点实现 (修改 backend/src/api/ai.py)

### 运单管理端点
- [x] T052 POST /api/shipments 端点实现 backend/src/api/logistics.py
- [x] T053 GET /api/shipments 端点实现 (修改 backend/src/api/logistics.py)
- [x] T054 GET /api/shipments/{id} 端点实现 (修改 backend/src/api/logistics.py)
- [x] T055 PUT /api/shipments/{id}/status 端点实现 (修改 backend/src/api/logistics.py)

### GPS和实时数据端点
- [x] T056 [P] 实时SSE端点 backend/src/api/sse.py (GPS位置流)
- [x] T057 GET /api/gps/realtime/{shipment_id} 端点实现 (修改 backend/src/api/sse.py)
- [x] T058 POST /api/gps/locations 端点实现 (修改 backend/src/api/sse.py)
- [x] T059 GET /api/gps/route/{shipment_id} 端点实现 (修改 backend/src/api/sse.py)

### 管理员配置端点
- [x] T060 [P] 管理员API backend/src/api/admin.py (AI模型配置管理)

## Phase 3.8: Celery异步任务系统

- [x] T061 [P] Celery应用配置 backend/src/core/celery_app.py
- [x] T062 [P] GPS数据处理任务 backend/src/tasks/gps_tasks.py
- [x] T063 [P] AI对话处理任务 backend/src/tasks/ai_tasks.py
- [x] T064 [P] 通知发送任务 backend/src/tasks/notification_tasks.py

## Phase 3.9: 应用集成和配置

- [x] T065 FastAPI应用主程序 backend/src/main.py (路由注册 + 中间件)
- [x] T066 CORS和安全中间件配置 (修改 backend/src/main.py)
- [x] T067 异常处理和日志记录 (修改 backend/src/main.py)
- [x] T068 启动脚本和健康检查端点 (修改 backend/src/main.py)

## Phase 3.10: 前端API集成

- [x] T069 [P] 前端API客户端配置 src/services/api.ts (替换mockData)
  **📋 详细指导**: `implementation-guide.md#src/services/api.ts` + `frontend-backend-mapping.md#API响应转换器`
- [ ] T070 [P] 认证服务集成 src/services/auth.ts
  **📋 参考**: T069 API客户端模板
- [ ] T071 [P] SSE实时数据服务 src/services/sse.ts (替换mock GPS数据)
  **📋 详细指导**: `implementation-guide.md#src/services/sse.ts`
- [ ] T072 更新ChatPanel组件连接真实AI API (修改 src/components/ChatPanel.tsx)
  **📋 详细指导**: `frontend-backend-mapping.md#3. ChatPanel组件更新`
- [ ] T073 更新RealTimeGPSMap组件连接SSE (修改 src/components/RealTimeGPSMap.tsx)
  **📋 详细指导**: `frontend-backend-mapping.md#2. RealTimeGPSMap组件更新`
- [ ] T074 更新LoadList组件连接真实API (修改 src/components/LoadList.tsx)
  **📋 详细指导**: `frontend-backend-mapping.md#1. LoadList组件更新`

## Phase 3.11: 数据迁移和种子数据

- [x] T075 [P] 租户和用户种子数据脚本 backend/scripts/seed_data.py
- [x] T076 [P] 测试运单数据脚本 backend/scripts/seed_shipments.py
- [x] T077 [P] AI模型配置种子数据 backend/scripts/seed_ai_config.py

## Phase 3.12: 完整性测试和优化

- [ ] T078 [P] 端到端测试：完整业务流程 backend/tests/e2e/test_complete_workflow.py
- [ ] T079 [P] 性能测试：API响应时间验证 backend/tests/performance/test_api_performance.py
- [ ] T080 [P] 负载测试：1000-5000并发用户 backend/tests/performance/test_load.py
- [ ] T081 [P] 安全测试：多租户隔离验证 backend/tests/security/test_tenant_isolation.py

## Phase 3.13: 部署和运维

- [ ] T082 [P] 生产环境Docker配置 Dockerfile + docker-compose.prod.yml
- [ ] T083 [P] CI/CD管道配置 .github/workflows/backend.yml
- [ ] T084 [P] 监控和日志配置 backend/src/core/monitoring.py
- [ ] T085 [P] API文档生成和部署 backend/docs/ (自动从OpenAPI生成)

---

## 依赖关系

### 严格顺序依赖
- **环境设置** (T001-T005) → **数据库基础** (T006-T009) → **所有后续任务**
- **合约测试** (T010-T027) → **对应的实现任务** (T028及后续)
- **数据模型** (T028-T033) → **服务层** (T034-T043) → **API端点** (T044-T060)
- **核心API** (T044-T060) → **前端集成** (T069-T074)
- **基础功能** → **Celery任务** (T061-T064) → **完整性测试** (T078-T081)

### 并行执行分组
```bash
# 合约测试可并行执行 (不同文件)
T010-T027: 所有合约测试

# 数据模型可并行创建 (不同文件)
T028-T032: 所有模型文件

# 服务层可并行实现 (不同文件)
T034-T043: 所有服务和集成

# 前端集成可并行进行 (不同组件文件)
T069-T071, T075-T077: API集成和种子数据
```

## 特殊注意事项

### 前端代码保护
- ✅ **保留所有现有** src/components/ 组件
- ✅ **保持现有界面设计**和用户体验
- ✅ **兼容现有TypeScript类型**定义
- ✅ **重用shadcn-ui组件库**配置
- ✅ **渐进式集成**: MockData → Real API → 实时功能

### 多租户开发重点
- 🔒 **所有API**必须强制租户隔离
- 🔒 **数据库查询**必须包含tenant_id过滤
- 🔒 **测试覆盖**多租户数据隔离场景
- 🔒 **性能优化**考虑RLS策略效率

### AI功能集成
- 🤖 **Instructor框架**替代LangChain (30%性能提升)
- 🤖 **支持国内外主流**AI模型API
- 🤖 **关键任务确认**机制 (创建运单、状态变更)
- 🤖 **渠道优先级**: 微信 > 电话 > 短信

## 验证检查清单

- [x] 所有合约都有对应测试 (T010-T024)
- [x] 所有实体都有模型任务 (T028-T032)
- [x] 所有测试都在实现之前 (Phase 3.3 → 3.4+)
- [x] 并行任务真正独立 ([P]标记的不同文件)
- [x] 每个任务指定确切文件路径
- [x] 没有任务修改与其他[P]任务相同的文件
- [x] 覆盖前端集成和现有组件保护
- [x] 包含多租户、AI、GPS实时追踪所有核心功能