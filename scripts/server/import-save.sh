#!/bin/bash
# Satisfactory Save Import Script
# Imports a local save file to the server

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common

# Save server directory
SERVER_SAVE_DIR="${SAVE_DIR}/server"

print_header "Satisfactory Save Import Tool"

# Check if save file is provided
if [[ $# -eq 0 ]]; then
    print_warn "Usage: $0 <path-to-save-file.sav> [save-name]"
    echo ""
    print_info "Example:"
    echo "  $0 ~/Downloads/MySave.sav"
    echo "  $0 ~/Downloads/MySave.sav MyServerSave"
    echo ""
    print_info "Where to find your save files:"
    echo "  Windows: %LOCALAPPDATA%\\FactoryGame\\Saved\\SaveGames\\server\\"
    echo "  Linux:   ~/.config/Epic/FactoryGame/Saved/SaveGames/server/"
    echo "  macOS:   ~/Library/Application Support/Epic/FactoryGame/Saved/SaveGames/server/"
    exit 1
fi

SAVE_FILE="$1"
SAVE_NAME="${2:-$(basename "$SAVE_FILE" .sav)}"

# Validate save file exists
if [[ ! -f "$SAVE_FILE" ]]; then
    print_error "Save file not found: $SAVE_FILE"
    exit 1
fi

# Validate it's a .sav file
if [[ ! "$SAVE_FILE" =~ \.sav$ ]]; then
    print_warn "File doesn't have .sav extension"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if server is running
print_info "Checking server status..."
SERVER_WAS_RUNNING=false
if is_container_running "satisfactory-server"; then
    print_warn "Server is currently running"
    print_warn "It's recommended to stop the server before importing a save"
    read -p "Stop server now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping server..."
        docker compose -f "$DOCKER_COMPOSE_FILE" stop satisfactory-server
        SERVER_WAS_RUNNING=true
    else
        print_warn "Continuing with server running (not recommended)"
    fi
fi

# Create backup of existing saves
print_header "Creating Backup"
BACKUP_FILE="${BACKUP_DIR}/pre-import-$(date +%Y%m%d-%H%M%S).tar.gz"
if [[ -d "$SERVER_SAVE_DIR" ]] && [[ "$(ls -A "$SERVER_SAVE_DIR" 2>/dev/null)" ]]; then
    if tar -czf "$BACKUP_FILE" -C "$PROJECT_DIR" data/saved/server 2>/dev/null; then
        print_success "Backup created: $(basename "$BACKUP_FILE")"
    else
        print_warn "Backup creation failed (continuing anyway)"
    fi
else
    print_warn "No existing saves to backup"
fi

# Create save directory
mkdir -p "$SERVER_SAVE_DIR"

# Copy save file
print_header "Importing Save"
FINAL_SAVE_NAME="${SAVE_NAME}.sav"
FINAL_SAVE_PATH="${SERVER_SAVE_DIR}/${FINAL_SAVE_NAME}"

if cp "$SAVE_FILE" "$FINAL_SAVE_PATH"; then
    print_success "Save file imported successfully"
    echo "   Source: $SAVE_FILE"
    echo "   Destination: $FINAL_SAVE_PATH"

    # Set proper permissions
    chmod 644 "$FINAL_SAVE_PATH"

    # Get file size
    SIZE=$(du -h "$FINAL_SAVE_PATH" | cut -f1)
    echo "   Size: $SIZE"
else
    print_error "Failed to import save file"
    exit 1
fi

# Restart server if it was running
if [[ "$SERVER_WAS_RUNNING" == true ]]; then
    print_info "Starting server..."
    docker compose -f "$DOCKER_COMPOSE_FILE" start satisfactory-server
    print_success "Server started"
fi

# Summary
print_header "Import Complete"
print_success "Save file imported: ${FINAL_SAVE_NAME}"
echo ""
print_warn "Important Notes:"
echo "  1. The save file is now in: ${SERVER_SAVE_DIR}"
echo "  2. If server was running, it has been restarted"
echo "  3. Backup of old saves: ${BACKUP_FILE}"
echo "  4. You may need to configure the save in server settings"
echo ""
print_info "Next Steps:"
echo "  1. Start server if not running: docker compose up -d"
echo "  2. Check server logs: docker compose logs satisfactory"
echo "  3. The save should appear in the server's save list"
