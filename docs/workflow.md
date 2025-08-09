# End-to-End Workflow

1. **Apply schema** to Supabase (`crawled_pages.sql`): pgvector, tables, indexes, RLS, RPCs.
   - Via MCP Supabase management tools (requires `SUPABASE_ACCESS_TOKEN`), or SQL Editor.
2. **Start services**: ensure this service runs and can reach Ollama on the shared network.
3. **Crawl** pages:
   - `POST /mcp/crawl_single_page` with `{ "url": "https://example.com" }`
   - Service extracts text, chunks, embeds with Ollama, and upserts into Supabase.
4. **Verify** data:
   - `GET {SUPABASE_URL}/rest/v1/sources?select=source_id,summary,updated_at&limit=5`
   - `GET {SUPABASE_URL}/rest_v1/crawled_pages?select=id,url,chunk_number,source_id&limit=5`
5. **RAG Query**:
   - `POST /mcp/perform_rag_query` with `{ "query": "example domain", "max_results": 5 }`
6. **Iterate**: add sources, adjust filters, scale embeddings, refine chunking.

## Notes & Best Practices

- Prefer service role key in container; never expose it externally.
- Keep `SUPABASE_VECTOR_DIM` consistent with embedding model.
- Maintain the Docker network link to Ollama; use service DNS (`ollama`).
- Monitor health and logs for browser crashes; fallback path still persists data.
