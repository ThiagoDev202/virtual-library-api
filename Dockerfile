# Stage 1: builder — instala dependências de produção com uv
FROM python:3.12-slim AS builder

WORKDIR /app

# Instala uv
RUN pip install --no-cache-dir uv

# Copia apenas os arquivos de manifesto para aproveitar cache de camadas
COPY pyproject.toml uv.lock ./

# Gera o ambiente virtual com dependências de produção (sem dev)
RUN uv sync --frozen --no-dev

# Stage 2: runtime — imagem enxuta sem ferramentas de build
FROM python:3.12-slim

WORKDIR /app

# Cria usuário não-root para segurança (UID/GID 1000 alinha com usuário padrão do host
# em bind mounts tipo ./data:/app/data)
RUN addgroup --system --gid 1000 appgroup && adduser --system --uid 1000 --ingroup appgroup appuser

# Copia o ambiente virtual gerado no builder
COPY --from=builder /app/.venv /app/.venv

# Copia código-fonte e configurações necessárias em runtime
COPY app/ app/
COPY migrations/ migrations/
COPY alembic.ini ./
COPY docker/entrypoint.sh ./entrypoint.sh

# Torna o entrypoint executável
RUN chmod +x /app/entrypoint.sh

# Cria diretório de dados com permissões corretas para o volume SQLite
RUN mkdir -p /app/data && chown appuser:appgroup /app/data

# Garante que o appuser seja dono dos arquivos copiados
RUN chown -R appuser:appgroup /app

# Adiciona o venv ao PATH
ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
