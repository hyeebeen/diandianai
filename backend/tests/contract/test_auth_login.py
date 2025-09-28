import pytest
from httpx import AsyncClient
from jsonschema import validate

# 请求schema
PASSWORD_LOGIN_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "identifier": {"type": "string"},
        "password": {"type": "string"}
    },
    "required": ["identifier", "password"]
}

WECHAT_LOGIN_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string"}
    },
    "required": ["code"]
}

# 响应schema
LOGIN_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "accessToken": {"type": "string"},
        "refreshToken": {"type": "string"},
        "tokenType": {"type": "string"},
        "expiresIn": {"type": "integer"},
        "user": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "username": {"type": "string"},
                "email": {"type": "string"},
                "role": {"type": "string"},
                "tenantId": {"type": "string"}
            },
            "required": ["id", "username", "role", "tenantId"]
        }
    },
    "required": ["accessToken", "refreshToken", "tokenType", "expiresIn", "user"]
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
async def test_login_contract_password_valid_request():
    """测试登录接口合约 - 密码登录有效请求"""
    request_data = {
        "identifier": "test@example.com",
        "password": "password123"
    }

    # 验证请求格式
    validate(instance=request_data, schema=PASSWORD_LOGIN_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    # 当我们有了实际的client时，可以这样测试：
    # response = await test_client.post("/api/auth/login", json=request_data)
    # assert response.status_code == 200
    # validate(instance=response.json(), schema=LOGIN_RESPONSE_SCHEMA)

    # 目前标记为预期失败的测试
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_login_contract_wechat_valid_request():
    """测试登录接口合约 - 微信登录有效请求"""
    request_data = {
        "code": "wx_code_123"
    }

    # 验证请求格式
    validate(instance=request_data, schema=WECHAT_LOGIN_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_login_contract_invalid_request():
    """测试登录接口合约 - 无效请求"""
    request_data = {"identifier": "test"}  # 缺少必需的password字段

    # 这应该在请求验证时失败
    with pytest.raises(Exception):
        validate(instance=request_data, schema=PASSWORD_LOGIN_REQUEST_SCHEMA)


@pytest.mark.asyncio
async def test_login_contract_unauthorized_response():
    """测试登录接口合约 - 401响应格式"""
    # 模拟401响应应该符合错误响应schema
    error_response = {
        "detail": "Invalid credentials",
        "code": "INVALID_CREDENTIALS"
    }

    validate(instance=error_response, schema=ERROR_RESPONSE_SCHEMA)


# 这些测试目前都会失败，符合TDD要求
# 在实现API后，这些测试应该通过