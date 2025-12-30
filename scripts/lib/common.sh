#!/bin/bash
# Satisfactory Server - Common Bash Library
# Shared functions for all scripts

# Prevent multiple sourcing
[[ -n "${_COMMON_SH_LOADED:-}" ]] && return
_COMMON_SH_LOADED=1

# =============================================================================
# Path Resolution
# =============================================================================

# Get the scripts root directory (parent of lib/)
get_scripts_dir() {
    local source="${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}"
    local dir
    dir="$(cd "$(dirname "$source")" && pwd)"

    # If we're in a subdirectory, go up to scripts root
    if [[ "$dir" == */lib ]]; then
        echo "$(dirname "$dir")"
    elif [[ "$dir" == */server ]] || [[ "$dir" == */mods ]] || [[ "$dir" == */network ]] || [[ "$dir" == */setup ]]; then
        echo "$(dirname "$dir")"
    else
        echo "$dir"
    fi
}

# Get the project root directory
get_project_dir() {
    local scripts_dir
    scripts_dir="$(get_scripts_dir)"
    echo "$(dirname "$scripts_dir")"
}

# Initialize common paths (call this at the start of each script)
init_paths() {
    SCRIPTS_DIR="$(get_scripts_dir)"
    PROJECT_DIR="$(get_project_dir)"
    DATA_DIR="${PROJECT_DIR}/data"
    LOGS_DIR="${DATA_DIR}/logs"
    BACKUP_DIR="${DATA_DIR}/backups"
    SAVE_DIR="${DATA_DIR}/saved"
    MODS_DIR="${DATA_DIR}/gamefiles/FactoryGame/Mods"

    # Create necessary directories
    mkdir -p "$LOGS_DIR" "$BACKUP_DIR"
}

# =============================================================================
# Terminal Colors
# =============================================================================

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'  # No Color

# =============================================================================
# Logging
# =============================================================================

# Default log file (can be overridden)
LOG_FILE=""

# Set log file path
set_log_file() {
    LOG_FILE="$1"
    mkdir -p "$(dirname "$LOG_FILE")"
}

# Logging function with timestamp
log() {
    local message="$1"
    local timestamp
    timestamp="[$(date '+%Y-%m-%d %H:%M:%S')]"

    if [[ -n "$LOG_FILE" ]]; then
        echo "$timestamp $message" | tee -a "$LOG_FILE"
    else
        echo "$timestamp $message"
    fi
}

# Log levels
log_info() {
    log "INFO: $1"
}

log_warn() {
    log "WARNING: $1"
}

log_error() {
    log "ERROR: $1"
}

log_success() {
    log "SUCCESS: $1"
}

# Print with color (doesn't go to log file)
print_info() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# =============================================================================
# Environment Loading
# =============================================================================

# Load environment variables from .env file
load_env() {
    local env_file="${PROJECT_DIR}/.env"

    if [[ -f "$env_file" ]]; then
        # Export all non-comment, non-empty lines
        set -a
        # shellcheck disable=SC1090
        source <(grep -v '^\s*#' "$env_file" | grep -v '^\s*$')
        set +a
        return 0
    fi
    return 1
}

# Get env variable with default
get_env() {
    local var_name="$1"
    local default_value="${2:-}"
    echo "${!var_name:-$default_value}"
}

# =============================================================================
# Docker Operations
# =============================================================================

DOCKER_COMPOSE_FILE=""

# Initialize docker compose file path
init_docker() {
    DOCKER_COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
}

# Check if a container is running
is_container_running() {
    local container_name="${1:-satisfactory-server}"
    docker compose -f "$DOCKER_COMPOSE_FILE" ps "$container_name" 2>/dev/null | grep -q "Up"
}

# Check container health status
get_container_health() {
    local container_name="${1:-satisfactory-server}"
    docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown"
}

# Wait for container to become healthy
wait_for_healthy() {
    local container_name="${1:-satisfactory-server}"
    local max_attempts="${2:-30}"
    local attempt=0

    log "Waiting for $container_name to become healthy..."

    while [[ $attempt -lt $max_attempts ]]; do
        local health
        health=$(get_container_health "$container_name")

        if [[ "$health" == "healthy" ]]; then
            log "Container $container_name is healthy"
            return 0
        fi

        attempt=$((attempt + 1))
        log "Health check attempt $attempt/$max_attempts (status: $health)..."
        sleep 2
    done

    log_warn "Container did not become healthy within timeout"
    return 1
}

# =============================================================================
# Discord Notifications
# =============================================================================

# Send Discord notification via webhook
send_discord_notification() {
    local title="$1"
    local message="$2"
    local color="${3:-3447003}"  # Default: blue

    local webhook_url
    webhook_url=$(get_env "DISCORD_WEBHOOK_URL")

    # Skip if no webhook configured
    if [[ -z "$webhook_url" ]] || [[ "$webhook_url" == "your_discord_webhook_url_here" ]]; then
        return 0
    fi

    local embed
    embed=$(cat <<EOF
{
    "embeds": [{
        "title": "$title",
        "description": "$message",
        "color": $color,
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    }]
}
EOF
)

    curl -s -H "Content-Type: application/json" -d "$embed" "$webhook_url" > /dev/null || true
}

# Discord color constants
DISCORD_GREEN=3066993
DISCORD_RED=15158332
DISCORD_YELLOW=15844367
DISCORD_BLUE=3447003

# =============================================================================
# Server Operations
# =============================================================================

# Check if game port is responding
check_game_port() {
    local port="${1:-7777}"
    timeout 3 bash -c "echo > /dev/tcp/localhost/$port" 2>/dev/null
}

# =============================================================================
# Backup Utilities
# =============================================================================

# Create a backup with timestamp
create_backup_archive() {
    local backup_name="$1"
    local backup_type="${2:-daily}"
    local timestamp
    timestamp=$(date '+%Y%m%d-%H%M%S')

    local backup_file
    if [[ "$backup_type" == "weekly" ]]; then
        backup_file="${BACKUP_DIR}/${backup_name}-weekly-$(date '+%Y%m%d').tar.gz"
    else
        backup_file="${BACKUP_DIR}/${backup_name}-${timestamp}.tar.gz"
    fi

    echo "$backup_file"
}

# =============================================================================
# Dependency Checking
# =============================================================================

# Check if required commands are available
check_dependencies() {
    local deps=("$@")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done

    if [[ ${#missing[@]} -ne 0 ]]; then
        print_error "Missing dependencies: ${missing[*]}"
        return 1
    fi

    return 0
}

# =============================================================================
# Initialization
# =============================================================================

# Full initialization (call this at script start)
init_common() {
    init_paths
    init_docker
    load_env 2>/dev/null || true
}
