import os
import sys
from pathlib import Path

# --- Configuration initiale du chemin ---
# Ajoute la racine du projet au sys.path pour permettre les imports relatifs
# Le fichier actuel est dans src/mcp_crawl4ai_rag, donc on remonte de deux niveaux
project_root_path = Path(__file__).resolve().parents[1]
if str(project_root_path) not in sys.path:
    sys.path.insert(0, str(project_root_path))

# --- Point d'entrée de l'application ---
# Importer l'application FastAPI (`app`) depuis le module principal qui contient la logique MCP.
# C'est cet `app` qui sera servi par Uvicorn.
try:
    import sys
    from pathlib import Path
    import uvicorn
    from fastapi import FastAPI, APIRouter
    from fastapi.middleware.cors import CORSMiddleware
    from datetime import datetime
    from fastapi.responses import JSONResponse
    import importlib.util
    import logging
    
    # Configuration du logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
    logger = logging.getLogger("mcp_crawl4ai_rag")
    
    # Importer les modules MCP
    # Le fichier est dans src/mcp_crawl4ai_rag, on cherche crawl4ai_mcp.py dans src/
    parent_dir = Path(__file__).resolve().parents[1]
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Le chemin correct est donc dans le parent (src)
    crawl4ai_mcp_path = parent_dir / "crawl4ai_mcp.py"
    if not crawl4ai_mcp_path.exists():
        logger.error(f"Le fichier crawl4ai_mcp.py n'existe pas à l'emplacement: {crawl4ai_mcp_path}")
        raise FileNotFoundError(f"Le fichier crawl4ai_mcp.py n'existe pas à l'emplacement: {crawl4ai_mcp_path}")
    
    # Importer le module crawl4ai_mcp
    spec = importlib.util.spec_from_file_location("crawl4ai_mcp", crawl4ai_mcp_path)
    crawl4ai_mcp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(crawl4ai_mcp)
    
    # Vérifier si l'application FastAPI est déjà définie dans crawl4ai_mcp
    if hasattr(crawl4ai_mcp, 'app'):
        # Utiliser l'application existante
        app = crawl4ai_mcp.app
        logger.info("Utilisation de l'application FastAPI définie dans crawl4ai_mcp")
    else:
        # Créer une nouvelle application FastAPI
        app = FastAPI(
            title="MCP Crawl4AI RAG Service",
            description="Service MCP pour le crawling web et RAG (Retrieval-Augmented Generation)",
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
        
        logger.info("Nouvelle application FastAPI créée")
    
    # Vérifier si l'objet mcp est défini et a un routeur
    if hasattr(crawl4ai_mcp, 'mcp') and crawl4ai_mcp.mcp is not None:
        if hasattr(crawl4ai_mcp.mcp, 'router'):
            # Vérifier si le routeur n'est pas déjà inclus
            router_already_included = False
            for route in app.routes:
                if getattr(route, "prefix", "") == "/mcp":
                    router_already_included = True
                    break
            
            if not router_already_included:
                app.include_router(crawl4ai_mcp.mcp.router, prefix="/mcp")
                logger.info("Le routeur MCP a été ajouté à l'application FastAPI")
            else:
                logger.info("Le routeur MCP est déjà inclus dans l'application FastAPI")
        else:
            logger.warning("L'objet mcp existe mais n'a pas d'attribut router")
    else:
        logger.warning("L'objet mcp n'est pas défini dans crawl4ai_mcp ou est None")
        
    logger.info("Configuration de l'application FastAPI terminée")
    
    # Ajouter des routes de base pour la santé et l'information
    @app.get("/")
    async def root():
        return {
            "service": "MCP Crawl4AI RAG Service",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "mcp": "/mcp/",
                "docs": "/docs"
            }
        }
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "mcp-crawl4ai-rag",
            "version": "0.1.0",
            "timestamp": datetime.utcnow().isoformat()
        }
        
except ImportError as e:
    print(f"\n[ERREUR] Impossible d'importer l'application depuis 'crawl4ai_mcp.py': {e}")
    print("Assurez-vous que le fichier 'crawl4ai_mcp.py' existe et ne contient pas d'erreurs de syntaxe.")
    # Créer une fausse application pour éviter que le serveur ne plante complètement
    from fastapi import FastAPI
    app = FastAPI()
    
    # Définir le message d'erreur comme une variable locale
    error_msg = str(e)
    
    @app.get("/error")
    def read_error():
        return {"error": "Failed to load MCP application", "details": error_msg}
    
    @app.get("/")
    def root():
        return {"error": "Failed to load MCP application", "details": error_msg}
        
    @app.get("/health")
    def health_check():
        return {"status": "error", "error": error_msg}

# Ce fichier sert maintenant uniquement de point d'entrée pour Uvicorn.
# Toute la logique, y compris les routes, les outils et la configuration SSE,
# est gérée dans `crawl4ai_mcp.py`.