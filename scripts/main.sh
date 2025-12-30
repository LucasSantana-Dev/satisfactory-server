#!/bin/bash
# Satisfactory Server Management CLI
# Unified entry point for all server management operations

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# Initialize paths
init_common

VERSION="1.0.0"

# Show version
show_version() {
    echo "Satisfactory Server CLI v${VERSION}"
}

# Show usage
show_usage() {
    cat << EOF
${BLUE}Satisfactory Server Management CLI${NC}
Version: ${VERSION}

${BOLD}USAGE:${NC}
    $(basename "$0") <command> [subcommand] [options]

${BOLD}COMMANDS:${NC}
    ${GREEN}server${NC}      Server lifecycle management
        backup      Create a backup of server data
        update      Update server to latest version
        monitor     Run health check and monitoring
        import      Import a save file

    ${GREEN}mods${NC}        Mod management
        install     Install mods (automatic download)
        manual      Install mods manually from files
        list        Generate mod download list

    ${GREEN}network${NC}     Network and Cloudflare operations
        cloudflare  Configure Cloudflare Zero Trust
        verify      Verify tunnel connectivity

    ${GREEN}setup${NC}       One-time setup operations
        cron        Install cron jobs for backup/monitoring

    ${GREEN}help${NC}        Show this help message
    ${GREEN}version${NC}     Show version information

${BOLD}EXAMPLES:${NC}
    $(basename "$0") server backup           # Create backup
    $(basename "$0") server update           # Update server
    $(basename "$0") mods install            # Install mods
    $(basename "$0") mods manual ~/Downloads/*.pak  # Install local mods
    $(basename "$0") network verify          # Verify tunnel
    $(basename "$0") setup cron              # Install cron jobs

${BOLD}QUICK REFERENCE:${NC}
    Docker commands:
        docker compose up -d         # Start server
        docker compose down          # Stop server
        docker compose logs -f       # View logs
        docker compose restart       # Restart server

${BOLD}DOCUMENTATION:${NC}
    Server:     README.md
    Mods:       scripts/docs/MODS.md
    Cloudflare: CLOUDFLARE_ZERO_TRUST_SETUP.md
    Friends:    FRIEND_GUIDE.md
EOF
}

# Server commands
cmd_server() {
    local subcmd="${1:-}"
    shift || true

    case "$subcmd" in
        backup)
            exec "${SCRIPT_DIR}/server/backup.sh" "$@"
            ;;
        update)
            exec "${SCRIPT_DIR}/server/update.sh" "$@"
            ;;
        monitor)
            exec "${SCRIPT_DIR}/server/monitor.sh" "$@"
            ;;
        import)
            exec "${SCRIPT_DIR}/server/import-save.sh" "$@"
            ;;
        *)
            echo -e "${RED}Unknown server command: ${subcmd}${NC}"
            echo ""
            echo "Available commands:"
            echo "  backup    - Create a backup of server data"
            echo "  update    - Update server to latest version"
            echo "  monitor   - Run health check and monitoring"
            echo "  import    - Import a save file"
            exit 1
            ;;
    esac
}

# Mods commands
cmd_mods() {
    local subcmd="${1:-}"
    shift || true

    case "$subcmd" in
        install)
            exec "${SCRIPT_DIR}/mods/install.sh" "$@"
            ;;
        manual)
            exec "${SCRIPT_DIR}/mods/manual.sh" "$@"
            ;;
        list|generate)
            exec "${SCRIPT_DIR}/mods/generate-list.sh" "$@"
            ;;
        *)
            echo -e "${RED}Unknown mods command: ${subcmd}${NC}"
            echo ""
            echo "Available commands:"
            echo "  install   - Install mods (automatic download)"
            echo "  manual    - Install mods manually from files"
            echo "  list      - Generate mod download list"
            exit 1
            ;;
    esac
}

# Network commands
cmd_network() {
    local subcmd="${1:-}"
    shift || true

    case "$subcmd" in
        cloudflare|configure)
            exec "${SCRIPT_DIR}/network/configure-cloudflare.sh" "$@"
            ;;
        verify)
            exec "${SCRIPT_DIR}/network/verify-tunnel.sh" "$@"
            ;;
        *)
            echo -e "${RED}Unknown network command: ${subcmd}${NC}"
            echo ""
            echo "Available commands:"
            echo "  cloudflare - Configure Cloudflare Zero Trust"
            echo "  verify     - Verify tunnel connectivity"
            exit 1
            ;;
    esac
}

# Setup commands
cmd_setup() {
    local subcmd="${1:-}"
    shift || true

    case "$subcmd" in
        cron)
            exec "${SCRIPT_DIR}/setup/install-cron.sh" "$@"
            ;;
        *)
            echo -e "${RED}Unknown setup command: ${subcmd}${NC}"
            echo ""
            echo "Available commands:"
            echo "  cron - Install cron jobs for backup/monitoring"
            exit 1
            ;;
    esac
}

# Status command - quick overview
cmd_status() {
    print_header "Satisfactory Server Status"

    # Check server container
    echo -n "Server container: "
    if is_container_running "satisfactory-server"; then
        print_success "Running"
    else
        print_error "Stopped"
    fi

    # Check cloudflared
    echo -n "Cloudflared:      "
    if docker compose -f "$DOCKER_COMPOSE_FILE" ps cloudflared 2>/dev/null | grep -q "Up"; then
        print_success "Running"
    else
        print_error "Stopped"
    fi

    # Check game port
    echo -n "Game port (7777): "
    if check_game_port 7777; then
        print_success "Responding"
    else
        print_error "Not responding"
    fi

    # Count backups
    local backup_count
    backup_count=$(find "$BACKUP_DIR" -name "*.tar.gz" 2>/dev/null | wc -l)
    echo "Backups:          ${backup_count} files"

    # Count mods
    local mod_count
    mod_count=$(find "$MODS_DIR" -name "*.pak" 2>/dev/null | wc -l)
    echo "Installed mods:   ${mod_count} mods"

    echo ""
    print_info "For detailed info, run: docker compose logs -f"
}

# Main entry point
main() {
    local cmd="${1:-help}"
    shift || true

    case "$cmd" in
        server)
            cmd_server "$@"
            ;;
        mods)
            cmd_mods "$@"
            ;;
        network)
            cmd_network "$@"
            ;;
        setup)
            cmd_setup "$@"
            ;;
        status)
            cmd_status "$@"
            ;;
        help|--help|-h)
            show_usage
            ;;
        version|--version|-v)
            show_version
            ;;
        *)
            echo -e "${RED}Unknown command: ${cmd}${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
