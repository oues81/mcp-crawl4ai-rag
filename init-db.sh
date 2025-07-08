#!/bin/bash
set -e

echo "En attente de la base de données..."
until pg_isready -h db -p 5432 -U postgres; do
  echo "En attente de la base de données..."
  sleep 2
done

echo "Base de données disponible, initialisation..."

# Exécution du script SQL d'initialisation
echo "Exécution du script SQL d'initialisation..."
PGPASSWORD=postgres psql -h db -U postgres -d sti_map_generator -f /app/crawled_pages.sql
echo "Script SQL exécuté avec succès"

# Démarrer le serveur MCP
echo "Démarrage du serveur MCP Crawl4AI RAG..."
cd /app
python -m src.crawl4ai_mcp
