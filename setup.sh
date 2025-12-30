#!/bin/bash
# Satisfactory Server Setup Script
# Initial setup and environment validation

set -e

# Source common library if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${SCRIPT_DIR}/scripts/lib/common.sh" ]]; then
    source "${SCRIPT_DIR}/scripts/lib/common.sh"
    init_paths
    HAS_COMMON=true
else
    HAS_COMMON=false
    # Fallback colors
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
fi

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║           Satisfactory Dedicated Server Setup                 ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_env_file() {
    echo -e "${BLUE}Checking environment configuration...${NC}"

    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            echo -e "${YELLOW}Creating .env from .env.example...${NC}"
            cp .env.example .env
            echo -e "${GREEN}✓ .env file created${NC}"
            echo ""
            echo -e "${YELLOW}⚠ IMPORTANT: Edit .env and configure required values:${NC}"
            echo "   - CLOUDFLARE_TUNNEL_TOKEN (required)"
            echo "   - SFTP_PASSWORD (if using SFTP)"
            echo "   - DISCORD_WEBHOOK_URL (optional, for notifications)"
            echo ""
        else
            echo -e "${RED}✗ .env.example not found${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ .env file exists${NC}"
    fi
}

validate_secrets() {
    echo -e "${BLUE}Validating secrets...${NC}"

    local has_errors=false

    # Check Cloudflare token
    if grep -q "^CLOUDFLARE_TUNNEL_TOKEN=$" .env 2>/dev/null || \
       grep -q "^CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token_here" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠ CLOUDFLARE_TUNNEL_TOKEN not configured${NC}"
        echo "   Get token from: https://one.dash.cloudflare.com/ > Networks > Tunnels"
        has_errors=true
    else
        echo -e "${GREEN}✓ CLOUDFLARE_TUNNEL_TOKEN is configured${NC}"
    fi

    # Check SFTP password if user intends to use SFTP
    if grep -q "^SFTP_PASSWORD=$" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠ SFTP_PASSWORD not set (SFTP disabled by default)${NC}"
        echo "   To enable SFTP: Set password and run: docker compose --profile sftp up -d"
    fi

    # Check Discord webhook (optional)
    if grep -q "^DISCORD_WEBHOOK_URL=$" .env 2>/dev/null || \
       grep -q "^DISCORD_WEBHOOK_URL=your_discord_webhook_url_here" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠ DISCORD_WEBHOOK_URL not configured (notifications disabled)${NC}"
    else
        if grep -q "^DISCORD_WEBHOOK_URL=" .env 2>/dev/null; then
            echo -e "${GREEN}✓ DISCORD_WEBHOOK_URL is configured${NC}"
        fi
    fi

    if [[ "$has_errors" == true ]]; then
        echo ""
        echo -e "${YELLOW}Some required secrets are not configured.${NC}"
        echo -e "${YELLOW}Server may not start correctly until configured.${NC}"
    fi
}

create_directories() {
    echo -e "${BLUE}Creating data directories...${NC}"

    mkdir -p data/backups data/saved data/gamefiles data/logs
    echo -e "${GREEN}✓ Data directories created${NC}"
}

check_docker() {
    echo -e "${BLUE}Checking Docker installation...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed${NC}"
        echo "   Install Docker: https://docs.docker.com/engine/install/"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is installed${NC}"

    if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Docker Compose is not installed${NC}"
        echo "   Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        echo -e "${RED}✗ Docker daemon is not running${NC}"
        echo "   Start Docker: sudo systemctl start docker"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker daemon is running${NC}"
}

check_resources() {
    echo -e "${BLUE}Checking system resources...${NC}"

    # Check available memory
    local available_mem
    available_mem=$(free -g | awk '/^Mem:/{print $7}')
    if [[ "$available_mem" -lt 8 ]]; then
        echo -e "${YELLOW}⚠ Less than 8GB RAM available (found ${available_mem}GB)${NC}"
        echo "   Server may experience performance issues"
    else
        echo -e "${GREEN}✓ Sufficient memory available (${available_mem}GB free)${NC}"
    fi

    # Check disk space
    local available_disk
    available_disk=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ "${available_disk%.*}" -lt 10 ]]; then
        echo -e "${YELLOW}⚠ Less than 10GB disk space available (found ${available_disk}GB)${NC}"
    else
        echo -e "${GREEN}✓ Sufficient disk space available (${available_disk}GB)${NC}"
    fi
}

show_next_steps() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                       Next Steps                              ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "1. Configure required secrets in .env:"
    echo "   - CLOUDFLARE_TUNNEL_TOKEN"
    echo ""
    echo "2. Configure Cloudflare Tunnel:"
    echo "   - Go to: https://one.dash.cloudflare.com/"
    echo "   - Create tunnel and copy token"
    echo "   - Configure private network routing"
    echo ""
    echo "3. Start the server:"
    echo -e "   ${GREEN}make start${NC}  or  ${GREEN}docker compose up -d${NC}"
    echo ""
    echo "4. Check status:"
    echo -e "   ${GREEN}make status${NC}  or  ${GREEN}docker compose ps${NC}"
    echo ""
    echo "5. View logs:"
    echo -e "   ${GREEN}make logs${NC}  or  ${GREEN}docker compose logs -f${NC}"
    echo ""
    echo -e "For detailed instructions, see: ${YELLOW}README.md${NC}"
    echo -e "For Cloudflare setup, see: ${YELLOW}docs/CLOUDFLARE_ZERO_TRUST.md${NC}"
    echo ""
}

main() {
    print_banner

    check_env_file
    echo ""

    validate_secrets
    echo ""

    create_directories
    echo ""

    check_docker
    echo ""

    check_resources
    echo ""

    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Setup Complete!                            ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"

    show_next_steps
}

main "$@"
