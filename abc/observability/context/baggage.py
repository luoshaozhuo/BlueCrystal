"""OpenTelemetry baggage integration helpers."""

from __future__ import annotations

from opentelemetry import baggage, context


def set_observation_baggage(
    values: dict[str, str],
) -> context.Context:
    """Create an OTel context containing observation baggage."""
    ctx = context.get_current()
    for key, value in values.items():
        ctx = baggage.set_baggage(
            key,
            value,
            ctx,
        )
    return ctx


def get_observation_baggage(
    key: str,
) -> str | None:
    """Read a baggage value from current OTel context."""
    return baggage.get_baggage(key)
