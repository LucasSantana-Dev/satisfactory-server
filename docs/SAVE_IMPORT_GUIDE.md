# Satisfactory Save Import Guide

This guide explains how to import your local Satisfactory save files to the dedicated server.

## Quick Import

Use the import script:
```bash
./scripts/import-save.sh <path-to-save-file.sav> [save-name]
```

**Example:**
```bash
./scripts/import-save.sh ~/Downloads/MyWorld.sav MyServerWorld
```

## Finding Your Save Files

### Windows
**Location:**
```
%LOCALAPPDATA%\FactoryGame\Saved\SaveGames\server\
```

**Full path example:**
```
C:\Users\YourName\AppData\Local\FactoryGame\Saved\SaveGames\server\
```

**To find it:**
1. Press `Win + R`
2. Type: `%LOCALAPPDATA%\FactoryGame\Saved\SaveGames\server\`
3. Press Enter

### Linux
**Location:**
```
~/.config/Epic/FactoryGame/Saved/SaveGames/server/
```

**Or:**
```
~/.local/share/Epic/FactoryGame/Saved/SaveGames/server/
```

### macOS
**Location:**
```
~/Library/Application Support/Epic/FactoryGame/Saved/SaveGames/server/
```

## Save File Types

Satisfactory uses `.sav` files. You'll typically find:
- **World saves**: `Save_*.sav` (e.g., `Save_0001.sav`)
- **Server settings**: `ServerSettings.*.sav` (e.g., `ServerSettings.7777.sav`)

## Import Methods

### Method 1: Using the Import Script (Recommended)

1. **Stop the server** (recommended):
   ```bash
   docker compose stop satisfactory-server
   ```

2. **Run the import script:**
   ```bash
   ./scripts/import-save.sh /path/to/your/save.sav MySaveName
   ```

3. **The script will:**
   - Create a backup of existing saves
   - Copy your save file to the server
   - Set proper permissions
   - Optionally restart the server

4. **Start the server:**
   ```bash
   docker compose start satisfactory-server
   ```

### Method 2: Manual Import

1. **Stop the server:**
   ```bash
   docker compose stop satisfactory-server
   ```

2. **Create backup of existing saves:**
   ```bash
   cd /home/luk-server/satisfactory-server
   tar -czf data/backups/manual-$(date +%Y%m%d-%H%M%S).tar.gz data/saved/server/
   ```

3. **Copy your save file:**
   ```bash
   # Create server save directory if it doesn't exist
   mkdir -p data/saved/server

   # Copy your save file
   cp /path/to/your/save.sav data/saved/server/MySave.sav

   # Set permissions
   chmod 644 data/saved/server/MySave.sav
   ```

4. **Start the server:**
   ```bash
   docker compose start satisfactory-server
   ```

### Method 3: Using Docker Exec

If the server is running:

```bash
# Copy save file into container
docker cp /path/to/your/save.sav satisfactory-server:/config/saved/server/MySave.sav

# Set permissions
docker compose exec satisfactory-server chmod 644 /config/saved/server/MySave.sav
```

## Server Save Directory Structure

After import, your saves will be in:
```
data/saved/server/
├── MySave.sav
├── AnotherSave.sav
└── ...
```

The server will automatically detect saves in this directory.

## Configuring the Server to Use Your Save

1. **Access server console:**
   ```bash
   docker compose exec satisfactory-server bash
   ```

2. **Or check server settings:**
   ```bash
   # View server settings file
   cat data/saved/ServerSettings.7777.sav
   ```

3. **The server should automatically detect saves**, but you may need to:
   - Restart the server
   - Select the save in-game when connecting
   - Configure via server admin panel (if available)

## Importing Multiple Saves

You can import multiple save files:

```bash
# Import first save
./scripts/import-save.sh ~/Saves/Save1.sav World1

# Import second save
./scripts/import-save.sh ~/Saves/Save2.sav World2
```

All saves will be available in the server's save list.

## Backup Before Import

The import script automatically creates a backup, but you can also create one manually:

```bash
# Create backup
tar -czf data/backups/before-import-$(date +%Y%m%d-%H%M%S).tar.gz data/saved/server/

# List backups
ls -lh data/backups/
```

## Restoring from Backup

If something goes wrong:

```bash
# Stop server
docker compose stop satisfactory-server

# Extract backup
cd data/backups
tar -xzf before-import-YYYYMMDD-HHMMSS.tar.gz -C ../

# Start server
docker compose start satisfactory-server
```

## Troubleshooting

### Save File Not Appearing

1. **Check file location:**
   ```bash
   ls -lh data/saved/server/
   ```

2. **Verify file permissions:**
   ```bash
   chmod 644 data/saved/server/*.sav
   ```

3. **Check server logs:**
   ```bash
   docker compose logs satisfactory | grep -i save
   ```

4. **Restart server:**
   ```bash
   docker compose restart satisfactory-server
   ```

### Save File Corrupted

If the save file is corrupted:

1. **Restore from backup:**
   ```bash
   # Use the backup created before import
   tar -xzf data/backups/pre-import-*.tar.gz -C ./
   ```

2. **Verify save file integrity:**
   - Try opening it in Satisfactory locally first
   - Ensure it's a valid `.sav` file

### Permission Denied

If you get permission errors:

```bash
# Fix ownership
sudo chown -R $(id -u):$(id -g) data/saved/

# Fix permissions
chmod -R 644 data/saved/server/*.sav
```

### Server Won't Load Save

1. **Check save file format:**
   - Ensure it's a server save, not a local save
   - Server saves are typically in the `server/` subdirectory

2. **Check server logs:**
   ```bash
   docker compose logs satisfactory | tail -50
   ```

3. **Verify save compatibility:**
   - Save must match server game version
   - Check if mods are required (if save uses mods)

## Best Practices

1. **Always backup before importing:**
   - The import script does this automatically
   - Keep backups for at least a week

2. **Stop server before importing:**
   - Prevents file corruption
   - Ensures clean import

3. **Test save locally first:**
   - Open save in Satisfactory locally
   - Verify it's not corrupted

4. **Use descriptive names:**
   - Name saves clearly (e.g., `MyWorld-v2.sav`)
   - Avoid special characters

5. **Keep backups:**
   - Regular backups are automated
   - Manual backups before major changes

## Additional Notes

- **Save file size:** Large saves (100MB+) may take time to copy
- **Server restart:** Server may need restart to detect new saves
- **Multiple saves:** Server can have multiple saves available
- **Save selection:** Players select save when connecting to server

## Related Documentation

- **Backup Guide**: See `README.md` - Backup and Restore section
- **Server Management**: See `README.md` - Management Commands
- **Troubleshooting**: See `README.md` - Troubleshooting section

