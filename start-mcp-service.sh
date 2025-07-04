#!/bin/sh
set -e

# Afficher les informations de version
python --version
pip --version

# Définir le chemin vers uvicorn
UVICORN_CMD="python -m uvicorn"

# Installer les dépendances si nécessaire
if [ "$INSTALL_DEPS" = "true" ]; then
    echo "Installing dependencies..."
    pip install --no-cache-dir -r requirements.txt
fi

# Vérifier la présence du module uvicorn
if ! $UVICORN_CMD --version > /dev/null 2>&1; then
    echo "Error: uvicorn module is not installed. Please rebuild the Docker image."
    exit 1
fi

# Créer les répertoires de données si nécessaire
mkdir -p /app/data /app/logs /app/.cache/huggingface
export TRANSFORMERS_CACHE=/app/.cache/huggingface

# Afficher les variables d'environnement pour le débogage
echo "Environment variables:"
echo "- PYTHONPATH: ${PYTHONPATH:-Not set}"
echo "- SUPABASE_URL: ${SUPABASE_URL:-Not set}"

# Afficher les clés de manière sécurisée
if [ -n "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "- SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY:0:5}...${SUPABASE_SERVICE_ROLE_KEY: -5} (${#SUPABASE_SERVICE_ROLE_KEY} chars)"
else
    echo "- SUPABASE_SERVICE_ROLE_KEY: Not set"
fi

if [ -n "$SUPABASE_ANON_KEY" ]; then
    echo "- SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:5}...${SUPABASE_ANON_KEY: -5} (${#SUPABASE_ANON_KEY} chars)"
else
    echo "- SUPABASE_ANON_KEY: Not set"
fi

# Démarrer le serveur de santé HTTP en arrière-plan
echo "Starting health check server on port 8080..."
python -c "import asyncio; from crawl4ai_mcp import start_http_server; asyncio.run(start_http_server())" &

# Démarrer le serveur principal
echo "Starting MCP server on port 8002..."
$UVICORN_CMD crawl4ai_mcp:app --host 0.0.0.0 --port 8002 --reload \
    --workers 2 \
    --no-access-log \
    --timeout-keep-alive 300 \
    --limit-concurrency 100 \
    --backlog 1000 \
    --limit-max-requests 10000 \
    --no-server-header \
    --no-date-header
