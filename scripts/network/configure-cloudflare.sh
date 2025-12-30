#!/bin/bash
# Cloudflare Zero Trust Configuration Helper Script
# This script helps configure Cloudflare Zero Trust for Satisfactory server

set -euo pipefail

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common

# Configuration
DOCKER_NETWORK_CIDR="172.19.0.0/16"
TUNNEL_NAME="satisfactory-server"
ZERO_TRUST_DASHBOARD="https://one.dash.cloudflare.com/"

print_header "Cloudflare Zero Trust Configuration Helper"

# Check if required tools are available
check_cloudflare_dependencies() {
    local missing_deps=()

    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi

    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi

    if [[ ${#missing_deps[@]} -ne 0 ]]; then
        print_warn "Missing dependencies: ${missing_deps[*]}"
        echo "Some features may not work without these tools."
        return 1
    fi

    return 0
}

# Extract tunnel information from token
get_tunnel_info() {
    local env_file="${PROJECT_DIR}/.env"

    if [[ ! -f "$env_file" ]]; then
        print_error ".env file not found"
        return 1
    fi

    local token
    token=$(grep "CLOUDFLARE_TUNNEL_TOKEN" "$env_file" | cut -d'=' -f2 | tr -d '"' | tr -d "'")

    if [[ -z "$token" ]]; then
        print_error "CLOUDFLARE_TUNNEL_TOKEN not found in .env"
        return 1
    fi

    print_success "Tunnel token found"
    print_info "Tunnel token (first 20 chars): ${token:0:20}..."
    echo ""

    return 0
}

# Check Docker network
check_docker_network() {
    print_info "Checking Docker network configuration..."

    if ! docker network inspect satisfactory-server_satisfactory-network &> /dev/null; then
        print_warn "Docker network not found"
        echo "Network should be: satisfactory-server_satisfactory-network"
        return 1
    fi

    local network_info
    network_info=$(docker network inspect satisfactory-server_satisfactory-network --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
    print_success "Docker network found"
    print_info "Network subnet: ${network_info}"
    print_info "Expected CIDR: ${DOCKER_NETWORK_CIDR}"
    echo ""

    return 0
}

# Display configuration checklist
show_checklist() {
    print_header "Configuration Checklist"
    echo "Complete these steps in the Cloudflare Zero Trust Dashboard:"
    echo ""
    echo -e "1. ${YELLOW}Create/Verify Zero Trust Organization${NC}"
    echo "   - Go to: ${ZERO_TRUST_DASHBOARD}"
    echo "   - Navigate to: Settings > Account"
    echo "   - Note your Team Domain (e.g., luk-homeserver.cloudflareaccess.com)"
    echo ""
    echo -e "2. ${YELLOW}Configure Private Network Routing${NC}"
    echo "   - Go to: Networks > Tunnels > Your tunnel"
    echo "   - Click: Private Network tab"
    echo "   - Add CIDR: ${DOCKER_NETWORK_CIDR}"
    echo "   - Description: Satisfactory Docker Network"
    echo ""
    echo -e "3. ${YELLOW}Configure WARP Enrollment${NC}"
    echo "   - Go to: Settings > WARP Client"
    echo "   - Click: Add a rule"
    echo "   - Rule name: Satisfactory Players"
    echo "   - Selector: Emails or One-time PIN"
    echo "   - Add friend emails or generate PIN"
    echo ""
    echo -e "4. ${YELLOW}Verify Configuration${NC}"
    echo "   - Check tunnel status shows: Healthy and Connected"
    echo "   - Verify private network appears in tunnel config"
    echo "   - Test friend enrollment"
    echo ""
    print_success "For detailed instructions, see: CLOUDFLARE_ZERO_TRUST_SETUP.md"
    echo ""
}

# Display connection information for friends
show_connection_info() {
    print_header "Connection Information for Friends"
    echo "Share this information with your friends:"
    echo ""
    print_success "Server Connection Details:"
    echo "  - IP Address: ${YELLOW}172.19.0.2${NC}"
    echo "  - Port: ${YELLOW}7777${NC}"
    echo "  - Protocol: TCP/UDP"
    echo ""
    print_success "Required Steps:"
    echo "  1. Install Cloudflare WARP client"
    echo "  2. Enroll device using team domain or PIN"
    echo "  3. Connect to server using IP: 172.19.0.2:7777"
    echo ""
    print_info "Friend Guide: Share FRIEND_GUIDE.md with your friends"
    echo ""
}

# Main execution
main() {
    print_info "Starting configuration check..."
    echo ""

    # Check dependencies
    check_cloudflare_dependencies || true

    # Get tunnel info
    get_tunnel_info || true

    # Check Docker network
    check_docker_network || true

    # Show checklist
    show_checklist

    # Show connection info
    show_connection_info

    print_success "=== Next Steps ==="
    echo "1. Complete the checklist above in Cloudflare dashboard"
    echo "2. Share FRIEND_GUIDE.md with your friends"
    echo "3. Test connection after Zero Trust is configured"
    echo ""
    print_info "Dashboard URL: ${ZERO_TRUST_DASHBOARD}"
    echo ""
}

main
