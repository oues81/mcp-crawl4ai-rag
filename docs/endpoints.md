# Endpoints

## Health
- `GET /health`
- `HEAD /health`

## Crawl
- `POST /mcp/crawl_single_page`
  - Body: `{ "url": string }`
  - Behavior: attempts Playwright-based crawl; on failure, HTTP fallback. On success, ingests into Supabase (`upsert_document`).
- `POST /mcp/smart_crawl_url`
  - Same shape as `crawl_single_page` (placeholder to extend: sitemap/llms-full/recursive).

## RAG
- `POST /mcp/perform_rag_query`
  - Body: `{ "query": string, "max_results"?: number, "filters"?: object }`
  - Behavior: embed query with Ollama, call Supabase RPC `match_crawled_pages`, return ranked matches.

## MCP Compatibility
- `GET /sse` — SSE stream
- `POST /messages` — Minimal JSON-RPC 2.0 handler
  - Tools: `crawl_single_page`, `smart_crawl_url`, `perform_rag_query`, `get_available_sources`

## Supabase RPC (server-side)
- `match_crawled_pages(query_embedding vector(1536), match_count int, filter jsonb, source_filter text)`
- `match_code_examples(...)` similar but over `code_examples`.
