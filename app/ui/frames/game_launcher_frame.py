"""
Game Launcher Frame

Provides functionality for launching and managing games.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, List, Optional, Tuple
import os
import threading
import time
from PIL import Image, ImageTk

from app.ui.base.base_frame import BaseFrame
from app.core.app_instance import get_app_instance
from app.utils.logger import LoggerWrapper

class GameLauncherFrame(BaseFrame):
    """Game launcher frame for launching and managing games."""
    
    def __init__(self, master, **kwargs):
        """Initialize the game launcher frame."""
        super().__init__(master, **kwargs)
        self.logger = LoggerWrapper(name="game_launcher_frame")
        
        # State variables
        self.games = {}
        self.running_games = {}
        self.selected_game = None
        self.sandbox_enabled = False
        self.sandbox_type = "sandboxie"
        self.mac_spoofing = False
        self.hw_spoofing = False
        
    def on_init(self):
        """Initialize the game launcher frame."""
        try:
            super().on_init()
            
            # Set up layout
            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=0)  # Header
            self.rowconfigure(1, weight=1)  # Content
            
            # Create header
            self._create_header()
            
            # Create content
            self._create_content()
            
            # Load games
            self._load_games()
            
            # Start monitoring running games
            self.after(1000, self._monitor_running_games)
            
        except Exception as e:
            self.logger.error(f"Error initializing game launcher frame: {e}", exc_info=True)
            
    def on_enter(self):
        """Called when the frame becomes visible."""
        super().on_enter()
        
        # Refresh running games
        self._refresh_running_games()
        
    def on_exit(self):
        """Called when the frame is about to be hidden."""
        super().on_exit()
        
    def refresh(self):
        """Refresh the frame's content."""
        super().refresh()
        
        # Refresh games and running games
        self._load_games()
        self._refresh_running_games()
            
    def _create_header(self):
        """Create the header section."""
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        title = ctk.CTkLabel(
            header,
            text="Game Launcher",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left", padx=20, pady=10)
        
        # Add refresh button
        refresh_button = ctk.CTkButton(
            header,
            text="Refresh",
            width=100,
            command=self.refresh
        )
        refresh_button.pack(side="right", padx=20, pady=10)
        
    def _create_content(self):
        """Create the main content."""
        content = ctk.CTkFrame(self)
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        # Create two-column layout
        content.columnconfigure(0, weight=1)  # Left column
        content.columnconfigure(1, weight=1)  # Right column
        content.rowconfigure(0, weight=1)
        
        # Create left column (game configuration)
        left_column = ctk.CTkFrame(content)
        left_column.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create sections in left column
        self._create_game_config_section(left_column)
        self._create_launch_options_section(left_column)
        self._create_sandbox_section(left_column)
        self._create_network_wrapper_section(left_column)
        
        # Create right column (running games)
        right_column = ctk.CTkFrame(content)
        right_column.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Create running games section
        self._create_running_games_section(right_column)
        
    def _create_game_config_section(self, parent):
        """Create game configuration section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", padx=10, pady=10)
        
        # Section title
        title = ctk.CTkLabel(
            section,
            text="Game Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(anchor="w", padx=10, pady=10)
        
        # Game selection
        game_frame = ctk.CTkFrame(section, fg_color="transparent")
        game_frame.pack(fill="x", padx=10, pady=5)
        
        game_label = ctk.CTkLabel(game_frame, text="Game:")
        game_label.pack(side="left", padx=5)
        
        self.game_var = tk.StringVar()
        self.game_dropdown = ctk.CTkComboBox(
            game_frame,
            variable=self.game_var,
            width=200,
            command=self._on_game_selected
        )
        self.game_dropdown.pack(side="left", padx=5)
        
        # Game path
        path_frame = ctk.CTkFrame(section, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=5)
        
        path_label = ctk.CTkLabel(path_frame, text="Path:")
        path_label.pack(side="left", padx=5)
        
        self.path_var = tk.StringVar()
        path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.path_var,
            width=200
        )
        path_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        browse_button = ctk.CTkButton(
            path_frame,
            text="Browse",
            width=80,
            command=self._browse_game_path
        )
        browse_button.pack(side="left", padx=5)
        
        # Game arguments
        args_frame = ctk.CTkFrame(section, fg_color="transparent")
        args_frame.pack(fill="x", padx=10, pady=5)
        
        args_label = ctk.CTkLabel(args_frame, text="Arguments:")
        args_label.pack(side="left", padx=5)
        
        self.args_var = tk.StringVar()
        args_entry = ctk.CTkEntry(
            args_frame,
            textvariable=self.args_var,
            width=280
        )
        args_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Save button
        save_button = ctk.CTkButton(
            section,
            text="Save Game Configuration",
            command=self._save_game_config
        )
        save_button.pack(padx=10, pady=10, fill="x")
        
    def _create_launch_options_section(self, parent):
        """Create launch options section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", padx=10, pady=10)
        
        # Section title
        title = ctk.CTkLabel(
            section,
            text="Launch Options",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(anchor="w", padx=10, pady=10)
        
        # MAC spoofing option
        mac_frame = ctk.CTkFrame(section, fg_color="transparent")
        mac_frame.pack(fill="x", padx=10, pady=5)
        
        self.mac_var = tk.BooleanVar(value=False)
        mac_checkbox = ctk.CTkCheckBox(
            mac_frame,
            text="Enable MAC Address Spoofing",
            variable=self.mac_var,
            command=self._on_mac_spoofing_toggle
        )
        mac_checkbox.pack(side="left", padx=5)
        
        # Hardware ID spoofing option
        hw_frame = ctk.CTkFrame(section, fg_color="transparent")
        hw_frame.pack(fill="x", padx=10, pady=5)
        
        self.hw_var = tk.BooleanVar(value=False)
        hw_checkbox = ctk.CTkCheckBox(
            hw_frame,
            text="Enable Hardware ID Spoofing",
            variable=self.hw_var,
            command=self._on_hw_spoofing_toggle
        )
        hw_checkbox.pack(side="left", padx=5)
        
        # Launch buttons frame
        buttons_frame = ctk.CTkFrame(section, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Launch button
        launch_button = ctk.CTkButton(
            buttons_frame,
            text="Launch Game",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._launch_game
        )
        launch_button.pack(side="left", padx=5, fill="x", expand=True)
        
        # Launch with Bot button
        launch_bot_button = ctk.CTkButton(
            buttons_frame,
            text="Launch with Bot",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#3a7ebf", "#1f538d"),  # Slightly different color
            command=self._launch_game_with_bot
        )
        launch_bot_button.pack(side="right", padx=5, fill="x", expand=True)
        
    def _create_sandbox_section(self, parent):
        """Create sandbox section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", padx=10, pady=10)
        
        # Section title
        title = ctk.CTkLabel(
            section,
            text="Sandbox Options",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(anchor="w", padx=10, pady=10)
        
        # Enable sandbox option
        sandbox_frame = ctk.CTkFrame(section, fg_color="transparent")
        sandbox_frame.pack(fill="x", padx=10, pady=5)
        
        self.sandbox_var = tk.BooleanVar(value=False)
        self.sandbox_checkbox = ctk.CTkCheckBox(
            sandbox_frame,
            text="Launch in Sandbox",
            variable=self.sandbox_var,
            command=self._on_sandbox_toggle
        )
        self.sandbox_checkbox.pack(side="left", padx=5)
        
        # Sandbox type selection
        type_frame = ctk.CTkFrame(section, fg_color="transparent")
        type_frame.pack(fill="x", padx=10, pady=5)
        
        type_label = ctk.CTkLabel(type_frame, text="Sandbox Type:")
        type_label.pack(side="left", padx=5)
        
        self.sandbox_type_var = tk.StringVar(value="built_in")
        sandbox_types = ["built_in", "sandboxie", "windows_sandbox", "virtualbox"]
        type_dropdown = ctk.CTkComboBox(
            type_frame,
            values=sandbox_types,
            variable=self.sandbox_type_var,
            width=150,
            command=self._on_sandbox_type_selected
        )
        type_dropdown.pack(side="left", padx=5)
        
        # Sandbox path (for Sandboxie)
        path_frame = ctk.CTkFrame(section, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=5)
        
        path_label = ctk.CTkLabel(path_frame, text="Sandbox Path:")
        path_label.pack(side="left", padx=5)
        
        self.sandbox_path_var = tk.StringVar(value="C:\\Program Files\\Sandboxie-Plus\\Start.exe")
        self.sandbox_path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.sandbox_path_var,
            width=200
        )
        self.sandbox_path_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.sandbox_browse_button = ctk.CTkButton(
            path_frame,
            text="Browse",
            width=80,
            command=self._browse_sandbox_path
        )
        self.sandbox_browse_button.pack(side="left", padx=5)
        
        # Initially disable path input if built-in is selected
        if self.sandbox_type_var.get() == "built_in":
            self.sandbox_path_entry.configure(state="disabled")
            self.sandbox_browse_button.configure(state="disabled")
        
        # Network isolation option
        network_frame = ctk.CTkFrame(section, fg_color="transparent")
        network_frame.pack(fill="x", padx=10, pady=5)
        
        self.network_var = tk.BooleanVar(value=True)
        network_checkbox = ctk.CTkCheckBox(
            network_frame,
            text="Enable Network Isolation",
            variable=self.network_var
        )
        network_checkbox.pack(side="left", padx=5)
        
        # Check network button
        check_button = ctk.CTkButton(
            section,
            text="Check Network Isolation",
            command=self._check_network_isolation
        )
        check_button.pack(padx=10, pady=10, fill="x")
        
    def _create_network_wrapper_section(self, parent):
        """Create network wrapper section."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=5)
        
        # Network wrapper checkbox
        self.network_wrapper_var = ctk.BooleanVar(value=False)
        network_wrapper_check = ctk.CTkCheckBox(
            frame,
            text="Use Network Wrapper",
            variable=self.network_wrapper_var,
            command=self._toggle_network_wrapper
        )
        network_wrapper_check.pack(anchor="w", padx=10, pady=5)
        
        # Network profile options (initially hidden)
        self.network_profile_frame = ctk.CTkFrame(frame, fg_color="transparent")
        
        # Profile type
        profile_label = ctk.CTkLabel(self.network_profile_frame, text="Network Profile:")
        profile_label.pack(side="left", padx=(20, 5))
        
        self.profile_type_var = ctk.StringVar(value="random")
        profile_type = ctk.CTkOptionMenu(
            self.network_profile_frame,
            values=["Random", "United States", "Europe", "Asia", "Custom"],
            variable=self.profile_type_var
        )
        profile_type.pack(side="left", padx=5)
        
        # Initially hide network profile options
        if not self.network_wrapper_var.get():
            self.network_profile_frame.pack_forget()
        else:
            self.network_profile_frame.pack(fill="x", padx=10, pady=5)
        
    def _create_running_games_section(self, parent):
        """Create running games section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Section title
        title_frame = ctk.CTkFrame(section, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            title_frame,
            text="Running Games",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(side="left", padx=10)
        
        # Terminate all button
        terminate_all_button = ctk.CTkButton(
            title_frame,
            text="Terminate All",
            width=120,
            fg_color=("red", "#F44336"),
            hover_color=("darkred", "#D32F2F"),
            command=self._terminate_all_games
        )
        terminate_all_button.pack(side="right", padx=10)
        
        # Create scrollable frame for running games
        self.running_games_frame = ctk.CTkScrollableFrame(section)
        self.running_games_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Show no games message initially
        self.no_games_label = ctk.CTkLabel(
            self.running_games_frame,
            text="No games running",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray70")
        )
        self.no_games_label.pack(pady=50)
        
    def _load_games(self):
        """Load saved games from settings."""
        try:
            app = get_app_instance()
            if not app:
                return
                
            settings_service = app.get_service("settings")
            if not settings_service:
                self.logger.warning("Settings service not available")
                return
                
            # Get games from settings
            games = settings_service.get("game.paths", {})
            self.games = games
            
            # Update dropdown
            game_names = list(games.keys())
            self.game_dropdown.configure(values=game_names)
            
            if game_names and not self.game_var.get():
                self.game_var.set(game_names[0])
                self._on_game_selected(game_names[0])
                
        except Exception as e:
            self.logger.error(f"Error loading games: {e}", exc_info=True)
            
    def _browse_game_path(self):
        """Browse for game executable."""
        try:
            from tkinter import filedialog
            
            file_path = filedialog.askopenfilename(
                title="Select Game Executable",
                filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
            )
            
            if file_path:
                self.path_var.set(file_path)
                
                # Auto-set game name if not already set
                if not self.game_var.get():
                    game_name = os.path.basename(file_path).split('.')[0]
                    self.game_var.set(game_name)
                    
        except Exception as e:
            self.logger.error(f"Error browsing for game path: {e}", exc_info=True)
            
    def _browse_sandbox_path(self):
        """Browse for sandbox executable."""
        try:
            from tkinter import filedialog
            
            file_path = filedialog.askopenfilename(
                title="Select Sandbox Executable",
                filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
            )
            
            if file_path:
                self.sandbox_path_var.set(file_path)
                
        except Exception as e:
            self.logger.error(f"Error browsing for sandbox path: {e}", exc_info=True)
            
    def _save_game_config(self):
        """Save game configuration to settings."""
        try:
            game_id = self.game_var.get()
            game_path = self.path_var.get()
            
            if not game_id or not game_path:
                self._show_error("Please enter a game name and path")
                return
                
            app = get_app_instance()
            if not app:
                return
                
            settings_service = app.get_service("settings")
            if not settings_service:
                self.logger.warning("Settings service not available")
                return
                
            # Save game path
            settings_service.set(f"game.paths.{game_id}", game_path)
            
            # Save game arguments if provided
            if self.args_var.get():
                settings_service.set(f"game.args.{game_id}", self.args_var.get())
                
            # Reload games
            self._load_games()
            
            # Show success message
            self._show_info(f"Game '{game_id}' saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving game config: {e}", exc_info=True)
            self._show_error(f"Error saving game config: {str(e)}")
            
    def _on_game_selected(self, game_id):
        """Handle game selection."""
        try:
            if not game_id:
                return
                
            self.selected_game = game_id
            
            # Update path
            if game_id in self.games:
                self.path_var.set(self.games[game_id])
                
            # Update arguments
            app = get_app_instance()
            if app:
                settings_service = app.get_service("settings")
                if settings_service:
                    args = settings_service.get(f"game.args.{game_id}", "")
                    self.args_var.set(args)
                    
        except Exception as e:
            self.logger.error(f"Error selecting game: {e}", exc_info=True)
            
    def _on_sandbox_toggle(self):
        """Handle sandbox toggle."""
        self.sandbox_enabled = self.sandbox_var.get()
        
    def _on_sandbox_type_selected(self, sandbox_type):
        """Handle sandbox type selection."""
        self.sandbox_type = sandbox_type
        
        # Disable path input for built-in sandbox
        if sandbox_type == "built_in":
            self.sandbox_path_entry.configure(state="disabled")
            self.sandbox_browse_button.configure(state="disabled")
        else:
            self.sandbox_path_entry.configure(state="normal")
            self.sandbox_browse_button.configure(state="normal")
        
    def _on_mac_spoofing_toggle(self):
        """Handle MAC spoofing toggle."""
        self.mac_spoofing = self.mac_var.get()
        
    def _on_hw_spoofing_toggle(self):
        """Handle hardware ID spoofing toggle."""
        self.hw_spoofing = self.hw_var.get()
        
    def _toggle_network_wrapper(self):
        """Toggle network wrapper options."""
        if self.network_wrapper_var.get():
            self.network_profile_frame.pack(fill="x", padx=10, pady=5)
            # Disable sandbox option when network wrapper is enabled
            self.sandbox_checkbox.configure(state="disabled")
        else:
            self.network_profile_frame.pack_forget()
            # Enable sandbox option when network wrapper is disabled
            self.sandbox_checkbox.configure(state="normal")
            
    def _launch_game(self):
        """Launch the selected game."""
        try:
            # Get selected game
            game_id = self.game_var.get()
            if not game_id:
                self._show_error("Please select a game to launch")
                return
                
            # Get game path
            game_path = self.path_var.get()
            if not game_path:
                self._show_error("Please enter a game path")
                return
                
            # Get arguments
            args = self.args_var.get().strip()
            args_list = args.split() if args else []
            
            # Check if network wrapper is enabled
            network_wrapper_enabled = self.network_wrapper_var.get()
            
            # Launch in a separate thread to avoid blocking UI
            threading.Thread(
                target=self._launch_game_thread,
                args=(game_id, game_path, args_list, network_wrapper_enabled),
                daemon=True
            ).start()
            
        except Exception as e:
            self.logger.error(f"Error launching game: {e}", exc_info=True)
            self._show_error(f"Error launching game: {str(e)}")
            
    def _launch_game_thread(self, game_id, game_path, args, use_network_wrapper=False):
        """Launch game in a separate thread."""
        try:
            app = get_app_instance()
            if not app:
                self.after(0, lambda: self._show_error("App instance not available"))
                return
                
            game_launcher = app.get_service("game_launcher")
            if not game_launcher:
                self.after(0, lambda: self._show_error("Game launcher service not available"))
                return
                
            # Register game if not already registered
            if not game_launcher.is_game_registered(game_id):
                game_launcher.register_game(game_id, game_path)
                
            # Launch game
            success = False
            
            if use_network_wrapper:
                # Get profile type
                profile_type = self.profile_type_var.get().lower()
                if profile_type == "random":
                    network_profile = "random"
                elif profile_type == "united states":
                    network_profile = "country_us"
                elif profile_type == "europe":
                    network_profile = "country_eu"
                elif profile_type == "asia":
                    network_profile = "country_as"
                else:
                    network_profile = "custom"
                    
                # Launch with network wrapper
                success = game_launcher.launch_game_with_network_wrapper(
                    game_id, 
                    network_profile, 
                    args
                )
            elif self.sandbox_var.get():
                # Launch in sandbox
                sandbox_type = self.sandbox_type_var.get()
                
                # Check if sandbox type is available
                available_types = game_launcher.get_available_sandbox_types()
                if sandbox_type not in available_types:
                    self.after(0, lambda: self._show_error(
                        f"Sandbox type '{sandbox_type}' is not available.\n\n"
                        f"Available types: {', '.join(available_types)}\n\n"
                        "Please select an available sandbox type or install the required software."
                    ))
                    return
                
                success = game_launcher.launch_game_in_sandbox(game_id, sandbox_type, args)
            else:
                # Launch normally
                success = game_launcher.launch_game(game_id, args)
                
            if success:
                # Show success message
                success_msg = f"Game {game_id} launched successfully"
                self.after(0, lambda msg=success_msg: self._show_info(msg))
                
                # Refresh running games list
                self.after(1000, self._refresh_running_games)
            else:
                # Show error message
                error_msg = f"Failed to launch game: {game_id}"
                self.after(0, lambda msg=error_msg: self._show_error(msg))
                
        except Exception as e:
            # Capture the error message
            error_msg = f"Error launching game: {str(e)}"
            # Pass the message to the lambda, not the exception
            self.after(0, lambda msg=error_msg: self._show_error(msg))
            
    def _refresh_running_games(self):
        """Refresh the list of running games."""
        try:
            app = get_app_instance()
            if not app:
                return
                
            game_launcher = app.get_service("game_launcher")
            if not game_launcher:
                self.logger.warning("Game launcher service not available")
                return
                
            # Get running games
            running_games = {}
            
            # First get the list of running game instance IDs
            instance_ids = game_launcher.get_running_games()
            
            # Initialize tracking dictionary for boolean game info if not already done
            if not hasattr(self, "_converted_game_info_ids"):
                self._converted_game_info_ids = set()
            
            for instance_id in instance_ids:
                # Try to get game info
                try:
                    game_info = game_launcher.get_game_info(instance_id)
                    
                    # Skip if game_info is None (process no longer exists)
                    if game_info is None:
                        continue
                    
                    # Handle the case where game_info is a boolean (True/False) instead of a dictionary
                    if isinstance(game_info, bool):
                        # Create a proper dictionary
                        game_id = instance_id.split('_')[0] if '_' in instance_id else instance_id
                        game_info = {
                            "game_id": game_id,
                            "instance_id": instance_id,
                            "start_time": time.time(),
                            "in_sandbox": game_launcher.is_game_in_sandbox(instance_id),
                            "sandbox_type": "unknown"
                        }
                        
                        # Only log once per instance ID
                        if instance_id not in self._converted_game_info_ids:
                            self.logger.debug(f"Converted boolean game info to dictionary for {instance_id}")
                            self._converted_game_info_ids.add(instance_id)
                    
                    # Add to running games
                    running_games[instance_id] = game_info
                except Exception as e:
                    # Only log errors once per instance ID
                    if not hasattr(self, "_error_logged_ids"):
                        self._error_logged_ids = {}
                    
                    if instance_id not in self._error_logged_ids or time.time() - self._error_logged_ids.get(instance_id, 0) > 60:
                        self.logger.error(f"Error getting game info for {instance_id}: {e}")
                        self._error_logged_ids[instance_id] = time.time()
                    
                    # Create a minimal game info dictionary
                    game_id = instance_id.split('_')[0] if '_' in instance_id else instance_id
                    running_games[instance_id] = {
                        "game_id": game_id,
                        "instance_id": instance_id,
                        "start_time": time.time(),
                        "error": str(e)
                    }
            
            # Clean up tracking sets for instance IDs that are no longer running
            if hasattr(self, "_converted_game_info_ids"):
                self._converted_game_info_ids = {id for id in self._converted_game_info_ids if id in instance_ids}
            
            if hasattr(self, "_error_logged_ids"):
                self._error_logged_ids = {id: time for id, time in self._error_logged_ids.items() if id in instance_ids}
            
            # Update running games
            self.running_games = running_games
            
            # Update UI
            self._update_running_games_ui()
            
            # Schedule next refresh
            self.after(5000, self._refresh_running_games)
            
        except Exception as e:
            self.logger.error(f"Error refreshing running games: {e}", exc_info=True)
            # Schedule next refresh even if there was an error
            self.after(5000, self._refresh_running_games)
            
    def _update_running_games_ui(self):
        """Update the running games UI."""
        try:
            # Clear existing items
            for widget in self.running_games_frame.winfo_children():
                widget.destroy()
                
            if not self.running_games:
                # Show no games message
                self.no_games_label = ctk.CTkLabel(
                    self.running_games_frame,
                    text="No games running",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                self.no_games_label.pack(pady=50)
                return
                
            # Add running games
            for instance_id, game_info in self.running_games.items():
                self._create_game_item(instance_id, game_info)
                
        except Exception as e:
            self.logger.error(f"Error updating running games UI: {e}", exc_info=True)
            
    def _create_game_item(self, instance_id, game_info):
        """Create a running game item."""
        try:
            # Ensure game_info is a dictionary
            if not isinstance(game_info, dict):
                self.logger.warning(f"Game info for {instance_id} is not a dictionary, converting")
                # Convert to a dictionary with basic info
                game_id = instance_id.split('_')[0] if '_' in instance_id else instance_id
                game_info = {
                    "instance_id": instance_id,
                    "game_id": game_id,
                    "path": self.games.get(game_id, "Unknown"),
                    "start_time": time.time(),
                    "in_sandbox": bool(game_info)  # Convert to boolean
                }
            
            # Get the original game ID
            game_id = game_info.get("game_id", instance_id.split('_')[0] if '_' in instance_id else instance_id)
            
            # Create frame for the game
            game_frame = ctk.CTkFrame(self.running_games_frame)
            game_frame.pack(fill="x", padx=5, pady=5)
            
            # Game name
            name_label = ctk.CTkLabel(
                game_frame,
                text=game_id,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            name_label.pack(anchor="w", padx=10, pady=5)
            
            # Game path
            path = game_info.get("path", self.games.get(game_id, "Unknown"))
            path_label = ctk.CTkLabel(
                game_frame,
                text=f"Path: {path}",
                font=ctk.CTkFont(size=12)
            )
            path_label.pack(anchor="w", padx=10, pady=2)
            
            # Instance ID (shortened)
            short_instance_id = instance_id[-12:] if len(instance_id) > 12 else instance_id
            instance_label = ctk.CTkLabel(
                game_frame,
                text=f"Instance: {short_instance_id}",
                font=ctk.CTkFont(size=12)
            )
            instance_label.pack(anchor="w", padx=10, pady=2)
            
            # Sandbox status
            in_sandbox = game_info.get("in_sandbox", False)
            sandbox_type = game_info.get("sandbox_type", "None")
            
            if in_sandbox:
                sandbox_status = f"In Sandbox ({sandbox_type})"
            else:
                sandbox_status = "Normal"
            
            sandbox_label = ctk.CTkLabel(
                game_frame,
                text=f"Mode: {sandbox_status}",
                font=ctk.CTkFont(size=12)
            )
            sandbox_label.pack(anchor="w", padx=10, pady=2)
            
            # Uptime
            start_time = game_info.get("start_time", time.time())
            uptime_seconds = int(time.time() - start_time)
            uptime_str = self._format_uptime(uptime_seconds)
            
            uptime_label = ctk.CTkLabel(
                game_frame,
                text=f"Uptime: {uptime_str}",
                font=ctk.CTkFont(size=12)
            )
            uptime_label.pack(anchor="w", padx=10, pady=2)
            
            # Buttons frame
            buttons_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
            buttons_frame.pack(fill="x", padx=10, pady=5)
            
            # Focus button
            focus_button = ctk.CTkButton(
                buttons_frame,
                text="Focus",
                width=80,
                command=lambda: self._focus_game(instance_id)
            )
            focus_button.pack(side="left", padx=5)
            
            # Screenshot button
            screenshot_button = ctk.CTkButton(
                buttons_frame,
                text="Screenshot",
                width=100,
                command=lambda: self._take_screenshot(instance_id)
            )
            screenshot_button.pack(side="left", padx=5)
            
            # Terminate button
            terminate_button = ctk.CTkButton(
                buttons_frame,
                text="Terminate",
                width=100,
                fg_color=("red", "#F44336"),
                hover_color=("darkred", "#D32F2F"),
                command=lambda: self._terminate_game(instance_id)
            )
            terminate_button.pack(side="right", padx=5)
            
        except Exception as e:
            self.logger.error(f"Error creating game item: {e}", exc_info=True)
            
    def _format_uptime(self, seconds):
        """Format uptime in seconds to a human-readable string."""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minutes"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} hours, {minutes} minutes"
            
    def _focus_game(self, instance_id):
        """Focus on a running game."""
        try:
            app = get_app_instance()
            if not app:
                return
                
            game_launcher = app.get_service("game_launcher")
            if not game_launcher:
                self.logger.warning("Game launcher service not available")
                return
                
            # Get the original game ID for display
            game_id = "Unknown"
            if instance_id in self.running_games:
                game_info = self.running_games[instance_id]
                if isinstance(game_info, dict):
                    game_id = game_info.get("game_id", instance_id)
            
            # Focus the game window
            if game_launcher.focus_game_window(instance_id):
                self.logger.info(f"Focused game window for '{game_id}'")
            else:
                self._show_warning(f"Could not focus game window for '{game_id}'")
                
        except Exception as e:
            self.logger.error(f"Error focusing game window: {e}", exc_info=True)
            self._show_error(f"Error focusing game window: {str(e)}")
            
    def _take_screenshot(self, instance_id):
        """Take a screenshot of a running game."""
        try:
            app = get_app_instance()
            if not app:
                return
                
            game_launcher = app.get_service("game_launcher")
            if not game_launcher:
                self.logger.warning("Game launcher service not available")
                return
                
            # Get the original game ID for display
            game_id = "Unknown"
            if instance_id in self.running_games:
                game_info = self.running_games[instance_id]
                if isinstance(game_info, dict):
                    game_id = game_info.get("game_id", instance_id)
            
            # Take screenshot
            screenshot_path = game_launcher.take_screenshot(instance_id)
            
            if screenshot_path:
                self.logger.info(f"Screenshot taken for '{game_id}': {screenshot_path}")
                self._show_info(f"Screenshot saved to: {screenshot_path}")
            else:
                self._show_warning(f"Could not take screenshot for '{game_id}'")
                
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}", exc_info=True)
            self._show_error(f"Error taking screenshot: {str(e)}")
            
    def _terminate_game(self, instance_id):
        """Terminate a running game."""
        try:
            app = get_app_instance()
            if not app:
                return
                
            game_launcher = app.get_service("game_launcher")
            if not game_launcher:
                self.logger.warning("Game launcher service not available")
                return
                
            # Get the original game ID for display
            game_id = "Unknown"
            if instance_id in self.running_games:
                game_info = self.running_games[instance_id]
                if isinstance(game_info, dict):
                    game_id = game_info.get("game_id", instance_id)
            
            # Get confirmation
            if not self._show_question("Terminate Game", f"Are you sure you want to terminate '{game_id}'?"):
                return
            
            # Terminate the game
            if game_launcher.terminate_game(instance_id):
                self.logger.info(f"Game '{game_id}' terminated successfully")
                
                # Remove from running games
                if instance_id in self.running_games:
                    del self.running_games[instance_id]
                    
                # Update UI
                self._update_running_games_ui()
            else:
                self._show_error(f"Failed to terminate game '{game_id}'")
                
        except Exception as e:
            self.logger.error(f"Error terminating game: {e}", exc_info=True)
            self._show_error(f"Error terminating game: {str(e)}")
            
    def _terminate_all_games(self):
        """Terminate all running games."""
        try:
            app = get_app_instance()
            if not app:
                return
                
            game_launcher = app.get_service("game_launcher")
            if not game_launcher:
                self.logger.warning("Game launcher service not available")
                return
                
            # Get confirmation
            if not self._show_question("Terminate All Games", "Are you sure you want to terminate all running games?"):
                return
                
            # Terminate all games
            for game_id in list(self.running_games.keys()):
                game_launcher.terminate_game(game_id)
                
            # Clear running games
            self.running_games = {}
            
            # Update UI
            self._update_running_games_ui()
            
            self._show_info("All games terminated successfully")
            
        except Exception as e:
            self.logger.error(f"Error terminating all games: {e}", exc_info=True)
            self._show_error(f"Error terminating all games: {str(e)}")
            
    def _check_network_isolation(self):
        """Check network isolation for sandbox."""
        try:
            app = get_app_instance()
            if not app:
                return
                
            game_launcher = app.get_service("game_launcher")
            if not game_launcher:
                self.logger.warning("Game launcher service not available")
                return
                
            # Get selected game
            game_id = self.game_var.get()
            if not game_id:
                self._show_error("Please select a game to check")
                return
                
            # Find running instances of this game
            running_instances = []
            for instance_id, game_info in self.running_games.items():
                if isinstance(game_info, dict) and game_info.get("game_id") == game_id:
                    running_instances.append(instance_id)
            
            if not running_instances:
                self._show_error(f"Game '{game_id}' is not running")
                return
            
            # Use the first running instance
            instance_id = running_instances[0]
            
            # Check network isolation
            if hasattr(game_launcher, "check_sandbox_network"):
                result = game_launcher.check_sandbox_network(instance_id)
                
                if result.get("status") == "not_running":
                    self._show_error(f"Game '{game_id}' is not running")
                    return
                
                if result.get("status") == "no_sandbox":
                    self._show_warning(f"Game '{game_id}' is not running in a sandbox")
                    return
                
                if result.get("status") == "sandbox_not_running":
                    self._show_error(f"Sandbox for game '{game_id}' is not running")
                    return
                
                if result.get("network_isolated", False):
                    self._show_info("Network Isolation: PASSED\n\nThe game is properly isolated from the network.")
                else:
                    self._show_warning(
                        "Network Isolation: FAILED\n\n"
                        f"The game has access to: {', '.join(result.get('accessible', ['Internet']))}\n\n"
                        "This may allow the game to detect it's running in a sandbox."
                    )
        except Exception as e:
            self.logger.error(f"Error checking network isolation: {e}", exc_info=True)
            self._show_error(f"Error checking network isolation: {str(e)}")
            
    def _monitor_running_games(self):
        """Periodically monitor running games."""
        try:
            # Refresh running games
            self._refresh_running_games()
            
            # Schedule next check
            if self.is_active():
                self.after(5000, self._monitor_running_games)
                
        except Exception as e:
            self.logger.error(f"Error monitoring running games: {e}", exc_info=True)
            
    def _show_error(self, message):
        """Show error message."""
        try:
            from app.ui.utils.dialogs import show_error
            show_error(self, "Error", message)
        except ImportError:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", message)
            
    def _show_info(self, message):
        """Show info message."""
        try:
            from app.ui.utils.dialogs import show_info
            show_info(self, "Information", message)
        except ImportError:
            import tkinter.messagebox as messagebox
            messagebox.showinfo("Information", message)
            
    def _show_warning(self, message):
        """Show warning message."""
        try:
            from app.ui.utils.dialogs import show_warning
            show_warning(self, "Warning", message)
        except ImportError:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Warning", message)
            
    def _show_question(self, title, message):
        """Show question dialog."""
        try:
            from app.ui.utils.dialogs import show_question
            return show_question(self, title, message)
        except ImportError:
            import tkinter.messagebox as messagebox
            return messagebox.askyesno(title, message)
            
    def _launch_game_with_bot(self):
        """Launch the selected game with bot monitoring."""
        try:
            game_id = self.game_var.get()
            game_path = self.path_var.get()
            
            if not game_id or not game_path:
                self._show_error("Please select a game to launch")
                return
                
            if not os.path.exists(game_path):
                self._show_error(f"Game executable not found: {game_path}")
                return
                
            # Get arguments
            args = self.args_var.get().split() if self.args_var.get() else []
            
            # Launch in a separate thread to avoid UI freezing
            threading.Thread(
                target=self._launch_game_with_bot_thread,
                args=(game_id, game_path, args),
                daemon=True
            ).start()
            
        except Exception as e:
            self.logger.error(f"Error launching game with bot: {e}", exc_info=True)
            self._show_error(f"Error launching game with bot: {str(e)}")
            
    def _launch_game_with_bot_thread(self, game_id, game_path, args):
        """Launch a game with bot in a separate thread."""
        try:
            # Get game launcher service
            app = get_app_instance()
            if not app:
                error_msg = "Application instance not available"
                self.after(0, lambda msg=error_msg: self._show_error(msg))
                return
                
            game_launcher = app.get_service("game_launcher")
            if not game_launcher:
                error_msg = "Game launcher service not available"
                self.after(0, lambda msg=error_msg: self._show_error(msg))
                return
                
            # Check if game is registered
            if not game_launcher.is_game_registered(game_id):
                # Register the game first
                success = game_launcher.register_game(game_id, game_path)
                if not success:
                    error_msg = f"Failed to register game: {game_id}"
                    self.after(0, lambda msg=error_msg: self._show_error(msg))
                    return
                    
            # Launch the game with bot
            if hasattr(game_launcher, "launch_game_with_bot"):
                success = game_launcher.launch_game_with_bot(game_id, args)
            else:
                # Fallback to normal launch if method doesn't exist
                success = game_launcher.launch_game(game_id, args)
                
            if success:
                # Show success message
                success_msg = f"Game {game_id} launched with bot successfully"
                self.after(0, lambda msg=success_msg: self._show_info(msg))
                
                # Refresh running games list
                self.after(1000, self._refresh_running_games)
            else:
                # Show error message
                error_msg = f"Failed to launch game with bot: {game_id}"
                self.after(0, lambda msg=error_msg: self._show_error(msg))
                
        except Exception as e:
            # Capture the error message
            error_msg = f"Error launching game with bot: {str(e)}"
            # Pass the message to the lambda, not the exception
            self.after(0, lambda msg=error_msg: self._show_error(msg)) 