# Satisfactory Mods Installation Guide

This guide explains how to install and manage mods on your Satisfactory dedicated server.

## Prerequisites

- SFTP client (FileZilla, Cyberduck, WinSCP, or command-line `sftp`)
- Satisfactory Mod Manager (SMM) installed on your game client
- Access to [ficsit.app](https://ficsit.app) to download mods

## SFTP Connection

The server includes an SFTP container for easy mod file management.

### Connection Details

- **Host**: Your server IP address (or `172.19.0.1` if connecting via WARP)
- **Port**: `2222` (default, configurable via `SFTP_PORT` in `.env`)
- **Username**: `satisfactory` (configurable via `SFTP_USER` in `.env`)
- **Password**: Set in `.env` file via `SFTP_PASSWORD`
- **Protocol**: SFTP

### Connect via Command Line

```bash
sftp -P 2222 satisfactory@<server-ip>
```

### Connect via GUI Client

**FileZilla:**
1. Open FileZilla
2. File → Site Manager → New Site
3. Protocol: **SFTP - SSH File Transfer Protocol**
4. Host: Your server IP
5. Port: `2222`
6. Logon Type: **Normal**
7. User: `satisfactory`
8. Password: (from `.env` file)
9. Connect

**Cyberduck:**
1. Open Cyberduck
2. New Connection
3. Protocol: **SFTP (SSH File Transfer Protocol)**
4. Server: Your server IP
5. Port: `2222`
6. Username: `satisfactory`
7. Password: (from `.env` file)
8. Connect

## Mod Installation Location

Mods must be placed in:
```
/home/satisfactory/data/gamefiles/FactoryGame/Mods/
```

When connected via SFTP, navigate to:
```
data/gamefiles/FactoryGame/Mods/
```

## Recommended Mods

### Quality of Life Mods

| Mod | Description | Link |
|-----|-------------|------|
| **SMART!** | Mass building of foundations, walls, and more. Essential for large builds. | [ficsit.app](https://ficsit.app/mod/Smart) |
| **Micro Manage** | Precise object positioning, rotation, and scaling. Perfect for fine-tuning builds. | [ficsit.app](https://ficsit.app/mod/MicroManage) |
| **Efficiency Checker** | Monitor production line efficiency and identify bottlenecks. | [ficsit.app](https://ficsit.app/mod/EfficiencyChecker) |
| **Item Hopper** | Easily move items between inventories. Great for inventory management. | [ficsit.app](https://ficsit.app/mod/ItemHopper) |
| **Pak Utility Mod** | Required dependency for many mods. Install this first! | [ficsit.app](https://ficsit.app/mod/PakUtility) |

### Content Mods

| Mod | Description | Link |
|-----|-------------|------|
| **Refined Power** | New power generation options (solar, wind, nuclear variants). | [ficsit.app](https://ficsit.app/mod/RefinedPower) |
| **Ficsit Farming** | Farming mechanics and food production. Adds new gameplay dimension. | [ficsit.app](https://ficsit.app/mod/FicsitFarming) |
| **Teleporter** | Instant travel between locations. Saves time on large maps. | [ficsit.app](https://ficsit.app/mod/Teleporter) |
| **Linear Motion** | Moving platforms and elevators. Great for vertical factories. | [ficsit.app](https://ficsit.app/mod/LinearMotion) |

## Installation Methods

### Method 1: Automatic Installation (Recommended)

Use the automatic installation script to download and install all recommended mods:

```bash
cd /home/luk-server/satisfactory-server
python3 scripts/mods/install.py
```

**Selective Installation:**
```bash
# Install only Quality of Life mods
python3 scripts/mods/install.py --qol-only

# Install only Content mods
python3 scripts/mods/install.py --content-only

# Install only Cheat mods
python3 scripts/mods/install.py --cheat-only
```

**Note:** Some mods are client-only and don't have Linux server builds. These will be skipped automatically.

### Method 2: Manual Installation

If automatic download fails, use manual installation:

#### Step 1: Download Mods

1. Visit [ficsit.app](https://ficsit.app)
2. Browse or search for mods
3. Click on a mod to view details
4. Click "Download" or "Install" button
5. Save the `.pak` file to your computer

#### Step 2: Install on Server

**Option A: Using Manual Installation Script**

```bash
# Install single mod
./scripts/manual-mod-install.sh ~/Downloads/PakUtility.pak

# Install multiple mods
./scripts/manual-mod-install.sh ~/Downloads/*.pak
```

**Option B: Using SFTP**

1. Connect to the server via SFTP (see connection details above)
2. Navigate to `data/gamefiles/FactoryGame/Mods/`
3. Upload the downloaded mod `.pak` files
4. Ensure file permissions are readable (644)

### 3. Install on Client

**Important:** Both server AND client must have the same mods installed with matching versions!

1. Install [Satisfactory Mod Manager (SMM)](https://github.com/satisfactorymodding/SatisfactoryModManager/releases)
2. Open SMM
3. Install the same mods you installed on the server
4. Ensure mod versions match exactly

### 4. Restart Server

After uploading mods to the server:

```bash
cd /home/luk-server/satisfactory-server
docker compose restart satisfactory
```

Wait for the server to fully start (check logs: `docker compose logs -f satisfactory`)

### 5. Verify Mods

1. Connect to the server in-game
2. Check the mod list in the server browser
3. Verify all mods are loaded correctly

## Mod File Structure

The mods directory structure should look like:

```
data/gamefiles/FactoryGame/Mods/
├── UtilityMod/
│   ├── UtilityMod.uplugin
│   ├── UtilityModFactoryGame-LinuxServer.pak
│   ├── UtilityModFactoryGame-LinuxServer.ucas
│   └── UtilityModFactoryGame-LinuxServer.utoc
├── SmartFoundations/
│   └── ...
├── EfficiencyCheckerMod/
│   └── ...
└── ...
```

Each mod has its own directory containing:
- `.uplugin` - Plugin metadata
- `.pak` - Main mod content
- `.ucas` and `.utoc` - Additional Unreal Engine asset files

## Troubleshooting

### Mods Not Loading

1. **Check file permissions:**
   ```bash
   docker compose exec satisfactory ls -la /config/gamefiles/FactoryGame/Mods/
   ```
   Files should be readable (644)

2. **Verify mod versions match:**
   - Server and client must have identical mod versions
   - Check mod version in SMM and compare with server files

3. **Check server logs:**
   ```bash
   docker compose logs satisfactory | grep -i mod
   ```

4. **Restart server:**
   ```bash
   docker compose restart satisfactory
   ```

### Connection Issues

1. **SFTP container not running:**
   ```bash
   docker compose ps sftp-server
   docker compose up -d sftp-server
   ```

2. **Port not accessible:**
   - Verify `SFTP_PORT` in `.env` matches your connection
   - Check firewall rules if connecting from outside

3. **Wrong credentials:**
   - Check `SFTP_USER` and `SFTP_PASSWORD` in `.env`
   - Restart SFTP container after changing credentials:
     ```bash
     docker compose restart sftp-server
     ```

### Mod Compatibility Issues

- Some mods may conflict with each other
- Check mod descriptions on ficsit.app for compatibility notes
- Start with essential mods (Pak Utility, SMART!) and add others gradually
- Test in a single-player game first before adding to server

## Best Practices

1. **Always backup before adding mods:**
   ```bash
   ./scripts/backup.sh
   ```

2. **Install mods one at a time** to identify any conflicts

3. **Keep mods updated** - check ficsit.app regularly for updates

4. **Document your mod list** - keep track of which mods are installed

5. **Test mods in single-player** before adding to server

6. **Coordinate with players** - ensure all players have the same mods installed

## Mod Dependencies

Many mods require **Pak Utility Mod** as a dependency. Always install this first!

Check each mod's page on ficsit.app for specific dependency requirements.

## Removing Mods

1. Connect via SFTP
2. Navigate to `data/gamefiles/FactoryGame/Mods/`
3. Delete the mod `.pak` file(s)
4. Restart server
5. Remove from client using SMM

## Additional Resources

- [Satisfactory Modding Documentation](https://docs.ficsit.app/)
- [Satisfactory Mod Manager GitHub](https://github.com/satisfactorymodding/SatisfactoryModManager)
- [ficsit.app - Mod Repository](https://ficsit.app)
- [Satisfactory Modding Discord](https://discord.gg/satisfactorymodding)

---

**Note:** Mods can significantly change gameplay. Always backup your saves before installing new mods, and test thoroughly before using in production.
