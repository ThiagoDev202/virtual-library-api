"""Fixtures globais de testes: engine in-memory, sessão async e cliente HTTP."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_session
from app.main import app


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Engine SQLite em memória isolada por teste.

    Usa `StaticPool` para compartilhar a mesma conexão entre múltiplos usos
    no mesmo teste — caso contrário cada nova conexão contra `:memory:` criaria
    um banco distinto. `create_all`/`drop_all` só é permitido por tratar-se
    de contexto de testes (convenção do projeto).
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def client(async_engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP assíncrono com `get_session` sobrescrito para a engine de teste."""
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as async_client:
            yield async_client
    finally:
        app.dependency_overrides.clear()
