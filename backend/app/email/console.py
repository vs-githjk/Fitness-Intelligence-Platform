"""Development email provider: a local preview channel.

Writes the message (including any link) to a stream — by default stdout. This is the
delivery channel in local development, not application logging: seeing the message is the
whole point when there is no real inbox. A deployed environment must never select this
provider (the config validator forbids `console` in staging/production), so no secret is
written to a production log.
"""

from __future__ import annotations

import sys
from typing import TextIO

from app.email.base import EmailMessage, EmailProviderKind


class ConsoleEmailProvider:
    kind = EmailProviderKind.CONSOLE

    def __init__(self, *, stream: TextIO | None = None) -> None:
        self._stream = stream if stream is not None else sys.stdout

    def send(self, message: EmailMessage) -> None:
        lines = [
            "──────── EMAIL (console provider · local preview) ────────",
            f"To:      {message.to}",
            f"Subject: {message.subject}",
            "",
            message.text_body,
            "──────────────────────────────────────────────────────────",
        ]
        print("\n".join(lines), file=self._stream, flush=True)
