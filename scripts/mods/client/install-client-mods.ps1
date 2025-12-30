<#
.SYNOPSIS
    Satisfactory Client Mod Installer
    Downloads and installs mods from ficsit.app for Windows game clients.

.DESCRIPTION
    This script automatically:
    1. Detects your Satisfactory game installation (Steam or Epic Games)
    2. Downloads the required mods from ficsit.app API
    3. Installs them to match the server's mod configuration

    Run this script to ensure your game has the same mods as the server.

.PARAMETER GamePath
    Optional. Manually specify the Satisfactory installation path.

.PARAMETER SkipBackup
    Skip creating a backup of existing mods before installation.

.PARAMETER CategoryFilter
    Install only mods from a specific category: dependency, quality-of-life, content, cheat

.EXAMPLE
    .\install-client-mods.ps1

.EXAMPLE
    .\install-client-mods.ps1 -GamePath "D:\Games\Satisfactory"

.EXAMPLE
    .\install-client-mods.ps1 -CategoryFilter "quality-of-life"

.NOTES
    Version: 1.0.0
    Author: Satisfactory Server Management
    Requires: PowerShell 5.1+, Windows 10/11
#>

param(
    [Parameter(HelpMessage = "Manually specify Satisfactory installation path")]
    [string]$GamePath = "",

    [Parameter(HelpMessage = "Skip backup of existing mods")]
    [switch]$SkipBackup = $false,

    [Parameter(HelpMessage = "Install only mods from specific category")]
    [ValidateSet("dependency", "quality-of-life", "content", "cheat", "")]
    [string]$CategoryFilter = ""
)

# =============================================================================
# Configuration
# =============================================================================

$Script:API_URL = "https://api.ficsit.app"
$Script:GRAPHQL_ENDPOINT = "$Script:API_URL/v2/query"
$Script:TEMP_DIR = Join-Path $env:TEMP "SatisfactoryModInstaller"
$Script:TARGET_PLATFORM = "Windows"

# Embedded mod list (matches server configuration)
$Script:MODS_LIST = @'
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
'@

# =============================================================================
# Output Functions
# =============================================================================

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# =============================================================================
# Game Path Detection
# =============================================================================

function Find-SteamSatisfactory {
    <#
    .SYNOPSIS
        Find Satisfactory installation via Steam
    #>

    Write-Info "Searching for Steam installation..."

    # Method 1: Check Steam uninstall registry for Satisfactory
    $steamAppKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 526870"
    if (Test-Path $steamAppKey) {
        try {
            $installPath = (Get-ItemProperty -Path $steamAppKey -ErrorAction Stop).InstallLocation
            if ($installPath -and (Test-Path $installPath)) {
                Write-Success "Found via Steam registry: $installPath"
                return $installPath
            }
        } catch { }
    }

    # Method 2: Parse Steam library folders
    $steamPaths = @(
        "$env:ProgramFiles (x86)\Steam",
        "$env:ProgramFiles\Steam",
        "C:\Steam",
        "D:\Steam",
        "E:\Steam"
    )

    foreach ($steamPath in $steamPaths) {
        $libraryFile = Join-Path $steamPath "steamapps\libraryfolders.vdf"
        if (Test-Path $libraryFile) {
            Write-Info "Parsing Steam library: $libraryFile"

            try {
                $content = Get-Content $libraryFile -Raw

                # Extract library paths from VDF
                $pathMatches = [regex]::Matches($content, '"path"\s+"([^"]+)"')
                $libraryPaths = @($steamPath)

                foreach ($match in $pathMatches) {
                    $libPath = $match.Groups[1].Value -replace '\\\\', '\'
                    if ($libPath -ne $steamPath) {
                        $libraryPaths += $libPath
                    }
                }

                # Check each library for Satisfactory
                foreach ($libPath in $libraryPaths) {
                    $satisfactoryPath = Join-Path $libPath "steamapps\common\Satisfactory"
                    if (Test-Path $satisfactoryPath) {
                        Write-Success "Found in Steam library: $satisfactoryPath"
                        return $satisfactoryPath
                    }
                }
            } catch {
                Write-Warning "Failed to parse Steam library file: $_"
            }
        }
    }

    # Method 3: Check common default paths
    $defaultPaths = @(
        "$env:ProgramFiles (x86)\Steam\steamapps\common\Satisfactory",
        "$env:ProgramFiles\Steam\steamapps\common\Satisfactory",
        "C:\Steam\steamapps\common\Satisfactory",
        "D:\SteamLibrary\steamapps\common\Satisfactory",
        "E:\SteamLibrary\steamapps\common\Satisfactory"
    )

    foreach ($path in $defaultPaths) {
        if (Test-Path $path) {
            Write-Success "Found at default path: $path"
            return $path
        }
    }

    return $null
}

function Find-EpicSatisfactory {
    <#
    .SYNOPSIS
        Find Satisfactory installation via Epic Games
    #>

    Write-Info "Searching for Epic Games installation..."

    # Method 1: Check Epic manifest files
    $manifestDir = "$env:ProgramData\Epic\EpicGamesLauncher\Data\Manifests"
    if (Test-Path $manifestDir) {
        $manifestFiles = Get-ChildItem -Path $manifestDir -Filter "*.item" -ErrorAction SilentlyContinue

        foreach ($manifest in $manifestFiles) {
            try {
                $content = Get-Content $manifest.FullName -Raw | ConvertFrom-Json

                # Check if this is Satisfactory (multiple possible app names)
                $satisfactoryApps = @("CrabEA", "CrabTest", "Satisfactory")
                if ($content.AppName -in $satisfactoryApps -or
                    $content.DisplayName -like "*Satisfactory*") {

                    $installPath = $content.InstallLocation
                    if ($installPath -and (Test-Path $installPath)) {
                        Write-Success "Found via Epic manifest: $installPath"
                        return $installPath
                    }
                }
            } catch { }
        }
    }

    # Method 2: Check Epic launcher registry
    $epicKey = "HKLM:\SOFTWARE\WOW6432Node\Epic Games\EpicGamesLauncher"
    if (Test-Path $epicKey) {
        try {
            $epicPath = (Get-ItemProperty -Path $epicKey -ErrorAction Stop).AppDataPath
            # Epic typically installs games in a default location
        } catch { }
    }

    # Method 3: Check common default paths
    $defaultPaths = @(
        "$env:ProgramFiles\Epic Games\Satisfactory",
        "$env:ProgramFiles\Epic Games\SatisfactoryExperimental",
        "C:\Epic Games\Satisfactory",
        "D:\Epic Games\Satisfactory",
        "E:\Epic Games\Satisfactory",
        "$env:ProgramFiles\Satisfactory",
        "D:\Games\Satisfactory",
        "E:\Games\Satisfactory"
    )

    foreach ($path in $defaultPaths) {
        if (Test-Path $path) {
            Write-Success "Found at default path: $path"
            return $path
        }
    }

    return $null
}

function Find-SatisfactoryPath {
    <#
    .SYNOPSIS
        Find Satisfactory installation (Steam or Epic)
    #>

    Write-Header "Detecting Satisfactory Installation"

    # Try Steam first (more common)
    $steamPath = Find-SteamSatisfactory
    if ($steamPath) {
        return @{
            Path = $steamPath
            Platform = "Steam"
        }
    }

    # Try Epic Games
    $epicPath = Find-EpicSatisfactory
    if ($epicPath) {
        return @{
            Path = $epicPath
            Platform = "Epic Games"
        }
    }

    return $null
}

function Validate-GamePath {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $false
    }

    # Check for key game files
    $expectedFiles = @(
        "FactoryGame\Binaries\Win64\FactoryGame-Win64-Shipping.exe",
        "FactoryGame\Content\Paks"
    )

    foreach ($file in $expectedFiles) {
        $fullPath = Join-Path $Path $file
        if (-not (Test-Path $fullPath)) {
            # Also check alternative structure
            $altPath = Join-Path $Path "FactoryGame"
            if (Test-Path $altPath) {
                return $true
            }
            return $false
        }
    }

    return $true
}

# =============================================================================
# API Functions
# =============================================================================

function Invoke-GraphQLQuery {
    param([string]$Query)

    $body = @{ query = $Query } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri $Script:GRAPHQL_ENDPOINT `
            -Method Post `
            -Body $body `
            -ContentType "application/json" `
            -TimeoutSec 30

        if ($response.errors) {
            Write-ErrorMsg "GraphQL error: $($response.errors | ConvertTo-Json)"
            return $null
        }

        return $response.data
    }
    catch {
        Write-ErrorMsg "API request failed: $_"
        return $null
    }
}

function Get-ModInfo {
    param([string]$ModReference)

    $query = @"
    query {
        getModByReference(modReference: "$ModReference") {
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
    }
"@

    $data = Invoke-GraphQLQuery -Query $query
    if ($data -and $data.getModByReference) {
        return $data.getModByReference
    }
    return $null
}

# =============================================================================
# Installation Functions
# =============================================================================

function New-ModsBackup {
    param([string]$ModsDir)

    if (-not (Test-Path $ModsDir)) {
        return $true
    }

    $existingMods = Get-ChildItem -Path $ModsDir -Directory -ErrorAction SilentlyContinue
    if ($existingMods.Count -eq 0) {
        return $true
    }

    Write-Info "Creating backup of existing mods..."

    $backupDir = Join-Path $env:USERPROFILE "SatisfactoryModBackups"
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    }

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = Join-Path $backupDir "mods-backup-$timestamp"

    try {
        Copy-Item -Path $ModsDir -Destination $backupPath -Recurse -Force
        Write-Success "Backup created: $backupPath"
        return $true
    }
    catch {
        Write-ErrorMsg "Failed to create backup: $_"
        return $false
    }
}

function Install-ModFromSmod {
    param(
        [string]$SmodPath,
        [string]$ModReference,
        [string]$ModsDir
    )

    $extractDir = Join-Path $Script:TEMP_DIR "extract_$ModReference"

    try {
        # Clean up previous extraction
        if (Test-Path $extractDir) {
            Remove-Item -Path $extractDir -Recurse -Force
        }
        New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

        # Extract the smod (it's a zip file)
        Expand-Archive -Path $SmodPath -DestinationPath $extractDir -Force

        # Find the pak files
        $paksDir = Join-Path $extractDir "Content\Paks\Windows"
        if (-not (Test-Path $paksDir)) {
            $paksDir = Join-Path $extractDir "Content\Paks"
        }
        if (-not (Test-Path $paksDir)) {
            # Try to find any pak files
            $pakFiles = Get-ChildItem -Path $extractDir -Filter "*.pak" -Recurse
            if ($pakFiles.Count -eq 0) {
                Write-Warning "No pak files found in $ModReference"
                return $false
            }
            $paksDir = $pakFiles[0].DirectoryName
        }

        # Create mod destination directory
        $modDestDir = Join-Path $ModsDir $ModReference
        if (-not (Test-Path $modDestDir)) {
            New-Item -ItemType Directory -Path $modDestDir -Force | Out-Null
        }

        # Copy pak files
        $filesCopied = 0
        $extensions = @("*.pak", "*.ucas", "*.utoc")

        foreach ($ext in $extensions) {
            $files = Get-ChildItem -Path $paksDir -Filter $ext -ErrorAction SilentlyContinue
            foreach ($file in $files) {
                Copy-Item -Path $file.FullName -Destination $modDestDir -Force
                $filesCopied++
            }
        }

        # Copy uplugin file if exists
        $upluginFiles = Get-ChildItem -Path $extractDir -Filter "*.uplugin" -ErrorAction SilentlyContinue
        if ($upluginFiles.Count -gt 0) {
            Copy-Item -Path $upluginFiles[0].FullName -Destination $modDestDir -Force
            $filesCopied++
        }

        # Cleanup
        Remove-Item -Path $extractDir -Recurse -Force -ErrorAction SilentlyContinue

        if ($filesCopied -gt 0) {
            Write-Success "Installed $filesCopied files for $ModReference"
            return $true
        }
        else {
            Write-Warning "No files extracted for $ModReference"
            return $false
        }
    }
    catch {
        Write-ErrorMsg "Extraction failed for $ModReference`: $_"
        return $false
    }
}

function Install-Mod {
    param(
        [PSCustomObject]$ModInfo,
        [string]$ModsDir
    )

    $modReference = $ModInfo.mod_reference
    $modName = $ModInfo.name

    Write-Info "Processing: $modName ($modReference)"

    # Get mod details from API
    $apiInfo = Get-ModInfo -ModReference $modReference
    if (-not $apiInfo) {
        Write-ErrorMsg "Could not find mod: $modReference"
        return $false
    }

    $versions = $apiInfo.versions
    if (-not $versions -or $versions.Count -eq 0) {
        Write-ErrorMsg "No versions available for: $modReference"
        return $false
    }

    $version = $versions[0]
    $versionNum = $version.version

    # Find Windows target
    $targets = $version.targets
    $windowsTarget = $targets | Where-Object { $_.targetName -eq $Script:TARGET_PLATFORM } | Select-Object -First 1

    if (-not $windowsTarget) {
        Write-Warning "No Windows version for: $modReference (may be server-only)"
        return $false
    }

    $downloadLink = $windowsTarget.link
    if (-not $downloadLink.StartsWith("http")) {
        $downloadLink = "$Script:API_URL$downloadLink"
    }

    # Create temp directory
    if (-not (Test-Path $Script:TEMP_DIR)) {
        New-Item -ItemType Directory -Path $Script:TEMP_DIR -Force | Out-Null
    }

    # Download the smod file
    $smodPath = Join-Path $Script:TEMP_DIR "$modReference-$versionNum.smod"

    Write-Info "Downloading v$versionNum..."

    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $downloadLink -OutFile $smodPath -TimeoutSec 120
        $ProgressPreference = 'Continue'
    }
    catch {
        Write-ErrorMsg "Download failed for $modReference`: $_"
        return $false
    }

    # Verify it's a valid zip file
    try {
        $null = [System.IO.Compression.ZipFile]::OpenRead($smodPath)
    }
    catch {
        Write-ErrorMsg "Downloaded file is not a valid archive: $modReference"
        Remove-Item -Path $smodPath -Force -ErrorAction SilentlyContinue
        return $false
    }

    # Extract and install
    $result = Install-ModFromSmod -SmodPath $smodPath -ModReference $modReference -ModsDir $ModsDir

    # Cleanup smod file
    Remove-Item -Path $smodPath -Force -ErrorAction SilentlyContinue

    if ($result) {
        Write-Success "Installed: $modName v$versionNum"
    }

    return $result
}

# =============================================================================
# Main Script
# =============================================================================

function Main {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Satisfactory Client Mod Installer" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # Determine game path
    $gamePath = $null
    $platform = "Unknown"

    if ($GamePath) {
        Write-Info "Using provided game path: $GamePath"
        if (Validate-GamePath -Path $GamePath) {
            $gamePath = $GamePath
            $platform = "Manual"
        }
        else {
            Write-ErrorMsg "Invalid game path: $GamePath"
            Write-ErrorMsg "The path should contain FactoryGame folder with game files."
            exit 1
        }
    }
    else {
        $detection = Find-SatisfactoryPath
        if ($detection) {
            $gamePath = $detection.Path
            $platform = $detection.Platform
        }
    }

    if (-not $gamePath) {
        Write-ErrorMsg "Could not find Satisfactory installation!"
        Write-Host ""
        Write-Host "Please specify the path manually:" -ForegroundColor Yellow
        Write-Host "  .\install-client-mods.ps1 -GamePath `"C:\Path\To\Satisfactory`"" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Common installation locations:" -ForegroundColor Yellow
        Write-Host "  Steam: C:\Program Files (x86)\Steam\steamapps\common\Satisfactory" -ForegroundColor Gray
        Write-Host "  Epic:  C:\Program Files\Epic Games\Satisfactory" -ForegroundColor Gray
        exit 1
    }

    Write-Success "Found Satisfactory ($platform)"
    Write-Host "  Path: $gamePath" -ForegroundColor Gray

    # Determine mods directory
    $modsDir = Join-Path $gamePath "FactoryGame\Mods"
    Write-Info "Mods directory: $modsDir"

    # Create mods directory if needed
    if (-not (Test-Path $modsDir)) {
        Write-Info "Creating Mods directory..."
        New-Item -ItemType Directory -Path $modsDir -Force | Out-Null
    }

    # Backup existing mods
    if (-not $SkipBackup) {
        $backupResult = New-ModsBackup -ModsDir $modsDir
        if (-not $backupResult) {
            Write-Warning "Backup failed, continuing anyway..."
        }
    }

    # Load mods list
    Write-Header "Loading Mod Configuration"

    try {
        $modsConfig = $Script:MODS_LIST | ConvertFrom-Json
        $mods = $modsConfig.mods
    }
    catch {
        Write-ErrorMsg "Failed to parse mods configuration: $_"
        exit 1
    }

    # Filter by category if specified
    if ($CategoryFilter) {
        $mods = $mods | Where-Object { $_.category -eq $CategoryFilter }
        Write-Info "Installing $CategoryFilter mods only"
    }

    # Sort by priority
    $mods = $mods | Sort-Object -Property priority

    Write-Info "Found $($mods.Count) mods to install"
    Write-Host ""

    # Install each mod
    $successCount = 0
    $failCount = 0
    $skipCount = 0

    foreach ($mod in $mods) {
        $result = Install-Mod -ModInfo $mod -ModsDir $modsDir

        if ($result -eq $true) {
            $successCount++
        }
        elseif ($result -eq $false) {
            # Check if it's a skip (no Windows version) or actual failure
            $apiInfo = Get-ModInfo -ModReference $mod.mod_reference
            if ($apiInfo) {
                $hasWindows = $apiInfo.versions[0].targets | Where-Object { $_.targetName -eq "Windows" }
                if (-not $hasWindows) {
                    $skipCount++
                }
                else {
                    $failCount++
                }
            }
            else {
                $failCount++
            }
        }

        Write-Host ""
    }

    # Summary
    Write-Header "Installation Complete"

    Write-Host "  Successful: $successCount" -ForegroundColor Green
    if ($skipCount -gt 0) {
        Write-Host "  Skipped (no Windows version): $skipCount" -ForegroundColor Yellow
    }
    if ($failCount -gt 0) {
        Write-Host "  Failed: $failCount" -ForegroundColor Red
    }

    # List installed mods
    $installedMods = Get-ChildItem -Path $modsDir -Directory -ErrorAction SilentlyContinue
    if ($installedMods.Count -gt 0) {
        Write-Host ""
        Write-Host "Installed mods:" -ForegroundColor Cyan
        foreach ($mod in $installedMods | Sort-Object Name) {
            Write-Host "  - $($mod.Name)" -ForegroundColor Gray
        }
    }

    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Launch Satisfactory" -ForegroundColor Gray
    Write-Host "  2. Connect to the server" -ForegroundColor Gray
    Write-Host "  3. Enjoy playing with mods!" -ForegroundColor Gray
    Write-Host ""

    # Cleanup temp directory
    if (Test-Path $Script:TEMP_DIR) {
        Remove-Item -Path $Script:TEMP_DIR -Recurse -Force -ErrorAction SilentlyContinue
    }

    if ($failCount -gt 0) {
        exit 1
    }
    exit 0
}

# Add .NET assembly for zip handling
Add-Type -AssemblyName System.IO.Compression.FileSystem

# Run main
Main
