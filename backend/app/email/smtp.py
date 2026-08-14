"""Production email provider over SMTP (stdlib smtplib — no third-party dependency).

Credentials are injected from the environment via Settings, never embedded here. STARTTLS
is used by default. The raw password is held only for the login call and is never logged.
"""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage as MimeMessage

from app.email.base import EmailMessage, EmailProviderKind


class SmtpEmailProvider:
    kind = EmailProviderKind.SMTP

    def __init__(
        self,
        *,
        host: str,
        port: int,
        sender: str,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        timeout: int = 10,
    ) -> None:
        self._host = host
        self._port = port
        self._sender = sender
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._timeout = timeout

    # Building the MIME message is separated from transport so it can be verified without
    # a live SMTP server (tests build the message and assert it carries no leaked secret
    # beyond the intended body).
    def build_message(self, message: EmailMessage) -> MimeMessage:
        mime = MimeMessage()
        mime["From"] = self._sender
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.text_body)
        if message.html_body:
            mime.add_alternative(message.html_body, subtype="html")
        return mime

    def send(self, message: EmailMessage) -> None:
        mime = self.build_message(message)
        with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as client:
            if self._use_tls:
                client.starttls(context=ssl.create_default_context())
            if self._username and self._password:
                client.login(self._username, self._password)
            client.send_message(mime)
