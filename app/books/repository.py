"""Repositório assíncrono para acesso à tabela de livros."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.books.models import Book


class BookRepository:
    """Encapsula queries assíncronas sobre a entidade `Book`.

    A camada de repositório não executa `commit`; apenas `flush`. A decisão de
    confirmar ou reverter a transação é responsabilidade do service.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Armazena a sessão assíncrona utilizada em todas as queries."""
        self.session = session

    async def add(self, book: Book) -> Book:
        """Adiciona um livro à sessão e dá `flush` para materializar o ID."""
        self.session.add(book)
        await self.session.flush()
        return book

    async def get_by_id(self, book_id: str) -> Book | None:
        """Busca um livro pelo ID; retorna `None` se não existir."""
        stmt = select(Book).where(Book.id == book_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        title: str | None,
        author: str | None,
        page: int,
        size: int,
    ) -> tuple[list[Book], int]:
        """Lista livros com filtros parciais case-insensitive e paginação.

        Retorna a tupla `(items, total)`, onde `total` respeita os mesmos
        filtros aplicados aos itens. Ordena por `created_at` decrescente.
        """
        filters = []
        if title:
            filters.append(Book.title.ilike(f"%{title}%"))
        if author:
            filters.append(Book.author.ilike(f"%{author}%"))

        base_stmt = select(Book)
        count_stmt = select(func.count()).select_from(Book)
        if filters:
            base_stmt = base_stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        offset = (page - 1) * size
        items_stmt = base_stmt.order_by(Book.created_at.desc()).offset(offset).limit(size)

        items_result = await self.session.execute(items_stmt)
        total_result = await self.session.execute(count_stmt)

        items = list(items_result.scalars().all())
        total = int(total_result.scalar_one())
        return items, total

    async def update(self, book: Book) -> Book:
        """Persiste alterações pendentes no livro e retorna a instância atualizada."""
        await self.session.flush()
        return book

    async def delete(self, book: Book) -> None:
        """Remove o livro e dá `flush` para efetivar a operação na sessão."""
        await self.session.delete(book)
        await self.session.flush()
