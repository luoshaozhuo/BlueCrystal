"""Fencing token helpers."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Callable

from sqlalchemy.orm import Session, sessionmaker

from whale.shared.persistence.orm import IngestFencingToken


@dataclass(frozen=True, slots=True)
class FencingToken:
    """One monotonic fencing token snapshot."""

    token_name: str
    value: int


class FencingTokenRepository:
    """Persist monotonic fencing tokens in the runtime DB."""

    def __init__(self, session_factory: sessionmaker[Session] | Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def next_value(self, token_name: str) -> FencingToken:
        """Advance and return one fencing token."""

        session = self._session_factory()
        try:
            row = session.get(IngestFencingToken, token_name)
            if row is None:
                row = IngestFencingToken(token_name=token_name, current_value=1)
                session.add(row)
            else:
                row.current_value += 1
            session.commit()
            session.refresh(row)
            return FencingToken(token_name=row.token_name, value=row.current_value)
        finally:
            session.close()

    def current_value(self, token_name: str) -> FencingToken:
        """Return the current value for one fencing token name."""

        session = self._session_factory()
        try:
            row = session.get(IngestFencingToken, token_name)
            if row is None:
                return FencingToken(token_name=token_name, value=0)
            return FencingToken(token_name=row.token_name, value=row.current_value)
        finally:
            session.close()


def redact_fencing_token(token: int | None) -> str | None:
    """Return one stable redacted token digest for audit output."""

    if token is None:
        return None
    return sha256(str(token).encode("utf-8")).hexdigest()[:16]
