import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from datetime import datetime

from supabase import create_client, Client  # type: ignore

_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_SERVICE_KEY")
    or os.getenv("SUPABASE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
)

if not _SUPABASE_URL or not _SUPABASE_KEY:
    raise RuntimeError("Supabase configuration is missing. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")

_sb: Client = create_client(_SUPABASE_URL, _SUPABASE_KEY)


def _domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc or "unknown"
    except Exception:
        return "unknown"


def upsert_chunks(
    *,
    source_id: str,
    url: str,
    title: str,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """Upsert chunks and sources into Supabase.
    Returns number of chunks persisted.
    """
    if not chunks:
        return 0
    # Ensure source entry exists (best effort)
    try:
        _sb.table("sources").upsert({
            "source_id": source_id,
            "summary": title or source_id,
            "updated_at": datetime.utcnow().isoformat(),
        }, on_conflict="source_id").execute()
    except Exception:
        pass

    rows = []
    meta_base = {"title": title or "", **(extra_metadata or {})}
    for ch, emb in zip(chunks, embeddings):
        row = {
            "url": url,
            "chunk_number": int(ch.get("chunk_number", 0)),
            "content": ch.get("content", ""),
            "metadata": meta_base,
            "source_id": source_id,
        }
        # Route to the correct embedding column by vector length
        try:
            dim = len(emb)
        except Exception:
            dim = 0
        if dim == 768:
            row["embedding_768"] = emb
        elif dim == 1536:
            row["embedding_1536"] = emb
        else:
            # Unknown dimension: skip to avoid DB errors
            continue
        rows.append(row)
    # Upsert chunks; rely on unique(url, chunk_number)
    _sb.table("crawled_pages").upsert(rows, on_conflict="url,chunk_number").execute()
    return len(rows)


def list_sources() -> List[str]:
    res = _sb.table("crawled_pages").select("source_id").execute()
    vals = res.data or []
    uniq = sorted({r.get("source_id", "") for r in vals if r.get("source_id")})
    return uniq


def search(
    query_embedding: List[float],
    *,
    match_count: int = 5,
    filter: Optional[Dict[str, Any]] = None,
    source_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    # Choose RPC based on embedding dimension
    fn = "match_crawled_pages"
    try:
        dim = len(query_embedding)
    except Exception:
        dim = 0
    if dim == 768:
        fn = "match_crawled_pages_768"
    elif dim == 1536:
        fn = "match_crawled_pages_1536"
    # Build params matching the RPC signature
    if fn in ("match_crawled_pages_768", "match_crawled_pages_1536"):
        rpc_params: Dict[str, Any] = {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "filter": filter or None,
            "source_filter": source_filter,
        }
    else:
        rpc_params = {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "filter": filter or {},
            "source_filter": source_filter,
        }
    res = _sb.rpc(fn, params=rpc_params).execute()
    return res.data or []
