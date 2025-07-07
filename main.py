"""
Point d'entrée principal pour l'application FastAPI MCP Crawl4AI RAG.
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Créer une application FastAPI
app = FastAPI(
    title="MCP Crawl4AI RAG",
    description="API pour le service MCP Crawl4AI RAG",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint racine
@app.get("/")
async def root():
    return {
        "service": "mcp-crawl4ai-rag",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "sse": "/sse"
        },
        "version": "1.0.0"
    }

# Endpoint de santé
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Point d'entrée pour l'exécution directe
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
