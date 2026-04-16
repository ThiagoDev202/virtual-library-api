"""Schemas Pydantic v2 para entrada e saída de dados de livros."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

_BOOK_EXAMPLE = {
    "title": "Dom Casmurro",
    "author": "Machado de Assis",
    "published_date": "1899-01-01",
    "summary": (
        "Narrativa em primeira pessoa que acompanha a trajetória de Bento Santiago "
        "e sua obsessão por Capitu."
    ),
}

_BOOK_READ_EXAMPLE = {
    "id": "b3f4e8c2-8a4d-4a5a-9c1f-1a2b3c4d5e6f",
    **_BOOK_EXAMPLE,
    "created_at": "2026-04-16T14:30:00Z",
    "updated_at": "2026-04-16T14:30:00Z",
}


class BookBase(BaseModel):
    """Campos comuns de entrada para operações de escrita de livro."""

    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    published_date: date
    summary: str = Field(..., min_length=10, max_length=5000)


class BookCreate(BookBase):
    """Payload para cadastrar um novo livro."""

    model_config = ConfigDict(json_schema_extra={"example": _BOOK_EXAMPLE})


class BookUpdate(BookBase):
    """Payload para atualização total (PUT) de um livro existente."""

    model_config = ConfigDict(json_schema_extra={"example": _BOOK_EXAMPLE})


class BookRead(BookBase):
    """Representação de saída de um livro."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": _BOOK_READ_EXAMPLE},
    )


class BookPage(BaseModel):
    """Página de resultados para listagem paginada de livros."""

    items: list[BookRead]
    total: int
    page: int
    size: int
