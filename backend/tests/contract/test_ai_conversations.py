import pytest
from httpx import AsyncClient
from jsonschema import validate

# 对话列表请求schema
CONVERSATIONS_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "page": {"type": "integer", "minimum": 1},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100}
    }
}

# 对话列表响应schema
CONVERSATIONS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "conversations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "lastMessage": {"type": "string"},
                    "lastActivityAt": {"type": "string"},
                    "messageCount": {"type": "integer"},
                    "isActive": {"type": "boolean"}
                },
                "required": ["id", "title", "lastActivityAt", "messageCount", "isActive"]
            }
        },
        "pagination": {
            "type": "object",
            "properties": {
                "page": {"type": "integer"},
                "limit": {"type": "integer"},
                "total": {"type": "integer"},
                "pages": {"type": "integer"}
            },
            "required": ["page", "limit", "total", "pages"]
        }
    },
    "required": ["conversations", "pagination"]
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
async def test_ai_conversations_contract_valid_request():
    """测试AI对话列表接口合约 - 有效请求"""
    query_params = {
        "page": 1,
        "limit": 10
    }

    # 验证查询参数格式
    validate(instance=query_params, schema=CONVERSATIONS_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_ai_conversations_contract_default_pagination():
    """测试AI对话列表接口合约 - 默认分页"""
    query_params = {}

    # 空查询参数应该也是有效的，使用默认值
    validate(instance=query_params, schema=CONVERSATIONS_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_ai_conversations_response_format():
    """测试AI对话列表响应格式"""
    # 模拟成功响应
    expected_response = {
        "conversations": [
            {
                "id": "conv-uuid-123",
                "title": "运单创建咨询",
                "lastMessage": "我已经为您创建了运单",
                "lastActivityAt": "2025-09-27T10:30:00Z",
                "messageCount": 5,
                "isActive": True
            },
            {
                "id": "conv-uuid-456",
                "title": "货物追踪查询",
                "lastMessage": "您的货物正在运输中",
                "lastActivityAt": "2025-09-27T09:15:00Z",
                "messageCount": 3,
                "isActive": True
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 10,
            "total": 25,
            "pages": 3
        }
    }

    validate(instance=expected_response, schema=CONVERSATIONS_RESPONSE_SCHEMA)


@pytest.mark.asyncio
async def test_ai_conversations_contract_invalid_pagination():
    """测试AI对话列表接口合约 - 无效分页参数"""
    invalid_params = {
        "page": 0,  # page不能为0
        "limit": 200  # limit超过最大值
    }

    # 这应该在请求验证时失败
    with pytest.raises(Exception):
        validate(instance=invalid_params, schema=CONVERSATIONS_REQUEST_SCHEMA)


@pytest.mark.asyncio
async def test_ai_conversations_contract_unauthorized():
    """测试AI对话列表接口合约 - 未授权访问"""
    # 模拟401响应
    error_response = {
        "detail": "Authentication required",
        "code": "UNAUTHORIZED"
    }

    validate(instance=error_response, schema=ERROR_RESPONSE_SCHEMA)