"""Rate limiting — pure sliding-window logic and the deployed 429 path."""

from types import SimpleNamespace

import app.main as main
from app.rate_limit import RateLimiter


def test_allows_up_to_limit_then_blocks():
    clock = {"t": 0.0}
    limiter = RateLimiter(limit=3, window_seconds=60, clock=lambda: clock["t"])
    assert [limiter.check("k")[0] for _ in range(3)] == [True, True, True]
    allowed, retry = limiter.check("k")
    assert allowed is False and retry >= 1


def test_window_slides_so_older_hits_expire():
    clock = {"t": 0.0}
    limiter = RateLimiter(limit=1, window_seconds=10, clock=lambda: clock["t"])
    assert limiter.check("k")[0] is True
    assert limiter.check("k")[0] is False
    clock["t"] = 11.0  # past the window
    assert limiter.check("k")[0] is True


def test_keys_are_independent():
    limiter = RateLimiter(limit=1, window_seconds=60)
    assert limiter.check("a")[0] is True
    assert limiter.check("b")[0] is True  # a different client is unaffected
    assert limiter.check("a")[0] is False


def test_idle_keys_are_swept_to_bound_memory():
    clock = {"t": 0.0}
    limiter = RateLimiter(limit=5, window_seconds=10, clock=lambda: clock["t"], sweep_at=2)
    limiter.check("a")
    clock["t"] = 20.0  # a's window has fully expired
    limiter.check("b")  # crossing the sweep threshold reclaims the idle "a"
    assert "a" not in limiter._hits
    assert limiter.tracked_keys() <= 2


def _req(xff=None, peer="1.2.3.4"):
    headers = {"X-Forwarded-For": xff} if xff else {}
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=peer))


def test_client_ip_uses_rightmost_forwarded_only_when_trusted(monkeypatch):
    monkeypatch.setattr(main.settings, "rate_limit_trust_forwarded", False)
    assert main._client_ip(_req("9.9.9.9, 5.5.5.5", peer="1.2.3.4")) == "1.2.3.4"
    monkeypatch.setattr(main.settings, "rate_limit_trust_forwarded", True)
    # rightmost hop (proxy-observed), never the leftmost client-claimed 9.9.9.9
    assert main._client_ip(_req("9.9.9.9, 5.5.5.5", peer="1.2.3.4")) == "5.5.5.5"


def test_deployed_login_returns_429_with_retry_after(client, monkeypatch):
    # Simulate a deployed environment and a tight limit, then exceed it.
    monkeypatch.setattr(main, "_DEPLOYED", True)
    monkeypatch.setitem(
        main._RATE_LIMITS, ("POST", "/api/v1/auth/login"),
        RateLimiter(limit=1, window_seconds=60),
    )
    body = {"email": "nobody@example.com", "password": "wrong-password"}
    first = client.post("/api/v1/auth/login", json=body)
    assert first.status_code in (401, 400)
    second = client.post("/api/v1/auth/login", json=body)
    assert second.status_code == 429
    assert int(second.headers["Retry-After"]) >= 1
    assert second.json()["error"]["code"] == "rate_limited"
    assert second.headers["X-Content-Type-Options"] == "nosniff"  # tail still applied
