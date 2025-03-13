"""
Admin Panel Frame

Provides administrative functionality for managing users and system settings.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, List, Optional, Tuple
import os
import time
from datetime import datetime, timedelta

from app.ui.base.base_frame import BaseFrame
from app.core.app_instance import get_app_instance
from app.utils.logger import LoggerWrapper

class AdminPanelFrame(BaseFrame):
    """Admin panel frame for administrative tasks."""
    
    def __init__(self, master, **kwargs):
        """Initialize the admin panel frame."""
        super().__init__(master, **kwargs)
        self.logger = LoggerWrapper(name="admin_panel_frame")
        
    def on_init(self):
        """Initialize the admin panel frame."""
        try:
            super().on_init()
            
            # Check if user is admin
            app = get_app_instance()
            if not app or not app.current_user or app.current_user.get("role") != "admin":
                self._show_access_denied()
                return
                
            # Create admin panel content
            self._create_content()
            
        except Exception as e:
            self.logger.error(f"Error initializing admin panel frame: {e}", exc_info=True)
            self._show_error(str(e))
            
    def _show_access_denied(self):
        """Show access denied message."""
        # Clear any existing content
        for widget in self.winfo_children():
            widget.destroy()
            
        # Create access denied message
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        icon_label = ctk.CTkLabel(
            frame,
            text="🔒",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(40, 10))
        
        title = ctk.CTkLabel(
            frame,
            text="Access Denied",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("red", "#FF5555")
        )
        title.pack(pady=(10, 5))
        
        message = ctk.CTkLabel(
            frame,
            text="You do not have permission to access the admin panel.\nPlease contact an administrator if you need access.",
            font=ctk.CTkFont(size=14),
            wraplength=400
        )
        message.pack(pady=10)
        
    def _show_error(self, error_message):
        """Show error message."""
        # Clear any existing content
        for widget in self.winfo_children():
            widget.destroy()
            
        # Create error message
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title = ctk.CTkLabel(
            frame,
            text="Error",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("red", "#FF5555")
        )
        title.pack(pady=(40, 10))
        
        message = ctk.CTkLabel(
            frame,
            text=f"An error occurred: {error_message}",
            font=ctk.CTkFont(size=14),
            wraplength=400
        )
        message.pack(pady=10)
        
        retry_button = ctk.CTkButton(
            frame,
            text="Retry",
            command=self.on_init
        )
        retry_button.pack(pady=20)
        
    def _create_content(self):
        """Create the admin panel content."""
        # Clear any existing content
        for widget in self.winfo_children():
            widget.destroy()
            
        # Create main layout
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True)
        
        # Create header
        self._create_header()
        
        # Create tabview for different admin sections
        self.tabs = ctk.CTkTabview(self.main_frame)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Add tabs
        self.users_tab = self.tabs.add("Users")
        self.system_tab = self.tabs.add("System")
        self.logs_tab = self.tabs.add("Logs")
        self.stats_tab = self.tabs.add("Statistics")
        
        # Create content for each tab
        self._create_users_tab(self.users_tab)
        self._create_system_tab(self.system_tab)
        self._create_logs_tab(self.logs_tab)
        self._create_stats_tab(self.stats_tab)
        
    def _create_header(self):
        """Create the header section."""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(
            header_frame,
            text="Admin Panel",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left", padx=10)
        
        # Add refresh button
        refresh_button = ctk.CTkButton(
            header_frame,
            text="Refresh",
            width=100,
            command=self.refresh
        )
        refresh_button.pack(side="right", padx=10)
        
    def _create_users_tab(self, parent):
        """Create the users tab content."""
        # Create layout
        self.users_frame = ctk.CTkFrame(parent)
        self.users_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create search and filter section
        search_frame = ctk.CTkFrame(self.users_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=(0, 5))
        
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, width=200, textvariable=self.search_var)
        search_entry.pack(side="left", padx=5)
        
        search_button = ctk.CTkButton(
            search_frame,
            text="Search",
            width=80,
            command=self._search_users
        )
        search_button.pack(side="left", padx=5)
        
        # Add user button
        add_user_button = ctk.CTkButton(
            search_frame,
            text="Add User",
            width=100,
            command=self._add_user
        )
        add_user_button.pack(side="right", padx=5)
        
        # Create users table
        table_frame = ctk.CTkFrame(self.users_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Table headers
        headers_frame = ctk.CTkFrame(table_frame, fg_color=("gray85", "gray25"))
        headers_frame.pack(fill="x", padx=5, pady=5)
        
        headers = ["Username", "Role", "Status", "Last Login", "Actions"]
        widths = [0.2, 0.15, 0.15, 0.2, 0.3]
        
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(weight="bold")
            )
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            headers_frame.grid_columnconfigure(i, weight=int(widths[i] * 100))
            
        # Create scrollable frame for users
        self.users_scrollable = ctk.CTkScrollableFrame(table_frame)
        self.users_scrollable.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure columns
        for i, width in enumerate(widths):
            self.users_scrollable.grid_columnconfigure(i, weight=int(width * 100))
            
        # Load users
        self._load_users()
        
    def _create_system_tab(self, parent):
        """Create the system tab content."""
        # Create layout
        self.system_frame = ctk.CTkFrame(parent)
        self.system_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create sections
        sections = [
            ("System Information", self._create_system_info_section),
            ("Database", self._create_database_section),
            ("Services", self._create_services_section),
            ("Maintenance", self._create_maintenance_section)
        ]
        
        for i, (title, create_func) in enumerate(sections):
            section_frame = ctk.CTkFrame(self.system_frame)
            section_frame.pack(fill="x", padx=10, pady=10)
            
            section_title = ctk.CTkLabel(
                section_frame,
                text=title,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            section_title.pack(anchor="w", padx=10, pady=(10, 5))
            
            # Create section content
            create_func(section_frame)
            
    def _create_system_info_section(self, parent):
        """Create system information section."""
        try:
            info_frame = ctk.CTkFrame(parent, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=10)
            
            # Create grid layout
            info_frame.columnconfigure(0, weight=0)  # Label column
            info_frame.columnconfigure(1, weight=1)  # Value column
            
            # Get app instance
            app = get_app_instance()
            
            # Application version
            row = 0
            ctk.CTkLabel(
                info_frame,
                text="Application Version:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            ctk.CTkLabel(
                info_frame,
                text="1.0.0",
                font=ctk.CTkFont(size=14)
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            # Uptime
            row += 1
            ctk.CTkLabel(
                info_frame,
                text="Uptime:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            uptime = self._format_uptime()
            ctk.CTkLabel(
                info_frame,
                text=uptime,
                font=ctk.CTkFont(size=14)
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            # Python version
            row += 1
            ctk.CTkLabel(
                info_frame,
                text="Python Version:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            ctk.CTkLabel(
                info_frame,
                text=python_version,
                font=ctk.CTkFont(size=14)
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            # OS info
            row += 1
            ctk.CTkLabel(
                info_frame,
                text="Operating System:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            import platform
            os_info = f"{platform.system()} {platform.release()}"
            ctk.CTkLabel(
                info_frame,
                text=os_info,
                font=ctk.CTkFont(size=14)
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
        except Exception as e:
            self.logger.error(f"Error creating system info section: {e}", exc_info=True)
            
    def _create_database_section(self, parent):
        """Create database information section."""
        try:
            db_frame = ctk.CTkFrame(parent, fg_color="transparent")
            db_frame.pack(fill="x", padx=10, pady=10)
            
            # Create grid layout
            db_frame.columnconfigure(0, weight=0)  # Label column
            db_frame.columnconfigure(1, weight=1)  # Value column
            
            # Get app instance
            app = get_app_instance()
            if not app:
                return
                
            # Get database service
            db_service = app.get_service("database")
            if not db_service:
                ctk.CTkLabel(
                    db_frame,
                    text="Database service not available",
                    font=ctk.CTkFont(size=14),
                    text_color=("red", "#F44336")
                ).grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
                return
                
            # Database status
            row = 0
            ctk.CTkLabel(
                db_frame,
                text="Status:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            is_connected = db_service.check_health() if hasattr(db_service, "check_health") else False
            status_text = "Connected" if is_connected else "Disconnected"
            status_color = ("green", "#4CAF50") if is_connected else ("red", "#F44336")
            
            ctk.CTkLabel(
                db_frame,
                text=status_text,
                font=ctk.CTkFont(size=14),
                text_color=status_color
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            # Database type
            row += 1
            ctk.CTkLabel(
                db_frame,
                text="Type:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            db_type = "MongoDB" if not getattr(db_service, "use_mock_db", True) else "Mock Database"
            ctk.CTkLabel(
                db_frame,
                text=db_type,
                font=ctk.CTkFont(size=14)
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            # Database name
            row += 1
            ctk.CTkLabel(
                db_frame,
                text="Database:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            db_name = getattr(db_service, "database_name", "Unknown")
            ctk.CTkLabel(
                db_frame,
                text=db_name,
                font=ctk.CTkFont(size=14)
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            # Add reconnect button
            row += 1
            reconnect_button = ctk.CTkButton(
                db_frame,
                text="Reconnect",
                width=100,
                command=self._reconnect_database
            )
            reconnect_button.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="w")
            
        except Exception as e:
            self.logger.error(f"Error creating database section: {e}", exc_info=True)
            
    def _reconnect_database(self):
        """Reconnect to the database."""
        try:
            # Get app instance
            app = get_app_instance()
            if not app:
                return
                
            # Get database service
            db_service = app.get_service("database")
            if not db_service:
                return
                
            # Reconnect
            if hasattr(db_service, "reconnect"):
                success = db_service.reconnect()
                
                # Show result
                from app.ui.utils.dialogs import show_info, show_error
                if success:
                    show_info(self, "Database", "Successfully reconnected to the database.")
                else:
                    show_error(self, "Database", "Failed to reconnect to the database.")
                    
                # Refresh UI
                self.refresh()
                
        except Exception as e:
            self.logger.error(f"Error reconnecting to database: {e}", exc_info=True)
            
    def _create_services_section(self, parent):
        """Create services information section."""
        try:
            services_frame = ctk.CTkFrame(parent, fg_color="transparent")
            services_frame.pack(fill="x", padx=10, pady=10)
            
            # Get app instance
            app = get_app_instance()
            if not app:
                return
                
            # Check if service status is available
            if not hasattr(app, "service_status"):
                ctk.CTkLabel(
                    services_frame,
                    text="Service status information not available",
                    font=ctk.CTkFont(size=14)
                ).pack(padx=10, pady=5, anchor="w")
                return
                
            # Create a table for services
            for i, (service_id, status) in enumerate(app.service_status.items()):
                # Create a frame for each service
                service_row = ctk.CTkFrame(services_frame, fg_color="transparent")
                service_row.pack(fill="x", padx=10, pady=2)
                
                # Service name
                ctk.CTkLabel(
                    service_row,
                    text=service_id,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    width=150
                ).pack(side="left", padx=5)
                
                # Service status
                status_color = ("green", "#4CAF50") if status == "ready" else \
                              ("red", "#F44336") if status == "failed" else \
                              ("orange", "#FF9800")
                              
                ctk.CTkLabel(
                    service_row,
                    text=status,
                    font=ctk.CTkFont(size=14),
                    text_color=status_color
                ).pack(side="left", padx=5)
                
        except Exception as e:
            self.logger.error(f"Error creating services section: {e}", exc_info=True)
            
    def _create_maintenance_section(self, parent):
        """Create maintenance section."""
        try:
            maintenance_frame = ctk.CTkFrame(parent, fg_color="transparent")
            maintenance_frame.pack(fill="x", padx=10, pady=10)
            
            # Create buttons for maintenance tasks
            buttons = [
                ("Clear Cache", self._clear_cache),
                ("Backup Database", self._backup_database),
                ("Restore Database", self._restore_database),
                ("Reset Settings", self._reset_settings)
            ]
            
            for i, (text, command) in enumerate(buttons):
                button = ctk.CTkButton(
                    maintenance_frame,
                    text=text,
                    width=150,
                    command=command
                )
                button.pack(side="left", padx=10, pady=10)
                
        except Exception as e:
            self.logger.error(f"Error creating maintenance section: {e}", exc_info=True)
            
    def _clear_cache(self):
        """Clear application cache."""
        try:
            # Show confirmation dialog
            from app.ui.utils.dialogs import show_question, show_info
            if show_question(self, "Clear Cache", "Are you sure you want to clear the application cache?"):
                # Clear cache directory
                import shutil
                import os
                
                cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "cache")
                
                if os.path.exists(cache_dir):
                    # Remove all files in the cache directory
                    for filename in os.listdir(cache_dir):
                        file_path = os.path.join(cache_dir, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                        except Exception as e:
                            self.logger.error(f"Error deleting {file_path}: {e}")
                            
                    show_info(self, "Cache Cleared", "Application cache has been cleared successfully.")
                else:
                    show_info(self, "Cache", "No cache directory found.")
                    
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}", exc_info=True)
            
    def _backup_database(self):
        """Backup the database."""
        try:
            # Show info dialog
            from app.ui.utils.dialogs import show_info
            show_info(self, "Backup Database", "This feature is not yet implemented.")
            
        except Exception as e:
            self.logger.error(f"Error backing up database: {e}", exc_info=True)
            
    def _restore_database(self):
        """Restore the database from backup."""
        try:
            # Show info dialog
            from app.ui.utils.dialogs import show_info
            show_info(self, "Restore Database", "This feature is not yet implemented.")
            
        except Exception as e:
            self.logger.error(f"Error restoring database: {e}", exc_info=True)
            
    def _reset_settings(self):
        """Reset application settings."""
        try:
            # Show confirmation dialog
            from app.ui.utils.dialogs import show_question, show_info
            if show_question(self, "Reset Settings", "Are you sure you want to reset all application settings to default?"):
                # Get app instance
                app = get_app_instance()
                if not app:
                    return
                    
                # Get settings service
                settings_service = app.get_service("settings")
                if not settings_service:
                    show_info(self, "Settings", "Settings service not available.")
                    return
                    
                # Reset settings
                if hasattr(settings_service, "reset"):
                    settings_service.reset()
                    show_info(self, "Settings Reset", "Application settings have been reset to default values.")
                    
        except Exception as e:
            self.logger.error(f"Error resetting settings: {e}", exc_info=True)
            
    def _create_stats_tab(self, parent):
        """Create the statistics tab content."""
        try:
            stats_frame = ctk.CTkFrame(parent)
            stats_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create a message that stats are not yet implemented
            message = ctk.CTkLabel(
                stats_frame,
                text="Statistics functionality is not yet implemented.",
                font=ctk.CTkFont(size=16)
            )
            message.pack(pady=50)
            
        except Exception as e:
            self.logger.error(f"Error creating stats tab: {e}", exc_info=True)
            
    def _create_logs_tab(self, parent):
        """Create the logs tab content."""
        # Create layout
        self.logs_frame = ctk.CTkFrame(parent)
        self.logs_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create controls
        controls_frame = ctk.CTkFrame(self.logs_frame, fg_color="transparent")
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        # Log file selector
        log_label = ctk.CTkLabel(controls_frame, text="Log File:")
        log_label.pack(side="left", padx=(0, 5))
        
        self.log_file_var = tk.StringVar(value="wydbot.log")
        log_files = ["wydbot.log", "error.log", "debug.log"]
        log_dropdown = ctk.CTkComboBox(
            controls_frame,
            values=log_files,
            variable=self.log_file_var,
            width=150,
            command=self._load_log_file
        )
        log_dropdown.pack(side="left", padx=5)
        
        # Log level filter
        level_label = ctk.CTkLabel(controls_frame, text="Level:")
        level_label.pack(side="left", padx=(20, 5))
        
        self.log_level_var = tk.StringVar(value="All")
        log_levels = ["All", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level_dropdown = ctk.CTkComboBox(
            controls_frame,
            values=log_levels,
            variable=self.log_level_var,
            width=100,
            command=self._filter_logs
        )
        level_dropdown.pack(side="left", padx=5)
        
        # Refresh button
        refresh_button = ctk.CTkButton(
            controls_frame,
            text="Refresh",
            width=80
        )
        refresh_button.pack(side="left", padx=5)
        
    def _format_uptime(self):
        """Format the application uptime."""
        # Get app instance
        app = get_app_instance()
        
        if not app or not hasattr(app, "startup_timestamp"):
            return "Unknown"
            
        # Calculate uptime
        uptime_seconds = time.time() - app.startup_timestamp
        
        # Format uptime
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{int(days)}d {int(hours)}h {int(minutes)}m"
        elif hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
            
    def refresh(self):
        """Refresh the admin panel."""
        # Reload users
        if hasattr(self, "users_scrollable"):
            self._load_users()
            
        # Reload logs
        if hasattr(self, "log_text"):
            self._load_log_file()
            
        # Refresh system info
        self._create_content() 

    def _search_users(self):
        """Search users based on the search input."""
        try:
            search_term = self.search_var.get().strip().lower()
            self.logger.debug(f"Searching users with term: {search_term}")
            
            # Clear existing user rows
            for widget in self.users_scrollable.winfo_children():
                widget.destroy()
                
            # Get app instance
            app = get_app_instance()
            if not app:
                return
                
            # Get database service
            db_service = app.get_service("database")
            if not db_service:
                self.logger.error("Database service not available")
                return
                
            # Query users from database
            query = {}
            if search_term:
                # Case-insensitive search on username, email, or role
                query = {
                    "$or": [
                        {"username": {"$regex": search_term, "$options": "i"}},
                        {"email": {"$regex": search_term, "$options": "i"}},
                        {"role": {"$regex": search_term, "$options": "i"}}
                    ]
                }
                
            users = db_service.find("users", query)
            
            # Display users
            if not users:
                # Show no results message
                no_results = ctk.CTkLabel(
                    self.users_scrollable,
                    text="No users found",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                no_results.grid(row=0, column=0, columnspan=5, padx=20, pady=20)
                return
                
            # Display users
            self._display_users(users)
            
        except Exception as e:
            self.logger.error(f"Error searching users: {e}", exc_info=True)
            
    def _display_users(self, users):
        """Display users in the table."""
        try:
            # Display each user
            for i, user in enumerate(users):
                # Username
                username = ctk.CTkLabel(
                    self.users_scrollable,
                    text=user.get("username", ""),
                    font=ctk.CTkFont(size=14)
                )
                username.grid(row=i, column=0, padx=5, pady=5, sticky="w")
                
                # Role
                role = ctk.CTkLabel(
                    self.users_scrollable,
                    text=user.get("role", "user"),
                    font=ctk.CTkFont(size=14)
                )
                role.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                
                # Status
                status = ctk.CTkLabel(
                    self.users_scrollable,
                    text=user.get("status", "active"),
                    font=ctk.CTkFont(size=14)
                )
                status.grid(row=i, column=2, padx=5, pady=5, sticky="w")
                
                # Last login
                last_login = ctk.CTkLabel(
                    self.users_scrollable,
                    text=user.get("last_login", "Never"),
                    font=ctk.CTkFont(size=14)
                )
                last_login.grid(row=i, column=3, padx=5, pady=5, sticky="w")
                
                # Actions
                actions_frame = ctk.CTkFrame(self.users_scrollable, fg_color="transparent")
                actions_frame.grid(row=i, column=4, padx=5, pady=5, sticky="e")
                
                # Edit button
                edit_button = ctk.CTkButton(
                    actions_frame,
                    text="Edit",
                    width=60,
                    height=25,
                    command=lambda u=user.get("username", ""): self._edit_user(u)
                )
                edit_button.pack(side="left", padx=2)
                
                # Delete button
                delete_button = ctk.CTkButton(
                    actions_frame,
                    text="Delete",
                    width=60,
                    height=25,
                    fg_color=("red", "#F44336"),
                    hover_color=("darkred", "#D32F2F"),
                    command=lambda u=user.get("username", ""): self._delete_user(u)
                )
                delete_button.pack(side="left", padx=2)
                
        except Exception as e:
            self.logger.error(f"Error displaying users: {e}", exc_info=True)
            
    def _add_user(self):
        """Show dialog to add a new user."""
        try:
            # This would typically show a dialog to add a new user
            self.logger.debug("Add user button clicked")
            
            # For now, just show a message
            from app.ui.utils.dialogs import show_info
            show_info(self, "Add User", "This feature is not yet implemented.")
            
        except Exception as e:
            self.logger.error(f"Error adding user: {e}", exc_info=True)
            
    def _edit_user(self, username):
        """Show dialog to edit a user."""
        try:
            self.logger.debug(f"Edit user button clicked for {username}")
            
            # For now, just show a message
            from app.ui.utils.dialogs import show_info
            show_info(self, "Edit User", f"Editing user {username} is not yet implemented.")
            
        except Exception as e:
            self.logger.error(f"Error editing user: {e}", exc_info=True)
            
    def _delete_user(self, username):
        """Show confirmation dialog to delete a user."""
        try:
            self.logger.debug(f"Delete user button clicked for {username}")
            
            # For now, just show a message
            from app.ui.utils.dialogs import show_question
            if show_question(self, "Delete User", f"Are you sure you want to delete user {username}?"):
                self.logger.info(f"User confirmed deletion of {username}")
                # Implement actual deletion here
                
        except Exception as e:
            self.logger.error(f"Error deleting user: {e}", exc_info=True)
            
    def _load_users(self):
        """Load users from the database."""
        try:
            # Get app instance
            app = get_app_instance()
            if not app:
                return
                
            # Get database service
            db_service = app.get_service("database")
            if not db_service:
                self.logger.error("Database service not available")
                return
                
            # Query all users
            users = db_service.find("users", {})
            
            # Display users
            self._display_users(users)
            
        except Exception as e:
            self.logger.error(f"Error loading users: {e}", exc_info=True)
            
    def _load_log_file(self, file_name=None):
        """Load and display log file contents."""
        try:
            if file_name is None:
                file_name = self.log_file_var.get()
                
            # Get log directory
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "logs")
            log_file = os.path.join(log_dir, file_name)
            
            # Check if log file exists
            if not os.path.exists(log_file):
                if not hasattr(self, "log_text"):
                    self.log_text = ctk.CTkTextbox(self.logs_frame)
                    self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
                    
                self.log_text.delete("1.0", "end")
                self.log_text.insert("1.0", f"Log file not found: {log_file}")
                return
                
            # Read log file
            with open(log_file, "r") as f:
                log_content = f.read()
                
            # Filter by log level if needed
            level = self.log_level_var.get()
            if level != "All":
                filtered_lines = []
                for line in log_content.splitlines():
                    if f"[{level}]" in line:
                        filtered_lines.append(line)
                log_content = "\n".join(filtered_lines)
                
            # Create or update text widget
            if not hasattr(self, "log_text"):
                self.log_text = ctk.CTkTextbox(self.logs_frame)
                self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
                
            self.log_text.delete("1.0", "end")
            self.log_text.insert("1.0", log_content)
            
            # Scroll to end
            self.log_text.see("end")
            
        except Exception as e:
            self.logger.error(f"Error loading log file: {e}", exc_info=True)
            
    def _filter_logs(self, level=None):
        """Filter logs by level."""
        self._load_log_file() 