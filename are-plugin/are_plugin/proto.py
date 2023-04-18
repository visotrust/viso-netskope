from typing import Optional
from typing_extensions import Protocol

class Application(Protocol):
    applicationId: int
    vendor: str

    cci: Optional[int]

    discoveryDomains: list[str]
    steeringDomains: list[str]
