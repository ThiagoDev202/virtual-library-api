"""Ponto de entrada da aplicação FastAPI."""

from fastapi import FastAPI

app = FastAPI(
    title="Virtual Library API",
    version="0.1.0",
    description="API REST assíncrona para cadastro e consulta de livros em uma biblioteca virtual.",
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Verifica a disponibilidade da API."""
    return {"status": "ok"}
