import pytest
from jsonschema import validate

# 运单详情响应schema (基于shipment-api.yaml)
SHIPMENT_DETAIL_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "shipmentNumber": {"type": "string"},
        "status": {
            "type": "string",
            "enum": ["created", "picked_up", "in_transit", "delivered", "cancelled"]
        },
        "sender": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "company": {"type": "string"}
            },
            "required": ["name", "phone"]
        },
        "senderAddress": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "province": {"type": "string"},
                "country": {"type": "string"},
                "coordinates": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                        "longitude": {"type": "number", "minimum": -180, "maximum": 180}
                    },
                    "required": ["latitude", "longitude"]
                }
            },
            "required": ["street", "city", "province", "country"]
        },
        "receiver": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "company": {"type": "string"}
            },
            "required": ["name", "phone"]
        },
        "receiverAddress": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "province": {"type": "string"},
                "country": {"type": "string"},
                "coordinates": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                        "longitude": {"type": "number", "minimum": -180, "maximum": 180}
                    },
                    "required": ["latitude", "longitude"]
                }
            },
            "required": ["street", "city", "province", "country"]
        },
        "cargo": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "weight": {"type": "number"},
                "volume": {"type": "number"},
                "quantity": {"type": "integer"},
                "unit": {"type": "string"},
                "value": {"type": "number"},
                "specialRequirements": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["description", "weight", "quantity", "unit"]
        },
        "driverId": {"type": ["string", "null"]},
        "driverName": {"type": ["string", "null"]},
        "vehicleId": {"type": ["string", "null"]},
        "vehiclePlateNumber": {"type": ["string", "null"]},
        "pickupTime": {"type": ["string", "null"], "format": "date-time"},
        "estimatedDeliveryTime": {"type": ["string", "null"], "format": "date-time"},
        "actualDeliveryTime": {"type": ["string", "null"], "format": "date-time"},
        "freight": {"type": "number"},
        "currency": {"type": "string"},
        "route": {
            "type": ["object", "null"],
            "properties": {
                "id": {"type": "string"},
                "startLocation": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"}
                    },
                    "required": ["latitude", "longitude"]
                },
                "endLocation": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"}
                    },
                    "required": ["latitude", "longitude"]
                },
                "totalDistance": {"type": ["number", "null"]},
                "estimatedDuration": {"type": ["integer", "null"]},
                "actualDuration": {"type": ["integer", "null"]},
                "status": {
                    "type": "string",
                    "enum": ["planned", "active", "completed", "paused"]
                }
            }
        },
        "statusHistory": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["created", "picked_up", "in_transit", "delivered", "cancelled"]
                    },
                    "notes": {"type": ["string", "null"]},
                    "location": {
                        "type": ["object", "null"],
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        }
                    },
                    "address": {"type": ["string", "null"]},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "updatedBy": {"type": "string"}
                },
                "required": ["id", "status", "timestamp", "updatedBy"]
            }
        },
        "createdAt": {"type": "string", "format": "date-time"},
        "updatedAt": {"type": "string", "format": "date-time"}
    },
    "required": [
        "id", "shipmentNumber", "status", "sender", "senderAddress",
        "receiver", "receiverAddress", "cargo", "freight", "currency",
        "statusHistory", "createdAt", "updatedAt"
    ]
}

# 错误响应schema
ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {"type": "string"},
        "message": {"type": "string"}
    },
    "required": ["error", "message"]
}


@pytest.mark.asyncio
async def test_get_shipment_detail_contract_valid_response():
    """测试获取运单详情接口合约 - 有效响应"""
    expected_response = {
        "id": "shipment_123",
        "shipmentNumber": "WD202501270001",
        "status": "in_transit",
        "sender": {
            "name": "张三",
            "phone": "13800138000",
            "company": "北京物流有限公司"
        },
        "senderAddress": {
            "street": "中关村大街1号",
            "city": "北京市",
            "province": "北京市",
            "country": "中国",
            "coordinates": {
                "latitude": 39.9042,
                "longitude": 116.4074
            }
        },
        "receiver": {
            "name": "李四",
            "phone": "13900139000",
            "company": "上海货运公司"
        },
        "receiverAddress": {
            "street": "南京路100号",
            "city": "上海市",
            "province": "上海市",
            "country": "中国",
            "coordinates": {
                "latitude": 31.2304,
                "longitude": 121.4737
            }
        },
        "cargo": {
            "description": "电子产品",
            "weight": 25.5,
            "volume": 0.5,
            "quantity": 10,
            "unit": "箱",
            "value": 5000.00,
            "specialRequirements": ["易碎", "防潮"]
        },
        "driverId": "driver_456",
        "driverName": "王师傅",
        "vehicleId": "vehicle_789",
        "vehiclePlateNumber": "京A12345",
        "pickupTime": "2025-01-27T09:00:00Z",
        "estimatedDeliveryTime": "2025-01-28T18:00:00Z",
        "actualDeliveryTime": None,
        "freight": 500.00,
        "currency": "CNY",
        "route": {
            "id": "route_101",
            "startLocation": {
                "latitude": 39.9042,
                "longitude": 116.4074
            },
            "endLocation": {
                "latitude": 31.2304,
                "longitude": 121.4737
            },
            "totalDistance": 1200.5,
            "estimatedDuration": 720,
            "actualDuration": None,
            "status": "active"
        },
        "statusHistory": [
            {
                "id": "status_1",
                "status": "created",
                "notes": "运单已创建",
                "location": {
                    "latitude": 39.9042,
                    "longitude": 116.4074
                },
                "address": "北京市海淀区中关村大街1号",
                "timestamp": "2025-01-27T08:00:00Z",
                "updatedBy": "user_123"
            },
            {
                "id": "status_2",
                "status": "picked_up",
                "notes": "货物已提取",
                "location": {
                    "latitude": 39.9042,
                    "longitude": 116.4074
                },
                "address": "北京市海淀区中关村大街1号",
                "timestamp": "2025-01-27T09:30:00Z",
                "updatedBy": "driver_456"
            }
        ],
        "createdAt": "2025-01-27T08:00:00Z",
        "updatedAt": "2025-01-27T09:30:00Z"
    }

    # 验证响应格式
    validate(instance=expected_response, schema=SHIPMENT_DETAIL_RESPONSE_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "GET /api/shipments/{id} endpoint not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_get_shipment_detail_contract_not_found():
    """测试获取运单详情接口合约 - 运单不存在"""
    expected_error_response = {
        "error": "SHIPMENT_NOT_FOUND",
        "message": "运单不存在"
    }

    # 验证错误响应格式
    validate(instance=expected_error_response, schema=ERROR_RESPONSE_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "GET /api/shipments/{id} 404 response not yet implemented - this test should fail"


@pytest.mark.asyncio
async def test_get_shipment_detail_contract_minimal_response():
    """测试获取运单详情接口合约 - 最小响应（刚创建的运单）"""
    minimal_response = {
        "id": "shipment_456",
        "shipmentNumber": "WD202501270002",
        "status": "created",
        "sender": {
            "name": "赵六",
            "phone": "13700137000"
        },
        "senderAddress": {
            "street": "解放路88号",
            "city": "天津市",
            "province": "天津市",
            "country": "中国"
        },
        "receiver": {
            "name": "钱七",
            "phone": "13600136000"
        },
        "receiverAddress": {
            "street": "环城路99号",
            "city": "济南市",
            "province": "山东省",
            "country": "中国"
        },
        "cargo": {
            "description": "服装",
            "weight": 15.0,
            "quantity": 5,
            "unit": "件"
        },
        "driverId": None,
        "driverName": None,
        "vehicleId": None,
        "vehiclePlateNumber": None,
        "pickupTime": None,
        "estimatedDeliveryTime": None,
        "actualDeliveryTime": None,
        "freight": 300.00,
        "currency": "CNY",
        "route": None,
        "statusHistory": [
            {
                "id": "status_3",
                "status": "created",
                "notes": "运单已创建，等待分配司机",
                "location": None,
                "address": None,
                "timestamp": "2025-01-27T10:00:00Z",
                "updatedBy": "user_789"
            }
        ],
        "createdAt": "2025-01-27T10:00:00Z",
        "updatedAt": "2025-01-27T10:00:00Z"
    }

    # 验证最小响应格式（只包含必需字段）
    validate(instance=minimal_response, schema=SHIPMENT_DETAIL_RESPONSE_SCHEMA)

    # 这个测试现在应该失败，因为还没有实现
    assert False, "GET /api/shipments/{id} minimal response not yet implemented - this test should fail"