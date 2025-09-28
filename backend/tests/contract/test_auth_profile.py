import pytest
from httpx import AsyncClient
from jsonschema import validate

# 用户资料响应schema
USER_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "username": {"type": "string"},
        "email": {"type": "string"},
        "role": {"type": "string"},
        "tenantId": {"type": "string"},
        "tenantName": {"type": "string"},
        "avatar": {"type": ["string", "null"]},
        "phone": {"type": ["string", "null"]},
        "isActive": {"type": "boolean"},
        "lastLoginAt": {"type": ["string", "null"]},
        "createdAt": {"type": "string"}
    },
    "required": ["id", "username", "email", "role", "tenantId", "isActive", "createdAt"]
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
async def test_auth_me_contract_valid_token():
    """测试获取用户资料接口合约 - 有效token"""
    # 模拟有效响应
    expected_response = {
        "id": "uuid-123",
        "username": "testuser",
        "email": "test@example.com",
        "role": "user",
        "tenantId": "tenant-uuid-456",
        "tenantName": "测试公司",
        "avatar": None,
        "phone": None,
        "isActive": True,
        "lastLoginAt": "2025-09-27T10:00:00Z",
        "createdAt": "2025-09-27T09:00:00Z"
    }

    # 验证响应格式
    validate(instance=expected_response, schema=USER_PROFILE_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_auth_me_contract_invalid_token():
    """测试获取用户资料接口合约 - 无效token"""
    # 模拟401响应
    error_response = {
        "detail": "Could not validate credentials",
        "code": "INVALID_TOKEN"
    }

    validate(instance=error_response, schema=ERROR_RESPONSE_SCHEMA)


@pytest.mark.asyncio
async def test_auth_me_contract_missing_token():
    """测试获取用户资料接口合约 - 缺少token"""
    # 模拟401响应
    error_response = {
        "detail": "Authorization header missing"
    }

    validate(instance=error_response, schema=ERROR_RESPONSE_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"