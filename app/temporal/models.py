from enum import StrEnum
from pydantic import BaseModel

class TemporalValidity(StrEnum):
    CURRENT = "CURRENT"
    SUPERSEDED_OUTDATED = "SUPERSEDED_OUTDATED"
    UNKNOWN = "UNKNOWN"
