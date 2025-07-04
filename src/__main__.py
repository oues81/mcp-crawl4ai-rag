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

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importer directement le module principal
from crawl4ai_mcp import main as crawl4ai_main

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


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
        import crawl4ai
        
        logger.info("Toutes les dépendances sont installées.")
    except ImportError as e:
        logger.error(f"Dépendance manquante : {e}")
        logger.error("Veuillez installer les dépendances avec : poetry install")
        sys.exit(1)
    
    # Démarrer le service
    logger.info("Démarrage du service MCP Crawl4AI RAG...")
    
    # Exécuter la fonction principale du module
    await crawl4ai_main()
    
    # Configuration du serveur
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8002"))
    
    logger.info(f"Démarrage du serveur MCP Crawl4AI RAG sur http://{host}:{port}")
    
    try:
        import uvicorn
        
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            reload=os.getenv("ENV") == "development",
            workers=int(os.getenv("WORKERS", "1")),
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    except ImportError:
        logger.error("Impossible d'importer uvicorn. Veuillez l'installer avec : pip install uvicorn[standard]")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Erreur lors du démarrage du serveur : {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
