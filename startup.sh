#!/bin/bash
set -e

# Afficher les variables d'environnement pour le débogage
echo "=== Environment Variables ==="
echo "HOST: $HOST"
echo "PORT: $PORT"
echo "TRANSPORT: $TRANSPORT"
echo "SUPABASE_URL: $SUPABASE_URL"
echo "SUPABASE_SERVICE_KEY: ${SUPABASE_SERVICE_KEY:0:10}..."  # Afficher uniquement le début de la clé pour des raisons de sécurité
echo "OLAMA_BASE_URL: $OLAMA_BASE_URL"
echo "EMBEDDING_MODEL: $EMBEDDING_MODEL"
echo "============================"

# Vérifier si Supabase est configuré
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo "ERREUR: Les variables d'environnement SUPABASE_URL et SUPABASE_SERVICE_KEY sont requises"
    exit 1
fi

# Démarrer l'application
echo "Starting MCP Crawl4AI server with Supabase..."
cd /app/mcp-crawl4ai-rag
exec python src/crawl4ai_mcp.py
