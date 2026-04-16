"""Ponto de entrada da aplicação FastAPI."""

from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.exceptions import register_exception_handlers

app = FastAPI(
    title="Virtual Library API",
    version="0.1.0",
    description="API REST assíncrona para cadastro e consulta de livros em uma biblioteca virtual.",
)

register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Verifica a disponibilidade da API."""
    return {"status": "ok"}
