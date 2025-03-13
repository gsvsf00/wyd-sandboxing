"""
Register Dialog Module

Provides a dialog for user registration.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional, Callable

import threading
from app.utils.logger import LoggerWrapper

logger = LoggerWrapper(name="register_dialog")

class RegisterDialog(ctk.CTkToplevel):
    """Dialog for user registration."""
    
    def __init__(self, parent):
        """Initialize the registration dialog."""
        super().__init__(parent)
        
        self.parent = parent
        self.logger = LoggerWrapper(name="register_dialog")
        self.success = False
        self.user_data = None
        
        # Set dialog properties
        self.title("Register for WydBot")
        self.geometry("400x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create UI
        self._create_widgets()
        
        # Check service status
        self.after(100, self.check_service_status)
        
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Create Account",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))
        
        # Form frame
        self.form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Username
        self.username_label = ctk.CTkLabel(self.form_frame, text="Username")
        self.username_label.grid(row=0, column=0, sticky="w", padx=20, pady=(10, 0))
        
        self.username_entry = ctk.CTkEntry(self.form_frame, width=300)
        self.username_entry.grid(row=1, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")
        
        # Password
        self.password_label = ctk.CTkLabel(self.form_frame, text="Password")
        self.password_label.grid(row=2, column=0, sticky="w", padx=20, pady=(10, 0))
        
        self.password_entry = ctk.CTkEntry(self.form_frame, width=300, show="•")
        self.password_entry.grid(row=3, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")
        
        # Character Name
        self.character_label = ctk.CTkLabel(self.form_frame, text="Character Name")
        self.character_label.grid(row=4, column=0, sticky="w", padx=20, pady=(10, 0))
        
        self.character_entry = ctk.CTkEntry(self.form_frame, width=300)
        self.character_entry.grid(row=5, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")
        
        # Server
        self.server_label = ctk.CTkLabel(self.form_frame, text="Server")
        self.server_label.grid(row=6, column=0, sticky="w", padx=20, pady=(10, 0))
        
        self.server_entry = ctk.CTkEntry(self.form_frame, width=300)
        self.server_entry.grid(row=7, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")
        
        # Error message
        self.error_label = ctk.CTkLabel(
            self.form_frame,
            text="",
            text_color=("red", "#FF5555"),
            wraplength=300
        )
        self.error_label.grid(row=8, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")
        
        # Health check button (for debugging)
        self.health_button = ctk.CTkButton(
            self.form_frame,
            text="Check Connection",
            command=self._check_health,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            width=150,
            height=30
        )
        self.health_button.grid(row=9, column=0, columnspan=2, padx=20, pady=(10, 0))
        
        # Create Account button - Add this directly to the form frame
        self.register_button = ctk.CTkButton(
            self.form_frame,
            text="Create Account",
            command=self._handle_register,
            fg_color=("#4B91F1", "#4B91F1"),
            hover_color=("#3A7EBF", "#3A7EBF"),
            height=40
        )
        self.register_button.grid(row=10, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        
        # Cancel button
        self.cancel_button = ctk.CTkButton(
            self.form_frame,
            text="Cancel",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self.destroy,
            height=40
        )
        self.cancel_button.grid(row=11, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        
        # Login link
        self.login_link = ctk.CTkLabel(
            self.form_frame,
            text="Already have an account? Login",
            cursor="hand2",
            text_color=("#3B8ED0", "#1F6AA5")
        )
        self.login_link.grid(row=12, column=0, columnspan=2, padx=20, pady=(10, 0))
        self.login_link.bind("<Button-1>", self._handle_login)
        
    def _handle_register(self):
        """Handle register button click."""
        try:
            # Get form values
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()
            character_name = self.character_entry.get().strip()
            server = self.server_entry.get().strip()
            
            # Validate inputs
            if not username:
                self._set_error_message("Username is required")
                return
            
            if not password:
                self._set_error_message("Password is required")
                return
            
            # Set registration in progress
            self._set_registration_in_progress(True)
            
            # Get app instance and auth service
            from app.core.app_instance import get_app_instance
            app = get_app_instance()
            
            if not app:
                self._set_error_message("Application instance not available")
                self._set_registration_in_progress(False)
                return
            
            # Check if auth service is ready
            if not hasattr(app, "is_service_ready") or not app.is_service_ready("auth"):
                self._set_error_message("Authentication service is not ready")
                self._set_registration_in_progress(False)
                return
            
            # Get auth service
            auth_service = app.get_service("auth")
            if not auth_service:
                self._set_error_message("Authentication service is not available")
                self._set_registration_in_progress(False)
                return
            
            # Register in a separate thread to avoid UI freezing
            self.after(100, lambda: self._do_register(username, password, character_name, server))
            
        except Exception as e:
            self.logger.error(f"Error handling registration: {e}", exc_info=True)
            self._set_error_message(f"Registration error: {str(e)}")
            self._set_registration_in_progress(False)
        
    def _do_register(self, username, password, character_name, server):
        """Perform registration in a separate thread."""
        try:
            # Call auth service
            success, message, token = self.auth_service.register_user(
                username=username,
                password=password,
                character_name=character_name,
                server=server
            )
            
            if success:
                # Get user data
                _, _, user_data = self.auth_service.authenticate(username, password)
                
                # Schedule UI update on main thread
                self.after(0, lambda: self._handle_register_result(success, message, user_data))
            else:
                # Registration failed
                self.after(0, lambda: self._handle_register_result(success, message, None))
                
        except Exception as e:
            logger.error(f"Registration error: {e}", exc_info=True)
            self.after(0, lambda: self._handle_register_result(False, str(e), None))
            
    def _handle_register_result(self, success, message, user_data):
        """Handle registration result."""
        if success:
            # Store result
            self.success = True
            self.user_data = user_data
            
            # Close dialog
            self.destroy()
        else:
            # Show error message
            self.error_label.configure(text=message)
            
            # Re-enable inputs
            self._set_registration_in_progress(False)
            
    def _set_registration_in_progress(self, in_progress):
        """Set the registration in progress state."""
        try:
            if in_progress:
                self.register_button.configure(state="disabled", text="Registering...")
                if hasattr(self, "progress_bar"):
                    self.progress_bar.grid(row=6, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")
                else:
                    self.progress_bar = ctk.CTkProgressBar(self.form_frame)
                    self.progress_bar.grid(row=6, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")
                    self.progress_bar.configure(mode="indeterminate")
                    self.progress_bar.start()
            else:
                self.register_button.configure(state="normal", text="Create Account")
                if hasattr(self, "progress_bar"):
                    self.progress_bar.stop()
                    self.progress_bar.grid_forget()
        except Exception as e:
            self.logger.error(f"Error setting registration in progress: {e}", exc_info=True)
            
    def _handle_login(self, event=None):
        """Handle login link click."""
        # Close this dialog
        self.destroy()
        
        # Show login dialog
        from app.ui.dialogs.login_dialog import LoginDialog
        login_dialog = LoginDialog(self.master)
        self.master.wait_window(login_dialog)
        
        # Check result
        if login_dialog.success and login_dialog.user_data:
            # Store result
            self.success = True
            self.user_data = login_dialog.user_data 

    def check_service_status(self):
        """Check if the authentication service is available."""
        try:
            from app.core.app_instance import get_app_instance
            app = get_app_instance()
            
            if not app:
                self._set_error_message("Application instance not available")
                return
            
            # Check if auth service is ready
            if not hasattr(app, "is_service_ready") or not app.is_service_ready("auth"):
                self._set_error_message("Authentication service is still initializing")
                
                # Add a progress bar to show initialization status
                if not hasattr(self, "init_progress"):
                    self.init_progress = ctk.CTkProgressBar(self.form_frame)
                    self.init_progress.grid(row=6, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")
                    self.init_progress.configure(mode="indeterminate")
                    self.init_progress.start()
                
                # Check again in 1 second
                self.after(1000, self.check_service_status)
                return
            
            # Auth service is ready, remove progress bar if it exists
            if hasattr(self, "init_progress"):
                self.init_progress.stop()
                self.init_progress.grid_forget()
                self._set_error_message("")  # Clear error message
            
        except Exception as e:
            self.logger.error(f"Error checking service status: {e}", exc_info=True)
            self._set_error_message("Error checking service status") 

    def _check_health(self):
        """Check the health of the auth service."""
        try:
            from app.core.app_instance import get_app_instance
            app = get_app_instance()
            
            if not app:
                self._set_error_message("Application instance not available")
                return
            
            # Check database service
            db_service = app.get_service("database")
            if not db_service:
                self._set_error_message("Database service not available")
                return
            
            # Check database connection
            if not db_service.check_health():
                self._set_error_message("Database connection failed")
                return
            
            # Check auth service
            auth_service = app.get_service("auth")
            if not auth_service:
                self._set_error_message("Authentication service not available")
                return
            
            # All checks passed
            self._set_error_message("Connection successful!", is_error=False)
            
        except Exception as e:
            self.logger.error(f"Error checking health: {e}", exc_info=True)
            self._set_error_message(f"Health check error: {str(e)}") 

    def _set_error_message(self, message, is_error=True):
        """Set the error message."""
        if not hasattr(self, "error_label"):
            return
        
        self.error_label.configure(text=message)
        
        if is_error:
            self.error_label.configure(text_color=("red", "#FF5555"))
        else:
            self.error_label.configure(text_color=("green", "#55FF55")) 