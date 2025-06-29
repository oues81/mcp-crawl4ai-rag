#!/bin/bash
set -e

# Fonction pour logger les messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Vérifier que les commandes nécessaires sont disponibles
for cmd in curl pg_isready; do
    if ! command -v $cmd &> /dev/null; then
        log "ERREUR: La commande $cmd est requise mais n'est pas installée"
        exit 1
    fi
done

# Vérifier si les variables d'environnement requises sont définies
log "Vérification des variables d'environnement requises..."

REQUIRED_VARS=(
    "DATABASE_URL"
    "REDIS_URL"
    "QDRANT_URL"
    "VAULT_URL"
    "SUPABASE_URL"
    "SUPABASE_KEY"
    "OPENAI_API_KEY"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
        log "ATTENTION: La variable $var n'est pas définie"
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    log "ERREUR: Les variables d'environnement suivantes sont requises mais non définies :"
    for var in "${MISSING_VARS[@]}"; do
        log "  - $var"
    done
    exit 1
fi

log "Toutes les variables d'environnement requises sont définies"

# Fonction pour vérifier si un service est prêt
wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_retries=30
    local retry_count=0
    
    log "Vérification de la disponibilité de $service_name sur $host:$port..."
    
    while [ $retry_count -lt $max_retries ]; do
        if nc -z -w 5 "$host" "$port" 2>/dev/null; then
            log "$service_name est disponible sur $host:$port"
            return 0
        fi
        
        retry_count=$((retry_count + 1))
        log "En attente de $service_name ($retry_count/$max_retries)..."
        sleep 2
    done
    
    log "ERREUR: Impossible de se connecter à $service_name après $max_retries tentatives"
    return 1
}

# Attendre que les services dépendants soient prêts
log "Vérification de la disponibilité des services dépendants..."

# Fonction pour extraire l'hôte et le port d'une URL
extract_host_port() {
    local url=$1
    local default_port=$2
    
    # Extraire les informations d'authentification, l'hôte, le port et le chemin
    # Format attendu: postgresql://user:password@host:port/database
    
    # Supprimer le préfixe postgresql://
    local no_proto="${url#*//}"
    
    # Extraire les informations d'authentification si elles existent
    local auth_part="${no_proto%%@*}"
    local host_part="${no_proto#*@}"
    
    # Si pas de @, alors pas d'authentification
    if [ "$host_part" = "$no_proto" ]; then
        host_part="$no_proto"
    fi
    
    # Extraire le host et le port
    local host_port=$(echo "$host_part" | cut -d'/' -f1)
    
    # Séparer l'hôte et le port
    local host=$(echo "$host_port" | cut -d':' -f1)
    local port=$(echo "$host_port" | cut -s -d':' -f2)
    
    # Utiliser le port par défaut si non spécifié
    if [ -z "$port" ]; then
        port=$default_port
    fi
    
    echo "$host $port"
}

# Vérifier PostgreSQL - Désactivé temporairement pour le débogage
log "ATTENTION: Vérification de la base de données désactivée pour le débogage"
read DB_HOST DB_PORT < <(extract_host_port "$DATABASE_URL" 5432)
log "Configuration de la base de données - Hôte: $DB_HOST, Port: $DB_PORT"

# Vérification manuelle de la connexion
log "Test de connexion à la base de données avec psql..."
if PGPASSWORD=postgres psql -h "$DB_HOST" -U postgres -d sti_map_generator -c 'SELECT 1;' &>/dev/null; then
    log "Connexion à PostgreSQL réussie avec psql"
else
    log "ERREUR: Échec de la connexion à PostgreSQL avec psql"
    log "Détails de la commande: PGPASSWORD=postgres psql -h $DB_HOST -U postgres -d sti_map_generator -c 'SELECT 1;'"
    # Ne pas quitter pour permettre le débogage
    # exit 1
fi

# Vérifier Redis
read REDIS_HOST REDIS_PORT < <(extract_host_port "$REDIS_URL" 6379)
if ! wait_for_service "Redis" "$REDIS_HOST" "$REDIS_PORT"; then
    log "ERREUR: Impossible de se connecter à Redis sur $REDIS_HOST:$REDIS_PORT"
    exit 1
fi

# Vérifier Qdrant
read QDRANT_HOST QDRANT_PORT < <(extract_host_port "$QDRANT_URL" 6333)
if ! wait_for_service "Qdrant" "$QDRANT_HOST" "$QDRANT_PORT"; then
    log "ERREUR: Impossible de se connecter à Qdrant sur $QDRANT_HOST:$QDRANT_PORT"
    exit 1
fi

# Vérifier Vault
read VAULT_HOST VAULT_PORT < <(extract_host_port "$VAULT_URL" 8200)
if ! wait_for_service "Vault" "$VAULT_HOST" "$VAULT_PORT"; then
    log "ERREUR: Impossible de se connecter à Vault sur $VAULT_HOST:$VAULT_PORT"
    exit 1
fi

# Vérifier que Vault est initialisé
log "Vérification de l'initialisation de Vault..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RESPONSE=$(curl -s -w "\n%{http_code}" "$VAULT_URL/v1/sys/health" 2>/dev/null)
    STATUS_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "429" ]; then
        log "Vault est initialisé et fonctionnel"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log "En attente de l'initialisation de Vault ($RETRY_COUNT/$MAX_RETRIES)..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log "ERREUR: Vault n'est pas initialisé après $MAX_RETRIES tentatives"
    exit 1
fi

# Fonction pour nettoyer les ressources lors de l'arrêt
cleanup() {
    log "Nettoyage avant l'arrêt..."
    # Ajoutez ici les commandes de nettoyage si nécessaire
    exit 0
}

# Capturer les signaux d'arrêt
trap cleanup SIGINT SIGTERM

# Démarrer le service
log "Démarrage du service MCP-Crawl4AI-RAG..."

# Exécuter les migrations si nécessaire
if [ "$RUN_MIGRATIONS" = "true" ]; then
    log "Exécution des migrations de base de données..."
    if ! alembic upgrade head; then
        log "ERREUR: Échec de l'exécution des migrations"
        exit 1
    fi
    log "Migrations exécutées avec succès"
fi

# Vérifier que le répertoire source existe
if [ ! -d "/app/src" ]; then
    log "ERREUR: Le répertoire /app/src est introuvable"
    ls -la /app
    exit 1
fi

# Vérifier que le fichier main.py existe
if [ ! -f "/app/main.py" ]; then
    log "ERREUR: Le fichier /app/main.py est introuvable"
    ls -la /app
    exit 1
fi

# Afficher les informations de version
log "=== Informations de version ==="
python --version
pip list | grep -E "fastapi|uvicorn|sqlalchemy|alembic"
log "============================="

# Démarrer l'application
log "Démarrage de l'application sur le port $PORT..."
log "Contenu du répertoire /app: $(ls -la /app)"

# Exporter PYTHONPATH pour inclure /app
export PYTHONPATH="/app:$PYTHONPATH"

set -x
# Lancer l'application avec le bon nom de module
if [ -f "/app/main.py" ]; then
    log "Fichier main.py trouvé dans /app/"
    cd /app
    exec uvicorn main:app --host 0.0.0.0 --port $PORT --reload
else
    log "ERREUR: Impossible de trouver le fichier main.py dans /app/"
    exit 1
fi
