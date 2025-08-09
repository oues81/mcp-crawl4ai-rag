# syntax=docker/dockerfile:1.7-labs
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
    PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright \
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

## 1) Dépendances système minimales + caches APT
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    python3-dev \
    postgresql-client \
    iputils-ping \
    dnsutils \
    net-tools \
    lsof \
    curl \
    git \
    jq \
    # Deps Chromium headless minimales (au lieu de playwright install-deps massif)
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnss3 \
    libnspr4 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    libxshmfence1 \
    libegl1 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxcb-dri3-0

## 2) Préparer le répertoire app
WORKDIR /app

## 3) Installer uv + dépendances Python (sans lier aux sources) avec cache UV
COPY pyproject.toml uv.lock requirements-optimized.txt ./
RUN --mount=type=cache,target=/root/.cache/uv \
    pip install --no-cache-dir --upgrade pip uv && \
    uv pip install --system torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu && \
    # Installer un jeu de dépendances stable (sans editable) pour maximiser le cache
    uv pip install --system -r requirements-optimized.txt

## 4) Installer les dépendances système Playwright requises et les navigateurs
RUN python -m playwright install-deps chromium && \
    python -m playwright install firefox chromium

## 5) Créer les répertoires nécessaires avec les bonnes permissions
RUN mkdir -p /app/data /app/logs /app/.cache /tmp/chrome-crashes && \
    chmod -R 777 /app/logs /app/data /app/.cache /tmp/chrome-crashes

# Créer un utilisateur non-root pour exécuter l'application
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    # Préparer le répertoire de cache des navigateurs Playwright
    mkdir -p /home/appuser/.cache/ms-playwright && \
    chown -R appuser:appuser /home/appuser/.cache

## 6) Copier le code applicatif en dernier pour minimiser les invalidations de cache
COPY . .

# Basculer vers l'utilisateur non-root
USER appuser

# Exposer le port du serveur
EXPOSE ${PORT}

## 7) Installer la couche d'application (setup + éventuelles migrations locales) côté appuser
RUN crawl4ai-setup

# Point d'entrée pour démarrer le service HTTP
CMD ["python", "src/http_server.py"]
