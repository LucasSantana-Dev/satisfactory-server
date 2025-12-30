#!/bin/bash
# Satisfactory Server Monitoring Script
# Monitors server health and sends Discord notifications

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common
set_log_file "${LOGS_DIR}/monitor.log"

# State management
STATE_FILE="${LOGS_DIR}/monitor.state"
COOLDOWN_FILE="${LOGS_DIR}/monitor.cooldown"
COOLDOWN_SECONDS=300

# Get server game port from env
SERVER_GAME_PORT=$(get_env "SERVER_GAME_PORT" "7777")

# Read previous state
read_state() {
    if [[ -f "$STATE_FILE" ]]; then
        cat "$STATE_FILE"
    else
        echo "unknown"
    fi
}

# Write current state
write_state() {
    echo "$1" > "$STATE_FILE"
}

# Check if we're in cooldown period
is_in_cooldown() {
    if [[ ! -f "$COOLDOWN_FILE" ]]; then
        return 1
    fi

    local cooldown_time
    cooldown_time=$(cat "$COOLDOWN_FILE")
    local current_time
    current_time=$(date +%s)
    local elapsed=$((current_time - cooldown_time))

    [[ $elapsed -lt $COOLDOWN_SECONDS ]]
}

# Update cooldown timestamp
update_cooldown() {
    date +%s > "$COOLDOWN_FILE"
}

# Main monitoring function
main() {
    log "=== Health Check Started ==="

    local previous_state
    previous_state=$(read_state)
    local current_state="unknown"
    local container_running=false
    local port_responding=false
    local health_ok=false

    # Check container status
    if is_container_running "satisfactory-server"; then
        container_running=true
        log "Container is running"

        # Check health status
        local health
        health=$(get_container_health "satisfactory-server")
        if [[ "$health" == "healthy" ]] || [[ "$health" == "" ]]; then
            health_ok=true
            log "Container health check passed"
        else
            log_warn "Container health check failed (status: $health)"
        fi

        # Check port
        if check_game_port "$SERVER_GAME_PORT"; then
            port_responding=true
            log "Port ${SERVER_GAME_PORT} is responding"
        else
            log_warn "Port ${SERVER_GAME_PORT} is not responding"
        fi

        # Determine overall state
        if [[ "$container_running" == true ]] && [[ "$port_responding" == true ]]; then
            current_state="up"
        elif [[ "$container_running" == true ]]; then
            current_state="degraded"
        else
            current_state="down"
        fi
    else
        log_error "Container is not running"
        current_state="down"
    fi

    # Handle state changes
    if [[ "$previous_state" != "$current_state" ]]; then
        log "State changed: $previous_state -> $current_state"
        write_state "$current_state"

        case "$current_state" in
            "up")
                if [[ "$previous_state" == "down" ]] || [[ "$previous_state" == "degraded" ]]; then
                    log "Server recovered! Sending notification..."
                    send_discord_notification "✅ Server Recovered" \
                        "Satisfactory server is now online and responding on port ${SERVER_GAME_PORT}" \
                        "$DISCORD_GREEN"
                    update_cooldown
                fi
                ;;
            "degraded")
                if ! is_in_cooldown; then
                    log "Server is degraded! Sending notification..."
                    send_discord_notification "⚠️ Server Degraded" \
                        "Container is running but port ${SERVER_GAME_PORT} is not responding. Check server logs." \
                        "$DISCORD_YELLOW"
                    update_cooldown
                else
                    log "Server degraded but in cooldown period, skipping notification"
                fi
                ;;
            "down")
                if ! is_in_cooldown; then
                    log "Server is down! Sending notification..."
                    send_discord_notification "🔴 Server Down" \
                        "Satisfactory server container is not running. Immediate attention required!" \
                        "$DISCORD_RED"
                    update_cooldown
                else
                    log "Server down but in cooldown period, skipping notification"
                fi
                ;;
        esac
    else
        log "State unchanged: $current_state"
    fi

    log "=== Health Check Completed ==="
    log "Status: $current_state (Container: $container_running, Port: $port_responding, Health: $health_ok)"
}

main "$@"
