# 测试文档

## 测试框架
使用 Playwright 进行端到端测试、性能测试、负载测试和安全测试。

## 测试结构

```
tests/
├── e2e/                    # 端到端测试
│   ├── auth.spec.ts        # 认证流程测试
│   ├── shipment-workflow.spec.ts # 运单业务流程测试
│   ├── ai-chat.spec.ts     # AI聊天功能测试
│   └── realtime-features.spec.ts # 实时功能测试
├── performance/            # 性能测试
│   └── api-performance.spec.ts # API响应时间测试
├── load/                   # 负载测试
│   └── load-testing.spec.ts # 并发负载测试
├── security/               # 安全测试
│   └── security-tests.spec.ts # 安全漏洞测试
└── README.md              # 本文档
```

## 运行测试

### 前提条件
1. 确保前端开发服务器运行在 http://localhost:8080
2. 确保后端API服务器运行在 http://localhost:8000
3. 确保测试用户账户已创建：
   - 用户名: test@example.com
   - 密码: testpassword

### 测试命令

```bash
# 运行所有E2E测试
npm run test:e2e

# 运行E2E测试(带UI界面)
npm run test:e2e:ui

# 运行E2E测试(显示浏览器)
npm run test:e2e:headed

# 运行性能测试
npm run test:performance

# 运行负载测试
npm run test:load

# 运行安全测试
npm run test:security

# 运行所有测试并生成HTML报告
npm run test:all
```

## 测试覆盖范围

### E2E测试 (T078)
- **认证流程测试**: 登录、登出、权限验证
- **运单工作流测试**: 运单列表、搜索、筛选、详情查看
- **AI聊天测试**: 消息发送、实时响应、对话管理
- **实时功能测试**: SSE连接、通知系统、状态更新

### 性能测试 (T079)
- **API响应时间验证**:
  - 登录 API < 2秒
  - 运单列表 API < 1.5秒
  - 运单详情 API < 1秒
  - GPS数据 API < 800毫秒
  - AI响应 API < 5秒
- **并发请求处理**
- **分页和筛选性能**

### 负载测试 (T080)
- **低负载测试**: 10个并发用户
- **中等负载测试**: 50个并发用户
- **高负载测试**: 100个并发用户
- **压力测试**: 200个并发用户
- **SSE连接负载测试**: 20个并发SSE连接
- **持续负载测试**: 1分钟持续负载

### 安全测试 (T081)
- **认证安全**: 无效token、恶意header、暴力破解防护
- **多租户隔离**: 跨租户数据访问防护
- **输入验证**: XSS防护、SQL注入防护
- **API安全头**: CORS配置、安全响应头
- **数据隐私**: 敏感信息保护、错误信息安全
- **访问控制**: 资源权限验证

## 测试数据要求

### 认证测试用户
```
用户名: test@example.com
密码: testpassword
租户: 默认租户
```

### 多租户测试(可选)
```
租户A用户: test@example.com
租户B用户: test@tenantb.com
租户ID: tenant-b
```

## 性能基准

### API响应时间阈值
- 认证: < 2000ms
- 运单列表: < 1500ms
- 运单详情: < 1000ms
- GPS数据: < 800ms
- AI响应: < 5000ms
- 搜索: < 1000ms

### 负载测试成功率
- 低负载(10用户): > 95%
- 中等负载(50用户): > 90%
- 高负载(100用户): > 85%
- 压力测试(200用户): > 70%

## 故障排除

### 常见问题

1. **测试连接失败**
   - 检查前后端服务是否正常运行
   - 验证端口配置是否正确

2. **认证测试失败**
   - 确认测试用户账户已创建
   - 检查用户名密码是否正确

3. **负载测试性能不达标**
   - 检查系统资源使用情况
   - 验证数据库连接池配置
   - 确认缓存策略是否有效

4. **安全测试误报**
   - 检查安全策略配置
   - 验证输入验证规则
   - 确认错误处理机制

### 调试技巧

1. **查看测试报告**
   ```bash
   # 运行测试后查看HTML报告
   npx playwright show-report
   ```

2. **录制测试执行过程**
   ```bash
   # 录制视频和截图
   npm run test:e2e:headed
   ```

3. **调试特定测试**
   ```bash
   # 只运行特定测试文件
   npx playwright test auth.spec.ts --headed
   ```

## 持续集成

测试可以集成到CI/CD流程中：

```yaml
# 示例 GitHub Actions 配置
- name: Run E2E Tests
  run: |
    npm run build
    npm run test:e2e

- name: Run Performance Tests
  run: npm run test:performance

- name: Run Security Tests
  run: npm run test:security
```

## 测试最佳实践

1. **测试隔离**: 每个测试应独立运行，不依赖其他测试
2. **数据清理**: 测试后清理测试数据，避免影响后续测试
3. **错误处理**: 合理使用try-catch，提供清晰的错误信息
4. **等待策略**: 使用合适的等待条件，避免时间竞争
5. **断言明确**: 使用具体的断言，提供清晰的失败信息

## 报告和分析

测试完成后会生成：
- HTML测试报告 (test-results/index.html)
- 截图和视频记录 (test-results/)
- 性能指标数据
- 覆盖率报告

定期审查测试结果，持续优化系统性能和安全性。