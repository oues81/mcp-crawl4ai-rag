# syntax=docker/dockerfile:1.4

# =============================================================================
# ÉTAPE 1: BUILDER - Installation des dépendances
# =============================================================================
FROM python:3.11-slim as builder

# Variables d'environnement pour Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

WORKDIR /app

# Installation des dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Installation de Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"

# Copie des fichiers de dépendances
# Le contexte est la racine du projet, donc on spécifie le chemin
COPY pyproject.toml poetry.lock ./

# Installation des dépendances applicatives (uniquement 'main')
# L'option --no-root empêche l'installation du projet lui-même, ce qui est bien car nous copions le code source plus tard.
# Installe les dépendances de production uniquement (la syntaxe --no-dev est obsolète)
RUN poetry install --no-root

# =============================================================================
# ÉTAPE 2: FINAL - Image d'exécution optimisée
# =============================================================================
FROM python:3.11-slim as final

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CRAWL4_AI_BASE_DIRECTORY=/data \
    PORT=8002

WORKDIR /app

# Copie des dépendances installées depuis l'étape builder
COPY --from=builder /app /app

# Copie du code source de l'application
# Copie du code source de l'application, en utilisant le chemin correct fourni
COPY ./docker/services/mcp-crawl4ai-rag/src /app/src

# Copie du script d'entrée et le rend exécutable
COPY ./docker/services/mcp-crawl4ai-rag/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE ${PORT}

# Le point d'entrée exécute le script qui lance l'application
ENTRYPOINT ["/app/entrypoint.sh"]

# La commande par défaut peut être surchargée, mais ici on lance uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]