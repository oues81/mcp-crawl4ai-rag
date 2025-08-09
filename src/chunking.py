from typing import List, Dict
import re

# Simple header/size-aware chunker

def split_into_chunks(text: str, max_chars: int = 2000, min_chars: int = 500) -> List[Dict]:
    if not text:
        return []
    # Split by headings to preserve structure
    sections = re.split(r"\n(?=#+\s)|\n(?=\w+\n[-=]{3,}\n)", text)
    chunks: List[Dict] = []
    buf = []
    size = 0
    idx = 0
    for sec in sections:
        s = sec.strip()
        if not s:
            continue
        if size + len(s) + 1 > max_chars and size >= min_chars:
            chunks.append({"chunk_number": len(chunks), "content": "\n".join(buf)})
            buf = [s]
            size = len(s)
        else:
            buf.append(s)
            size += len(s) + 1
        idx += 1
    if buf:
        chunks.append({"chunk_number": len(chunks), "content": "\n".join(buf)})
    return chunks
