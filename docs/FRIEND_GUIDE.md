# Friend Connection Guide - Satisfactory Server

This guide will help you connect to the Satisfactory server using Cloudflare WARP.

## Prerequisites

- Satisfactory game installed (Steam or Epic Games)
- Internet connection
- Administrator access to install WARP client
- Required mods installed (see Step 5)

## Step 1: Install Cloudflare WARP Client

1. Download WARP client for your operating system:
   - **Windows**: [Download WARP for Windows](https://1.1.1.1/)
   - **macOS**: [Download WARP for macOS](https://1.1.1.1/)
   - **Linux**: [Download WARP for Linux](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/warp/download-warp/)

2. Install the WARP client:
   - **Windows**: Run the installer and follow the setup wizard
   - **macOS**: Open the DMG file and drag WARP to Applications
   - **Linux**: Follow distribution-specific instructions

## Step 2: Enroll Your Device

1. Open the Cloudflare WARP application
2. Click on **Settings** (gear icon)
3. Navigate to **Account** or **Preferences**
4. Click **Login with Cloudflare Zero Trust** or **Connect to organization**
5. Enter the team domain: `luk-homelab` (your team name)
   - Full domain: `luk-homelab.cloudflareaccess.com`
6. Complete enrollment using one of these methods:

### Method A: Email Enrollment (If your email was added)
- Enter your email address
- Check your email for a verification link
- Click the link to complete enrollment

### Method B: One-time PIN (If provided)
- Click **Use PIN** or **One-time PIN**
- Enter the PIN provided by the server owner
- Click **Enroll**

## Step 3: Verify WARP Connection

1. After enrollment, WARP should automatically connect
2. You should see a green shield icon or "Connected" status
3. The WARP icon in your system tray should show as active

**Important**: WARP must be connected for the game connection to work!

## Step 4: Connect to Satisfactory Server

### Option 1: Using Domain Name (Recommended)

1. Open Satisfactory
2. Go to **Server Manager** (from main menu)
3. Click **Add Server**
4. Enter the following:
   - **Server Address**: `satisfactory.luk-homeserver.com.br`
   - **Port**: `7777`
   - **Server Name**: `Luk's Satisfactory Server` (optional)
5. Click **Add** or **Connect**

**Note**: If the domain doesn't work, use the IP address as fallback (see Option 2).

### Option 2: Direct IP Connection (Fallback)

1. Open Satisfactory
2. Go to **Server Manager** (from main menu)
3. Click **Add Server**
4. Enter the following:
   - **Server Address**: `172.19.0.2`
   - **Port**: `7777`
   - **Server Name**: `Luk's Satisfactory Server` (optional)
5. Click **Add** or **Connect**

### Option 3: Using Server Browser

1. Open Satisfactory
2. Go to **Server Manager**
3. Click **Refresh** to see available servers
4. Look for the server in the list (may appear as `satisfactory.luk-homeserver.com.br:7777` or `172.19.0.2:7777`)
5. Click **Join** or double-click the server

## Step 5: Install Required Mods

The server uses mods to enhance gameplay. **You must install the same mods** to connect.

### Quick Install (Recommended)

**Option A: GUI Application (Best!)**

1. Download `SatisfactoryModInstaller.exe` from the server owner
2. **Double-click** to run
3. Select mods (required ones are pre-selected)
4. Click "Install Selected Mods"
5. Done!

This has a nice visual interface, progress bar, and is less likely to trigger antivirus warnings.

**Option B: Batch File**

1. Download `install-mods.bat` from the server owner
2. **Double-click** the file to run it
3. Follow the on-screen instructions

**Option C: PowerShell**

Open PowerShell (press `Win + X` → "Windows PowerShell") and run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
irm https://raw.githubusercontent.com/YOUR_USERNAME/satisfactory-server/main/scripts/mods/client/install-client-mods.ps1 -OutFile install-mods.ps1
.\install-mods.ps1
```

The script will:
1. Automatically detect your Satisfactory installation
2. Download all required mods from ficsit.app
3. Install them to the correct location

### Manual Install

If the scripts don't work, use [Satisfactory Mod Manager (SMM)](https://github.com/satisfactorymodding/SatisfactoryModManager/releases):

1. Download and install SMM
2. Install these mods (search by name):
   - **SML** (Satisfactory Mod Loader)
   - **UtilityMod** (Pak Utility)
   - Smart!, Micro Manage, Efficiency Checker
   - Infinite Zoop, Infinite Nudge
   - And other mods as listed in [CLIENT_MODS_INSTALL.md](CLIENT_MODS_INSTALL.md)

### Verify Mods Are Installed

Check that `<game>\FactoryGame\Mods\` contains mod folders like:
- `SML\`
- `UtilityMod\`
- `SmartFoundations\`
- etc.

For detailed instructions, see [CLIENT_MODS_INSTALL.md](CLIENT_MODS_INSTALL.md).

## Troubleshooting

### WARP Won't Connect

1. **Check your internet connection**
   - Ensure you have an active internet connection
   - Try disabling and re-enabling WARP

2. **Verify enrollment**
   - Make sure you completed the enrollment process
   - Check that your email/PIN was correct
   - Try logging out and back into WARP

3. **Firewall issues**
   - Ensure WARP is allowed through your firewall
   - Windows: Check Windows Firewall settings
   - macOS: Check System Preferences > Security & Privacy

4. **Re-enroll device**
   - In WARP settings, click **Logout** or **Disconnect**
   - Follow Step 2 again to re-enroll

### Can't See Server in Satisfactory

1. **Verify WARP is connected**
   - Check WARP status shows "Connected"
   - Try disconnecting and reconnecting WARP

2. **Use direct connection**
   - Don't rely on server browser
   - Use Option 1 above with domain: `satisfactory.luk-homeserver.com.br:7777`
   - Or Option 2 with IP: `172.19.0.2:7777` (fallback)

3. **Check server status**
   - Ask the server owner if the server is running
   - Server owner can check with: `docker compose ps`

### Connection Timeout or Failed

1. **WARP must be enabled**
   - This is critical - the server is only accessible through WARP
   - Ensure WARP shows as connected before trying to join

2. **Try restarting WARP**
   - Disconnect WARP
   - Wait 10 seconds
   - Reconnect WARP
   - Try connecting to server again

3. **Check server address**
   - Try domain first: `satisfactory.luk-homeserver.com.br:7777`
   - If domain doesn't work, use IP: `172.19.0.2:7777`
   - Ensure WARP is connected before trying to connect

### Game Lags or Disconnects

1. **Network performance**
   - WARP adds a small latency overhead
   - This is normal for secure tunneling

2. **Server resources**
   - Ask server owner to check server performance
   - Server may need more resources if multiple players are on

### Mod Issues

1. **"Mod version mismatch" error**
   - Run the mod installer script again to update mods
   - Or update mods manually in SMM

2. **Mods not loading**
   - Ensure Satisfactory is fully closed before installing mods
   - Verify mods are in `<game>\FactoryGame\Mods\`
   - Each mod should have its own folder with `.pak` files

3. **Script won't run**
   - Run this first: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
   - Or use SMM as an alternative

## Important Notes

- **WARP must be running**: The server is only accessible when WARP is connected
- **Use domain name**: Connect using `satisfactory.luk-homeserver.com.br:7777` (easier to remember)
- **IP fallback**: If domain doesn't work, use `172.19.0.2:7777` as fallback
- **UDP support**: WARP enables UDP traffic needed for Satisfactory gameplay
- **Always connected**: Keep WARP running while playing Satisfactory

## Getting Help

If you continue to have issues:

1. Check with the server owner that:
   - Server is running and healthy
   - Your device is enrolled in Zero Trust
   - Private network routing is configured

2. Provide the server owner with:
   - Your email address (if using email enrollment)
   - Error messages you're seeing
   - Screenshots of WARP connection status

## System Requirements

- **Windows**: Windows 10/11 (64-bit)
- **macOS**: macOS 10.15 or later
- **Linux**: Most modern distributions
- **RAM**: 4GB minimum (8GB recommended)
- **Network**: Stable internet connection

## Security Note

WARP encrypts your connection to the server, providing secure access without exposing the server's public IP address. This is a security feature, not a bug!

---

**Need the enrollment PIN or team name?** Contact the server owner.
