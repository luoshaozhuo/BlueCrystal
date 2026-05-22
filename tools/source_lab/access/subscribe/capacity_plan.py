"""Subscribe capacity matrix planning helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SubscribeCapacityMatrixPlan:
    """Pure subscribe capacity matrix dimensions without execution behavior."""

    process_counts: tuple[int, ...]
    server_counts: tuple[int, ...]
    source_update_hz_values: tuple[float, ...]
    sample_hz_values: tuple[float, ...]
    queue_sizes: tuple[int, ...]

    def combo_count(self) -> int:
        """Return the full cartesian-product size of this matrix plan."""

        self.validate()
        return (
            len(self.process_counts)
            * len(self.server_counts)
            * len(self.source_update_hz_values)
            * len(self.sample_hz_values)
            * len(self.queue_sizes)
        )

    def validate(self) -> None:
        """Validate that each matrix dimension is non-empty and positive."""

        if not self.process_counts:
            raise ValueError("process_counts must not be empty")
        if not self.server_counts:
            raise ValueError("server_counts must not be empty")
        if not self.source_update_hz_values:
            raise ValueError("source_update_hz_values must not be empty")
        if not self.sample_hz_values:
            raise ValueError("sample_hz_values must not be empty")
        if not self.queue_sizes:
            raise ValueError("queue_sizes must not be empty")
        if any(value <= 0 for value in self.process_counts):
            raise ValueError("process_counts must contain positive integers")
        if any(value <= 0 for value in self.server_counts):
            raise ValueError("server_counts must contain positive integers")
        if any(value <= 0 for value in self.queue_sizes):
            raise ValueError("queue_sizes must contain positive integers")
        if any(value <= 0 for value in self.source_update_hz_values):
            raise ValueError("source_update_hz_values must contain positive values")
        if any(value <= 0 for value in self.sample_hz_values):
            raise ValueError("sample_hz_values must contain positive values")
