"""Testes de integração dos endpoints `/api/v1/books` e `/health`."""

from typing import Any

import pytest
from httpx import AsyncClient

_VALID_PAYLOAD: dict[str, Any] = {
    "title": "Dom Casmurro",
    "author": "Machado de Assis",
    "published_date": "1899-01-01",
    "summary": "Narrativa em primeira pessoa sobre Bento Santiago e Capitu.",
}

_MISSING_ID = "00000000-0000-0000-0000-000000000000"


def _payload(**overrides: Any) -> dict[str, Any]:
    """Gera um payload válido permitindo sobrescrever campos pontualmente."""
    data = dict(_VALID_PAYLOAD)
    data.update(overrides)
    return data


async def _create_book(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    """Cria um livro via API e retorna o corpo da resposta."""
    response = await client.post("/api/v1/books", json=_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """`GET /health` retorna 200 com status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_book_returns_201_with_generated_id(client: AsyncClient) -> None:
    """`POST /api/v1/books` retorna 201 com livro completo e ID gerado."""
    response = await client.post("/api/v1/books", json=_VALID_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert len(body["id"]) == 36
    assert body["title"] == _VALID_PAYLOAD["title"]
    assert body["author"] == _VALID_PAYLOAD["author"]
    assert body["published_date"] == _VALID_PAYLOAD["published_date"]
    assert body["summary"] == _VALID_PAYLOAD["summary"]
    assert body["created_at"]
    assert body["updated_at"]


@pytest.mark.asyncio
async def test_create_book_invalid_payload_returns_422(client: AsyncClient) -> None:
    """Payload inválido (título vazio, resumo curto) retorna 422."""
    response = await client.post(
        "/api/v1/books",
        json=_payload(title="", summary="curto"),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_books_without_filters_returns_pagination(client: AsyncClient) -> None:
    """`GET /api/v1/books` sem filtros retorna a paginação correta."""
    await _create_book(client, title="Livro A")
    await _create_book(client, title="Livro B")

    response = await client.get("/api/v1/books")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["size"] == 20
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_list_books_filters_by_title_case_insensitive(client: AsyncClient) -> None:
    """Filtro `title` é parcial e case-insensitive."""
    await _create_book(client, title="Dom Casmurro")
    await _create_book(client, title="Memórias Póstumas")

    response = await client.get("/api/v1/books", params={"title": "dom"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Dom Casmurro"


@pytest.mark.asyncio
async def test_list_books_filters_by_author_case_insensitive(client: AsyncClient) -> None:
    """Filtro `author` é parcial e case-insensitive."""
    await _create_book(client, author="Machado de Assis")
    await _create_book(client, author="Clarice Lispector")

    response = await client.get("/api/v1/books", params={"author": "assis"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["author"] == "Machado de Assis"


@pytest.mark.asyncio
async def test_list_books_combined_filters(client: AsyncClient) -> None:
    """Filtros `title` e `author` combinam com AND."""
    await _create_book(client, title="Dom Casmurro", author="Machado de Assis")
    await _create_book(client, title="Dom Quixote", author="Cervantes")
    await _create_book(client, title="Memórias Póstumas", author="Machado de Assis")

    response = await client.get(
        "/api/v1/books",
        params={"title": "dom", "author": "machado"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Dom Casmurro"


@pytest.mark.asyncio
async def test_list_books_pagination_second_page(client: AsyncClient) -> None:
    """Paginação `page=2&size=5` retorna a fatia correta."""
    for idx in range(7):
        await _create_book(client, title=f"Livro {idx}")

    response = await client.get("/api/v1/books", params={"page": 2, "size": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 7
    assert body["page"] == 2
    assert body["size"] == 5
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_list_books_invalid_page_returns_422(client: AsyncClient) -> None:
    """`page=0` viola validação de query e retorna 422."""
    response = await client.get("/api/v1/books", params={"page": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_books_invalid_size_returns_422(client: AsyncClient) -> None:
    """`size=0` viola validação de query e retorna 422."""
    response = await client.get("/api/v1/books", params={"size": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_book_returns_200_when_found(client: AsyncClient) -> None:
    """`GET /api/v1/books/{id}` retorna 200 para livro existente."""
    created = await _create_book(client)

    response = await client.get(f"/api/v1/books/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["title"] == created["title"]


@pytest.mark.asyncio
async def test_get_book_returns_404_when_missing(client: AsyncClient) -> None:
    """`GET /api/v1/books/{id}` retorna 404 com mensagem padrão quando não existe."""
    response = await client.get(f"/api/v1/books/{_MISSING_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Livro não encontrado"}


@pytest.mark.asyncio
async def test_update_book_returns_200_when_found(client: AsyncClient) -> None:
    """`PUT /api/v1/books/{id}` atualiza e retorna 200 com dados novos."""
    created = await _create_book(client)

    new_payload = _payload(
        title="Novo Título",
        author="Outro Autor",
        published_date="1900-05-10",
        summary="Resumo atualizado com tamanho suficiente para validar.",
    )
    response = await client.put(f"/api/v1/books/{created['id']}", json=new_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["title"] == "Novo Título"
    assert body["author"] == "Outro Autor"
    assert body["published_date"] == "1900-05-10"
    assert body["summary"] == "Resumo atualizado com tamanho suficiente para validar."


@pytest.mark.asyncio
async def test_update_book_returns_404_when_missing(client: AsyncClient) -> None:
    """`PUT /api/v1/books/{id}` retorna 404 quando o livro não existe."""
    response = await client.put(f"/api/v1/books/{_MISSING_ID}", json=_VALID_PAYLOAD)

    assert response.status_code == 404
    assert response.json() == {"detail": "Livro não encontrado"}


@pytest.mark.asyncio
async def test_delete_book_returns_204_and_subsequent_get_404(client: AsyncClient) -> None:
    """`DELETE /api/v1/books/{id}` retorna 204 e `GET` subsequente dá 404."""
    created = await _create_book(client)

    delete_response = await client.delete(f"/api/v1/books/{created['id']}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = await client.get(f"/api/v1/books/{created['id']}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_book_returns_404_when_missing(client: AsyncClient) -> None:
    """`DELETE /api/v1/books/{id}` retorna 404 com mensagem padrão quando não existe."""
    response = await client.delete(f"/api/v1/books/{_MISSING_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Livro não encontrado"}
