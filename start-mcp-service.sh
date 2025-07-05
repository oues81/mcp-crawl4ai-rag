#!/bin/bash
set -e

# Configuration minimale
PORT=${PORT:-8002}  # Port principal du serveur (par défaut: 8002)
HEALTH_PORT=${HEALTH_PORT:-8052}  # Port pour le serveur de santé
HOST=0.0.0.0        # Forcer l'écoute sur toutes les interfaces
LOG_LEVEL=${LOG_LEVEL:-info}

# Journalisation améliorée
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Fonction pour vérifier si un port est en écoute
check_port() {
    local port=$1
    local host=$2
    nc -z $host $port >/dev/null 2>&1
    return $?
}

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
    log "Starting health check server on http://$HOST:$HEALTH_PORT/health"
    
    # Créer le répertoire pour les logs si nécessaire
    mkdir -p /app/logs
    
    # Créer un script Python minimal pour le serveur de santé
    cat > /app/health_server.py << 'EOL'
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import uvicorn
import os
import sys
from contextlib import asynccontextmanager

# Configuration du logging
import logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/health_server.log')
    ]
)
logger = logging.getLogger('health-server')

# État global de santé
service_healthy = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global service_healthy
    # Démarrage
    logger.info("Health check server starting...")
    service_healthy = True
    yield
    # Arrêt
    service_healthy = False
    logger.info("Health check server shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get('/health')
async def health_check():
    global service_healthy
    if not service_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "service": "mcp-crawl4ai-rag"}
        )
    return {"status": "healthy", "service": "mcp-crawl4ai-rag"}

if __name__ == "__main__":
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('HEALTH_PORT', '8052'))
    logger.info(f"Starting health check server on http://{host}:{port}/health")
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level='info',
            access_log=True,
            timeout_keep_alive=30,
            log_config=None
        )
    except Exception as e:
        logger.error(f"Health server error: {str(e)}", exc_info=True)
        sys.exit(1)
EOL
    
    # Exécuter le serveur de santé en arrière-plan avec redirection des logs
    nohup python3 /app/health_server.py >> /app/logs/health_server.log 2>&1 & 
    echo $! > /tmp/health_server.pid
    
    # Attendre que le serveur démarre
    sleep 2
    
    # Vérifier que le serveur est bien démarré
    if ! check_port $HOST $HEALTH_PORT; then
        log "ERROR: Failed to start health check server"
        if [ -f /app/logs/health_server.log ]; then
            log "Health server logs:"
            cat /app/logs/health_server.log
        fi
        exit 1
    fi
    
    log "Health check server started successfully on port $HEALTH_PORT"
}

# Fonction pour vérifier que le serveur de santé répond
wait_for_health_server() {
    local max_attempts=15
    local attempt=0
    local health_url="http://$HOST:$HEALTH_PORT/health"
    
    log "Waiting for health check server to be ready at $health_url..."
    
    while [ $attempt -lt $max_attempts ]; do
        if check_port $HOST $HEALTH_PORT; then
            # Le port est en écoute, vérifions la réponse HTTP
            local response=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" 2>/dev/null || echo "000")
            
            if [ "$response" = "200" ]; then
                log "Health check server is ready and responding with HTTP 200"
                return 0
            else
                log "Health check server is running but returned HTTP $response"
            fi
        else
            log "Health check server port $HEALTH_PORT not yet listening (attempt $((attempt + 1))/$max_attempts)"
        fi
        
        attempt=$((attempt + 1))
        sleep 2
    done
    
    log "ERROR: Health check server failed to start after $max_attempts attempts"
    
    # Afficher les logs du serveur de santé en cas d'échec
    if [ -f /app/logs/health_server.log ]; then
        log "=== Health Server Logs ==="
        tail -n 50 /app/logs/health_server.log
        log "=========================="
    fi
    
    return 1
}

# Fonction de nettoyage
cleanup() {
    log "Shutting down..."
    
    # Arrêter le serveur de santé
    if [ -f /tmp/health_server.pid ]; then
        local pid=$(cat /tmp/health_server.pid)
        if [ -n "$pid" ] && ps -p $pid > /dev/null; then
            log "Stopping health check server (PID: $pid)"
            kill -TERM "$pid" 2>/dev/null || true
            # Attendre que le processus s'arrête
            for i in {1..5}; do
                if ! ps -p $pid > /dev/null; then
                    break
                fi
                sleep 1
            done
            # Tuer le processus s'il est toujours en cours d'exécution
            if ps -p $pid > /dev/null; then
                log "Force killing health check server (PID: $pid)"
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f /tmp/health_server.pid
    fi
    
    # Nettoyer les fichiers temporaires
    rm -f /app/healthcheck.tmp
    
    log "Cleanup complete"
    exit 0
}

# Configurer le trap pour la gestion des signaux
trap cleanup SIGTERM SIGINT

# Démarrer le serveur de santé
start_health_server

# Attendre que le serveur de santé soit prêt
if ! wait_for_health_server; then
    log "ERROR: Health check server is not responding, exiting..."
    cleanup
    exit 1
fi

# Démarrer le serveur principal
log "Starting main API server on http://$HOST:$PORT"

# Changer de répertoire
cd /app

# Exporter les variables d'environnement nécessaires
export PYTHONPATH="/app:$PYTHONPATH"

# Créer un fichier de log pour le serveur principal
mkdir -p /app/logs

# Démarrer le serveur principal en arrière-plan avec redirection des logs
log "Starting main server process..."
nohup python -c "from src.crawl4ai_mcp import main; import asyncio; asyncio.run(main())" >> /app/logs/main_server.log 2>&1 &
MAIN_SERVER_PID=$!
echo $MAIN_SERVER_PID > /tmp/main_server.pid

log "Main server started with PID $MAIN_SERVER_PID"

# Attendre que le serveur principal soit prêt
log "Waiting for main server to start on port $PORT..."
local server_started=false

for i in {1..30}; do
    if check_port $HOST $PORT; then
        log "Main server is running on port $PORT"
        server_started=true
        break
    fi
    log "Waiting for main server to start (attempt $i/30)..."
    sleep 1
done

if [ "$server_started" = false ]; then
    log "ERROR: Main server failed to start on port $PORT"
    
    # Afficher les logs du serveur principal en cas d'échec
    if [ -f /app/logs/main_server.log ]; then
        log "=== Main Server Logs ==="
        tail -n 50 /app/logs/main_server.log
        log "========================"
    fi
    
    cleanup
    exit 1
fi

# Mettre à jour l'état de santé global
log "Service is now fully operational"

# Boucle principale de surveillance
while true; do
    # Vérifier que le serveur principal est toujours en cours d'exécution
    if ! ps -p $MAIN_SERVER_PID > /dev/null; then
        log "ERROR: Main server process (PID: $MAIN_SERVER_PID) has stopped unexpectedly"
        break
    fi
    
    # Vérifier que le serveur de santé est toujours en cours d'exécution
    if [ -f /tmp/health_server.pid ]; then
        local health_pid=$(cat /tmp/health_server.pid)
        if [ -n "$health_pid" ] && ! ps -p $health_pid > /dev/null; then
            log "ERROR: Health server process (PID: $health_pid) has stopped unexpectedly"
            break
        fi
    else
        log "ERROR: Health server PID file not found"
        break
    fi
    
    sleep 5
done

# Si on sort de la boucle, il y a eu un problème
log "ERROR: Service is no longer healthy, initiating shutdown..."
cleanup
exit 1
