from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.config import settings


def external_http_enabled() -> bool:
    return bool(settings.ALLOW_EXTERNAL_HTTP_APIS)


def host_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return bool(host and host in settings.allowed_hosts)


async def call_external_http(url: str, method: str = "POST", body: dict | None = None, headers: dict | None = None) -> dict:
    if not external_http_enabled():
        return {"ok": False, "error": "external_http_disabled"}
    if not host_allowed(url):
        return {"ok": False, "error": "host_not_allowed"}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.request(method.upper(), url, json=body or {}, headers=headers or {})
        content_type = response.headers.get("content-type", "")
        data = response.json() if "application/json" in content_type else {"text": response.text[:2000]}
        return {"ok": response.is_success, "status_code": response.status_code, "data": data}
