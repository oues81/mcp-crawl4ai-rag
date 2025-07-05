# Dockerfile optimisé pour le service mcp-crawl4ai-rag
# Utilisation d'une image Python officielle plus légère
FROM python:3.11-slim as builder

# Installation des dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier uniquement les fichiers nécessaires pour l'installation des dépendances
COPY requirements.txt .

# Installer les dépendances Python dans un répertoire temporaire
RUN pip install --user --no-warn-script-location -r requirements.txt

# Étape 2: Image finale
FROM python:3.11-slim

# Installer les dépendances système minimales
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    procps \
    ca-certificates \
    iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/nc.openbsd /usr/bin/nc \
    && ln -s /usr/bin/nc.openbsd /usr/bin/netcat

WORKDIR /app

# Copier les fichiers nécessaires
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
COPY start-mcp-service.sh .

# Configurer l'environnement
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Assurer que le script de démarrage est exécutable
RUN chmod +x /app/start-mcp-service.sh

# Nettoyer le cache pip
RUN find /usr/local -depth \
    \( \
        \( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
        -o \
        \( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
    \) -exec rm -rf '{}' + \
    && rm -rf /root/.cache/pip/*

# Point d'entrée
CMD ["./start-mcp-service.sh"]
