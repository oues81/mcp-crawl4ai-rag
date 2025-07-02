# ===========================================
# Étape finale - Construction de l'image finale
# ===========================================
FROM python:3.11-slim as final

# Création d'un utilisateur non-root pour la sécurité
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -s /sbin/nologin -c "Docker image user" appuser

# Définition des variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH=/app \
    # Configuration des chemins
    CRAWL4_AI_BASE_DIRECTORY=/app/data

# Installation des dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 libopenblas-dev gfortran curl dnsutils netcat-openbsd \
    git build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
WORKDIR /app
COPY requirements.txt .

# Installation des dépendances
RUN pip install --no-cache-dir setuptools==70.0.0 wheel==0.43.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copie des sources
COPY src/ src/
COPY pyproject.toml .

# Exposition du port utilisé par l'application
EXPOSE 8051

# Définition de l'utilisateur non-root
USER appuser

# Configuration pour forcer l'utilisation du CPU
ENV DISABLE_GPU=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_ENABLE_ONEDNN_OPTS=0 \
    TORCH_USE_CUDA=0 \
    PYTORCH_CUDA_ALLOC_CONF=0

# Commande de démarrage du serveur MCP
CMD ["python", "src/crawl4ai_mcp.py"]
