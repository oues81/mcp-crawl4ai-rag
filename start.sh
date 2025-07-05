#!/bin/bash

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "Erreur: Docker n'est pas installé. Veuillez installer Docker et réessayer."
    exit 1
fi

# Vérifier si docker-compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "Erreur: docker-compose n'est pas installé. Veuillez installer docker-compose et réessayer."
    exit 1
fi

# Vérifier si le fichier .env existe
if [ ! -f .env ]; then
    echo "Création du fichier .env à partir de .env.example..."
    cp .env.example .env
    echo "Veuvez configurer le fichier .env avec vos clés API et paramètres, puis relancez le script."
    exit 1
fi

# Vérifier les variables d'environnement requises
if ! grep -q "^OPENAI_API_KEY=" .env || ! grep -q "^SUPABASE_URL=" .env || ! grep -q "^SUPABASE_SERVICE_KEY=" .env; then
    echo "Erreur: Veuillez configurer les variables OPENAI_API_KEY, SUPABASE_URL et SUPABASE_SERVICE_KEY dans le fichier .env"
    exit 1
fi

echo "Arrêt des conteneurs existants..."
docker-compose down

echo "Construction et démarrage des services..."
docker-compose up --build -d

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Service MCP Crawl4AI RAG démarré avec succès!"
    echo "URL: http://localhost:8002"
    echo ""
    echo "Pour afficher les logs: docker-compose logs -f"
    echo "Pour arrêter: docker-compose down"
    echo "========================================"
    echo ""
    
    # Afficher les logs
    docker-compose logs -f
else
    echo ""
    echo "Erreur lors du démarrage du service. Vérifiez les logs ci-dessus pour plus d'informations."
    exit 1
fi
