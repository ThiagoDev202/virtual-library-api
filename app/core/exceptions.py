"""Exceções de domínio e handlers HTTP centralizados."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class BookNotFoundError(Exception):
    """Levantada quando um livro solicitado não existe no banco."""

    def __init__(self, message: str = "Livro não encontrado") -> None:
        super().__init__(message)
        self.message = message


async def _book_not_found_handler(_request: Request, exc: BookNotFoundError) -> JSONResponse:
    """Converte `BookNotFoundError` em resposta HTTP 404 com payload padrão."""
    return JSONResponse(status_code=404, content={"detail": exc.message})


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers de exceções de domínio no aplicativo FastAPI."""
    app.add_exception_handler(BookNotFoundError, _book_not_found_handler)
