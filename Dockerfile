# ========== Étape de construction ==========
FROM python:3.12-slim as builder

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    git \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && chmod +x ${POETRY_HOME}/bin/poetry

# Set working directory
WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN ${POETRY_HOME}/bin/poetry install --no-root --only main

# Development stage
FROM base as development
ENV ENVIRONMENT=development
RUN ${POETRY_HOME}/bin/poetry install --no-root
CMD ["${POETRY_HOME}/bin/poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

# Production stage
FROM base as production
ENV ENVIRONMENT=production

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app \
    PORT=8002 \
    HOST=0.0.0.0 \
    LOG_LEVEL=info \
    # Performance optimizations
    PYTHONPATH=/app \
    SUPABASE_TIMEOUT=30 \
    MAX_RETRIES=3 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1 \
    DISABLE_GPU=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_ENABLE_ONEDNN_OPTS=0 \
    TORCH_USE_CUDA=0 \
    PYTORCH_CUDA_ALLOC_CONF=0

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

USER 1000:1000
CMD ["uvicorn", "src.mcp_crawl4ai_rag.main:app", "--host", "0.0.0.0", "--port", "8000"]
