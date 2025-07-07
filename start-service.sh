#!/bin/bash
set -e

# Vérifier si le fichier .env.local existe
if [ ! -f ".env.local" ]; then
    echo "Création du fichier .env.local à partir de .env.example..."
    cp .env.example .env.local
    echo "Veuillez configurer les variables d'environnement dans le fichier .env.local"
    exit 1
fi

# Charger les variables d'environnement
export $(grep -v '^#' .env.local | xargs)

# Vérifier les variables d'environnement requises
required_vars=("SUPABASE_URL" "SUPABASE_SERVICE_KEY" "SUPABASE_ANON_KEY" "SUPABASE_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Erreur: La variable $var n'est pas définie dans .env.local"
        exit 1
    fi
done

# Créer les répertoires nécessaires
mkdir -p data logs .cache

# Démarrer le service avec Docker Compose
echo "Démarrage du service MCP Crawl4AI RAG..."
docker-compose up --build -d

echo "\nLe service est en cours de démarrage..."
echo "Vérification de l'état du service..."

# Attendre que le service soit prêt
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8002/health >/dev/null; then
        echo "\n✅ Le service est opérationnel!"
        echo "- URL du service: http://localhost:8002"
        echo "- Endpoint de santé: http://localhost:8002/health"
        echo "- Endpoint SSE: http://localhost:8002/sse"
        exit 0
    fi
    
    echo "En attente du démarrage du service (tentative $attempt/$max_attempts)..."
    sleep 2
    ((attempt++))
done

echo "\n❌ Le service n'a pas démarré correctement après $max_attempts tentatives."
echo "Consultez les logs avec la commande: docker-compose logs -f"
exit 1
