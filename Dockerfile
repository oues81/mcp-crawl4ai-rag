# syntax=docker/dockerfile:1.4

# Étape 1: Image de base avec CUDA
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 as base

# Variables d'environnement communes
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH="/root/.local/bin:$PATH" \
    PIP_CACHE_DIR=/root/.cache/pip \
    PIP_NO_CACHE_DIR=0 \
    HF_HOME=/root/.cache/huggingface \
    TORCH_HOME=/root/.cache/torch \
    FLASH_ATTENTION_SKIP_CUDA_BUILD=1

# Installation des dépendances système
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    python3-pip \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Configuration de Python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    pip install --upgrade pip setuptools wheel

# Création des dossiers de cache
RUN mkdir -p /root/.cache/huggingface /root/.cache/torch /root/.cache/pip && \
    chmod -R 777 /root/.cache

# Étape 2: Builder l'application
FROM base as builder

WORKDIR /app

# Copier les fichiers de dépendances d'abord pour optimiser le cache
COPY requirements.txt .

# Installer d'abord les dépendances lourdes avec cache optimisé
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/torch \
    --mount=type=cache,target=/root/.cache/huggingface \
    pip install --no-cache-dir torch==2.1.2+cu121 torchvision==0.16.2+cu121 torchaudio==2.1.2+cu121 --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Étape 3: Image finale (app)
FROM base as app

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/app/bin:$PATH" \
    HUGGINGFACE_HUB_CACHE="/root/.cache/huggingface/hub" \
    TORCH_HOME="/root/.cache/torch" \
    CUDA_VISIBLE_DEVICES="all"

# Installation des dépendances système minimales
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier uniquement les fichiers nécessaires
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Créer les dossiers de cache nécessaires
RUN mkdir -p /root/.cache/huggingface/hub /root/.cache/torch /root/.cache/pip \
    && chmod -R 777 /root/.cache

# Rendre les scripts exécutables
RUN find /app -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

# Exposer le port de l'application
EXPOSE 8051

# Commande par défaut
CMD ["./startup.sh"]
