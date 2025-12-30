#!/bin/bash
#
# Satisfactory Client Mod Installer for Linux/macOS
# Downloads and installs mods from ficsit.app to match server configuration
#
# Usage:
#   ./install-client-mods.sh                          # Auto-detect game path
#   ./install-client-mods.sh --game-path /path/to    # Manual path
#   ./install-client-mods.sh --category quality-of-life  # Install specific category
#   ./install-client-mods.sh --dry-run               # Show what would be installed
#
# Requirements:
#   - curl, jq, unzip
#   - Satisfactory installed (Steam or manual)
#

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_URL="https://api.ficsit.app"
GRAPHQL_ENDPOINT="${API_URL}/v2/query"
TEMP_DIR="${TMPDIR:-/tmp}/satisfactory-mod-installer"
BACKUP_DIR="${HOME}/SatisfactoryModBackups"

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
    TARGET_PLATFORM="Windows"  # Mods are Windows builds on Mac via Proton/Wine
else
    PLATFORM="Linux"
    TARGET_PLATFORM="Windows"  # Mods are Windows builds on Linux via Proton
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# Embedded Mods List
# =============================================================================

MODS_LIST='
{
  "mods": [
    {
      "name": "Satisfactory Mod Loader",
      "mod_reference": "SML",
      "category": "dependency",
      "required": true,
      "priority": 0,
      "description": "Required for ALL mods. Must be installed first."
    },
    {
      "name": "Pak Utility Mod",
      "mod_reference": "UtilityMod",
      "category": "dependency",
      "required": true,
      "priority": 1,
      "description": "Required dependency for most mods. Must be installed first."
    },
    {
      "name": "Smart!",
      "mod_reference": "SmartFoundations",
      "category": "quality-of-life",
      "required": false,
      "priority": 2,
      "description": "Mass building of foundations, walls, and more"
    },
    {
      "name": "Micro Manage",
      "mod_reference": "MicroManage",
      "category": "quality-of-life",
      "required": false,
      "priority": 2,
      "description": "Precise object positioning, rotation, and scaling"
    },
    {
      "name": "Efficiency Checker Mod",
      "mod_reference": "EfficiencyCheckerMod",
      "category": "quality-of-life",
      "required": false,
      "priority": 2,
      "description": "Monitor production line efficiency and identify bottlenecks"
    },
    {
      "name": "Infinite Zoop",
      "mod_reference": "InfiniteZoop",
      "category": "quality-of-life",
      "required": false,
      "priority": 2,
      "description": "Unlimited zoop range for building"
    },
    {
      "name": "Infinite Nudge",
      "mod_reference": "InfiniteNudge",
      "category": "quality-of-life",
      "required": false,
      "priority": 2,
      "description": "Unlimited nudge range for placing objects"
    },
    {
      "name": "Structural Solutions",
      "mod_reference": "SS_Mod",
      "category": "quality-of-life",
      "required": false,
      "priority": 2,
      "description": "More building options and structures"
    },
    {
      "name": "Modular Load Balancers",
      "mod_reference": "LoadBalancers",
      "category": "quality-of-life",
      "required": false,
      "priority": 2,
      "description": "Better load balancing for conveyor belts"
    },
    {
      "name": "MAM Enhancer",
      "mod_reference": "MAMTips",
      "category": "quality-of-life",
      "required": false,
      "priority": 2,
      "description": "Enhanced MAM research interface"
    },
    {
      "name": "MiniMap",
      "mod_reference": "MiniMap",
      "category": "quality-of-life",
      "required": false,
      "priority": 2,
      "description": "In-game minimap for navigation"
    },
    {
      "name": "Refined Power",
      "mod_reference": "RefinedPower",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "New power generation (solar, wind, nuclear variants)"
    },
    {
      "name": "Ficsit Farming",
      "mod_reference": "FicsitFarming",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "Farming mechanics and food production"
    },
    {
      "name": "Teleporter",
      "mod_reference": "Teleporter",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "Instant travel between locations"
    },
    {
      "name": "Linear Motion",
      "mod_reference": "LinearMotion",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "Moving platforms and elevators"
    },
    {
      "name": "Mk++",
      "mod_reference": "MK22k20",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "Higher tier buildings and machines"
    },
    {
      "name": "Fluid Extras",
      "mod_reference": "AB_FluidExtras",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "Additional fluid handling options"
    },
    {
      "name": "Storage Teleporter",
      "mod_reference": "StorageTeleporter",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "Teleport items between storage containers"
    },
    {
      "name": "Big Storage Tank",
      "mod_reference": "BigStorageTank",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "Large storage tanks for fluids"
    },
    {
      "name": "Container Screens",
      "mod_reference": "ContainerScreen",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "Display screens for containers"
    },
    {
      "name": "Item Dispenser",
      "mod_reference": "Dispenser",
      "category": "content",
      "required": false,
      "priority": 3,
      "description": "Dispense items automatically"
    },
    {
      "name": "EasyCheat",
      "mod_reference": "EasyCheat",
      "category": "cheat",
      "required": false,
      "priority": 4,
      "description": "Simple cheat menu for resources and unlocks"
    },
    {
      "name": "PowerSuit",
      "mod_reference": "PowerSuit",
      "category": "cheat",
      "required": false,
      "priority": 4,
      "description": "Enhanced player abilities and stats"
    },
    {
      "name": "Additional 300 Inventory Slots",
      "mod_reference": "Additional_300_Inventory_Slots",
      "category": "cheat",
      "required": false,
      "priority": 4,
      "description": "Extra inventory space"
    }
  ]
}
'

# =============================================================================
# Output Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}=== $1 ===${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Dependency Check
# =============================================================================

check_dependencies() {
    local missing=()

    for cmd in curl jq unzip; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing[*]}"
        echo ""

        if [[ "$PLATFORM" == "macOS" ]]; then
            echo "Install with Homebrew:"
            echo "  brew install ${missing[*]}"
        else
            echo "Install with your package manager:"
            echo "  Ubuntu/Debian: sudo apt install ${missing[*]}"
            echo "  Fedora: sudo dnf install ${missing[*]}"
            echo "  Arch: sudo pacman -S ${missing[*]}"
        fi
        exit 1
    fi
}

# =============================================================================
# Game Path Detection
# =============================================================================

find_steam_satisfactory() {
    print_info "Searching for Steam installation..."

    local steam_paths=()

    if [[ "$PLATFORM" == "macOS" ]]; then
        steam_paths=(
            "$HOME/Library/Application Support/Steam"
        )
    else
        steam_paths=(
            "$HOME/.steam/steam"
            "$HOME/.local/share/Steam"
            "$HOME/.steam"
        )
    fi

    for steam_path in "${steam_paths[@]}"; do
        if [[ -d "$steam_path" ]]; then
            # Check main steamapps
            local satisfactory_path="$steam_path/steamapps/common/Satisfactory"
            if [[ -d "$satisfactory_path" ]]; then
                print_success "Found in Steam: $satisfactory_path"
                echo "$satisfactory_path"
                return 0
            fi

            # Check library folders
            local library_file="$steam_path/steamapps/libraryfolders.vdf"
            if [[ -f "$library_file" ]]; then
                # Parse library paths from VDF
                while IFS= read -r line; do
                    if [[ "$line" =~ \"path\"[[:space:]]*\"([^\"]+)\" ]]; then
                        local lib_path="${BASH_REMATCH[1]}"
                        local satisfactory_lib="$lib_path/steamapps/common/Satisfactory"
                        if [[ -d "$satisfactory_lib" ]]; then
                            print_success "Found in Steam library: $satisfactory_lib"
                            echo "$satisfactory_lib"
                            return 0
                        fi
                    fi
                done < "$library_file"
            fi
        fi
    done

    return 1
}

find_heroic_satisfactory() {
    print_info "Searching for Heroic Games Launcher installation..."

    local heroic_paths=(
        "$HOME/.config/heroic/GamesConfig"
        "$HOME/Games/Heroic"
    )

    for heroic_path in "${heroic_paths[@]}"; do
        if [[ -d "$heroic_path" ]]; then
            # Look for Satisfactory in Heroic config
            local satisfactory_path
            satisfactory_path=$(find "$heroic_path" -type d -name "Satisfactory*" 2>/dev/null | head -1)
            if [[ -n "$satisfactory_path" && -d "$satisfactory_path" ]]; then
                print_success "Found via Heroic: $satisfactory_path"
                echo "$satisfactory_path"
                return 0
            fi
        fi
    done

    return 1
}

find_lutris_satisfactory() {
    print_info "Searching for Lutris installation..."

    local lutris_path="$HOME/Games"
    if [[ -d "$lutris_path" ]]; then
        local satisfactory_path
        satisfactory_path=$(find "$lutris_path" -type d -name "Satisfactory" 2>/dev/null | head -1)
        if [[ -n "$satisfactory_path" && -d "$satisfactory_path" ]]; then
            print_success "Found via Lutris/Games: $satisfactory_path"
            echo "$satisfactory_path"
            return 0
        fi
    fi

    return 1
}

find_satisfactory_path() {
    print_header "Detecting Satisfactory Installation"

    local game_path

    # Try Steam first (most common on Linux)
    game_path=$(find_steam_satisfactory 2>/dev/null) && {
        echo "$game_path"
        return 0
    }

    # Try Heroic (Epic Games on Linux)
    game_path=$(find_heroic_satisfactory 2>/dev/null) && {
        echo "$game_path"
        return 0
    }

    # Try Lutris
    game_path=$(find_lutris_satisfactory 2>/dev/null) && {
        echo "$game_path"
        return 0
    }

    return 1
}

validate_game_path() {
    local path="$1"

    if [[ ! -d "$path" ]]; then
        return 1
    fi

    # Check for key game files/directories
    if [[ -d "$path/FactoryGame" ]] || [[ -d "$path/Engine" ]]; then
        return 0
    fi

    return 1
}

# =============================================================================
# API Functions
# =============================================================================

graphql_query() {
    local query="$1"
    local body
    body=$(jq -n --arg q "$query" '{"query": $q}')

    local response
    response=$(curl -s -X POST "$GRAPHQL_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$body" \
        --max-time 30) || {
        print_error "API request failed"
        return 1
    }

    # Check for errors
    if echo "$response" | jq -e '.errors' > /dev/null 2>&1; then
        print_error "GraphQL error: $(echo "$response" | jq -r '.errors[0].message')"
        return 1
    fi

    echo "$response"
}

get_mod_info() {
    local mod_reference="$1"

    local query="query {
        getModByReference(modReference: \"$mod_reference\") {
            id
            name
            mod_reference
            versions(filter: {limit: 1, order_by: created_at, order: desc}) {
                id
                version
                targets {
                    targetName
                    link
                }
            }
        }
    }"

    local response
    response=$(graphql_query "$query") || return 1

    echo "$response" | jq '.data.getModByReference'
}

# =============================================================================
# Installation Functions
# =============================================================================

create_backup() {
    local mods_dir="$1"

    if [[ ! -d "$mods_dir" ]]; then
        return 0
    fi

    local mod_count
    mod_count=$(find "$mods_dir" -maxdepth 1 -type d | wc -l)

    if [[ $mod_count -le 1 ]]; then
        return 0
    fi

    print_info "Creating backup of existing mods..."

    mkdir -p "$BACKUP_DIR"

    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_path="$BACKUP_DIR/mods-backup-$timestamp"

    cp -r "$mods_dir" "$backup_path" || {
        print_warning "Failed to create backup"
        return 1
    }

    print_success "Backup created: $backup_path"
    return 0
}

install_mod() {
    local mod_reference="$1"
    local mod_name="$2"
    local mods_dir="$3"
    local dry_run="${4:-false}"

    print_info "Processing: $mod_name ($mod_reference)"

    # Get mod details from API
    local api_info
    api_info=$(get_mod_info "$mod_reference") || {
        print_error "Could not find mod: $mod_reference"
        return 1
    }

    if [[ "$api_info" == "null" ]]; then
        print_error "Mod not found: $mod_reference"
        return 1
    fi

    # Get latest version
    local version
    version=$(echo "$api_info" | jq -r '.versions[0].version')

    if [[ -z "$version" || "$version" == "null" ]]; then
        print_error "No versions available for: $mod_reference"
        return 1
    fi

    # Find Windows target
    local download_link
    download_link=$(echo "$api_info" | jq -r ".versions[0].targets[] | select(.targetName == \"$TARGET_PLATFORM\") | .link")

    if [[ -z "$download_link" || "$download_link" == "null" ]]; then
        print_warning "No Windows version for: $mod_reference (may be server-only)"
        return 2  # Skip, not failure
    fi

    # Ensure full URL
    if [[ ! "$download_link" =~ ^https?:// ]]; then
        download_link="${API_URL}${download_link}"
    fi

    if [[ "$dry_run" == "true" ]]; then
        print_info "Would download: $mod_name v$version"
        return 0
    fi

    # Create temp directory
    mkdir -p "$TEMP_DIR"

    # Download the smod file
    local smod_path="$TEMP_DIR/${mod_reference}-${version}.smod"

    print_info "Downloading v$version..."

    curl -sL -o "$smod_path" "$download_link" --max-time 120 || {
        print_error "Download failed for $mod_reference"
        return 1
    }

    # Verify it's a valid zip file
    if ! unzip -tq "$smod_path" > /dev/null 2>&1; then
        print_error "Downloaded file is not a valid archive: $mod_reference"
        rm -f "$smod_path"
        return 1
    fi

    # Extract the smod
    local extract_dir="$TEMP_DIR/extract_${mod_reference}"
    rm -rf "$extract_dir"
    mkdir -p "$extract_dir"

    unzip -q "$smod_path" -d "$extract_dir" || {
        print_error "Extraction failed for $mod_reference"
        rm -f "$smod_path"
        return 1
    }

    # Find pak files
    local paks_dir="$extract_dir/Content/Paks/Windows"
    if [[ ! -d "$paks_dir" ]]; then
        paks_dir="$extract_dir/Content/Paks"
    fi
    if [[ ! -d "$paks_dir" ]]; then
        # Try to find any pak files
        paks_dir=$(find "$extract_dir" -name "*.pak" -type f -exec dirname {} \; | head -1)
    fi

    if [[ -z "$paks_dir" || ! -d "$paks_dir" ]]; then
        print_warning "No pak files found in $mod_reference"
        rm -rf "$extract_dir" "$smod_path"
        return 1
    fi

    # Create mod destination directory
    local mod_dest_dir="$mods_dir/$mod_reference"
    mkdir -p "$mod_dest_dir"

    # Copy files
    local files_copied=0

    for ext in "pak" "ucas" "utoc"; do
        for file in "$paks_dir"/*."$ext"; do
            if [[ -f "$file" ]]; then
                cp "$file" "$mod_dest_dir/"
                ((files_copied++))
            fi
        done
    done

    # Copy uplugin file if exists
    local uplugin_file
    uplugin_file=$(find "$extract_dir" -name "*.uplugin" -type f | head -1)
    if [[ -n "$uplugin_file" ]]; then
        cp "$uplugin_file" "$mod_dest_dir/"
        ((files_copied++))
    fi

    # Cleanup
    rm -rf "$extract_dir" "$smod_path"

    if [[ $files_copied -gt 0 ]]; then
        print_success "Installed: $mod_name v$version ($files_copied files)"
        return 0
    else
        print_warning "No files extracted for $mod_reference"
        return 1
    fi
}

# =============================================================================
# Main
# =============================================================================

usage() {
    cat << EOF
Satisfactory Client Mod Installer for Linux/macOS

Usage: $(basename "$0") [OPTIONS]

Options:
    --game-path PATH    Manually specify Satisfactory installation path
    --category CAT      Install only mods from specific category
                        (dependency, quality-of-life, content, cheat)
    --skip-backup       Skip creating backup of existing mods
    --dry-run           Show what would be installed without installing
    --list              List all available mods and exit
    -h, --help          Show this help message

Examples:
    $(basename "$0")
    $(basename "$0") --game-path ~/.steam/steam/steamapps/common/Satisfactory
    $(basename "$0") --category quality-of-life
    $(basename "$0") --dry-run

EOF
}

list_mods() {
    print_header "Available Mods"

    echo "$MODS_LIST" | jq -r '.mods | group_by(.category) | .[] |
        "\n\(.[ 0].category | ascii_upcase):\n" +
        (.[] | "  - \(.name) (\(.mod_reference))\n    \(.description)")'
}

main() {
    local game_path=""
    local category_filter=""
    local skip_backup=false
    local dry_run=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --game-path)
                game_path="$2"
                shift 2
                ;;
            --category)
                category_filter="$2"
                shift 2
                ;;
            --skip-backup)
                skip_backup=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --list)
                list_mods
                exit 0
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    echo ""
    echo -e "${CYAN}======================================${NC}"
    echo -e "${CYAN}  Satisfactory Client Mod Installer${NC}"
    echo -e "${CYAN}  Platform: $PLATFORM${NC}"
    echo -e "${CYAN}======================================${NC}"
    echo ""

    # Check dependencies
    check_dependencies

    # Determine game path
    if [[ -n "$game_path" ]]; then
        print_info "Using provided game path: $game_path"
        if ! validate_game_path "$game_path"; then
            print_error "Invalid game path: $game_path"
            print_error "The path should contain FactoryGame folder with game files."
            exit 1
        fi
    else
        game_path=$(find_satisfactory_path) || {
            print_error "Could not find Satisfactory installation!"
            echo ""
            echo -e "${YELLOW}Please specify the path manually:${NC}"
            echo "  $0 --game-path /path/to/Satisfactory"
            echo ""
            echo -e "${YELLOW}Common installation locations:${NC}"
            echo "  Steam: ~/.steam/steam/steamapps/common/Satisfactory"
            echo "  Heroic: ~/Games/Heroic/Satisfactory"
            echo "  Lutris: ~/Games/Satisfactory"
            exit 1
        }
    fi

    print_success "Found Satisfactory"
    echo "  Path: $game_path"

    # Determine mods directory
    local mods_dir="$game_path/FactoryGame/Mods"
    print_info "Mods directory: $mods_dir"

    # Create mods directory if needed
    if [[ ! -d "$mods_dir" ]]; then
        print_info "Creating Mods directory..."
        mkdir -p "$mods_dir"
    fi

    # Backup existing mods
    if [[ "$skip_backup" != "true" && "$dry_run" != "true" ]]; then
        create_backup "$mods_dir"
    fi

    # Load mods list
    print_header "Loading Mod Configuration"

    local mods
    mods=$(echo "$MODS_LIST" | jq -c '.mods | sort_by(.priority) | .[]')

    # Filter by category if specified
    if [[ -n "$category_filter" ]]; then
        mods=$(echo "$MODS_LIST" | jq -c --arg cat "$category_filter" '.mods | sort_by(.priority) | .[] | select(.category == $cat)')
        print_info "Installing $category_filter mods only"
    fi

    local mod_count
    mod_count=$(echo "$mods" | wc -l)
    print_info "Found $mod_count mods to install"
    echo ""

    if [[ "$dry_run" == "true" ]]; then
        print_warning "DRY RUN MODE - No files will be installed"
        echo ""
    fi

    # Install each mod
    local success_count=0
    local fail_count=0
    local skip_count=0

    while IFS= read -r mod_json; do
        local mod_ref mod_name
        mod_ref=$(echo "$mod_json" | jq -r '.mod_reference')
        mod_name=$(echo "$mod_json" | jq -r '.name')

        local result
        install_mod "$mod_ref" "$mod_name" "$mods_dir" "$dry_run"
        result=$?

        if [[ $result -eq 0 ]]; then
            ((success_count++))
        elif [[ $result -eq 2 ]]; then
            ((skip_count++))
        else
            ((fail_count++))
        fi

        echo ""
    done <<< "$mods"

    # Summary
    print_header "Installation Complete"

    echo -e "  ${GREEN}Successful: $success_count${NC}"
    if [[ $skip_count -gt 0 ]]; then
        echo -e "  ${YELLOW}Skipped (no Windows version): $skip_count${NC}"
    fi
    if [[ $fail_count -gt 0 ]]; then
        echo -e "  ${RED}Failed: $fail_count${NC}"
    fi

    # List installed mods
    if [[ "$dry_run" != "true" && -d "$mods_dir" ]]; then
        local installed_mods
        installed_mods=$(find "$mods_dir" -maxdepth 1 -type d ! -name "Mods" | sort)

        if [[ -n "$installed_mods" ]]; then
            echo ""
            echo -e "${CYAN}Installed mods:${NC}"
            while IFS= read -r mod_dir; do
                echo "  - $(basename "$mod_dir")"
            done <<< "$installed_mods"
        fi
    fi

    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Launch Satisfactory (via Steam/Heroic/Lutris)"
    echo "  2. Connect to the server"
    echo "  3. Enjoy playing with mods!"
    echo ""

    # Cleanup temp directory
    rm -rf "$TEMP_DIR"

    if [[ $fail_count -gt 0 ]]; then
        exit 1
    fi
    exit 0
}

main "$@"
