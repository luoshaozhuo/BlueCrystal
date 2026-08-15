"""可复用实体定义。包含 node_state、source_health_state 等 ingest 领域实体。"""

from pacific.whale.ingest.entities.node_state import NodeState
from pacific.whale.ingest.entities.source_health_state import SourceHealthState

__all__ = ["NodeState", "SourceHealthState"]
