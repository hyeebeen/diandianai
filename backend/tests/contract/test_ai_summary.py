import pytest
from httpx import AsyncClient
from jsonschema import validate

# AI摘要请求schema
SUMMARY_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "period": {
            "type": "string",
            "enum": ["daily", "weekly", "monthly"]
        },
        "startDate": {
            "type": "string",
            "format": "date"
        },
        "endDate": {
            "type": "string",
            "format": "date"
        }
    }
}

# AI摘要响应schema
SUMMARY_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "period": {
            "type": "string",
            "enum": ["daily", "weekly", "monthly"]
        },
        "startDate": {"type": "string"},
        "endDate": {"type": "string"},
        "statistics": {
            "type": "object",
            "properties": {
                "totalInteractions": {"type": "integer"},
                "shipmentsCreated": {"type": "integer"},
                "shipmentsCompleted": {"type": "integer"},
                "averageResponseTime": {"type": "number"},
                "successRate": {"type": "number"}
            },
            "required": ["totalInteractions", "shipmentsCreated", "shipmentsCompleted"]
        },
        "insights": {
            "type": "object",
            "properties": {
                "keyTopics": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "commonTasks": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "trends": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "metric": {"type": "string"},
                            "change": {"type": "number"},
                            "direction": {"type": "string", "enum": ["up", "down", "stable"]}
                        },
                        "required": ["metric", "change", "direction"]
                    }
                }
            },
            "required": ["keyTopics", "commonTasks", "suggestions"]
        },
        "generatedAt": {"type": "string"},
        "generatedBy": {"type": "string"}
    },
    "required": ["id", "period", "startDate", "endDate", "statistics", "insights", "generatedAt"]
}

ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "detail": {"type": "string"},
        "code": {"type": "string"}
    },
    "required": ["detail"]
}


@pytest.mark.asyncio
async def test_ai_summary_contract_daily():
    """测试AI摘要接口合约 - 日报"""
    query_params = {
        "period": "daily",
        "startDate": "2025-09-27"
    }

    # 验证查询参数格式
    validate(instance=query_params, schema=SUMMARY_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_ai_summary_contract_weekly():
    """测试AI摘要接口合约 - 周报"""
    query_params = {
        "period": "weekly",
        "startDate": "2025-09-23",
        "endDate": "2025-09-29"
    }

    # 验证查询参数格式
    validate(instance=query_params, schema=SUMMARY_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_ai_summary_contract_monthly():
    """测试AI摘要接口合约 - 月报"""
    query_params = {
        "period": "monthly",
        "startDate": "2025-09-01",
        "endDate": "2025-09-30"
    }

    # 验证查询参数格式
    validate(instance=query_params, schema=SUMMARY_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_ai_summary_response_format():
    """测试AI摘要响应格式"""
    # 模拟成功响应
    expected_response = {
        "id": "summary-uuid-123",
        "period": "weekly",
        "startDate": "2025-09-23",
        "endDate": "2025-09-29",
        "statistics": {
            "totalInteractions": 156,
            "shipmentsCreated": 23,
            "shipmentsCompleted": 18,
            "averageResponseTime": 1.8,
            "successRate": 0.92
        },
        "insights": {
            "keyTopics": [
                "运单创建",
                "货物追踪",
                "状态更新",
                "路线优化"
            ],
            "commonTasks": [
                "创建北京到上海的运单",
                "查询货物当前位置",
                "更新运单状态为已发货"
            ],
            "suggestions": [
                "建议在高峰期增加客服响应",
                "优化常见查询的自动回复",
                "增加运单模板功能"
            ],
            "trends": [
                {
                    "metric": "daily_interactions",
                    "change": 15.2,
                    "direction": "up"
                },
                {
                    "metric": "response_time",
                    "change": -8.5,
                    "direction": "down"
                }
            ]
        },
        "generatedAt": "2025-09-27T10:30:00Z",
        "generatedBy": "ai-analyst-v1.0"
    }

    validate(instance=expected_response, schema=SUMMARY_RESPONSE_SCHEMA)


@pytest.mark.asyncio
async def test_ai_summary_contract_invalid_period():
    """测试AI摘要接口合约 - 无效周期"""
    invalid_params = {
        "period": "yearly",  # 不在枚举范围内
        "startDate": "2025-09-01"
    }

    # 这应该在请求验证时失败
    with pytest.raises(Exception):
        validate(instance=invalid_params, schema=SUMMARY_REQUEST_SCHEMA)


@pytest.mark.asyncio
async def test_ai_summary_contract_unauthorized():
    """测试AI摘要接口合约 - 未授权访问"""
    # 模拟401响应
    error_response = {
        "detail": "Authentication required",
        "code": "UNAUTHORIZED"
    }

    validate(instance=error_response, schema=ERROR_RESPONSE_SCHEMA)