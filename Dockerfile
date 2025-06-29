# syntax=docker/dockerfile:1.4

FROM python:3.12-slim

WORKDIR /app

# Installation des dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Variables d'environnement
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CRAWL4_AI_BASE_DIRECTORY=/data \
    PORT=8002

# Installation des dépendances avec pip
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir "crawl4ai[cpu]" "fastapi[all]" "uvicorn[standard]" "pydantic[email]" "pydantic-settings" "python-dotenv" "httpx[http2]" "anyio" "gunicorn" "mcp" "fastmcp" "supabase" "beautifulsoup4" "lxml" "aiofiles" "aiohttp" "aiosqlite" "brotli" "chardet" "click" "colorama" "cssselect" "fake-useragent" "humanize" "litellm" "nltk" "numpy" "pillow" "playwright" "psutil" "pyopenssl" "pyperclip" "rank-bm25" "rich" "snowballstemmer" "tf-playwright-stealth" "xxhash" "sqlalchemy" "alembic" "pandas" "neo4j" "python-jose[cryptography]" "passlib[bcrypt]" "python-slugify" "pyyaml" "jinja2" "sentence-transformers" "openai" "huggingface-hub" "torch" "transformers" "fastapi-pagination" "python-multipart"

# Installation des navigateurs pour Playwright
RUN playwright install --with-deps

# Copie du code source de l'application
COPY ./docker/services/mcp-crawl4ai-rag/src /app/

# Création du répertoire knowledge_graphs s'il n'existe pas
RUN mkdir -p /app/knowledge_graphs

# Copie des fichiers nécessaires
COPY ./docker/services/mcp-crawl4ai-rag/src/knowledge_graphs /app/knowledge_graphs/
COPY ./docker/services/mcp-crawl4ai-rag/src/main.py /app/
COPY ./docker/services/mcp-crawl4ai-rag/src/crawl4ai_mcp.py /app/

EXPOSE ${PORT}

# Commande de démarrage
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
