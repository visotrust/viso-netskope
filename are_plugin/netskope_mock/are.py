from typing import Optional
from pydantic import BaseModel

from enum import Enum
from datetime import datetime

class _Result(BaseModel):
    success: bool
    message: str


class ValidationResult(_Result):
    pass


class PushResult(_Result):
    pass


class MappingType(str, Enum):
    STRING  = 'string'
    # there are also INTEGERs, but nobody uses them.


class TargetMappingFields(BaseModel):
    label: str
    type:  MappingType
    value: str


class CloudConfidenceLevel(str, Enum):
    POOR = 'poor'
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


class Application(BaseModel):
    applicationId: int
    applicationName: str
    vendor: str

    cci: Optional[int]
    ccl: Optional[CloudConfidenceLevel]

    categoryName: Optional[str]
    deepLink: str

    users: list[str]
    customTags: list[str]

    discoveryDomains: list[str]
    steeringDomains: list[str]

    createdTime: datetime
    updatedTime: datetime
    firstSeen: datetime
    lastSeen: datetime
