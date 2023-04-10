from typing import Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class CloudConfidenceLevel(str, Enum):
    POOR = 'poor'
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    EXCELLENT = 'excellent'


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
