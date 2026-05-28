"""Command-line entrypoint for the ingest runtime image."""

from __future__ import annotations

from whale.ingest.runtime.cli import app


def main() -> int:
    """Run the ingest runtime CLI."""

    app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
