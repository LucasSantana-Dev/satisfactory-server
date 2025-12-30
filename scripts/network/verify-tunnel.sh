#!/bin/bash
# Cloudflare Tunnel Verification Script
# Verifies that the tunnel is working and friends can connect

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common

DOMAIN="satisfactory.luk-homeserver.com.br"

print_header "Cloudflare Tunnel Verification"

# Check if containers are running
print_info "1. Checking container status..."
if is_container_running "satisfactory-server"; then
    print_success "Satisfactory server container is running"
else
    print_error "Satisfactory server container is NOT running"
    exit 1
fi

if docker compose -f "$DOCKER_COMPOSE_FILE" ps cloudflared | grep -q "Up"; then
    print_success "Cloudflared tunnel container is running"
else
    print_error "Cloudflared tunnel container is NOT running"
    exit 1
fi

# Check tunnel logs
echo ""
print_info "2. Checking tunnel connection status..."
TUNNEL_LOGS=$(docker compose -f "$DOCKER_COMPOSE_FILE" logs cloudflared --tail 50 2>/dev/null)

if echo "$TUNNEL_LOGS" | grep -q "Registered tunnel connection"; then
    CONNECTION_COUNT=$(echo "$TUNNEL_LOGS" | grep -c "Registered tunnel connection" || echo "0")
    print_success "Tunnel is connected (${CONNECTION_COUNT} connection(s) registered)"
else
    print_error "No tunnel connections found"
    print_warn "Check tunnel logs: docker compose logs cloudflared"
fi

# Check WARP routing
if echo "$TUNNEL_LOGS" | grep -q '"warp-routing":{"enabled":true}'; then
    print_success "WARP routing is enabled"
else
    print_warn "WARP routing status unclear from logs"
fi

# Check server health
echo ""
print_info "3. Checking server health..."
HEALTH=$(get_container_health "satisfactory-server")
if [[ "$HEALTH" == "healthy" ]]; then
    print_success "Server is healthy"
elif [[ "$HEALTH" == "" ]] || [[ "$HEALTH" == "unknown" ]]; then
    print_warn "Health check not configured (this is OK)"
else
    print_error "Server health: $HEALTH"
fi

# Check port connectivity
echo ""
print_info "4. Testing port connectivity..."
if check_game_port 7777; then
    print_success "Port 7777 (game) is responding"
else
    print_error "Port 7777 is not responding"
fi

if timeout 3 bash -c "echo > /dev/tcp/localhost/8888" 2>/dev/null; then
    print_success "Port 8888 (messaging) is responding"
else
    print_error "Port 8888 is not responding"
fi

# Get container IP
echo ""
print_info "5. Network information..."
CONTAINER_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' satisfactory-server 2>/dev/null || echo "172.19.0.2")
echo "   Container IP: ${CONTAINER_IP}"
echo "   Expected IP: 172.19.0.2 (if using default Docker network)"

# Check Cloudflare dashboard status
echo ""
print_info "6. Cloudflare Dashboard Check"
print_warn "   Manual verification required:"
echo "   1. Go to: https://one.dash.cloudflare.com/"
echo "   2. Navigate to: Networks > Tunnels"
echo "   3. Check tunnel status (should be HEALTHY)"
echo "   4. Verify private network route: 172.19.0.0/16"

# Summary
print_header "Verification Summary"
print_success "For friends to connect:"
echo "   1. Friends must install Cloudflare WARP client"
echo "   2. Friends must enroll in Zero Trust (team: luk-homelab)"
echo "   3. Friends connect using: ${DOMAIN}:7777 (recommended)"
echo "   4. Or fallback IP: ${CONTAINER_IP}:7777"
echo "   5. WARP must be connected while playing"
echo ""
print_warn "See FRIEND_GUIDE.md for detailed connection instructions"

echo ""
print_info "Quick Test Commands:"
echo "   Check tunnel logs: ${YELLOW}docker compose logs cloudflared --tail 50${NC}"
echo "   Check server logs: ${YELLOW}docker compose logs satisfactory --tail 50${NC}"
echo "   Test port: ${YELLOW}nc -zv localhost 7777${NC}"
