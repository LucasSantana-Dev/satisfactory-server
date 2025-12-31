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
from typing import Dict, List, Optional, Callable

import customtkinter as ctk

# Import core logic - handle both packaged and development scenarios
try:
    from mod_installer_core import (
        GamePathDetector, ModManager, Mod, InstallResult,
        FicsitAPIClient, FicsitCLI, get_embedded_mods_config,
        PreVerifyInstaller, DependencyResolver, ModScanner,
        VersionCache, UpdateChecker, ModVersion, UpdateInfo
    )
except ImportError:
    # When running as packaged exe, might need different import
    from .mod_installer_core import (
        GamePathDetector, ModManager, Mod, InstallResult,
        FicsitAPIClient, FicsitCLI, get_embedded_mods_config,
        PreVerifyInstaller, DependencyResolver, ModScanner,
        VersionCache, UpdateChecker, ModVersion, UpdateInfo
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

        self.title("Satisfactory Mod Installer v2.0")
        self.geometry("850x900")
        self.minsize(750, 700)

        # State
        self.game_path: Optional[str] = None
        self.mod_manager: Optional[ModManager] = None
        self.pre_verify_installer: Optional[PreVerifyInstaller] = None
        self.mod_checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.mod_vars: Dict[str, ctk.BooleanVar] = {}
        self.is_installing = False
        self.install_queue = queue.Queue()

        # Version selection state
        self.mod_version_vars: Dict[str, ctk.StringVar] = {}
        self.mod_version_dropdowns: Dict[str, ctk.CTkComboBox] = {}
        self.mod_available_versions: Dict[str, List[str]] = {}

        # Update checking state
        self.api_client: Optional[FicsitAPIClient] = None
        self.version_cache: Optional[VersionCache] = None
        self.update_checker: Optional[UpdateChecker] = None
        self.pending_updates: List[UpdateInfo] = []
        self.update_checkboxes: Dict[str, ctk.BooleanVar] = {}

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

        # Updates panel (collapsible)
        self._create_updates_panel()

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

        # Fetch versions button
        self.fetch_versions_btn = ctk.CTkButton(
            btn_frame,
            text="Load Versions",
            width=100,
            fg_color="gray40",
            command=self._fetch_all_versions
        )
        self.fetch_versions_btn.pack(side="left", padx=5)

        # Scrollable frame for mods
        self.mod_list_frame = ctk.CTkScrollableFrame(
            list_container,
            label_text="Available Mods"
        )
        self.mod_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        # Configure columns: 0=checkbox (expand), 1=version dropdown (fixed)
        self.mod_list_frame.grid_columnconfigure(0, weight=1)
        self.mod_list_frame.grid_columnconfigure(1, weight=0, minsize=120)

    def _create_updates_panel(self):
        """Create collapsible updates panel."""
        # Updates container (initially hidden)
        self.updates_frame = ctk.CTkFrame(self)
        self.updates_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=5)
        self.updates_frame.grid_columnconfigure(0, weight=1)
        self.updates_frame.grid_remove()  # Hidden by default

        # Header with count
        header_frame = ctk.CTkFrame(self.updates_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        header_frame.grid_columnconfigure(0, weight=1)

        self.updates_header = ctk.CTkLabel(
            header_frame,
            text="Updates Available",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4da6ff"
        )
        self.updates_header.grid(row=0, column=0, sticky="w")

        # Select all updates checkbox
        self.select_all_updates_var = ctk.BooleanVar(value=False)
        self.select_all_updates_cb = ctk.CTkCheckBox(
            header_frame,
            text="Select All",
            variable=self.select_all_updates_var,
            command=self._toggle_all_updates
        )
        self.select_all_updates_cb.grid(row=0, column=1, padx=10)

        # Update Selected button
        self.update_selected_btn = ctk.CTkButton(
            header_frame,
            text="Update Selected",
            width=120,
            fg_color="#2d5a27",
            hover_color="#3d7a37",
            command=self._update_selected_mods
        )
        self.update_selected_btn.grid(row=0, column=2, padx=5)

        # Close button
        close_btn = ctk.CTkButton(
            header_frame,
            text="X",
            width=30,
            fg_color="gray40",
            command=self._hide_updates_panel
        )
        close_btn.grid(row=0, column=3, padx=5)

        # Scrollable list of updates
        self.updates_list_frame = ctk.CTkScrollableFrame(
            self.updates_frame,
            height=150
        )
        self.updates_list_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.updates_list_frame.grid_columnconfigure(0, weight=0)  # Checkbox
        self.updates_list_frame.grid_columnconfigure(1, weight=1)  # Mod name
        self.updates_list_frame.grid_columnconfigure(2, weight=0)  # Version info
        self.updates_list_frame.grid_columnconfigure(3, weight=0)  # Update button

    def _create_progress_section(self):
        """Create progress bar and status section."""
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
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
        log_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=10)
        log_frame.grid_columnconfigure(0, weight=1)

        # Log textbox
        self.log_text = ctk.CTkTextbox(log_frame, height=120)
        self.log_text.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.log_text.configure(state="disabled")

    def _create_action_buttons(self):
        """Create main action buttons."""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=6, column=0, sticky="ew", padx=20, pady=(10, 20))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)

        # Install button
        self.install_btn = ctk.CTkButton(
            btn_frame,
            text="Install Selected Mods",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._start_installation
        )
        self.install_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Check Updates button
        self.check_updates_btn = ctk.CTkButton(
            btn_frame,
            text="Check Updates",
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#2d5a27",
            hover_color="#3d7a37",
            command=self._check_for_updates
        )
        self.check_updates_btn.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Verify button
        self.verify_btn = ctk.CTkButton(
            btn_frame,
            text="Verify Installation",
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="gray40",
            command=self._verify_installation
        )
        self.verify_btn.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

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
        """Load mod list and create checkboxes with version dropdowns."""
        if not self.game_path:
            return

        # Clear existing widgets
        for widget in self.mod_list_frame.winfo_children():
            widget.destroy()
        self.mod_checkboxes.clear()
        self.mod_vars.clear()
        self.mod_version_vars.clear()
        self.mod_version_dropdowns.clear()
        self.mod_available_versions.clear()

        # Initialize mod manager and helpers
        self.mod_manager = ModManager(self.game_path)
        self.api_client = FicsitAPIClient()
        self.version_cache = VersionCache()
        mods_dir = Path(self.game_path) / "FactoryGame" / "Mods"
        self.update_checker = UpdateChecker(mods_dir, self.api_client, self.version_cache)

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

            # Category header (spans both columns)
            header = ctk.CTkLabel(
                self.mod_list_frame,
                text=category_name,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            header.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5))
            row += 1

            # Mod rows
            for mod in mods:
                # Mod row frame for checkbox + dropdown
                mod_row_frame = ctk.CTkFrame(self.mod_list_frame, fg_color="transparent")
                mod_row_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=2)
                mod_row_frame.grid_columnconfigure(0, weight=1)
                mod_row_frame.grid_columnconfigure(1, weight=0)

                # Checkbox
                var = ctk.BooleanVar(value=mod.required)
                self.mod_vars[mod.mod_reference] = var

                checkbox_text = f"{mod.name}"
                if mod.required:
                    checkbox_text += " (Required)"

                checkbox = ctk.CTkCheckBox(
                    mod_row_frame,
                    text=checkbox_text,
                    variable=var,
                    onvalue=True,
                    offvalue=False
                )
                checkbox.grid(row=0, column=0, sticky="w", padx=20)
                self.mod_checkboxes[mod.mod_reference] = checkbox

                if mod.required:
                    checkbox.configure(state="disabled")

                # Version dropdown (defaults to "Latest")
                version_var = ctk.StringVar(value="Latest")
                self.mod_version_vars[mod.mod_reference] = version_var
                self.mod_available_versions[mod.mod_reference] = ["Latest"]

                version_dropdown = ctk.CTkComboBox(
                    mod_row_frame,
                    variable=version_var,
                    values=["Latest"],
                    width=100,
                    state="readonly"
                )
                version_dropdown.grid(row=0, column=1, sticky="e", padx=5)
                self.mod_version_dropdowns[mod.mod_reference] = version_dropdown

                row += 1

                # Description
                if mod.description:
                    desc_label = ctk.CTkLabel(
                        self.mod_list_frame,
                        text=f"    {mod.description}",
                        text_color="gray",
                        font=ctk.CTkFont(size=11)
                    )
                    desc_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=50, pady=(0, 5))
                    row += 1

        self.log(f"[OK] Loaded {len(self.mod_manager.mods)} mods")
        self.log("[INFO] Click 'Load Versions' to fetch available versions")

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

    def _fetch_all_versions(self):
        """Fetch available versions for all mods from the API."""
        if not self.mod_manager:
            self.log("[ERROR] No mods loaded")
            return

        self.fetch_versions_btn.configure(state="disabled", text="Loading...")
        self.log("")
        self.log("Fetching available versions...")

        def fetch_thread():
            try:
                total = len(self.mod_manager.mods)
                for i, mod in enumerate(self.mod_manager.mods):
                    # Update status
                    self.after(0, lambda m=mod, idx=i: self.status_label.configure(
                        text=f"Fetching versions: {m.name} ({idx+1}/{total})"
                    ))

                    # Fetch versions using cache
                    versions = self.version_cache.get_or_fetch(
                        mod.mod_reference,
                        self.api_client,
                        limit=15
                    )

                    if versions:
                        # Build version list with "Latest" as first option
                        version_strings = ["Latest"] + [v.version for v in versions if v.has_windows_target]
                        self.mod_available_versions[mod.mod_reference] = version_strings

                        # Update dropdown on main thread
                        self.after(0, lambda ref=mod.mod_reference, vals=version_strings:
                            self._update_version_dropdown(ref, vals)
                        )

                self.after(0, self._on_versions_fetched)

            except Exception as e:
                self.after(0, lambda err=str(e): self.log(f"[ERROR] Failed to fetch versions: {err}"))
                self.after(0, lambda: self.fetch_versions_btn.configure(state="normal", text="Load Versions"))

        threading.Thread(target=fetch_thread, daemon=True).start()

    def _update_version_dropdown(self, mod_ref: str, versions: List[str]):
        """Update a version dropdown with new values."""
        if mod_ref in self.mod_version_dropdowns:
            dropdown = self.mod_version_dropdowns[mod_ref]
            dropdown.configure(values=versions)
            # Keep "Latest" selected unless user changed it
            if self.mod_version_vars[mod_ref].get() == "Latest" or \
               self.mod_version_vars[mod_ref].get() not in versions:
                self.mod_version_vars[mod_ref].set("Latest")

    def _on_versions_fetched(self):
        """Called when version fetching is complete."""
        self.fetch_versions_btn.configure(state="normal", text="Load Versions")
        self.status_label.configure(text="Ready - Versions loaded")
        self.log("[OK] All versions loaded. You can now select specific versions from dropdowns.")

    def _check_for_updates(self):
        """Check for available updates for installed mods."""
        if not self.game_path or not self.mod_manager:
            self.log("[ERROR] Please select a valid game path first")
            return

        self.check_updates_btn.configure(state="disabled", text="Checking...")
        self.log("")
        self.log("=" * 50)
        self.log("CHECKING FOR UPDATES")
        self.log("=" * 50)

        def check_thread():
            try:
                # Get all mod references and names
                mod_refs = [mod.mod_reference for mod in self.mod_manager.mods]
                mod_names = {mod.mod_reference: mod.name for mod in self.mod_manager.mods}

                def progress_cb(mod_ref, status):
                    self.after(0, lambda s=status: self.status_label.configure(text=s))

                # Check for updates
                updates = self.update_checker.check_for_updates(
                    mod_refs,
                    mod_names,
                    progress_cb
                )

                # Filter to only outdated mods
                outdated = [u for u in updates if u.needs_update]
                self.pending_updates = outdated

                self.after(0, lambda: self._on_updates_checked(updates, outdated))

            except Exception as e:
                self.after(0, lambda err=str(e): self.log(f"[ERROR] Update check failed: {err}"))
                self.after(0, lambda: self.check_updates_btn.configure(state="normal", text="Check Updates"))

        threading.Thread(target=check_thread, daemon=True).start()

    def _on_updates_checked(self, all_updates: List[UpdateInfo], outdated: List[UpdateInfo]):
        """Called when update checking is complete."""
        self.check_updates_btn.configure(state="normal", text="Check Updates")

        # Log results
        installed_count = sum(1 for u in all_updates if u.installed_version)
        not_installed = sum(1 for u in all_updates if not u.installed_version)

        self.log(f"Checked {len(all_updates)} mods")
        self.log(f"  Installed: {installed_count}")
        self.log(f"  Not installed: {not_installed}")
        self.log(f"  Updates available: {len(outdated)}")

        if outdated:
            self.log("")
            self.log("Mods with updates available:")
            for u in outdated:
                self.log(f"  {u.mod_name}: {u.installed_version} -> {u.latest_version}")

            # Show updates panel
            self._show_updates_panel(outdated)
            self.status_label.configure(text=f"{len(outdated)} updates available")
        else:
            self.log("")
            self.log("[OK] All installed mods are up to date!")
            self.status_label.configure(text="All mods up to date")
            self._hide_updates_panel()

    def _show_updates_panel(self, updates: List[UpdateInfo]):
        """Display the updates panel with outdated mods."""
        # Clear existing items
        for widget in self.updates_list_frame.winfo_children():
            widget.destroy()
        self.update_checkboxes.clear()

        # Update header
        self.updates_header.configure(text=f"Updates Available ({len(updates)})")

        # Add update rows
        for i, update in enumerate(updates):
            # Checkbox for selection
            var = ctk.BooleanVar(value=True)
            self.update_checkboxes[update.mod_reference] = var

            cb = ctk.CTkCheckBox(
                self.updates_list_frame,
                text="",
                variable=var,
                width=20
            )
            cb.grid(row=i, column=0, padx=5, pady=3)

            # Mod name
            name_label = ctk.CTkLabel(
                self.updates_list_frame,
                text=update.mod_name,
                anchor="w"
            )
            name_label.grid(row=i, column=1, sticky="w", padx=5, pady=3)

            # Version info
            version_text = f"{update.installed_version or '?'} → {update.latest_version}"
            version_label = ctk.CTkLabel(
                self.updates_list_frame,
                text=version_text,
                text_color="#4da6ff",
                font=ctk.CTkFont(size=11)
            )
            version_label.grid(row=i, column=2, padx=10, pady=3)

            # Individual update button
            update_btn = ctk.CTkButton(
                self.updates_list_frame,
                text="Update",
                width=70,
                height=25,
                font=ctk.CTkFont(size=11),
                fg_color="#2d5a27",
                hover_color="#3d7a37",
                command=lambda ref=update.mod_reference: self._update_single_mod(ref)
            )
            update_btn.grid(row=i, column=3, padx=5, pady=3)

        # Show the panel
        self.updates_frame.grid()
        self.select_all_updates_var.set(True)

    def _hide_updates_panel(self):
        """Hide the updates panel."""
        self.updates_frame.grid_remove()

    def _toggle_all_updates(self):
        """Toggle all update checkboxes."""
        select_all = self.select_all_updates_var.get()
        for var in self.update_checkboxes.values():
            var.set(select_all)

    def _update_single_mod(self, mod_ref: str):
        """Update a single mod to its latest version."""
        self._update_mods([mod_ref])

    def _update_selected_mods(self):
        """Update all selected mods from the updates panel."""
        selected = [
            ref for ref, var in self.update_checkboxes.items()
            if var.get()
        ]

        if not selected:
            self.log("[WARN] No mods selected for update")
            return

        self._update_mods(selected)

    def _update_mods(self, mod_refs: List[str]):
        """Update specified mods to their latest versions."""
        if self.is_installing:
            return

        self.is_installing = True
        self.install_btn.configure(state="disabled")
        self.check_updates_btn.configure(state="disabled")
        self.update_selected_btn.configure(state="disabled", text="Updating...")

        self.log("")
        self.log("=" * 50)
        self.log("UPDATING MODS")
        self.log("=" * 50)
        self.log(f"Updating {len(mod_refs)} mod(s)...")

        def update_thread():
            try:
                # Initialize installer
                installer = PreVerifyInstaller(self.game_path)

                success_count = 0
                fail_count = 0

                for i, mod_ref in enumerate(mod_refs):
                    self.after(0, lambda m=mod_ref, idx=i: self.log(f"  Updating {m} ({idx+1}/{len(mod_refs)})..."))
                    self.after(0, lambda m=mod_ref: self.status_label.configure(text=f"Updating {m}..."))

                    # Get latest version info
                    versions = self.version_cache.get_or_fetch(mod_ref, self.api_client)
                    if not versions:
                        self.after(0, lambda m=mod_ref: self.log(f"    [FAIL] {m}: No versions found"))
                        fail_count += 1
                        continue

                    latest = versions[0]
                    if not latest.download_url:
                        self.after(0, lambda m=mod_ref: self.log(f"    [FAIL] {m}: No download URL"))
                        fail_count += 1
                        continue

                    # Download and install
                    result = installer.downloader.download_and_install(
                        mod_ref,
                        latest.download_url
                    )

                    if result.success:
                        self.after(0, lambda m=mod_ref, v=latest.version:
                            self.log(f"    [OK] {m} updated to v{v}")
                        )
                        success_count += 1
                        # Invalidate cache for this mod
                        self.version_cache.invalidate(mod_ref)
                    else:
                        self.after(0, lambda m=mod_ref, msg=result.message:
                            self.log(f"    [FAIL] {m}: {msg}")
                        )
                        fail_count += 1

                self.after(0, lambda s=success_count, f=fail_count:
                    self._on_update_complete(s, f)
                )

            except Exception as e:
                self.after(0, lambda err=str(e): self.log(f"[ERROR] Update failed: {err}"))
                self.after(0, self._on_update_complete_error)

        threading.Thread(target=update_thread, daemon=True).start()

    def _on_update_complete(self, success_count: int, fail_count: int):
        """Called when mod update is complete."""
        self.is_installing = False
        self.install_btn.configure(state="normal")
        self.check_updates_btn.configure(state="normal")
        self.update_selected_btn.configure(state="normal", text="Update Selected")

        self.log("")
        self.log("=" * 50)
        if fail_count == 0:
            self.log(f"UPDATE COMPLETE - {success_count} mod(s) updated successfully!")
            self.status_label.configure(text="Update complete!")
        else:
            self.log(f"UPDATE FINISHED - {success_count} succeeded, {fail_count} failed")
            self.status_label.configure(text=f"Update finished with {fail_count} failure(s)")

        # Hide updates panel and re-check
        self._hide_updates_panel()

    def _on_update_complete_error(self):
        """Called when update fails with an error."""
        self.is_installing = False
        self.install_btn.configure(state="normal")
        self.check_updates_btn.configure(state="normal")
        self.update_selected_btn.configure(state="normal", text="Update Selected")
        self.status_label.configure(text="Update failed")

    def _start_installation(self):
        """Start mod installation process using pre-verify workflow."""
        if self.is_installing:
            return

        if not self.game_path or not self.mod_manager:
            self.log("[ERROR] Please select a valid game path first")
            return

        # Get selected mods (just the references)
        selected_refs = [
            mod.mod_reference for mod in self.mod_manager.mods
            if self.mod_vars.get(mod.mod_reference, ctk.BooleanVar()).get()
        ]

        if not selected_refs:
            self.log("[WARN] No mods selected")
            return

        self.is_installing = True
        self.install_btn.configure(state="disabled", text="Installing...")
        self.verify_btn.configure(state="disabled")

        self.log("")
        self.log("=" * 50)
        self.log("PRE-VERIFY INSTALLATION")
        self.log("=" * 50)
        self.log(f"Selected {len(selected_refs)} mods")
        self.log("")

        # Create backup first
        try:
            backup_path = self.mod_manager.backup_mods()
            if backup_path:
                self.log(f"[OK] Backup created: {backup_path}")
        except Exception as e:
            self.log(f"[WARN] Backup failed: {e}")

        # Initialize pre-verify installer
        self.pre_verify_installer = PreVerifyInstaller(self.game_path)

        # Run installation in background thread
        threading.Thread(
            target=self._run_preverify_installation,
            args=(selected_refs,),
            daemon=True
        ).start()

    def _run_preverify_installation(self, selected_refs: List[str]):
        """Run the pre-verify installation workflow in background."""
        phase_count = 6  # Now includes cleanup phase
        current_phase = 0

        def progress_callback(mod_ref: str, status: str):
            # Update progress and log
            self.after(0, lambda s=status: self.log(f"  {s}"))
            # Update progress bar based on phase
            progress = (current_phase / phase_count) + (0.1 / phase_count)
            self.after(0, lambda p=progress, s=status: self._update_progress(p, s))

        def download_progress_callback(downloaded: int, total: int):
            if total > 0:
                pct = downloaded / total
                status = f"Downloading... {downloaded // 1024}KB / {total // 1024}KB"
                # Progress within phase 4
                progress = (4 / phase_count) + (pct / phase_count)
                self.after(0, lambda p=progress, s=status: self._update_progress(p, s))

        try:
            # Phase 0: Cleanup obsolete mods
            current_phase = 0
            self.after(0, lambda: self.log(""))
            self.after(0, lambda: self.log("[PHASE 0] Cleanup Obsolete Mods"))
            self.after(0, lambda: self.log("-" * 40))
            self.after(0, lambda: self._update_progress(0.05, "Cleaning up obsolete mods..."))

            # Get all valid mod refs from our config
            valid_refs = [mod.mod_reference for mod in (self.mod_manager.mods if self.mod_manager else [])]
            removed, failed = self.pre_verify_installer.cleanup_obsolete_mods(
                valid_refs, progress_callback
            )

            if removed:
                self.after(0, lambda: self.log(f"  Removed {len(removed)} obsolete mod(s):"))
                for ref in removed:
                    self.after(0, lambda r=ref: self.log(f"    - {r}"))
            else:
                self.after(0, lambda: self.log("  No obsolete mods to remove"))

            if failed:
                self.after(0, lambda: self.log(f"  [WARN] Failed to remove {len(failed)} mod(s)"))

            # Phase 1: Resolve dependencies
            current_phase = 1
            self.after(0, lambda: self.log(""))
            self.after(0, lambda: self.log("[PHASE 1] Resolving Dependencies"))
            self.after(0, lambda: self.log("-" * 40))
            self.after(0, lambda: self._update_progress(0.15, "Resolving dependencies..."))

            result = self.pre_verify_installer.phase1_resolve_dependencies(
                selected_refs, progress_callback
            )
            self._log_phase_result(result)

            if not result.success:
                self.after(0, lambda: self._on_preverify_complete(False, "Dependency resolution failed"))
                return

            # Phase 2: Scan installed mods
            current_phase = 2
            self.after(0, lambda: self.log(""))
            self.after(0, lambda: self.log("[PHASE 2] Scanning Installed Mods"))
            self.after(0, lambda: self.log("-" * 40))
            self.after(0, lambda: self._update_progress(0.35, "Scanning installed mods..."))

            result = self.pre_verify_installer.phase2_scan_installed(progress_callback)
            self._log_phase_result(result)

            # Phase 3: Gap analysis
            current_phase = 3
            self.after(0, lambda: self.log(""))
            self.after(0, lambda: self.log("[PHASE 3] Gap Analysis"))
            self.after(0, lambda: self.log("-" * 40))
            self.after(0, lambda: self._update_progress(0.5, "Analyzing gaps..."))

            result = self.pre_verify_installer.phase3_gap_analysis(progress_callback)
            self._log_phase_result(result)

            gap = self.pre_verify_installer.gap_analysis
            if gap and gap.all_ok:
                self.after(0, lambda: self.log(""))
                self.after(0, lambda: self.log("[OK] All mods already installed and valid!"))
                self.after(0, lambda: self._on_preverify_complete(True, "All mods already installed"))
                return

            # Phase 4: Install missing mods
            current_phase = 4
            self.after(0, lambda: self.log(""))
            self.after(0, lambda: self.log("[PHASE 4] Installing Missing Mods"))
            self.after(0, lambda: self.log("-" * 40))
            self.after(0, lambda: self._update_progress(0.6, "Installing missing mods..."))

            result = self.pre_verify_installer.phase4_install_missing(
                progress_callback, download_progress_callback
            )
            self._log_phase_result(result)

            # Phase 5: Final verification
            current_phase = 5
            self.after(0, lambda: self.log(""))
            self.after(0, lambda: self.log("[PHASE 5] Final Verification"))
            self.after(0, lambda: self.log("-" * 40))
            self.after(0, lambda: self._update_progress(0.85, "Verifying installation..."))

            result = self.pre_verify_installer.phase5_final_verify(progress_callback)
            self._log_phase_result(result)

            # Complete
            self.after(0, lambda r=result: self._on_preverify_complete(
                r.success, r.message
            ))

        except Exception as e:
            import traceback
            error_msg = f"Installation error: {str(e)}"
            self.after(0, lambda e=error_msg: self.log(f"[ERROR] {e}"))
            self.after(0, lambda: self.log(traceback.format_exc()))
            self.after(0, lambda: self._on_preverify_complete(False, error_msg))

    def _log_phase_result(self, result):
        """Log details from a phase result."""
        for detail in result.details:
            self.after(0, lambda d=detail: self.log(f"  {d}"))
        self.after(0, lambda r=result: self.log(f"  >> {r.message}"))

    def _update_progress(self, value: float, status: str):
        """Update progress bar and status label."""
        self.progress_bar.set(min(value, 1.0))
        self.status_label.configure(text=status)

    def _on_preverify_complete(self, success: bool, message: str):
        """Handle pre-verify installation completion."""
        self.is_installing = False
        self.install_btn.configure(state="normal", text="Install Selected Mods")
        self.verify_btn.configure(state="normal")
        self.progress_bar.set(1)

        self.log("")
        self.log("=" * 50)

        if success:
            self.log("INSTALLATION SUCCESSFUL!")
            self.log("=" * 50)
            self.status_label.configure(text="Installation complete! Launch Satisfactory to play.")

            # Show summary
            if self.pre_verify_installer and self.pre_verify_installer.gap_analysis:
                gap = self.pre_verify_installer.gap_analysis
                self.log(f"  Total mods required: {len(gap.needed_mods)}")
                self.log(f"  Already installed: {len(gap.valid_mods)}")
                self.log(f"  Newly installed: {len(gap.mods_to_install)}")

            self.log("")
            self.log("Next steps:")
            self.log("  1. Launch Satisfactory from Steam/Epic")
            self.log("  2. The game should detect mods automatically")
            self.log("  3. Look for 'MODS' button in main menu")
            self.log("  4. Connect to the modded server")
        else:
            self.log("INSTALLATION FAILED!")
            self.log("=" * 50)
            self.log(f"  Reason: {message}")
            self.status_label.configure(text="Installation failed. Check log for details.")

            # Show what's still missing
            if self.pre_verify_installer:
                scanner = ModScanner(self.pre_verify_installer.mods_dir)
                missing = scanner.get_missing_mods(
                    list(self.pre_verify_installer.resolved_mods.keys())
                )
                if missing:
                    self.log("")
                    self.log("Still missing mods:")
                    for ref in missing:
                        self.log(f"  - {ref}")

            self.log("")
            self.log("Try:")
            self.log("  1. Check your internet connection")
            self.log("  2. Try running the installer again")
            self.log("  3. Check if mods are available on ficsit.app")

    def _verify_installation(self):
        """Verify installed mods using the ModScanner."""
        if not self.game_path:
            self.log("[ERROR] Please select a valid game path first")
            return

        self.log("")
        self.log("=" * 50)
        self.log("VERIFICATION")
        self.log("=" * 50)

        # Get selected mod references
        selected_refs = [
            mod.mod_reference for mod in (self.mod_manager.mods if self.mod_manager else [])
            if self.mod_vars.get(mod.mod_reference, ctk.BooleanVar()).get()
        ]

        if not selected_refs:
            self.log("[WARN] No mods selected to verify")
            return

        # Use ModScanner to check installed mods
        mods_dir = Path(self.game_path) / "FactoryGame" / "Mods"
        scanner = ModScanner(mods_dir)

        self.log("")
        self.log("Scanning mods directory...")
        installed = scanner.scan_installed()

        self.log(f"Found {len(installed)} installed mod folders")
        self.log("")

        valid_count = 0
        invalid_count = 0
        missing_count = 0

        # First check all selected mods
        self.log("Selected mods status:")
        for ref in selected_refs:
            mod = next((m for m in self.mod_manager.mods if m.mod_reference == ref), None) if self.mod_manager else None
            name = mod.name if mod else ref

            if ref not in installed:
                self.log(f"  [!!] {name} - NOT INSTALLED")
                missing_count += 1
            elif not installed[ref].valid:
                status = installed[ref]
                self.log(f"  [!!] {name} - INVALID: {status.message}")
                invalid_count += 1
            else:
                status = installed[ref]
                version_str = f"v{status.version}" if status.version else ""
                self.log(f"  [OK] {name} {version_str} - {status.pak_count} pak, {status.dll_count} dll")
                valid_count += 1

        # Show additional installed mods (dependencies that may have been auto-installed)
        extra_mods = [ref for ref in installed.keys() if ref not in selected_refs]
        if extra_mods:
            self.log("")
            self.log("Additional installed mods (dependencies):")
            for ref in extra_mods:
                status = installed[ref]
                if status.valid:
                    self.log(f"  [OK] {ref} - {status.pak_count} pak")
                    valid_count += 1
                else:
                    self.log(f"  [!!] {ref} - {status.message}")
                    invalid_count += 1

        # Summary
        self.log("")
        self.log("-" * 40)
        self.log(f"Valid: {valid_count}, Invalid: {invalid_count}, Missing: {missing_count}")

        # Check SML specifically
        if "SML" in installed and installed["SML"].valid:
            self.log("[OK] SML (Mod Loader) is properly installed")
        else:
            self.log("[ERROR] SML is NOT installed - mods will NOT work!")

        # Final verdict
        self.log("")
        if missing_count == 0 and invalid_count == 0:
            self.log("VERIFICATION PASSED - All mods are correctly installed!")
            self.status_label.configure(text="Verification passed!")
        else:
            self.log("VERIFICATION FAILED - Some mods are missing or invalid")
            self.log("Run 'Install Selected Mods' to repair")
            self.status_label.configure(text="Verification failed - repair needed")

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
