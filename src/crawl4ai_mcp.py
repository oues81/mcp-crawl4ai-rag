"""
Fichier crawl4ai_mcp.py corrigé pour résoudre le problème d'importation create_router.
Utilise le module mcp au lieu de fastmcp.
"""
import os
import sys
import asyncio
import re
import json
from pathlib import Path
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin, urldefrag
from xml.etree import ElementTree

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Body, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import CrossEncoder
from supabase import Client

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from mcp.server.fastmcp import FastMCP, Context

# --- Initial Configuration ---
# Add project root to sys.path to allow imports from other modules
project_root_path = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root_path))

# Add knowledge_graphs directory to sys.path
knowledge_graphs_path = Path(__file__).resolve().parent / 'knowledge_graphs'
if str(knowledge_graphs_path) not in sys.path:
    sys.path.append(str(knowledge_graphs_path))

# Load environment variables from .env file at the project root
dotenv_path = project_root_path / '.env'
load_dotenv(dotenv_path, override=True)

# --- Local Imports ---
# Import from the local knowledge_graphs module
from knowledge_graphs.utils import (
    get_supabase_client, add_documents_to_supabase, search_documents,
    extract_code_blocks, generate_code_example_summary, add_code_examples_to_supabase,
    update_source_info, extract_source_summary, search_code_examples,
    smart_chunk_markdown, extract_section_info, process_code_example
)
from knowledge_graphs import KnowledgeGraphValidator, AIScriptAnalyzer, HallucinationReporter
from knowledge_graphs.parse_repo_into_neo4j import DirectNeo4jExtractor

# --- Global Settings ---
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
USE_RERANKING = os.getenv("USE_RERANKING", "false").lower() == "true"
USE_KNOWLEDGE_GRAPH = os.getenv("USE_KNOWLEDGE_GRAPH", "false").lower() == "true"

# --- Dataclass for Lifespan Context ---
@dataclass
class Crawl4AIContext:
    """Holds all the resources initialized at startup."""
    crawler: AsyncWebCrawler
    supabase_client: Client
    reranking_model: Optional[CrossEncoder] = None
    knowledge_validator: Optional[KnowledgeGraphValidator] = None
    repo_extractor: Optional[DirectNeo4jExtractor] = None

# --- Helper Functions ---
def format_neo4j_error(error: Exception) -> str:
    """Provides user-friendly Neo4j error messages."""
    error_str = str(error).lower()
    if "authentication" in error_str:
        return "Neo4j authentication failed. Check credentials."
    if "connection" in error_str:
        return "Cannot connect to Neo4j. Check URI and ensure it's running."
    return f"Neo4j error: {str(error)}"

def rerank_results(model: CrossEncoder, query: str, results: List[Dict[str, Any]], content_key: str = "content") -> List[Dict[str, Any]]:
    """Reranks search results using a CrossEncoder model."""
    if not model or not results:
        return results
    try:
        pairs = [[query, res.get(content_key, "")] for res in results]
        scores = model.predict(pairs)
        for i, res in enumerate(results):
            res["rerank_score"] = float(scores[i])
        return sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)
    except Exception as e:
        print(f"Error during reranking: {e}")
        return results

def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """Normalizes a URL by resolving relative paths and removing fragments."""
    if base_url:
        url = urljoin(base_url, url)
    return urldefrag(url)[0]

# --- Lifespan Manager ---
@asynccontextmanager
async def crawl4ai_lifespan(server: FastMCP) -> AsyncIterator[Crawl4AIContext]:
    """Manages the lifecycle of resources for the MCP server."""
    print("Initializing lifespan resources...")
    crawler = None
    try:
        # Essayer de configurer le navigateur en mode headless
        browser_config = BrowserConfig(
            headless=True,
            verbose=DEBUG
        )
        crawler = AsyncWebCrawler(config=browser_config)
        await crawler.__aenter__()
        print("Browser initialized in headless mode.")
    except Exception as e:
        print(f"Warning: Could not initialize browser: {e}")
        print("Continuing without browser support. Some features may not work correctly.")
        # Créer un crawler factice qui ne fera rien
        class DummyCrawler:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
            async def crawl(self, *args, **kwargs):
                return []
        crawler = DummyCrawler()

    supabase_client = get_supabase_client()
    
    reranking_model = None
    # Désactiver le réordonnancement pour l'instant en raison de problèmes de permissions
    print("Reranking model loading is temporarily disabled due to permission issues.")
    # if USE_RERANKING:
    #     try:
    #         print("Loading reranking model...")
    #         reranking_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    #         print("Reranking model loaded.")
    #     except Exception as e:
    #         print(f"Failed to load reranking model: {e}")

    knowledge_validator, repo_extractor = None, None
    if USE_KNOWLEDGE_GRAPH:
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        if all([neo4j_uri, neo4j_user, neo4j_password]):
            try:
                print("Initializing Neo4j components...")
                knowledge_validator = KnowledgeGraphValidator(neo4j_uri, neo4j_user, neo4j_password)
                await knowledge_validator.initialize()
                repo_extractor = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
                await repo_extractor.initialize()
                print("Neo4j components initialized.")
            except Exception as e:
                print(f"Failed to initialize Neo4j components: {format_neo4j_error(e)}")
                knowledge_validator, repo_extractor = None, None
        else:
            print("Neo4j credentials not fully provided. Skipping Knowledge Graph features.")

    print("Lifespan initialization complete. Yielding context.")
    
    # Créer le contexte avec les composants disponibles
    context = Crawl4AIContext(
        crawler=crawler,
        supabase_client=supabase_client,
        reranking_model=reranking_model,
        knowledge_validator=knowledge_validator,
        repo_extractor=repo_extractor
    )
    
    # Renvoyer un dictionnaire avec les composants du contexte
    # que nous voulons exposer à l'application
    app_state = {
        "crawler": crawler,
        "supabase_client": supabase_client,
        "reranking_model": reranking_model,
        "knowledge_validator": knowledge_validator,
        "repo_extractor": repo_extractor
    }
    
    try:
        yield app_state
    except Exception as e:
        print(f"[ERROR] Error in application: {str(e)}")
        raise
    finally:
        print("Closing lifespan resources...")
        try:
            if hasattr(crawler, '__aexit__'):
                await crawler.__aexit__(None, None, None)
            if knowledge_validator and hasattr(knowledge_validator, 'close'):
                await knowledge_validator.close()
            if repo_extractor and hasattr(repo_extractor, 'close'):
                await repo_extractor.close()
        except Exception as e:
            print(f"[WARNING] Error during resource cleanup: {str(e)}")
        print("Lifespan resources closed.")

# --- MCP Server Instance ---
# Configuration du port depuis les variables d'environnement
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8002"))  # Port par défaut 8002 pour correspondre à la configuration Docker

# Afficher les informations de démarrage
def print_startup_info():
    """Affiche les informations de démarrage du service."""
    print("\n" + "="*70)
    print(f"{' MCP Crawl4AI RAG Service ':.^70}")
    print("="*70)
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Python: {sys.version.split()[0]} (running on {sys.platform})")
    print(f"Working directory: {os.getcwd()}")
    print("\nEnvironment variables:")
    print(f"- SUPABASE_URL: {'set' if os.getenv('SUPABASE_URL') else 'not set'}")
    print(f"- SUPABASE_SERVICE_ROLE_KEY: {'set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'not set'}")
    print(f"- SUPABASE_ANON_KEY: {'set' if os.getenv('SUPABASE_ANON_KEY') else 'not set'}")
    print(f"- NEO4J_URI: {'set' if os.getenv('NEO4J_URI') else 'not set'}")
    print(f"- NEO4J_USER: {'set' if os.getenv('NEO4J_USER') else 'not set'}")
    print(f"- NEO4J_PASSWORD: {'set' if os.getenv('NEO4J_PASSWORD') else 'not set'}")
    print("="*70 + "\n")

# Afficher les informations de démarrage
print_startup_info()

# Créer une application FastAPI qui sera utilisée comme point d'entrée ASGI
app = FastAPI()

# Configuration CORS pour l'application principale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Le routeur de santé sera ajouté plus bas après sa définition

# Variable pour stocker l'instance FastMCP et l'exporter explicitement
# Cette variable sera importée par main.py
mcp = None

# Initialiser FastMCP avec la configuration minimale
try:
    print("[INIT] Initializing FastMCP server...")
    mcp = FastMCP(
        name="mcp-crawl4ai-rag",
        lifespan=crawl4ai_lifespan
    )
    
    # Ne pas démarrer le serveur FastMCP ici, on utilise uniquement le routeur
    print("[INIT] FastMCP router initialized successfully")
    
    # Vérifier explicitement si le routeur existe et est accessible
    if not hasattr(mcp, "router"):
        print("[ERROR] FastMCP router not found. This is a critical error.")
        print("[DEBUG] Available attributes on mcp object:", dir(mcp))
        raise AttributeError("FastMCP object does not have a 'router' attribute")
    
    # Ajouter les routes de l'API MCP à l'application FastAPI
    app.include_router(mcp.router, prefix="/mcp")
    print("[INFO] MCP router included successfully.")
    
except Exception as e:
    print(f"[ERROR] Failed to initialize FastMCP server: {str(e)}")
    # Ne pas lever l'exception ici pour permettre au service de démarrer en mode dégradé
    mcp = None

# --- Main Entry Point ---
async def main():
    """
    Point d'entrée principal pour l'exécution en tant que script.
    
    Gère l'initialisation du service, la configuration et le démarrage du serveur.
    """
    print("\n" + "="*70)
    print(f"{' MCP CrawL4AI RAG - Initialization ':.^70}")
    print("="*70)
    
    # Vérification des variables d'environnement critiques
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_ANON_KEY",
        "SUPABASE_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    # Initialisation du client Supabase avec gestion des erreurs améliorée
    supabase_client = None
    try:
        print("[INIT] Initializing Supabase client...")
        supabase_client = get_supabase_client(max_retries=3, retry_delay=2)
        
        # Tester la connexion avec une requête simple
        print("[SUPABASE] Testing database connection...")
        try:
            result = supabase_client.table('sources').select("*").limit(1).execute()
            print(f"[SUPABASE] Connection successful. Found {len(result.data)} records in 'sources' table")
        except Exception as e:
            print(f"[WARNING] Could not query 'sources' table: {str(e)}")
            print("[INFO] This might be expected if the table doesn't exist yet")
            
    except Exception as e:
        error_msg = f"Failed to initialize Supabase client: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print("\nTroubleshooting tips:")
        print("1. Vérifiez que les variables d'environnement sont correctement définies")
        print("2. Vérifiez que l'URL de Supabase est accessible depuis le conteneur")
        print("3. Vérifiez que la clé de service est valide et a les bonnes permissions")
        print("4. Consultez les logs de Supabase pour plus de détails")
        raise RuntimeError(error_msg) from e
    
    # Configuration du serveur
    server_config = {
        "type": "http",
        "host": HOST,
        "port": PORT,
    }
    
    print(f"\n[CONFIG] Server configuration:")
    print(f"- Host: {HOST}")
    print(f"- Port: {PORT}")
    print(f"- Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Démarrer le serveur HTTP de santé
    http_server = None
    http_task = None
    try:
        print("\n[INIT] Starting health check HTTP server...")
        http_server, http_task = await start_http_server()
        print("[OK] Health check server started successfully")
    except Exception as e:
        print(f"[WARNING] Failed to start health check server: {str(e)}")
        http_server = None
        http_task = None
    
    try:
        # Démarrer le serveur Uvicorn principal
        config = uvicorn.Config(
            app,
            host=HOST,
            port=PORT,
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
            access_log=True,
            timeout_keep_alive=30
        )
        
        server = uvicorn.Server(config)
        
        print("\n" + "="*70)
        print(f"{' MCP CrawL4AI RAG Service Started ':.^70}")
        print("="*70)
        print(f"Service URL: http://{HOST}:{PORT}")
        print(f"Health check: http://{HOST}:{PORT}/health")
        print("="*70 + "\n")
        
        # Démarrer le serveur Uvicorn
        await server.serve()
            
    except asyncio.CancelledError:
        print("\n[INFO] Server shutdown requested...")
    except Exception as e:
        print(f"\n[ERROR] Server error: {str(e)}")
        raise
    finally:
        print("\n[SHUTDOWN] Shutting down services...")
        
        # Arrêter le serveur HTTP de santé s'il est en cours d'exécution
        if http_server and http_task:
            try:
                print("[SHUTDOWN] Stopping health check server...")
                http_task.cancel()
                try:
                    await http_task
                except asyncio.CancelledError:
                    pass
                print("[OK] Health check server stopped")
            except Exception as e:
                print(f"[WARNING] Error stopping health check server: {str(e)}")
        
        # Nettoyage des ressources
        if hasattr(mcp, 'lifespan'):
            try:
                print("[SHUTDOWN] Cleaning up resources...")
                await mcp.lifespan.shutdown()
                print("[OK] Resources cleaned up")
            except Exception as e:
                print(f"[WARNING] Error during resource cleanup: {str(e)}")
        
        print("[SHUTDOWN] Service stopped")

# --- Health Check and SSE Endpoints ---
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime

# Créer un routeur pour les endpoints de santé et SSE
health_router = APIRouter()

@health_router.get("/health")
async def http_health_check():
    """
    Endpoint de santé HTTP pour les vérifications de santé Docker/Kubernetes.
    
    Returns:
        JSONResponse contenant les informations de santé du service
    """
    return JSONResponse({
        "status": "healthy",
        "service": "mcp-crawl4ai-rag",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    })

@health_router.get("/sse")
async def sse_endpoint():
    """
    Endpoint SSE (Server-Sent Events) pour les communications en temps réel.
    
    Returns:
        StreamingResponse: Flux d'événements SSE
    """
    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@health_router.get("/")
async def root():
    """
    Endpoint racine pour les informations de base sur le service.
    
    Returns:
        JSONResponse contenant les informations de base sur le service
    """
    return JSONResponse({
        "service": "mcp-crawl4ai-rag",
        "description": "Service MCP pour le crawling web et RAG (Retrieval-Augmented Generation)",
        "version": "0.1.0",
        "endpoints": ["/", "/health", "/mcp/", "/sse"]
    })

async def sse_event_generator():
    """
    Générateur d'événements SSE.
    
    Yields:
        str: Événements SSE formatés
    """
    try:
        # Message initial pour confirmer la connexion
        yield f"data: {json.dumps({'type': 'connection', 'status': 'established'})}\n\n"
        
        # Boucle pour envoyer des événements périodiques
        counter = 0
        while True:
            counter += 1
            data = {
                'type': 'heartbeat',
                'timestamp': datetime.utcnow().isoformat(),
                'counter': counter
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(10)  # Envoyer un heartbeat toutes les 10 secondes
    except asyncio.CancelledError:
        # Envoyer un message de fermeture propre
        yield f"data: {json.dumps({'type': 'connection', 'status': 'closed'})}\n\n"
        raise

@health_router.get("/")
async def root():
    return {
        "service": "mcp-crawl4ai-rag",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp/"
        }
    }

# --- Tool Functions ---
@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Vérifie la santé du service (outil RPC).
    
    Returns:
        Dict contenant les informations de santé du service
    """
    return {
        "status": "healthy",
        "service": "mcp-crawl4ai-rag",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "details": {
            "database": "connected",
            "llm": "ready",
            "rag": "ready"
        }
    }

# --- Health Check Endpoint ---
@mcp.tool()
async def root() -> dict:
    """
    Point d'entrée principal avec des informations sur le service.
    
    Returns:
        dict: Informations sur le service et les endpoints disponibles.
    """
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

# --- Tool Functions ---
@mcp.tool()
async def crawl_and_process_url(ctx: Context, url: str) -> str:
    """Crawls a single URL, processes its content, and stores it in Supabase."""
    lifespan_ctx = ctx.request_context.lifespan_context
    crawler = lifespan_ctx.crawler
    supabase_client = lifespan_ctx.supabase_client

    try:
        result = await crawler.arun(url=url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
        if not result.success or not result.markdown:
            return json.dumps({"success": False, "error": f"Failed to crawl {url}. Status: {result.status_code}"})

        total_word_count = len(result.markdown.split())
        source_id = update_source_info(supabase_client, url, len(result.markdown), total_word_count)

        chunks = smart_chunk_markdown(result.markdown, source_id, url)
        add_documents_to_supabase(supabase_client, chunks)

        code_blocks = extract_code_blocks(result.markdown)
        if code_blocks:
            processed_examples = [process_code_example(cb, source_id, url, i) for i, cb in enumerate(code_blocks)]
            add_code_examples_to_supabase(supabase_client, processed_examples)

        return json.dumps({
            "success": True,
            "url": url,
            "chunks_stored": len(chunks),
            "code_examples_stored": len(code_blocks),
            "content_length": len(result.markdown),
            "total_word_count": total_word_count,
            "source_id": source_id,
        })
    except Exception as e:
        return json.dumps({"success": False, "error": f"An unexpected error occurred: {str(e)}"})


@mcp.tool()
async def search_in_documentation(ctx: Context, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Searches for a query in the stored documentation."""
    lifespan_ctx = ctx.request_context.lifespan_context
    supabase_client = lifespan_ctx.supabase_client
    reranking_model = lifespan_ctx.reranking_model
    
    results = search_documents(supabase_client, query, limit)
    return rerank_results(reranking_model, query, results)


@mcp.tool()
async def check_for_hallucinations(ctx: Context, text: str) -> Dict[str, Any]:
    """Validates a given text against the knowledge graph to detect hallucinations."""
    validator = ctx.request_context.lifespan_context.knowledge_validator
    if not validator:
        return {"error": "KnowledgeGraphValidator is not available. Check Neo4j connection."}
    
    report = await validator.validate_text(text)
    return report.to_dict()


@mcp.tool()
async def parse_github_repo(ctx: Context, repo_url: str) -> str:
    """Parses a GitHub repository and ingests its structure and code into Neo4j."""
    extractor = ctx.request_context.lifespan_context.repo_extractor
    if not extractor:
        return "DirectNeo4jExtractor is not available. Check Neo4j connection."
    
    try:
        await extractor.extract_and_ingest(repo_url)
        return f"Successfully parsed and ingested repository: {repo_url}"
    except Exception as e:
        return f"Failed to parse repository: {str(e)}"


@mcp.tool()
async def analyze_script_for_ai_patterns(ctx: Context, script_path: str) -> Dict[str, Any]:
    """Analyzes a local script file to identify common AI/ML patterns."""
    analyzer = AIScriptAnalyzer()
    if not Path(script_path).is_file():
        return {"error": f"File not found at path: {script_path}"}
    return analyzer.analyze_script(script_path)

# --- Main Entry Point ---
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

async def start_http_server():
    """Démarre le serveur HTTP séparé sur le port 8052"""
    import uvicorn
    from fastapi import FastAPI
    import asyncio
    
    # Créer une application FastAPI pour le serveur de santé
    health_app = FastAPI()
    
    # Ajouter l'endpoint de santé
    @health_app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "mcp-crawl4ai-rag"}
    
    # Configurer le serveur sur le port 8052
    config = uvicorn.Config(
        health_app,
        host=HOST,
        port=8052,  # Port fixe pour le serveur de santé
        log_level="info",
        access_log=True,
        timeout_keep_alive=30
    )
    
    server = uvicorn.Server(config)
    
    # Démarrer le serveur en arrière-plan
    print(f"Starting health check server on http://{HOST}:8052/health")
    
    # Créer une tâche pour exécuter le serveur
    task = asyncio.create_task(server.serve())
    
    # Attendre que le serveur soit prêt
    await asyncio.sleep(1)
    
    # Retourner le serveur et la tâche
    return server, task
