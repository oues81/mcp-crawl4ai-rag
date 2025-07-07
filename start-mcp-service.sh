#!/bin/bash
set -e

# Fonction pour logger avec horodatage
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Afficher les informations de version et de configuration
log "=== Démarrage du service MCP Crawl4AI RAG ==="
log "Répertoire de travail: $(pwd)"
log "Utilisateur: $(whoami)"
log "Python: $(python --version 2>&1)"
log "Uvicorn: $(python -c 'import uvicorn; print(uvicorn.__version__)' 2>/dev/null || echo 'Non installé')"

# Vérification des variables d'environnement requises
log "Vérification des variables d'environnement requises..."
REQUIRED_VARS=("SUPABASE_URL" "SUPABASE_SERVICE_KEY" "OPENAI_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    log "ERREUR: Les variables d'environnement suivantes sont requises mais non définies:"
    for var in "${MISSING_VARS[@]}"; do
        log "- $var"
    done
    exit 1
fi

# Afficher la configuration RAG activée
log "=== Configuration RAG activée ==="
[ "$USE_CONTEXTUAL_EMBEDDINGS" = "true" ] && log "- USE_CONTEXTUAL_EMBEDDINGS: true" || log "- USE_CONTEXTUAL_EMBEDDINGS: false"
[ "$USE_HYBRID_SEARCH" = "true" ] && log "- USE_HYBRID_SEARCH: true" || log "- USE_HYBRID_SEARCH: false"
[ "$USE_AGENTIC_RAG" = "true" ] && log "- USE_AGENTIC_RAG: true" || log "- USE_AGENTIC_RAG: false"
[ "$USE_RERANKING" = "true" ] && log "- USE_RERANKING: true" || log "- USE_RERANKING: false"
[ "$USE_KNOWLEDGE_GRAPH" = "true" ] && log "- USE_KNOWLEDGE_GRAPH: true" || log "- USE_KNOWLEDGE_GRAPH: false"

# Vérifier l'installation des dépendances
log "Vérification des dépendances principales..."
REQUIRED_PACKAGES=("uvicorn" "fastapi" "crawl4ai" "sentence-transformers" "supabase")

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! python -c "import $pkg" 2>/dev/null; then
        log "ATTENTION: Le paquet $pkg n'est pas installé correctement"
    fi
done

# Démarrer le service avec uvicorn directement
log "=== Démarrage du service avec uvicorn ==="
log "HOST: ${HOST:-0.0.0.0}"
log "PORT: ${PORT:-8002}"
log "WORKERS: ${WORKERS:-1}"
log "LOG_LEVEL: ${LOG_LEVEL:-info}"

# S'assurer que le répertoire de travail est correct
cd /app/src

# Vérifier que le fichier principal existe
if [ ! -f "crawl4ai_mcp.py" ]; then
    log "ERREUR: Le fichier crawl4ai_mcp.py est introuvable dans /app/src"
    log "Contenu du répertoire /app/src:"
    ls -la /app/src
    exit 1
fi

# Exécuter uvicorn avec les paramètres appropriés
exec uvicorn \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8002}" \
    --workers "${WORKERS:-1}" \
    --proxy-headers \
    --forwarded-allow-ips "*" \
    --log-level "${LOG_LEVEL:-info}" \
    --no-access-log \
    crawl4ai_mcp:app

# En cas d'échec, afficher un message d'erreur
echo "ERREUR: Le service MCP Crawl4AI RAG a échoué à démarrer"
exit 1
