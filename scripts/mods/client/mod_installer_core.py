"""
Satisfactory Mod Installer - Core Logic
Handles game path detection, API communication, and mod downloads.
"""

import json
import logging
import os
import platform
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
FICSIT_API_URL = "https://api.ficsit.app/v2/query"
REQUEST_TIMEOUT = 60
DOWNLOAD_TIMEOUT = 300


@dataclass
class Mod:
    """Represents a mod from the configuration."""
    name: str
    mod_reference: str
    category: str
    required: bool
    priority: int
    description: str

    # Populated after API query
    version: Optional[str] = None
    download_url: Optional[str] = None
    has_windows_target: bool = True


@dataclass
class InstallResult:
    """Result of a mod installation attempt."""
    mod_reference: str
    success: bool
    message: str
    version: Optional[str] = None
    files_installed: int = 0


class GamePathDetector:
    """Detects Satisfactory installation paths on Windows."""

    STEAM_REGISTRY_PATHS = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 526870",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 526870",
    ]

    COMMON_STEAM_PATHS = [
        r"C:\Program Files (x86)\Steam\steamapps\common\Satisfactory",
        r"C:\Program Files\Steam\steamapps\common\Satisfactory",
        r"C:\Steam\steamapps\common\Satisfactory",
        r"D:\Steam\steamapps\common\Satisfactory",
        r"D:\SteamLibrary\steamapps\common\Satisfactory",
        r"E:\Steam\steamapps\common\Satisfactory",
        r"E:\SteamLibrary\steamapps\common\Satisfactory",
        r"F:\Steam\steamapps\common\Satisfactory",
        r"F:\SteamLibrary\steamapps\common\Satisfactory",
    ]

    COMMON_EPIC_PATHS = [
        r"C:\Program Files\Epic Games\Satisfactory",
        r"C:\Program Files\Epic Games\SatisfactoryExperimental",
        r"D:\Epic Games\Satisfactory",
        r"D:\Games\Satisfactory",
        r"E:\Epic Games\Satisfactory",
        r"F:\Epic Games\Satisfactory",
    ]

    @classmethod
    def detect(cls) -> Optional[str]:
        """Detect Satisfactory installation path."""
        if platform.system() != "Windows":
            logger.warning("Game path detection only supported on Windows")
            return None

        # Try registry first
        path = cls._check_registry()
        if path:
            return path

        # Try common Steam paths
        for steam_path in cls.COMMON_STEAM_PATHS:
            if cls._is_valid_game_path(steam_path):
                return steam_path

        # Try common Epic paths
        for epic_path in cls.COMMON_EPIC_PATHS:
            if cls._is_valid_game_path(epic_path):
                return epic_path

        # Try Steam library folders
        path = cls._check_steam_libraries()
        if path:
            return path

        return None

    @classmethod
    def _check_registry(cls) -> Optional[str]:
        """Check Windows registry for Steam installation."""
        try:
            import winreg
            for reg_path in cls.STEAM_REGISTRY_PATHS:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    value, _ = winreg.QueryValueEx(key, "InstallLocation")
                    winreg.CloseKey(key)
                    if cls._is_valid_game_path(value):
                        return value
                except WindowsError:
                    continue
        except ImportError:
            pass
        return None

    @classmethod
    def _check_steam_libraries(cls) -> Optional[str]:
        """Parse Steam library folders to find game."""
        steam_paths = [
            r"C:\Program Files (x86)\Steam",
            r"D:\Steam",
            r"E:\Steam",
        ]

        for steam_path in steam_paths:
            vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
            if os.path.exists(vdf_path):
                try:
                    with open(vdf_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Simple VDF parsing for "path" values
                    import re
                    paths = re.findall(r'"path"\s+"([^"]+)"', content)
                    for library_path in paths:
                        library_path = library_path.replace("\\\\", "\\")
                        game_path = os.path.join(library_path, "steamapps", "common", "Satisfactory")
                        if cls._is_valid_game_path(game_path):
                            return game_path
                except Exception as e:
                    logger.debug(f"Error parsing VDF: {e}")

        return None

    @classmethod
    def _is_valid_game_path(cls, path: str) -> bool:
        """Check if path contains valid Satisfactory installation."""
        if not path or not os.path.exists(path):
            return False
        factory_game = os.path.join(path, "FactoryGame")
        return os.path.isdir(factory_game)


class FicsitAPIClient:
    """Client for ficsit.app GraphQL API."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "SatisfactoryModInstaller/1.0"
        })

    def get_mod_info(self, mod_reference: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get latest version info for a mod.

        Returns:
            Tuple of (version, download_url) or (None, None) if not found
        """
        query = """
        query GetMod($modReference: ModReference!) {
            getModByReference(modReference: $modReference) {
                name
                versions(filter: {limit: 1, order_by: created_at, order: desc}) {
                    version
                    targets {
                        targetName
                        link
                    }
                }
            }
        }
        """

        variables = {"modReference": mod_reference}

        try:
            response = self.session.post(
                FICSIT_API_URL,
                json={"query": query, "variables": variables},
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            mod_data = data.get("data", {}).get("getModByReference")
            if not mod_data:
                return None, None

            versions = mod_data.get("versions", [])
            if not versions:
                return None, None

            version_info = versions[0]
            version = version_info.get("version")

            # Find Windows target
            targets = version_info.get("targets", [])
            for target in targets:
                if target.get("targetName") == "Windows":
                    link = target.get("link", "")
                    if not link.startswith("http"):
                        link = f"https://api.ficsit.app{link}"
                    return version, link

            # No Windows target found
            return version, None

        except requests.RequestException as e:
            logger.error(f"API request failed for {mod_reference}: {e}")
            return None, None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse API response for {mod_reference}: {e}")
            return None, None

    def test_connection(self) -> bool:
        """Test if API is reachable."""
        try:
            response = self.session.get(
                "https://api.ficsit.app",
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False


class ModDownloader:
    """Downloads and extracts mods from ficsit.app."""

    def __init__(self, mods_dir: str):
        self.mods_dir = Path(mods_dir)
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SatisfactoryModInstaller/1.0"
        })

    def download_and_install(
        self,
        mod_reference: str,
        download_url: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> InstallResult:
        """
        Download and install a mod.

        Args:
            mod_reference: The mod's reference ID
            download_url: URL to download .smod file
            progress_callback: Optional callback(downloaded_bytes, total_bytes)

        Returns:
            InstallResult with success status and details
        """
        temp_dir = None
        try:
            # Create temp directory for download
            temp_dir = tempfile.mkdtemp(prefix="satisfactory_mod_")
            smod_path = os.path.join(temp_dir, f"{mod_reference}.smod")

            # Download the .smod file
            logger.info(f"Downloading {mod_reference}...")
            response = self.session.get(
                download_url,
                stream=True,
                timeout=DOWNLOAD_TIMEOUT
            )
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(smod_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)

            # Verify download
            if not os.path.exists(smod_path) or os.path.getsize(smod_path) < 1000:
                return InstallResult(
                    mod_reference=mod_reference,
                    success=False,
                    message="Download failed or file too small"
                )

            # Extract and install
            logger.info(f"Extracting {mod_reference}...")
            files_installed = self._extract_and_install(smod_path, mod_reference)

            if files_installed > 0:
                return InstallResult(
                    mod_reference=mod_reference,
                    success=True,
                    message=f"Installed successfully ({files_installed} files)",
                    files_installed=files_installed
                )
            else:
                return InstallResult(
                    mod_reference=mod_reference,
                    success=False,
                    message="No files extracted from archive"
                )

        except requests.RequestException as e:
            return InstallResult(
                mod_reference=mod_reference,
                success=False,
                message=f"Download error: {str(e)}"
            )
        except zipfile.BadZipFile:
            return InstallResult(
                mod_reference=mod_reference,
                success=False,
                message="Invalid archive format"
            )
        except Exception as e:
            return InstallResult(
                mod_reference=mod_reference,
                success=False,
                message=f"Installation error: {str(e)}"
            )
        finally:
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_and_install(self, smod_path: str, mod_reference: str) -> int:
        """
        Extract .smod archive and install to mods directory.
        Preserves full directory structure (Binaries, Config, Content, etc.)

        Returns:
            Number of files installed
        """
        extract_dir = tempfile.mkdtemp(prefix="extract_")

        try:
            # Extract archive
            with zipfile.ZipFile(smod_path, 'r') as zf:
                zf.extractall(extract_dir)

            # Determine source directory
            # smod may contain a folder named after the mod, or content directly
            source_dir = extract_dir
            mod_subfolder = os.path.join(extract_dir, mod_reference)

            if os.path.isdir(mod_subfolder):
                # smod contains a folder named after the mod
                source_dir = mod_subfolder
            else:
                # Check for .uplugin to confirm we have the right level
                uplugins = list(Path(extract_dir).glob("*.uplugin"))
                if not uplugins:
                    # Look one level deeper
                    subdirs = [d for d in Path(extract_dir).iterdir() if d.is_dir()]
                    if len(subdirs) == 1:
                        source_dir = str(subdirs[0])

            # Remove existing mod directory
            dest_dir = self.mods_dir / mod_reference
            if dest_dir.exists():
                shutil.rmtree(dest_dir)

            # Copy entire directory structure
            shutil.copytree(source_dir, dest_dir)

            # Count installed files
            files_count = sum(1 for _ in dest_dir.rglob("*") if _.is_file())

            return files_count

        finally:
            # Cleanup extraction directory
            shutil.rmtree(extract_dir, ignore_errors=True)

    def verify_installation(self, mod_reference: str) -> Dict[str, any]:
        """
        Verify a mod installation.

        Returns:
            Dict with verification results
        """
        mod_dir = self.mods_dir / mod_reference

        if not mod_dir.exists():
            return {
                "installed": False,
                "valid": False,
                "message": "Mod folder not found"
            }

        has_uplugin = any(mod_dir.glob("*.uplugin"))
        pak_files = list(mod_dir.rglob("*.pak"))
        dll_files = list(mod_dir.rglob("*.dll"))

        return {
            "installed": True,
            "valid": has_uplugin,
            "has_uplugin": has_uplugin,
            "pak_count": len(pak_files),
            "dll_count": len(dll_files),
            "message": "Valid" if has_uplugin else "Missing .uplugin file"
        }


class ModManager:
    """High-level mod management."""

    def __init__(self, game_path: str, config_path: Optional[str] = None):
        self.game_path = Path(game_path)
        self.mods_dir = self.game_path / "FactoryGame" / "Mods"
        self.mods_dir.mkdir(parents=True, exist_ok=True)

        self.api_client = FicsitAPIClient()
        self.downloader = ModDownloader(str(self.mods_dir))

        # Load mod configuration
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to mods-list.json in the same directory as this script
            self.config_path = Path(__file__).parent.parent / "config" / "mods-list.json"

        self.mods: List[Mod] = []
        self._load_config()

    def _load_config(self):
        """Load mod list from configuration file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for mod_data in data.get("mods", []):
                mod = Mod(
                    name=mod_data["name"],
                    mod_reference=mod_data["mod_reference"],
                    category=mod_data.get("category", "other"),
                    required=mod_data.get("required", False),
                    priority=mod_data.get("priority", 99),
                    description=mod_data.get("description", "")
                )
                self.mods.append(mod)

            # Sort by priority
            self.mods.sort(key=lambda m: m.priority)

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load config: {e}")

    def get_mods_by_category(self) -> Dict[str, List[Mod]]:
        """Get mods organized by category."""
        categories: Dict[str, List[Mod]] = {}
        for mod in self.mods:
            if mod.category not in categories:
                categories[mod.category] = []
            categories[mod.category].append(mod)
        return categories

    def fetch_mod_info(self, mod: Mod) -> bool:
        """
        Fetch latest version info for a mod from API.

        Returns:
            True if mod has Windows version available
        """
        version, download_url = self.api_client.get_mod_info(mod.mod_reference)
        mod.version = version
        mod.download_url = download_url
        mod.has_windows_target = download_url is not None
        return mod.has_windows_target

    def install_mod(
        self,
        mod: Mod,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> InstallResult:
        """Install a single mod."""
        if not mod.download_url:
            # Try to fetch info first
            if not self.fetch_mod_info(mod):
                return InstallResult(
                    mod_reference=mod.mod_reference,
                    success=False,
                    message="No Windows version available"
                )

        result = self.downloader.download_and_install(
            mod.mod_reference,
            mod.download_url,
            progress_callback
        )
        result.version = mod.version
        return result

    def verify_all(self) -> Dict[str, Dict]:
        """Verify all mod installations."""
        results = {}
        for mod in self.mods:
            results[mod.mod_reference] = self.downloader.verify_installation(mod.mod_reference)
        return results

    def backup_mods(self, backup_dir: Optional[str] = None) -> Optional[str]:
        """
        Create a backup of current mods.

        Returns:
            Path to backup directory, or None if no mods to backup
        """
        if not any(self.mods_dir.iterdir()):
            return None

        if not backup_dir:
            backup_dir = Path.home() / "SatisfactoryModBackups"
        else:
            backup_dir = Path(backup_dir)

        backup_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"mods_backup_{timestamp}"

        shutil.copytree(self.mods_dir, backup_path)
        return str(backup_path)


def get_embedded_mods_config() -> List[Dict]:
    """
    Return embedded mod configuration for standalone executable.
    This is used when mods-list.json is not available.
    """
    return [
        {"name": "Satisfactory Mod Loader", "mod_reference": "SML", "category": "dependency", "required": True, "priority": 0, "description": "Required for ALL mods"},
        {"name": "Pak Utility Mod", "mod_reference": "UtilityMod", "category": "dependency", "required": True, "priority": 1, "description": "Required dependency for most mods"},
        {"name": "Smart!", "mod_reference": "SmartFoundations", "category": "quality-of-life", "required": False, "priority": 2, "description": "Mass building of foundations, walls, and more"},
        {"name": "Micro Manage", "mod_reference": "MicroManage", "category": "quality-of-life", "required": False, "priority": 2, "description": "Precise object positioning, rotation, and scaling"},
        {"name": "Efficiency Checker", "mod_reference": "EfficiencyCheckerMod", "category": "quality-of-life", "required": False, "priority": 2, "description": "Monitor production efficiency"},
        {"name": "Infinite Zoop", "mod_reference": "InfiniteZoop", "category": "quality-of-life", "required": False, "priority": 2, "description": "Unlimited zoop range"},
        {"name": "Infinite Nudge", "mod_reference": "InfiniteNudge", "category": "quality-of-life", "required": False, "priority": 2, "description": "Unlimited nudge range"},
        {"name": "Structural Solutions", "mod_reference": "SS_Mod", "category": "quality-of-life", "required": False, "priority": 2, "description": "More building options"},
        {"name": "Load Balancers", "mod_reference": "LoadBalancers", "category": "quality-of-life", "required": False, "priority": 2, "description": "Better load balancing"},
        {"name": "MAM Enhancer", "mod_reference": "MAMTips", "category": "quality-of-life", "required": False, "priority": 2, "description": "Enhanced MAM interface"},
        {"name": "MiniMap", "mod_reference": "MiniMap", "category": "quality-of-life", "required": False, "priority": 2, "description": "In-game minimap"},
        {"name": "Refined Power", "mod_reference": "RefinedPower", "category": "content", "required": False, "priority": 3, "description": "New power generation options"},
        {"name": "Ficsit Farming", "mod_reference": "FicsitFarming", "category": "content", "required": False, "priority": 3, "description": "Farming mechanics"},
        {"name": "Teleporter", "mod_reference": "Teleporter", "category": "content", "required": False, "priority": 3, "description": "Instant travel"},
        {"name": "Linear Motion", "mod_reference": "LinearMotion", "category": "content", "required": False, "priority": 3, "description": "Moving platforms and elevators"},
        {"name": "Mk++", "mod_reference": "MK22k20", "category": "content", "required": False, "priority": 3, "description": "Higher tier machines"},
        {"name": "Fluid Extras", "mod_reference": "AB_FluidExtras", "category": "content", "required": False, "priority": 3, "description": "Additional fluid handling"},
        {"name": "Storage Teleporter", "mod_reference": "StorageTeleporter", "category": "content", "required": False, "priority": 3, "description": "Teleport items between storage"},
        {"name": "Big Storage Tank", "mod_reference": "BigStorageTank", "category": "content", "required": False, "priority": 3, "description": "Large fluid storage"},
        {"name": "Container Screens", "mod_reference": "ContainerScreen", "category": "content", "required": False, "priority": 3, "description": "Display screens for containers"},
        {"name": "Item Dispenser", "mod_reference": "Dispenser", "category": "content", "required": False, "priority": 3, "description": "Automatic item dispensing"},
        {"name": "EasyCheat", "mod_reference": "EasyCheat", "category": "cheat", "required": False, "priority": 4, "description": "Cheat menu"},
        {"name": "PowerSuit", "mod_reference": "PowerSuit", "category": "cheat", "required": False, "priority": 4, "description": "Enhanced player abilities"},
        {"name": "Extra Inventory", "mod_reference": "Additional_300_Inventory_Slots", "category": "cheat", "required": False, "priority": 4, "description": "300 extra inventory slots"},
    ]


if __name__ == "__main__":
    # Test the core functionality
    print("Detecting game path...")
    path = GamePathDetector.detect()
    if path:
        print(f"Found: {path}")
    else:
        print("Not found")

    print("\nTesting API connection...")
    client = FicsitAPIClient()
    if client.test_connection():
        print("API connection OK")
        version, url = client.get_mod_info("SML")
        print(f"SML latest version: {version}")
    else:
        print("API connection failed")
