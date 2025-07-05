# Utiliser une image Python 3.11 légère
FROM python:3.11-slim-bullseye

# Définir les variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    CRAWL4_AI_BASE_DIRECTORY=/app/data \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    TOKENIZERS_PARALLELISM=true \
    PORT=8002 \
    PYTHONPATH=/app

WORKDIR /app

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Installer uv via pip
RUN pip install uv

# Copier les fichiers du projet
COPY pyproject.toml . 
COPY src/ ./src

# Installer les dépendances du projet dans l'environnement système
# Utiliser --extra-index-url pour les paquets CPU de torch
RUN uv pip install --system --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match -r pyproject.toml

# Exécuter le script de configuration de crawl4ai
RUN crawl4ai-setup

# Créer le répertoire de données pour que les permissions soient correctes
RUN mkdir -p /app/data

# Créer un utilisateur non-root pour l'exécution
RUN useradd --create-home --shell /bin/bash appuser
RUN chown -R appuser:appuser /app


# Exposer le port de l'application
EXPOSE 8002

# Commande pour démarrer le serveur
CMD ["uvicorn", "src.mcp_crawl4ai_rag.main:app", "--host", "0.0.0.0", "--port", "8002"]
