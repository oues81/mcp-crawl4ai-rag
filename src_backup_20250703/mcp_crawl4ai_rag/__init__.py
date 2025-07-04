"""
MCP Crawl4AI RAG - Un service MCP pour le crawling web et le RAG (Retrieval-Augmented Generation).

Ce module fournit une implémentation du protocole MCP (Model Context Protocol) pour le crawling web
et la recherche augmentée par génération (RAG) en utilisant la bibliothèque Crawl4AI.

Exemple d'utilisation :
    from mcp_crawl4ai_rag import crawl_website, search_rag
    
    # Crawler un site web
    result = await crawl_website("https://example.com")
    
    # Effectuer une recherche RAG
    results = await search_rag("Qu'est-ce que le RAG ?")
"""

__version__ = "0.1.0"
__author__ = "Windsurf Cascade"
__email__ = "support@windsurf.ai"

# Import des éléments principaux du package
from .main import app  # noqa: F401

# Configuration du logging
import logging
from pathlib import Path

# Créer le répertoire de logs s'il n'existe pas
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configuration du logging de base
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "mcp_crawl4ai_rag.log"),
    ],
)

# Désactiver les logs trop verbeux par défaut
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
