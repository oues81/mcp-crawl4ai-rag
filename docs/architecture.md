# Architecture

## Components

- **HTTP server** `src/http_server.py`
  - Endpoints: `/health`, `/mcp/crawl_single_page`, `/mcp/smart_crawl_url`, `/mcp/perform_rag_query`
  - MCP JSON-RPC: `/messages`, SSE: `/sse`
- **Crawl** via `crawl4ai`
  - `AsyncWebCrawler` with `BrowserConfig` honoring env vars (`CRAWLER_BROWSER_TYPE`, `USE_MANAGED_BROWSER`, `CRAWLER_HEADLESS`)
  - Fallback to simple HTTP + BeautifulSoup on browser failure
- **Embedding** `src/embeddings.py`
  - Default provider `ollama` with model `nomic-embed-text`
  - Pads/truncates vectors to `SUPABASE_VECTOR_DIM` (default 1536)
- **Persistence / Vector Store** `src/vector_store.py`
  - Supabase client using `SUPABASE_URL` + service role key
  - `upsert_chunks()` creates/updates `sources` and `crawled_pages`
  - `search()` calls RPC `match_crawled_pages`
- **Schema** `crawled_pages.sql`
  - `pgvector` extension
  - Tables: `sources`, `crawled_pages`, `code_examples`
  - Indexes (IVFFlat, GIN) + RLS policies
  - RPC functions: `match_crawled_pages`, `match_code_examples`

## Data Model (Core)

- `sources(source_id text primary key, summary text, total_word_count int, created_at, updated_at)`
- `crawled_pages(id bigserial, url, chunk_number, content, metadata jsonb, source_id, embedding vector(1536))`
  - Unique `(url, chunk_number)`, FK `source_id -> sources(source_id)`
- `code_examples(...)` same pattern for code snippets.

## Networks & Services

- Runs on container network(s), including shared `ai_network` for Ollama (`http://ollama:11434`).
- Requires Supabase project reachable over the Internet (REST and RPC).

## Security and RLS

- Public read policies on tables for simplicity; write is from the service role in the container.
- Do not expose service role key outside the secure environment.
