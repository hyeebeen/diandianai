import pytest
from httpx import AsyncClient
from jsonschema import validate

# AI任务创建请求schema
TASK_CREATE_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["create_shipment", "update_status", "query_location", "get_route", "generate_report"]
        },
        "parameters": {
            "type": "object",
            "additionalProperties": True
        },
        "conversationId": {"type": "string"},
        "requiresConfirmation": {"type": "boolean"}
    },
    "required": ["action", "parameters"]
}

# AI任务响应schema
TASK_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "taskId": {"type": "string"},
        "action": {"type": "string"},
        "status": {
            "type": "string",
            "enum": ["pending", "processing", "completed", "failed", "cancelled"]
        },
        "result": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "object"}
            },
            "required": ["success", "message"]
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "createdAt": {"type": "string"},
        "updatedAt": {"type": "string"}
    },
    "required": ["taskId", "action", "status", "createdAt"]
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
async def test_ai_tasks_contract_create_shipment():
    """测试AI任务接口合约 - 创建运单任务"""
    request_data = {
        "action": "create_shipment",
        "parameters": {
            "pickup_address": "北京市朝阳区望京SOHO",
            "delivery_address": "上海市浦东新区陆家嘴金融区",
            "customer_name": "张三",
            "weight_kg": 25.5,
            "commodity_type": "电子产品"
        },
        "conversationId": "conv-uuid-123",
        "requiresConfirmation": True
    }

    # 验证请求格式
    validate(instance=request_data, schema=TASK_CREATE_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_ai_tasks_contract_update_status():
    """测试AI任务接口合约 - 更新状态任务"""
    request_data = {
        "action": "update_status",
        "parameters": {
            "shipment_id": "shipment-456",
            "new_status": "in_transit",
            "location": "天津市"
        },
        "conversationId": "conv-uuid-123",
        "requiresConfirmation": False
    }

    # 验证请求格式
    validate(instance=request_data, schema=TASK_CREATE_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_ai_tasks_contract_query_location():
    """测试AI任务接口合约 - 查询位置任务"""
    request_data = {
        "action": "query_location",
        "parameters": {
            "shipment_id": "shipment-789"
        }
    }

    # 验证请求格式
    validate(instance=request_data, schema=TASK_CREATE_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_ai_tasks_response_format():
    """测试AI任务响应格式"""
    # 模拟成功响应
    expected_response = {
        "taskId": "task-uuid-abc",
        "action": "create_shipment",
        "status": "completed",
        "result": {
            "success": True,
            "message": "运单创建成功",
            "data": {
                "shipment_id": "shipment-new-123",
                "shipment_number": "SH-BJ-20240927-001"
            }
        },
        "confidence": 0.95,
        "createdAt": "2025-09-27T10:30:00Z",
        "updatedAt": "2025-09-27T10:30:05Z"
    }

    validate(instance=expected_response, schema=TASK_RESPONSE_SCHEMA)


@pytest.mark.asyncio
async def test_ai_tasks_contract_invalid_action():
    """测试AI任务接口合约 - 无效动作"""
    invalid_request = {
        "action": "invalid_action",  # 不在枚举范围内
        "parameters": {}
    }

    # 这应该在请求验证时失败
    with pytest.raises(Exception):
        validate(instance=invalid_request, schema=TASK_CREATE_REQUEST_SCHEMA)


@pytest.mark.asyncio
async def test_ai_tasks_contract_missing_parameters():
    """测试AI任务接口合约 - 缺少参数"""
    invalid_request = {
        "action": "create_shipment"
        # 缺少必需的parameters字段
    }

    # 这应该在请求验证时失败
    with pytest.raises(Exception):
        validate(instance=invalid_request, schema=TASK_CREATE_REQUEST_SCHEMA)