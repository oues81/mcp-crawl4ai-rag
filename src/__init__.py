"""
MCP Crawl4AI RAG - Un service MCP pour le crawling web et le RAG (Retrieval-Augmented Generation).

Ce module fournit une implémentation du protocole MCP (Model Context Protocol) pour le crawling web
et la recherche augmentée par génération (RAG) en utilisant la bibliothèque Crawl4AI.
"""

__version__ = "0.1.0"
__author__ = "Windsurf Cascade"
__email__ = "support@windsurf.ai"

# Configuration du logging
import logging
from pathlib import Path
import os
import tempfile

# Utiliser un répertoire temporaire pour les logs
log_dir = Path(tempfile.gettempdir()) / "mcp_crawl4ai_rag_logs"
os.makedirs(log_dir, exist_ok=True)
log_file = log_dir / "mcp_crawl4ai_rag.log"

# Configuration du logging de base
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode='a'),
    ],
)

# S'assurer que les logs sont accessibles
os.chmod(log_file, 0o666)

# Désactiver les logs trop verbeux par défaut
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
