from datetime import datetime
from enum import Enum
from typing import Optional

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

    createdTime: datetime = datetime.now()
    updatedTime: datetime = datetime.now()
    firstSeen: datetime = datetime.now()
    lastSeen: datetime = datetime.now()
