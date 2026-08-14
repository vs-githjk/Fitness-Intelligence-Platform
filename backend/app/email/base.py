"""Transactional email abstraction.

A tiny provider seam (mirroring the storage abstraction): the product builds an
`EmailMessage` and hands it to an `EmailProvider`; the concrete provider is selected by
environment. No product/domain logic lives here, and no vendor credential is embedded —
SMTP credentials come from the environment via Settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


class EmailProviderKind(StrEnum):
    CONSOLE = "console"
    SMTP = "smtp"


@dataclass(frozen=True, slots=True)
class EmailMessage:
    """A single transactional message. `text_body` is always present; `html_body` is
    optional. Secrets (e.g. a reset link) live in the body and are never logged."""

    to: str
    subject: str
    text_body: str
    html_body: str | None = None


@runtime_checkable
class EmailProvider(Protocol):
    kind: EmailProviderKind

    def send(self, message: EmailMessage) -> None:
        """Deliver the message. Raises on unrecoverable delivery failure."""
        ...
