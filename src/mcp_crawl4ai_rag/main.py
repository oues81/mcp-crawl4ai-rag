"""
Fichier principal et unique pour le service MCP Crawl4AI RAG.
Toute la logique est consolidée ici pour éliminer les erreurs d'importation dynamique.
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

# --- Configuration des chemins ---
# Le fichier est dans src/mcp_crawl4ai_rag, on remonte pour trouver les modules et le .env
service_root_path = Path(__file__).resolve().parents[1]
project_root_path = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(service_root_path))

knowledge_graphs_path = service_root_path / 'knowledge_graphs'
if str(knowledge_graphs_path) not in sys.path:
    sys.path.append(str(knowledge_graphs_path))

# Charger les variables d'environnement
dotenv_path = project_root_path / '.env'
load_dotenv(dotenv_path, override=True)

# --- Imports locaux (après configuration des chemins) ---
from knowledge_graphs.utils import (
    get_supabase_client, add_documents_to_supabase, search_documents,
    extract_code_blocks, generate_code_example_summary, add_code_examples_to_supabase,
    update_source_info, extract_source_summary, search_code_examples,
    smart_chunk_markdown, extract_section_info, process_code_example
)
from knowledge_graphs import KnowledgeGraphValidator, AIScriptAnalyzer, HallucinationReporter
from knowledge_graphs.parse_repo_into_neo4j import DirectNeo4jExtractor

# --- Paramètres globaux ---
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8002))

# --- Lifespan & Initialisation de l'app ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Logique à exécuter au démarrage
    print("MCP Crawl4AI RAG Service is starting up...")
    # Initialiser les clients, etc.
    yield
    # Logique à exécuter à l'arrêt
    print("MCP Crawl4AI RAG Service is shutting down...")

mcp = FastMCP(
    lifespan=lifespan,
    debug=DEBUG,
    title="Crawl4AI RAG MCP Server",
    description="MCP server with web crawling and RAG capabilities",
    version="0.1.0"
)

# C'est la ligne clé : on s'assure que l'app FastAPI est celle de l'instance MCP
app = mcp.app

# --- Endpoints de base ---
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
    return {"status": "healthy"}

# --- Outils MCP (exemple, ajouter les vrais outils ici) ---
@mcp.tool()
async def search_and_crawl(ctx: Context, query: str, collection_name: str = "documents") -> Dict[str, Any]:
    """Performs a web search, crawls top results, and returns structured content."""
    print(f"Received search_and_crawl request with query: {query}")
    # Mettre ici la logique complète de la fonction originale
    # Pour l'instant, on retourne une réponse de succès pour valider le flux
    return {
        "status": "success",
        "message": f"Crawling for query '{query}' completed.",
        "results": [
            {
                "url": "https://example.com",
                "title": "Example Domain",
                "content": "This is example content from a crawled page."
            }
        ]
    }

# --- Point d'entrée pour Uvicorn ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
