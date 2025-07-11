"""
Module principal de l'application MCP Crawl4AI RAG.

Ce module définit l'application FastAPI et les routes principales du service.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Configuration du logging
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="MCP Crawl4AI RAG Service",
    description="Service MCP pour le crawling web et le RAG (Retrieval-Augmented Generation)",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des répertoires statiques
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Gestionnaire d'erreurs global pour l'application."""
    logger.exception(f"Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Une erreur interne est survenue: {str(exc)}"},
    )


# Route de santé
@app.get("/health", tags=["santé"])
async def health_check() -> Dict[str, str]:
    """Vérifie l'état de santé du service."""
    return {"status": "ok", "service": "mcp-crawl4ai-rag"}


# Route d'accueil
@app.get("/", tags=["racine"])
async def root() -> Dict[str, str]:
    """Route racine de l'API."""
    return {
        "message": "Bienvenue sur le service MCP Crawl4AI RAG",
        "documentation": "/docs",
        "santé": "/health",
    }


# Fonction de démarrage de l'application
@app.on_event("startup")
async def startup_event() -> None:
    """Actions à effectuer au démarrage de l'application."""
    logger.info("Démarrage de l'application MCP Crawl4AI RAG...")
    
    # Vérification des variables d'environnement requises
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(
            f"Variables d'environnement manquantes : {', '.join(missing_vars)}. "
            "Certaines fonctionnalités pourraient ne pas fonctionner correctement."
        )
    
    # Initialisation des composants principaux
    try:
        # Initialisation des composants ici
        logger.info("Initialisation des composants principaux...")
        
        # Exemple d'initialisation (à adapter selon les besoins)
        # from .services.embedding import init_embedding_model
        # await init_embedding_model()
        
        logger.info("Initialisation terminée avec succès.")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de l'application : {e}")
        raise


# Fonction d'arrêt de l'application
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Actions à effectuer à l'arrêt de l'application."""
    logger.info("Arrêt de l'application MCP Crawl4AI RAG...")
    
    try:
        # Nettoyage des ressources ici
        logger.info("Nettoyage des ressources...")
        
        # Exemple de nettoyage (à adapter selon les besoins)
        # from .services.database import close_database
        # await close_database()
        
        logger.info("Nettoyage terminé avec succès.")
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des ressources : {e}")


# Import des routeurs (à décommenter et adapter selon les besoins)
# from .api import router as api_router
# app.include_router(api_router, prefix="/api/v1")


# Fonction utilitaire pour exécuter l'application en mode développement
def run_dev() -> None:
    """Exécute l'application en mode développement avec rechargement automatique."""
    import uvicorn
    
    uvicorn.run(
        "mcp_crawl4ai_rag.main:app",
        host="0.0.0.0",
        port=8051,
        reload=True,
        reload_dirs=["src"],
        log_level="info",
    )


# Point d'entrée pour l'exécution directe du module
if __name__ == "__main__":
    run_dev()
