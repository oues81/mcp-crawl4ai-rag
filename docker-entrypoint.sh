#!/bin/bash
set -e

# Afficher la configuration
echo "=== Configuration du service MCP Crawl4AI RAG ==="
echo "PORT=${PORT}"
echo "UVICORN_WORKERS=${UVICORN_WORKERS:-1}"
echo "PYTHONPATH=${PYTHONPATH}"
echo "CRAWL4_AI_BASE_DIRECTORY=${CRAWL4_AI_BASE_DIRECTORY}"

# Vérifier les permissions
echo -e "\n=== Vérification des permissions ==="
ls -ld /app /app/logs /app/data /app/.cache

# Vérifier les dépendances
echo -e "\n=== Vérification des dépendances ==="
pip list | grep -E "fastapi|uvicorn|neo4j|crawl4ai|supabase|fastmcp"

# Vérifier le fichier main.py
echo -e "\n=== Vérification du fichier main.py ==="
if [ -f "/app/main.py" ]; then
    echo "Fichier principal trouvé: /app/main.py"
    MAIN_FILE="main"
elif [ -f "/app/src/main.py" ]; then
    echo "Fichier principal trouvé: /app/src/main.py"
    MAIN_FILE="src.main"
else
    echo "ERREUR: Aucun fichier main.py trouvé"
    ls -la /app/
    exit 1
fi

# Démarrer le serveur FastAPI
echo -e "\n=== Démarrage du serveur FastAPI ==="
echo "Module: $MAIN_FILE"
echo "Port: ${PORT}"
echo "Workers: ${UVICORN_WORKERS}"

# Exécuter le serveur avec uvicorn
exec uvicorn \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers ${UVICORN_WORKERS} \
    --log-level info \
    --no-access-log \
    ${MAIN_FILE}:app
