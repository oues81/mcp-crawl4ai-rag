# MCP Crawl4AI RAG — Documentation

This documentation explains how the MCP-enabled Crawl4AI RAG service works, what it provides, how to configure it, and how to run the end-to-end workflow.

- Audience: developers/operators
- Scope: MCP server, tools, crawling, embeddings with Ollama, Supabase vector store, RAG querying

See also:
- `docs/architecture.md`
- `docs/configuration.md`
- `docs/endpoints.md`
- `docs/workflow.md`
- `docs/troubleshooting.md`

---

## Overview

- **Goal**: crawl web content, embed it with **Ollama** (e.g., `nomic-embed-text`), persist chunks and embeddings into **Supabase** (`pgvector`), and expose a **RAG** search endpoint. The service is MCP-compatible and integrates with other MCP tools.
- **Key components**:
  - `src/http_server.py` — FastAPI HTTP server exposing health, crawl and RAG endpoints, plus minimal MCP JSON-RPC compatibility.
  - `src/ingest.py` — chunking + embedding + upsert into Supabase.
  - `src/chunking.py` — simple text chunking.
  - `src/embeddings.py` — Ollama embeddings (default) with optional OpenAI fallback.
  - `src/vector_store.py` — Supabase client, upsert logic, RPC search via `match_crawled_pages`.
  - `crawled_pages.sql` — Supabase schema: tables, indexes, RLS, and RPC functions.

---

## What is MCP here?

- **MCP (Model Context Protocol)** is used to expose and consume tools/resources across microservices.
- This service acts as an MCP-compatible HTTP server with:
  - SSE endpoint: `/sse`
  - JSON-RPC endpoint: `/messages`
  - Tools mapped to HTTP endpoints: `crawl_single_page`, `smart_crawl_url`, `perform_rag_query`, `get_available_sources`.
- Separate MCP servers (e.g., Supabase Management) are used to apply migrations and manage projects (requires `SUPABASE_ACCESS_TOKEN`).

---

## High-level Flow

1. Crawl a URL using Playwright via **Crawl4AI**; fallback to HTTP extraction if browser fails.
2. Split content into chunks; compute **Ollama** embeddings (`nomic-embed-text`), padded to `SUPABASE_VECTOR_DIM`.
3. Upsert `sources` and `crawled_pages` with vectors into **Supabase** (see `crawled_pages.sql`).
4. Query with `perform_rag_query`: embed the query with Ollama and call Supabase RPC `match_crawled_pages` for KNN results.

---

## Quickstart

- Requirements: Docker/Compose, running **Ollama** container on shared network (e.g., `ai_network`), valid Supabase project URL + Service Role key.
- Ensure schema is applied to Supabase using `crawled_pages.sql` (via MCP Supabase tools or SQL editor).
- Start the service (see project-level `docker-compose.yml`).
- Test:
  - `GET http://localhost:8010/health`
  - `POST http://localhost:8010/mcp/crawl_single_page` with `{ "url": "https://example.com" }`
  - `POST http://localhost:8010/mcp/perform_rag_query` with `{ "query": "example domain" }`

---

## Where to go next

- Architecture details: `docs/architecture.md`
- Configuration and env vars: `docs/configuration.md`
- Endpoints (HTTP & MCP): `docs/endpoints.md`
- End-to-end workflow: `docs/workflow.md`
- Troubleshooting: `docs/troubleshooting.md`
