# Import base models first
from .base import BaseModel, Base, Tenant

# Import all models to ensure they're registered with SQLAlchemy
from .users import User, RefreshToken, UserRole
from .logistics import (
    Shipment, ShipmentStop, Vehicle,
    ShipmentStatus, StopType
)
from .gps import (
    GPSLocation, RoutePoint, Geofence,
    GPSSource
)
from .ai_models import (
    AIModelConfig, AIConversation, AIMessage,
    AIInteraction, AISummary,
    AIProvider, MessageRole
)
from .summaries import (
    BusinessSummary, SummaryTemplate,
    SummaryMetric, SummaryAlert,
    SummaryType, SummaryStatus
)

__all__ = [
    # Base
    "BaseModel", "Base", "Tenant",

    # Users
    "User", "RefreshToken", "UserRole",

    # Logistics
    "Shipment", "ShipmentStop", "Vehicle",
    "ShipmentStatus", "StopType",

    # GPS
    "GPSLocation", "RoutePoint", "Geofence",
    "GPSSource",

    # AI Models
    "AIModelConfig", "AIConversation", "AIMessage",
    "AIInteraction", "AISummary",
    "AIProvider", "MessageRole",

    # Summaries
    "BusinessSummary", "SummaryTemplate",
    "SummaryMetric", "SummaryAlert",
    "SummaryType", "SummaryStatus",
]