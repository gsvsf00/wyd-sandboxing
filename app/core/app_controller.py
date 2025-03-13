#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Application Controller for WydBot.
Manages the overall application lifecycle and provides centralized services.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional, List, Type, Callable
import time
import threading
import os
import sys
from pathlib import Path

# Import utilities
from app.utils.logger import LoggerWrapper
from app.utils.config import load_config, get_config_value
from app.utils.thread_manager import get_thread_manager, run_in_background

# Import UI components
from app.ui.frame_manager import FrameManager
from app.ui.utils import center_window, get_theme_color
from app.ui.utils.dialogs import CTkDialog, show_question, show_error, show_info
from app.core.frame_manager import FrameManager as CoreFrameManager
from app.core.app_instance import set_app_instance

# Import auth cache
from app.utils.auth_cache import AuthCache

# Global logger instance
logger = LoggerWrapper(name="app_controller")

# Global app instance
_app_instance = None


def get_app_instance():
    """Get the global app controller instance."""
    return _app_instance


def get_app_root():
    """Get the root window of the application."""
    app = get_app_instance()
    if app:
        return app.root
    return None


class AppController:
    """
    Main application controller.
    Manages services, frames, and application state.
    """
    
    def __init__(self, root, config=None):
        """
        Initialize the application controller.
        
        Args:
            root: The root Tkinter window
            config: Optional configuration dictionary
        """
        global _app_instance
        # Set global instance
        _app_instance = self
        set_app_instance(self)
        
        self.logger = LoggerWrapper(name="app_controller")
        self.root = root
        self.config = config or {}
        self.services = {}
        self.current_user = None
        self.frame_manager = None
        
        # Add service status tracking
        self.service_status = {}
        self.services_initializing = False
        self.initialization_complete = False
        self.is_shutting_down = False
        
        # Add auth cache
        self.auth_cache = AuthCache()
        
        # Initialize services first (frames may depend on them)
        self._init_services()
        
        # Initialize UI after services
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the application UI."""
        try:
            self.logger.info("Setting up application UI")
            
        # Configure root window
            self.root.title("WydBot")
            self.root.geometry("1280x720")
            self.root.minsize(800, 600)
        
            # Import here to avoid circular imports
            from app.ui.frames.main_container_frame import MainContainerFrame
        
            try:
        # Create main container frame
                self.main_container = MainContainerFrame(self.root)
                self.main_container.pack(fill="both", expand=True)
        
        # Initialize frame manager
                from app.core.frame_manager import FrameManager
                self.frame_manager = FrameManager(self.main_container.get_content_area())
        
        # Register frames
                self._register_frames()
                
                # Show initial frame - use try/except to handle missing methods
                try:
                    if hasattr(self.frame_manager, 'is_frame_registered') and self.frame_manager.is_frame_registered("dashboard"):
                        self.frame_manager.show_frame("dashboard")
                    elif hasattr(self.frame_manager, '_frames') and "dashboard" in self.frame_manager._frames:
                        self.frame_manager.show_frame("dashboard")
                    else:
                        self.logger.error("Initial frame 'dashboard' not registered")
                        # Create a fallback UI
                        self._create_fallback_ui()
                except Exception as e:
                    self.logger.error(f"Error showing initial frame: {e}", exc_info=True)
                    self._create_fallback_ui()
                    
            except Exception as e:
                self.logger.error(f"Error creating UI components: {e}", exc_info=True)
                self._create_fallback_ui()
                
        except Exception as e:
            self.logger.error(f"Error setting up UI: {e}", exc_info=True)
            self._create_fallback_ui()
            
    def _create_fallback_ui(self):
        """Create a fallback UI when normal initialization fails."""
        try:
            # Clear root window
            for widget in self.root.winfo_children():
                widget.destroy()
                
            # Create a simple frame with an error message
            frame = ctk.CTkFrame(self.root)
            frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            title = ctk.CTkLabel(
                frame,
                text="Application Error",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=("red", "#F44336")
            )
            title.pack(pady=(40, 10))
            
            message = ctk.CTkLabel(
                frame,
                text="There was an error initializing the application.\nCheck the logs for more details.",
                font=ctk.CTkFont(size=14)
            )
            message.pack(pady=10)
            
            # Add a restart button
            restart_button = ctk.CTkButton(
                frame,
                text="Restart Application",
                command=self.exit
            )
            restart_button.pack(pady=20)
            
        except Exception as e:
            self.logger.error(f"Error creating fallback UI: {e}", exc_info=True)
            # If even the fallback UI fails, show a message box
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Critical Error",
                "The application encountered a critical error and cannot continue.\n\n"
                "Please check the logs for details."
            )
            
    def _register_frames(self):
        """Register application frames with the frame manager."""
        try:
            # Import frames
            from app.ui.frames.dashboard_frame import DashboardFrame
            from app.ui.frames.game_launcher_frame import GameLauncherFrame
            from app.ui.frames.account_frame import AccountFrame
            from app.ui.frames.settings_frame import SettingsFrame
            from app.ui.frames.admin.admin_panel_frame import AdminPanelFrame
            
            # Register frames
            self.frame_manager.register_frame("dashboard", DashboardFrame)
            self.frame_manager.register_frame("game_launcher", GameLauncherFrame)
            self.frame_manager.register_frame("account", AccountFrame)
            self.frame_manager.register_frame("settings", SettingsFrame)
            self.frame_manager.register_frame("admin_panel", AdminPanelFrame)  # Make sure this matches the sidebar ID
            
            # Show initial frame
            self.frame_manager.show_frame("dashboard")
            
            self.logger.info("Application frames registered")
        except Exception as e:
            self.logger.error(f"Error registering frames: {e}", exc_info=True)
            self._create_fallback_ui()
    
    def _init_services(self):
        """Initialize application services."""
        self.logger.info("Initializing services")
        
        # Set initialization flag and track startup time
        self.services_initializing = True
        self.startup_timestamp = time.time()
        self.max_init_time = 60  # Maximum 60 seconds for initialization
        
        # Initialize service status tracking
        self.service_status = {
            "database": "initializing",
            "auth": "pending",
            "game_launcher": "pending",
            "network_mask": "pending",
            "bot": "pending",
            "settings": "pending"
        }
        
        # Start monitoring initialization timeout
        self._start_init_timeout_monitor()
        
        # Start initialization in background thread
        threading.Thread(target=self._init_services_async, daemon=True).start()
    
    def _start_init_timeout_monitor(self):
        """Start a timer to monitor service initialization timeouts."""
        def check_timeout():
            if not self.services_initializing:
                return  # Initialization already completed
            
            # Check if we've exceeded the maximum initialization time
            elapsed = time.time() - self.startup_timestamp
            if elapsed > self.max_init_time:
                self.logger.warning(f"Service initialization timed out after {elapsed:.1f} seconds")
                # Force initialization to complete
                self.services_initializing = False
                # Mark any pending services as timed out
                for service_id, status in self.service_status.items():
                    if status in ["pending", "initializing"]:
                        self.service_status[service_id] = "timeout"
                # Refresh UI
                self._refresh_ui()
            else:
                # Check again in 5 seconds
                self.root.after(5000, check_timeout)
            
        # Start the initial check
        self.root.after(5000, check_timeout)
    
    def _init_services_async(self):
        """Initialize services in a background thread."""
        try:
            self.logger.info("Starting async service initialization")
            
            # Set initialization flag
            self.services_initializing = True
            
            # Initialize database first
            db_success = self._init_database_service()
            if not db_success:
                self.logger.error("Failed to initialize database service")
                self.service_status["database"] = "failed"
                # Continue with other services - some might work without database
            
            # Initialize auth service after database
            if db_success:
                auth_success = self._init_auth_service()
                if not auth_success:
                    self.logger.error("Failed to initialize auth service")
                    self.service_status["auth"] = "failed"
            else:
                self.logger.warning("Skipping auth service initialization due to database failure")
                self.service_status["auth"] = "skipped"
            
            # Initialize other services
            self._init_game_launcher_service()
            self._init_network_mask_service()
            self._init_bot_service()
            self._init_settings_service()
            
            # Set initialization complete
            self.services_initializing = False
            
            # Call completion callback on main thread
            self.root.after(0, self._on_initialization_complete)
            
        except Exception as e:
            self.logger.error(f"Error in service initialization: {e}", exc_info=True)
            # Mark initialization as complete to prevent UI from being stuck
            self.services_initializing = False
            # Schedule UI update on main thread
            self.root.after(0, self._refresh_ui)
    
    def register_service(self, service_id: str, service_instance):
        """
        Register a service with the application.
        
        Args:
            service_id: Unique identifier for the service
            service_instance: The service instance to register
        """
        try:
            self.logger.debug(f"Registering service: {service_id}")
            self.services[service_id] = service_instance
        except Exception as e:
            self.logger.error(f"Error registering service {service_id}: {e}", exc_info=True)
            
    def get_service(self, service_id: str):
        """
        Get a service by ID.
        
        Args:
            service_id: The ID of the service to get
            
        Returns:
            The service instance, or None if not found
        """
        return self.services.get(service_id)
        
    def set_authenticated_user(self, user_data: Dict[str, Any]):
        """
        Set the authenticated user and update UI accordingly.
        
        Args:
            user_data: The user data
        """
        try:
            self.logger.info(f"Setting authenticated user: {user_data.get('username')}")
            self.current_user = user_data
            
            # Update sidebar with authentication status
            is_admin = user_data.get("role") == "admin"
            
            # Update main container if it exists
            if hasattr(self, "main_container") and self.main_container:
                if hasattr(self.main_container, "set_authenticated"):
                    self.main_container.set_authenticated(True, is_admin)
                elif hasattr(self.main_container, "_update_sidebar"):
                    self.main_container._update_sidebar()
            
            # Navigate to dashboard
            if self.frame_manager:
                self.frame_manager.show_frame("dashboard")
            
            # Log success
            self.logger.info(f"User {user_data.get('username')} authenticated successfully")
            
        except Exception as e:
            self.logger.error(f"Error setting authenticated user: {e}", exc_info=True)
            
    def logout(self):
        """Log out the current user."""
        try:
            self.logger.info("Logging out user")
            
            # Get current username
            username = self.current_user.get("username") if self.current_user else None
            
            # Get auth service and logout
            auth_service = self.get_service("auth")
            if auth_service and hasattr(auth_service, "logout"):
                auth_service.logout()
                
            # Clear cached credentials if a username is available
            if username:
                self.auth_cache.clear_credentials(username)
                
            # Clear current user
            self.current_user = None
            
            # Update sidebar
            if hasattr(self, "main_container") and self.main_container:
                if hasattr(self.main_container, "set_authenticated"):
                    self.main_container.set_authenticated(False, False)
                elif hasattr(self.main_container, "_update_sidebar"):
                    self.main_container._update_sidebar()
            
            # Navigate to dashboard
            if self.frame_manager:
                self.frame_manager.show_frame("dashboard")
            
            # Log success
            self.logger.info(f"User {username} logged out successfully")
            
        except Exception as e:
            self.logger.error(f"Error during logout: {e}", exc_info=True)
            
    def run(self):
        """Run the application main loop."""
        try:
            self.logger.info("Starting application main loop")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error in application main loop: {e}", exc_info=True)
            
    def exit(self):
        """Exit the application properly."""
        try:
            self.logger.info("Exiting application")
            
            # Cleanup services
            for service_id, service in self.services.items():
                try:
                    if hasattr(service, "cleanup") and callable(service.cleanup):
                        self.logger.debug(f"Cleaning up service: {service_id}")
                        service.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up service {service_id}: {e}", exc_info=True)
                    
            # Exit
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Error exiting application: {e}", exc_info=True)
            # Force exit in case of error
            self.root.destroy()
    
    def _init_database_service(self):
        """Initialize the database service."""
        try:
            self.logger.info("Initializing database service...")
            
            # Get database configuration
            db_config = self.config.get("database", {})
            connection_string = db_config.get("connection_string", "")
            
            # Use the mock_db setting from the config file
            use_mock_db = db_config.get("use_mock_db", False)
            
            # Set timeout values
            db_config.setdefault("connect_timeout_ms", 10000)
            db_config.setdefault("server_selection_timeout_ms", 10000)
            
            # Set SSL configuration
            db_config.setdefault("ssl", True)
            db_config.setdefault("tls_allow_invalid_certificates", True)
            
            # Create a masked version for logging
            masked_string = self._mask_connection_string(connection_string)
            self.logger.info(f"Database configuration: {masked_string} (use_mock_db={use_mock_db})")
            
            # Initialize database service
            from app.services.database_service import DatabaseService
            db_service = DatabaseService(db_config)
            self.register_service("database", db_service)
            
            # Attempt connection
            if not db_service.connect():
                self.logger.error("Failed to connect to MongoDB")
                # If connection fails and we're not using mock DB, mark as failed
                if not use_mock_db:
                    self.service_status["database"] = "failed"
                    return False
                else:
                    # If using mock DB, we can continue even if real connection fails
                    self.logger.warning("Using mock database instead of real MongoDB")
                    self.service_status["database"] = "ready"
                    return True
            
            self.logger.info("Database service initialized")
            self.service_status["database"] = "ready"
            return True
        except Exception as e:
            self.logger.error(f"Error initializing database service: {e}", exc_info=True)
            self.service_status["database"] = "failed"
            return False
    
    def _mask_connection_string(self, uri: str) -> str:
        """
        Mask sensitive information in a MongoDB connection string.
        
        Args:
            uri: MongoDB connection string
            
        Returns:
            Masked connection string
        """
        if not uri:
            return "None"
        
        try:
            # Simple masking for mongodb://user:pass@host:port/db format
            if '@' in uri:
                prefix, rest = uri.split('@', 1)
                if '//' in prefix and ':' in prefix:
                    protocol, auth = prefix.split('//', 1)
                    if ':' in auth:
                        user, _ = auth.split(':', 1)
                        return f"{protocol}//{user}:****@{rest}"
            
            # If we can't parse it properly, just return a generic masked string
            return uri.split('://')[0] + "://****"
        except Exception:
            return "mongodb://****"
    
    def _init_auth_service(self):
        """Initialize the authentication service."""
        try:
            self.logger.info("Initializing authentication service...")
            self.service_status["auth"] = "initializing"
            
            # Get database service
            db_service = self.get_service("database")
            if not db_service:
                self.logger.error("Database service not available, cannot initialize auth service")
                self.service_status["auth"] = "failed"
                return False
            
            # Initialize auth service
            from app.services.auth_service import AuthService
            auth_service = AuthService(db_service, self.config)
            
            # Register service
            self.register_service("auth", auth_service)
            self.service_status["auth"] = "ready"
            self.logger.info("Authentication service initialized")
            
            # Update UI to reflect auth service status
            self.root.after(0, lambda: self._update_service_ui("auth"))
            
            return True
        except Exception as e:
            self.logger.error(f"Error initializing auth service: {e}", exc_info=True)
            self.service_status["auth"] = "failed"
            return False
    
    def _init_game_launcher_service(self):
        """Initialize the game launcher service."""
        try:
            # First check if psutil is available
            try:
                import psutil
            except ImportError:
                # Try to install psutil
                from app.utils.dependency_installer import install_dependency
                if not install_dependency("psutil"):
                    self.logger.error("Failed to install psutil dependency")
                    self.service_status["game_launcher"] = "failed"
                    return False
            
            # Now initialize the service
            from app.services.game_launcher_service import GameLauncherService
            game_launcher_service = GameLauncherService(self.config)
            self.register_service("game_launcher", game_launcher_service)
            self.service_status["game_launcher"] = "ready"
            self.logger.info("Game launcher service initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize game launcher service: {e}", exc_info=True)
            self.service_status["game_launcher"] = "failed"
            return False
    
    def _init_network_mask_service(self):
        """Initialize network mask service."""
        try:
            from app.services.network_mask_service import NetworkMaskService
            network_service = NetworkMaskService(self.config)
            self.register_service('network_mask', network_service)
            logger.info("Network mask service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize network mask service: {e}")
    
    def _init_bot_service(self):
        """Initialize bot service."""
        try:
            from app.services.bot_service import BotService
            bot_service = BotService(self.config)
            self.register_service('bot', bot_service)
            logger.info("Bot service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize bot service: {e}")
    
    def _init_settings_service(self):
        """Initialize settings service."""
        try:
            from app.services.settings_service import SettingsService
            settings_service = SettingsService(self.config)
            self.register_service('settings', settings_service)
            logger.info("Settings service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize settings service: {e}")
    
    def _schedule_updates(self):
        """Schedule periodic updates."""
        # Schedule a health check every 60 seconds
        self.root.after(60000, self._health_check)
        
        # Schedule a UI refresh every 5 seconds
        self.root.after(5000, self._refresh_ui)
    
    def _health_check(self):
        """Perform a health check."""
        if self.is_shutting_down:
            return
        
        # Check services
        for name, service in self.services.items():
            if hasattr(service, "check_health") and callable(service.check_health):
                try:
                    is_healthy = service.check_health()
                    if not is_healthy:
                        logger.warning(f"Service {name} is not healthy")
                except Exception as e:
                    logger.error(f"Error checking health of service {name}: {e}")
        
        # Schedule next health check
        self.root.after(60000, self._health_check)
    
    def _refresh_ui(self):
        """Refresh the UI."""
        if self.is_shutting_down:
            return
        
        # Update current frame
        if self.frame_manager.current_frame_id:
            current_frame = self.frame_manager.get_frame_instance(self.frame_manager.current_frame_id)
            if current_frame:
                current_frame.on_update()
        
        # Schedule next refresh
        self.root.after(5000, self._refresh_ui)
    
    def _on_window_configure(self, event):
        """Handle window resize events."""
        # Only handle events from the root window
        if event.widget != self.root:
            return
        
        # Update layout if needed
        pass
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        is_fullscreen = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not is_fullscreen)
    
    def show_connection_error_and_exit(self):
        """Show a connection error dialog and exit the application."""
        from app.ui.utils.dialogs import show_error
        
        logger.error("Showing database connection error popup")
        show_error(
            title="Database Connection Error",
            message="Unable to connect to MongoDB server.\n\nPlease check your internet connection and try again later.",
            parent=self.root
        )
        
        # Schedule application exit
        self.root.after(500, self.exit) 

    def _update_service_ui(self, service_id):
        """Update UI based on service status."""
        try:
            # Check if main container is available
            if hasattr(self, "main_container") and self.main_container:
                # For auth service specifically, update sidebar
                if service_id == "auth":
                    self.main_container._update_sidebar()
        except Exception as e:
            self.logger.error(f"Error updating UI for service {service_id}: {e}", exc_info=True)

    def _on_initialization_complete(self):
        """Handle completion of service initialization."""
        try:
            self.logger.info("Service initialization complete")
            
            # Update main container if available
            if hasattr(self, "main_container") and self.main_container:
                if hasattr(self.main_container, "_update_sidebar"):
                    self.main_container._update_sidebar()
            
            # Refresh current frame - use try/except to handle missing methods
            try:
                if self.frame_manager:
                    if hasattr(self.frame_manager, 'get_current_frame'):
                        current_frame = self.frame_manager.get_current_frame()
                        if current_frame and hasattr(current_frame, "refresh"):
                            current_frame.refresh()
                    elif hasattr(self.frame_manager, 'current_frame_id') and hasattr(self.frame_manager, 'get_frame_instance'):
                        current_frame = self.frame_manager.get_frame_instance(self.frame_manager.current_frame_id)
                        if current_frame and hasattr(current_frame, "refresh"):
                            current_frame.refresh()
            except Exception as e:
                self.logger.error(f"Error refreshing current frame: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error handling initialization completion: {e}", exc_info=True)

    def is_service_ready(self, service_id):
        """Check if a specific service is ready."""
        return self.service_status.get(service_id) == "ready"
    
    def are_all_services_ready(self):
        """Check if all services are ready."""
        return all(status == "ready" for status in self.service_status.values())
    
    def get_service_status(self, service_id):
        """Get the status of a specific service."""
        return self.service_status.get(service_id, "unknown")

    def _show_login_dialog(self):
        """Show the login dialog."""
        try:
            # Check if user is already logged in
            if self.current_user:
                from app.ui.utils.dialogs import show_info
                show_info(
                    parent=self.root,
                    title="Already Logged In",
                    message=f"You are already logged in as {self.current_user.get('username')}."
                )
                return
            
            # Import login dialog
            from app.ui.dialogs.login_dialog import LoginDialog
            
            # Create and show login dialog
            login_dialog = LoginDialog(self.root)
            
            # Check if dialog was created (it might not be if user is already logged in)
            if hasattr(login_dialog, "dialog_created") and not login_dialog.dialog_created:
                return
            
            # Position dialog relative to main window
            if hasattr(login_dialog, "center_dialog"):
                login_dialog.center_dialog()
            
            # Make dialog modal
            login_dialog.grab_set()
            login_dialog.focus_set()
            
        except Exception as e:
            self.logger.error(f"Error showing login dialog: {e}", exc_info=True) 