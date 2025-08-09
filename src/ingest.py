from typing import Any, Dict
from urllib.parse import urlparse

from chunking import split_into_chunks
from embeddings import embed_texts
from vector_store import upsert_chunks


def _source_id_from_url(url: str) -> str:
    try:
        netloc = urlparse(url).netloc
        return netloc or "unknown"
    except Exception:
        return "unknown"


def upsert_document(url: str, title: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    chunks = split_into_chunks(content)
    embeddings = embed_texts([c["content"] for c in chunks]) if chunks else []
    source_id = metadata.get("domain") or _source_id_from_url(url)
    # Prepare metadata that will be persisted alongside chunks
    enriched_meta = dict(metadata)
    enriched_meta["persisted"] = bool(len(chunks) > 0)
    enriched_meta["chunks_count"] = len(chunks)
    count = upsert_chunks(
        source_id=source_id,
        url=url,
        title=title,
        chunks=chunks,
        embeddings=embeddings,
        extra_metadata=enriched_meta,
    )
    return {"persisted": bool(count > 0), "chunks_count": count, "source_id": source_id}
