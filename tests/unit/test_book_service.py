"""Testes unitários para `BookService` com repositório mockado."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.books.models import Book
from app.books.schemas import BookCreate, BookUpdate
from app.books.service import BookService
from app.core.exceptions import BookNotFoundError


def _make_payload() -> BookCreate:
    """Payload válido de criação de livro."""
    return BookCreate(
        title="Dom Casmurro",
        author="Machado de Assis",
        published_date=date(1899, 1, 1),
        summary="Narrativa em primeira pessoa sobre Bento Santiago e Capitu.",
    )


def _make_book(book_id: str = "11111111-1111-1111-1111-111111111111") -> Book:
    """Instância de `Book` já com ID atribuído para simular persistência."""
    return Book(
        id=book_id,
        title="Dom Casmurro",
        author="Machado de Assis",
        published_date=date(1899, 1, 1),
        summary="Narrativa em primeira pessoa sobre Bento Santiago e Capitu.",
    )


def _build_service() -> tuple[BookService, AsyncMock, AsyncMock]:
    """Instancia o service com sessão e repositório mockados."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    repository = AsyncMock()

    service = BookService.__new__(BookService)
    service.session = session
    service.repository = repository
    return service, session, repository


@pytest.mark.asyncio
async def test_create_returns_book_with_id_and_commits() -> None:
    """`create` delega ao repositório, dá commit e retorna o livro."""
    service, session, repository = _build_service()

    async def fake_add(book: Book) -> Book:
        book.id = "22222222-2222-2222-2222-222222222222"
        return book

    repository.add.side_effect = fake_add

    payload = _make_payload()
    result = await service.create(payload)

    repository.add.assert_awaited_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(result)
    assert result.id == "22222222-2222-2222-2222-222222222222"
    assert result.title == payload.title


@pytest.mark.asyncio
async def test_get_returns_existing_book() -> None:
    """`get` retorna o livro quando o repositório o encontra."""
    service, _session, repository = _build_service()
    expected = _make_book()
    repository.get_by_id.return_value = expected

    result = await service.get(expected.id)

    assert result is expected
    repository.get_by_id.assert_awaited_once_with(expected.id)


@pytest.mark.asyncio
async def test_get_raises_when_not_found() -> None:
    """`get` levanta `BookNotFoundError` quando o repositório retorna `None`."""
    service, _session, repository = _build_service()
    repository.get_by_id.return_value = None

    with pytest.raises(BookNotFoundError):
        await service.get("missing-id")


@pytest.mark.asyncio
async def test_list_delegates_to_repository() -> None:
    """`list` encaminha argumentos ao repositório e devolve a tupla."""
    service, _session, repository = _build_service()
    expected_items = [_make_book()]
    repository.list_paginated.return_value = (expected_items, 1)

    items, total = await service.list(title="dom", author=None, page=1, size=20)

    assert items == expected_items
    assert total == 1
    repository.list_paginated.assert_awaited_once_with("dom", None, 1, 20)


@pytest.mark.asyncio
async def test_update_persists_changes_when_book_exists() -> None:
    """`update` altera campos e dá commit quando o livro existe."""
    service, session, repository = _build_service()
    existing = _make_book()
    repository.get_by_id.return_value = existing
    repository.update.return_value = existing

    payload = BookUpdate(
        title="Novo Título",
        author="Outro Autor",
        published_date=date(1900, 5, 10),
        summary="Resumo atualizado com tamanho suficiente para validar.",
    )

    result = await service.update(existing.id, payload)

    assert result.title == "Novo Título"
    assert result.author == "Outro Autor"
    assert result.published_date == date(1900, 5, 10)
    assert result.summary == "Resumo atualizado com tamanho suficiente para validar."
    repository.update.assert_awaited_once_with(existing)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(existing)


@pytest.mark.asyncio
async def test_update_raises_when_book_missing() -> None:
    """`update` levanta `BookNotFoundError` quando o livro não existe."""
    service, session, repository = _build_service()
    repository.get_by_id.return_value = None

    payload = BookUpdate(
        title="Novo Título",
        author="Outro Autor",
        published_date=date(1900, 5, 10),
        summary="Resumo atualizado com tamanho suficiente para validar.",
    )

    with pytest.raises(BookNotFoundError):
        await service.update("missing-id", payload)

    repository.update.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_removes_book_when_exists() -> None:
    """`delete` chama o repositório e dá commit quando o livro existe."""
    service, session, repository = _build_service()
    existing = _make_book()
    repository.get_by_id.return_value = existing

    await service.delete(existing.id)

    repository.delete.assert_awaited_once_with(existing)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_raises_when_book_missing() -> None:
    """`delete` levanta `BookNotFoundError` quando o livro não existe."""
    service, session, repository = _build_service()
    repository.get_by_id.return_value = None

    with pytest.raises(BookNotFoundError):
        await service.delete("missing-id")

    repository.delete.assert_not_awaited()
    session.commit.assert_not_awaited()
