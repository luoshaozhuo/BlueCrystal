"""Internal observability events."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ObservationEvent:
    name: str
    timestamp: datetime
    attributes: dict[str, object]
