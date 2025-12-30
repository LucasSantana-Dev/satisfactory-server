# Satisfactory Server Scripts

Unified management scripts for the Satisfactory dedicated server.

## Quick Start

```bash
# Make the main script executable
chmod +x scripts/main.sh

# Show all available commands
./scripts/main.sh help

# Check server status
./scripts/main.sh status
```

## Directory Structure

```
scripts/
├── main.sh                 # Main CLI entry point
├── README.md               # This file
│
├── lib/                    # Shared libraries (DRY)
│   ├── common.sh           # Bash common functions
│   └── common.py           # Python common functions
│
├── server/                 # Server lifecycle management
│   ├── backup.sh           # Create compressed backups
│   ├── update.sh           # Update server with rollback
│   ├── monitor.sh          # Health monitoring + Discord
│   └── import-save.sh      # Import save files
│
├── mods/                   # Mod management
│   ├── install.sh          # Auto-install mods (bash)
│   ├── install.py          # Auto-install mods (Python)
│   ├── manual.sh           # Manual mod installation
│   ├── generate-list.sh    # Generate download list
│   ├── config/
│   │   └── mods-list.json  # Mod configuration
│   └── client/             # Client-side mod installer
│       ├── install-mods.bat         # Windows installer (Batch - easiest!)
│       ├── install-client-mods.ps1  # Windows installer (PowerShell)
│       ├── install-client-mods.sh   # Linux/macOS installer (Bash)
│       └── README.md       # Client installation guide
│
├── network/                # Network/Cloudflare
│   ├── configure-cloudflare.sh
│   ├── configure-cloudflare.py
│   └── verify-tunnel.sh
│
├── setup/                  # One-time setup
│   └── install-cron.sh     # Install cron jobs
│
└── docs/                   # Script documentation
    ├── MODS.md             # Mod installation guide
    ├── MODS_IMPORTANT.md   # Important mod notes
    └── MODS_DOWNLOAD.md    # Download instructions (generated)
```

## Commands Reference

### Server Management

```bash
# Create backup
./scripts/main.sh server backup

# Update server to latest version
./scripts/main.sh server update

# Run health monitoring
./scripts/main.sh server monitor

# Import a save file
./scripts/main.sh server import ~/Downloads/MySave.sav
```

### Mod Management (Server)

```bash
# Auto-install mods (tries GitHub releases first)
./scripts/main.sh mods install

# Install downloaded .pak files manually
./scripts/main.sh mods manual ~/Downloads/*.pak

# Generate download instructions
./scripts/main.sh mods list
```

### Mod Management (Client)

For friends connecting to the server, installer scripts are provided:

**Windows (Easiest - Double-click to run):**
```
scripts\mods\client\install-mods.bat
```

**Windows (PowerShell - More options):**
```powershell
.\scripts\mods\client\install-client-mods.ps1
.\scripts\mods\client\install-client-mods.ps1 -GamePath "D:\Games\Satisfactory"
.\scripts\mods\client\install-client-mods.ps1 -CategoryFilter "quality-of-life"
```

**Linux/macOS:**
```bash
./scripts/mods/client/install-client-mods.sh
./scripts/mods/client/install-client-mods.sh --game-path ~/.steam/steam/steamapps/common/Satisfactory
```

Features:
- Automatic game path detection (Steam, Epic Games, Heroic, Lutris)
- Downloads from ficsit.app API
- Creates backup before installation
- Installs platform-compatible mod versions

See `scripts/mods/client/README.md` for detailed instructions.

### Network Operations

```bash
# Configure Cloudflare Zero Trust
./scripts/main.sh network cloudflare

# Verify tunnel connectivity
./scripts/main.sh network verify
```

### Setup

```bash
# Install cron jobs for backup/monitoring
./scripts/main.sh setup cron
```

## Direct Script Access

You can also run scripts directly:

```bash
# Server scripts
./scripts/server/backup.sh
./scripts/server/update.sh
./scripts/server/monitor.sh
./scripts/server/import-save.sh ~/Downloads/save.sav

# Mod scripts
./scripts/mods/install.sh
python3 ./scripts/mods/install.py
./scripts/mods/manual.sh ~/Downloads/*.pak

# Network scripts
./scripts/network/verify-tunnel.sh
```

## Shared Library

The `lib/` directory contains shared functions used by all scripts:

### Bash (`lib/common.sh`)

```bash
# Source in your script
source "${SCRIPT_DIR}/../lib/common.sh"
init_common

# Available functions:
log "message"                    # Log with timestamp
print_success "message"          # Green checkmark
print_error "message"            # Red X
print_warn "message"             # Yellow warning
print_info "message"             # Blue info
print_header "Title"             # Section header

load_env                         # Load .env variables
get_env "VAR_NAME" "default"     # Get env with default

is_container_running "name"      # Check container
get_container_health "name"      # Get health status
wait_for_healthy "name" 30       # Wait for healthy

send_discord_notification "Title" "Message" $DISCORD_GREEN

check_dependencies curl jq       # Check commands exist
```

### Python (`lib/common.py`)

```python
from common import (
    init_script, print_header, print_success,
    is_container_running, send_discord_notification
)

# Initialize
paths, logger = init_script("script-name", "log-name")

# Available:
paths.project       # Project root
paths.mods          # Mods directory
paths.backups       # Backups directory

logger.info("message")
logger.error("message")
```

## Configuration

All scripts use environment variables from `.env`:

```bash
# Server
SERVER_GAME_PORT=7777

# Discord notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Backups
BACKUP_RETENTION_DAILY=7
BACKUP_RETENTION_WEEKLY=4

# Cloudflare
CLOUDFLARE_TUNNEL_TOKEN=...
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...
```

## Cron Jobs

After running `./scripts/main.sh setup cron`:

| Schedule | Job | Log File |
|----------|-----|----------|
| Daily 4 AM | Backup | `data/logs/backup-cron.log` |
| Every 5 min | Health check | `data/logs/monitor-cron.log` |

## Architecture Benefits

1. **DRY (Don't Repeat Yourself)**: Common functions in `lib/` eliminate code duplication
2. **Separation of Concerns**: Each directory has a single responsibility
3. **Unified CLI**: Single entry point for all operations
4. **Consistent Logging**: All scripts use the same logging format
5. **Discord Integration**: Centralized notification handling
6. **Testability**: Shared functions can be tested independently
