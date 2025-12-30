# Mod Installation - Important Notes

## Automatic Download Limitations

**ficsit.app does not expose direct download URLs** for mods. The website uses:

- JavaScript-rendered content (SvelteKit)
- GraphQL API with persisted queries (requires specific query hashes)
- SMM (Satisfactory Mod Manager) protocol handler for downloads

This makes **automatic download very difficult** without:

- A headless browser (Selenium/Playwright)
- Reverse-engineering the GraphQL API
- Using SMM programmatically

## Current Solution

The installation scripts (`mods/install.sh` and `mods/install.py`) will:

1. ✅ Attempt to download from GitHub releases (if mod has GitHub repo)
2. ⚠️ Attempt to extract download URLs from mod pages (limited success)
3. ❌ Provide clear manual download instructions if automatic download fails

## Recommended Approach: Manual Download

Since automatic download has limitations, **manual download is more reliable**:

### Option 1: Using Satisfactory Mod Manager

1. Install [Satisfactory Mod Manager (SMM)](https://github.com/satisfactorymodding/SatisfactoryModManager/releases)
2. Open SMM
3. Browse and download all mods from the list
4. Mods will be saved to:
   - **Windows:** `%LOCALAPPDATA%\SatisfactoryModManager\mods\`
   - **Linux/Mac:** `~/.local/share/SatisfactoryModManager/mods/`

### Option 2: Direct Installation via SFTP

If your server supports SFTP:

1. In SMM, go to "Manage Servers"
2. Add your server with SFTP credentials
3. Select your server in SMM
4. Install mods directly - SMM will upload them automatically

## Installing Downloaded Mods

```bash
# Copy all .pak files from SMM mods directory to server
./scripts/mods/manual.sh ~/.local/share/SatisfactoryModManager/mods/*.pak

# Or upload via SFTP to: data/gamefiles/FactoryGame/Mods/
```

## Mod Configuration

All 25 recommended mods are listed in `scripts/mods/config/mods-list.json`:

| Category | Count | Description |
|----------|-------|-------------|
| dependency | 1 | Pak Utility (required) |
| quality-of-life | 9 | Building, navigation, efficiency mods |
| content | 10 | New items, machines, features |
| cheat | 5 | Creative mode, unlimited resources |

## Summary

**For reliable mod installation:**

1. Use Satisfactory Mod Manager to download mods
2. Use `mods/manual.sh` to install on server
3. Or use SMM's SFTP feature to install directly

**Automatic download scripts are provided but may not work for all mods** due to ficsit.app's architecture.
