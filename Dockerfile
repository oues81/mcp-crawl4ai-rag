# Utiliser une image Python 3.12 comme base
FROM python:3.12-slim

# Définir les variables d'environnement
ARG PORT=8010
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CRAWL4_AI_BASE_DIRECTORY=/app/data \
    PORT=${PORT} \
    HOST=0.0.0.0 \
    TRANSPORT=sse \
    # Désactiver complètement le GPU
    CUDA_VISIBLE_DEVICES=-1 \
    # Désactiver les optimisations GPU de PyTorch
    TORCH_CUDA_ARCH_LIST= \
    # Forcer PyTorch à utiliser le CPU
    PYTORCH_CUDA_ALLOC_CONF= \
    # Désactiver les optimisations CPU qui pourraient causer des problèmes
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 \
    MKL_DYNAMIC=FALSE \
    OMP_DYNAMIC=FALSE

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    python3-dev \
    postgresql-client \
    iputils-ping \
    dnsutils \
    net-tools \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Créer et configurer le répertoire de l'application
WORKDIR /app

# Copier les fichiers de l'application
COPY . .

# Installer uv et les dépendances Python
RUN pip install --no-cache-dir --upgrade pip uv && \
    # Installer PyTorch avec support CPU uniquement
    uv pip install --system torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu && \
    # Installer les dépendances principales
    uv pip install --system -e . && \
    # Setup crawl4ai
    crawl4ai-setup

# Créer les répertoires nécessaires avec les bonnes permissions
RUN mkdir -p /app/data /app/logs /app/.cache && \
    chmod -R 777 /app/logs /app/data /app/.cache

# Créer un utilisateur non-root pour exécuter l'application
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Basculer vers l'utilisateur non-root
USER appuser

# Exposer le port du serveur
EXPOSE ${PORT}

# Point d'entrée pour démarrer le service HTTP
CMD ["python", "src/http_server.py"]
