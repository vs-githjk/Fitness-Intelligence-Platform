"""Security response headers — pure logic and a live response check."""

from fastapi.testclient import TestClient

from app.security_headers import security_headers


def test_deployed_sends_hsts_and_csp():
    headers = security_headers(path="/api/v1/auth/login", deployed=True, docs_enabled=False)
    assert headers["Strict-Transport-Security"].startswith("max-age=")
    assert "default-src 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"


def test_local_omits_hsts_but_keeps_csp():
    headers = security_headers(path="/api/v1/health", deployed=False, docs_enabled=True)
    assert "Strict-Transport-Security" not in headers
    assert "Content-Security-Policy" in headers


def test_docs_are_exempt_from_csp_when_docs_enabled():
    # So Swagger UI's assets load in local; docs are disabled in deployed environments.
    assert "Content-Security-Policy" not in security_headers(
        path="/docs", deployed=False, docs_enabled=True
    )
    # But if docs are disabled, even that path is locked down.
    assert "Content-Security-Policy" in security_headers(
        path="/docs", deployed=True, docs_enabled=False
    )


def test_live_response_carries_security_headers(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in res.headers
