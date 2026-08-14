"""Security response headers (Parts 59, 63).

Pure and framework-free so it can be unit-tested without a request. The API serves JSON
and authorized media bytes only (the SPA is a separate origin), so it locks the document
surface down hard: a strict Content-Security-Policy, no framing, no sniffing, no referrer.
HSTS is sent only on deployed (HTTPS) environments — never on local http. The interactive
API docs (enabled in local only) are exempted from CSP so Swagger UI's assets still load.
"""

from __future__ import annotations

_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")
_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
# Two years, matching the HSTS preload minimum; includeSubDomains is safe for an apex API.
_HSTS = "max-age=63072000; includeSubDomains"


def security_headers(*, path: str, deployed: bool, docs_enabled: bool) -> dict[str, str]:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Cross-Origin-Opener-Policy": "same-origin",
    }
    if deployed:
        headers["Strict-Transport-Security"] = _HSTS
    is_docs = any(path == p or path.startswith(p) for p in _DOCS_PATHS)
    if not (docs_enabled and is_docs):
        headers["Content-Security-Policy"] = _API_CSP
    return headers
