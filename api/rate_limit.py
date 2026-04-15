from __future__ import annotations

from fastapi import Request
from slowapi import Limiter

from api.config import settings


def get_client_ip(request: Request) -> str:
    for header_name in ("cf-connecting-ip", "x-forwarded-for"):
        header_value = request.headers.get(header_name)
        if header_value:
            return header_value.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[],
    headers_enabled=True,
    storage_uri=settings.rate_limit_storage_url,
)

auth_rate_limit = limiter.shared_limit(
    settings.auth_rate_limit,
    scope="auth",
)

tryon_rate_limit = limiter.shared_limit(
    settings.tryon_rate_limit,
    scope="tryon:create",
)
