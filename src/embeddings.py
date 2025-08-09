import os
from typing import List

# Enforce Ollama by default per project requirement
_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").strip().lower()
_MODEL = os.getenv("EMBEDDING_MODEL", os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")).strip()
_TARGET_DIM = int(os.getenv("SUPABASE_VECTOR_DIM", "1536"))

# Lazy imports
_ollama = None
_openai_client = None


def _embed_ollama(texts: List[str]) -> List[List[float]]:
    global _ollama
    if _ollama is None:
        import ollama  # type: ignore
        _ollama = ollama
    vectors: List[List[float]] = []
    for t in texts:
        r = _ollama.embeddings(model=_MODEL, prompt=t)
        vectors.append(r["embedding"])  # type: ignore
    return vectors


def _embed_openai(texts: List[str]) -> List[List[float]]:
    # Optional fallback if explicitly requested via EMBEDDING_PROVIDER=openai
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI()
    resp = _openai_client.embeddings.create(model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"), input=texts)
    return [d.embedding for d in resp.data]


def pad_to_dim(vectors: List[List[float]], target_dim: int = _TARGET_DIM) -> List[List[float]]:
    padded: List[List[float]] = []
    for v in vectors:
        if len(v) == target_dim:
            padded.append(v)
        elif len(v) < target_dim:
            padded.append(v + [0.0] * (target_dim - len(v)))
        else:
            padded.append(v[:target_dim])
    return padded


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    if _PROVIDER == "openai":
        vecs = _embed_openai(texts)
    else:
        vecs = _embed_ollama(texts)
    # Return native dimension vectors; routing to the proper DB column is handled downstream
    return vecs
