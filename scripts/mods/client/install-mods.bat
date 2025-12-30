@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: Satisfactory Client Mod Installer v3.0
:: Downloads and installs mods from ficsit.app for Windows game clients
:: Fixed: Preserves full mod directory structure for proper installation
:: =============================================================================

title Satisfactory Mod Installer
color 0B

echo.
echo ========================================
echo   Satisfactory Client Mod Installer
echo   Version 3.0 - Full Structure Fix
echo ========================================
echo.

:: =============================================================================
:: Parse Command Line Arguments
:: =============================================================================

set "SKIP_NETWORK_TEST=0"
set "FORCE_POWERSHELL=0"
set "VERBOSE=0"
set "VERIFY_ONLY=0"

:parse_args
if "%~1"=="" goto :done_args
if /i "%~1"=="--skip-network-test" set "SKIP_NETWORK_TEST=1"
if /i "%~1"=="--force-powershell" set "FORCE_POWERSHELL=1"
if /i "%~1"=="--verbose" set "VERBOSE=1"
if /i "%~1"=="-v" set "VERBOSE=1"
if /i "%~1"=="--verify" set "VERIFY_ONLY=1"
if /i "%~1"=="--help" goto :show_help
if /i "%~1"=="-h" goto :show_help
shift
goto :parse_args
:done_args

:: Handle verify-only mode
if "!VERIFY_ONLY!"=="1" goto :verify_only_mode

:: =============================================================================
:: Configuration
:: =============================================================================

set "MAX_RETRIES=3"
set "RETRY_DELAY=5"
set "DOWNLOAD_TIMEOUT=180"
set "API_TIMEOUT=60"

:: =============================================================================
:: Check Dependencies
:: =============================================================================

echo [INFO] Checking system requirements...
echo.

:: Check Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo [INFO] Windows Version: %VERSION%

:: Check for curl
set "HAS_CURL=0"
where curl >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] curl found
    set "HAS_CURL=1"
) else (
    echo [WARN] curl not found, will use PowerShell for downloads
)

:: Check for tar
set "USE_TAR=0"
where tar >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] tar found
    set "USE_TAR=1"
) else (
    echo [INFO] tar not found, will use PowerShell for extraction
)

:: Check for PowerShell
where powershell >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] PowerShell not found - this is required
    goto :error
)
echo [OK] PowerShell found

:: Determine download method
if "!FORCE_POWERSHELL!"=="1" (
    echo [INFO] Forcing PowerShell for downloads (--force-powershell)
    set "USE_CURL=0"
) else if "!HAS_CURL!"=="1" (
    set "USE_CURL=1"
) else (
    set "USE_CURL=0"
)
echo.

:: =============================================================================
:: Test Network Connectivity (Optional)
:: =============================================================================

if "!SKIP_NETWORK_TEST!"=="1" (
    echo [INFO] Skipping network test (--skip-network-test)
    echo.
    goto :skip_network
)

echo [INFO] Testing network connectivity...
echo [INFO] (Use --skip-network-test to bypass this check)
echo.

:: Method 1: Try PowerShell (most reliable across firewalls)
echo [....] Testing with PowerShell...
set "NET_OK=0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { $null = Invoke-WebRequest -Uri 'https://api.ficsit.app' -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop; Write-Output 'OK' } catch { Write-Output 'FAIL' }" > "%TEMP%\nettest.txt" 2>nul
set /p NET_RESULT=<"%TEMP%\nettest.txt"
del "%TEMP%\nettest.txt" >nul 2>&1

if "!NET_RESULT!"=="OK" (
    echo [OK] Network connection verified via PowerShell
    set "NET_OK=1"
    goto :network_ok
)

:: Method 2: Try curl if available
if "!HAS_CURL!"=="1" (
    echo [....] Testing with curl...
    curl -s --max-time 15 --tlsv1.2 -o nul "https://api.ficsit.app" >nul 2>&1
    if !errorLevel! equ 0 (
        echo [OK] Network connection verified via curl
        set "NET_OK=1"
        goto :network_ok
    )
)

:: Method 3: Try ping (very basic, may be blocked)
echo [....] Testing with ping...
ping -n 1 -w 5000 api.ficsit.app >nul 2>&1
if !errorLevel! equ 0 (
    echo [OK] Network connection verified via ping
    set "NET_OK=1"
    goto :network_ok
)

:: Method 4: Test DNS resolution
echo [....] Testing DNS resolution...
nslookup api.ficsit.app >nul 2>&1
if !errorLevel! equ 0 (
    echo [OK] DNS resolution working - proceeding anyway
    set "NET_OK=1"
    goto :network_ok
)

:: All tests failed
echo.
echo [WARN] ================================================
echo [WARN] Network connectivity tests failed!
echo [WARN] ================================================
echo.
echo This could mean:
echo   1. No internet connection
echo   2. Firewall/antivirus blocking the connection
echo   3. Corporate network restrictions
echo   4. VPN issues
echo.
echo Do you want to continue anyway? The download might still work.
echo.
set /p "CONTINUE=Continue anyway? (Y/N): "
if /i "!CONTINUE!"=="Y" goto :network_ok
if /i "!CONTINUE!"=="YES" goto :network_ok
echo.
echo [INFO] To skip this test next time, run with: --skip-network-test
goto :error

:network_ok
echo.

:skip_network

:: =============================================================================
:: Find Satisfactory Installation
:: =============================================================================

echo [INFO] Searching for Satisfactory installation...
echo.

set "GAME_PATH="

:: Method 1: Check Steam registry (32-bit view)
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 526870" /v InstallLocation 2^>nul') do set "GAME_PATH=%%b"
if defined GAME_PATH if exist "!GAME_PATH!\FactoryGame" (
    echo [OK] Found via Steam registry: !GAME_PATH!
    goto :found_game
)

:: Method 1b: Check Steam registry (64-bit view)
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 526870" /v InstallLocation 2^>nul') do set "GAME_PATH=%%b"
if defined GAME_PATH if exist "!GAME_PATH!\FactoryGame" (
    echo [OK] Found via Steam registry (64-bit): !GAME_PATH!
    goto :found_game
)

:: Method 2: Check common Steam paths
echo [INFO] Checking common Steam paths...
for %%d in (C D E F G H) do (
    for %%p in (
        "%%d:\Program Files (x86)\Steam\steamapps\common\Satisfactory"
        "%%d:\Program Files\Steam\steamapps\common\Satisfactory"
        "%%d:\Steam\steamapps\common\Satisfactory"
        "%%d:\SteamLibrary\steamapps\common\Satisfactory"
        "%%d:\Games\Steam\steamapps\common\Satisfactory"
        "%%d:\Games\SteamLibrary\steamapps\common\Satisfactory"
    ) do (
        if exist "%%~p\FactoryGame" (
            set "GAME_PATH=%%~p"
            echo [OK] Found at: !GAME_PATH!
            goto :found_game
        )
    )
)

:: Method 3: Check Epic Games paths
echo [INFO] Checking Epic Games paths...
for %%d in (C D E F G H) do (
    for %%p in (
        "%%d:\Program Files\Epic Games\Satisfactory"
        "%%d:\Program Files\Epic Games\SatisfactoryExperimental"
        "%%d:\Epic Games\Satisfactory"
        "%%d:\Games\Satisfactory"
        "%%d:\Games\Epic Games\Satisfactory"
    ) do (
        if exist "%%~p\FactoryGame" (
            set "GAME_PATH=%%~p"
            echo [OK] Found at: !GAME_PATH!
            goto :found_game
        )
    )
)

:: Method 4: Try to parse Steam library folders
echo [INFO] Parsing Steam library configuration...
for %%s in ("C:\Program Files (x86)\Steam" "D:\Steam" "E:\Steam") do (
    if exist "%%~s\steamapps\libraryfolders.vdf" (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$content = Get-Content '%%~s\steamapps\libraryfolders.vdf' -Raw -ErrorAction SilentlyContinue; if ($content) { $matches = [regex]::Matches($content, '\"path\"\s+\"([^\"]+)\"'); foreach ($m in $matches) { $p = $m.Groups[1].Value -replace '\\\\', '\'; $sf = Join-Path $p 'steamapps\common\Satisfactory'; if (Test-Path (Join-Path $sf 'FactoryGame')) { Write-Output $sf; break } } }" > "%TEMP%\sf_path.txt" 2>nul
        set /p GAME_PATH=<"%TEMP%\sf_path.txt"
        del "%TEMP%\sf_path.txt" >nul 2>&1
        if defined GAME_PATH if exist "!GAME_PATH!\FactoryGame" (
            echo [OK] Found in Steam library: !GAME_PATH!
            goto :found_game
        )
    )
)

:: Not found - ask user
echo.
echo [WARN] Could not find Satisfactory installation automatically.
echo.
echo Common installation paths:
echo   Steam: C:\Program Files (x86)\Steam\steamapps\common\Satisfactory
echo   Epic:  C:\Program Files\Epic Games\Satisfactory
echo.
echo Please enter the full path to your Satisfactory folder
echo (the folder that contains "FactoryGame"):
echo.
set /p "GAME_PATH=Path: "

if not defined GAME_PATH (
    echo [ERROR] No path entered.
    goto :error
)

:: Remove quotes if present
set "GAME_PATH=!GAME_PATH:"=!"

if not exist "!GAME_PATH!\FactoryGame" (
    echo [ERROR] Invalid path. FactoryGame folder not found at: !GAME_PATH!
    goto :error
)

:found_game
echo.
echo [OK] Game path: !GAME_PATH!
echo.

:: =============================================================================
:: Setup Directories
:: =============================================================================

set "MODS_DIR=!GAME_PATH!\FactoryGame\Mods"
set "TEMP_DIR=%TEMP%\SatisfactoryModInstaller_%RANDOM%"
set "BACKUP_DIR=%USERPROFILE%\SatisfactoryModBackups"
set "LOG_FILE=%TEMP%\satisfactory_mod_install.log"

:: Create directories
if not exist "!MODS_DIR!" mkdir "!MODS_DIR!"
if not exist "!TEMP_DIR!" mkdir "!TEMP_DIR!"
if not exist "!BACKUP_DIR!" mkdir "!BACKUP_DIR!"

echo [INFO] Mods directory: !MODS_DIR!
if "!VERBOSE!"=="1" (
    echo [INFO] Temp directory: !TEMP_DIR!
    echo [INFO] Log file: !LOG_FILE!
)
echo.

:: Initialize log
echo Satisfactory Mod Installer Log > "!LOG_FILE!"
echo Started: %date% %time% >> "!LOG_FILE!"
echo Game Path: !GAME_PATH! >> "!LOG_FILE!"
echo Download Method: !USE_CURL! (1=curl, 0=PowerShell) >> "!LOG_FILE!"
echo. >> "!LOG_FILE!"

:: =============================================================================
:: Backup Existing Mods
:: =============================================================================

set "HAS_MODS=0"
for /d %%d in ("!MODS_DIR!\*") do set "HAS_MODS=1"

if "!HAS_MODS!"=="1" (
    echo [INFO] Creating backup of existing mods...
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "DATESTAMP=%%c%%a%%b"
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "TIMESTAMP=%%a%%b"
    set "BACKUP_PATH=!BACKUP_DIR!\mods-backup-!DATESTAMP!-!TIMESTAMP!"
    xcopy "!MODS_DIR!" "!BACKUP_PATH!\" /E /I /Q >nul 2>&1
    if !errorLevel! equ 0 (
        echo [OK] Backup created: !BACKUP_PATH!
    ) else (
        echo [WARN] Backup failed, continuing anyway...
    )
    echo.
)

:: =============================================================================
:: Define Mods to Install
:: =============================================================================

set "MOD_COUNT=31"
:: Dependencies (must be installed first)
set "MOD[0]=SML"
set "MOD[1]=UtilityMod"
set "MOD[2]=ModUpdateNotifier"
set "MOD[3]=MarcioCommonLibs"
set "MOD[4]=MinoDabsCommonLib"
set "MOD[5]=ModularUI"
set "MOD[6]=RefinedRDApi"
set "MOD[7]=RefinedRDLib"
set "MOD[8]=avMallLib"
:: Quality of Life mods
set "MOD[9]=SmartFoundations"
set "MOD[10]=MicroManage"
set "MOD[11]=EfficiencyCheckerMod"
set "MOD[12]=InfiniteZoop"
set "MOD[13]=InfiniteNudge"
set "MOD[14]=SS_Mod"
set "MOD[15]=LoadBalancers"
set "MOD[16]=MAMTips"
set "MOD[17]=MiniMap"
:: Content mods
set "MOD[18]=RefinedPower"
set "MOD[19]=FicsitFarming"
set "MOD[20]=Teleporter"
set "MOD[21]=LinearMotion"
set "MOD[22]=MK22k20"
set "MOD[23]=AB_FluidExtras"
set "MOD[24]=StorageTeleporter"
set "MOD[25]=BigStorageTank"
set "MOD[26]=ContainerScreen"
set "MOD[27]=Dispenser"
:: Cheat mods
set "MOD[28]=EasyCheat"
set "MOD[29]=PowerSuit"
set "MOD[30]=Additional_300_Inventory_Slots"

set "NAME[0]=Satisfactory Mod Loader"
set "NAME[1]=Pak Utility Mod"
set "NAME[2]=Mod Update Notifier"
set "NAME[3]=Marcio Common Libs"
set "NAME[4]=MinoDabs Common Lib"
set "NAME[5]=Modular UI"
set "NAME[6]=Refined R&D API"
set "NAME[7]=Refined R&D Lib"
set "NAME[8]=avMall Lib"
set "NAME[9]=Smart!"
set "NAME[10]=Micro Manage"
set "NAME[11]=Efficiency Checker"
set "NAME[12]=Infinite Zoop"
set "NAME[13]=Infinite Nudge"
set "NAME[14]=Structural Solutions"
set "NAME[15]=Load Balancers"
set "NAME[16]=MAM Enhancer"
set "NAME[17]=MiniMap"
set "NAME[18]=Refined Power"
set "NAME[19]=Ficsit Farming"
set "NAME[20]=Teleporter"
set "NAME[21]=Linear Motion"
set "NAME[22]=Mk++"
set "NAME[23]=Fluid Extras"
set "NAME[24]=Storage Teleporter"
set "NAME[25]=Big Storage Tank"
set "NAME[26]=Container Screens"
set "NAME[27]=Item Dispenser"
set "NAME[28]=EasyCheat"
set "NAME[29]=PowerSuit"
set "NAME[30]=Additional 300 Inventory Slots"

:: =============================================================================
:: Download and Install Mods
:: =============================================================================

echo ========================================
echo   Installing Mods (0/%MOD_COUNT%)
echo ========================================
echo.

set "SUCCESS_COUNT=0"
set "FAIL_COUNT=0"
set "SKIP_COUNT=0"

set /a "LAST_MOD=MOD_COUNT-1"
for /L %%i in (0,1,%LAST_MOD%) do (
    set /a "CURRENT=%%i+1"
    echo ----------------------------------------
    echo [!CURRENT!/%MOD_COUNT%] !NAME[%%i]! ^(!MOD[%%i]!^)
    echo ----------------------------------------
    call :install_mod_with_retry "!MOD[%%i]!" "!NAME[%%i]!"
)

echo.
echo ========================================
echo   Installation Complete
echo ========================================
echo.
echo   Successful: !SUCCESS_COUNT!
echo   Skipped:    !SKIP_COUNT! (no Windows version)
echo   Failed:     !FAIL_COUNT!
echo.

:: List installed mods with verification
echo Installed mod folders:
for /d %%d in ("!MODS_DIR!\*") do (
    set "MOD_FOLDER=%%d"
    set "HAS_UPLUGIN="
    set "HAS_PAK="
    set "HAS_DLL="
    if exist "%%d\*.uplugin" set "HAS_UPLUGIN=Y"
    dir /s /b "%%d\*.pak" >nul 2>&1 && set "HAS_PAK=Y"
    dir /s /b "%%d\*.dll" >nul 2>&1 && set "HAS_DLL=Y"
    if defined HAS_UPLUGIN (
        if defined HAS_PAK (
            if defined HAS_DLL (
                echo   [OK] %%~nxd (uplugin + pak + dll)
            ) else (
                echo   [OK] %%~nxd (uplugin + pak)
            )
        ) else (
            echo   [??] %%~nxd (uplugin only - may be incomplete)
        )
    ) else (
        echo   [!!] %%~nxd (missing uplugin - INVALID)
    )
)

:: Verify SML is installed (required for all mods)
echo.
if exist "!MODS_DIR!\SML\SML.uplugin" (
    echo [OK] SML (Satisfactory Mod Loader) is installed correctly
) else (
    echo [ERROR] SML is NOT installed correctly!
    echo         Without SML, NO mods will work.
    echo         Please try reinstalling or use Satisfactory Mod Manager.
)

echo.
echo ========================================
echo   Next Steps
echo ========================================
echo.
echo   1. Launch Satisfactory from Steam/Epic
echo   2. Look for "MODS" button in main menu (confirms SML loaded)
echo   3. Connect to the modded server
echo.
echo   If you DON'T see a "MODS" button in the main menu:
echo   - Mods are NOT loading properly
echo   - Try running: install-mods.bat --verify
echo   - Or use Satisfactory Mod Manager (SMM) instead
echo.

if !FAIL_COUNT! gtr 0 (
    echo [WARN] Some mods failed to install.
    echo.
    echo Troubleshooting:
    echo   1. Run as Administrator (right-click, Run as administrator)
    echo   2. Try: install-mods.bat --skip-network-test
    echo   3. Try: install-mods.bat --force-powershell
    echo   4. Temporarily disable antivirus
    echo   5. Check log: !LOG_FILE!
    echo.
)

:: Cleanup
rd /s /q "!TEMP_DIR!" >nul 2>&1

goto :success

:: =============================================================================
:: Function: Show Help
:: =============================================================================

:show_help
echo.
echo Satisfactory Client Mod Installer v3.0
echo.
echo Usage: install-mods.bat [options]
echo.
echo Options:
echo   --skip-network-test   Skip the network connectivity test
echo   --force-powershell    Use PowerShell instead of curl for downloads
echo   --verbose, -v         Show detailed output
echo   --verify              Only verify existing installation (no download)
echo   --help, -h            Show this help
echo.
echo Examples:
echo   install-mods.bat                           Install all mods
echo   install-mods.bat --skip-network-test       Skip network check
echo   install-mods.bat --verify                  Check current installation
echo.
exit /b 0

:: =============================================================================
:: Verify Only Mode
:: =============================================================================

:verify_only_mode
echo.
echo ========================================
echo   Verification Mode
echo ========================================
echo.
echo [INFO] Searching for Satisfactory installation...

set "GAME_PATH="

:: Quick game path detection
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 526870" /v InstallLocation 2^>nul') do set "GAME_PATH=%%b"
if not defined GAME_PATH (
    for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 526870" /v InstallLocation 2^>nul') do set "GAME_PATH=%%b"
)

:: Check common paths
if not defined GAME_PATH (
    for %%d in (C D E F G) do (
        for %%p in (
            "%%d:\Program Files (x86)\Steam\steamapps\common\Satisfactory"
            "%%d:\Program Files\Steam\steamapps\common\Satisfactory"
            "%%d:\Steam\steamapps\common\Satisfactory"
            "%%d:\SteamLibrary\steamapps\common\Satisfactory"
            "%%d:\Program Files\Epic Games\Satisfactory"
        ) do (
            if exist "%%~p\FactoryGame" (
                set "GAME_PATH=%%~p"
                goto :verify_found
            )
        )
    )
)

if not defined GAME_PATH (
    echo [ERROR] Could not find Satisfactory installation.
    echo         Please run without --verify to enter path manually.
    goto :error
)

:verify_found
echo [OK] Game found: !GAME_PATH!
echo.

set "MODS_DIR=!GAME_PATH!\FactoryGame\Mods"

if not exist "!MODS_DIR!" (
    echo [ERROR] Mods folder not found: !MODS_DIR!
    echo         No mods are installed.
    goto :error
)

echo ========================================
echo   Installed Mods Verification
echo ========================================
echo.
echo Mods directory: !MODS_DIR!
echo.

set "TOTAL_MODS=0"
set "VALID_MODS=0"
set "INVALID_MODS=0"

for /d %%d in ("!MODS_DIR!\*") do (
    set /a "TOTAL_MODS+=1"
    set "MOD_NAME=%%~nxd"
    set "HAS_UPLUGIN="
    set "HAS_PAK="
    set "HAS_DLL="
    set "PAK_COUNT=0"
    set "DLL_COUNT=0"

    if exist "%%d\*.uplugin" set "HAS_UPLUGIN=Y"

    for /f %%c in ('dir /s /b "%%d\*.pak" 2^>nul ^| find /c /v ""') do set "PAK_COUNT=%%c"
    for /f %%c in ('dir /s /b "%%d\*.dll" 2^>nul ^| find /c /v ""') do set "DLL_COUNT=%%c"

    if !PAK_COUNT! gtr 0 set "HAS_PAK=Y"
    if !DLL_COUNT! gtr 0 set "HAS_DLL=Y"

    if defined HAS_UPLUGIN (
        set /a "VALID_MODS+=1"
        if defined HAS_PAK (
            if defined HAS_DLL (
                echo [OK] !MOD_NAME!
                echo     - uplugin: YES
                echo     - pak files: !PAK_COUNT!
                echo     - dll files: !DLL_COUNT!
            ) else (
                echo [OK] !MOD_NAME!
                echo     - uplugin: YES
                echo     - pak files: !PAK_COUNT!
                echo     - dll files: 0 (blueprint-only mod)
            )
        ) else (
            echo [??] !MOD_NAME!
            echo     - uplugin: YES
            echo     - pak files: 0 (might be config-only)
            echo     - dll files: !DLL_COUNT!
        )
    ) else (
        set /a "INVALID_MODS+=1"
        echo [!!] !MOD_NAME!
        echo     - uplugin: MISSING (INVALID INSTALLATION)
        echo     - pak files: !PAK_COUNT!
        echo     - dll files: !DLL_COUNT!
    )
    echo.
)

echo ========================================
echo   Summary
echo ========================================
echo.
echo Total mod folders: !TOTAL_MODS!
echo Valid mods:        !VALID_MODS!
echo Invalid mods:      !INVALID_MODS!
echo.

if exist "!MODS_DIR!\SML\SML.uplugin" (
    echo [OK] SML (Satisfactory Mod Loader) is installed
) else (
    echo [ERROR] SML is NOT installed!
    echo         Without SML, the game will NOT load ANY mods.
    echo         Run this script without --verify to install mods.
)

echo.
if !INVALID_MODS! gtr 0 (
    echo [WARN] Some mods are invalid. Run without --verify to reinstall.
)

echo Press any key to exit...
pause >nul
exit /b 0

:: =============================================================================
:: Function: Install mod with retry
:: =============================================================================

:install_mod_with_retry
set "M_REF=%~1"
set "M_NAME=%~2"
set "INSTALL_SUCCESS=0"

for /L %%r in (1,1,%MAX_RETRIES%) do (
    if !INSTALL_SUCCESS! equ 0 (
        if %%r gtr 1 (
            echo [RETRY] Attempt %%r of %MAX_RETRIES%...
            timeout /t %RETRY_DELAY% /nobreak >nul
        )
        call :install_mod "!M_REF!" "!M_NAME!"
        if !errorLevel! equ 0 set "INSTALL_SUCCESS=1"
        if !errorLevel! equ 2 set "INSTALL_SUCCESS=2"
    )
)

if !INSTALL_SUCCESS! equ 0 (
    echo [FAIL] Could not install !M_NAME! after %MAX_RETRIES% attempts
    echo [FAIL] !M_REF!: Failed after %MAX_RETRIES% attempts >> "!LOG_FILE!"
    set /a "FAIL_COUNT+=1"
)
echo.
goto :eof

:: =============================================================================
:: Function: Install a single mod (using PowerShell for everything)
:: =============================================================================

:install_mod
set "MOD_REF=%~1"
set "MOD_NAME=%~2"

echo [....] Querying API for !MOD_REF!...
echo [API] Querying !MOD_REF! >> "!LOG_FILE!"

:: Create comprehensive PowerShell script for API + Download
set "PS_SCRIPT=!TEMP_DIR!\install_!MOD_REF!.ps1"

(
echo $ErrorActionPreference = 'Stop'
echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
echo.
echo $modRef = '!MOD_REF!'
echo $tempDir = '!TEMP_DIR!'
echo $modsDir = '!MODS_DIR!'
echo.
echo function Write-Log($msg^) { Write-Host $msg }
echo.
echo try {
echo     # Query API
echo     $query = @{ query = "query { getModByReference(modReference: `"$modRef`"^) { name versions(filter: {limit: 1, order_by: created_at, order: desc}^) { version targets { targetName link } } } }" } ^| ConvertTo-Json -Compress
echo.
echo     $response = Invoke-RestMethod -Uri 'https://api.ficsit.app/v2/query' -Method Post -Body $query -ContentType 'application/json' -TimeoutSec 60
echo.
echo     if (-not $response.data.getModByReference.versions -or $response.data.getModByReference.versions.Count -eq 0^) {
echo         Write-Output "RESULT:NOT_FOUND"
echo         exit 0
echo     }
echo.
echo     $version = $response.data.getModByReference.versions[0]
echo     $target = $version.targets ^| Where-Object { $_.targetName -eq 'Windows' } ^| Select-Object -First 1
echo.
echo     if (-not $target^) {
echo         Write-Output "RESULT:NO_WINDOWS"
echo         exit 0
echo     }
echo.
echo     $link = $target.link
echo     if (-not $link.StartsWith('http'^)^) { $link = 'https://api.ficsit.app' + $link }
echo.
echo     Write-Log "[....] Downloading v$($version.version^)..."
echo.
echo     # Download
echo     $smodFile = Join-Path $tempDir "$modRef.smod"
echo     Invoke-WebRequest -Uri $link -OutFile $smodFile -UseBasicParsing -TimeoutSec 180
echo.
echo     if (-not (Test-Path $smodFile^) -or (Get-Item $smodFile^).Length -lt 1000^) {
echo         Write-Output "RESULT:DOWNLOAD_FAILED"
echo         exit 0
echo     }
echo.
echo     Write-Log "[....] Extracting..."
echo.
echo     # Extract to temp folder
echo     $extractDir = Join-Path $tempDir "extract_$modRef"
echo     if (Test-Path $extractDir^) { Remove-Item $extractDir -Recurse -Force }
echo     Expand-Archive -Path $smodFile -DestinationPath $extractDir -Force
echo.
echo     # Remove existing mod folder to ensure clean install
echo     $modDestDir = Join-Path $modsDir $modRef
echo     if (Test-Path $modDestDir^) { Remove-Item $modDestDir -Recurse -Force }
echo.
echo     # Determine the source - smod may have mod folder inside or be the content directly
echo     $sourceDir = $extractDir
echo     $modSubFolder = Join-Path $extractDir $modRef
echo     if (Test-Path $modSubFolder^) {
echo         # smod contains a folder named after the mod
echo         $sourceDir = $modSubFolder
echo     } else {
echo         # smod extracts content directly, check for uplugin to confirm
echo         $uplugins = Get-ChildItem -Path $extractDir -Filter "*.uplugin" -ErrorAction SilentlyContinue
echo         if ($uplugins.Count -eq 0^) {
echo             # Look one level deeper
echo             $subFolders = Get-ChildItem -Path $extractDir -Directory -ErrorAction SilentlyContinue
echo             if ($subFolders.Count -eq 1^) {
echo                 $sourceDir = $subFolders[0].FullName
echo             }
echo         }
echo     }
echo.
echo     # Copy ENTIRE directory structure preserving all folders
echo     Write-Log "[....] Installing to Mods folder..."
echo     Copy-Item -Path $sourceDir -Destination $modDestDir -Recurse -Force
echo.
echo     # Count installed files for verification
echo     $filesCopied = 0
echo     $hasUplugin = Test-Path (Join-Path $modDestDir "*.uplugin"^)
echo     $hasPak = (Get-ChildItem -Path $modDestDir -Filter "*.pak" -Recurse -ErrorAction SilentlyContinue^).Count
echo     $hasDll = (Get-ChildItem -Path $modDestDir -Filter "*.dll" -Recurse -ErrorAction SilentlyContinue^).Count
echo     $filesCopied = (Get-ChildItem -Path $modDestDir -Recurse -File -ErrorAction SilentlyContinue^).Count
echo.
echo     # Verify critical files exist
echo     $validation = @()
echo     if ($hasUplugin^) { $validation += 'uplugin' }
echo     if ($hasPak -gt 0^) { $validation += "$hasPak pak" }
echo     if ($hasDll -gt 0^) { $validation += "$hasDll dll" }
echo     $validationStr = $validation -join ', '
echo.
echo     # Cleanup temp files
echo     Remove-Item $smodFile -Force -ErrorAction SilentlyContinue
echo     Remove-Item $extractDir -Recurse -Force -ErrorAction SilentlyContinue
echo.
echo     if ($filesCopied -gt 0 -and $hasUplugin^) {
echo         Write-Output "RESULT:OK:$($version.version^):$filesCopied files ($validationStr^)"
echo     } elseif ($filesCopied -gt 0^) {
echo         Write-Output "RESULT:OK:$($version.version^):$filesCopied files (no uplugin warning^)"
echo     } else {
echo         Write-Output "RESULT:NO_FILES"
echo     }
echo.
echo } catch {
echo     Write-Output "RESULT:ERROR:$($_.Exception.Message^)"
echo }
) > "!PS_SCRIPT!"

:: Execute PowerShell script
set "PS_OUTPUT="
for /f "tokens=*" %%a in ('powershell -NoProfile -ExecutionPolicy Bypass -File "!PS_SCRIPT!" 2^>^&1') do (
    set "LINE=%%a"
    if "!LINE:~0,7!"=="RESULT:" (
        set "PS_OUTPUT=!LINE!"
    ) else (
        echo %%a
    )
)

del "!PS_SCRIPT!" >nul 2>&1

:: Parse result - format is RESULT:TYPE:VERSION:INFO
for /f "tokens=1,2,3,* delims=:" %%a in ("!PS_OUTPUT!") do (
    set "RESULT_TYPE=%%b"
    set "RESULT_VER=%%c"
    set "RESULT_FILES=%%d"
)

if "!RESULT_TYPE!"=="NOT_FOUND" (
    echo [WARN] Mod not found in repository
    echo [SKIP] !MOD_REF!: Not found >> "!LOG_FILE!"
    set /a "SKIP_COUNT+=1"
    exit /b 2
)

if "!RESULT_TYPE!"=="NO_WINDOWS" (
    echo [SKIP] No Windows version (server-only mod)
    echo [SKIP] !MOD_REF!: No Windows version >> "!LOG_FILE!"
    set /a "SKIP_COUNT+=1"
    exit /b 2
)

if "!RESULT_TYPE!"=="DOWNLOAD_FAILED" (
    echo [WARN] Download failed
    echo [ERROR] !MOD_REF!: Download failed >> "!LOG_FILE!"
    exit /b 1
)

if "!RESULT_TYPE!"=="NO_FILES" (
    echo [WARN] No files extracted
    echo [ERROR] !MOD_REF!: No files >> "!LOG_FILE!"
    exit /b 1
)

if "!RESULT_TYPE!"=="ERROR" (
    echo [WARN] Error: !RESULT_VER!
    echo [ERROR] !MOD_REF!: !RESULT_VER! >> "!LOG_FILE!"
    exit /b 1
)

if "!RESULT_TYPE!"=="OK" (
    echo [ OK ] Installed v!RESULT_VER! (!RESULT_FILES! files)
    echo [SUCCESS] !MOD_REF! v!RESULT_VER! >> "!LOG_FILE!"
    set /a "SUCCESS_COUNT+=1"
    exit /b 0
)

:: Unknown result
echo [WARN] Unknown result: !PS_OUTPUT!
echo [ERROR] !MOD_REF!: Unknown result >> "!LOG_FILE!"
exit /b 1

:: =============================================================================
:: Exit Handlers
:: =============================================================================

:success
echo.
echo Log file: !LOG_FILE!
echo.
echo Press any key to exit...
pause >nul
exit /b 0

:error
echo.
echo [ERROR] Installation failed!
echo.
echo Try these options:
echo   install-mods.bat --skip-network-test
echo   install-mods.bat --force-powershell
echo.
echo Or use Satisfactory Mod Manager (SMM) instead:
echo   https://github.com/satisfactorymodding/SatisfactoryModManager/releases
echo.
echo Press any key to exit...
pause >nul
exit /b 1
