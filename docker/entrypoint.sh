#!/bin/sh
# Executa as migrations pendentes antes de subir o servidor,
# garantindo que o schema esteja sempre atualizado no volume.
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
