# syntax=docker/dockerfile:1.4

FROM python:3.12-slim

WORKDIR /app

# Installation des dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Variables d'environnement
ENV PYTHONPATH=/app:/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CRAWL4_AI_BASE_DIRECTORY=/data \
    PORT=8002

# Installation de Poetry
ENV POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="$POETRY_HOME/bin:$PATH"

# Installation de Poetry et configuration
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry && \
    chmod 755 /root/.local/bin/poetry && \
    poetry config virtualenvs.create false && \
    poetry config virtualenvs.in-project false

# Copie des fichiers de dépendances
COPY pyproject.toml poetry.lock* ./

# Installation des dépendances avec Poetry
RUN poetry install --no-interaction --no-ansi --no-root --only main && \
    # Nettoyage
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copie du code source de l'application
COPY ./docker/services/mcp-crawl4ai-rag/src /app/src

EXPOSE ${PORT}

# Commande de démarrage
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
