FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY alembic.ini /app/alembic.ini
COPY alembic_multidb /app/alembic_multidb
COPY config /app/config

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-m", "whale.ingest.runtime.entrypoint"]
