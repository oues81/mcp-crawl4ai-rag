# Étape 1: Builder pour les dépendances de compilation
FROM python:3.12-slim-bookworm as builder

# Installer uniquement les dépendances de compilation nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Créer et activer un environnement virtuel
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Installer les dépendances de manière optimisée
WORKDIR /app
COPY docker/services/mcp-crawl4ai-rag/requirements-minimal.txt .

# Installer les dépendances en une seule couche pour réduire la taille
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --no-warn-script-location \
    --no-deps \
    -r requirements-minimal.txt

# Étape 2: Image finale minimale
FROM python:3.12-slim-bookworm

# Variables d'environnement minimales
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    CRAWL4_AI_BASE_DIRECTORY=/app/data \
    PYTHONPATH="/app/src"  # Mise à jour du PYTHONPATH

# Installer uniquement les dépendances système essentielles
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier uniquement l'environnement virtuel nécessaire
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Configurer l'utilisateur non-root
RUN useradd -m appuser && \
    mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 777 /app/data /app/logs

# Copier uniquement les fichiers nécessaires
COPY --chown=appuser:appuser docker/services/mcp-crawl4ai-rag/src/ /app/src/

# Vérifier que le fichier crawl4ai_mcp.py est présent
RUN ls -la /app/src/crawl4ai_mcp.py

# Utiliser l'utilisateur non-root
USER appuser
WORKDIR /app

# Exposer le port et démarrer
EXPOSE 8002
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
