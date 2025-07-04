#!/bin/bash
set -e

# Configuration minimale
PORT=${PORT:-8002}  # Port principal du serveur (par défaut: 8002)
HEALTH_PORT=8052     # Port pour le serveur de santé
HOST=0.0.0.0        # Forcer l'écoute sur toutes les interfaces
LOG_LEVEL=${LOG_LEVEL:-info}

# Vérification des variables requises
REQUIRED_VARS=("SUPABASE_URL" "SUPABASE_SERVICE_ROLE_KEY" "NEO4J_URI" "NEO4J_USER" "NEO4J_PASSWORD")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: Missing required environment variable: $var. Please define it in your .env file."
        exit 1
    fi
done

# Création des répertoires
mkdir -p /app/data /app/logs /app/.cache/huggingface

# Configuration de l'environnement
export TRANSFORMERS_CACHE=/app/.cache/huggingface
export PYTHONPATH="/app:$PYTHONPATH"

# Installation des dépendances Python nécessaires
if ! pip show uvicorn >/dev/null 2>&1; then
    pip install --no-cache-dir uvicorn[standard]
fi

if ! pip show fastapi >/dev/null 2>&1; then
    pip install --no-cache-dir fastapi
fi

# Ajout du répertoire src au PYTHONPATH
export PYTHONPATH=/app/src

# Fonction pour démarrer le serveur de santé
start_health_server() {
    echo "[$(date)] Starting health check server on http://$HOST:$HEALTH_PORT/health"
    
    # Créer un script Python minimal pour le serveur de santé
    cat > /app/health_server.py << 'EOL'
from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get('/health')
async def health_check():
    return {'status': 'ok', 'service': 'mcp-crawl4ai-rag'}

if __name__ == "__main__":
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('HEALTH_PORT', '8052'))
    print(f"Starting health check server on http://{host}:{port}/health")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level='info',
        access_log=True,
        timeout_keep_alive=30
    )
EOL
    
    # Exécuter le serveur de santé
    python3 /app/health_server.py
}

# Fonction pour vérifier que le serveur de santé répond
wait_for_health_server() {
    local max_attempts=10
    local attempt=0
    
    echo "[$(date)] Waiting for health check server to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://$HOST:$HEALTH_PORT/health" &> /dev/null; then
            echo "[$(date)] Health check server is ready!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo "[$(date)] Waiting for health check server to start (attempt $attempt/$max_attempts)..."
        sleep 2
    done
    
    echo "[$(date)] ERROR: Health check server failed to start after $max_attempts attempts"
    return 1
}

# Fonction de nettoyage
cleanup() {
    echo "[$(date)] Shutting down..."
    if [ -n "$HEALTH_SERVER_PID" ]; then
        echo "[$(date)] Stopping health check server (PID: $HEALTH_SERVER_PID)"
        kill -TERM "$HEALTH_SERVER_PID" 2>/dev/null || true
    fi
    exit 0
}

# Configurer le trap pour la gestion des signaux
trap cleanup SIGTERM SIGINT

# Créer le script de santé s'il n'existe pas
if [ ! -f /app/health_server.py ]; then
    start_health_server
fi

# Démarrer le serveur de santé en arrière-plan
echo "[$(date)] Starting health check server in background..."
python3 /app/health_server.py &
HEALTH_SERVER_PID=$!

# Attendre un court instant pour que le serveur démarre
sleep 2

# Vérifier que le serveur de santé est en cours d'exécution
if ! ps -p $HEALTH_SERVER_PID > /dev/null; then
    echo "[$(date)] ERROR: Failed to start health check server, exiting..."
    cleanup
    exit 1
fi

# Attendre que le serveur de santé soit prêt
if ! wait_for_health_server; then
    echo "[$(date)] ERROR: Health check server is not responding, exiting..."
    cleanup
    exit 1
fi

# Démarrer le serveur principal
echo "[$(date)] Starting main API server on http://$HOST:$PORT"

# Exécuter le script Python directement
cd /app
exec python -c "from src.crawl4ai_mcp import main; import asyncio; asyncio.run(main())"
