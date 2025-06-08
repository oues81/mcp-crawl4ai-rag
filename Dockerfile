FROM python:3.12-slim

ARG PORT=8051

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy requirements first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv pip install --system --no-cache-dir -e .


# Copy the rest of the application
COPY . .

# Make init script executable
RUN chmod +x /app/init_db.sh

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application
CMD ["./startup.sh"]
