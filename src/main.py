"""
Point d'entrée principal du service MCP Crawl4AI RAG
"""
import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configuration du Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import de l'application depuis crawl4ai_mcp
from src.crawl4ai_mcp import app as crawl4ai_app

# Création de l'application FastAPI
app = FastAPI(
    title="MCP Crawl4AI RAG Service",
    description="Service d'API pour le crawling web et RAG avec MCP",
    version="0.1.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter l'application crawl4ai sous le préfixe /api
app.mount("/api", crawl4ai_app)

# Point de terminaison de santé
@app.get("/health")
async def health_check():
    """Endpoint de vérification de la santé du service."""
    return {"status": "healthy"}

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
            "api_docs": "/api/docs",
            "openapi_schema": "/api/openapi.json"
        }
    }
@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application."""
    # Configuration du répertoire de base pour crawl4ai
    os.makedirs("/app/data", exist_ok=True)
    os.environ["CRAWL4_AI_BASE_DIRECTORY"] = "/app/data"
    print(f"Répertoire de base pour crawl4ai configuré sur: {os.environ['CRAWL4_AI_BASE_DIRECTORY']}")

if __name__ == "__main__":
    # Configuration du serveur
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8002"))
    
    # Affichage des informations de démarrage
    print(f"Démarrage du service MCP Crawl4AI RAG sur http://{host}:{port}")
    print(f"Documentation de l'API disponible sur http://{host}:{port}/docs")
    
    # Démarrage du serveur
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level="info"
    )
