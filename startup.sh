#!/bin/bash
set -e

# Fonction pour logger les messages avec horodatage
log() {
    local level=$1
    shift
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [$level] $*"
}

# Vérifier les dépendances système requises
check_dependencies() {
    local missing=()
    
    # Vérifier les commandes requises
    for cmd in python3 pip3; do
        if ! command -v $cmd &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        log "ERROR" "Dépendances manquantes: ${missing[*]}"
        exit 1
    fi
}

# Vérifier les variables d'environnement requises
check_environment() {
    local required_vars=("SUPABASE_URL" "SUPABASE_SERVICE_KEY" "VAULT_ADDR")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log "ERROR" "Variables d'environnement requises manquantes: ${missing_vars[*]}"
        exit 1
    fi
}

# Vérifier la connexion à Vault
check_vault_connection() {
    if [ "$VAULT_ENABLED" = "true" ]; then
        log "INFO" "Vérification de la connexion à Vault..."
        
        # Vérifier si le token Vault est défini
        if [ -z "$VAULT_TOKEN" ]; then
            log "WARNING" "VAULT_TOKEN n'est pas défini. Tentative d'authentification avec Kubernetes ou AppRole..."
            # Ici, vous pouvez ajouter une logique d'authentification alternative si nécessaire
        fi
        
        # Tester la connexion à Vault
        if ! curl -s -f "$VAULT_ADDR/v1/sys/health"; then
            log "ERROR" "Impossible de se connecter à Vault à l'adresse: $VAULT_ADDR"
            exit 1
        fi
        
        log "INFO" "Connexion à Vault établie avec succès"
    else
        log "WARNING" "Vault est désactivé. Les secrets seront chargés depuis les variables d'environnement."
    fi
}

# Afficher la configuration (sans les secrets)
log_config() {
    log "INFO" "=== Configuration du service MCP Crawl4AI RAG ==="
    log "INFO" "HOST: $HOST"
    log "INFO" "PORT: $PORT"
    log "INFO" "TRANSPORT: $TRANSPORT"
    log "INFO" "SUPABASE_URL: $SUPABASE_URL"
    log "INFO" "SUPABASE_SERVICE_KEY: ${SUPABASE_SERVICE_KEY:0:10}..."
    log "INFO" "OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-Non défini}"
    log "INFO" "EMBEDDING_MODEL: ${EMBEDDING_MODEL:-Non défini}"
    log "INFO" "VAULT_ENABLED: ${VAULT_ENABLED:-false}"
    log "INFO" "VAULT_ADDR: ${VAULT_ADDR:-Non défini}"
    log "INFO" "CRAWL4_AI_BASE_DIRECTORY: ${CRAWL4_AI_BASE_DIRECTORY:-/app/data}"
    log "INFO" "================================================"
}

# Vérifier les dossiers nécessaires
setup_directories() {
    local dirs=("$CRAWL4_AI_BASE_DIRECTORY" "/app/logs")
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log "INFO" "Création du répertoire: $dir"
            mkdir -p "$dir"
        fi
        
        # Vérifier les permissions
        if [ ! -w "$dir" ]; then
            log "ERROR" "Le répertoire $dir n'est pas accessible en écriture"
            exit 1
        fi
    done
}

# Point d'entrée principal
main() {
    log "INFO" "Démarrage du service MCP Crawl4AI RAG..."
    
    # Vérifications initiales
    check_dependencies
    check_environment
    check_vault_connection
    
    # Afficher la configuration
    log_config
    
    # Configurer les dossiers
    setup_directories
    
    # Démarrer l'application
    cd /app
    
    # Utiliser exec pour permettre à Python de gérer correctement les signaux
    log "INFO" "Lancement de l'application..."
    exec python -m src.crawl4ai_mcp "$@"
}

# Appeler la fonction principale
main "$@"
