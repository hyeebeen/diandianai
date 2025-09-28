import pytest
from httpx import AsyncClient
from jsonschema import validate

# 注册请求schema
REGISTER_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "email": {"type": "string"},
        "password": {"type": "string"},
        "confirmPassword": {"type": "string"},
        "role": {"type": "string"},
        "tenantCode": {"type": "string"}
    },
    "required": ["username", "email", "password", "confirmPassword"]
}

# 注册响应schema
REGISTER_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
        "userId": {"type": "string"}
    },
    "required": ["message", "userId"]
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
async def test_register_contract_valid_request():
    """测试注册接口合约 - 有效请求"""
    request_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "confirmPassword": "password123",
        "role": "user",
        "tenantCode": "default"
    }

    # 验证请求格式
    validate(instance=request_data, schema=REGISTER_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_register_contract_missing_required_fields():
    """测试注册接口合约 - 缺少必需字段"""
    request_data = {
        "username": "testuser",
        "email": "test@example.com"
        # 缺少password和confirmPassword
    }

    # 这应该在请求验证时失败
    with pytest.raises(Exception):
        validate(instance=request_data, schema=REGISTER_REQUEST_SCHEMA)


@pytest.mark.asyncio
async def test_register_contract_conflict_response():
    """测试注册接口合约 - 409冲突响应格式"""
    # 模拟409响应应该符合错误响应schema
    error_response = {
        "detail": "User already exists",
        "code": "USER_EXISTS"
    }

    validate(instance=error_response, schema=ERROR_RESPONSE_SCHEMA)