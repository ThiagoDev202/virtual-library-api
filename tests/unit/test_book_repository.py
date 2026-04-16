"""Testes unitários para `BookRepository` usando SQLite em memória."""

from collections.abc import AsyncGenerator
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.books.models import Book
from app.books.repository import BookRepository
from app.core.database import Base


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Cria uma engine SQLite em memória isolada por teste.

    Usa `StaticPool` para manter uma única conexão compartilhada — necessário
    porque cada conexão nova contra `:memory:` geraria um banco distinto. O
    uso de `Base.metadata.create_all` é permitido aqui por tratar-se de um
    cenário de teste em memória, conforme convenção do projeto.
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
async def session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão nova por teste, garantindo fechamento ao final."""
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as s:
        yield s


def _make_book(
    title: str = "Dom Casmurro",
    author: str = "Machado de Assis",
    summary: str = "Narrativa em primeira pessoa sobre Bento Santiago e Capitu.",
    published: date = date(1899, 1, 1),
) -> Book:
    """Fábrica simples para instanciar `Book` nos testes."""
    return Book(title=title, author=author, published_date=published, summary=summary)


@pytest.mark.asyncio
async def test_add_persists_book_and_assigns_id(session: AsyncSession) -> None:
    """`add` deve atribuir ID via default e tornar o livro recuperável."""
    repo = BookRepository(session)
    book = _make_book()

    saved = await repo.add(book)
    await session.commit()

    assert saved.id is not None
    assert len(saved.id) == 36


@pytest.mark.asyncio
async def test_get_by_id_returns_book_when_found(session: AsyncSession) -> None:
    """`get_by_id` retorna o livro quando o ID existe."""
    repo = BookRepository(session)
    book = await repo.add(_make_book())
    await session.commit()

    fetched = await repo.get_by_id(book.id)

    assert fetched is not None
    assert fetched.id == book.id
    assert fetched.title == "Dom Casmurro"


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing(session: AsyncSession) -> None:
    """`get_by_id` retorna `None` quando o ID é inexistente."""
    repo = BookRepository(session)

    fetched = await repo.get_by_id("00000000-0000-0000-0000-000000000000")

    assert fetched is None


@pytest.mark.asyncio
async def test_list_paginated_without_filters(session: AsyncSession) -> None:
    """Sem filtros, retorna todos os livros respeitando `page`/`size`."""
    repo = BookRepository(session)
    for i in range(5):
        await repo.add(_make_book(title=f"Livro {i}"))
    await session.commit()

    items, total = await repo.list_paginated(title=None, author=None, page=1, size=2)

    assert total == 5
    assert len(items) == 2


@pytest.mark.asyncio
async def test_list_paginated_second_page(session: AsyncSession) -> None:
    """A segunda página retorna o restante dos itens dentro de `size`."""
    repo = BookRepository(session)
    for i in range(3):
        await repo.add(_make_book(title=f"Livro {i}"))
    await session.commit()

    items, total = await repo.list_paginated(title=None, author=None, page=2, size=2)

    assert total == 3
    assert len(items) == 1


@pytest.mark.asyncio
async def test_list_paginated_filters_by_title_case_insensitive(session: AsyncSession) -> None:
    """Filtro de título deve ser parcial e case-insensitive."""
    repo = BookRepository(session)
    await repo.add(_make_book(title="Dom Casmurro"))
    await repo.add(_make_book(title="Memórias Póstumas"))
    await repo.add(_make_book(title="A Moreninha", author="Joaquim Manuel"))
    await session.commit()

    items, total = await repo.list_paginated(title="casmurro", author=None, page=1, size=10)

    assert total == 1
    assert items[0].title == "Dom Casmurro"


@pytest.mark.asyncio
async def test_list_paginated_filters_by_author_case_insensitive(session: AsyncSession) -> None:
    """Filtro de autor deve ser parcial e case-insensitive."""
    repo = BookRepository(session)
    await repo.add(_make_book(title="A", author="Machado de Assis"))
    await repo.add(_make_book(title="B", author="Clarice Lispector"))
    await session.commit()

    items, total = await repo.list_paginated(title=None, author="MACHADO", page=1, size=10)

    assert total == 1
    assert items[0].author == "Machado de Assis"


@pytest.mark.asyncio
async def test_list_paginated_filters_by_title_and_author(session: AsyncSession) -> None:
    """Filtros combinados devem ser aplicados com AND."""
    repo = BookRepository(session)
    await repo.add(_make_book(title="Dom Casmurro", author="Machado de Assis"))
    await repo.add(_make_book(title="Dom Quixote", author="Cervantes"))
    await repo.add(_make_book(title="Memórias Póstumas", author="Machado de Assis"))
    await session.commit()

    items, total = await repo.list_paginated(title="dom", author="machado", page=1, size=10)

    assert total == 1
    assert items[0].title == "Dom Casmurro"


@pytest.mark.asyncio
async def test_update_persists_field_changes(session: AsyncSession) -> None:
    """`update` deve persistir alterações feitas na entidade."""
    repo = BookRepository(session)
    book = await repo.add(_make_book())
    await session.commit()

    book.title = "Novo Título"
    await repo.update(book)
    await session.commit()

    refreshed = await repo.get_by_id(book.id)
    assert refreshed is not None
    assert refreshed.title == "Novo Título"


@pytest.mark.asyncio
async def test_delete_removes_book(session: AsyncSession) -> None:
    """`delete` deve remover o livro da base."""
    repo = BookRepository(session)
    book = await repo.add(_make_book())
    await session.commit()

    await repo.delete(book)
    await session.commit()

    assert await repo.get_by_id(book.id) is None
