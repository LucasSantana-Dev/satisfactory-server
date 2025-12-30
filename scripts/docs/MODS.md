# Mod Installation Guide

## Quick Start

### Automatic Installation (Attempts Download)

The installation scripts will attempt to automatically download mods, but **ficsit.app doesn't expose direct download URLs**, so automatic download may not work for all mods.

```bash
# Run from project root
./scripts/mods/install.sh

# Or use Python version (better web scraping)
python3 ./scripts/mods/install.py
```

**Note:** If automatic download fails, you'll see instructions for manual download.

### Manual Installation (Recommended)

Since automatic download has limitations, manual installation is more reliable:

#### Step 1: Download Mods

1. Visit [ficsit.app](https://ficsit.app)
2. For each mod in the list, click "Download" or use Satisfactory Mod Manager
3. Save all `.pak` files to a folder (e.g., `~/Downloads/mods/`)

#### Step 2: Install on Server

```bash
# Install all downloaded mods at once
./scripts/mods/manual.sh ~/Downloads/mods/*.pak
```

Or upload via SFTP to: `data/gamefiles/FactoryGame/Mods/`

## Mod List

See `scripts/mods/config/mods-list.json` for the complete list of 25 recommended mods:

| Category | Count |
|----------|-------|
| Dependencies | 1 (Pak Utility) |
| Quality of Life | 9 |
| Content | 10 |
| Cheat | 5 |

## Installation Order

Mods are installed in priority order:
1. **Dependencies** (Pak Utility) - **MUST be first**
2. Quality of Life mods
3. Content mods
4. Cheat mods

## After Installation

1. **Restart server:**
   ```bash
   docker compose restart satisfactory
   ```

2. **Install same mods on your game client** using Satisfactory Mod Manager

3. **Verify mods are loaded** when connecting to the server

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Mods not loading | Check file permissions: `chmod 644 data/gamefiles/FactoryGame/Mods/*.pak` |
| Server won't start | Check logs: `docker compose logs satisfactory` |
| Version mismatch | Ensure server and client have the same mod versions |

## Script Reference

| Script | Purpose |
|--------|---------|
| `mods/install.sh` | Automatic mod installation (bash) |
| `mods/install.py` | Automatic mod installation (Python) |
| `mods/manual.sh` | Manual installation of .pak files |
| `mods/generate-list.sh` | Generate download instructions |

For detailed download instructions, see [MODS_DOWNLOAD.md](./MODS_DOWNLOAD.md).
