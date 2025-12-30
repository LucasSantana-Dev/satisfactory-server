#!/bin/bash
# Manual Mod Installation Helper
# Helps install mods that were downloaded manually

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common

print_header "Manual Mod Installation Helper"

# Create mods directory if needed
mkdir -p "$MODS_DIR"

# Function to install a .pak file
install_pak_file() {
    local pak_file=$1

    if [[ ! -f "$pak_file" ]]; then
        print_error "File not found: ${pak_file}"
        return 1
    fi

    if [[ ! "$pak_file" =~ \.pak$ ]]; then
        print_warn "File doesn't have .pak extension"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    local filename
    filename=$(basename "$pak_file")
    local dest="${MODS_DIR}/${filename}"

    if cp "$pak_file" "$dest"; then
        chmod 644 "$dest"
        print_success "Installed: ${filename}"
        return 0
    else
        print_error "Failed to install: ${filename}"
        return 1
    fi
}

# Main function
main() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: $0 <path-to-mod.pak> [<path-to-mod2.pak> ...]"
        echo ""
        echo "Example:"
        echo "  $0 ~/Downloads/PakUtility.pak ~/Downloads/Smart.pak"
        echo ""
        echo "Or install all .pak files from a directory:"
        echo "  $0 ~/Downloads/*.pak"
        exit 1
    fi

    print_info "Installing mod files..."
    echo ""

    local installed=0
    local failed=0

    for pak_file in "$@"; do
        if install_pak_file "$pak_file"; then
            installed=$((installed + 1))
        else
            failed=$((failed + 1))
        fi
    done

    print_header "Installation Summary"
    echo -e "Installed: ${GREEN}${installed}${NC}"
    echo -e "Failed: ${RED}${failed}${NC}"
    echo ""
    echo "Mods location: ${MODS_DIR}"
    echo ""
    print_info "Next steps:"
    echo "1. Restart server: docker compose restart satisfactory"
    echo "2. Install same mods on your game client"
}

main "$@"
