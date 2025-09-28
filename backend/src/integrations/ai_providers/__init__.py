"""
AI模型提供商集成包
支持OpenAI和国产AI模型的统一接口
"""

from .openai_provider import OpenAIProvider, openai_provider
from .domestic_providers import (
    WenxinProvider,
    QwenProvider,
    ZhipuProvider,
    DomesticAIManager,
    domestic_ai_manager
)

__all__ = [
    "OpenAIProvider",
    "openai_provider",
    "WenxinProvider",
    "QwenProvider",
    "ZhipuProvider",
    "DomesticAIManager",
    "domestic_ai_manager"
]