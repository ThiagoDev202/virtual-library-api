"""Infraestrutura assíncrona de banco de dados (engine, sessão e Base ORM)."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os models do projeto."""


engine = create_async_engine(settings.DATABASE_URL, future=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão assíncrona por request, garantindo fechamento ao final."""
    async with AsyncSessionLocal() as session:
        yield session
