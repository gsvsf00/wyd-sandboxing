import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, List, Optional, Tuple
import os
import json

from app.ui.base.base_frame import BaseFrame
from app.core.app_instance import get_app_instance
from app.utils.logger import LoggerWrapper

class SettingsFrame(BaseFrame):
    """Settings frame for application configuration."""
    
    def __init__(self, master, **kwargs):
        """Initialize the settings frame."""
        super().__init__(master, **kwargs)
        self.logger = LoggerWrapper(name="settings_frame")
        self.settings_tabs = None
        self.settings = {}
        # Don't call on_init here to avoid duplicate initialization
        
    def on_init(self):
        """Initialize the settings frame."""
        try:
            super().on_init()
            self._create_content()
            self._load_settings()
        except Exception as e:
            self.logger.error(f"Error initializing settings frame: {e}", exc_info=True)
            
    def _create_content(self):
        """Create the settings content."""
        try:
            # Create header
            header_frame = ctk.CTkFrame(self, fg_color="transparent")
            header_frame.pack(fill="x", padx=20, pady=(20, 10))
            
            title = ctk.CTkLabel(
                header_frame,
                text="Settings",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(side="left", padx=10)
            
            # Create tabview for settings categories
            self.settings_tabs = ctk.CTkTabview(self)
            self.settings_tabs.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Add tabs
            general_tab = self.settings_tabs.add("General")
            appearance_tab = self.settings_tabs.add("Appearance")
            game_tab = self.settings_tabs.add("Game")
            network_tab = self.settings_tabs.add("Network")
            advanced_tab = self.settings_tabs.add("Advanced")
            
            # Create settings content for each tab
            self._create_general_settings(general_tab)
            self._create_appearance_settings(appearance_tab)
            self._create_game_settings(game_tab)
            self._create_network_settings(network_tab)
            self._create_advanced_settings(advanced_tab)
            
            # Create footer with save/reset buttons
            footer_frame = ctk.CTkFrame(self, fg_color="transparent")
            footer_frame.pack(fill="x", padx=20, pady=(10, 20))
            
            reset_button = ctk.CTkButton(
                footer_frame,
                text="Reset to Defaults",
                command=self._reset_settings,
                fg_color="transparent",
                border_width=1,
                text_color=("gray10", "gray90")
            )
            reset_button.pack(side="left", padx=10)
            
            save_button = ctk.CTkButton(
                footer_frame,
                text="Save Settings",
                command=self._save_settings
            )
            save_button.pack(side="right", padx=10)
            
            self.logger.debug("Settings frame content created")
        except Exception as e:
            self.logger.error(f"Error creating settings content: {e}", exc_info=True)
            
    def _create_general_settings(self, parent):
        """Create general settings section."""
        # Application settings
        app_frame = ctk.CTkFrame(parent)
        app_frame.pack(fill="x", padx=10, pady=10)
        
        app_label = ctk.CTkLabel(
            app_frame,
            text="Application Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        app_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Startup option
        startup_var = tk.BooleanVar(value=False)
        startup_check = ctk.CTkCheckBox(
            app_frame,
            text="Start application on system startup",
            variable=startup_var,
            onvalue=True,
            offvalue=False
        )
        startup_check.pack(anchor="w", padx=20, pady=5)
        
        # Minimize to tray option
        tray_var = tk.BooleanVar(value=True)
        tray_check = ctk.CTkCheckBox(
            app_frame,
            text="Minimize to system tray when closed",
            variable=tray_var,
            onvalue=True,
            offvalue=False
        )
        tray_check.pack(anchor="w", padx=20, pady=5)
        
        # Auto-update option
        update_var = tk.BooleanVar(value=True)
        update_check = ctk.CTkCheckBox(
            app_frame,
            text="Check for updates automatically",
            variable=update_var,
            onvalue=True,
            offvalue=False
        )
        update_check.pack(anchor="w", padx=20, pady=5)
        
        # Save variables for later access
        self.settings["general"] = {
            "startup": startup_var,
            "minimize_to_tray": tray_var,
            "auto_update": update_var
        }
        
    def _create_appearance_settings(self, parent):
        """Create appearance settings section."""
        # Theme settings
        theme_frame = ctk.CTkFrame(parent)
        theme_frame.pack(fill="x", padx=10, pady=10)
        
        theme_label = ctk.CTkLabel(
            theme_frame,
            text="Theme Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        theme_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Color theme
        color_label = ctk.CTkLabel(theme_frame, text="Color Theme:")
        color_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        color_var = tk.StringVar(value="dark")
        color_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=20, pady=5)
        
        light_radio = ctk.CTkRadioButton(
            color_frame,
            text="Light",
            variable=color_var,
            value="light"
        )
        light_radio.pack(side="left", padx=(0, 10))
        
        dark_radio = ctk.CTkRadioButton(
            color_frame,
            text="Dark",
            variable=color_var,
            value="dark"
        )
        dark_radio.pack(side="left", padx=10)
        
        system_radio = ctk.CTkRadioButton(
            color_frame,
            text="System",
            variable=color_var,
            value="system"
        )
        system_radio.pack(side="left", padx=10)
        
        # UI scaling
        scaling_label = ctk.CTkLabel(theme_frame, text="UI Scaling:")
        scaling_label.pack(anchor="w", padx=20, pady=(15, 5))
        
        scaling_var = tk.StringVar(value="100%")
        scaling_combobox = ctk.CTkComboBox(
            theme_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            variable=scaling_var
        )
        scaling_combobox.pack(anchor="w", padx=20, pady=5)
        
        # Save variables for later access
        self.settings["appearance"] = {
            "color_theme": color_var,
            "ui_scaling": scaling_var
        }
        
    def _create_game_settings(self, parent):
        """Create game settings section."""
        # Game settings
        game_frame = ctk.CTkFrame(parent)
        game_frame.pack(fill="x", padx=10, pady=10)
        
        game_label = ctk.CTkLabel(
            game_frame,
            text="Game Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        game_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Game path
        path_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=20, pady=10)
        
        path_label = ctk.CTkLabel(path_frame, text="Game Path:")
        path_label.pack(anchor="w")
        
        path_entry_frame = ctk.CTkFrame(path_frame, fg_color="transparent")
        path_entry_frame.pack(fill="x", pady=5)
        
        path_var = tk.StringVar(value="")
        path_entry = ctk.CTkEntry(
            path_entry_frame,
            textvariable=path_var,
            width=300
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_button = ctk.CTkButton(
            path_entry_frame,
            text="Browse",
            width=80,
            command=self._browse_game_path
        )
        browse_button.pack(side="right")
        
        # Game options
        options_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=10)
        
        options_label = ctk.CTkLabel(
            options_frame,
            text="Launch Options:",
            font=ctk.CTkFont(weight="bold")
        )
        options_label.pack(anchor="w")
        
        # Auto-login option
        autologin_var = tk.BooleanVar(value=True)
        autologin_check = ctk.CTkCheckBox(
            options_frame,
            text="Enable auto-login",
            variable=autologin_var,
            onvalue=True,
            offvalue=False
        )
        autologin_check.pack(anchor="w", pady=5)
        
        # Save variables for later access
        self.settings["game"] = {
            "game_path": path_var,
            "auto_login": autologin_var
        }
        
    def _create_network_settings(self, parent):
        """Create network settings section."""
        # Network settings
        network_frame = ctk.CTkFrame(parent)
        network_frame.pack(fill="x", padx=10, pady=10)
        
        network_label = ctk.CTkLabel(
            network_frame,
            text="Network Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        network_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Proxy settings
        proxy_frame = ctk.CTkFrame(network_frame, fg_color="transparent")
        proxy_frame.pack(fill="x", padx=20, pady=10)
        
        proxy_var = tk.BooleanVar(value=False)
        proxy_check = ctk.CTkCheckBox(
            proxy_frame,
            text="Use proxy",
            variable=proxy_var,
            onvalue=True,
            offvalue=False,
            command=self._toggle_proxy_settings
        )
        proxy_check.pack(anchor="w")
        
        # Proxy details frame
        proxy_details_frame = ctk.CTkFrame(proxy_frame, fg_color="transparent")
        proxy_details_frame.pack(fill="x", pady=10)
        
        # Host
        host_label = ctk.CTkLabel(proxy_details_frame, text="Host:")
        host_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        host_var = tk.StringVar(value="")
        host_entry = ctk.CTkEntry(proxy_details_frame, textvariable=host_var, width=200)
        host_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Port
        port_label = ctk.CTkLabel(proxy_details_frame, text="Port:")
        port_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        port_var = tk.StringVar(value="")
        port_entry = ctk.CTkEntry(proxy_details_frame, textvariable=port_var, width=200)
        port_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Username
        username_label = ctk.CTkLabel(proxy_details_frame, text="Username:")
        username_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        username_var = tk.StringVar(value="")
        username_entry = ctk.CTkEntry(proxy_details_frame, textvariable=username_var, width=200)
        username_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Password
        password_label = ctk.CTkLabel(proxy_details_frame, text="Password:")
        password_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        
        password_var = tk.StringVar(value="")
        password_entry = ctk.CTkEntry(proxy_details_frame, textvariable=password_var, width=200, show="•")
        password_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        
        # Configure grid
        proxy_details_frame.grid_columnconfigure(1, weight=1)
        
        # Initially disable proxy settings
        self._toggle_proxy_settings_state(False)
        
        # Save variables for later access
        self.settings["network"] = {
            "use_proxy": proxy_var,
            "proxy_host": host_var,
            "proxy_port": port_var,
            "proxy_username": username_var,
            "proxy_password": password_var,
            "proxy_details_frame": proxy_details_frame
        }
        
    def _create_advanced_settings(self, parent):
        """Create advanced settings section."""
        # Advanced settings
        advanced_frame = ctk.CTkFrame(parent)
        advanced_frame.pack(fill="x", padx=10, pady=10)
        
        advanced_label = ctk.CTkLabel(
            advanced_frame,
            text="Advanced Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        advanced_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Warning label
        warning_label = ctk.CTkLabel(
            advanced_frame,
            text="Warning: These settings are for advanced users only.",
            text_color=("red", "#FF5555")
        )
        warning_label.pack(anchor="w", padx=20, pady=5)
        
        # Debug mode
        debug_var = tk.BooleanVar(value=False)
        debug_check = ctk.CTkCheckBox(
            advanced_frame,
            text="Enable debug mode",
            variable=debug_var,
            onvalue=True,
            offvalue=False
        )
        debug_check.pack(anchor="w", padx=20, pady=5)
        
        # Log level
        log_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        log_frame.pack(fill="x", padx=20, pady=5)
        
        log_label = ctk.CTkLabel(log_frame, text="Log Level:")
        log_label.pack(anchor="w")
        
        log_var = tk.StringVar(value="INFO")
        log_combobox = ctk.CTkComboBox(
            log_frame,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            variable=log_var
        )
        log_combobox.pack(anchor="w", pady=5)
        
        # Database connection
        db_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        db_frame.pack(fill="x", padx=20, pady=10)
        
        db_label = ctk.CTkLabel(db_frame, text="Database Connection:")
        db_label.pack(anchor="w")
        
        db_var = tk.StringVar(value="")
        db_entry = ctk.CTkEntry(db_frame, textvariable=db_var, width=300)
        db_entry.pack(fill="x", pady=5)
        
        # Save variables for later access
        self.settings["advanced"] = {
            "debug_mode": debug_var,
            "log_level": log_var,
            "db_connection": db_var
        }
        
    def _toggle_proxy_settings(self):
        """Toggle proxy settings based on checkbox state."""
        use_proxy = self.settings["network"]["use_proxy"].get()
        self._toggle_proxy_settings_state(use_proxy)
        
    def _toggle_proxy_settings_state(self, enabled):
        """Enable or disable proxy settings fields."""
        if "network" not in self.settings:
            self.logger.warning("Network settings not initialized")
            return
        
        state = "normal" if enabled else "disabled"
        proxy_details_frame = self.settings["network"].get("proxy_details_frame")
        
        if not proxy_details_frame:
            self.logger.warning("Proxy details frame not found")
            return
        
        for child in proxy_details_frame.winfo_children():
            if isinstance(child, ctk.CTkEntry):
                if state == "normal":
                    child.configure(state="normal")
                else:
                    child.configure(state="disabled")
                    
    def _browse_game_path(self):
        """Open file dialog to browse for game executable."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Select Game Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        
        if file_path:
            self.settings["game"]["game_path"].set(file_path)
            
    def _load_settings(self):
        """Load settings from app configuration."""
        try:
            app = get_app_instance()
            if not app:
                self.logger.warning("App instance not available, using default settings")
                return
                
            settings_service = app.get_service("settings")
            if not settings_service:
                self.logger.warning("Settings service not available, using default settings")
                return
                
            # Load general settings
            if "general" in self.settings:
                self.settings["general"]["startup"].set(
                    settings_service.get("general.startup", False)
                )
                self.settings["general"]["minimize_to_tray"].set(
                    settings_service.get("general.minimize_to_tray", True)
                )
                self.settings["general"]["auto_update"].set(
                    settings_service.get("general.auto_update", True)
                )
                
            # Load appearance settings
            if "appearance" in self.settings:
                self.settings["appearance"]["color_theme"].set(
                    settings_service.get("appearance.color_theme", "dark")
                )
                self.settings["appearance"]["ui_scaling"].set(
                    settings_service.get("appearance.ui_scaling", "100%")
                )
                
            # Load game settings
            if "game" in self.settings:
                self.settings["game"]["game_path"].set(
                    settings_service.get("game.path", "")
                )
                self.settings["game"]["auto_login"].set(
                    settings_service.get("game.auto_login", True)
                )
                
            # Load network settings
            if "network" in self.settings:
                use_proxy = settings_service.get("network.use_proxy", False)
                self.settings["network"]["use_proxy"].set(use_proxy)
                self.settings["network"]["proxy_host"].set(
                    settings_service.get("network.proxy.host", "")
                )
                self.settings["network"]["proxy_port"].set(
                    settings_service.get("network.proxy.port", "")
                )
                self.settings["network"]["proxy_username"].set(
                    settings_service.get("network.proxy.username", "")
                )
                self.settings["network"]["proxy_password"].set(
                    settings_service.get("network.proxy.password", "")
                )
                self._toggle_proxy_settings_state(use_proxy)
                
            # Load advanced settings
            if "advanced" in self.settings:
                self.settings["advanced"]["debug_mode"].set(
                    settings_service.get("advanced.debug_mode", False)
                )
                self.settings["advanced"]["log_level"].set(
                    settings_service.get("advanced.log_level", "INFO")
                )
                self.settings["advanced"]["db_connection"].set(
                    settings_service.get("advanced.db_connection", "")
                )
                
            self.logger.debug("Settings loaded from configuration")
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}", exc_info=True)
            
    def _save_settings(self):
        """Save settings to app configuration."""
        try:
            app = get_app_instance()
            if not app:
                self.logger.error("App instance not available, cannot save settings")
                return
                
            settings_service = app.get_service("settings")
            if not settings_service:
                self.logger.error("Settings service not available, cannot save settings")
                return
                
            # Save general settings
            if "general" in self.settings:
                settings_service.set("general.startup", self.settings["general"]["startup"].get())
                settings_service.set("general.minimize_to_tray", self.settings["general"]["minimize_to_tray"].get())
                settings_service.set("general.auto_update", self.settings["general"]["auto_update"].get())
                
            # Save appearance settings
            if "appearance" in self.settings:
                settings_service.set("appearance.color_theme", self.settings["appearance"]["color_theme"].get())
                settings_service.set("appearance.ui_scaling", self.settings["appearance"]["ui_scaling"].get())
                
            # Save game settings
            if "game" in self.settings:
                settings_service.set("game.path", self.settings["game"]["game_path"].get())
                settings_service.set("game.auto_login", self.settings["game"]["auto_login"].get())
                
            # Save network settings
            if "network" in self.settings:
                settings_service.set("network.use_proxy", self.settings["network"]["use_proxy"].get())
                settings_service.set("network.proxy.host", self.settings["network"]["proxy_host"].get())
                settings_service.set("network.proxy.port", self.settings["network"]["proxy_port"].get())
                settings_service.set("network.proxy.username", self.settings["network"]["proxy_username"].get())
                settings_service.set("network.proxy.password", self.settings["network"]["proxy_password"].get())
                
            # Save advanced settings
            if "advanced" in self.settings:
                settings_service.set("advanced.debug_mode", self.settings["advanced"]["debug_mode"].get())
                settings_service.set("advanced.log_level", self.settings["advanced"]["log_level"].get())
                settings_service.set("advanced.db_connection", self.settings["advanced"]["db_connection"].get())
                
            # Apply settings
            self._apply_settings()
            
            self.logger.info("Settings saved successfully")
            
            # Show success message
            self._show_success_message("Settings saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}", exc_info=True)
            
    def _reset_settings(self):
        """Reset settings to defaults."""
        try:
            # Confirm reset
            from app.ui.utils.dialogs import show_question
            
            if not show_question(self, "Reset Settings", "Are you sure you want to reset all settings to defaults?"):
                return
                
            # Reset general settings
            if "general" in self.settings:
                self.settings["general"]["startup"].set(False)
                self.settings["general"]["minimize_to_tray"].set(True)
                self.settings["general"]["auto_update"].set(True)
                
            # Reset appearance settings
            if "appearance" in self.settings:
                self.settings["appearance"]["color_theme"].set("dark")
                self.settings["appearance"]["ui_scaling"].set("100%")
                
            # Reset game settings
            if "game" in self.settings:
                self.settings["game"]["game_path"].set("")
                self.settings["game"]["auto_login"].set(True)
                
            # Reset network settings
            if "network" in self.settings:
                self.settings["network"]["use_proxy"].set(False)
                self.settings["network"]["proxy_host"].set("")
                self.settings["network"]["proxy_port"].set("")
                self.settings["network"]["proxy_username"].set("")
                self.settings["network"]["proxy_password"].set("")
                self._toggle_proxy_settings_state(False)
                
            # Reset advanced settings
            if "advanced" in self.settings:
                self.settings["advanced"]["debug_mode"].set(False)
                self.settings["advanced"]["log_level"].set("INFO")
                self.settings["advanced"]["db_connection"].set("")
                
            self.logger.info("Settings reset to defaults")
            
            # Show success message
            self._show_success_message("Settings reset to defaults")
        except Exception as e:
            self.logger.error(f"Error resetting settings: {e}", exc_info=True)
            
    def _apply_settings(self):
        """Apply settings that can be changed at runtime."""
        try:
            app = get_app_instance()
            if not app:
                return
                
            # Apply appearance settings
            appearance = self.settings.get("appearance", {})
            if "color_theme" in appearance:
                theme = appearance["color_theme"].get()
                ctk.set_appearance_mode(theme)
                
            if "ui_scaling" in appearance:
                scaling = appearance["ui_scaling"].get()
                scale_value = float(scaling.strip("%")) / 100
                ctk.set_widget_scaling(scale_value)
                
            # Apply advanced settings
            advanced = self.settings.get("advanced", {})
            if "log_level" in advanced:
                log_level = advanced["log_level"].get()
                # Update log level (implementation depends on your logging setup)
                
            self.logger.debug("Applied runtime settings")
        except Exception as e:
            self.logger.error(f"Error applying settings: {e}", exc_info=True)
            
    def _show_success_message(self, message):
        """Show a success message that disappears after a few seconds."""
        try:
            # Create success message frame
            if hasattr(self, "success_frame"):
                self.success_frame.destroy()
                
            self.success_frame = ctk.CTkFrame(
                self,
                fg_color=("#DDFFDD", "#005500"),
                corner_radius=6
            )
            self.success_frame.place(relx=0.5, rely=0.9, anchor="center")
            
            success_label = ctk.CTkLabel(
                self.success_frame,
                text=message,
                text_color=("#005500", "#FFFFFF"),
                font=ctk.CTkFont(weight="bold")
            )
            success_label.pack(padx=20, pady=10)
            
            # Schedule removal
            self.after(3000, self._hide_success_message)
        except Exception as e:
            self.logger.error(f"Error showing success message: {e}", exc_info=True)
            
    def _hide_success_message(self):
        """Hide the success message."""
        if hasattr(self, "success_frame"):
            self.success_frame.destroy()
            delattr(self, "success_frame") 