#!/usr/bin/env python3
"""
Satisfactory Mod Installation Script using Browser Automation
Uses Playwright to navigate ficsit.app and download mods automatically

Requirements:
    pip install playwright
    playwright install chromium
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from common import (
    init_script, load_json_config, get_file_size,
    print_header, print_info, print_success, print_error, print_warn,
    Colors
)

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print_error("'playwright' library not found")
    print("Install with: pip3 install playwright && playwright install chromium")
    sys.exit(1)


def create_backup(paths, logger):
    """Create backup before mod installation"""
    paths.mods.mkdir(parents=True, exist_ok=True)
    paths.backups.mkdir(parents=True, exist_ok=True)

    backup_name = f"pre-mods-{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"
    backup_path = paths.backups / backup_name

    try:
        subprocess.run(
            ["tar", "-czf", str(backup_path), "-C", str(paths.project),
             "data/saved", "data/gamefiles/FactoryGame/Mods"],
            check=True, capture_output=True
        )
        size = get_file_size(backup_path)
        logger.info(f"Backup created: {backup_name} (Size: {size})")
        print_success("Backup created")
        return True
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ["tar", "-czf", str(backup_path), "-C", str(paths.project), "data/saved"],
                check=True, capture_output=True
            )
            logger.info(f"Backup created (saves only): {backup_name}")
            return True
        except Exception:
            logger.warn("Backup creation failed")
            print_warn("Backup failed, continuing...")
            return False


def download_mod_browser(page, mod_info, paths, logger):
    """Download a mod using browser automation"""
    mod_name = mod_info["name"]
    mod_slug = mod_info["slug"]
    mod_url = mod_info["url"]

    output_file = paths.mods / f"{mod_slug}.pak"

    # Skip if already exists
    if output_file.exists():
        logger.info(f"Mod already installed: {mod_name}")
        print_warn(f"{mod_name} already installed, skipping...")
        return True

    print_info(f"Downloading: {mod_name}...")
    logger.info(f"Downloading {mod_name} ({mod_slug}) from {mod_url}")

    try:
        # Navigate to mod page
        logger.info(f"Navigating to {mod_url}")
        page.goto(mod_url, wait_until="networkidle", timeout=30000)

        # Wait for page to fully load (JavaScript rendering)
        time.sleep(2)

        # Try to find download button
        download_button = None

        selectors = [
            'button:has-text("download")',
            'button[aria-label*="download" i]',
            'a:has-text("download")',
            'button.download',
            '[data-testid*="download"]',
            'button:has(svg)',
        ]

        for selector in selectors:
            try:
                download_button = page.locator(selector).first
                if download_button.is_visible(timeout=2000):
                    logger.info(f"Found download button with selector: {selector}")
                    break
            except Exception:
                continue

        # If no button found, try to find by text content
        if not download_button or not download_button.is_visible():
            all_buttons = page.locator('button, a').all()
            for btn in all_buttons:
                try:
                    text = btn.inner_text().lower()
                    if 'download' in text or 'install' in text:
                        download_button = btn
                        logger.info(f"Found download button by text: {text}")
                        break
                except Exception:
                    continue

        if not download_button:
            logger.error(f"Could not find download button for {mod_name}")
            print_error(f"Could not find download button: {mod_name}")
            return False

        # Set up download listener
        with page.expect_download(timeout=30000) as download_info:
            logger.info(f"Clicking download button for {mod_name}")
            download_button.click()
            download = download_info.value

        # Wait for download to complete
        logger.info("Download started, waiting for completion...")
        downloaded_file = download.path()

        if not downloaded_file or not os.path.exists(downloaded_file):
            logger.error(f"Download file not found for {mod_name}")
            print_error(f"Download failed: {mod_name}")
            return False

        # Move downloaded file to mods directory
        logger.info("Moving downloaded file to mods directory")
        shutil.move(downloaded_file, output_file)

        # Verify file
        if not output_file.exists() or output_file.stat().st_size == 0:
            logger.error(f"Downloaded file is invalid for {mod_name}")
            if output_file.exists():
                output_file.unlink()
            print_error(f"Invalid file downloaded: {mod_name}")
            return False

        # Set permissions
        output_file.chmod(0o644)
        size = get_file_size(output_file)
        logger.success(f"Downloaded {mod_name} ({size})")
        print_success(f"Downloaded: {mod_name} ({size})")
        return True

    except PlaywrightTimeout as e:
        logger.error(f"Timeout downloading {mod_name}: {e}")
        print_error(f"Timeout downloading: {mod_name}")
        return False
    except Exception as e:
        logger.error(f"Failed to download {mod_name}: {e}")
        print_error(f"Download failed: {mod_name} - {str(e)}")
        return False


def main():
    print_header("Satisfactory Mod Installation (Browser Automation)")

    # Initialize
    paths, logger = init_script("mods-browser-install", "mods-browser-install")

    # Create directories
    paths.mods.mkdir(parents=True, exist_ok=True)

    # Load mods list
    mods_list_file = paths.mods_config / "mods-list.json"
    mods_data = load_json_config(mods_list_file)

    if not mods_data:
        print_error(f"Mods list not found: {mods_list_file}")
        return 1

    # Create backup
    create_backup(paths, logger)

    print_header("Installing Mods")

    # Install in priority order
    installed = 0
    failed = 0

    with sync_playwright() as p:
        logger.info("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            for priority in [1, 2, 3, 4]:
                mods = [m for m in mods_data["mods"] if m.get("priority") == priority]
                if not mods:
                    continue

                category = mods[0].get("category", "unknown")
                print_header(f"Installing {category} mods (priority {priority})")

                for mod in mods:
                    if download_mod_browser(page, mod, paths, logger):
                        installed += 1
                    else:
                        failed += 1

                    # Small delay between downloads
                    time.sleep(2)

        finally:
            browser.close()

    # Summary
    print_header("Installation Summary")
    total_installed = len(list(paths.mods.glob("*.pak")))
    print_success("Installation complete!")
    print(f"   Successfully downloaded: {installed}")
    print(f"   Failed downloads: {failed}")
    print(f"   Total mods in directory: {total_installed}")
    print(f"   Location: {paths.mods}")
    print()

    if failed > 0:
        print_warn("Note: Some mods failed to download.")
        print_warn(f"Check the log file for details: {paths.logs / 'mods-browser-install.log'}")

    print()
    print_info("Next steps:")
    print("1. Review installed mods: ls -lh data/gamefiles/FactoryGame/Mods/")
    print("2. Restart server: docker compose restart satisfactory")
    print("3. Install same mods on your game client using Satisfactory Mod Manager")

    return 0


if __name__ == "__main__":
    sys.exit(main())
