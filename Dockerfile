# Stage 1: Builder - Install dependencies with Poetry
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app

# Copy dependency files from the context root
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry lock
RUN poetry install --without dev --no-root

# Install PyTorch for CPU separately to avoid dependency resolution issues
RUN . /app/.venv/bin/activate && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Stage 2: Final image
FROM python:3.12-slim AS final

# Create a non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Copy virtual env from builder stage
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy the application source code from the context's src directory
COPY --chown=appuser:appgroup src/ /app/src/

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8002

# Define the command to run the application
CMD ["/app/.venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
