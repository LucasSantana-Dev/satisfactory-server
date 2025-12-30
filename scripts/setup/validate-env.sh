#!/bin/bash
# Environment Validation Script
# Validates that all required environment variables are set

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common

print_header "Environment Validation"

# Track validation status
ERRORS=0
WARNINGS=0

# Required variables (server will fail without these)
REQUIRED_VARS=(
    "CLOUDFLARE_TUNNEL_TOKEN"
)

# Optional but recommended variables
RECOMMENDED_VARS=(
    "DISCORD_WEBHOOK_URL"
    "MAXPLAYERS"
    "MEMORY_LIMIT"
)

# SFTP-specific variables (only required if using SFTP)
SFTP_VARS=(
    "SFTP_PASSWORD"
    "SFTP_USER"
    "SFTP_PORT"
)

# Load .env if it exists
ENV_FILE="${PROJECT_DIR}/.env"

if [[ ! -f "$ENV_FILE" ]]; then
    print_error ".env file not found!"
    echo "Run './setup.sh' to create one from .env.example"
    exit 1
fi

print_info "Loading environment from: $ENV_FILE"
echo ""

# Source the .env file to get variables
set -a
source "$ENV_FILE"
set +a

# Validate required variables
print_info "Checking required variables..."
for var in "${REQUIRED_VARS[@]}"; do
    value="${!var}"

    if [[ -z "$value" ]]; then
        print_error "$var is not set (REQUIRED)"
        ((ERRORS++))
    elif [[ "$value" == "your_"* ]] || [[ "$value" == "changeme"* ]]; then
        print_error "$var has placeholder value (REQUIRED)"
        ((ERRORS++))
    else
        # Mask the value for security
        masked="${value:0:8}..."
        print_success "$var is configured ($masked)"
    fi
done

echo ""

# Validate recommended variables
print_info "Checking recommended variables..."
for var in "${RECOMMENDED_VARS[@]}"; do
    value="${!var}"

    if [[ -z "$value" ]]; then
        print_warn "$var is not set (optional)"
        ((WARNINGS++))
    elif [[ "$value" == "your_"* ]]; then
        print_warn "$var has placeholder value (optional)"
        ((WARNINGS++))
    else
        print_success "$var is configured"
    fi
done

echo ""

# Check SFTP configuration
print_info "Checking SFTP configuration..."
if [[ -n "$SFTP_PASSWORD" ]] && [[ "$SFTP_PASSWORD" != "changeme" ]]; then
    print_success "SFTP is configured"

    # Check password strength (basic check)
    if [[ ${#SFTP_PASSWORD} -lt 12 ]]; then
        print_warn "SFTP_PASSWORD is short (< 12 chars) - consider a stronger password"
        ((WARNINGS++))
    fi
else
    print_warn "SFTP is not configured (disabled by default)"
    echo "   To enable: Set SFTP_PASSWORD and run: docker compose --profile sftp up -d"
fi

echo ""

# Check for common security issues
print_info "Security checks..."

# Check if secrets are in .env.example format
if grep -q "your_tunnel_token_here" "$ENV_FILE" 2>/dev/null; then
    print_error "Found placeholder 'your_tunnel_token_here' in .env"
    ((ERRORS++))
fi

if grep -q "your_discord_webhook_url_here" "$ENV_FILE" 2>/dev/null; then
    print_warn "Discord webhook has placeholder value"
    ((WARNINGS++))
fi

# Check .gitignore includes .env
GITIGNORE="${PROJECT_DIR}/.gitignore"
if [[ -f "$GITIGNORE" ]]; then
    if grep -q "^\.env$" "$GITIGNORE" || grep -q "^\.env\*" "$GITIGNORE"; then
        print_success ".env is in .gitignore"
    else
        print_error ".env is NOT in .gitignore - secrets may be exposed!"
        ((ERRORS++))
    fi
fi

echo ""

# Validate port configuration
print_info "Checking port configuration..."
SERVER_GAME_PORT="${SERVER_GAME_PORT:-7777}"
SERVER_MESSAGING_PORT="${SERVER_MESSAGING_PORT:-8888}"

# Check if ports are in valid range
for port_var in SERVER_GAME_PORT SERVER_MESSAGING_PORT SERVER_QUERY_PORT SERVER_BEACON_PORT SFTP_PORT; do
    port="${!port_var}"
    if [[ -n "$port" ]]; then
        if [[ "$port" -lt 1 ]] || [[ "$port" -gt 65535 ]]; then
            print_error "$port_var has invalid value: $port"
            ((ERRORS++))
        elif [[ "$port" -lt 1024 ]]; then
            print_warn "$port_var uses privileged port $port (requires root)"
            ((WARNINGS++))
        else
            print_success "$port_var: $port"
        fi
    fi
done

echo ""

# Validate memory configuration
print_info "Checking resource configuration..."
MEMORY_LIMIT="${MEMORY_LIMIT:-8G}"
MEMORY_RESERVATION="${MEMORY_RESERVATION:-4G}"

# Extract numeric value
mem_limit_num=$(echo "$MEMORY_LIMIT" | sed 's/[^0-9]//g')
mem_reserve_num=$(echo "$MEMORY_RESERVATION" | sed 's/[^0-9]//g')

if [[ "$mem_limit_num" -lt 4 ]]; then
    print_warn "MEMORY_LIMIT ($MEMORY_LIMIT) is low - recommend at least 8G"
    ((WARNINGS++))
else
    print_success "MEMORY_LIMIT: $MEMORY_LIMIT"
fi

if [[ "$mem_reserve_num" -gt "$mem_limit_num" ]]; then
    print_error "MEMORY_RESERVATION ($MEMORY_RESERVATION) is greater than MEMORY_LIMIT ($MEMORY_LIMIT)"
    ((ERRORS++))
else
    print_success "MEMORY_RESERVATION: $MEMORY_RESERVATION"
fi

# Summary
print_header "Validation Summary"

if [[ $ERRORS -gt 0 ]]; then
    print_error "Validation failed with $ERRORS error(s) and $WARNINGS warning(s)"
    echo ""
    echo "Fix the errors above before starting the server."
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    print_warn "Validation passed with $WARNINGS warning(s)"
    echo ""
    echo "Server can start, but consider fixing the warnings."
    exit 0
else
    print_success "All validations passed!"
    echo ""
    echo "Environment is properly configured."
    exit 0
fi
