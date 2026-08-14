"""Email provider factory — selects the concrete provider by environment.

`console` for local development preview; `smtp` for deployed delivery. The deployed
config validator forbids `console` and requires SMTP host, so a misconfigured deployment
fails fast at startup rather than silently dropping mail.
"""

from __future__ import annotations

from functools import lru_cache

from app.config import Settings
from app.config import settings as _settings
from app.email.base import EmailMessage, EmailProvider, EmailProviderKind
from app.email.console import ConsoleEmailProvider

__all__ = [
    "EmailMessage",
    "EmailProvider",
    "EmailProviderKind",
    "build_email_provider",
    "get_email_provider",
]


def build_email_provider(config: Settings) -> EmailProvider:
    provider = config.email_provider.strip().lower()
    if provider == EmailProviderKind.SMTP:
        # Imported lazily so local/test runs never require SMTP settings to be present.
        from app.email.smtp import SmtpEmailProvider

        if not config.email_smtp_host:
            raise ValueError("EMAIL_SMTP_HOST is required when EMAIL_PROVIDER=smtp")
        return SmtpEmailProvider(
            host=config.email_smtp_host,
            port=config.email_smtp_port,
            sender=config.email_from,
            username=config.email_smtp_username,
            password=config.email_smtp_password,
            use_tls=config.email_smtp_use_tls,
        )
    if provider == EmailProviderKind.CONSOLE:
        return ConsoleEmailProvider()
    raise ValueError(f"Unknown EMAIL_PROVIDER: {config.email_provider!r}")


@lru_cache
def get_email_provider() -> EmailProvider:
    return build_email_provider(_settings)
