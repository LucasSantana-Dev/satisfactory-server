# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Satisfactory Mod Installer
Creates a single-file Windows executable with all dependencies bundled.

Usage:
    pyinstaller SatisfactoryModInstaller.spec

Output:
    dist/SatisfactoryModInstaller.exe
"""

import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Collect all customtkinter data (themes, assets, etc.)
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all('customtkinter')

# Application metadata
APP_NAME = 'SatisfactoryModInstaller'
APP_VERSION = '1.0.0'

# Analysis - find all dependencies
a = Analysis(
    ['mod_installer_gui.py'],
    pathex=[],
    binaries=ctk_binaries,
    datas=ctk_datas,
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'PIL.Image',
        'PIL.ImageTk',
        'requests',
        'json',
        'zipfile',
        'threading',
        'queue',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ] + ctk_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'setuptools',
        'wheel',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Create the PYZ archive (compressed Python modules)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Use UPX compression if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # No custom icon - use default
    version_info=None,  # Can add Windows version info here
)

