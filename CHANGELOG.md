# Changelog

All notable changes to the Satisfactory server setup will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.4] - 2024-12-31

### Added

- **Daily Mod Auto-Update**: Server mods are now automatically updated every day at 4:30 AM
  - New `scripts/server/update-mods.sh` script handles safe server stop, mod update, and restart
  - Discord notifications sent when server goes down and when it comes back online
  - Runs 30 minutes after daily backup to ensure save data is protected
  - Cron job automatically added via `scripts/setup/install-cron.sh`

### Changed

- **Cron schedule**: Updated to include mod update job
  - 4:00 AM - Daily backup
  - 4:30 AM - Mod update (with Discord notifications)
  - Every 5 min - Health check

## [1.2.3] - 2024-12-30

### Fixed

- **Server mod extraction**: Fixed critical bug where mods were installed without full directory structure
  - Server was only extracting `.pak` files, missing `Binaries/`, `Content/`, `Config/` directories
  - This caused server crashes when loading any mod except the original 4
  - Now correctly extracts full mod structure from `.smod` archives
  - Server now runs successfully with all 44 mods

### Removed

- **Smart! (SmartFoundations)**: No longer available on ficsit.app
- **Container Screens (ContainerScreen)**: No longer available on ficsit.app

### Changed

- **Client installer**: Synced embedded config with server config (44 mods total)
  - Automatic cleanup in Phase 0 now removes all deprecated/unavailable mods
  - Users with old mods installed will have them automatically cleaned up

## [1.2.2] - 2024-12-30

### Added

- **Automatic Cleanup Feature**: Installer now removes obsolete/broken mods before installation
  - Phase 0 added to installation workflow: "Cleanup Obsolete Mods"
  - Automatically detects and removes mod folders that are not in the valid mod list
  - Prevents "module not found" errors from old broken mods lingering in the Mods folder
  - Logs all removed mods for user visibility

### Removed

- **MicroManage**: Marked as BROKEN on ficsit.app (broken by Update 8, last updated April 2023)
- **Teleporter**: Marked as BROKEN on ficsit.app (broken by Satisfactory 1.0)
- **Mk++ (MK22k20)**: Marked as BROKEN on ficsit.app (broken since 1.0, consider Industrial Evolution)

### Fixed

- Fixed "Plugin 'X' failed to load because module 'X' could not be found" errors
  - These errors were caused by broken mods remaining in the Mods folder from previous installs
  - The new cleanup feature automatically removes these obsolete mod folders

### Technical

- Added `cleanup_obsolete_mods()` method to `PreVerifyInstaller` class
- Updated GUI installation workflow to include cleanup phase (Phase 0)
- Updated embedded mod config to remove broken mods
- Installation workflow now has 6 phases (0-5) instead of 5 (1-5)

## [1.2.1] - 2024-12-30

### Added

- **Compatibility checking**: Installer now checks ficsit.app for broken/incompatible mods
  - Mods marked as "Broken" on ficsit.app are automatically skipped
  - Shows clear warnings during dependency resolution phase
  - Prevents installing mods that would crash the game

- **18 New Popular Mods** (all verified compatible with Satisfactory 1.0):

  **New Dependency:**
  - ContentLib - Content library required by FlexSplines

  **Quality of Life / Building:**
  - Floor Hole Ceiling Logistics (`FloorHole`) - Pass belts/pipes through floors
  - Conveyor Wall Hole (`WallHoleConveyor`) - Pass conveyors through walls
  - Flex Splines (`FlexSplines`) - Longer bendable conveyors and pipes
  - Daisy Chain Power (`DaisyChainPowerCables`) - Daisy chain power cables
  - Covered Conveyor Belts (`CoveredConveyor`) - Aesthetic covered belts
  - Underground Belts (`UndergroundBelts`) - Hidden underground conveyors
  - Wall Pipe Supports (`WallPipeSupports`) - Better pipe wall mounts
  - Upside Down Foundations (`UpsideDownFoundations`) - More foundation options

  **Monitoring / Info:**
  - Power Checker (`PowerChecker`) - Monitor power consumption
  - Throughput Counter and Limiter (`CounterLimiter`) - Count items and limit throughput
  - FicsIt-Networks (`FicsItNetworks`) - Lua scripting factory automation

  **Content / Gameplay:**
  - Magic Machines (`MagicMachine`) - Sandbox spawners
  - Faster Manual Crafting Redux (`FasterManualCraftingRedux`) - Speed up hand crafting
  - Advanced Logistics (`AdvancedLogistics`) - Programmable splitters
  - Fluid Sink (`FluidSink`) - Sink fluids for points

  **Cheats / Convenience:**
  - Unlock All Alternate Recipes (`UnlockAllAlternateRecipes`) - Skip hard drives
  - Item Spawner (`ItemSpawner`) - Spawn any item
  - All Nodes Pure (`AllNodesPure`) - Make all resource nodes pure

### Removed

- **PowerSuit mod**: Removed from default mod list (marked as BROKEN on ficsit.app, incompatible with Satisfactory 1.0)

### Technical

- Added `compatibility_warning` field to `ResolvedMod` dataclass
- Added `is_broken` property to check if mod is incompatible
- Updated API query to fetch EA/EXP compatibility status
- Gap analysis now excludes broken mods from installation

## [1.2.0] - 2024-12-30

### Added (Client Mod Installer - Major Rewrite)

- **Pre-Verification Installation System**
  - New 5-phase installation workflow that guarantees correct mod installation
  - Phase 1: Resolve all dependencies from ficsit.app API recursively
  - Phase 2: Scan currently installed mods and verify file integrity
  - Phase 3: Gap analysis - compare needed mods vs installed mods
  - Phase 4: Targeted repair - only download what's actually missing
  - Phase 5: Final verification - confirm all mods are correctly installed

- **DependencyResolver class**
  - Recursively fetches all dependencies from ficsit.app GraphQL API
  - Handles transitive dependencies (dependencies of dependencies)
  - Builds topologically sorted list (dependencies before dependents)
  - Caches resolved mods to avoid duplicate API calls

- **ModScanner class**
  - Scans game's Mods directory to inventory installed mods
  - Verifies file integrity (checks for .uplugin, .pak, .dll files)
  - Extracts version information from .uplugin files
  - Identifies missing or invalid mod installations

- **Targeted Repair**
  - Only downloads mods that are actually missing or invalid
  - Skips already-valid mods for faster installation
  - Re-downloads corrupt or incomplete mods automatically

- **Better Verification**
  - Shows detailed status of each installed mod
  - Displays dependency mods that were auto-installed
  - Clear pass/fail verdict with repair instructions

### Fixed

- **Root cause fix for missing dependencies**
  - Previous versions reported success but dependencies weren't installed
  - Now verifies BEFORE reporting success, fails if mods are missing
  - Resolves issues with ModUpdateNotifier, avMallLib, MarcioCommonLibs, ModularUI

### Changed

- Removed ficsit-cli integration (was unreliable for dependency resolution)
- Now uses direct download from ficsit.app API exclusively
- Installation is more reliable but may take slightly longer

### Technical Details

- New classes: `DependencyResolver`, `ModScanner`, `PreVerifyInstaller`, `GapAnalysisResult`, `ModStatus`, `ResolvedMod`, `InstallPhaseResult`
- API: `get_mod_with_dependencies()` fetches mod info including dependency list
- Topological sorting ensures dependencies are installed before dependents

## [1.1.6] - 2024-12-30

### Fixed (Client Mod Installer)

- **Critical fix: Add missing `apply` command**
  - ficsit-cli's `set-profile` only LINKS a profile to installation - it doesn't download mods!
  - Now we call `apply <path>` after setting profile to actually download and install mods
  - This is the root cause of why dependency mods weren't being installed

## [1.1.5] - 2024-12-30

### Fixed (Client Mod Installer)

- **Critical fix: Dependencies now installed explicitly**
  - Previous versions relied on ficsit-cli auto-resolution for dependencies
  - Dependencies (ModUpdateNotifier, avMallLib, etc.) were NOT actually being installed
  - Now ALL mods including dependencies are added to ficsit-cli profile explicitly
  - This fixes "Missing Plugin" errors in the game

- **Verification no longer assumes dependencies are installed**
  - Removed false "Auto-resolved by ficsit-cli" status
  - Missing mods are now correctly reported as "Not installed"

## [1.1.4] - 2024-12-30

### Fixed (Client Mod Installer)

- **Critical fix: "installation already present" error**
  - ficsit-cli returns "already present" but we were checking for "already exists"
  - Now correctly handles both messages as success
  - This was causing all mod installations to fail when installation was already registered

## [1.1.3] - 2024-12-30

### Added (Client Mod Installer)

- **Verbose ficsit-cli error output** for debugging
  - Now shows actual error messages instead of just "failed via ficsit-cli"
  - Displays step-by-step diagnostics: Registration, Profile creation, Mod additions
  - Example: `[WARN] SmartFoundations failed: profile with name ServerMods does not exist`

### Changed

- `install_mods()` now returns detailed error messages with each failed mod
- GUI displays diagnostic info showing which step succeeded/failed
- Better error truncation for long error messages (max 100 chars)

## [1.1.2] - 2024-12-30

### Fixed (Client Mod Installer)

- **Critical fix: ficsit-cli profile command syntax**
  - Root cause: Used `profile create` but ficsit-cli uses `profile new`
  - This caused profile creation to fail, making all subsequent mod additions fail
  - All 22 mods were reported as "failed via ficsit-cli" because the profile didn't exist
  - Mods appeared installed because they were from previous direct-download attempts

### Improved

- Better error logging for ficsit-cli commands (captures both stdout and stderr)
- More detailed debug logging to help diagnose future issues

## [1.1.1] - 2024-12-30

### Fixed (Client Mod Installer)

- **Fixed dependency mods not installing with ficsit-cli**
  - Root cause: ficsit-cli automatically resolves dependencies, but we were trying to install them explicitly
  - Solution: Only add "leaf" mods (non-dependencies) to ficsit-cli profile; let it auto-resolve deps
  - Dependencies like ModUpdateNotifier, MarcioCommonLibs, etc. are now properly handled

### Changed

- Improved logging to show when ficsit-cli is auto-resolving dependencies
- Updated verification to recognize auto-resolved dependency mods
- Better error messages and status reporting during installation

## [1.1.0] - 2024-12-30

### Changed (Client Mod Installer)

- **Integrated official ficsit-cli tool** for reliable mod installation
  - Downloads and caches ficsit-cli (~15MB) from GitHub releases
  - Uses the same installation method as the official Satisfactory Mod Manager
  - Properly registers game installation and creates mod profiles
  - Handles mod dependencies automatically
  - Ensures mods are recognized by the game (fixes "default game client" error)
- GUI now shows ficsit-cli initialization status on startup
- Installation process now shows which method is being used
- Improved installation completion messages with clear next steps

### Added

- `FicsitCLI` class in `mod_installer_core.py` for managing the official CLI tool
- Automatic ficsit-cli download and caching system
- Fallback to direct download method if ficsit-cli fails

### Fixed

- **Fixed "Is not possible to connect to a modded server in a default game client" error**
  - Root cause: Manual file placement alone wasn't enough for the game to recognize mods
  - Solution: Using ficsit-cli ensures proper mod registration and profile management

## [1.0.1] - 2024-12-30

### Fixed (Client Mod Installer)

- **Added 7 missing mod dependencies** that were causing "missing plugin" errors:
  - `ModUpdateNotifier` - required by Additional_300_Inventory_Slots
  - `MarcioCommonLibs` - required by EfficiencyCheckerMod
  - `MinoDabsCommonLib` - required by Additional_300_Inventory_Slots
  - `ModularUI` - required by RefinedPower, FicsitFarming
  - `RefinedRDApi` - required by RefinedPower, FicsitFarming
  - `RefinedRDLib` - required by RefinedPower, FicsitFarming
  - `avMallLib` - required by Dispenser
- Updated mod count from 24 to 31 in all installers
- Dependencies are now installed before main mods (priority ordering)

## [1.0.0] - 2024-12-30

### Added (Client Mod Installer)

- **Python GUI Application** (`scripts/mods/client/mod_installer_gui.py`) - **RECOMMENDED**
  - Modern desktop application using CustomTkinter
  - Visual mod selection with checkboxes organized by category
  - Real-time progress bar during installation
  - Dark/Light mode toggle
  - Built-in log viewer for troubleshooting
  - Less likely to trigger antivirus than batch scripts
  - Can be packaged as standalone .exe (no Python required)
- **Core logic module** (`scripts/mods/client/mod_installer_core.py`)
  - Reusable Python module for game path detection
  - Ficsit.app GraphQL API client
  - Download manager with proper .smod extraction
  - Full directory structure preservation (Binaries, Config, Content)
- **Build script** (`scripts/mods/client/build_exe.py`)
  - Creates standalone Windows .exe using PyInstaller
  - Single file output (~15-20MB)
- **Windows batch file installer v3.0** (`scripts/mods/client/install-mods.bat`)
  - Double-click to run - no configuration needed!
  - Automatic detection of Satisfactory installation (Steam and Epic Games)
  - Downloads mods from ficsit.app GraphQL API
  - Creates backup before installation
  - **v3.0 fix**: Preserves full mod directory structure (uplugin, pak, dll, config)
  - **v3.0 fix**: Proper extraction of .smod archives including Binaries and Config folders
  - Verification mode (`--verify`) to check current installation without downloading
  - Installation validation showing pak/dll/uplugin counts per mod
  - Multiple network test methods for corporate/restricted networks
- **Windows PowerShell installer** (`scripts/mods/client/install-client-mods.ps1`)
  - More command-line options for advanced users
  - Category filtering, skip backup, manual path options
- **Linux/macOS bash installer** (`scripts/mods/client/install-client-mods.sh`)
  - Supports Steam, Heroic, and Lutris installations
  - Dry-run mode and mod listing
- **Client mod installation documentation**
  - `scripts/mods/client/README.md` - Quick start guide
  - `docs/CLIENT_MODS_INSTALL.md` - Detailed installation guide
- **Updated FRIEND_GUIDE.md** with mod installation instructions (Step 5)

### Changed (Project Architecture Overhaul)

#### Overall Project Structure
- **New `config/` directory** for all configuration files
  - Moved cloudflared config to `config/cloudflared/`
- **New `docs/` directory** for all documentation
  - Moved all `.md` guides from root to `docs/`
- **New `Makefile`** for task automation with targets:
  - `make start/stop/restart/logs/status` - Server lifecycle
  - `make backup/update` - Operations
  - `make mods-install/mods-manual` - Mod management
  - `make network-verify` - Network operations
  - `make validate-env` - Configuration validation

#### Security Improvements
- **Removed hardcoded default secrets** from docker-compose.yml
  - `CLOUDFLARE_TUNNEL_TOKEN` now required (fails fast if not set)
  - `SFTP_PASSWORD` now required if using SFTP (no default)
- **SFTP disabled by default** - must explicitly enable with `--profile sftp`
- **New environment validation script** (`scripts/setup/validate-env.sh`)
  - Validates required secrets are configured
  - Checks for placeholder values
  - Validates port ranges and memory settings
  - Security checks for .gitignore inclusion
- **Updated `.env.example`** with clear documentation
  - Separated required vs optional secrets
  - Added security notes and generation commands

#### Scripts Reorganization
- **Major refactoring of scripts folder** with improved architecture:
  - New unified CLI entry point (`scripts/main.sh`) for all operations
  - Shared libraries (`lib/common.sh` and `lib/common.py`) eliminating code duplication
  - Organized subdirectories by concern: `server/`, `mods/`, `network/`, `setup/`, `docs/`
  - Centralized documentation in `scripts/docs/`
  - Mod configuration moved to `scripts/mods/config/`

### Added (Scripts)
- **`scripts/main.sh`**: Unified CLI for all server management operations
  - `server backup|update|monitor|import` - Server lifecycle commands
  - `mods install|manual|list` - Mod management commands
  - `network cloudflare|verify` - Network operations
  - `setup cron` - Setup operations
  - `status` - Quick server status overview
- **`scripts/lib/common.sh`**: Shared bash library with:
  - Path resolution, logging, colors, environment loading
  - Docker operations, Discord notifications, backup utilities
  - Dependency checking helpers
- **`scripts/lib/common.py`**: Shared Python library with equivalent functionality
- **Browser automation mod installer** (`scripts/mods/install-browser.py`) using Playwright
- **Environment validation script** (`scripts/setup/validate-env.sh`)

### Added (Infrastructure)
- **Makefile** for task automation
- **Docker logging configuration** with rotation (10MB max, 3 files)
- **Fixed network subnet** (172.19.0.0/16) in docker-compose.yml

### Added
- **SFTP server container** for easy mod file management (port 2222)
- **Mods installation guide** (`MODS_GUIDE.md`) with recommended mods and installation instructions
- **Automatic mod installation script** (`scripts/install-mods.sh` and `scripts/install-mods-python.py`)
- **Manual mod installation helper** (`scripts/manual-mod-install.sh`)
- **Mod download instructions generator** (`scripts/generate-mod-download-list.sh`)
- **Comprehensive mod list** (`scripts/mods-list.json`) with 25 recommended mods:
  - Quality of Life mods (9 mods)
  - Content mods (10 mods)
  - Cheat mods (5 mods)
  - Required dependencies (1 mod)
- SFTP configuration variables: `SFTP_PORT`, `SFTP_USER`, `SFTP_PASSWORD`
- Pre-mod installation backup created before mod setup
- Initial setup with Docker Compose
- Cloudflare Tunnel integration for secure access
- Environment-based configuration (.env)
- Automatic backup system (via container)
- Health checks for container monitoring
- Resource limits and reservations
- Comprehensive README documentation
- .gitignore for sensitive files
- Cloudflared configuration template
- Setup verification script (setup.sh)
- Cloudflared README with setup instructions
- **Cloudflare Zero Trust setup guide** (`CLOUDFLARE_ZERO_TRUST_SETUP.md`)
- **Friend connection guide** (`FRIEND_GUIDE.md`) with WARP installation instructions
- WARP routing enabled in cloudflared configuration
- Increased max players from 4 to 8
- **Automated backup script** (`scripts/backup.sh`) with retention policy (7 daily + 4 weekly)
- **Health monitoring script** (`scripts/monitor.sh`) with Discord webhook notifications
- **Safe update script** (`scripts/update.sh`) with automatic backup and rollback
- **Cron installation helper** (`scripts/install-cron.sh`) for automated tasks
- Server discovery ports (15000/TCP, 15777/UDP) for server browser
- Discord webhook integration for notifications (backups, monitoring, updates)
- New environment variables: `AUTOSAVEINTERVAL`, `AUTOPAUSE`, `AUTOSAVEONDISCONNECT`, `CRASHREPORT`, `NETWORKQUALITY`
- Backup configuration options: `BACKUP_RETENTION_DAILY`, `BACKUP_RETENTION_WEEKLY`
- Enhanced logging with persistent game logs (LOG=true)

### Fixed
- **Mod download script completely rewritten** - Previous browser automation was downloading Chromium binary instead of mod files
  - Now uses ficsit.app GraphQL API for direct downloads
  - Downloads .smod archives and extracts proper .pak, .ucas, .utoc files
  - Validates downloaded files are proper Unreal Engine archives
  - 20 mods successfully installed (3 client-only mods have no Linux server builds)
- **Corrected mod references** in mods-list.json to match actual ficsit.app API identifiers

### Changed
- Updated MAXPLAYERS default from 4 to 8 in `.env`
- Enhanced documentation with Zero Trust and WARP routing details
- Updated STATUS.md with Zero Trust configuration requirements
- Enabled persistent logging by default (LOG=true)
- Added server discovery ports to docker-compose.yml
- Enhanced .env.example with all available configuration options
- Updated README.md with comprehensive scripts documentation and backup/restore procedures
- **Backup retention policy**: Changed from count-based (7 daily) to age-based (3 days) for daily backups
- Backup script now deletes daily backups older than 3 days automatically

### Configuration
- Default max players: 8
- Memory limit: 8GB (reservation: 4GB)
- Ports: 7777 (TCP/UDP), 8888 (TCP), 15000 (TCP), 15777 (UDP), 2222 (SFTP)
- Automatic save rotation: 5 files
- Autosave interval: 300 seconds
- Backup retention: 3 days for daily backups, 4 weeks for weekly backups
- User/Group IDs: 1000/1000
- Logging: Enabled (LOG=true)
- SFTP: Port 2222, user `satisfactory` (configurable)

### Documentation
- Setup instructions for both Cloudflare Tunnel and port forwarding
- Management commands reference
- Troubleshooting guide
- MCP tools integration notes
- Automation scripts usage guide
- Backup and restore procedures
- Monitoring setup instructions
- Discord webhook configuration guide
- **Mods installation guide** with SFTP connection, recommended mods, and troubleshooting

### Investigated
- **9 PM auto-restart**: Investigated reported daily 9 PM server restart. No cron jobs, systemd timers, or configuration found that would cause this. Server restart policy is `unless-stopped` (only restarts on crash). If restart continues, it may be:
  - Internal Satisfactory server feature (check in-game server settings)
  - External automation not visible in current configuration
  - Manual restart pattern

## [1.0.0] - 2024-11-02

### Initial Release
- Complete Docker Compose setup
- Cloudflare Tunnel configuration
- Environment variable management
- Documentation and changelog
