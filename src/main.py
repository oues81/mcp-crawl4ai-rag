"""
Point d'entrée principal du service MCP Crawl4AI RAG
"""
import os
import sys
import uvicorn
from fastapi import FastAPI

# Configuration du Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Vérification du répertoire courant
print(f"Répertoire de travail: {os.getcwd()}")
print(f"Contenu du répertoire: {os.listdir('.')}")

# Import de l'application depuis crawl4ai_mcp
from crawl4ai_mcp import mcp

# Création d'une nouvelle instance FastAPI
app = mcp.app

# Point d'entrée principal
@app.get("/")
async def root():
    """Point d'entrée principal avec des informations sur le service."""
    return {
        "service": "MCP Crawl4AI RAG Service",
        "status": "en cours d'exécution",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

# Point de terminaison de santé
@app.get("/health")
async def health_check():
    """Endpoint de vérification de la santé du service."""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application."""
    # Configuration du répertoire de base pour crawl4ai
    os.makedirs("/app/data", exist_ok=True)
    os.makedirs("/app/logs", exist_ok=True)
    print("Démarrage du service MCP Crawl4AI RAG...")

if __name__ == "__main__":
    # Configuration du serveur
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8051"))
    
    # Affichage des informations de démarrage
    print(f"Démarrage du service MCP Crawl4AI RAG sur http://{host}:{port}")
    print(f"Documentation de l'API disponible sur http://{host}:{port}/docs")
    
    # Démarrer le serveur Uvicorn
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level="info"
    )
