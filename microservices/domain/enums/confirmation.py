from enum import Enum


class ConfirmationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EDITED = "edited"
    CANCELLED = "cancelled"


class ConfirmationType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    PARTIAL = "partial"
    MODIFICATION = "modification"
    CORRECTION = "correction"
    CANCELLATION = "cancellation"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"
