"""
Script de validation des variables d'environnement requises.
À exécuter avant le démarrage du service.
"""
import os
import sys
from typing import Dict, List, Optional

# Définition des variables requises et optionnelles
REQUIRED_ENV_VARS = {
    'PORT': 'Port du serveur (ex: 8010)',
    'DATABASE_URL': 'URL de connexion à la base de données PostgreSQL',
    'REDIS_URL': 'URL de connexion à Redis',
    'QDRANT_URL': 'URL de connexion à Qdrant',
    'SUPABASE_URL': 'URL de l\'instance Supabase',
    'SUPABASE_KEY': 'Clé d\'API Supabase',
    'OPENAI_API_KEY': 'Clé d\'API OpenAI',
    'VAULT_ADDR': 'URL de l\'instance Vault',
    'VAULT_TOKEN': 'Token d\'authentification Vault'
}

OPTIONAL_ENV_VARS = {
    'ENVIRONMENT': 'Environnement d\'exécution (défaut: production)',
    'DEBUG': 'Active le mode débogage (défaut: false)',
    'LOG_LEVEL': 'Niveau de journalisation (défaut: info)',
    'CRAWL4_AI_BASE_DIRECTORY': 'Répertoire de base pour crawl4ai (défaut: /app/data)'
}

def check_environment() -> bool:
    """Vérifie que toutes les variables d'environnement requises sont définies."""
    missing_vars = []
    warnings = []
    
    # Vérifier les variables requises
    for var, description in REQUIRED_ENV_VARS.items():
        if var not in os.environ or not os.environ[var]:
            missing_vars.append((var, description))
    
    # Vérifier les variables optionnelles
    for var, description in OPTIONAL_ENV_VARS.items():
        if var not in os.environ or not os.environ[var]:
            default_value = 'production' if var == 'ENVIRONMENT' else \
                         'false' if var == 'DEBUG' else \
                         'info' if var == 'LOG_LEVEL' else \
                         '/app/data' if var == 'CRAWL4_AI_BASE_DIRECTORY' else ''
            warnings.append(f"{var}: {description} (défaut: {default_value})")
    
    # Afficher les résultats
    if missing_vars:
        print("\n[ERREUR] Variables d'environnement requises manquantes :", file=sys.stderr)
        for var, description in missing_vars:
            print(f"  - {var}: {description}", file=sys.stderr)
    
    if warnings:
        print("\n[ATTENTION] Variables d'environnement optionnelles non définies :")
        for warning in warnings:
            print(f"  - {warning}")
    
    # Vérifier les répertoires nécessaires
    required_dirs = [
        os.environ.get('CRAWL4_AI_BASE_DIRECTORY', '/app/data'),
        '/app/logs'
    ]
    
    for dir_path in required_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"[OK] Répertoire {dir_path} créé ou existant")
        except Exception as e:
            print(f"[ERREUR] Impossible de créer le répertoire {dir_path}: {e}", file=sys.stderr)
            return False
    
    return len(missing_vars) == 0

if __name__ == "__main__":
    print("=== Validation de l'environnement ===")
    if not check_environment():
        print("\n[ERREUR] Configuration de l'environnement invalide.", file=sys.stderr)
        sys.exit(1)
    
    print("\n[SUCCÈS] Toutes les validations ont réussi !")
    sys.exit(0)
