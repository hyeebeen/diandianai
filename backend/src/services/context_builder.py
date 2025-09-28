"""
运单上下文构建器
为AI助手"点点精灵"提供运单相关的智能上下文
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from models.logistics import Shipment, ShipmentStatus


@dataclass
class ShipmentContext:
    """运单上下文数据结构"""
    shipment_id: str
    shipment_number: str
    status: str
    customer_info: Dict[str, Any]
    addresses: Dict[str, Any]
    cargo_info: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    current_location: Optional[Dict[str, Any]] = None
    estimated_delivery: Optional[str] = None


class ContextBuilder:
    """运单上下文构建器"""

    def __init__(self):
        self.assistant_name = "点点精灵"
        self.assistant_personality = self._build_personality()

    def _build_personality(self) -> str:
        """构建AI助手的人设"""
        return """
你是点点精灵，一个专业、友好的物流AI助手。你的特点：

🎯 **专业能力**：
- 精通物流运输、供应链管理
- 熟悉运单状态、配送流程
- 能够分析运输路线和时效

🤖 **性格特征**：
- 热情友好，乐于助人
- 回复简洁明了，重点突出
- 用中文交流，语言自然流畅
- 适时使用emoji增加亲和力

💡 **服务理念**：
- 主动提供有用信息
- 预测用户需求并提前解答
- 遇到问题时提供解决方案
- 始终以客户满意为目标
"""

    def build_system_prompt(self, shipment_context: Optional[ShipmentContext] = None) -> str:
        """构建系统提示词"""
        base_prompt = f"""
{self.assistant_personality}

当前时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
"""

        if shipment_context:
            shipment_info = self._format_shipment_info(shipment_context)
            base_prompt += f"""

📦 **当前选中运单信息**：
{shipment_info}

请基于以上运单信息回答用户问题。如果用户询问运单相关内容，请提供准确、详细的信息。
"""
        else:
            base_prompt += """
用户当前没有选择特定运单，请提供通用的物流咨询服务。
"""

        return base_prompt.strip()

    def _format_shipment_info(self, context: ShipmentContext) -> str:
        """格式化运单信息"""
        # 状态映射
        status_map = {
            'created': '已创建',
            'assigned': '已分配',
            'picked_up': '已取货',
            'in_transit': '运输中',
            'delivered': '已送达',
            'cancelled': '已取消'
        }

        status_display = status_map.get(context.status, context.status)

        # 构建信息字符串
        info_parts = [
            f"🏷️ 运单号：{context.shipment_number}",
            f"📊 状态：{status_display}",
            f"👤 客户：{context.customer_info.get('name', '未知')}",
            f"📞 联系电话：{context.customer_info.get('phone', '未知')}",
            f"📍 发货地址：{context.addresses.get('pickup', '未知')}",
            f"🏢 收货地址：{context.addresses.get('delivery', '未知')}",
            f"📦 货物：{context.cargo_info.get('description', '未知')}",
            f"⚖️ 重量：{context.cargo_info.get('weight', '未知')}公斤"
        ]

        # 添加当前位置信息
        if context.current_location:
            location = context.current_location
            info_parts.append(f"🚚 当前位置：{location.get('address', '位置更新中')}")

        # 添加预计送达时间
        if context.estimated_delivery:
            info_parts.append(f"⏰ 预计送达：{context.estimated_delivery}")

        # 添加时间线信息
        if context.timeline:
            info_parts.append("\n📅 **运输进展**：")
            for event in context.timeline[-3:]:  # 显示最近3条记录
                timestamp = event.get('timestamp', '')
                if isinstance(timestamp, str) and timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m月%d日 %H:%M')
                    except:
                        time_str = timestamp
                else:
                    time_str = '时间未知'

                status_text = status_map.get(event.get('status', ''), event.get('status', ''))
                notes = event.get('notes', '')
                location_info = ""
                if event.get('location'):
                    location_info = f" - {event['location'].get('address', '')}"

                info_parts.append(f"  • {time_str}: {status_text}{location_info}")
                if notes:
                    info_parts.append(f"    备注：{notes}")

        return "\n".join(info_parts)

    def extract_shipment_context(self, shipment: Shipment) -> ShipmentContext:
        """从运单模型提取上下文信息"""

        # 提取客户信息
        customer_info = {
            'name': shipment.customer_name or '未知客户',
            'phone': getattr(shipment, 'customer_phone', '未提供')
        }

        # 提取地址信息
        addresses = {
            'pickup': shipment.pickup_address or '发货地址未知',
            'delivery': shipment.delivery_address or '收货地址未知'
        }

        # 提取货物信息
        cargo_info = {
            'description': shipment.commodity_type or '货物描述未知',
            'weight': float(shipment.weight_kg) if shipment.weight_kg else 0
        }

        # 构建时间线（简化版，实际应该从状态历史表获取）
        timeline = []
        if shipment.created_at:
            timeline.append({
                'timestamp': shipment.created_at.isoformat(),
                'status': 'created',
                'notes': '运单已创建'
            })

        if shipment.status and shipment.updated_at:
            timeline.append({
                'timestamp': shipment.updated_at.isoformat(),
                'status': shipment.status.value if hasattr(shipment.status, 'value') else str(shipment.status),
                'notes': f'状态更新为：{shipment.status}'
            })

        # 提取当前位置（如果有的话）
        current_location = None
        if hasattr(shipment, 'current_latitude') and hasattr(shipment, 'current_longitude'):
            if shipment.current_latitude and shipment.current_longitude:
                current_location = {
                    'latitude': float(shipment.current_latitude),
                    'longitude': float(shipment.current_longitude),
                    'address': getattr(shipment, 'current_address', '位置更新中')
                }

        # 预计送达时间
        estimated_delivery = None
        if hasattr(shipment, 'estimated_delivery') and shipment.estimated_delivery:
            if isinstance(shipment.estimated_delivery, datetime):
                estimated_delivery = shipment.estimated_delivery.strftime('%Y年%m月%d日')
            else:
                estimated_delivery = str(shipment.estimated_delivery)

        return ShipmentContext(
            shipment_id=str(shipment.id),
            shipment_number=shipment.shipment_number or f"运单{shipment.id}",
            status=shipment.status.value if hasattr(shipment.status, 'value') else str(shipment.status),
            customer_info=customer_info,
            addresses=addresses,
            cargo_info=cargo_info,
            timeline=timeline,
            current_location=current_location,
            estimated_delivery=estimated_delivery
        )

    def build_conversation_context(self,
                                 user_message: str,
                                 shipment_context: Optional[ShipmentContext] = None,
                                 conversation_history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """构建完整的对话上下文"""

        # 构建系统消息
        system_prompt = self.build_system_prompt(shipment_context)

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # 添加历史对话（最近5轮）
        if conversation_history:
            for msg in conversation_history[-10:]:  # 保留最近10条消息
                messages.append(msg)

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})

        return messages


# 全局实例
context_builder = ContextBuilder()