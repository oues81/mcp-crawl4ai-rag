"""
MCP Crawl4AI RAG - Un service MCP pour le crawling web et le RAG (Retrieval-Augmented Generation).

Ce module fournit une implémentation du protocole MCP (Model Context Protocol) pour le crawling web
et la recherche augmentée par génération (RAG) en utilisant la bibliothèque Crawl4AI.
"""

__version__ = "0.1.0"
__author__ = "Windsurf Cascade"
__email__ = "support@windsurf.ai"

# Import de l'application FastAPI
from .main import app  # noqa: F401

# Configuration du logging
import logging
from pathlib import Path

# Créer le répertoire de logs s'il n'existe pas
log_dir = Path("/app/logs")
log_dir.mkdir(parents=True, exist_ok=True)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "mcp_crawl4ai_rag.log")
    ]
)

logger = logging.getLogger(__name__)
logger.info("MCP Crawl4AI RAG service initialisé")
