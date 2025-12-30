#!/bin/bash
# Generate Mod Download List
# Creates a list of all mods with download instructions

set -e

# Source common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

# Initialize
init_common

MODS_CONFIG_DIR="${SCRIPTS_DIR}/mods/config"
MODS_LIST="${MODS_CONFIG_DIR}/mods-list.json"
OUTPUT_FILE="${SCRIPTS_DIR}/docs/MODS_DOWNLOAD.md"

print_info "Generating mod download instructions..."

cat > "$OUTPUT_FILE" << 'EOF'
# Mod Download Instructions

This file contains download links and instructions for all recommended mods.

## How to Download Mods

1. Visit each mod's page on ficsit.app using the links below
2. Click the "Download" or "Install" button
3. Save the `.pak` file to a temporary location
4. Use the manual installation script to install:

```bash
./scripts/mods/manual.sh ~/Downloads/*.pak
```

Or upload via SFTP to: `data/gamefiles/FactoryGame/Mods/`

## Installation Order

Install mods in this order:
1. **Pak Utility Mod** (required first)
2. Quality of Life mods
3. Content mods
4. Cheat mods

---

EOF

# Generate mod list from JSON
jq -r '.mods[] | "## \(.name)\n- **Category**: \(.category)\n- **Priority**: \(.priority)\n- **Description**: \(.description)\n- **Download**: \(.url)\n- **GitHub**: \(.github // "N/A")\n"' "$MODS_LIST" >> "$OUTPUT_FILE"

print_success "Generated: $OUTPUT_FILE"
