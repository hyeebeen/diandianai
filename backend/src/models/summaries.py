from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey, DECIMAL, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class SummaryType(enum.Enum):
    """摘要类型枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class SummaryStatus(enum.Enum):
    """摘要状态枚举"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class BusinessSummary(BaseModel):
    """业务摘要模型"""
    __tablename__ = "business_summaries"

    # 摘要基本信息
    title = Column(String(200), nullable=False)
    summary_type = Column(String(20), nullable=False)  # 存储枚举值

    # 时间范围
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # 摘要内容
    summary_content = Column(Text, nullable=False)
    executive_summary = Column(Text)  # 执行摘要

    # 业务指标
    total_shipments = Column(String(10), default="0")  # 使用字符串存储数字
    completed_shipments = Column(String(10), default="0")
    revenue = Column(DECIMAL(15, 2), default=0.00)
    cost = Column(DECIMAL(15, 2), default=0.00)
    profit_margin = Column(DECIMAL(5, 2))  # 利润率百分比

    # 运营指标
    on_time_delivery_rate = Column(DECIMAL(5, 2))  # 准时交付率
    customer_satisfaction_score = Column(DECIMAL(3, 2))  # 客户满意度评分
    average_delivery_time = Column(DECIMAL(8, 2))  # 平均交付时间(小时)
    fuel_efficiency = Column(DECIMAL(6, 2))  # 燃油效率

    # AI分析结果
    insights = Column(JSON)  # AI生成的洞察和建议
    trends = Column(JSON)    # 趋势分析
    predictions = Column(JSON)  # 预测数据
    recommendations = Column(JSON)  # 改进建议

    # 数据源
    data_sources = Column(JSON)  # 数据来源描述
    sample_size = Column(String(10))  # 样本大小
    confidence_level = Column(DECIMAL(3, 2))  # 置信度

    # 生成信息
    generated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    generated_by_model = Column(String(100))  # 使用的AI模型
    generation_time = Column(DECIMAL(8, 3))  # 生成耗时(秒)
    status = Column(String(20), default=SummaryStatus.PENDING.value)

    # 审核信息
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    is_approved = Column(Boolean, default=False)

    # 发布信息
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True))
    published_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # 访问控制
    is_public = Column(Boolean, default=False)
    allowed_roles = Column(JSON)  # 允许访问的角色列表

    # 关联关系
    generated_by = relationship("User", foreign_keys=[generated_by_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
    published_by = relationship("User", foreign_keys=[published_by_user_id])

    def __repr__(self):
        return f"<BusinessSummary(type='{self.summary_type}', period='{self.period_start}-{self.period_end}')>"


class SummaryTemplate(BaseModel):
    """摘要模板模型"""
    __tablename__ = "summary_templates"

    # 模板信息
    name = Column(String(100), nullable=False)
    description = Column(Text)
    summary_type = Column(String(20), nullable=False)

    # 模板内容
    template_content = Column(Text, nullable=False)  # 模板文本
    required_metrics = Column(JSON)  # 必需的指标列表
    optional_metrics = Column(JSON)  # 可选的指标列表

    # 配置
    auto_generate = Column(Boolean, default=False)  # 是否自动生成
    generation_schedule = Column(String(50))  # 生成计划(cron表达式)

    # 状态
    is_active = Column(Boolean, default=True)
    version = Column(String(10), default="1.0")

    # 创建者
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # 关联关系
    created_by = relationship("User")

    def __repr__(self):
        return f"<SummaryTemplate(name='{self.name}', type='{self.summary_type}')>"


class SummaryMetric(BaseModel):
    """摘要指标模型"""
    __tablename__ = "summary_metrics"

    summary_id = Column(UUID(as_uuid=True), ForeignKey("business_summaries.id"), nullable=False)

    # 指标信息
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(String(50))  # 指标分类

    # 指标值
    current_value = Column(DECIMAL(15, 4))
    previous_value = Column(DECIMAL(15, 4))
    target_value = Column(DECIMAL(15, 4))

    # 计算信息
    calculation_method = Column(Text)
    data_source = Column(String(200))
    unit = Column(String(20))  # 单位

    # 比较分析
    change_percentage = Column(DECIMAL(6, 2))  # 变化百分比
    trend_direction = Column(String(20))  # up, down, stable
    performance_status = Column(String(20))  # excellent, good, average, poor

    # 关联关系
    summary = relationship("BusinessSummary")

    def __repr__(self):
        return f"<SummaryMetric(name='{self.metric_name}', value={self.current_value})>"


class SummaryAlert(BaseModel):
    """摘要告警模型"""
    __tablename__ = "summary_alerts"

    summary_id = Column(UUID(as_uuid=True), ForeignKey("business_summaries.id"), nullable=False)

    # 告警信息
    alert_type = Column(String(50), nullable=False)  # performance, anomaly, threshold
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # 触发条件
    metric_name = Column(String(100))
    threshold_value = Column(DECIMAL(15, 4))
    actual_value = Column(DECIMAL(15, 4))

    # 处理状态
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    acknowledged_at = Column(DateTime(timezone=True))

    is_resolved = Column(Boolean, default=False)
    resolved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)

    # 关联关系
    summary = relationship("BusinessSummary")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])

    def __repr__(self):
        return f"<SummaryAlert(type='{self.alert_type}', severity='{self.severity}')>"