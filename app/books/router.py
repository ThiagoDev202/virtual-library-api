"""Endpoints HTTP da feature `books` sob o prefixo `/books`."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.schemas import BookCreate, BookPage, BookRead, BookUpdate
from app.books.service import BookService
from app.core.database import get_session

router = APIRouter(prefix="/books", tags=["books"])


async def get_book_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BookService:
    """Instancia `BookService` vinculado à sessão injetada por request."""
    return BookService(session)


BookServiceDep = Annotated[BookService, Depends(get_book_service)]


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar livro",
)
async def create_book(payload: BookCreate, service: BookServiceDep) -> BookRead:
    """Cria um novo livro e retorna o recurso persistido."""
    book = await service.create(payload)
    return BookRead.model_validate(book)


@router.get(
    "",
    response_model=BookPage,
    summary="Listar livros",
)
async def list_books(
    service: BookServiceDep,
    title: Annotated[
        str | None,
        Query(description="Filtro parcial case-insensitive por título."),
    ] = None,
    author: Annotated[
        str | None,
        Query(description="Filtro parcial case-insensitive por autor."),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Página atual (>= 1).")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Itens por página (1..100).")] = 20,
) -> BookPage:
    """Lista livros com paginação e filtros opcionais por título e autor."""
    items, total = await service.list(title=title, author=author, page=page, size=size)
    return BookPage(
        items=[BookRead.model_validate(book) for book in items],
        total=total,
        page=page,
        size=size,
    )


@router.get(
    "/{book_id}",
    response_model=BookRead,
    summary="Detalhar livro",
)
async def get_book(book_id: str, service: BookServiceDep) -> BookRead:
    """Retorna o livro correspondente ao identificador informado."""
    book = await service.get(book_id)
    return BookRead.model_validate(book)


@router.put(
    "/{book_id}",
    response_model=BookRead,
    summary="Atualizar livro",
)
async def update_book(
    book_id: str,
    payload: BookUpdate,
    service: BookServiceDep,
) -> BookRead:
    """Atualiza todos os campos de um livro existente."""
    book = await service.update(book_id, payload)
    return BookRead.model_validate(book)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover livro",
)
async def delete_book(book_id: str, service: BookServiceDep) -> None:
    """Remove um livro existente; resposta sem corpo."""
    await service.delete(book_id)
