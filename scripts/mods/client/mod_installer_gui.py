"""
Satisfactory Mod Installer - GUI Application
A modern desktop application for installing Satisfactory mods.
"""

import os
import sys
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import customtkinter as ctk

# Import core logic - handle both packaged and development scenarios
try:
    from mod_installer_core import (
        GamePathDetector, ModManager, Mod, InstallResult,
        FicsitAPIClient, get_embedded_mods_config
    )
except ImportError:
    # When running as packaged exe, might need different import
    from .mod_installer_core import (
        GamePathDetector, ModManager, Mod, InstallResult,
        FicsitAPIClient, get_embedded_mods_config
    )


# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ModInstallerApp(ctk.CTk):
    """Main application window."""

    CATEGORY_NAMES = {
        "dependency": "Required Dependencies",
        "quality-of-life": "Quality of Life",
        "content": "Content Mods",
        "cheat": "Cheat Mods",
        "other": "Other"
    }

    CATEGORY_ORDER = ["dependency", "quality-of-life", "content", "cheat", "other"]

    def __init__(self):
        super().__init__()

        self.title("Satisfactory Mod Installer")
        self.geometry("700x800")
        self.minsize(600, 600)

        # State
        self.game_path: Optional[str] = None
        self.mod_manager: Optional[ModManager] = None
        self.mod_checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.mod_vars: Dict[str, ctk.BooleanVar] = {}
        self.is_installing = False
        self.install_queue = queue.Queue()

        # Setup UI
        self._create_widgets()
        self._detect_game_path()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Mod list area expands

        # Header
        self._create_header()

        # Game path section
        self._create_path_section()

        # Mod list section
        self._create_mod_list_section()

        # Progress section
        self._create_progress_section()

        # Log section
        self._create_log_section()

        # Action buttons
        self._create_action_buttons()

    def _create_header(self):
        """Create header with title and theme toggle."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Satisfactory Mod Installer",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Theme toggle
        self.theme_switch = ctk.CTkSwitch(
            header_frame,
            text="Dark Mode",
            command=self._toggle_theme,
            onvalue=True,
            offvalue=False
        )
        self.theme_switch.grid(row=0, column=1, sticky="e")
        self.theme_switch.select()  # Start in dark mode

    def _create_path_section(self):
        """Create game path selection section."""
        path_frame = ctk.CTkFrame(self)
        path_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        path_frame.grid_columnconfigure(1, weight=1)

        # Label
        path_label = ctk.CTkLabel(path_frame, text="Game Path:")
        path_label.grid(row=0, column=0, padx=10, pady=10)

        # Entry
        self.path_entry = ctk.CTkEntry(path_frame, placeholder_text="Detecting...")
        self.path_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=10)

        # Browse button
        browse_btn = ctk.CTkButton(
            path_frame,
            text="Browse",
            width=80,
            command=self._browse_path
        )
        browse_btn.grid(row=0, column=2, padx=10, pady=10)

        # Status label
        self.path_status = ctk.CTkLabel(
            path_frame,
            text="",
            text_color="gray"
        )
        self.path_status.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10))

    def _create_mod_list_section(self):
        """Create scrollable mod list section."""
        # Container frame
        list_container = ctk.CTkFrame(self)
        list_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(1, weight=1)

        # Selection buttons
        btn_frame = ctk.CTkFrame(list_container, fg_color="transparent")
        btn_frame.grid(row=0, column=0, sticky="ew", pady=(10, 5))

        select_all_btn = ctk.CTkButton(
            btn_frame,
            text="Select All",
            width=100,
            command=self._select_all
        )
        select_all_btn.pack(side="left", padx=5)

        deselect_all_btn = ctk.CTkButton(
            btn_frame,
            text="Deselect All",
            width=100,
            command=self._deselect_all
        )
        deselect_all_btn.pack(side="left", padx=5)

        required_btn = ctk.CTkButton(
            btn_frame,
            text="Required Only",
            width=100,
            command=self._select_required
        )
        required_btn.pack(side="left", padx=5)

        # Scrollable frame for mods
        self.mod_list_frame = ctk.CTkScrollableFrame(
            list_container,
            label_text="Available Mods"
        )
        self.mod_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.mod_list_frame.grid_columnconfigure(0, weight=1)

    def _create_progress_section(self):
        """Create progress bar and status section."""
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        progress_frame.grid_columnconfigure(0, weight=1)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=5)
        self.progress_bar.set(0)

        # Status label
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=1, column=0, sticky="w", pady=5)

    def _create_log_section(self):
        """Create log output section."""
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        log_frame.grid_columnconfigure(0, weight=1)

        # Log textbox
        self.log_text = ctk.CTkTextbox(log_frame, height=120)
        self.log_text.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.log_text.configure(state="disabled")

    def _create_action_buttons(self):
        """Create main action buttons."""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=(10, 20))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Install button
        self.install_btn = ctk.CTkButton(
            btn_frame,
            text="Install Selected Mods",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._start_installation
        )
        self.install_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Verify button
        self.verify_btn = ctk.CTkButton(
            btn_frame,
            text="Verify Installation",
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="gray40",
            command=self._verify_installation
        )
        self.verify_btn.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

    def _toggle_theme(self):
        """Toggle between dark and light mode."""
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="Light Mode")

    def _detect_game_path(self):
        """Auto-detect game installation path."""
        self.log("Detecting Satisfactory installation...")

        def detect_thread():
            path = GamePathDetector.detect()
            self.after(0, lambda: self._on_path_detected(path))

        threading.Thread(target=detect_thread, daemon=True).start()

    def _on_path_detected(self, path: Optional[str]):
        """Handle detected game path."""
        if path:
            self.game_path = path
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)
            self.path_status.configure(text="Game found!", text_color="green")
            self.log(f"[OK] Game found: {path}")
            self._load_mods()
        else:
            self.path_status.configure(
                text="Game not found. Please browse to select.",
                text_color="orange"
            )
            self.log("[WARN] Could not detect game path automatically")

    def _browse_path(self):
        """Open folder browser dialog."""
        from tkinter import filedialog

        path = filedialog.askdirectory(
            title="Select Satisfactory Installation Folder",
            initialdir="C:\\Program Files (x86)\\Steam\\steamapps\\common"
        )

        if path:
            # Validate path
            factory_game = os.path.join(path, "FactoryGame")
            if os.path.isdir(factory_game):
                self.game_path = path
                self.path_entry.delete(0, "end")
                self.path_entry.insert(0, path)
                self.path_status.configure(text="Valid game path!", text_color="green")
                self.log(f"[OK] Game path set: {path}")
                self._load_mods()
            else:
                self.path_status.configure(
                    text="Invalid path - FactoryGame folder not found",
                    text_color="red"
                )
                self.log("[ERROR] Invalid path selected")

    def _load_mods(self):
        """Load mod list and create checkboxes."""
        if not self.game_path:
            return

        # Clear existing checkboxes
        for widget in self.mod_list_frame.winfo_children():
            widget.destroy()
        self.mod_checkboxes.clear()
        self.mod_vars.clear()

        # Initialize mod manager
        self.mod_manager = ModManager(self.game_path)

        # If no mods loaded from config, use embedded config
        if not self.mod_manager.mods:
            self.log("[INFO] Using embedded mod configuration")
            for mod_data in get_embedded_mods_config():
                mod = Mod(
                    name=mod_data["name"],
                    mod_reference=mod_data["mod_reference"],
                    category=mod_data.get("category", "other"),
                    required=mod_data.get("required", False),
                    priority=mod_data.get("priority", 99),
                    description=mod_data.get("description", "")
                )
                self.mod_manager.mods.append(mod)

        # Get mods by category
        categories = self.mod_manager.get_mods_by_category()

        row = 0
        for category in self.CATEGORY_ORDER:
            if category not in categories:
                continue

            mods = categories[category]
            category_name = self.CATEGORY_NAMES.get(category, category.title())

            # Category header
            header = ctk.CTkLabel(
                self.mod_list_frame,
                text=category_name,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            header.grid(row=row, column=0, sticky="w", padx=10, pady=(15, 5))
            row += 1

            # Mod checkboxes
            for mod in mods:
                var = ctk.BooleanVar(value=mod.required)
                self.mod_vars[mod.mod_reference] = var

                # Create checkbox with description
                checkbox_text = f"{mod.name}"
                if mod.required:
                    checkbox_text += " (Required)"

                checkbox = ctk.CTkCheckBox(
                    self.mod_list_frame,
                    text=checkbox_text,
                    variable=var,
                    onvalue=True,
                    offvalue=False
                )
                checkbox.grid(row=row, column=0, sticky="w", padx=30, pady=2)
                self.mod_checkboxes[mod.mod_reference] = checkbox

                # Disable required mods
                if mod.required:
                    checkbox.configure(state="disabled")

                row += 1

                # Description
                if mod.description:
                    desc_label = ctk.CTkLabel(
                        self.mod_list_frame,
                        text=f"    {mod.description}",
                        text_color="gray",
                        font=ctk.CTkFont(size=11)
                    )
                    desc_label.grid(row=row, column=0, sticky="w", padx=50, pady=(0, 5))
                    row += 1

        self.log(f"[OK] Loaded {len(self.mod_manager.mods)} mods")

    def _select_all(self):
        """Select all mods."""
        for ref, var in self.mod_vars.items():
            var.set(True)

    def _deselect_all(self):
        """Deselect all optional mods (keep required)."""
        for mod in self.mod_manager.mods:
            if not mod.required:
                self.mod_vars[mod.mod_reference].set(False)

    def _select_required(self):
        """Select only required mods."""
        for mod in self.mod_manager.mods:
            self.mod_vars[mod.mod_reference].set(mod.required)

    def _start_installation(self):
        """Start mod installation process."""
        if self.is_installing:
            return

        if not self.game_path or not self.mod_manager:
            self.log("[ERROR] Please select a valid game path first")
            return

        # Get selected mods
        selected_mods = [
            mod for mod in self.mod_manager.mods
            if self.mod_vars.get(mod.mod_reference, ctk.BooleanVar()).get()
        ]

        if not selected_mods:
            self.log("[WARN] No mods selected")
            return

        self.is_installing = True
        self.install_btn.configure(state="disabled", text="Installing...")
        self.verify_btn.configure(state="disabled")

        self.log("")
        self.log("=" * 40)
        self.log(f"Starting installation of {len(selected_mods)} mods...")
        self.log("=" * 40)

        # Create backup first
        try:
            backup_path = self.mod_manager.backup_mods()
            if backup_path:
                self.log(f"[OK] Backup created: {backup_path}")
        except Exception as e:
            self.log(f"[WARN] Backup failed: {e}")

        # Start installation thread
        def install_thread():
            success_count = 0
            fail_count = 0
            skip_count = 0

            total = len(selected_mods)
            for i, mod in enumerate(selected_mods):
                progress = i / total
                self.after(0, lambda p=progress, m=mod.name: self._update_progress(p, f"Fetching {m}..."))

                # Fetch mod info
                has_windows = self.mod_manager.fetch_mod_info(mod)

                if not has_windows:
                    self.after(0, lambda m=mod.name: self.log(f"[SKIP] {m} - No Windows version"))
                    skip_count += 1
                    continue

                self.after(0, lambda m=mod.name, v=mod.version: self.log(f"[....] Downloading {m} v{v}..."))

                # Download and install
                def progress_callback(downloaded, total_bytes):
                    if total_bytes > 0:
                        pct = downloaded / total_bytes
                        self.after(0, lambda p=progress + (pct / total): self._update_progress(
                            p, f"Downloading... {downloaded // 1024}KB / {total_bytes // 1024}KB"
                        ))

                result = self.mod_manager.install_mod(mod, progress_callback)

                if result.success:
                    self.after(0, lambda m=mod.name, r=result: self.log(
                        f"[OK] {m} v{r.version} - {r.message}"
                    ))
                    success_count += 1
                else:
                    self.after(0, lambda m=mod.name, r=result: self.log(
                        f"[FAIL] {m} - {r.message}"
                    ))
                    fail_count += 1

            # Complete
            self.after(0, lambda: self._on_installation_complete(success_count, fail_count, skip_count))

        threading.Thread(target=install_thread, daemon=True).start()

    def _update_progress(self, value: float, status: str):
        """Update progress bar and status label."""
        self.progress_bar.set(value)
        self.status_label.configure(text=status)

    def _on_installation_complete(self, success: int, failed: int, skipped: int):
        """Handle installation completion."""
        self.is_installing = False
        self.install_btn.configure(state="normal", text="Install Selected Mods")
        self.verify_btn.configure(state="normal")
        self.progress_bar.set(1)

        self.log("")
        self.log("=" * 40)
        self.log("Installation Complete!")
        self.log(f"  Successful: {success}")
        self.log(f"  Skipped: {skipped} (no Windows version)")
        self.log(f"  Failed: {failed}")
        self.log("=" * 40)

        if success > 0:
            self.status_label.configure(text="Installation complete! Launch Satisfactory to play.")
            self.log("")
            self.log("Next steps:")
            self.log("  1. Launch Satisfactory from Steam/Epic")
            self.log("  2. Look for 'MODS' button in main menu")
            self.log("  3. Connect to the modded server")
        else:
            self.status_label.configure(text="Installation failed. Check log for details.")

    def _verify_installation(self):
        """Verify installed mods."""
        if not self.mod_manager:
            self.log("[ERROR] Please select a valid game path first")
            return

        self.log("")
        self.log("=" * 40)
        self.log("Verifying Installation...")
        self.log("=" * 40)

        results = self.mod_manager.verify_all()

        valid_count = 0
        invalid_count = 0
        missing_count = 0

        for ref, result in results.items():
            mod = next((m for m in self.mod_manager.mods if m.mod_reference == ref), None)
            name = mod.name if mod else ref

            if not result["installed"]:
                if self.mod_vars.get(ref, ctk.BooleanVar()).get():
                    self.log(f"[!!] {name} - Not installed")
                    missing_count += 1
            elif not result["valid"]:
                self.log(f"[!!] {name} - Invalid ({result['message']})")
                invalid_count += 1
            else:
                pak_count = result.get("pak_count", 0)
                dll_count = result.get("dll_count", 0)
                self.log(f"[OK] {name} - {pak_count} pak, {dll_count} dll")
                valid_count += 1

        self.log("")
        self.log(f"Valid: {valid_count}, Invalid: {invalid_count}, Missing: {missing_count}")

        # Check SML specifically
        sml_result = results.get("SML", {})
        if sml_result.get("valid"):
            self.log("[OK] SML (Mod Loader) is properly installed")
        else:
            self.log("[ERROR] SML is NOT properly installed - mods will NOT work!")

    def log(self, message: str):
        """Add message to log output."""
        self.log_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        if message.strip():
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
        else:
            self.log_text.insert("end", "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


def main():
    """Application entry point."""
    app = ModInstallerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
