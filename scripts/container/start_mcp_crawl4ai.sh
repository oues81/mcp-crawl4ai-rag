#!/bin/bash
# Script pour démarrer le service MCP Crawl4AI dans le conteneur
set -e

# Activer le mode de débogage si DEBUG est défini à true
if [ "${DEBUG:-false}" = "true" ]; then
    set -x
fi

# Définition des variables par défaut
: "${PORT:=8002}"
: "${HOST:=0.0.0.0}"
: "${WORKERS:=2}"
: "${LOG_LEVEL:=info}"
: "${PYTHONPATH:=/app}"

# Chemins importants
APP_DIR="/app"
VENV_DIR="/app/.venv"

# Fonction pour afficher un message d'erreur et quitter
function error_exit {
    echo "[ERREUR] $1" >&2
    exit 1
}

# Vérifier si le répertoire de l'application existe
if [ ! -d "$APP_DIR" ]; then
    error_exit "Le répertoire de l'application n'est pas trouvé à l'emplacement : $APP_DIR"
fi

# Vérifier si l'environnement virtuel existe
if [ ! -d "$VENV_DIR" ]; then
    error_exit "L'environnement virtuel n'est pas trouvé à l'emplacement : $VENV_DIR"
fi

# Activer l'environnement virtuel
source "${VENV_DIR}/bin/activate"

# Aller dans le répertoire de l'application
cd "$APP_DIR" || error_exit "Impossible de se déplacer dans le répertoire $APP_DIR"

# Charger les variables d'environnement si le fichier .env existe
if [ -f ".env" ]; then
    echo "Chargement des variables d'environnement depuis .env"
    set -a
    # shellcheck source=/dev/null
    source .env
    set +a
fi

# Afficher les informations de configuration
echo "=== Configuration du service MCP Crawl4AI ==="

# Création des répertoires nécessaires
mkdir -p /app/logs
mkdir -p /app/data

# Configuration des logs
exec > >(tee -a "$LOG_FILE") 2>&1

# Fonction pour logger les messages
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message"
}

# Vérification de la présence des fichiers requis
check_required_files() {
    local missing_files=0
    
    for file in "/app/src/main.py" "/app/src/crawl4ai_mcp.py"; do
        if [ ! -f "$file" ]; then
            log "ERROR" "Fichier requis introuvable: $file"
            missing_files=$((missing_files + 1))
        fi
    done
    
    if [ $missing_files -gt 0 ]; then
        log "ERROR" "$missing_files fichiers requis sont manquants"
        return 1
    fi
    
    return 0
}

# Vérification de l'environnement virtuel
check_virtualenv() {
    if [ ! -d "/app/.venv" ]; then
        log "ERROR" "L'environnement virtuel Python est introuvable dans /app/.venv"
        return 1
    fi
    
    # Vérification de la présence de uvicorn dans l'environnement virtuel
    if [ ! -f "/app/.venv/bin/uvicorn" ]; then
        log "ERROR" "uvicorn n'est pas installé dans l'environnement virtuel"
        return 1
    fi
    
    return 0
}

# Validation de l'environnement
validate_environment() {
    log "INFO" "Validation de l'environnement..."
    
    # Vérification des fichiers requis
    if ! check_required_files; then
        return 1
    fi
    
    # Vérification de l'environnement virtuel
    if ! check_virtualenv; then
        return 1
    fi
    
    # Vérification des variables d'environnement requises
    local required_vars=(
        "DATABASE_URL" "REDIS_URL" "QDRANT_URL"
        "SUPABASE_URL" "SUPABASE_KEY" "OPENAI_API_KEY"
        "VAULT_ADDR" "VAULT_TOKEN"
    )
    
    local missing_vars=0
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log "ERROR" "Variable d'environnement requise non définie: $var"
            missing_vars=$((missing_vars + 1))
        fi
    done
    
    if [ $missing_vars -gt 0 ]; then
        log "ERROR" "$missing_vars variables d'environnement requises sont manquantes"
        return 1
    fi
    
    # Vérification de la connectivité aux services
    if ! nc -z db 5432; then
        log "ERROR" "Impossible de se connecter à PostgreSQL sur db:5432"
        return 1
    fi
    
    if ! nc -z redis 6379; then
        log "ERROR" "Impossible de se connecter à Redis sur redis:6379"
        return 1
    fi
    
    if ! nc -z qdrant 6333; then
        log "ERROR" "Impossible de se connecter à Qdrant sur qdrant:6333"
        return 1
    fi
    
    log "INFO" "Validation de l'environnement réussie"
    return 0
}

# Affichage des informations de configuration
log "INFO" "Configuration du service MCP Crawl4AI RAG :"
log "INFO" "- HOST: $HOST"
log "INFO" "- PORT: $PORT"
log "INFO" "- WORKERS: $WORKERS"
log "INFO" "- TIMEOUT: $TIMEOUT"
log "INFO" "- LOG_LEVEL: $LOG_LEVEL"
log "INFO" "- PYTHONPATH: $PYTHONPATH"
log "INFO" "- CRAWL4_AI_BASE_DIRECTORY: ${CRAWL4_AI_BASE_DIRECTORY:-Non défini}"

# Validation de l'environnement avant démarrage
if ! validate_environment; then
    log "ERROR" "Échec de la validation de l'environnement. Arrêt du service."
    exit 1
fi

# Activation de l'environnement virtuel
log "INFO" "Activation de l'environnement virtuel..."
source /app/.venv/bin/activate

# Configuration du PYTHONPATH
export PYTHONPATH="/app:$PYTHONPATH"

# Exécution de l'application
log "INFO" "Démarrage du service MCP Crawl4AI RAG..."
exec /app/.venv/bin/uvicorn src.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --timeout-keep-alive "${TIMEOUT}" \
    --log-level "${LOG_LEVEL}" \
    --log-config /app/scripts/logging.ini \
    --reload