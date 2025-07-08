# Utiliser une image Python 3.11 slim comme base
FROM python:3.11-slim

# Définir les variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CRAIL4_AI_BASE_DIRECTORY=/app/data \
    PORT=8002 \
    LOG_LEVEL=INFO

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Créer et configurer le répertoire de l'application
WORKDIR /app

# Créer les répertoires nécessaires avec les bonnes permissions
RUN mkdir -p /app/data /app/logs /app/.cache && \
    chmod -R 777 /app/logs

# Copier les fichiers de l'application
COPY --chown=1000:1000 . .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir neo4j==5.14.1 uvicorn[standard] fastapi

# Vérifier l'installation des dépendances
RUN pip list | grep -E 'neo4j|uvicorn|fastapi|crawl4ai|fastmcp'

# Donner les permissions d'exécution au script d'entrée
RUN chmod +x /app/docker-entrypoint.sh

# Créer les répertoires nécessaires avec les bonnes permissions
RUN mkdir -p /app/logs /app/data /app/.cache/huggingface/transformers /app/.cache/torch && \
    chmod -R 777 /app/logs /app/data /app/.cache

# Créer un utilisateur non-root pour exécuter l'application
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Basculer vers l'utilisateur non-root
USER appuser

# Définir le répertoire de travail
WORKDIR /app

# Définir les variables d'environnement pour les caches
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers
ENV TORCH_HOME=/app/.cache/torch
ENV PYTHONPATH=/app
ENV CRAWL4_AI_BASE_DIRECTORY=/app/data
ENV PORT=8002

# Exposer le port
EXPOSE 8002

# Définir le point d'entrée
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Commande par défaut
CMD ["start-service"]
