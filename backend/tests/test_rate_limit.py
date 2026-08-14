"""Rate limiting — pure sliding-window logic and the deployed 429 path."""

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
