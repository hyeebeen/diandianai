from sqlalchemy import Column, String, Text, JSON, ForeignKey, DateTime, Boolean, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class AIProvider(enum.Enum):
    """AI服务提供商枚举"""
    OPENAI = "openai"
    QWEN = "qwen"
    BAIDU = "baidu"
    ZHIPU = "zhipu"
    CUSTOM = "custom"


class MessageRole(enum.Enum):
    """消息角色枚举 - 对应前端 MessageRole"""
    USER = "human"      # 对应前端 'human'
    ASSISTANT = "agent" # 对应前端 'agent'
    SYSTEM = "system"   # 对应前端 'system'


class AIModelConfig(BaseModel):
    """AI模型配置模型"""
    __tablename__ = "ai_model_configs"

    name = Column(String(100), nullable=False)
    provider = Column(String(20), nullable=False)  # 存储枚举值
    model_name = Column(String(100), nullable=False)

    # API配置
    api_key = Column(String(500), nullable=False)
    api_base_url = Column(String(500))
    api_version = Column(String(20))

    # 模型参数
    max_tokens = Column(String(10), default="1000")  # 使用字符串存储数字
    temperature = Column(DECIMAL(3, 2), default=0.7)
    top_p = Column(DECIMAL(3, 2), default=1.0)

    # 配置
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    priority = Column(String(10), default="0")  # 使用字符串存储数字

    # 使用限制
    rate_limit_per_minute = Column(String(10), default="60")  # 使用字符串存储数字
    daily_quota = Column(String(10))  # 使用字符串存储数字

    def __repr__(self):
        return f"<AIModelConfig(name='{self.name}', provider='{self.provider}')>"


class AIConversation(BaseModel):
    """AI对话会话模型"""
    __tablename__ = "ai_conversations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200))  # 对话标题

    # 上下文信息
    context_data = Column(JSON)  # 存储上下文信息（如运单ID等）

    # 状态
    is_active = Column(Boolean, default=True)
    message_count = Column(String(10), default="0")  # 使用字符串存储数字

    # 最后活动时间
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    user = relationship("User", back_populates="ai_conversations")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AIConversation(id='{self.id}', user_id='{self.user_id}')>"


class AIMessage(BaseModel):
    """AI消息模型 - 对应前端 ChatMessage"""
    __tablename__ = "ai_messages"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id"), nullable=False)

    # 消息内容 - 对应前端 ChatMessage 字段
    role = Column(String(20), nullable=False)  # 存储枚举值
    content = Column(Text, nullable=False)

    # AI响应特有字段
    confidence = Column(DECIMAL(4, 3))  # 置信度 0.000-1.000
    suggested_actions = Column(JSON)  # 建议操作列表
    requires_confirmation = Column(Boolean, default=False)

    # 元数据
    model_used = Column(String(100))  # 使用的模型
    token_count = Column(String(10))  # 使用字符串存储数字
    processing_time = Column(DECIMAL(8, 3))  # 处理时间（秒）

    # 附件 - 对应前端 ChatMessage.attachments
    attachments = Column(JSON)  # 存储附件信息

    # 状态
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # 关联关系
    conversation = relationship("AIConversation", back_populates="messages")

    def __repr__(self):
        return f"<AIMessage(role='{self.role}', content='{self.content[:50]}...')>"


class AIInteraction(BaseModel):
    """AI交互记录模型 - 与业务实体关联"""
    __tablename__ = "ai_interactions"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id"), nullable=False)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=True)

    # 交互类型
    interaction_type = Column(String(50), nullable=False)  # create_shipment, update_status, query_location

    # 结果
    success = Column(Boolean, default=False)
    result_data = Column(JSON)  # 存储操作结果
    error_message = Column(Text)

    # 用户确认
    requires_confirmation = Column(Boolean, default=False)
    confirmed_by_user = Column(Boolean, default=False)
    confirmed_at = Column(DateTime(timezone=True))

    # 关联关系
    conversation = relationship("AIConversation")
    shipment = relationship("Shipment", back_populates="ai_interactions")

    def __repr__(self):
        return f"<AIInteraction(type='{self.interaction_type}', success={self.success})>"


class AISummary(BaseModel):
    """AI摘要模型"""
    __tablename__ = "ai_summaries"

    # 摘要类型
    summary_type = Column(String(50), nullable=False)  # daily, weekly, monthly, custom

    # 时间范围
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # 摘要内容
    title = Column(String(200), nullable=False)
    summary_text = Column(Text, nullable=False)

    # 统计数据
    statistics = Column(JSON)  # 存储各种统计数据
    insights = Column(JSON)   # 存储AI生成的洞察

    # 生成信息
    generated_by_model = Column(String(100))
    generation_time = Column(DECIMAL(8, 3))  # 生成耗时

    def __repr__(self):
        return f"<AISummary(type='{self.summary_type}', period='{self.period_start}-{self.period_end}')>"