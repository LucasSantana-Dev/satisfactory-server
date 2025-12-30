"""
Satisfactory Mod Installer - Core Logic
Handles game path detection, API communication, and mod downloads.
Integrates with ficsit-cli for reliable mod installation.
"""

import json
import logging
import os
import platform
import shutil
import subprocess
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
FICSIT_CLI_RELEASES_URL = "https://api.github.com/repos/satisfactorymodding/ficsit-cli/releases/latest"
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


class FicsitCLI:
    """
    Wrapper for the official ficsit-cli tool.
    Downloads and uses ficsit-cli for reliable mod installation.
    """

    PROFILE_NAME = "SatisfactoryServerMods"

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize FicsitCLI wrapper.

        Args:
            cache_dir: Directory to cache ficsit-cli executable
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Default to user's AppData/Local on Windows
            if platform.system() == "Windows":
                self.cache_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SatisfactoryModInstaller"
            else:
                self.cache_dir = Path.home() / ".satisfactory-mod-installer"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cli_path: Optional[Path] = None
        self._find_or_download_cli()

    def _find_or_download_cli(self) -> bool:
        """Find existing ficsit-cli or download it."""
        # Check if already cached
        if platform.system() == "Windows":
            cli_name = "ficsit.exe"
        else:
            cli_name = "ficsit"

        cached_cli = self.cache_dir / cli_name
        if cached_cli.exists():
            self.cli_path = cached_cli
            logger.info(f"Found cached ficsit-cli at {cached_cli}")
            return True

        # Need to download
        return self._download_cli()

    def _download_cli(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """
        Download ficsit-cli from GitHub releases.

        Returns:
            True if download successful
        """
        logger.info("Downloading ficsit-cli from GitHub...")

        try:
            # Get latest release info
            response = requests.get(FICSIT_CLI_RELEASES_URL, timeout=30)
            response.raise_for_status()
            release_data = response.json()

            # Find the appropriate asset for this platform
            system = platform.system().lower()
            machine = platform.machine().lower()

            # Map architecture names
            if machine in ("x86_64", "amd64"):
                arch = "amd64"
            elif machine in ("i386", "i686", "x86"):
                arch = "386"
            elif machine in ("arm64", "aarch64"):
                arch = "arm64"
            else:
                arch = "amd64"  # Default

            # Build expected asset name
            if system == "windows":
                asset_name = f"ficsit_windows_{arch}.exe"
                cli_name = "ficsit.exe"
            elif system == "darwin":
                asset_name = "ficsit_darwin_all"
                cli_name = "ficsit"
            else:
                asset_name = f"ficsit_linux_{arch}"
                cli_name = "ficsit"

            # Find asset URL
            download_url = None
            for asset in release_data.get("assets", []):
                if asset["name"] == asset_name:
                    download_url = asset["browser_download_url"]
                    break

            if not download_url:
                logger.error(f"Could not find ficsit-cli asset: {asset_name}")
                return False

            # Download the executable
            logger.info(f"Downloading {asset_name}...")
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            cli_path = self.cache_dir / cli_name
            with open(cli_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)

            # Make executable on Unix
            if system != "windows":
                os.chmod(cli_path, 0o755)

            self.cli_path = cli_path
            logger.info(f"ficsit-cli downloaded to {cli_path}")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to download ficsit-cli: {e}")
            return False
        except Exception as e:
            logger.error(f"Error downloading ficsit-cli: {e}")
            return False

    def is_available(self) -> bool:
        """Check if ficsit-cli is available."""
        return self.cli_path is not None and self.cli_path.exists()

    def _run_command(self, args: List[str], capture_output: bool = True) -> Tuple[bool, str]:
        """
        Run a ficsit-cli command.

        Returns:
            Tuple of (success, output/error message)
        """
        if not self.is_available():
            return False, "ficsit-cli not available"

        cmd = [str(self.cli_path)] + args
        cmd_str = ' '.join(cmd)
        logger.debug(f"Running ficsit-cli: {cmd_str}")

        try:
            if platform.system() == "Windows":
                # Hide console window on Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(
                    cmd,
                    capture_output=capture_output,
                    text=True,
                    timeout=300,
                    startupinfo=startupinfo
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=capture_output,
                    text=True,
                    timeout=300
                )

            if result.returncode == 0:
                if capture_output and result.stdout:
                    logger.debug(f"ficsit-cli stdout: {result.stdout.strip()}")
                return True, result.stdout if capture_output else ""
            else:
                # Capture both stderr and stdout for better error messages
                error_parts = []
                if capture_output:
                    if result.stderr:
                        error_parts.append(result.stderr.strip())
                    if result.stdout:
                        error_parts.append(result.stdout.strip())
                error_msg = " | ".join(error_parts) if error_parts else f"Exit code: {result.returncode}"
                logger.warning(f"ficsit-cli command failed: {cmd_str}")
                logger.warning(f"ficsit-cli error: {error_msg}")
                return False, error_msg

        except subprocess.TimeoutExpired:
            logger.error(f"ficsit-cli command timed out: {cmd_str}")
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"ficsit-cli exception: {e}")
            return False, str(e)

    def add_installation(self, game_path: str) -> Tuple[bool, str]:
        """Add a game installation to ficsit-cli."""
        success, output = self._run_command(["installation", "add", game_path])
        if success:
            return True, f"Added installation: {game_path}"
        # ficsit-cli may return "already exists" or "already present"
        elif "already exists" in output.lower() or "already present" in output.lower():
            return True, f"Installation already registered: {game_path}"
        return False, output

    def create_profile(self, profile_name: Optional[str] = None) -> Tuple[bool, str]:
        """Create a mod profile."""
        name = profile_name or self.PROFILE_NAME
        # Note: ficsit-cli uses "new" not "create" for profile creation
        success, output = self._run_command(["profile", "new", name])
        if success:
            return True, f"Created profile: {name}"
        # ficsit-cli may return "already exists" or "already present"
        elif "already exists" in output.lower() or "already present" in output.lower():
            return True, f"Profile already exists: {name}"
        return False, output

    def add_mod_to_profile(self, mod_reference: str, profile_name: Optional[str] = None) -> Tuple[bool, str]:
        """Add a mod to a profile."""
        name = profile_name or self.PROFILE_NAME
        success, output = self._run_command(["profile", "mod", "add", name, mod_reference])
        if success:
            return True, f"Added {mod_reference} to profile"
        return False, output

    def set_installation_profile(self, game_path: str, profile_name: Optional[str] = None) -> Tuple[bool, str]:
        """Set the profile for an installation (links profile to game)."""
        name = profile_name or self.PROFILE_NAME
        success, output = self._run_command(["installation", "set-profile", game_path, name])
        if success:
            return True, f"Linked profile {name} to installation"
        return False, output

    def apply_installation(self, game_path: str) -> Tuple[bool, str]:
        """Apply profile and actually download/install mods."""
        success, output = self._run_command(["apply", game_path])
        if success:
            return True, "Mods downloaded and installed"
        return False, output

    def install_mods(
        self,
        game_path: str,
        mod_references: List[str],
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> Tuple[bool, List[str], Dict[str, str], str]:
        """
        Install mods using ficsit-cli.

        Args:
            game_path: Path to Satisfactory installation
            mod_references: List of mod references to install
            progress_callback: Optional callback(mod_ref, status_message)

        Returns:
            Tuple of (overall_success, successful_mods, failed_mods_with_errors, diagnostic_info)
            - failed_mods_with_errors: Dict mapping mod_ref to error message
            - diagnostic_info: String with step-by-step status
        """
        successful = []
        failed_with_errors: Dict[str, str] = {}
        diagnostics = []

        # Step 1: Add installation
        if progress_callback:
            progress_callback("", "Registering game installation...")

        success, msg = self.add_installation(game_path)
        if success:
            diagnostics.append(f"[OK] Registration: {msg}")
        else:
            diagnostics.append(f"[FAILED] Registration: {msg}")
            logger.error(f"Failed to add installation: {msg}")
            # Return all mods as failed with the same error
            for ref in mod_references:
                failed_with_errors[ref] = f"Installation registration failed: {msg}"
            return False, [], failed_with_errors, "\n".join(diagnostics)

        # Step 2: Create profile
        if progress_callback:
            progress_callback("", "Creating mod profile...")

        success, msg = self.create_profile()
        if success:
            diagnostics.append(f"[OK] Profile: {msg}")
            logger.info(f"Profile ready: {msg}")
        else:
            diagnostics.append(f"[FAILED] Profile: {msg}")
            logger.error(f"Failed to create profile: {msg}")
            # Return all mods as failed with the same error
            for ref in mod_references:
                failed_with_errors[ref] = f"Profile creation failed: {msg}"
            return False, [], failed_with_errors, "\n".join(diagnostics)

        # Step 3: Add each mod to the profile
        for mod_ref in mod_references:
            if progress_callback:
                progress_callback(mod_ref, f"Adding {mod_ref} to profile...")

            success, msg = self.add_mod_to_profile(mod_ref)
            if success:
                successful.append(mod_ref)
                logger.info(f"Added {mod_ref} to profile")
            else:
                failed_with_errors[mod_ref] = msg
                logger.warning(f"Failed to add {mod_ref}: {msg}")

        diagnostics.append(f"[INFO] Mods added: {len(successful)}/{len(mod_references)}")

        # Step 4: Link profile to installation
        if progress_callback:
            progress_callback("", "Linking profile to installation...")

        success, msg = self.set_installation_profile(game_path)
        if success:
            diagnostics.append(f"[OK] Profile linked: {msg}")
        else:
            diagnostics.append(f"[FAILED] Profile link: {msg}")
            logger.error(f"Failed to link profile: {msg}")
            return False, successful, failed_with_errors, "\n".join(diagnostics)

        # Step 5: Apply - actually download and install mods
        if progress_callback:
            progress_callback("", "Downloading and installing mods...")

        success, msg = self.apply_installation(game_path)
        if success:
            diagnostics.append(f"[OK] Installation: {msg}")
        else:
            diagnostics.append(f"[FAILED] Installation: {msg}")
            logger.error(f"Failed to install mods: {msg}")
            return False, successful, failed_with_errors, "\n".join(diagnostics)

        return len(failed_with_errors) == 0, successful, failed_with_errors, "\n".join(diagnostics)

    def get_version(self) -> Optional[str]:
        """Get ficsit-cli version."""
        success, output = self._run_command(["--version"])
        if success:
            return output.strip()
        return None


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

    def get_mod_with_dependencies(self, mod_reference: str) -> Tuple[Optional[str], Optional[str], List[str], Optional[str]]:
        """
        Get mod info including its dependencies and compatibility status.

        Returns:
            Tuple of (version, download_url, list of dependency mod_references, compatibility_warning)
            compatibility_warning is None if mod is compatible, otherwise a warning message
        """
        query = """
        query GetModWithDeps($modReference: ModReference!) {
            getModByReference(modReference: $modReference) {
                name
                mod_reference
                compatibility {
                    EA { state note }
                    EXP { state note }
                }
                versions(filter: {limit: 1, order_by: created_at, order: desc}) {
                    version
                    dependencies {
                        mod_reference
                        condition
                    }
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
                logger.warning(f"Mod not found on ficsit.app: {mod_reference}")
                return None, None, [], None

            versions = mod_data.get("versions", [])
            if not versions:
                logger.warning(f"No versions found for mod: {mod_reference}")
                return None, None, [], None

            version_info = versions[0]
            version = version_info.get("version")

            # Check compatibility status
            compatibility_warning = None
            compatibility = mod_data.get("compatibility", {})
            ea_status = compatibility.get("EA", {}).get("state", "")
            exp_status = compatibility.get("EXP", {}).get("state", "")

            if ea_status == "Broken" or exp_status == "Broken":
                note = compatibility.get("EA", {}).get("note") or compatibility.get("EXP", {}).get("note") or ""
                compatibility_warning = f"BROKEN - incompatible with current game version"
                if note:
                    compatibility_warning += f" ({note})"
                logger.warning(f"Mod {mod_reference} is marked as BROKEN on ficsit.app")

            # Extract dependencies (excluding SML as it's always required)
            dependencies = []
            for dep in version_info.get("dependencies", []):
                dep_ref = dep.get("mod_reference")
                if dep_ref and dep_ref != "SML":
                    dependencies.append(dep_ref)

            # Find Windows target
            download_url = None
            targets = version_info.get("targets", [])
            for target in targets:
                if target.get("targetName") == "Windows":
                    link = target.get("link", "")
                    if link and not link.startswith("http"):
                        link = f"https://api.ficsit.app{link}"
                    download_url = link
                    break

            return version, download_url, dependencies, compatibility_warning

        except requests.RequestException as e:
            logger.error(f"API request failed for {mod_reference}: {e}")
            return None, None, [], None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse API response for {mod_reference}: {e}")
            return None, None, [], None


@dataclass
class ModStatus:
    """Status of a mod installation."""
    mod_reference: str
    installed: bool
    valid: bool
    version: Optional[str] = None
    has_uplugin: bool = False
    pak_count: int = 0
    dll_count: int = 0
    so_count: int = 0
    message: str = ""


@dataclass
class ResolvedMod:
    """A mod with its resolved information from the API."""
    mod_reference: str
    name: str
    version: Optional[str]
    download_url: Optional[str]
    dependencies: List[str]
    has_windows_target: bool
    compatibility_warning: Optional[str] = None

    @property
    def is_broken(self) -> bool:
        """True if mod is marked as broken/incompatible."""
        return self.compatibility_warning is not None and "BROKEN" in self.compatibility_warning


class DependencyResolver:
    """
    Resolves complete dependency trees for mods by querying ficsit.app API.
    Handles transitive dependencies recursively.
    """

    def __init__(self, api_client: Optional[FicsitAPIClient] = None):
        self.api_client = api_client or FicsitAPIClient()
        self._cache: Dict[str, ResolvedMod] = {}
        self._resolution_errors: Dict[str, str] = {}

    def resolve_all(
        self,
        mod_references: List[str],
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> Tuple[List[ResolvedMod], Dict[str, str]]:
        """
        Recursively resolve all dependencies for the given mods.

        Args:
            mod_references: List of mod references to resolve
            progress_callback: Optional callback(mod_ref, status_message)

        Returns:
            Tuple of (list of all resolved mods including dependencies, dict of errors)
        """
        self._cache.clear()
        self._resolution_errors.clear()

        # Always include SML as it's required for all mods
        all_needed = set(["SML"])
        to_process = list(mod_references)

        while to_process:
            mod_ref = to_process.pop(0)

            if mod_ref in self._cache:
                continue

            if progress_callback:
                progress_callback(mod_ref, f"Resolving dependencies for {mod_ref}...")

            logger.info(f"Resolving: {mod_ref}")

            version, download_url, dependencies, compat_warning = self.api_client.get_mod_with_dependencies(mod_ref)

            if version is None:
                self._resolution_errors[mod_ref] = f"Mod not found on ficsit.app"
                logger.warning(f"Could not resolve {mod_ref}")
                continue

            resolved = ResolvedMod(
                mod_reference=mod_ref,
                name=mod_ref,
                version=version,
                download_url=download_url,
                dependencies=dependencies,
                has_windows_target=download_url is not None,
                compatibility_warning=compat_warning
            )

            # Warn about broken mods but still add them (user can decide)
            if resolved.is_broken:
                self._resolution_errors[mod_ref] = compat_warning
                logger.warning(f"Mod {mod_ref} is BROKEN: {compat_warning}")

            self._cache[mod_ref] = resolved
            all_needed.add(mod_ref)

            # Queue dependencies for resolution
            for dep in dependencies:
                if dep not in self._cache and dep not in to_process:
                    to_process.append(dep)
                    all_needed.add(dep)

        # Build ordered list (dependencies first)
        ordered = self._topological_sort(list(all_needed))

        return [self._cache[ref] for ref in ordered if ref in self._cache], self._resolution_errors

    def _topological_sort(self, mod_refs: List[str]) -> List[str]:
        """
        Sort mods so dependencies come before dependents.
        SML always comes first.
        """
        # Simple approach: dependencies first based on depth
        result = []
        visited = set()

        def visit(ref: str, depth: int = 0):
            if ref in visited or depth > 50:  # Prevent infinite loops
                return
            visited.add(ref)

            if ref in self._cache:
                for dep in self._cache[ref].dependencies:
                    visit(dep, depth + 1)

            if ref not in result:
                result.append(ref)

        # SML first
        if "SML" in mod_refs:
            visit("SML")

        # Then all others
        for ref in mod_refs:
            visit(ref)

        return result

    def get_all_required_refs(self) -> List[str]:
        """Get all resolved mod references."""
        return list(self._cache.keys())

    def get_resolution_errors(self) -> Dict[str, str]:
        """Get any errors encountered during resolution."""
        return self._resolution_errors.copy()


class ModScanner:
    """
    Scans the game's Mods directory to inventory installed mods
    and verify their file integrity.
    """

    def __init__(self, mods_dir: Path):
        self.mods_dir = Path(mods_dir)

    def scan_installed(self) -> Dict[str, ModStatus]:
        """
        Scan the mods directory and return status of each installed mod.

        Returns:
            Dict mapping mod_reference to ModStatus
        """
        results: Dict[str, ModStatus] = {}

        if not self.mods_dir.exists():
            logger.warning(f"Mods directory does not exist: {self.mods_dir}")
            return results

        for item in self.mods_dir.iterdir():
            if not item.is_dir():
                continue

            mod_ref = item.name
            status = self._check_mod_directory(item, mod_ref)
            results[mod_ref] = status

        return results

    def _check_mod_directory(self, mod_dir: Path, mod_ref: str) -> ModStatus:
        """Check a single mod directory for validity."""
        # Look for .uplugin file
        uplugin_files = list(mod_dir.glob("*.uplugin"))
        has_uplugin = len(uplugin_files) > 0

        # Count pak files (in Content/Paks subdirectories)
        pak_files = list(mod_dir.rglob("*.pak"))
        pak_count = len(pak_files)

        # Count dll files (Windows binaries)
        dll_files = list(mod_dir.rglob("*.dll"))
        dll_count = len(dll_files)

        # Count .so files (Linux binaries)
        so_files = list(mod_dir.rglob("*.so"))
        so_count = len(so_files)

        # Try to read version from uplugin
        version = None
        if uplugin_files:
            try:
                with open(uplugin_files[0], 'r', encoding='utf-8') as f:
                    uplugin_data = json.load(f)
                    version = uplugin_data.get("VersionName") or uplugin_data.get("Version")
            except (json.JSONDecodeError, IOError):
                pass

        # Determine validity
        # A mod is valid if it has either:
        # - A .uplugin file (metadata)
        # - OR pak files (content)
        is_valid = has_uplugin or pak_count > 0

        if not is_valid:
            message = "Missing .uplugin and no pak files"
        elif not has_uplugin:
            message = "Missing .uplugin file (may still work)"
        elif pak_count == 0:
            message = "No pak files found (content-less mod?)"
        else:
            message = "Valid"

        return ModStatus(
            mod_reference=mod_ref,
            installed=True,
            valid=is_valid,
            version=version,
            has_uplugin=has_uplugin,
            pak_count=pak_count,
            dll_count=dll_count,
            so_count=so_count,
            message=message
        )

    def check_mod(self, mod_ref: str) -> ModStatus:
        """Check status of a specific mod."""
        mod_dir = self.mods_dir / mod_ref

        if not mod_dir.exists():
            return ModStatus(
                mod_reference=mod_ref,
                installed=False,
                valid=False,
                message="Not installed"
            )

        return self._check_mod_directory(mod_dir, mod_ref)

    def get_missing_mods(self, required_refs: List[str]) -> List[str]:
        """
        Compare required mods against installed mods.

        Returns:
            List of mod references that are missing or invalid
        """
        installed = self.scan_installed()
        missing = []

        for ref in required_refs:
            if ref not in installed:
                missing.append(ref)
            elif not installed[ref].valid:
                missing.append(ref)

        return missing


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


@dataclass
class GapAnalysisResult:
    """Result of comparing needed mods vs installed mods."""
    needed_mods: List[str]
    installed_mods: Dict[str, ModStatus]
    missing_mods: List[str]
    invalid_mods: List[str]
    valid_mods: List[str]
    resolution_errors: Dict[str, str]

    @property
    def all_ok(self) -> bool:
        """True if no mods need to be installed or repaired."""
        return len(self.missing_mods) == 0 and len(self.invalid_mods) == 0

    @property
    def mods_to_install(self) -> List[str]:
        """List of mods that need to be installed or re-installed."""
        return self.missing_mods + self.invalid_mods


@dataclass
class InstallPhaseResult:
    """Result of an installation phase."""
    phase_name: str
    success: bool
    message: str
    details: List[str]


class PreVerifyInstaller:
    """
    Pre-verification based mod installer.
    Resolves dependencies, scans installed mods, identifies gaps,
    and performs targeted repair/installation.
    """

    def __init__(self, game_path: str):
        self.game_path = Path(game_path)
        self.mods_dir = self.game_path / "FactoryGame" / "Mods"
        self.mods_dir.mkdir(parents=True, exist_ok=True)

        self.api_client = FicsitAPIClient()
        self.resolver = DependencyResolver(self.api_client)
        self.scanner = ModScanner(self.mods_dir)
        self.downloader = ModDownloader(str(self.mods_dir))

        # Results tracking
        self.resolved_mods: Dict[str, ResolvedMod] = {}
        self.gap_analysis: Optional[GapAnalysisResult] = None

    def phase1_resolve_dependencies(
        self,
        mod_references: List[str],
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> InstallPhaseResult:
        """
        Phase 1: Resolve all dependencies from ficsit.app API.

        Returns:
            InstallPhaseResult with resolution status
        """
        details = []
        details.append(f"Resolving dependencies for {len(mod_references)} selected mods...")

        if progress_callback:
            progress_callback("", "Phase 1: Resolving dependencies...")

        resolved_list, errors = self.resolver.resolve_all(mod_references, progress_callback)

        # Store resolved mods for later phases
        self.resolved_mods = {m.mod_reference: m for m in resolved_list}

        details.append(f"Resolved {len(resolved_list)} mods (including dependencies)")

        # Check for broken mods
        broken_mods = [m for m in resolved_list if m.is_broken]
        if broken_mods:
            details.append("")
            details.append("WARNING: The following mods are BROKEN and will be skipped:")
            for m in broken_mods:
                details.append(f"  [BROKEN] {m.mod_reference}: {m.compatibility_warning}")

        if errors:
            for ref, error in errors.items():
                if "BROKEN" not in error:  # Don't duplicate broken mod warnings
                    details.append(f"  [WARN] {ref}: {error}")

        # Check for mods without Windows targets
        no_windows = [m for m in resolved_list if not m.has_windows_target and not m.is_broken]
        if no_windows:
            for m in no_windows:
                details.append(f"  [WARN] {m.mod_reference}: No Windows version available")

        success = len(resolved_list) > 0
        message = f"Resolved {len(resolved_list)} mods" if success else "Failed to resolve any mods"

        return InstallPhaseResult(
            phase_name="Dependency Resolution",
            success=success,
            message=message,
            details=details
        )

    def phase2_scan_installed(
        self,
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> InstallPhaseResult:
        """
        Phase 2: Scan currently installed mods.

        Returns:
            InstallPhaseResult with scan status
        """
        details = []

        if progress_callback:
            progress_callback("", "Phase 2: Scanning installed mods...")

        installed = self.scanner.scan_installed()

        details.append(f"Found {len(installed)} installed mod folders")

        valid_count = sum(1 for s in installed.values() if s.valid)
        invalid_count = sum(1 for s in installed.values() if not s.valid)

        details.append(f"  Valid: {valid_count}")
        details.append(f"  Invalid/Incomplete: {invalid_count}")

        for ref, status in installed.items():
            if status.valid:
                details.append(f"  [OK] {ref} v{status.version or 'unknown'}")
            else:
                details.append(f"  [!!] {ref}: {status.message}")

        return InstallPhaseResult(
            phase_name="Mod Scan",
            success=True,
            message=f"Scanned {len(installed)} installed mods",
            details=details
        )

    def phase3_gap_analysis(
        self,
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> InstallPhaseResult:
        """
        Phase 3: Compare needed mods vs installed mods.

        Returns:
            InstallPhaseResult with gap analysis
        """
        details = []

        if progress_callback:
            progress_callback("", "Phase 3: Analyzing gaps...")

        # Get what we need (excluding broken mods)
        needed_refs = [
            ref for ref, mod in self.resolved_mods.items()
            if not mod.is_broken
        ]
        broken_refs = [
            ref for ref, mod in self.resolved_mods.items()
            if mod.is_broken
        ]
        installed = self.scanner.scan_installed()

        missing = []
        invalid = []
        valid = []
        skipped_broken = broken_refs.copy()

        for ref in needed_refs:
            if ref not in installed:
                missing.append(ref)
            elif not installed[ref].valid:
                invalid.append(ref)
            else:
                valid.append(ref)

        # Store result
        self.gap_analysis = GapAnalysisResult(
            needed_mods=needed_refs,
            installed_mods=installed,
            missing_mods=missing,
            invalid_mods=invalid,
            valid_mods=valid,
            resolution_errors=self.resolver.get_resolution_errors()
        )

        details.append(f"Need {len(needed_refs)} mods total (excluding broken)")
        details.append(f"  Already valid: {len(valid)}")
        details.append(f"  Missing: {len(missing)}")
        details.append(f"  Invalid/needs repair: {len(invalid)}")
        if skipped_broken:
            details.append(f"  Skipped (BROKEN): {len(skipped_broken)}")

        if missing:
            details.append("Missing mods:")
            for ref in missing:
                details.append(f"  - {ref}")

        if invalid:
            details.append("Invalid mods (will be re-downloaded):")
            for ref in invalid:
                details.append(f"  - {ref}")

        if skipped_broken:
            details.append("Skipped broken mods (incompatible with current game):")
            for ref in skipped_broken:
                details.append(f"  - {ref}")

        if self.gap_analysis.all_ok:
            message = "All required mods are already installed and valid!"
        else:
            message = f"{len(missing) + len(invalid)} mods need to be installed/repaired"

        return InstallPhaseResult(
            phase_name="Gap Analysis",
            success=True,
            message=message,
            details=details
        )

    def phase4_install_missing(
        self,
        progress_callback: Optional[Callable[[str, str], None]] = None,
        download_progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> InstallPhaseResult:
        """
        Phase 4: Download and install missing/invalid mods.

        Returns:
            InstallPhaseResult with installation status
        """
        details = []

        if not self.gap_analysis:
            return InstallPhaseResult(
                phase_name="Install Missing",
                success=False,
                message="Gap analysis not performed",
                details=["Run phase 3 first"]
            )

        mods_to_install = self.gap_analysis.mods_to_install

        if not mods_to_install:
            return InstallPhaseResult(
                phase_name="Install Missing",
                success=True,
                message="No mods need to be installed",
                details=["All required mods are already present"]
            )

        if progress_callback:
            progress_callback("", f"Phase 4: Installing {len(mods_to_install)} mods...")

        details.append(f"Installing {len(mods_to_install)} mods...")

        success_count = 0
        fail_count = 0
        failed_mods = []

        for i, ref in enumerate(mods_to_install):
            if progress_callback:
                progress_callback(ref, f"Installing {ref} ({i+1}/{len(mods_to_install)})...")

            resolved = self.resolved_mods.get(ref)
            if not resolved or not resolved.download_url:
                details.append(f"  [SKIP] {ref}: No download URL available")
                fail_count += 1
                failed_mods.append(ref)
                continue

            result = self.downloader.download_and_install(
                ref,
                resolved.download_url,
                download_progress_callback
            )

            if result.success:
                details.append(f"  [OK] {ref} v{resolved.version}: {result.message}")
                success_count += 1
            else:
                details.append(f"  [FAIL] {ref}: {result.message}")
                fail_count += 1
                failed_mods.append(ref)

        success = fail_count == 0
        message = f"Installed {success_count}/{len(mods_to_install)} mods"
        if failed_mods:
            message += f" ({fail_count} failed)"

        return InstallPhaseResult(
            phase_name="Install Missing",
            success=success,
            message=message,
            details=details
        )

    def phase5_final_verify(
        self,
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> InstallPhaseResult:
        """
        Phase 5: Final verification that all required mods are correctly installed.

        Returns:
            InstallPhaseResult with final verification status
        """
        details = []

        if progress_callback:
            progress_callback("", "Phase 5: Final verification...")

        needed_refs = list(self.resolved_mods.keys())
        installed = self.scanner.scan_installed()

        all_valid = True
        still_missing = []
        still_invalid = []

        for ref in needed_refs:
            if ref not in installed:
                still_missing.append(ref)
                all_valid = False
            elif not installed[ref].valid:
                still_invalid.append(ref)
                all_valid = False
            else:
                status = installed[ref]
                details.append(f"  [OK] {ref}: {status.pak_count} pak, {status.dll_count} dll")

        if still_missing:
            details.append("STILL MISSING:")
            for ref in still_missing:
                details.append(f"  [!!] {ref}")

        if still_invalid:
            details.append("STILL INVALID:")
            for ref in still_invalid:
                status = installed.get(ref)
                msg = status.message if status else "Unknown"
                details.append(f"  [!!] {ref}: {msg}")

        if all_valid:
            message = f"All {len(needed_refs)} required mods are correctly installed!"
        else:
            message = f"VERIFICATION FAILED: {len(still_missing)} missing, {len(still_invalid)} invalid"

        return InstallPhaseResult(
            phase_name="Final Verification",
            success=all_valid,
            message=message,
            details=details
        )

    def run_full_installation(
        self,
        mod_references: List[str],
        progress_callback: Optional[Callable[[str, str], None]] = None,
        download_progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[bool, List[InstallPhaseResult]]:
        """
        Run the complete pre-verify, repair, install workflow.

        Args:
            mod_references: List of mod references to install
            progress_callback: Optional callback(mod_ref, status_message)
            download_progress_callback: Optional callback(downloaded_bytes, total_bytes)

        Returns:
            Tuple of (overall_success, list of phase results)
        """
        phases = []

        # Phase 1: Resolve dependencies
        result = self.phase1_resolve_dependencies(mod_references, progress_callback)
        phases.append(result)
        if not result.success:
            return False, phases

        # Phase 2: Scan installed
        result = self.phase2_scan_installed(progress_callback)
        phases.append(result)

        # Phase 3: Gap analysis
        result = self.phase3_gap_analysis(progress_callback)
        phases.append(result)

        # Phase 4: Install missing (if any)
        if self.gap_analysis and not self.gap_analysis.all_ok:
            result = self.phase4_install_missing(progress_callback, download_progress_callback)
            phases.append(result)

        # Phase 5: Final verification
        result = self.phase5_final_verify(progress_callback)
        phases.append(result)

        overall_success = result.success
        return overall_success, phases

    def get_needed_mods_summary(self) -> str:
        """Get a summary of what mods are needed and their status."""
        if not self.gap_analysis:
            return "Gap analysis not performed yet"

        lines = [
            f"Total needed: {len(self.gap_analysis.needed_mods)}",
            f"Already valid: {len(self.gap_analysis.valid_mods)}",
            f"Need to install: {len(self.gap_analysis.mods_to_install)}",
        ]
        return "\n".join(lines)

    def cleanup_obsolete_mods(
        self,
        valid_mod_refs: List[str],
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Remove mod folders that are not in the valid mod list.
        This cleans up broken/obsolete mods that may cause game errors.

        Args:
            valid_mod_refs: List of mod references that should remain installed
            progress_callback: Optional callback(mod_ref, status_message)

        Returns:
            Tuple of (removed_mods, failed_to_remove)
        """
        removed = []
        failed = []

        if not self.mods_dir.exists():
            return removed, failed

        if progress_callback:
            progress_callback("", "Cleaning up obsolete mods...")

        # Get all installed mod folders
        installed_folders = [d.name for d in self.mods_dir.iterdir() if d.is_dir()]

        # Find mods to remove (installed but not in valid list)
        valid_set = set(valid_mod_refs)
        to_remove = [ref for ref in installed_folders if ref not in valid_set]

        if not to_remove:
            logger.info("No obsolete mods to remove")
            return removed, failed

        logger.info(f"Found {len(to_remove)} obsolete mods to remove: {to_remove}")

        for mod_ref in to_remove:
            mod_path = self.mods_dir / mod_ref

            if progress_callback:
                progress_callback(mod_ref, f"Removing obsolete mod: {mod_ref}")

            try:
                shutil.rmtree(mod_path)
                removed.append(mod_ref)
                logger.info(f"Removed obsolete mod: {mod_ref}")
            except Exception as e:
                failed.append(mod_ref)
                logger.error(f"Failed to remove {mod_ref}: {e}")

        return removed, failed


def get_embedded_mods_config() -> List[Dict]:
    """
    Return embedded mod configuration for standalone executable.
    This is used when mods-list.json is not available.
    Synced with server mods-list.json - 44 mods total.

    NOTE: Removed mods (no longer available or broken):
    - Smart! (SmartFoundations) - no longer on ficsit.app
    - ContainerScreen - no longer on ficsit.app
    - MicroManage - marked as BROKEN
    - PowerSuit - marked as BROKEN
    - Teleporter - marked as BROKEN
    - MK22k20 (Mk++) - marked as BROKEN
    """
    return [
        # Core dependencies (priority 0-1) - 10 mods
        {"name": "Satisfactory Mod Loader", "mod_reference": "SML", "category": "dependency", "required": True, "priority": 0, "description": "Required for ALL mods"},
        {"name": "Pak Utility Mod", "mod_reference": "UtilityMod", "category": "dependency", "required": True, "priority": 1, "description": "Required dependency for most mods"},
        {"name": "Mod Update Notifier", "mod_reference": "ModUpdateNotifier", "category": "dependency", "required": True, "priority": 1, "description": "Notifies of mod updates"},
        {"name": "Marcio Common Libs", "mod_reference": "MarcioCommonLibs", "category": "dependency", "required": True, "priority": 1, "description": "Required by Efficiency Checker"},
        {"name": "MinoDabs Common Lib", "mod_reference": "MinoDabsCommonLib", "category": "dependency", "required": True, "priority": 1, "description": "Required by Additional_300_Inventory_Slots"},
        {"name": "Modular UI", "mod_reference": "ModularUI", "category": "dependency", "required": True, "priority": 1, "description": "Required by Refined Power, Ficsit Farming"},
        {"name": "Refined R&D API", "mod_reference": "RefinedRDApi", "category": "dependency", "required": True, "priority": 1, "description": "Required by Refined Power, Ficsit Farming"},
        {"name": "Refined R&D Lib", "mod_reference": "RefinedRDLib", "category": "dependency", "required": True, "priority": 1, "description": "Required by Refined Power, Ficsit Farming"},
        {"name": "avMall Lib", "mod_reference": "avMallLib", "category": "dependency", "required": True, "priority": 1, "description": "Required by Item Dispenser"},
        {"name": "ContentLib", "mod_reference": "ContentLib", "category": "dependency", "required": True, "priority": 1, "description": "Content library for FlexSplines and other mods"},
        # Quality of Life mods (priority 2) - 18 mods
        {"name": "Efficiency Checker", "mod_reference": "EfficiencyCheckerMod", "category": "quality-of-life", "required": False, "priority": 2, "description": "Monitor production efficiency"},
        {"name": "Infinite Zoop", "mod_reference": "InfiniteZoop", "category": "quality-of-life", "required": False, "priority": 2, "description": "Unlimited zoop range"},
        {"name": "Infinite Nudge", "mod_reference": "InfiniteNudge", "category": "quality-of-life", "required": False, "priority": 2, "description": "Unlimited nudge range"},
        {"name": "Structural Solutions", "mod_reference": "SS_Mod", "category": "quality-of-life", "required": False, "priority": 2, "description": "More building options"},
        {"name": "Load Balancers", "mod_reference": "LoadBalancers", "category": "quality-of-life", "required": False, "priority": 2, "description": "Better load balancing"},
        {"name": "MAM Enhancer", "mod_reference": "MAMTips", "category": "quality-of-life", "required": False, "priority": 2, "description": "Enhanced MAM interface"},
        {"name": "MiniMap", "mod_reference": "MiniMap", "category": "quality-of-life", "required": False, "priority": 2, "description": "In-game minimap"},
        {"name": "Floor Hole", "mod_reference": "FloorHole", "category": "quality-of-life", "required": False, "priority": 2, "description": "Pass conveyors through floors"},
        {"name": "Conveyor Wall Hole", "mod_reference": "WallHoleConveyor", "category": "quality-of-life", "required": False, "priority": 2, "description": "Holes in walls for conveyors"},
        {"name": "Flex Splines", "mod_reference": "FlexSplines", "category": "quality-of-life", "required": False, "priority": 2, "description": "Longer conveyors and pipes"},
        {"name": "Daisy Chain Power", "mod_reference": "DaisyChainPowerCables", "category": "quality-of-life", "required": False, "priority": 2, "description": "4 power connections for daisy-chaining"},
        {"name": "Covered Conveyor Belts", "mod_reference": "CoveredConveyor", "category": "quality-of-life", "required": False, "priority": 2, "description": "Aesthetic covered conveyor belts"},
        {"name": "Underground Belts", "mod_reference": "UndergroundBelts", "category": "quality-of-life", "required": False, "priority": 2, "description": "Hidden underground conveyor belts"},
        {"name": "Wall Pipe Supports", "mod_reference": "WallPipeSupports", "category": "quality-of-life", "required": False, "priority": 2, "description": "Additional wall pipe supports"},
        {"name": "Upside Down Foundations", "mod_reference": "UpsideDownFoundations", "category": "quality-of-life", "required": False, "priority": 2, "description": "More foundation options"},
        {"name": "Power Checker", "mod_reference": "PowerChecker", "category": "quality-of-life", "required": False, "priority": 2, "description": "Monitor power consumption"},
        {"name": "Throughput Counter", "mod_reference": "CounterLimiter", "category": "quality-of-life", "required": False, "priority": 2, "description": "Display and limit item throughput"},
        {"name": "FicsIt-Networks", "mod_reference": "FicsItNetworks", "category": "quality-of-life", "required": False, "priority": 2, "description": "Lua scripting for automation"},
        # Content mods (priority 3) - 11 mods
        {"name": "Refined Power", "mod_reference": "RefinedPower", "category": "content", "required": False, "priority": 3, "description": "New power generation options"},
        {"name": "Ficsit Farming", "mod_reference": "FicsitFarming", "category": "content", "required": False, "priority": 3, "description": "Farming mechanics"},
        {"name": "Linear Motion", "mod_reference": "LinearMotion", "category": "content", "required": False, "priority": 3, "description": "Moving platforms and elevators"},
        {"name": "Fluid Extras", "mod_reference": "AB_FluidExtras", "category": "content", "required": False, "priority": 3, "description": "Additional fluid handling"},
        {"name": "Storage Teleporter", "mod_reference": "StorageTeleporter", "category": "content", "required": False, "priority": 3, "description": "Teleport items between storage"},
        {"name": "Big Storage Tank", "mod_reference": "BigStorageTank", "category": "content", "required": False, "priority": 3, "description": "Large fluid storage"},
        {"name": "Item Dispenser", "mod_reference": "Dispenser", "category": "content", "required": False, "priority": 3, "description": "Automatic item dispensing"},
        {"name": "Magic Machines", "mod_reference": "MagicMachine", "category": "content", "required": False, "priority": 3, "description": "Spawners for fluids, solids, energy"},
        {"name": "Faster Manual Crafting", "mod_reference": "FasterManualCraftingRedux", "category": "content", "required": False, "priority": 3, "description": "Speed up manual crafting"},
        {"name": "Advanced Logistics", "mod_reference": "AdvancedLogistics", "category": "content", "required": False, "priority": 3, "description": "Programmable splitters and mergers"},
        {"name": "Fluid Sink", "mod_reference": "FluidSink", "category": "content", "required": False, "priority": 3, "description": "Sink fluids and overflow valves"},
        # Cheat mods (priority 4) - 5 mods
        {"name": "EasyCheat", "mod_reference": "EasyCheat", "category": "cheat", "required": False, "priority": 4, "description": "Cheat menu"},
        {"name": "Extra Inventory", "mod_reference": "Additional_300_Inventory_Slots", "category": "cheat", "required": False, "priority": 4, "description": "300 extra inventory slots"},
        {"name": "Unlock All Recipes", "mod_reference": "UnlockAllAlternateRecipes", "category": "cheat", "required": False, "priority": 4, "description": "Unlock all alternate recipes"},
        {"name": "Item Spawner", "mod_reference": "ItemSpawner", "category": "cheat", "required": False, "priority": 4, "description": "Spawn any item in-game"},
        {"name": "All Nodes Pure", "mod_reference": "AllNodesPure", "category": "cheat", "required": False, "priority": 4, "description": "All resource nodes are pure"},
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
