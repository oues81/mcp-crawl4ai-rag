"""
Point d'entrée principal pour l'exécution du package en tant que module.

Exemple d'utilisation :
    python -m mcp_crawl4ai_rag
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_crawl4ai_rag import __version__
from mcp_crawl4ai_rag.main import app

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
