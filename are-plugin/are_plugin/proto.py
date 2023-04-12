from typing_extensions import Protocol

class Application(Protocol):
    applicationId: int
    vendor: str

    discoveryDomains: list[str]
    steeringDomains: list[str]
