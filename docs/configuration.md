# Configuration

## Required Environment Variables

- **Supabase**
  - `SUPABASE_URL` — e.g., `https://<project>.supabase.co`
  - `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_SERVICE_KEY` — service role key used by the service for writes
  - Note: For Supabase Management MCP tools, set `SUPABASE_ACCESS_TOKEN` in that MCP server (account-level token)
- **Embeddings / Ollama**
  - `EMBEDDING_PROVIDER=ollama`
  - `OLLAMA_EMBED_MODEL=nomic-embed-text`
  - `SUPABASE_VECTOR_DIM=1536`
  - `OLLAMA_HOST=http://ollama:11434` (service DNS on shared Docker network)
- **Crawler**
  - `CRAWLER_BROWSER_TYPE=chromium|firefox|webkit` (default: chromium)
  - `USE_MANAGED_BROWSER=true|false` (default: true)
  - `CRAWLER_HEADLESS=true|false` (default: true)
- **Service**
  - `HOST=0.0.0.0`
  - `PORT=8010`

## Notes

- The service reads Supabase keys directly from env and initializes a single Supabase client.
- Keys preference order in `vector_store.py`: `SUPABASE_SERVICE_ROLE_KEY` → `SUPABASE_SERVICE_KEY` → `SUPABASE_KEY` → `SUPABASE_ANON_KEY`.
- Ensure the Supabase schema is applied using `crawled_pages.sql` before running ingestion.
