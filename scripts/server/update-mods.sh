#!/bin/bash
# Satisfactory Server Mod Update Script
# Safely updates mods with server restart and Discord notifications

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common
set_log_file "${LOGS_DIR}/update-mods.log"

# Mod installation script
MOD_INSTALL_SCRIPT="${SCRIPTS_DIR}/mods/install.py"

# Clear existing mods (except SML which is managed separately)
clear_mods() {
    log "Clearing existing mods..."

    if [[ -d "$MODS_DIR" ]]; then
        # Remove all mod directories except SML
        find "$MODS_DIR" -mindepth 1 -maxdepth 1 -type d ! -name "SML" -exec rm -rf {} \; 2>/dev/null || true
        # Remove loose .pak files (shouldn't exist but clean up anyway)
        find "$MODS_DIR" -maxdepth 1 -name "*.pak" -type f -delete 2>/dev/null || true
        log "Existing mods cleared"
    else
        log "Mods directory does not exist, creating..."
        mkdir -p "$MODS_DIR"
    fi
}

# Install latest mods
install_mods() {
    log "Installing latest mods..."

    if [[ ! -f "$MOD_INSTALL_SCRIPT" ]]; then
        log_error "Mod install script not found: $MOD_INSTALL_SCRIPT"
        return 1
    fi

    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is required but not installed"
        return 1
    fi

    cd "$PROJECT_DIR"
    if python3 "$MOD_INSTALL_SCRIPT"; then
        log_success "Mods installed successfully"
        return 0
    else
        log_error "Mod installation failed"
        return 1
    fi
}

# Count installed mods
count_mods() {
    if [[ -d "$MODS_DIR" ]]; then
        find "$MODS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l
    else
        echo "0"
    fi
}

# Main update function
main() {
    log "=== Mod Update Script Started ==="

    local server_was_running=false
    local start_time
    start_time=$(date +%s)

    # Check if server is currently running (use service name, not container name)
    if is_container_running "satisfactory"; then
        server_was_running=true
        log "Server is currently running"
    else
        log "Server is not running"
    fi

    # Send notification: Server going down
    if [[ "$server_was_running" == true ]]; then
        send_discord_notification "🔧 Mod Update Starting" \
            "Server is going offline for mod updates.\nGame will auto-save before shutdown." \
            "$DISCORD_YELLOW"

        # Stop server gracefully (triggers AUTOSAVEONDISCONNECT)
        log "Stopping server gracefully..."
        cd "$PROJECT_DIR"
        if docker compose stop satisfactory; then
            log "Server stopped successfully"
            # Give it a moment to fully stop
            sleep 5
        else
            log_error "Failed to stop server"
            send_discord_notification "❌ Mod Update Failed" \
                "Failed to stop server. Update aborted." \
                "$DISCORD_RED"
            exit 1
        fi
    fi

    # Clear and reinstall mods
    clear_mods

    if ! install_mods; then
        log_error "Mod installation failed"
        send_discord_notification "❌ Mod Update Failed" \
            "Mod installation failed. Server may need manual intervention." \
            "$DISCORD_RED"

        # Try to start the server anyway if it was running
        if [[ "$server_was_running" == true ]]; then
            log "Attempting to restart server despite mod failure..."
            cd "$PROJECT_DIR"
            docker compose up -d satisfactory || true
        fi
        exit 1
    fi

    local mod_count
    mod_count=$(count_mods)
    log "Total mods installed: $mod_count"

    # Start server if it was running (or start anyway for cron job)
    log "Starting server..."
    cd "$PROJECT_DIR"
    if docker compose up -d satisfactory; then
        log "Server start command issued"
    else
        log_error "Failed to start server"
        send_discord_notification "❌ Mod Update Failed" \
            "Mods updated but failed to start server. Manual intervention required!" \
            "$DISCORD_RED"
        exit 1
    fi

    # Wait for health check
    if wait_for_healthy "satisfactory-server" 60; then
        local end_time
        end_time=$(date +%s)
        local duration=$((end_time - start_time))

        log_success "Mod update completed successfully!"
        send_discord_notification "✅ Server Online" \
            "Mod update completed successfully!\n**Mods installed:** ${mod_count}\n**Downtime:** ${duration} seconds\nServer is healthy and ready to play." \
            "$DISCORD_GREEN"
    else
        log_warn "Server started but health check failed"
        send_discord_notification "⚠️ Server Status Unknown" \
            "Mods updated (${mod_count} installed) but health check failed.\nServer may still be starting up - please verify manually." \
            "$DISCORD_YELLOW"
    fi

    log "=== Mod Update Script Completed ==="
}

main "$@"
