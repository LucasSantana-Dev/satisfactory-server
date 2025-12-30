# Satisfactory Client Mod Installer

Automatically install mods on your game client to match the server's mod configuration.

## Available Installers

| Installer | Platform | How to Run | Best For |
|-----------|----------|------------|----------|
| `SatisfactoryModInstaller.exe` | Windows | Double-click | **Recommended** - GUI app |
| `install-mods.bat` | Windows | Double-click | Backup - Command line |
| `install-client-mods.ps1` | Windows | PowerShell | Advanced users |
| `install-client-mods.sh` | Linux/macOS | Terminal | Linux/Mac users |

## Quick Start

### Windows - GUI Application (Recommended!)

**Option 1: Download Pre-built Executable**

1. Download `SatisfactoryModInstaller.exe`
2. **Double-click** to run
3. Select mods you want, click "Install"
4. Done!

**Option 2: Run from Python**

```powershell
# Install dependencies
pip install -r requirements-gui.txt

# Run the application
python mod_installer_gui.py
```

**Features:**
- Modern graphical interface with dark/light mode
- Checkboxes to select individual mods
- Real-time progress bar during installation
- Built-in verification tool
- No antivirus issues (unlike batch scripts)

### Build Your Own Executable

```powershell
# Install build tools
pip install pyinstaller

# Build the .exe
python build_exe.py
```

Output: `dist/SatisfactoryModInstaller.exe` (~15-20MB)

---

### Windows - Batch File (Backup Method)

1. Download `install-mods.bat`
2. **Double-click** the file to run it
3. Follow the on-screen instructions

That's it! No command prompts or configuration needed.

> **Note:** Some antivirus software may flag batch files. If this happens, use the GUI application instead.

### Windows - PowerShell (More Control)

**Option 1: Run Directly**

Open PowerShell and run:

```powershell
# Download and run the installer
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
irm https://raw.githubusercontent.com/YOUR_USERNAME/satisfactory-server/main/scripts/mods/client/install-client-mods.ps1 -OutFile install-mods.ps1
.\install-mods.ps1
```

**Option 2: Download and Run**

1. Download `install-client-mods.ps1`
2. Right-click and select "Run with PowerShell"
3. If prompted about execution policy, type `Y` to allow

### Linux / macOS (Bash)

**Option 1: Direct Download and Run**

```bash
# Download and run
curl -sL https://raw.githubusercontent.com/YOUR_USERNAME/satisfactory-server/main/scripts/mods/client/install-client-mods.sh | bash
```

**Option 2: Download First**

```bash
# Download the script
curl -sLO https://raw.githubusercontent.com/YOUR_USERNAME/satisfactory-server/main/scripts/mods/client/install-client-mods.sh

# Make executable
chmod +x install-client-mods.sh

# Run
./install-client-mods.sh
```

**Requirements:**
- `curl`, `jq`, `unzip` (install via your package manager)
- Satisfactory installed via Steam, Heroic, or Lutris

## What It Does

1. **Detects your game** - Automatically finds Satisfactory installation
2. **Creates backup** - Backs up existing mods before making changes
3. **Downloads mods** - Gets the latest mod versions from ficsit.app
4. **Installs mods** - Extracts and installs to the correct location

## Command Line Options

### Windows (PowerShell)

```powershell
# Specify game path manually
.\install-client-mods.ps1 -GamePath "D:\Games\Satisfactory"

# Skip backup creation
.\install-client-mods.ps1 -SkipBackup

# Install only specific category
.\install-client-mods.ps1 -CategoryFilter "quality-of-life"

# Categories: dependency, quality-of-life, content, cheat
```

### Linux / macOS (Bash)

```bash
# Specify game path manually
./install-client-mods.sh --game-path ~/.steam/steam/steamapps/common/Satisfactory

# Skip backup creation
./install-client-mods.sh --skip-backup

# Install only specific category
./install-client-mods.sh --category quality-of-life

# Dry run (show what would be installed)
./install-client-mods.sh --dry-run

# List all available mods
./install-client-mods.sh --list

# Show help
./install-client-mods.sh --help
```

## Installed Mods

The script installs these mods to match the server:

### Dependencies (Required)

| Mod | Description |
|-----|-------------|
| SML | Satisfactory Mod Loader - Required for all mods |
| UtilityMod | Pak Utility Mod - Required dependency |

### Quality of Life

| Mod | Description |
|-----|-------------|
| Smart! | Mass building of foundations, walls, and more |
| Micro Manage | Precise object positioning and rotation |
| Efficiency Checker | Monitor production line efficiency |
| Infinite Zoop | Unlimited zoop range for building |
| Infinite Nudge | Unlimited nudge range for objects |
| Structural Solutions | More building options |
| Modular Load Balancers | Better conveyor load balancing |
| MAM Enhancer | Enhanced MAM research interface |
| MiniMap | In-game minimap for navigation |

### Content

| Mod | Description |
|-----|-------------|
| Refined Power | Solar, wind, nuclear power options |
| Ficsit Farming | Farming and food production |
| Teleporter | Instant travel between locations |
| Linear Motion | Moving platforms and elevators |
| Mk++ | Higher tier buildings and machines |
| Fluid Extras | Additional fluid handling |
| Storage Teleporter | Teleport items between containers |
| Big Storage Tank | Large fluid storage tanks |
| Container Screens | Display screens for containers |
| Item Dispenser | Automatic item dispensing |

### Cheat (Optional)

| Mod | Description |
|-----|-------------|
| EasyCheat | Simple cheat menu |
| PowerSuit | Enhanced player abilities |
| Additional 300 Inventory Slots | Extra inventory space |

## Troubleshooting

### "Could not find Satisfactory installation"

Specify the path manually:

**Windows:**
```powershell
.\install-client-mods.ps1 -GamePath "C:\Program Files (x86)\Steam\steamapps\common\Satisfactory"
```

**Linux:**
```bash
./install-client-mods.sh --game-path ~/.steam/steam/steamapps/common/Satisfactory
```

**Common paths:**

| Platform | OS | Path |
|----------|------|------|
| Steam | Windows | `C:\Program Files (x86)\Steam\steamapps\common\Satisfactory` |
| Steam | Linux | `~/.steam/steam/steamapps/common/Satisfactory` |
| Epic | Windows | `C:\Program Files\Epic Games\Satisfactory` |
| Heroic | Linux | `~/Games/Heroic/Satisfactory` |
| Lutris | Linux | `~/Games/Satisfactory` |

### Windows: "Execution policy" error

Run this command first:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Windows: "Access denied" error

Run PowerShell as Administrator, or check that Satisfactory is not running.

### Linux: "command not found" errors

Install required tools:

```bash
# Ubuntu/Debian
sudo apt install curl jq unzip

# Fedora
sudo dnf install curl jq unzip

# Arch
sudo pacman -S curl jq unzip

# macOS (with Homebrew)
brew install curl jq unzip
```

### Mods not working in game

1. Ensure the game is fully closed before running the installer
2. Verify mods are in `<game>/FactoryGame/Mods/`
3. Check that mod versions match the server
4. Try running the installer again

### Download failed

- Check your internet connection
- Some mods may not have Windows versions (server-only)
- Try running the script again

## Backup Location

Existing mods are backed up to:

**Windows:**
```
%USERPROFILE%\SatisfactoryModBackups\mods-backup-YYYYMMDD-HHMMSS
```

**Linux/macOS:**
```
~/SatisfactoryModBackups/mods-backup-YYYYMMDD-HHMMSS
```

## Requirements

### Windows (GUI Application - Recommended)
- Windows 10/11
- Internet connection
- Satisfactory game installed
- If running from source: Python 3.8+ with dependencies from `requirements-gui.txt`

### Windows (Batch File - install-mods.bat)
- Windows 10/11 (uses built-in curl and tar)
- Internet connection
- Satisfactory game installed

### Windows (PowerShell - install-client-mods.ps1)
- Windows 10/11
- PowerShell 5.1 or later (included in Windows)
- Internet connection
- Satisfactory game installed

### Linux/macOS
- curl, jq, unzip
- Internet connection
- Satisfactory game installed (Steam, Heroic, or Lutris)

## File Structure

```
scripts/mods/client/
├── mod_installer_gui.py       # Main GUI application
├── mod_installer_core.py      # Core logic (path detection, API, downloads)
├── install-mods.bat           # Windows batch installer (backup)
├── install-client-mods.ps1    # Windows PowerShell installer
├── install-client-mods.sh     # Linux/macOS bash installer
├── requirements-gui.txt       # Python dependencies
├── build_exe.py               # PyInstaller build script
└── assets/
    └── icon.ico               # Application icon (optional)
```

## Support

If you have issues:
1. Check the troubleshooting section above
2. Make sure your game version matches the server
3. Contact the server administrator
