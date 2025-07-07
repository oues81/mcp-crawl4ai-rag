"""
Point d'entrée principal pour l'exécution du service MCP Crawl4AI RAG.

Exemple d'utilisation :
    python -m crawl4ai_mcp
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Version de l'application
__version__ = "0.1.0"

def print_banner():
    """Affiche la bannière d'information au démarrage."""
    banner = f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   MCP Crawl4AI RAG Service - v{__version__:<15}          ║
    ║   Python {'.'.join(map(str, sys.version_info[:3])):<10}  ║
    ║   PID: {os.getpid():<8}                                  ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    """Fonction principale d'exécution du service."""
    print_banner()
    
    # Vérifier les dépendances
    logger.info("Vérification des dépendances Python...")
    try:
        # Vérifier les dépendances critiques
        import fastapi
        import uvicorn
        
        logger.info("Toutes les dépendances sont installées.")
    except ImportError as e:
        logger.error(f"Dépendance manquante : {e}")
        logger.error("Veuillez installer les dépendances avec : pip install -e .")
        sys.exit(1)
    
    # Démarrer le service
    logger.info("Démarrage du service MCP Crawl4AI RAG...")
    
    try:
        # Importer le module principal
        from crawl4ai_mcp import main as crawl4ai_main
        
        # Exécuter la fonction principale du module
        await crawl4ai_main()
        
    except ImportError as e:
        logger.error(f"Impossible d'importer le module principal: {e}")
        logger.error("Assurez-vous que le module est correctement installé.")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Erreur lors du démarrage du service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
