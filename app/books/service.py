"""Camada de serviço com regras de negócio e controle transacional de livros."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.books.models import Book
from app.books.repository import BookRepository
from app.books.schemas import BookCreate, BookUpdate
from app.core.exceptions import BookNotFoundError


class BookService:
    """Orquestra operações de livro aplicando regras de negócio e transação.

    Recebe a `AsyncSession` diretamente para ser responsável pelo `commit` e
    instancia o `BookRepository` internamente. Essa abordagem mantém o
    repositório focado em queries e concentra o controle transacional na
    camada de serviço, conforme convenção do projeto.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Guarda a sessão e cria o repositório associado a ela."""
        self.session = session
        self.repository = BookRepository(session)

    async def create(self, data: BookCreate) -> Book:
        """Cadastra um novo livro e confirma a transação."""
        book = Book(
            title=data.title,
            author=data.author,
            published_date=data.published_date,
            summary=data.summary,
        )
        await self.repository.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def get(self, book_id: str) -> Book:
        """Retorna o livro pelo ID ou levanta `BookNotFoundError`."""
        book = await self.repository.get_by_id(book_id)
        if book is None:
            raise BookNotFoundError
        return book

    async def list(
        self,
        title: str | None,
        author: str | None,
        page: int,
        size: int,
    ) -> tuple[list[Book], int]:
        """Delega ao repositório a listagem paginada com filtros."""
        return await self.repository.list_paginated(title, author, page, size)

    async def update(self, book_id: str, data: BookUpdate) -> Book:
        """Atualiza todos os campos de um livro existente e confirma a transação."""
        book = await self.repository.get_by_id(book_id)
        if book is None:
            raise BookNotFoundError
        book.title = data.title
        book.author = data.author
        book.published_date = data.published_date
        book.summary = data.summary
        await self.repository.update(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def delete(self, book_id: str) -> None:
        """Remove um livro existente e confirma a transação."""
        book = await self.repository.get_by_id(book_id)
        if book is None:
            raise BookNotFoundError
        await self.repository.delete(book)
        await self.session.commit()
