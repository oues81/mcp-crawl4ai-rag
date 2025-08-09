# Troubleshooting

- **RPC not found (PGRST202)**
  - Apply `crawled_pages.sql` to the correct Supabase project.
  - Confirm functions `match_crawled_pages`, `match_code_examples` exist.

- **Unauthorized MCP Supabase tools**
  - Set `SUPABASE_ACCESS_TOKEN` in the MCP Supabase server env and restart it.

- **No rows after crawl**
  - Check logs. If Playwright fails, HTTP fallback should still call `upsert_document`. Ensure that fallback path persists (see `src/http_server.py`).
  - Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set in the service.

- **Ollama unreachable**
  - Ensure the service container is attached to the same Docker network as Ollama (e.g., `ai_network`).
  - `OLLAMA_HOST=http://ollama:11434` inside the container should resolve.

- **Vector dimension mismatch**
  - Keep `SUPABASE_VECTOR_DIM` aligned to the embedding model output (1536 for `nomic-embed-text`).

- **Browser startup errors**
  - Playwright may crash in constrained containers; logs show crashpad errors.
  - The service falls back to HTTP extraction automatically.
