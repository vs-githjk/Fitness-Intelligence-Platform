import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import app.main as main_module
from app import __version__
from app.config import AppEnvironment, Settings, normalize_database_url
from app.database import engine_options
from app.main import app
from scripts.seed import ensure_seed_allowed


@app.get("/_test/failure", include_in_schema=False)
def synthetic_failure() -> None:
    raise RuntimeError("private failure detail")


def deployed_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "production",
        "database_url": "postgresql://user:pass@db.internal/fitness",
        "database_sslmode": "require",
        "jwt_secret": "x" * 64,
        "cors_origins": ["https://fitness.example.com"],
        "trusted_hosts": ["api.fitness.example.com"],
        "api_docs_enabled": False,
        "seed_demo_data": False,
        "demo_invite_code": "deployment-specific-invite",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_release_version_is_centralized() -> None:
    assert __version__ == "0.5.0"
    assert app.version == __version__
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text()
    assert 'dynamic = ["version"]' in pyproject
    assert 'path = "app/__init__.py"' in pyproject


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("postgres://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///test.db", "sqlite:///test.db"),
    ],
)
def test_database_url_normalization(source: str, expected: str) -> None:
    assert normalize_database_url(source) == expected


def test_production_settings_are_explicit_and_normalized() -> None:
    config = deployed_settings()
    assert config.database_url.startswith("postgresql+psycopg://")
    assert config.effective_migration_database_url == config.database_url
    assert config.cors_origins == ["https://fitness.example.com"]
    options = engine_options(config)
    assert options["pool_size"] == config.database_pool_size
    assert options["connect_args"] == {"connect_timeout": 5, "sslmode": "require"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"database_url": "sqlite:///unsafe.db"},
        {"jwt_secret": "local-development-secret-change-me-123456"},
        {"cors_origins": ["*"]},
        {"cors_origins": ["http://fitness.example.com"]},
        {"trusted_hosts": ["*"]},
        {"api_docs_enabled": True},
        {"seed_demo_data": True},
        {"demo_mode_enabled": True},
        {"database_sslmode": "prefer"},
    ],
)
def test_production_settings_fail_closed(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        deployed_settings(**overrides)


def test_demo_seed_requires_explicit_gate_and_never_runs_in_production() -> None:
    with pytest.raises(RuntimeError, match="disabled"):
        ensure_seed_allowed(Settings(_env_file=None, app_env="test", seed_demo_data=False))
    ensure_seed_allowed(Settings(_env_file=None, app_env="test", seed_demo_data=True))
    ensure_seed_allowed(deployed_settings(app_env="staging", seed_demo_data=True))
    deployed = SimpleNamespace(seed_demo_data=True, app_env=AppEnvironment.PRODUCTION)
    with pytest.raises(RuntimeError, match="not allowed"):
        ensure_seed_allowed(deployed)  # type: ignore[arg-type]


def test_demo_mode_defaults_off_and_requires_distinct_accounts() -> None:
    assert Settings(_env_file=None).demo_mode_enabled is False
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            demo_coach_email="same@example.com",
            demo_trainee_email="same@example.com",
        )


def test_live_and_ready_health(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json() == {"status": "healthy", "version": "0.5.0"}
    assert client.get("/health").json() == live.json()

    monkeypatch.setattr(main_module, "database_ready", lambda: None)
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "version": "0.5.0"}

    def unavailable() -> None:
        raise ConnectionError("database host should not be exposed")

    monkeypatch.setattr(main_module, "database_ready", unavailable)
    unavailable_response = client.get("/health/ready")
    assert unavailable_response.status_code == 503
    assert unavailable_response.json() == {"status": "unavailable", "version": "0.5.0"}
    assert "database host" not in unavailable_response.text


def test_correlation_id_and_safe_structured_log(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO", logger="fitness_intelligence.requests")
    response = client.get("/health?private=value", headers={"X-Request-ID": "request-123"})
    assert response.headers["X-Request-ID"] == "request-123"
    request_record = next(
        record for record in reversed(caplog.records) if record.name == "fitness_intelligence.requests"
    )
    payload = json.loads(request_record.message)
    assert payload["request_id"] == "request-123"
    assert payload["path"] == "/health"
    assert "private" not in request_record.message

    generated = client.get("/health", headers={"X-Request-ID": "invalid request id"})
    assert generated.headers["X-Request-ID"] != "invalid request id"


def test_untrusted_host_is_rejected_with_correlation_id(client: TestClient) -> None:
    response = client.get("/health", headers={"Host": "untrusted.example", "X-Request-ID": "host-1"})
    assert response.status_code == 400
    assert response.headers["X-Request-ID"] == "host-1"


def test_unhandled_error_is_sanitized_and_correlated(client: TestClient) -> None:
    response = client.get("/_test/failure", headers={"X-Request-ID": "failure-123"})
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "failure-123"
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "request_id": "failure-123",
        }
    }
    assert "private failure detail" not in response.text
