from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from api.config import settings


class Base(DeclarativeBase):
    pass


def build_asyncpg_connection_settings(database_url: str) -> tuple[str, dict[str, object]]:
    url = make_url(database_url)
    query = dict(url.query)
    connect_args: dict[str, object] = {}

    sslmode = query.pop("sslmode", None)
    if sslmode and sslmode != "disable":
        connect_args["ssl"] = True

    return url.set(query=query).render_as_string(hide_password=False), connect_args


database_url, connect_args = build_asyncpg_connection_settings(settings.database_url)

engine: AsyncEngine = create_async_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


async def ping_database() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def database_is_available() -> bool:
    try:
        await ping_database()
    except Exception:
        return False
    return True


async def init_models() -> None:
    from api.db import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


def init_db() -> None:
    asyncio.run(init_models())


async def close_database() -> None:
    await engine.dispose()
