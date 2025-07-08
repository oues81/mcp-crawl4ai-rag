#!/bin/bash
set -e

echo "Starting MCP Crawl4AI RAG Service..."
echo "Configuration:"
echo "  - Host: ${HOST:-0.0.0.0}"
echo "  - Port: ${PORT:-8010}"
echo "  - Transport: ${TRANSPORT:-sse}"
echo "  - Environment: ${ENVIRONMENT:-development}"

# Initialize database if needed (run in background)
if [ -f "/app/init-db.sh" ]; then
    echo "Running database initialization in background..."
    /app/init-db.sh &
fi

# Wait a moment for any background processes
sleep 2

# Start the MCP server directly with Python
echo "Starting MCP Crawl4AI RAG server..."
exec python src/crawl4ai_mcp.py
