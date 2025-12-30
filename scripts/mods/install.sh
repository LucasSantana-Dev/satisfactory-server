#!/bin/bash
# Satisfactory Mod Installation Script
# Automatically downloads and installs mods from ficsit.app
# Falls back to Python script if available for better download handling

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common
set_log_file "${LOGS_DIR}/mods-install.log"

# Configuration
MODS_CONFIG_DIR="${SCRIPTS_DIR}/mods/config"
MODS_LIST="${MODS_CONFIG_DIR}/mods-list.json"

print_header "Satisfactory Mod Installation Script"

# Create directories
mkdir -p "$MODS_DIR"
mkdir -p "$BACKUP_DIR"

# Check dependencies
check_install_dependencies() {
    check_dependencies curl jq || exit 1
}

# Create backup before mod installation
create_mod_backup() {
    log "Creating backup before mod installation..."
    local backup_name="pre-mods-$(date +%Y%m%d-%H%M%S).tar.gz"
    local backup_path="${BACKUP_DIR}/${backup_name}"

    if tar -czf "$backup_path" -C "$PROJECT_DIR" data/saved data/gamefiles/FactoryGame/Mods 2>/dev/null || \
       tar -czf "$backup_path" -C "$PROJECT_DIR" data/saved 2>/dev/null; then
        local size=$(du -h "$backup_path" | cut -f1)
        log "Backup created: $backup_name (Size: $size)"
        print_success "Backup created"
        return 0
    else
        log_warn "Backup creation failed, continuing anyway..."
        print_warn "Backup failed, continuing..."
        return 1
    fi
}

# Extract download URL from mod page
get_mod_download_url() {
    local mod_slug=$1
    local mod_url=$2
    local github_repo=$3

    log "Fetching download URL for ${mod_slug}..."

    local download_url=""

    # First, try GitHub releases API if GitHub repo is provided
    if [[ -n "$github_repo" ]] && [[ "$github_repo" != "null" ]]; then
        log "Trying GitHub releases for ${github_repo}..."
        download_url=$(curl -sL "https://api.github.com/repos/${github_repo}/releases/latest" 2>/dev/null | \
            jq -r '.assets[] | select(.name | endswith(".pak")) | .browser_download_url' 2>/dev/null | \
            head -1 || echo "")

        if [[ -n "$download_url" ]] && [[ "$download_url" != "null" ]]; then
            log "Found GitHub release URL: ${download_url}"
            echo "$download_url"
            return 0
        fi
    fi

    # Try to extract GitHub URL from mod page
    if [[ -z "$download_url" ]]; then
        local github_url
        github_url=$(curl -sL "$mod_url" 2>/dev/null | \
            grep -oP 'href="https://github.com/[^"]*"' | \
            head -1 | \
            sed 's/href="//;s/"$//' | \
            sed 's|/tree/.*||' | \
            sed 's|/blob/.*||' || echo "")

        if [[ -n "$github_url" ]]; then
            local repo
            repo=$(echo "$github_url" | sed 's|https://github.com/||')
            log "Found GitHub repo from page: ${repo}"
            download_url=$(curl -sL "https://api.github.com/repos/${repo}/releases/latest" 2>/dev/null | \
                jq -r '.assets[] | select(.name | endswith(".pak")) | .browser_download_url' 2>/dev/null | \
                head -1 || echo "")
        fi
    fi

    # Try to extract download link from mod page
    if [[ -z "$download_url" ]] || [[ "$download_url" == "null" ]]; then
        download_url=$(curl -sL "$mod_url" 2>/dev/null | \
            grep -oP 'href="[^"]*\.pak[^"]*"' | \
            head -1 | \
            sed 's/href="//;s/"$//' || echo "")
    fi

    # Make URL absolute if relative
    if [[ -n "$download_url" ]] && [[ "$download_url" != "null" ]] && [[ ! "$download_url" =~ ^https?:// ]]; then
        download_url="https://ficsit.app${download_url}"
    fi

    if [[ -z "$download_url" ]] || [[ "$download_url" == "null" ]]; then
        echo ""
    else
        echo "$download_url"
    fi
}

# Download mod file
download_mod() {
    local mod_name=$1
    local mod_slug=$2
    local mod_url=$3
    local github_repo=$4
    local output_file="${MODS_DIR}/${mod_slug}.pak"

    # Skip if already exists
    if [[ -f "$output_file" ]]; then
        log "Mod already installed: ${mod_name}"
        print_warn "${mod_name} already installed, skipping..."
        return 0
    fi

    log "Downloading ${mod_name} (${mod_slug})..."
    print_info "Downloading: ${mod_name}..."

    # Try to get download URL
    local download_url
    download_url=$(get_mod_download_url "$mod_slug" "$mod_url" "$github_repo")

    if [[ -z "$download_url" ]]; then
        log_warn "Could not find download URL for ${mod_name}"
        print_warn "Could not auto-download ${mod_name}"
        echo -e "   ${YELLOW}Please download manually from: ${mod_url}${NC}"
        echo -e "   ${YELLOW}Place the .pak file in: ${MODS_DIR}/${NC}"
        return 1
    fi

    log "Download URL: ${download_url}"

    # Download the file
    if curl -L -f -o "$output_file" "$download_url" 2>/dev/null; then
        # Verify it's a valid file (not empty, not HTML error page)
        if [[ -s "$output_file" ]] && ! file "$output_file" | grep -q "HTML"; then
            chmod 644 "$output_file"
            local size=$(du -h "$output_file" | cut -f1)
            log_success "Downloaded ${mod_name} (${size})"
            print_success "Downloaded: ${mod_name} (${size})"
            return 0
        else
            rm -f "$output_file"
            log_error "Downloaded file appears to be invalid for ${mod_name}"
            print_error "Invalid file downloaded for ${mod_name}"
            return 1
        fi
    else
        log_error "Download failed for ${mod_name}"
        print_error "Download failed: ${mod_name}"
        echo -e "   ${YELLOW}Please download manually from: ${mod_url}${NC}"
        return 1
    fi
}

# Install mods by category
install_mods_by_category() {
    local category=$1
    local priority=$2

    log "Installing mods: category=${category}, priority=${priority}"

    # Get mods filtered by category and priority
    local mods
    mods=$(jq -r ".mods[] | select(.category == \"${category}\" and .priority == ${priority}) | \"\(.name)|\(.slug)|\(.url)|\(.github // \"null\")\"" "$MODS_LIST")

    if [[ -z "$mods" ]]; then
        return 0
    fi

    print_header "Installing ${category} mods"

    while IFS='|' read -r name slug url github; do
        if [[ -n "$name" ]]; then
            download_mod "$name" "$slug" "$url" "$github"
        fi
    done <<< "$mods"
}

# Main installation function
main() {
    log "=== Mod Installation Started ==="

    # Try Python script first if available (better web scraping)
    if command -v python3 &> /dev/null && python3 -c "import requests" 2>/dev/null; then
        local python_script="${SCRIPTS_DIR}/mods/install.py"
        if [[ -f "$python_script" ]]; then
            print_info "Using Python script for better download handling..."
            python3 "$python_script"
            exit $?
        fi
    fi

    # Fall back to bash script
    check_install_dependencies

    # Check if mods list exists
    if [[ ! -f "$MODS_LIST" ]]; then
        print_error "Mods list not found: ${MODS_LIST}"
        exit 1
    fi

    # Create backup
    create_mod_backup

    print_header "Installing Mods"

    # Install in priority order
    install_mods_by_category "dependency" 1
    install_mods_by_category "quality-of-life" 2
    install_mods_by_category "content" 3
    install_mods_by_category "cheat" 4

    # Summary
    print_header "Installation Summary"
    local installed_count
    installed_count=$(find "$MODS_DIR" -name "*.pak" | wc -l)
    log "Total mods installed: ${installed_count}"
    print_success "Installation complete!"
    echo "   Installed mods: ${installed_count}"
    echo "   Location: ${MODS_DIR}"
    echo ""
    print_warn "Note: Some mods may require manual download if auto-download failed."
    print_warn "Check the log file for details: ${LOGS_DIR}/mods-install.log"
    echo ""
    print_info "Next steps:"
    echo "1. Review installed mods: ls -lh ${MODS_DIR}"
    echo "2. Restart server: docker compose restart satisfactory"
    echo "3. Install same mods on your game client using Satisfactory Mod Manager"

    log "=== Mod Installation Completed ==="
}

# Parse command line arguments
CATEGORY_FILTER=""
if [[ "$1" == "--qol-only" ]]; then
    CATEGORY_FILTER="quality-of-life"
elif [[ "$1" == "--content-only" ]]; then
    CATEGORY_FILTER="content"
elif [[ "$1" == "--cheat-only" ]]; then
    CATEGORY_FILTER="cheat"
fi

main
