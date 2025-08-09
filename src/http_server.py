#!/usr/bin/env python3
"""
Serveur HTTP simple pour exposer les fonctionnalités MCP Crawl4AI via des endpoints REST.
"""

import os
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from bs4 import BeautifulSoup  # fallback parsing
import requests  # HTTP fallback for crawling
import requests
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import c4ai_firefox_guard  # noqa: F401 ensure Crawl4AI respects firefox config
from crawl4ai.extraction_strategy import NoExtractionStrategy
from urllib.parse import urlparse

# RAG modules (support both `python src/http_server.py` and `uvicorn src.http_server:app`)
try:
    from ingest import upsert_document  # type: ignore
    from embeddings import embed_texts  # type: ignore
    from vector_store import list_sources as vs_list_sources, search as vs_search  # type: ignore
except Exception:  # pragma: no cover
    from src.ingest import upsert_document  # type: ignore
    from src.embeddings import embed_texts  # type: ignore
    from src.vector_store import list_sources as vs_list_sources, search as vs_search  # type: ignore

# Helper: build BrowserConfig from environment
def build_browser_config(context: str) -> BrowserConfig:
    """Construct a BrowserConfig honoring env vars and container constraints.
    Env:
      - CRAWLER_BROWSER_TYPE: 'chromium' | 'firefox' | 'webkit' (default: 'chromium')
      - USE_MANAGED_BROWSER: 'true'|'false' (default: 'true')
      - CRAWLER_HEADLESS: 'true'|'false' (default: 'true')
    """
    browser_type = os.getenv("CRAWLER_BROWSER_TYPE", "chromium").strip().lower()
    use_managed = os.getenv("USE_MANAGED_BROWSER", "true").strip().lower() == "true"
    headless = os.getenv("CRAWLER_HEADLESS", "true").strip().lower() == "true"

    extra_args = []
    # Minimal, container-safe flags for Chromium; harmless for others
    if browser_type == "chromium":
        extra_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--headless=new",
            "--disable-extensions",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
            "--disable-ipc-flooding-protection",
        ]

    cfg = BrowserConfig(
        browser_type=browser_type,
        headless=headless,
        browser_mode="dedicated",
        use_managed_browser=use_managed,
        verbose=True,
        extra_args=extra_args,
    )
    logger.info(
        "BrowserConfig(%s): %s",
        context,
        json.dumps({
            "browser_type": cfg.browser_type,
            "browser_mode": cfg.browser_mode,
            "use_managed_browser": cfg.use_managed_browser,
            "headless": cfg.headless,
            "extra_args": extra_args,
        }),
    )
    return cfg

# Configuration du logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Ensure Chromium crash dumps directory exists and is writable
def _ensure_crash_dumps_dir() -> None:
    try:
        crash_dir = Path("/tmp/chrome-crashes")
        crash_dir.mkdir(parents=True, exist_ok=True)
        try:
            # Best-effort permissive mode for containers
            os.chmod(crash_dir, 0o777)
        except Exception:
            # Non-fatal if chmod fails in read-only fs
            pass
        # Also ensure typical Crashpad DB locations under the app user's home are writable
        home = Path(os.getenv("HOME", "/home/appuser"))
        crashpad_paths = [
            home / ".config" / "Crashpad",
            home / ".local" / "share" / "Crashpad",
        ]
        for p in crashpad_paths:
            try:
                p.mkdir(parents=True, exist_ok=True)
                try:
                    os.chmod(p, 0o777)
                except Exception:
                    pass
            except Exception as ie:
                logger.debug(f"Unable to ensure {p}: {ie}")
        logger.info(f"Crash dumps dir ready: {crash_dir} and home crashpad dirs prepared")
    except Exception as e:
        logger.warning(f"Unable to ensure crash dumps dir: {e}")

_ensure_crash_dumps_dir()

# Queue des réponses MCP pour émission via SSE (mimique STI MCP)
_mcp_response_queue: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8010"))

# Création de l'application FastAPI
app = FastAPI(
    title="MCP Crawl4AI RAG Service",
    description="Service HTTP pour web crawling et RAG",
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

# Ensure crashpad directories at app startup too (import-time may be skipped in some scenarios)
@app.on_event("startup")
async def _startup_prepare_crashpad():
    _ensure_crash_dumps_dir()
    logger.info("Startup: crashpad directories ensured")

# Modèles Pydantic
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    details: Dict[str, Any]

class CrawlRequest(BaseModel):
    url: str
    extract_text: bool = True
    extract_metadata: bool = True

class RAGQueryRequest(BaseModel):
    query: str
    max_results: int = 5
    filters: Dict[str, Any] = {}

class CrawlResponse(BaseModel):
    success: bool
    url: str
    content: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class RAGQueryResponse(BaseModel):
    success: bool
    query: str
    results: List[Dict[str, Any]] = []
    error: Optional[str] = None

# Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de vérification de santé du service."""
    provider = os.getenv("EMBEDDING_PROVIDER", "ollama")
    model = os.getenv("EMBEDDING_MODEL", os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"))
    # Determine active vector column for visibility
    env_dim = int(os.getenv("SUPABASE_VECTOR_DIM", "1536"))
    if provider.strip().lower() == "openai" or env_dim == 1536:
        active_vector = {"column": "embedding_1536", "dim": 1536}
    else:
        active_vector = {"column": "embedding_768", "dim": 768}
    return HealthResponse(
        status="healthy",
        service="mcp-crawl4ai-rag",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        details={
            "database": "connected" if os.getenv("SUPABASE_URL") else "disconnected",
            "embedding_provider": provider,
            "embedding_model": model,
            "vector_dim": env_dim,
            "active_vector": active_vector,
            "knowledge_graph": "disabled",
            "reranking": "disabled"
        }
    )

# Support explicite du HEAD /health pour les healthchecks Windsurf
@app.head("/health")
async def health_head():
    return Response(status_code=200)

@app.get("/mcp/get_available_sources")
async def get_available_sources():
    try:
        sources = vs_list_sources()
        return {"success": True, "sources": sources}
    except Exception as e:
        logger.error(f"list_sources failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/crawl_single_page", response_model=CrawlResponse)
async def crawl_single_page(request: CrawlRequest):
    """
    Crawl une page web RÉELLEMENT avec crawl4ai.
    
    Args:
        request: Requête contenant l'URL à crawler
        
    Returns:
        Réponse avec le contenu réel de la page
    """
    try:
        logger.info(f"REAL CRAWLING page: {request.url}")
        
        # Utiliser vraiment crawl4ai
        _ensure_crash_dumps_dir()
        browser_config = build_browser_config("crawl_single_page")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=request.url,
                config=CrawlerRunConfig(
                    word_count_threshold=10,
                    extraction_strategy=NoExtractionStrategy(),
                    cache_mode=CacheMode.BYPASS
                )
            )
            
            if result.success:
                content = result.markdown or result.cleaned_html or "Pas de contenu disponible"
                meta = {
                    "source": "crawl4ai",
                    "timestamp": datetime.utcnow().isoformat(),
                    "length": len(content),
                    "title": result.metadata.get("title", ""),
                    "description": result.metadata.get("description", ""),
                    "domain": urlparse(request.url).netloc or (request.url.split('/')[2] if '//' in request.url else "unknown"),
                }
                # Defaults to always expose stable keys
                meta.setdefault("persisted", False)
                meta.setdefault("chunks_count", 0)
                try:
                    ingest_res = upsert_document(request.url, meta.get("title", ""), content, meta)
                    meta.update({"persisted": True, **ingest_res})
                except Exception as e:
                    logger.error(f"Supabase upsert failed: {e}")
                    meta.update({"persisted": False, "error": str(e)})
                return CrawlResponse(
                    success=True,
                    url=request.url,
                    content=content,
                    metadata=meta,
                )
            else:
                logger.error(f"Crawl failed for {request.url}: {result.error_message}")
                # HTTP fallback when Playwright crawl fails
                try:
                    logger.info(f"HTTP fallback for {request.url}")
                    r = requests.get(request.url, timeout=15)
                    r.raise_for_status()
                    soup = BeautifulSoup(r.text, "html.parser")
                    text = soup.get_text(" ")
                    content = text.strip()[:5000]
                    if content:
                        meta = {
                            "source": "http_fallback",
                            "timestamp": datetime.utcnow().isoformat(),
                            "length": len(content),
                            "title": soup.title.string if soup.title else "",
                            "description": "",
                            "domain": urlparse(request.url).netloc or (request.url.split('/')[2] if '//' in request.url else "unknown"),
                        }
                        # Defaults to always expose stable keys
                        meta.setdefault("persisted", False)
                        meta.setdefault("chunks_count", 0)
                        try:
                            ingest_res = upsert_document(request.url, meta.get("title", ""), content, meta)
                            meta.update({"persisted": True, **ingest_res})
                        except Exception as e2:
                            logger.error(f"Supabase upsert failed (fallback): {e2}")
                            meta.update({"persisted": False, "error": str(e2)})
                        return CrawlResponse(
                            success=True,
                            url=request.url,
                            content=content,
                            metadata=meta,
                        )
                except Exception as e2:
                    logger.error(f"HTTP fallback failed for {request.url}: {e2}")
                return CrawlResponse(
                    success=False,
                    url=request.url,
                    error=result.error_message or "Crawling failed"
                )
        
    except Exception as e:
        logger.error(f"Erreur lors du crawling de {request.url}: {e}")
        # Try HTTP fallback on exception too
        try:
            logger.info(f"HTTP fallback (exception) for {request.url}")
            r = requests.get(request.url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ")
            content = text.strip()[:5000]
            if content:
                meta = {
                    "source": "http_fallback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "length": len(content),
                    "title": soup.title.string if soup.title else "",
                    "description": "",
                    "domain": urlparse(request.url).netloc or (request.url.split('/')[2] if '//' in request.url else "unknown"),
                }
                # Defaults to always expose stable keys
                meta.setdefault("persisted", False)
                meta.setdefault("chunks_count", 0)
                try:
                    ingest_res = upsert_document(request.url, meta.get("title", ""), content, meta)
                    meta.update({"persisted": True, **ingest_res})
                except Exception as ie:
                    logger.error(f"Supabase upsert failed (exception fallback): {ie}")
                    meta.update({"persisted": False, "error": str(ie)})
                return CrawlResponse(
                    success=True,
                    url=request.url,
                    content=content,
                    metadata=meta,
                )
                
        except Exception as e2:
            logger.error(f"HTTP fallback (exception) failed for {request.url}: {e2}")
        return CrawlResponse(
            success=False,
            url=request.url,
            error=str(e)
        )

@app.post("/mcp/perform_rag_query", response_model=RAGQueryResponse)
async def perform_rag_query(request: RAGQueryRequest):
    """
    DB-backed RAG query using Supabase + Ollama embeddings.
    """
    try:
        logger.info(f"RAG DB query: '{request.query}'")
        qvec = embed_texts([request.query])[0]
        rows = vs_search(qvec, match_count=int(request.max_results or 5), filter=request.filters or {}, source_filter=None)
        results: List[Dict[str, Any]] = []
        for r in rows:
            url = r.get("url") or r.get("document_url") or ""
            meta = r.get("metadata") or {}
            title = (meta.get("title") if isinstance(meta, dict) else None) or meta or ""
            snippet = r.get("content") or r.get("chunk") or ""
            score = r.get("similarity") or r.get("score") or 0.0
            results.append({
                "url": url,
                "title": title,
                "snippet": snippet[:800] + ("..." if len(snippet) > 800 else ""),
                "content": snippet,
                "score": float(score),
                "metadata": meta if isinstance(meta, dict) else {"meta": meta},
            })
        return RAGQueryResponse(success=True, query=request.query, results=results)
    except Exception as e:
        logger.error(f"RAG DB query failed for '{request.query}': {e}")
        return RAGQueryResponse(success=False, query=request.query, error=str(e))

# --- Additional tools to match upstream ---
@app.post("/mcp/smart_crawl_url")
async def smart_crawl_url(request: CrawlRequest):
    """Smart crawl based on URL type (sitemap, llms-full.txt, or regular page).
    Minimal implementation: for now, treat as single-page crawl; can be extended.
    """
    try:
        return await crawl_single_page(request)
    except Exception as e:
        logger.error(f"smart_crawl_url failed for {request.url}: {e}")
        return CrawlResponse(success=False, url=request.url, error=str(e))

@app.get("/mcp/get_available_sources")
async def get_available_sources():
    """Return available sources (domains) in storage.
    Placeholder: return empty list until storage is wired.
    """
    try:
        return {"success": True, "sources": []}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/sse")
async def sse_endpoint(request: Request):
    """Vrai endpoint SSE (Server-Sent Events) pour compatibilité Windsurf MCP.

    Fournit un flux d'événements avec des pings réguliers pour maintenir la connexion.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        # Message d'ouverture
        yield "event: open\ndata: {\"status\":\"ready\"}\n\n"
        last_ping = time.monotonic()
        while True:
            if await request.is_disconnected():
                break
            try:
                # attente d'un message à émettre (jusqu'à 10s)
                resp = await asyncio.wait_for(_mcp_response_queue.get(), timeout=10.0)
                yield f"event: message\ndata: {json.dumps(resp)}\n\n"
            except asyncio.TimeoutError:
                now = time.monotonic()
                if now - last_ping >= 15:
                    yield "event: ping\ndata: keepalive\n\n"
                    last_ping = now

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)

@app.post("/messages")
async def messages(request: Request):
    """Endpoint JSON-RPC 2.0 minimal pour MCP: listTools, callTool, listResources, readResource."""
    try:
        body = await request.json()
    except Exception:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error"}
        }

    rpc_id = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}

    def ok(result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": rpc_id, "result": result}

    def err(code: int, message: str, data: Any = None) -> Dict[str, Any]:
        e = {"code": code, "message": message}
        if data is not None:
            e["data"] = data
        return {"jsonrpc": "2.0", "id": rpc_id, "error": e}

    try:
        logging.info("/messages: method=%s params_keys=%s", method, list(params.keys()) if isinstance(params, dict) else type(params))
        if method in {"initialize"}:
            response_payload = ok({
                "capabilities": {
                    "workspace": {"workspaceFolders": True},
                    "textDocument": {
                        "synchronization": {"dynamicRegistration": True},
                        "completion": {"dynamicRegistration": True},
                    },
                    "tools": {"listChanged": True, "supportsListing": True, "supportsCalling": True},
                },
                "serverInfo": {"name": "mcp-crawl4ai-rag", "version": "1.0.0"},
            })
            # publish to SSE
            await _mcp_response_queue.put(response_payload)
            return response_payload

        if method in {"initialized"}:
            response_payload = ok({})
            await _mcp_response_queue.put(response_payload)
            return response_payload

        if method in {"list_tools", "tools/list", "listTools"}:
            tools = [
                {
                    "name": "crawl_single_page",
                    "description": "Crawl a single web page and return extracted content.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                        "required": ["url"]
                    }
                },
                {
                    "name": "smart_crawl_url",
                    "description": "Intelligently crawl a website based on URL type (sitemap, llms-full.txt, or recursive).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "extract_text": {"type": "boolean", "default": True},
                            "extract_metadata": {"type": "boolean", "default": True}
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "get_available_sources",
                    "description": "List available sources (domains) in the database for filtering.",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "perform_rag_query",
                    "description": "Perform a basic RAG-style web query with crawling of known references.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}, "max_results": {"type": "integer", "default": 5}},
                        "required": ["query"]
                    }
                }
            ]
            response_payload = ok({"tools": tools})
            await _mcp_response_queue.put(response_payload)
            return response_payload

        if method in {"callTool", "tools/call"}:
            try:
                # Normalize callTool params. 'params' is already parsed above.
                call_params = params if isinstance(params, dict) else {}
                name = call_params.get("name") or call_params.get("toolName")
                arguments = call_params.get("arguments")
                if arguments is None:
                    arguments = call_params.get("args")
                if arguments is None:
                    arguments = {}
                if not isinstance(arguments, dict):
                    return err(-32602, "Invalid params for callTool", "arguments must be an object")
            except Exception as e:
                return err(-32602, "Invalid params for callTool", str(e))
            
            if name == "crawl_single_page":
                try:
                    req = CrawlRequest(url=str(arguments.get("url", "")))
                except Exception as e:
                    return err(-32602, "Invalid params for crawl_single_page", str(e))
                try:
                    # Bound execution time to avoid long Playwright hangs
                    res = await asyncio.wait_for(crawl_single_page(req), timeout=25)
                    # If browser path missing or other issue caused unsuccessful result, do HTTP fallback
                    if hasattr(res, "success") and not res.success:
                        logging.warning("crawl_single_page returned success=false; using HTTP fallback url=%s", req.url)
                        try:
                            r = requests.get(req.url, timeout=20)
                            r.raise_for_status()
                            html = r.text
                            soup = BeautifulSoup(html, "html.parser")
                            title = (soup.title.string.strip() if soup.title and soup.title.string else "")
                            text = soup.get_text(" ")
                            fallback_content = {
                                "url": req.url,
                                "status_code": r.status_code,
                                "title": title,
                                "excerpt": (text[:1000] if text else ""),
                                "note": "playwright unsuccessful; returned fallback extraction",
                            }
                            response_payload = ok({"content": [{"type": "text", "text": json.dumps(fallback_content)}]})
                            await _mcp_response_queue.put(response_payload)
                            return response_payload
                        except Exception as e2:
                            logging.exception("fallback requests extraction failed for url=%s", req.url)
                            response_payload = err(-32001, "crawl_single_page unsuccessful and fallback failed", str(e2))
                            await _mcp_response_queue.put(response_payload)
                            return response_payload
                    # Pydantic v2: model_dump
                    result_payload = res.model_dump() if hasattr(res, "model_dump") else res.dict()
                    response_payload = ok({"content": [{"type": "text", "text": json.dumps(result_payload)}]})
                    await _mcp_response_queue.put(response_payload)
                    return response_payload
                except asyncio.TimeoutError:
                    logging.error("crawl_single_page timeout after 25s, using fallback url=%s", req.url)
                    # Fallback handled below
                    pass
                except Exception:
                    logging.exception("crawl_single_page failed, falling back to requests for url=%s", req.url)
                    logging.exception("crawl_single_page failed, falling back to requests for url=%s", req.url)
                    # Fallback: basic HTTP GET + HTML extraction
                    try:
                        r = requests.get(req.url, timeout=20)
                        r.raise_for_status()
                        html = r.text
                        soup = BeautifulSoup(html, "html.parser")
                        title = (soup.title.string.strip() if soup.title and soup.title.string else "")
                        text = soup.get_text(" ")
                        fallback_content = {
                            "url": req.url,
                            "status_code": r.status_code,
                            "title": title,
                            "excerpt": (text[:1000] if text else ""),
                            "note": "playwright failed; returned fallback extraction",
                        }
                        response_payload = ok({"type": "result", "content": fallback_content})
                        await _mcp_response_queue.put(response_payload)
                        return response_payload
                    except Exception as e2:
                        logging.exception("fallback requests extraction failed for url=%s", req.url)
                        response_payload = err(-32001, "crawl_single_page failed and fallback failed", str(e2))
                        await _mcp_response_queue.put(response_payload)
                        return response_payload
            elif name == "smart_crawl_url":
                try:
                    req = CrawlRequest(
                        url=str(arguments.get("url", "")),
                        extract_text=bool(arguments.get("extract_text", True)),
                        extract_metadata=bool(arguments.get("extract_metadata", True)),
                    )
                except Exception as e:
                    return err(-32602, "Invalid params for smart_crawl_url", str(e))
                try:
                    res = await asyncio.wait_for(smart_crawl_url(req), timeout=90)
                    result_payload = res.model_dump() if hasattr(res, "model_dump") else res.dict()
                    response_payload = ok({"content": [{"type": "text", "text": json.dumps(result_payload)}]})
                    await _mcp_response_queue.put(response_payload)
                    return response_payload
                except asyncio.TimeoutError:
                    logging.error("smart_crawl_url timeout after 90s: url=%s", req.url)
                    response_payload = err(-32003, "smart_crawl_url timeout", req.url)
                    await _mcp_response_queue.put(response_payload)
                    return response_payload
                except Exception as e:
                    logging.exception("smart_crawl_url failed: url=%s", req.url)
                    response_payload = err(-32002, "smart_crawl_url failed", str(e))
                    await _mcp_response_queue.put(response_payload)
                    return response_payload
            elif name == "get_available_sources":
                try:
                    response_payload = ok({"content": [{"type": "text", "text": json.dumps({"success": True, "sources": []})}]})
                    await _mcp_response_queue.put(response_payload)
                    return response_payload
                except Exception as e:
                    response_payload = err(-32002, "get_available_sources failed", str(e))
                    await _mcp_response_queue.put(response_payload)
                    return response_payload
            elif name == "perform_rag_query":
                try:
                    req = RAGQueryRequest(
                        query=str(arguments.get("query", "")),
                        max_results=int(arguments.get("max_results", 5)),
                        filters=arguments.get("filters", {}) or {}
                    )
                except Exception as e:
                    return err(-32602, "Invalid params for perform_rag_query", str(e))
                try:
                    res = await asyncio.wait_for(perform_rag_query(req), timeout=90)
                    result_payload = res.model_dump() if hasattr(res, "model_dump") else res.dict()
                    response_payload = ok({"content": [{"type": "text", "text": json.dumps(result_payload)}]})
                    await _mcp_response_queue.put(response_payload)
                    return response_payload
                except asyncio.TimeoutError:
                    logging.error("perform_rag_query timeout after 90s: query=%s", req.query)
                    response_payload = err(-32003, "perform_rag_query timeout", req.query)
                    await _mcp_response_queue.put(response_payload)
                    return response_payload
                except Exception as e:
                    logging.exception("perform_rag_query failed: query=%s", req.query)
                    response_payload = err(-32002, "perform_rag_query failed", str(e))
                    await _mcp_response_queue.put(response_payload)
                    return response_payload
            else:
                response_payload = err(-32601, f"Tool not found: {name}")
                await _mcp_response_queue.put(response_payload)
                return response_payload

        if method in {"listResources", "resources/list"}:
            response_payload = ok({"resources": []})
            await _mcp_response_queue.put(response_payload)
            return response_payload

        if method in {"readResource", "resources/read"}:
            response_payload = err(-32601, "readResource not implemented")
            await _mcp_response_queue.put(response_payload)
            return response_payload

        response_payload = err(-32601, f"Method not found: {method}")
        await _mcp_response_queue.put(response_payload)
        return response_payload
    except Exception as e:
        response_payload = err(-32000, "Server error", str(e))
        await _mcp_response_queue.put(response_payload)
        return response_payload

@app.post("/sse")
async def sse_post(request: Request):
    """Compatibilité MCP: certains clients POSTent le JSON-RPC sur /sse.
    On délègue au même handler que /messages, comme dans `services/sti_mcp_server/main.py`.
    """
    return await messages(request)

# Point d'entrée principal
def main():
    """
    Démarre le serveur HTTP.
    """
    print("\n" + "="*70)
    print(f"{' MCP Crawl4AI RAG HTTP Service ':.^70}")
    print("="*70)
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print("="*70)
    print(f"Service URL: http://{HOST}:{PORT}")
    print(f"Health endpoint: http://{HOST}:{PORT}/health")
    print(f"Crawl endpoint: http://{HOST}:{PORT}/mcp/crawl_single_page")
    print(f"RAG endpoint: http://{HOST}:{PORT}/mcp/perform_rag_query")
    print("="*70 + "\n")
    
    # Démarrer le serveur Uvicorn
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )

if __name__ == "__main__":
    main()
