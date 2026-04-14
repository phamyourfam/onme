from __future__ import annotations

import uvicorn

from api.config import settings


def main() -> None:
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
