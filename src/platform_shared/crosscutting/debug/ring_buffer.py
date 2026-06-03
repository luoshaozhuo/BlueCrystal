"""Small recent-failure buffer used by debug tooling."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field

from platform_shared.crosscutting.debug.diagnostics import RunnerDiagnosticsSnapshot


@dataclass(slots=True)
class RecentFailureBuffer:
    """Bounded in-memory buffer of recent failure diagnostics."""

    capacity: int = 20
    _items: deque[RunnerDiagnosticsSnapshot] = field(init=False)

    def __post_init__(self) -> None:
        self._items = deque(maxlen=self.capacity)

    def add(self, snapshot: RunnerDiagnosticsSnapshot) -> None:
        """Append one diagnostics snapshot."""

        self._items.append(snapshot)

    def items(self) -> tuple[RunnerDiagnosticsSnapshot, ...]:
        """Return buffered snapshots in insertion order."""

        return tuple(self._items)

    def extend(self, snapshots: Iterable[RunnerDiagnosticsSnapshot]) -> None:
        """Append multiple diagnostics snapshots."""

        for snapshot in snapshots:
            self.add(snapshot)
