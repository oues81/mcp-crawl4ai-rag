#!/bin/bash
set -e

# Configuration
APP_DIR="/app"
LOG_DIR="${APP_DIR}/logs"
DATA_DIR="${APP_DIR}/data"
PORT=${PORT:-8051}
HOST=${HOST:-0.0.0.0}
WORKERS=${WORKERS:-1}

# Create necessary directories
mkdir -p "${LOG_DIR}" "${DATA_DIR}"

# --- Logging Function ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# --- Generic Service Wait Function (TCP check) ---
wait_for_service() {
    local name="$1"
    local host="$2"
    local port="$3"
    local max_retries=30
    local wait_time=3
    local count=0

    log "Waiting for $name on $host:$port..."
    while true; do
        if (exec 3<>/dev/tcp/"$host"/"$port") 2>/dev/null; then
            log "$name is available."
            exec 3<&-
            exec 3>&-
            return 0
        fi
        count=$((count + 1))
        if [ $count -ge $max_retries ]; then
            log "ERROR: $name was not available after $max_retries attempts."
            return 1
        fi
        log "Waiting for $name... (attempt $count/$max_retries)"
        sleep $wait_time
    done
}

# --- Supabase Check Function ---
check_supabase_connection() {
    log "Verifying Supabase connection..."
    local endpoint_url="${SUPABASE_URL}/rest/v1/"
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -H "apikey: ${SUPABASE_SERVICE_KEY}" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" "$endpoint_url")

    if [ "$http_code" = "200" ] || [ "$http_code" = "404" ]; then
        log "Supabase connection successful (HTTP $http_code)."
        return 0
    else
        log "ERROR: Supabase connection failed (HTTP $http_code)."
        return 1
    fi
}


# --- Main Execution ---

log "--- Starting Service Initialization ---"

# 1. Check environment variables
log "Checking required environment variables..."
REQUIRED_VARS=("SUPABASE_URL" "SUPABASE_SERVICE_KEY" "DATABASE_URL")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log "ERROR: Environment variable $var is not set. Exiting."
        exit 1
    fi
done
log "Environment variables are set."

# 2. Wait for dependent services
DB_HOST=$(echo "$DATABASE_URL" | awk -F'@' '{print $2}' | awk -F':' '{print $1}')
DB_PORT=$(echo "$DATABASE_URL" | awk -F':' '{print $4}' | awk -F'/' '{print $1}')
wait_for_service "PostgreSQL" "$DB_HOST" "$DB_PORT"

# 3. Check external connection to Supabase
check_supabase_connection

# Check if the last command succeeded
if [ $? -ne 0 ]; then
    log "Halting startup due to failed pre-flight checks."
    exit 1
fi

log "All pre-flight checks passed. Starting application."

# 4. Start the application
exec python -m uvicorn \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --log-level "info" \
    --no-access-log \
    --app-dir "${APP_DIR}" \
    "src.crawl4ai_mcp:app"
