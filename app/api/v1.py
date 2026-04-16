"""Router raiz da versão 1 da API, agregando as features sob `/api/v1`."""

from fastapi import APIRouter

from app.books.router import router as books_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(books_router)
