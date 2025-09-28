import pytest
from jsonschema import validate

# 创建运单请求schema
CREATE_SHIPMENT_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "pickupAddress": {"type": "string"},
        "deliveryAddress": {"type": "string"},
        "customerName": {"type": "string"},
        "transportMode": {"type": "string"},
        "equipmentType": {"type": "string"},
        "weightKg": {"type": "number"},
        "commodityType": {"type": "string"},
        "packingType": {"type": "string"},
        "pickupCoordinates": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 2,
            "maxItems": 2
        },
        "deliveryCoordinates": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 2,
            "maxItems": 2
        },
        "notes": {"type": "string"}
    },
    "required": ["pickupAddress", "deliveryAddress", "customerName"]
}

# 创建运单响应schema
CREATE_SHIPMENT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "shipmentNumber": {"type": "string"},
        "status": {"type": "string"},
        "createdAt": {"type": "string"},
        "estimatedDelivery": {"type": ["string", "null"]}
    },
    "required": ["id", "shipmentNumber", "status", "createdAt"]
}


@pytest.mark.asyncio
async def test_create_shipment_contract_valid_request():
    """测试创建运单接口合约 - 有效请求"""
    request_data = {
        "pickupAddress": "上海市浦东新区张江高科技园区",
        "deliveryAddress": "北京市朝阳区CBD商务区",
        "customerName": "测试客户有限公司",
        "transportMode": "整车运输",
        "equipmentType": "厢式货车",
        "weightKg": 5000.0,
        "commodityType": "电子产品",
        "packingType": "纸箱包装",
        "pickupCoordinates": [121.5, 31.2],
        "deliveryCoordinates": [116.4, 39.9],
        "notes": "易碎品，请轻拿轻放"
    }

    # 验证请求格式
    validate(instance=request_data, schema=CREATE_SHIPMENT_REQUEST_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "API endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_create_shipment_contract_missing_required():
    """测试创建运单接口合约 - 缺少必需字段"""
    request_data = {
        "pickupAddress": "上海市浦东新区"
        # 缺少deliveryAddress和customerName
    }

    # 这应该在请求验证时失败
    with pytest.raises(Exception):
        validate(instance=request_data, schema=CREATE_SHIPMENT_REQUEST_SCHEMA)


@pytest.mark.asyncio
async def test_create_shipment_response_format():
    """测试创建运单响应格式"""
    expected_response = {
        "id": "uuid-shipment-123",
        "shipmentNumber": "SH-BJ-20250927-001",
        "status": "created",
        "createdAt": "2025-09-27T10:30:00Z",
        "estimatedDelivery": "2025-09-29T18:00:00Z"
    }

    validate(instance=expected_response, schema=CREATE_SHIPMENT_RESPONSE_SCHEMA)