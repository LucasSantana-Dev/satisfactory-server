#!/bin/bash
# Satisfactory Server Update Script
# Safely updates the server with backup and rollback capability

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common
set_log_file "${LOGS_DIR}/update.log"

# Main update function
main() {
    log "=== Update Script Started ==="

    local server_was_running=false

    # Check if server is currently running
    if is_container_running "satisfactory-server"; then
        server_was_running=true
        log "Server is currently running, will restart after update"
    else
        log "Server is not running, will start after update"
    fi

    # Create backup before update
    log "Creating backup before update..."
    local backup_script="${SCRIPTS_DIR}/server/backup.sh"
    if [[ -f "$backup_script" ]]; then
        "$backup_script" || {
            log_error "Backup failed! Aborting update."
            send_discord_notification "❌ Update Aborted" \
                "Update failed: Backup could not be created. Server remains unchanged." \
                "$DISCORD_RED"
            exit 1
        }
    else
        log_warn "backup.sh not found, skipping backup"
    fi

    # Stop server if running
    if [[ "$server_was_running" == true ]]; then
        log "Stopping server..."
        cd "$PROJECT_DIR"
        docker compose stop satisfactory-server || {
            log_error "Failed to stop server"
            send_discord_notification "❌ Update Failed" \
                "Failed to stop server. Update aborted." \
                "$DISCORD_RED"
            exit 1
        }
        sleep 2
    fi

    # Pull latest image
    log "Pulling latest Satisfactory server image..."
    cd "$PROJECT_DIR"
    if docker compose pull satisfactory-server; then
        log "Image pulled successfully"
    else
        log_error "Failed to pull image"
        send_discord_notification "❌ Update Failed" \
            "Failed to pull latest image. Server remains on previous version." \
            "$DISCORD_RED"
        exit 1
    fi

    # Start server
    log "Starting server with new image..."
    cd "$PROJECT_DIR"
    if docker compose up -d satisfactory-server; then
        log "Server started successfully"
    else
        log_error "Failed to start server"
        send_discord_notification "❌ Update Failed" \
            "Failed to start server after update. Manual intervention required!" \
            "$DISCORD_RED"
        exit 1
    fi

    # Wait for health check
    if wait_for_healthy "satisfactory-server" 30; then
        log_success "Update completed successfully!"

        # Get new image version
        local image_id
        image_id=$(docker inspect --format='{{.Id}}' wolveix/satisfactory-server:latest 2>/dev/null | cut -c1-12 || echo "unknown")

        send_discord_notification "✅ Update Completed" \
            "Satisfactory server updated successfully!\nImage ID: \`${image_id}\`\nServer is healthy and running." \
            "$DISCORD_GREEN"
    else
        log_warn "Update completed but server health check failed"
        send_discord_notification "⚠️ Update Completed with Warnings" \
            "Server updated but health check failed. Please verify server status manually." \
            "$DISCORD_YELLOW"
    fi

    log "=== Update Script Completed ==="
}

main "$@"
