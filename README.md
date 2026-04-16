# Virtual Library API

API REST assíncrona para cadastro e consulta de livros em uma biblioteca virtual. Construída com FastAPI e SQLAlchemy 2.0 async sobre SQLite, expõe cinco endpoints CRUD sob `/api/v1/books` com paginação, filtros parciais case-insensitive e documentação interativa automática. Empacotada em Docker com migrations executadas automaticamente na inicialização.

---

## Stack

- **Python 3.12** com tipagem estática completa
- **FastAPI** — framework web async/await
- **SQLAlchemy 2.0** — ORM com API async nativa
- **aiosqlite** — driver SQLite assíncrono
- **Alembic** — migrations versionadas
- **Pydantic v2** + **pydantic-settings** — validação e configuração
- **uv** — gerenciador de pacotes e ambientes virtuais
- **Ruff** — lint e formatação
- **Docker + Docker Compose** — empacotamento e orquestração

---

## Pré-requisitos

| Ferramenta | Versão mínima | Obrigatório |
|------------|---------------|-------------|
| Python     | 3.12          | Sim (execução local) |
| uv         | qualquer      | Sim (execução local) |
| Docker     | 20.x          | Não (apenas para container) |
| Docker Compose | v2 (plugin) | Não (apenas para container) |

---

## Como rodar localmente

```bash
# 1. Instalar dependências (cria .venv automaticamente)
uv sync

# 2. Aplicar migrations no banco local
uv run alembic upgrade head

# 3. Subir o servidor com hot-reload
uv run uvicorn app.main:app --reload
```

A API ficará disponível em `http://localhost:8000`.

---

## Como rodar com Docker

```bash
docker compose up --build
```

O container executa as migrations automaticamente antes de iniciar o servidor. O banco SQLite é armazenado em `./data/library.db`, montado como volume para sobreviver a `docker compose down`.

---

## Endpoints disponíveis

| Método   | Path                      | Descrição                              |
|----------|---------------------------|----------------------------------------|
| `GET`    | `/health`                 | Liveness check                         |
| `POST`   | `/api/v1/books`           | Cadastrar livro                        |
| `GET`    | `/api/v1/books`           | Listar livros com paginação e filtros  |
| `GET`    | `/api/v1/books/{id}`      | Buscar livro por ID                    |
| `PUT`    | `/api/v1/books/{id}`      | Atualizar livro (todos os campos)      |
| `DELETE` | `/api/v1/books/{id}`      | Remover livro                          |

### Parâmetros de listagem (`GET /api/v1/books`)

| Parâmetro | Tipo     | Padrão | Descrição                                        |
|-----------|----------|--------|--------------------------------------------------|
| `title`   | string   | —      | Filtro parcial case-insensitive por título       |
| `author`  | string   | —      | Filtro parcial case-insensitive por autor        |
| `page`    | int ≥ 1  | 1      | Número da página                                 |
| `size`    | int 1–100| 20     | Itens por página                                 |

---

## Exemplos curl

### Health check

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### Cadastrar livro

```bash
curl -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Dom Casmurro",
    "author": "Machado de Assis",
    "published_date": "1899-01-01",
    "summary": "Narrativa em primeira pessoa que acompanha a trajetória de Bento Santiago e sua obsessão por Capitu."
  }'
```

Resposta `201`:

```json
{
  "id": "b3f4e8c2-8a4d-4a5a-9c1f-1a2b3c4d5e6f",
  "title": "Dom Casmurro",
  "author": "Machado de Assis",
  "published_date": "1899-01-01",
  "summary": "Narrativa em primeira pessoa que acompanha a trajetória de Bento Santiago e sua obsessão por Capitu.",
  "created_at": "2026-04-16T14:30:00Z",
  "updated_at": "2026-04-16T14:30:00Z"
}
```

### Listar livros

```bash
# Todos os livros (página 1, 20 por página)
curl "http://localhost:8000/api/v1/books"

# Filtrar por autor
curl "http://localhost:8000/api/v1/books?author=machado&page=1&size=10"
```

### Buscar livro por ID

```bash
curl http://localhost:8000/api/v1/books/b3f4e8c2-8a4d-4a5a-9c1f-1a2b3c4d5e6f
```

### Atualizar livro

```bash
curl -X PUT http://localhost:8000/api/v1/books/b3f4e8c2-8a4d-4a5a-9c1f-1a2b3c4d5e6f \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Dom Casmurro",
    "author": "Machado de Assis",
    "published_date": "1899-01-01",
    "summary": "Clássico da literatura brasileira publicado originalmente em 1899, narrado por Bento Santiago."
  }'
```

### Remover livro

```bash
curl -X DELETE http://localhost:8000/api/v1/books/b3f4e8c2-8a4d-4a5a-9c1f-1a2b3c4d5e6f
# 204 No Content
```

### Validação de persistência

Para confirmar que os dados sobrevivem a reinícios do container:

```bash
docker compose up -d --build

curl -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Persistencia Teste",
    "author": "QA",
    "published_date": "2026-04-16",
    "summary": "Registro de teste para validar persistencia entre reinicios do compose."
  }'

docker compose down
docker compose up -d

curl "http://localhost:8000/api/v1/books?title=persistencia"
# O livro criado antes do down deve aparecer na resposta.

docker compose down
```

O arquivo `./data/library.db` é montado como volume e preserva os dados entre execuções.

---

## Documentação interativa

Com a API em execução:

- **Swagger UI** — `http://localhost:8000/docs`
- **ReDoc** — `http://localhost:8000/redoc`

Ambas são geradas automaticamente pelo FastAPI a partir dos schemas Pydantic.

---

## Testes

```bash
uv run pytest -v --cov=app --cov-report=term-missing
```

- **Unitários** (`tests/unit/`) — `BookRepository` e `BookService` com SQLite em memória e mocks.
- **Integração** (`tests/integration/`) — endpoints testados com `httpx.AsyncClient` + SQLite em memória isolado por teste.
- **Cobertura alvo:** ≥ 85% em `app/books/`.

---

## Qualidade de código

```bash
# Verificar lint
uv run ruff check .

# Verificar formatação
uv run ruff format --check .
```

Ambos os comandos devem passar sem erros antes de qualquer commit.

---

## Estrutura do projeto

```
virtual-library-api/
├── app/
│   ├── main.py                 # Cria FastAPI, monta /api/v1, registra handlers
│   ├── core/
│   │   ├── config.py           # Settings com pydantic-settings
│   │   ├── database.py         # Engine async + get_session
│   │   └── exceptions.py       # Erros de domínio e handlers HTTP
│   ├── books/
│   │   ├── router.py           # Endpoints HTTP de /books
│   │   ├── service.py          # Regras de negócio e transações
│   │   ├── repository.py       # Queries SQLAlchemy async
│   │   ├── schemas.py          # DTOs Pydantic (entrada e saída)
│   │   └── models.py           # Entidade ORM Book
│   └── api/
│       └── v1.py               # Router raiz com prefixo /api/v1
├── tests/
│   ├── conftest.py             # Fixtures globais (engine in-memory, client)
│   ├── unit/                   # Testes unitários de service e repository
│   └── integration/            # Testes de endpoint com AsyncClient
├── migrations/
│   ├── env.py                  # Configuração Alembic async
│   └── versions/               # Migrations versionadas
├── docker/
│   └── entrypoint.sh           # Executa migrations e inicia uvicorn
├── data/                       # Volume SQLite (gitignored)
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── pyproject.toml
└── uv.lock
```

---

## Variáveis de ambiente

| Variável       | Padrão                                    | Descrição                                  |
|----------------|-------------------------------------------|--------------------------------------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/library.db`   | URL de conexão ao banco SQLite             |
| `APP_ENV`      | `development`                             | Ambiente de execução (`development` / `production`) |
| `LOG_LEVEL`    | `INFO`                                    | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

Em execução local, crie um arquivo `.env` na raiz com os valores desejados. No Docker, as variáveis são definidas no `docker-compose.yml`.

---

## Licença

MIT
