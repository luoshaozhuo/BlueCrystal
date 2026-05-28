"""External access policy contract tests with a local HTTP stub server."""

from __future__ import annotations

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

import pytest
from starlette.requests import Request

from whale.ingest.adapters.security.external_access_policy import ExternalAccessPolicy


class _StubPolicyHandler(BaseHTTPRequestHandler):
    """HTTP stub that returns configurable allow/deny responses."""

    _response: dict[str, Any] = {"allowed": True, "reason": ""}
    _status: int = 200

    def do_POST(self) -> None:  # type: ignore[override]
        # Consume request body before responding
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length > 0:
            self.rfile.read(content_length)
        body = json.dumps(self._response).encode("utf-8")
        self.send_response(self._status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        pass  # suppress logs


def _stub_url(response: dict[str, Any], status: int = 200) -> str:
    """Start a stub server on a random port and return its URL."""
    handler = _StubPolicyHandler
    handler._response = response
    handler._status = status
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_port
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return f"http://127.0.0.1:{port}", server


def _fake_request(actor: str = "admin", roles: str = "ingest") -> Request:
    """Create a bare-minimum Starlette Request for testing."""
    scope: dict[str, Any] = {
        "type": "http",
        "method": "GET",
        "path": "/healthz",
        "headers": [
            (b"x-actor", actor.encode()),
            (b"x-roles", roles.encode()),
        ],
    }
    return Request(scope)


class TestExternalAccessPolicyContract:

    @pytest.mark.integration
    def test_external_policy_allow(self) -> None:
        url, server = _stub_url({"allowed": True, "reason": ""})
        try:
            policy = ExternalAccessPolicy(url, timeout_seconds=3.0)
            req = _fake_request()
            assert policy.authorize(req, "read", "source") is True
            assert policy.last_error is None
        finally:
            server.shutdown()

    @pytest.mark.integration
    def test_external_policy_deny(self) -> None:
        url, server = _stub_url({"allowed": False, "reason": "no permission"})
        try:
            policy = ExternalAccessPolicy(url, timeout_seconds=3.0)
            req = _fake_request()
            assert policy.authorize(req, "write", "source_write") is False
        finally:
            server.shutdown()

    @pytest.mark.integration
    def test_external_policy_timeout_fail_closed(self) -> None:
        """When the external service is unreachable, fail_closed returns deny."""
        policy = ExternalAccessPolicy(
            "http://127.0.0.1:1/authorize",  # connection refused
            timeout_seconds=1.0,
            fail_closed=True,
        )
        req = _fake_request()
        assert policy.authorize(req, "read", "source") is False
        assert policy.last_error is not None

    @pytest.mark.integration
    def test_external_policy_fail_open_requires_explicit_config(self) -> None:
        """fail_open can be enabled, returning allow on error."""
        policy = ExternalAccessPolicy(
            "http://127.0.0.1:1/authorize",
            timeout_seconds=1.0,
            fail_closed=False,
        )
        req = _fake_request()
        assert policy.authorize(req, "read", "source") is True
        assert policy.last_error is not None

    @pytest.mark.integration
    def test_external_policy_redacts_token_in_errors(self) -> None:
        """Error messages should not contain auth tokens."""
        policy = ExternalAccessPolicy(
            "http://127.0.0.1:1/authorize",
            timeout_seconds=1.0,
            fail_closed=True,
        )
        req = _fake_request()
        policy.authorize(req, "read", "source")
        error_msg = str(policy.last_error) if policy.last_error else ""
        # Error should not contain request payload tokens
        assert "Bearer" not in error_msg
        assert "token" not in error_msg.lower()
