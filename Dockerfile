# Dockerfile optimisé pour le service mcp-crawl4ai-rag

# Étape 1: Builder avec Poetry
FROM python:3.11-slim as builder

# Variables d'environnement pour Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Installation de Poetry
RUN pip install poetry

# Création du répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY pyproject.toml poetry.lock* ./

# Installation des dépendances via Poetry
# --no-root pour ne pas installer le projet lui-même
RUN poetry install --no-root

# Installation des outils de débogage


# Étape 2: Image finale
FROM python:3.11-slim

# Variables d'environnement
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    CRAWL4_AI_BASE_DIRECTORY=/app/data

WORKDIR /app

# Copie de l'environnement virtuel depuis le builder
COPY --from=builder /app/.venv .venv

# Copie du code source de l'application
COPY . .

# Assurer que le script de démarrage est exécutable
RUN chmod +x /app/start-mcp-service.sh

# Point d'entrée
CMD ["/app/start-mcp-service.sh"]
