from enum import StrEnum


class ActionabilityStatus(StrEnum):
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    NO_DEADLINE = "NO_DEADLINE"
    UNKNOWN = "UNKNOWN"
