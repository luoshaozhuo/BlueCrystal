"""Shared fixed-width table rendering helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence


def render_fixed_width_table(
    *,
    headers: Sequence[str],
    rows: Sequence[object],
    format_cell: Callable[[str, object], str],
    default_widths: dict[str, int] | None = None,
) -> str:
    """Render a fixed-width table using caller-provided cell formatting."""

    normalized_headers = tuple(headers)
    if not rows:
        return ""
    widths = {
        header: max(len(header), 0 if default_widths is None else default_widths.get(header, len(header)))
        for header in normalized_headers
    }
    for header in normalized_headers:
        widths[header] = max(widths[header], *(len(format_cell(header, row)) for row in rows))
    border = "-" * (sum(widths.values()) + len(normalized_headers) - 1)
    lines = [
        border,
        " ".join(f"{header:>{widths[header]}}" for header in normalized_headers),
        border,
    ]
    for row in rows:
        lines.append(" ".join(f"{format_cell(header, row):>{widths[header]}}" for header in normalized_headers))
    lines.append(border)
    return "\n".join(lines)
