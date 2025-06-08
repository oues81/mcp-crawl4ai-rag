#!/bin/bash
set -e

# Attendre que PostgreSQL soit prêt
echo "Waiting for PostgreSQL to become available..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "Creating extensions and setting up database..."

# Créer les extensions nécessaires
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    -- Activer les extensions nécessaires
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    -- Vérifier que l'extension pgvector est bien installée
    SELECT * FROM pg_extension WHERE extname = 'vector';
    
    -- Vous pouvez ajouter d'autres configurations de base de données ici si nécessaire
EOSQL

# Exécuter les scripts SQL supplémentaires s'ils existent
if [ -f "/app/crawled_pages.sql" ]; then
    echo "Running crawled_pages.sql..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /app/crawled_pages.sql
fi

echo "Database initialization completed successfully!"
