#!/usr/bin/env python3
"""
Build Script for Satisfactory Mod Installer
Creates a standalone Windows executable using PyInstaller.

Requirements:
    pip install pyinstaller

Usage:
    python build_exe.py

Output:
    dist/SatisfactoryModInstaller.exe
"""

import os
import sys
import subprocess
from pathlib import Path

# Build configuration
APP_NAME = "SatisfactoryModInstaller"
MAIN_SCRIPT = "mod_installer_gui.py"
ICON_PATH = "assets/icon.ico"

# PyInstaller options
PYINSTALLER_OPTIONS = [
    "--onefile",           # Single executable
    "--windowed",          # No console window
    "--clean",             # Clean cache before build
    "--noconfirm",         # Overwrite without asking
    f"--name={APP_NAME}",
]


def check_dependencies():
    """Check if required build tools are installed."""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print("[ERROR] PyInstaller not found!")
        print("        Install with: pip install pyinstaller")
        return False


def create_spec_file():
    """Create a custom .spec file for more control over the build."""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{ICON_PATH}' if os.path.exists('{ICON_PATH}') else None,
)
'''

    spec_path = Path(f"{APP_NAME}.spec")
    with open(spec_path, 'w') as f:
        f.write(spec_content)

    print(f"[OK] Created {spec_path}")
    return spec_path


def build_executable():
    """Build the executable using PyInstaller."""
    print("\n" + "=" * 50)
    print("Building Satisfactory Mod Installer")
    print("=" * 50 + "\n")

    # Check dependencies
    if not check_dependencies():
        return False

    # Check main script exists
    if not os.path.exists(MAIN_SCRIPT):
        print(f"[ERROR] Main script not found: {MAIN_SCRIPT}")
        return False

    print(f"[OK] Main script: {MAIN_SCRIPT}")

    # Check for icon
    if os.path.exists(ICON_PATH):
        PYINSTALLER_OPTIONS.append(f"--icon={ICON_PATH}")
        print(f"[OK] Icon: {ICON_PATH}")
    else:
        print(f"[WARN] Icon not found: {ICON_PATH}")
        print("       Building without custom icon")

    # Add hidden imports for customtkinter
    PYINSTALLER_OPTIONS.extend([
        "--hidden-import=customtkinter",
        "--hidden-import=PIL._tkinter_finder",
        "--collect-all=customtkinter",
    ])

    # Build command
    cmd = ["pyinstaller"] + PYINSTALLER_OPTIONS + [MAIN_SCRIPT]

    print("\n[INFO] Running PyInstaller...")
    print(f"       Command: {' '.join(cmd)}")
    print()

    # Run PyInstaller
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)) or ".")

    if result.returncode == 0:
        exe_path = Path("dist") / f"{APP_NAME}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n" + "=" * 50)
            print("Build Successful!")
            print("=" * 50)
            print(f"\nOutput: {exe_path.absolute()}")
            print(f"Size: {size_mb:.1f} MB")
            print("\nYou can now distribute this .exe file to your friends!")
            return True

    print("\n[ERROR] Build failed!")
    return False


def create_icon_placeholder():
    """Create a placeholder icon if none exists."""
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)

    icon_path = assets_dir / "icon.ico"
    if not icon_path.exists():
        print(f"[INFO] No icon found. For a custom icon:")
        print(f"       1. Create or download a 256x256 .ico file")
        print(f"       2. Save it as: {icon_path.absolute()}")


def main():
    """Main entry point."""
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)

    print(f"Working directory: {script_dir}")

    # Create icon placeholder info
    create_icon_placeholder()

    # Build
    success = build_executable()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
