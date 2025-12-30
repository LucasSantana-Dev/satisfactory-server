#!/usr/bin/env python3
"""
Satisfactory Mod Installer
Downloads and installs mods from ficsit.app for Linux dedicated servers.
"""

import json
import os
import sys
import zipfile
import shutil
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, List, Any

# Configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_DIR = SCRIPT_DIR / "config"
MODS_LIST_FILE = CONFIG_DIR / "mods-list.json"
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODS_DIR = DATA_DIR / "gamefiles" / "FactoryGame" / "Mods"
TEMP_DIR = DATA_DIR / "temp_downloads"

API_URL = "https://api.ficsit.app"
GRAPHQL_ENDPOINT = f"{API_URL}/v2/query"

# Colors for terminal output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def print_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def print_success(msg: str):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")

def print_warn(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")

def graphql_query(query: str) -> Optional[Dict]:
    """Execute a GraphQL query against the ficsit.app API."""
    data = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "errors" in result and result["errors"]:
                print_error(f"GraphQL error: {result['errors']}")
                return None
            return result.get("data")
    except urllib.error.URLError as e:
        print_error(f"API request failed: {e}")
        return None

def get_mod_info(mod_reference: str) -> Optional[Dict]:
    """Get mod information including latest version and download links."""
    query = f'''
    query {{
        getModByReference(modReference: "{mod_reference}") {{
            id
            name
            mod_reference
            versions(filter: {{limit: 1, order_by: created_at, order: desc}}) {{
                id
                version
                targets {{
                    targetName
                    link
                }}
            }}
        }}
    }}
    '''
    data = graphql_query(query)
    if data and data.get("getModByReference"):
        return data["getModByReference"]
    return None

def download_file(url: str, dest: Path) -> bool:
    """Download a file from URL to destination."""
    try:
        # Follow redirects
        req = urllib.request.Request(url, headers={"User-Agent": "SatisfactoryModInstaller/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(dest, "wb") as f:
                shutil.copyfileobj(response, f)
        return True
    except Exception as e:
        print_error(f"Download failed: {e}")
        return False

def get_file_hash(filepath: Path) -> str:
    """Calculate MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()

def extract_smod(smod_path: Path, mod_reference: str) -> bool:
    """Extract .smod file and install mod files with FULL directory structure."""
    try:
        # Create a temporary extraction directory
        extract_dir = TEMP_DIR / f"extract_{mod_reference}"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True)

        # Extract the smod (zip) file
        with zipfile.ZipFile(smod_path, 'r') as zf:
            zf.extractall(extract_dir)

        # Remove old mod directory if exists
        mod_dest = MODS_DIR / mod_reference
        if mod_dest.exists():
            shutil.rmtree(mod_dest)

        # Copy ENTIRE mod structure, not just pak files
        # First, copy the root level files (.uplugin, .smm, etc.)
        files_copied = 0
        for item in extract_dir.iterdir():
            dest_path = mod_dest / item.name
            if item.is_file():
                mod_dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
                files_copied += 1
            elif item.is_dir():
                # Copy directories (Content, Binaries, Config, Resources, etc.)
                if item.name in ["Content", "Binaries", "Config", "Resources"]:
                    shutil.copytree(item, dest_path)
                    files_copied += sum(1 for _ in dest_path.rglob("*") if _.is_file())

        # Also copy pak files from Content/Paks/LinuxServer/ to mod root
        paks_dir = extract_dir / "Content" / "Paks" / "LinuxServer"
        if paks_dir.exists():
            mod_dest.mkdir(parents=True, exist_ok=True)
            for ext in ["*.pak", "*.ucas", "*.utoc"]:
                for file in paks_dir.glob(ext):
                    dest_file = mod_dest / file.name
                    if not dest_file.exists():  # Don't overwrite if already copied
                        shutil.copy2(file, dest_file)
                        files_copied += 1

        # Cleanup
        shutil.rmtree(extract_dir)

        if files_copied > 0:
            print_success(f"Installed {files_copied} files for {mod_reference}")
            return True
        else:
            print_error(f"No files extracted for {mod_reference}")
            return False

    except Exception as e:
        print_error(f"Extraction failed for {mod_reference}: {e}")
        return False

def install_mod(mod_info: Dict) -> bool:
    """Download and install a single mod."""
    mod_reference = mod_info["mod_reference"]
    name = mod_info["name"]

    print_info(f"Processing: {name} ({mod_reference})")

    # Get mod details from API
    api_info = get_mod_info(mod_reference)
    if not api_info:
        print_error(f"Could not find mod: {mod_reference}")
        return False

    versions = api_info.get("versions", [])
    if not versions:
        print_error(f"No versions available for: {mod_reference}")
        return False

    version = versions[0]
    version_id = version["id"]
    version_num = version["version"]

    # Find Linux server download link
    targets = version.get("targets", [])
    linux_target = next((t for t in targets if t["targetName"] == "LinuxServer"), None)

    if not linux_target:
        print_warn(f"No Linux server version for: {mod_reference}")
        return False

    download_link = linux_target["link"]
    if not download_link.startswith("http"):
        download_link = f"{API_URL}{download_link}"

    # Create temp directory
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Download the smod file
    smod_path = TEMP_DIR / f"{mod_reference}-{version_num}.smod"

    print_info(f"Downloading v{version_num}...")
    if not download_file(download_link, smod_path):
        return False

    # Verify it's a valid zip file
    if not zipfile.is_zipfile(smod_path):
        print_error(f"Downloaded file is not a valid archive: {mod_reference}")
        smod_path.unlink()
        return False

    # Extract and install
    if not extract_smod(smod_path, mod_reference):
        return False

    # Cleanup smod file
    smod_path.unlink()

    print_success(f"Installed: {name} v{version_num}")
    return True

def cleanup_old_mods():
    """Remove old/incorrect mod files."""
    if not MODS_DIR.exists():
        return

    print_info("Cleaning up old mod files...")

    # Remove any .pak files directly in Mods directory (old format)
    for pak_file in MODS_DIR.glob("*.pak"):
        file_size = pak_file.stat().st_size
        # The incorrect files were all 95MB (99456192 bytes)
        if file_size == 99456192:
            print_warn(f"Removing incorrect file: {pak_file.name}")
            pak_file.unlink()
        else:
            # Check if it's a valid pak (should have "FPakEntry" or similar markers)
            # For safety, just warn about unknown files
            print_warn(f"Unknown .pak file in root: {pak_file.name} ({file_size} bytes)")

def load_mods_list() -> List[Dict]:
    """Load the mods configuration."""
    if not MODS_LIST_FILE.exists():
        print_error(f"Mods list not found: {MODS_LIST_FILE}")
        sys.exit(1)

    with open(MODS_LIST_FILE, "r") as f:
        data = json.load(f)

    return data.get("mods", [])

def main():
    """Main entry point."""
    print(f"\n{Colors.BOLD}=== Satisfactory Mod Installer ==={Colors.RESET}\n")

    # Parse arguments
    category_filter = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--qol", "--qol-only"]:
            category_filter = "quality-of-life"
        elif arg in ["--content", "--content-only"]:
            category_filter = "content"
        elif arg in ["--cheat", "--cheat-only"]:
            category_filter = "cheat"
        elif arg in ["--help", "-h"]:
            print("Usage: install.py [OPTIONS]")
            print("Options:")
            print("  --qol-only      Install only Quality of Life mods")
            print("  --content-only  Install only Content mods")
            print("  --cheat-only    Install only Cheat mods")
            print("  (no option)     Install all mods")
            sys.exit(0)

    # Create necessary directories
    MODS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Cleanup old files
    cleanup_old_mods()

    # Load mods list
    mods = load_mods_list()

    # Filter by category if specified
    if category_filter:
        mods = [m for m in mods if m.get("category") == category_filter]
        print_info(f"Installing {category_filter} mods only")

    # Sort by priority
    mods.sort(key=lambda x: x.get("priority", 99))

    print_info(f"Found {len(mods)} mods to install\n")

    # Install each mod
    success_count = 0
    fail_count = 0

    for mod in mods:
        if install_mod(mod):
            success_count += 1
        else:
            fail_count += 1
        print()  # Empty line between mods

    # Summary
    print(f"\n{Colors.BOLD}=== Installation Complete ==={Colors.RESET}")
    print(f"  {Colors.GREEN}Successful:{Colors.RESET} {success_count}")
    if fail_count > 0:
        print(f"  {Colors.RED}Failed:{Colors.RESET} {fail_count}")

    # List installed mods
    if MODS_DIR.exists():
        installed = [d.name for d in MODS_DIR.iterdir() if d.is_dir()]
        if installed:
            print(f"\n{Colors.BOLD}Installed mods:{Colors.RESET}")
            for mod_name in sorted(installed):
                print(f"  - {mod_name}")

    print(f"\n{Colors.YELLOW}Remember to restart the server:{Colors.RESET}")
    print("  docker compose restart satisfactory\n")

    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
