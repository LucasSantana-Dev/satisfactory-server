#!/usr/bin/env python3
"""
Satisfactory Server - Common Python Library
Shared functions for all Python scripts
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

# =============================================================================
# Path Resolution
# =============================================================================

def get_scripts_dir() -> Path:
    """Get the scripts root directory"""
    current_file = Path(__file__).resolve()
    # lib/common.py -> go up to scripts/
    return current_file.parent.parent


def get_project_dir() -> Path:
    """Get the project root directory"""
    return get_scripts_dir().parent


@dataclass
class ProjectPaths:
    """Container for all project paths"""
    scripts: Path
    project: Path
    data: Path
    logs: Path
    backups: Path
    saves: Path
    mods: Path
    mods_config: Path
    docker_compose: Path
    env_file: Path


def init_paths() -> ProjectPaths:
    """Initialize and return all project paths"""
    scripts_dir = get_scripts_dir()
    project_dir = get_project_dir()
    data_dir = project_dir / "data"

    paths = ProjectPaths(
        scripts=scripts_dir,
        project=project_dir,
        data=data_dir,
        logs=data_dir / "logs",
        backups=data_dir / "backups",
        saves=data_dir / "saved",
        mods=data_dir / "gamefiles" / "FactoryGame" / "Mods",
        mods_config=scripts_dir / "mods" / "config",
        docker_compose=project_dir / "docker-compose.yml",
        env_file=project_dir / ".env"
    )

    # Create necessary directories
    paths.logs.mkdir(parents=True, exist_ok=True)
    paths.backups.mkdir(parents=True, exist_ok=True)
    paths.mods.mkdir(parents=True, exist_ok=True)

    return paths


# =============================================================================
# Terminal Colors
# =============================================================================

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

    @classmethod
    def green(cls, text: str) -> str:
        return f"{cls.GREEN}{text}{cls.NC}"

    @classmethod
    def red(cls, text: str) -> str:
        return f"{cls.RED}{text}{cls.NC}"

    @classmethod
    def yellow(cls, text: str) -> str:
        return f"{cls.YELLOW}{text}{cls.NC}"

    @classmethod
    def blue(cls, text: str) -> str:
        return f"{cls.BLUE}{text}{cls.NC}"

    @classmethod
    def cyan(cls, text: str) -> str:
        return f"{cls.CYAN}{text}{cls.NC}"

    @classmethod
    def bold(cls, text: str) -> str:
        return f"{cls.BOLD}{text}{cls.NC}"


# =============================================================================
# Logging
# =============================================================================

class Logger:
    """Simple logger with file and console output"""

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}"

        print(log_line)

        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(log_line + "\n")

    def info(self, message: str):
        self._log("INFO", message)

    def warn(self, message: str):
        self._log("WARNING", message)

    def error(self, message: str):
        self._log("ERROR", message)

    def success(self, message: str):
        self._log("SUCCESS", message)


# Print functions (colored, no log file)
def print_info(message: str):
    print(Colors.blue(message))


def print_success(message: str):
    print(Colors.green(f"✓ {message}"))


def print_error(message: str):
    print(Colors.red(f"✗ {message}"))


def print_warn(message: str):
    print(Colors.yellow(f"⚠ {message}"))


def print_header(title: str):
    print(f"\n{Colors.blue(f'=== {title} ===')}\n")


# =============================================================================
# Environment Loading
# =============================================================================

def load_env(env_file: Optional[Path] = None) -> Dict[str, str]:
    """Load environment variables from .env file"""
    if env_file is None:
        env_file = get_project_dir() / ".env"

    env_vars = {}

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes from value
                        value = value.strip().strip('"').strip("'")
                        env_vars[key.strip()] = value
                        os.environ[key.strip()] = value

    return env_vars


def get_env(key: str, default: str = "") -> str:
    """Get environment variable with default"""
    return os.environ.get(key, default)


# =============================================================================
# Docker Operations
# =============================================================================

def is_container_running(container_name: str = "satisfactory-server",
                         compose_file: Optional[Path] = None) -> bool:
    """Check if a Docker container is running"""
    if compose_file is None:
        compose_file = get_project_dir() / "docker-compose.yml"

    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "ps", container_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        return "Up" in result.stdout
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return False


def get_container_health(container_name: str = "satisfactory-server") -> str:
    """Get container health status"""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format={{.State.Health.Status}}", container_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip() or "unknown"
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return "unknown"


# =============================================================================
# Discord Notifications
# =============================================================================

# Discord embed colors
class DiscordColors:
    GREEN = 3066993
    RED = 15158332
    YELLOW = 15844367
    BLUE = 3447003


def send_discord_notification(title: str, message: str,
                               color: int = DiscordColors.BLUE) -> bool:
    """Send Discord notification via webhook"""
    webhook_url = get_env("DISCORD_WEBHOOK_URL")

    if not webhook_url or webhook_url == "your_discord_webhook_url_here":
        return True  # Not configured, skip silently

    try:
        import requests

        embed = {
            "embeds": [{
                "title": title,
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }]
        }

        response = requests.post(
            webhook_url,
            json=embed,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return response.status_code == 204
    except Exception:
        return False


# =============================================================================
# Backup Utilities
# =============================================================================

def create_backup_archive(paths: ProjectPaths, backup_name: str,
                          backup_type: str = "daily") -> Optional[Path]:
    """Create a backup archive"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    date_only = datetime.now().strftime("%Y%m%d")

    if backup_type == "weekly":
        backup_file = paths.backups / f"{backup_name}-weekly-{date_only}.tar.gz"
    else:
        backup_file = paths.backups / f"{backup_name}-{timestamp}.tar.gz"

    return backup_file


# =============================================================================
# Dependency Checking
# =============================================================================

def check_python_dependencies(*packages: str) -> bool:
    """Check if Python packages are installed"""
    missing = []
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print_error(f"Missing Python packages: {', '.join(missing)}")
        print(f"Install with: pip3 install {' '.join(missing)}")
        return False
    return True


def check_command_dependencies(*commands: str) -> bool:
    """Check if shell commands are available"""
    import shutil
    missing = [cmd for cmd in commands if not shutil.which(cmd)]

    if missing:
        print_error(f"Missing commands: {', '.join(missing)}")
        return False
    return True


# =============================================================================
# JSON Configuration
# =============================================================================

def load_json_config(config_file: Path) -> Optional[Dict[str, Any]]:
    """Load JSON configuration file"""
    if not config_file.exists():
        print_error(f"Configuration file not found: {config_file}")
        return None

    try:
        with open(config_file) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in {config_file}: {e}")
        return None


# =============================================================================
# File Size Formatting
# =============================================================================

def get_file_size(file_path: Path) -> str:
    """Get human-readable file size"""
    try:
        result = subprocess.run(
            ["du", "-h", str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.split()[0]
    except Exception:
        return "unknown"


# =============================================================================
# Script Initialization
# =============================================================================

def init_script(script_name: str, log_name: Optional[str] = None) -> tuple:
    """
    Initialize a script with paths, env, and optional logger.
    Returns: (paths, logger)
    """
    paths = init_paths()
    load_env(paths.env_file)

    logger = None
    if log_name:
        log_file = paths.logs / f"{log_name}.log"
        logger = Logger(log_file)

    return paths, logger
