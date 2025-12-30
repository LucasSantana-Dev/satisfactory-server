# Client Mod Installation Guide

This guide explains how to install the required mods on your game client to connect to the Satisfactory server.

## Why Mods Are Needed

The server uses mods to enhance the gameplay experience. **Your game client must have the same mods installed** to connect and play on the server.

## Installation Methods

### Method 1: GUI Application (Recommended!)

A modern desktop application with a visual interface - no command line needed!

**Option A: Pre-built Executable**
1. Download `SatisfactoryModInstaller.exe` from the server owner
2. **Double-click** to run
3. Select the mods you want (required mods are pre-selected)
4. Click "Install Selected Mods"
5. Done!

**Option B: Run from Python**
```powershell
# Install Python dependencies
pip install customtkinter requests Pillow

# Run the application
python mod_installer_gui.py
```

**Features:**
- Dark/Light mode toggle
- Checkbox selection for each mod
- Real-time download progress
- Built-in verification tool
- Log viewer for troubleshooting
- Less likely to trigger antivirus warnings

**If you don't see a "MODS" button in the game menu after installation:**
1. Click "Verify Installation" in the app
2. Check if SML shows as properly installed
3. If not, try reinstalling

---

### Method 2: Batch File (Backup Method)

If the GUI application doesn't work, try this simpler command-line method:

1. Download `install-mods.bat` from the server owner
2. **Double-click** the file to run it
3. Follow the on-screen instructions

> **Note:** Some antivirus software may flag batch files. Use the GUI application if you experience issues.

---

### Method 3: PowerShell Script (Advanced)

For advanced users who want more control:

Open PowerShell (press `Win + X`, then select "Windows PowerShell") and run:

```powershell
# Download and execute the installer
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
irm https://raw.githubusercontent.com/YOUR_USERNAME/satisfactory-server/main/scripts/mods/client/install-client-mods.ps1 -OutFile install-client-mods.ps1
.\install-client-mods.ps1
```

#### What the Scripts Do

1. **Detects your Satisfactory installation**
   - Checks Steam registry and library folders
   - Checks Epic Games manifests and common paths
   - Falls back to common default locations

2. **Creates a backup**
   - Backs up existing mods to `%USERPROFILE%\SatisfactoryModBackups\`
   - Preserves your current mod setup

3. **Downloads mods from ficsit.app**
   - Uses the official mod repository API
   - Downloads Windows-compatible versions
   - Gets the latest compatible versions

4. **Installs mods correctly**
   - Extracts mod files to the correct structure
   - Places mods in `<game>\FactoryGame\Mods\`
   - Handles all dependencies automatically

#### Advanced Options

```powershell
# If game path detection fails, specify manually
.\install-client-mods.ps1 -GamePath "D:\Games\Satisfactory"

# Skip backup creation
.\install-client-mods.ps1 -SkipBackup

# Install only quality-of-life mods
.\install-client-mods.ps1 -CategoryFilter "quality-of-life"

# Install only content mods
.\install-client-mods.ps1 -CategoryFilter "content"
```

### Method 3: Using Satisfactory Mod Manager (SMM)

If you prefer a GUI tool or the automatic scripts don't work:

1. **Download SMM**
   - Visit [Satisfactory Mod Manager Releases](https://github.com/satisfactorymodding/SatisfactoryModManager/releases)
   - Download the latest `.exe` installer
   - Run the installer

2. **Install each mod**
   - Open SMM
   - Search for each mod listed below
   - Click "Install" for each mod
   - Ensure versions match the server

**Required Mods to Install via SMM:**

| Priority | Mod Name | Search Term |
|----------|----------|-------------|
| 1 | Satisfactory Mod Loader | SML |
| 1 | Pak Utility Mod | UtilityMod |
| 2 | Smart! | SmartFoundations |
| 2 | Micro Manage | MicroManage |
| 2 | Efficiency Checker Mod | EfficiencyCheckerMod |
| 2 | Infinite Zoop | InfiniteZoop |
| 2 | Infinite Nudge | InfiniteNudge |
| 2 | Structural Solutions | SS_Mod |
| 2 | Modular Load Balancers | LoadBalancers |
| 2 | MAM Enhancer | MAMTips |
| 2 | MiniMap | MiniMap |
| 3 | Refined Power | RefinedPower |
| 3 | Ficsit Farming | FicsitFarming |
| 3 | Teleporter | Teleporter |
| 3 | Linear Motion | LinearMotion |
| 3 | Mk++ | MK22k20 |
| 3 | Fluid Extras | AB_FluidExtras |
| 3 | Storage Teleporter | StorageTeleporter |
| 3 | Big Storage Tank | BigStorageTank |
| 3 | Container Screens | ContainerScreen |
| 3 | Item Dispenser | Dispenser |
| 4 | EasyCheat | EasyCheat |
| 4 | PowerSuit | PowerSuit |
| 4 | Additional 300 Inventory Slots | Additional_300_Inventory_Slots |

### Method 4: Manual Installation

For advanced users who want full control:

1. **Find your game's Mods folder**
   - Steam: `C:\Program Files (x86)\Steam\steamapps\common\Satisfactory\FactoryGame\Mods`
   - Epic: `C:\Program Files\Epic Games\Satisfactory\FactoryGame\Mods`

2. **Download mods from ficsit.app**
   - Visit [ficsit.app](https://ficsit.app)
   - Search for each mod
   - Click "Versions" → Download the latest Windows version

3. **Extract and install**
   - Extract the `.smod` file (it's a ZIP)
   - Copy the mod folder to `FactoryGame\Mods\`
   - Structure should be: `Mods\ModName\ModName.pak`

## Mod Categories

### Dependencies (Always Required)

These must be installed first:

| Mod | Description |
|-----|-------------|
| **SML** | Satisfactory Mod Loader - The core mod loader required by all mods |
| **UtilityMod** | Pak Utility Mod - Common dependency for many mods |

### Quality of Life

Improvements to the gameplay experience without changing core mechanics:

| Mod | Description |
|-----|-------------|
| **Smart!** | Mass placement of foundations, walls, pillars. Essential for large factories. |
| **Micro Manage** | Precise positioning, rotation, and scaling of objects. |
| **Efficiency Checker** | See efficiency percentages on machines to identify bottlenecks. |
| **Infinite Zoop** | Remove the zoop limit when placing buildings. |
| **Infinite Nudge** | Remove distance limits when nudging objects. |
| **Structural Solutions** | Additional structural building pieces and options. |
| **Load Balancers** | Smart load balancing for conveyor belts. |
| **MAM Enhancer** | Better MAM research interface with helpful tips. |
| **MiniMap** | In-game minimap overlay for easier navigation. |

### Content

New items, buildings, and gameplay systems:

| Mod | Description |
|-----|-------------|
| **Refined Power** | Solar panels, wind turbines, and advanced nuclear options. |
| **Ficsit Farming** | Grow crops and produce food items. |
| **Teleporter** | Build teleporter pads for instant travel. |
| **Linear Motion** | Moving platforms, elevators, and conveyors. |
| **Mk++** | Higher tier versions of vanilla buildings. |
| **Fluid Extras** | Additional pipes, pumps, and fluid handling. |
| **Storage Teleporter** | Wirelessly move items between storage. |
| **Big Storage Tank** | Large capacity fluid storage tanks. |
| **Container Screens** | Display screens showing container contents. |
| **Item Dispenser** | Automatically dispense items from storage. |

### Cheats (Optional)

For testing or relaxed gameplay:

| Mod | Description |
|-----|-------------|
| **EasyCheat** | Simple cheat menu for spawning items. |
| **PowerSuit** | Enhanced player abilities (flight, speed, etc.). |
| **Additional 300 Inventory Slots** | Expanded player inventory. |

## Troubleshooting

### Script won't run / Execution Policy Error

```powershell
# Allow running local scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Could not find Satisfactory installation"

The script checks these locations:
- Steam registry and library folders
- Epic Games manifests
- Common installation paths

If detection fails, specify the path manually:

```powershell
.\install-client-mods.ps1 -GamePath "D:\Your\Path\Satisfactory"
```

### "No Windows version for mod"

Some mods are server-only and don't have Windows client versions. This is normal - the script will skip these automatically.

### Mods show as installed but don't work in-game

1. **Close Satisfactory completely** before running the installer
2. **Verify mod structure**: Each mod should be in its own folder under `FactoryGame\Mods\`
3. **Check for conflicts**: Remove old mod files and run the installer again
4. **Verify game files**: Use Steam/Epic to verify game integrity

### Can't connect to server

1. **Mod version mismatch**: Run the installer again to get latest versions
2. **Missing mods**: Ensure all mods are installed
3. **Game version**: Your game version must match the server

### Download errors

- Check your internet connection
- Try running the script again (temporary API issues)
- Use SMM as an alternative

## Verifying Installation

After running the installer, check your mods folder:

```
Satisfactory\
└── FactoryGame\
    └── Mods\
        ├── SML\
        │   ├── SML.uplugin
        │   └── SML-Windows.pak
        ├── UtilityMod\
        │   └── ...
        ├── SmartFoundations\
        │   └── ...
        └── ... (other mods)
```

Each mod folder should contain:
- `.uplugin` file (mod metadata)
- `.pak` file (mod content)
- Optional: `.ucas` and `.utoc` files

## Updating Mods

To update mods to the latest versions:

1. Close Satisfactory
2. Run the installer script again
3. The script will backup old mods and install fresh versions

Or using SMM:
1. Open SMM
2. Click "Update All" if available

## Removing Mods

To remove all mods:

1. Navigate to `<game>\FactoryGame\Mods\`
2. Delete all folders inside
3. Keep the `Mods` folder itself

Or restore from backup:

1. Go to `%USERPROFILE%\SatisfactoryModBackups\`
2. Find the backup you want
3. Copy contents back to `FactoryGame\Mods\`

## Need Help?

1. Check this troubleshooting guide
2. Ask in the server's Discord
3. Visit [Satisfactory Modding Discord](https://discord.gg/satisfactorymodding)
4. Check [ficsit.app](https://ficsit.app) for mod-specific issues
