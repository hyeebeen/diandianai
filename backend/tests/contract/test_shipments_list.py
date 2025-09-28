import pytest
from jsonschema import validate

# 运单列表响应schema
SHIPMENT_LIST_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "shipmentNumber": {"type": "string"},
                    "pickupAddress": {"type": "string"},
                    "deliveryAddress": {"type": "string"},
                    "status": {"type": "string"},
                    "customerName": {"type": "string"},
                    "createdAt": {"type": "string"}
                },
                "required": ["id", "shipmentNumber", "status"]
            }
        },
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "limit": {"type": "integer"},
        "totalPages": {"type": "integer"}
    },
    "required": ["items", "total", "page", "limit", "totalPages"]
}


@pytest.mark.asyncio
async def test_get_shipments_contract():
    """测试获取运单列表接口合约"""
    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_shipment_list_response_format():
    """测试运单列表响应格式"""
    expected_response = {
        "items": [
            {
                "id": "uuid-1",
                "shipmentNumber": "SH-001",
                "pickupAddress": "上海",
                "deliveryAddress": "北京",
                "status": "in_transit",
                "customerName": "客户A",
                "createdAt": "2025-09-27T10:00:00Z"
            }
        ],
        "total": 1,
        "page": 1,
        "limit": 20,
        "totalPages": 1
    }

    validate(instance=expected_response, schema=SHIPMENT_LIST_RESPONSE_SCHEMA)