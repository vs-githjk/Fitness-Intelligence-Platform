"""Email provider abstraction: console preview, SMTP message building, and factory."""

import io

import pytest

from app.config import Settings
from app.email import build_email_provider
from app.email.base import EmailMessage, EmailProviderKind
from app.email.console import ConsoleEmailProvider
from app.email.smtp import SmtpEmailProvider


def _message() -> EmailMessage:
    return EmailMessage(to="user@example.com", subject="Reset your Vytal password", text_body="link: https://x/y")


def test_console_provider_writes_a_preview() -> None:
    stream = io.StringIO()
    ConsoleEmailProvider(stream=stream).send(_message())
    output = stream.getvalue()
    assert "user@example.com" in output
    assert "Reset your Vytal password" in output
    assert "link: https://x/y" in output


def test_smtp_provider_builds_a_valid_message() -> None:
    provider = SmtpEmailProvider(host="smtp.example.com", port=587, sender="Vytal <no-reply@vytal.example>")
    mime = provider.build_message(_message())
    assert mime["To"] == "user@example.com"
    assert mime["From"] == "Vytal <no-reply@vytal.example>"
    assert mime["Subject"] == "Reset your Vytal password"
    assert "link: https://x/y" in mime.get_content()


def test_smtp_provider_send_uses_starttls_and_login(monkeypatch) -> None:
    calls: dict[str, object] = {}

    class _FakeSMTP:
        def __init__(self, host, port, timeout=10):
            calls["host"] = host
            calls["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def starttls(self, context=None):
            calls["starttls"] = True

        def login(self, username, password):
            calls["login"] = (username, password)

        def send_message(self, mime):
            calls["sent_to"] = mime["To"]

    monkeypatch.setattr("smtplib.SMTP", _FakeSMTP)
    provider = SmtpEmailProvider(
        host="smtp.example.com",
        port=587,
        sender="Vytal <no-reply@vytal.example>",
        username="apikey",
        password="secret",
    )
    provider.send(_message())
    assert calls["host"] == "smtp.example.com"
    assert calls["starttls"] is True
    assert calls["login"] == ("apikey", "secret")
    assert calls["sent_to"] == "user@example.com"


def test_factory_selects_console_by_default() -> None:
    provider = build_email_provider(Settings(_env_file=None))
    assert provider.kind == EmailProviderKind.CONSOLE


def test_factory_selects_smtp_when_configured() -> None:
    provider = build_email_provider(
        Settings(_env_file=None, email_provider="smtp", email_smtp_host="smtp.example.com")
    )
    assert provider.kind == EmailProviderKind.SMTP


def test_factory_requires_smtp_host() -> None:
    with pytest.raises(ValueError, match="EMAIL_SMTP_HOST"):
        build_email_provider(Settings(_env_file=None, email_provider="smtp"))


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unknown EMAIL_PROVIDER"):
        build_email_provider(Settings(_env_file=None, email_provider="carrier-pigeon"))
