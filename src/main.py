"""
Point d'entrée principal du service MCP Crawl4AI RAG
"""
import os
import sys
import asyncio
import traceback

# Configuration du Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import depuis le package
from src.crawl4ai_mcp import main as crawl4ai_main

if __name__ == "__main__":
    # Configuration de l'environnement
    os.environ.setdefault("CRAWL4_AI_BASE_DIRECTORY", "/app/data")
    os.makedirs(os.environ["CRAWL4_AI_BASE_DIRECTORY"], exist_ok=True)
    
    # Démarrer le serveur
    try:
        asyncio.run(crawl4ai_main())
    except Exception as e:
        print(f"Erreur: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
