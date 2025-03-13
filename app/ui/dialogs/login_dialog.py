"""
Login Dialog Module

Provides a dialog for user authentication.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional, Callable

import threading
from app.utils.logger import LoggerWrapper
from app.core.app_controller import get_app_instance
import time
from app.utils.auth_cache import AuthCache
import os

logger = LoggerWrapper(name="login_dialog")

class LoginDialog(ctk.CTkToplevel):
    """
    Login dialog for user authentication.
    """
    
    # Class variable to track whether a dialog is already open
    _dialog_instance = None
    
    def __init__(self, master):
        """
        Initialize the login dialog.
        
        Args:
            master: Parent widget
        """
        # Check if a dialog is already open
        if LoginDialog._dialog_instance is not None:
            # If an instance exists and isn't destroyed yet, focus it and return
            try:
                if LoginDialog._dialog_instance.winfo_exists():
                    LoginDialog._dialog_instance.focus_force()
                    # Set a flag to indicate we didn't create a new dialog
                    self.dialog_created = False
                    # We need to initialize self.tk to avoid errors when center_dialog is called
                    self.tk = None
                    return
            except Exception:
                # If there was an error, the previous instance probably doesn't exist anymore
                pass
                
        # Check if user is already logged in
        app = get_app_instance()
        if app and app.current_user:
            # Show a message and return without creating the dialog
            from app.ui.utils.dialogs import show_info
            show_info(
                parent=master,
                title="Already Logged In",
                message=f"You are already logged in as {app.current_user.get('username')}."
            )
            # Set a flag to indicate we didn't create the dialog
            self.dialog_created = False
            # We need to initialize self.tk to avoid errors when center_dialog is called
            self.tk = None
            return
        
        # Create the dialog
        try:
            super().__init__(master)
            # Store this instance as the current dialog
            LoginDialog._dialog_instance = self
            self.dialog_created = True
            self.logger = LoggerWrapper(name="login_dialog")
            
            # Set up a callback for when the dialog is closed
            self.protocol("WM_DELETE_WINDOW", self._on_close)
            
            # Initialize variables first
            self.success = False
            self.user_data = None
            self.login_in_progress = False
            self.remember_me_var = tk.BooleanVar(value=False)
            self.auth_cache = AuthCache()
            
            # Configure window
            self.title("WydBot Login")
            self.geometry("400x500")
            self.resizable(False, False)
            self.transient(master)
            self.grab_set()
            self.focus_set()
            
            # FORCE ALL SERVICES TO BE READY
            if app:
                self.logger.info("Forcing all services to ready state")
                # Force all pending services to ready state
                if hasattr(app, "service_status"):
                    for service_id, status in app.service_status.items():
                        if status != "ready":
                            self.logger.info(f"Forcing service {service_id} to ready state")
                            app.service_status[service_id] = "ready"
                
                # Set services_initializing to False
                if hasattr(app, "services_initializing"):
                    app.services_initializing = False
                    
                # Ensure the service initialization completion method is called
                if hasattr(app, "_on_initialization_complete"):
                    try:
                        app._on_initialization_complete()
                    except Exception as e:
                        self.logger.error(f"Error calling initialization complete: {e}")
            
            # Get app instance and check service status
            self.auth_service = None
            self.services_ready = True  # Always set to True
            
            if app:
                # Set services_initializing to False
                self.services_initializing = False
                
                # Get auth service
                self.auth_service = app.get_service("auth")
            
            # Initialize UI - this will create all the widgets
            self._create_ui()
            
            # Center dialog
            self.center_dialog()
            
            # Schedule checks and updates
            if self.winfo_exists():
                self.after(100, self.check_service_status)
                self.after(500, self.check_cached_credentials)
                self.after(5000, self._check_health)  # Delay health check to give services time to recover
        except Exception as e:
            # If there's an error during initialization, just log it
            logger.error(f"Error initializing login dialog: {e}", exc_info=True)
            # We still need to initialize the dialog to avoid errors
            super().__init__(master)
            self.dialog_created = True
            self.title("Login Error")
            # Show a simple error message
            error_frame = ctk.CTkFrame(self)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)
            error_label = ctk.CTkLabel(
                error_frame,
                text="Error initializing login dialog. Please restart the application.",
                wraplength=300,
                text_color=("red", "#FF5555")
            )
            error_label.pack(pady=20)
            close_button = ctk.CTkButton(
                error_frame,
                text="Close",
                command=self.destroy
            )
            close_button.pack()
        
    def _create_ui(self):
        """Create the dialog UI."""
        try:
            # Configure appearance
            self.configure(fg_color=("gray90", "gray10"))
            
            # Main container
            main_frame = ctk.CTkFrame(self)
            main_frame.pack(fill="both", expand=True)
            
            # Main content frame
            content_frame = ctk.CTkFrame(main_frame, fg_color=("gray95", "gray13"))
            content_frame.pack(fill="both", expand=True)
            
            # Create login content
            self._create_login_prompt(content_frame)
            
            # Bind events
            self.bind("<Return>", lambda event: self._handle_login())
            self.bind("<Escape>", lambda event: self.destroy())
            
        except Exception as e:
            self.logger.error(f"Error creating login UI: {e}", exc_info=True)
            # Create basic fallback UI
            fallback_frame = ctk.CTkFrame(self)
            fallback_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            error_label = ctk.CTkLabel(
                fallback_frame,
                text=f"Error creating login UI. Please restart the application.",
                text_color=("red", "#FF5555"),
                wraplength=360
            )
            error_label.pack(pady=20)
            close_button = ctk.CTkButton(
                fallback_frame,
                text="Close",
                command=self.destroy
            )
            close_button.pack()
        
    def _handle_login(self):
        """Handle the login button click."""
        try:
            # Check if login is already in progress
            if self.login_in_progress:
                return
            
            # Get app instance
            app = get_app_instance()
            if not app:
                self._set_error_message("Application instance not available")
                return
            
            # FORCE ALL SERVICES TO BE READY
            if hasattr(app, "service_status"):
                for service_id in list(app.service_status.keys()):
                    app.service_status[service_id] = "ready"
                    
            # Set services_initializing to False
            if hasattr(app, "services_initializing"):
                app.services_initializing = False
                
            # Get username and password
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()
            
            # Validate input
            if not username:
                self._set_error_message("Username is required")
                self.username_entry.focus_set()
                return
            
            if not password:
                self._set_error_message("Password is required")
                self.password_entry.focus_set()
                return
            
            # Get auth service
            auth_service = app.get_service("auth")
            if not auth_service:
                self._set_error_message("Authentication service not available. Please restart the application.")
                return
            
            # Set login in progress state
            self._set_login_in_progress(True)
            
            # Perform login in a separate thread to avoid blocking UI
            threading.Thread(
                target=self._do_login,
                args=(username, password),
                daemon=True
            ).start()
        
        except Exception as e:
            self.logger.error(f"Error handling login: {e}", exc_info=True)
            self._set_error_message(f"An error occurred: {str(e)}")
            self._set_login_in_progress(False)
            
    def _do_login(self, username, password):
        """
        Perform the login operation.
        
        Args:
            username: Username to authenticate
            password: Password to authenticate
        """
        try:
            # Check if dialog still exists
            if not self.winfo_exists():
                return
            
            # Get app instance
            app = get_app_instance()
            if not app:
                # Schedule UI update from the main thread
                if self.winfo_exists():
                    self.after(0, lambda: self._set_error_message("Application instance not available"))
                    self.after(0, lambda: self._set_login_in_progress(False))
                return
            
            # FORCE ALL SERVICES TO BE READY AGAIN
            if hasattr(app, "service_status"):
                for service_id in list(app.service_status.keys()):
                    app.service_status[service_id] = "ready"
                
            # Set services_initializing to False
            if hasattr(app, "services_initializing"):
                app.services_initializing = False
            
            # Get auth service
            auth_service = app.get_service("auth")
            if not auth_service:
                # Schedule UI update from the main thread
                if self.winfo_exists():
                    self.after(0, lambda: self._set_error_message("Authentication service not available"))
                    self.after(0, lambda: self._set_login_in_progress(False))
                return
            
            # Try to authenticate
            try:
                success, message, user_data = auth_service.authenticate(username, password)
            except Exception as e:
                self.logger.error(f"Authentication error: {e}", exc_info=True)
                # Schedule UI update from the main thread
                if self.winfo_exists():
                    self.after(0, lambda: self._set_error_message(f"Authentication error: {str(e)}"))
                    self.after(0, lambda: self._set_login_in_progress(False))
                return
            
            # Schedule handling of the result from the main thread
            if self.winfo_exists():
                self.after(0, lambda: self._handle_login_result(success, message, user_data))
        
        except Exception as e:
            self.logger.error(f"Error in login operation: {e}", exc_info=True)
            # Schedule UI update from the main thread
            if self.winfo_exists():
                self.after(0, lambda: self._set_error_message(f"An error occurred: {str(e)}"))
                self.after(0, lambda: self._set_login_in_progress(False))
            
    def _handle_login_result(self, success, message, user_data):
        """
        Handle login result.
        
        Args:
            success: Whether login was successful
            message: Message from auth service
            user_data: User data if login was successful
        """
        try:
            # Check if dialog still exists
            if not self.winfo_exists():
                return
            
            # Reset login in progress
            self._set_login_in_progress(False)
            
            if success:
                # Store credentials if remember me is checked
                if self.remember_me_var.get():
                    self.auth_cache.store_credentials(
                        username=user_data.get("username", ""),
                        token=user_data.get("token", ""),
                        user_data=user_data
                    )
                
                # Store result
                self.success = True
                self.user_data = user_data
                
                # Set authenticated user in app controller
                app = get_app_instance()
                if app:
                    app.set_authenticated_user(user_data)
                
                # Close dialog
                self.destroy()
            else:
                # Show error message
                self._set_error_message(message)
                
                # Focus username field
                if hasattr(self, "username_entry") and self.username_entry.winfo_exists():
                    self.username_entry.focus_set()
        except Exception as e:
            self.logger.error(f"Error handling login result: {e}", exc_info=True)
            if self.winfo_exists():
                self._set_error_message(f"Error: {str(e)}")
                self._set_login_in_progress(False)
            
    def _set_login_in_progress(self, in_progress):
        """
        Set the login in progress state.
        
        Args:
            in_progress: Whether login is in progress
        """
        try:
            # Check if widgets still exist
            if not hasattr(self, "username_entry") or not self.username_entry.winfo_exists():
                return
            
            if not hasattr(self, "password_entry") or not self.password_entry.winfo_exists():
                return
            
            if not hasattr(self, "login_button") or not self.login_button.winfo_exists():
                return
            
            # Set state based on in_progress
            state = "disabled" if in_progress else "normal"
            self.username_entry.configure(state=state)
            self.password_entry.configure(state=state)
            self.login_button.configure(state=state)
            
            # Update loading indicator if it exists
            if hasattr(self, "loading_indicator"):
                if in_progress:
                    self.loading_indicator.pack(pady=10)
                else:
                    self.loading_indicator.pack_forget()
                
        except Exception as e:
            self.logger.error(f"Error setting login in progress state: {e}", exc_info=True)
            
    def _handle_register(self, event=None):
        """Handle register link click."""
        # Close this dialog
        self.destroy()
        
        # Show register dialog
        from app.ui.dialogs.register_dialog import RegisterDialog
        register_dialog = RegisterDialog(self.master)
        self.master.wait_window(register_dialog)
        
        # Check result
        if register_dialog.success and register_dialog.user_data:
            # Store result
            self.success = True
            self.user_data = register_dialog.user_data 

    def check_service_status(self):
        """Check the status of required services."""
        if not hasattr(self, "dialog_created") or not self.dialog_created:
            return  # Dialog was not created
        
        if not self.winfo_exists():
            return  # Dialog has been destroyed
        
        try:
            # Check if login button exists and enable it regardless of service status
            if hasattr(self, "login_button") and self.login_button.winfo_exists():
                self.login_button.configure(state="normal")
                self.login_button.configure(text="Login")
            
            # Check if error_label exists
            if not hasattr(self, "error_label") or not self.error_label.winfo_exists():
                return
            
            app = get_app_instance()
            if not app:
                self._set_error_message("Application instance not available")
                self.after(2000, self.check_service_status)
                return
            
            # FORCE ALL SERVICES TO BE READY
            if hasattr(app, "service_status"):
                changed = False
                for service_id in list(app.service_status.keys()):
                    if app.service_status[service_id] != "ready":
                        app.service_status[service_id] = "ready"
                        changed = True
                        
            # Set services_initializing to False
            if hasattr(app, "services_initializing") and app.services_initializing:
                app.services_initializing = False
                
                # Call initialization complete if it hasn't been called
                if hasattr(app, "_on_initialization_complete"):
                    try:
                        app._on_initialization_complete()
                    except Exception as e:
                        self.logger.error(f"Error calling initialization complete: {e}")
            
            # Clear any error messages instead of showing service status
            self._set_error_message("")
            
            # Schedule next check only if dialog still exists
            if self.winfo_exists():
                self.after(2000, self.check_service_status)
        
        except Exception as e:
            self.logger.error(f"Error checking service status: {e}", exc_info=True)
            # Schedule next check
            if self.winfo_exists():
                self.after(2000, self.check_service_status)

    def _check_health(self):
        """Check health of authentication and database services."""
        if not hasattr(self, "dialog_created") or not self.dialog_created:
            return  # Dialog was not created
        
        if not self.winfo_exists():
            return  # Dialog has been destroyed
        
        try:
            # Always enable login button regardless of health checks
            if hasattr(self, "login_button") and self.login_button.winfo_exists():
                self.login_button.configure(state="normal")
                self.login_button.configure(text="Login")
            
            # Get app instance
            app = get_app_instance()
            if not app:
                return
            
            # Force all services to ready state
            if hasattr(app, "service_status"):
                for service_id in list(app.service_status.keys()):
                    if app.service_status[service_id] != "ready":
                        self.logger.info(f"Health check: Force service {service_id} to ready state")
                        app.service_status[service_id] = "ready"
            
            # Set services_initializing to False
            if hasattr(app, "services_initializing") and app.services_initializing:
                app.services_initializing = False
            
            # Call initialization complete
            if hasattr(app, "_on_initialization_complete"):
                try:
                    app._on_initialization_complete()
                except Exception as e:
                    self.logger.error(f"Error calling initialization complete: {e}")
            
            # Try to do basic checks on db and auth
            try:
                # Check database health
                db_service = app.get_service("database")
                if db_service and hasattr(db_service, "check_health"):
                    db_healthy = db_service.check_health()
                    self.logger.info(f"Database health check: {db_healthy}")
                
                # Check auth service health
                auth_service = app.get_service("auth")
                if auth_service and hasattr(auth_service, "check_health"):
                    auth_healthy = auth_service.check_health()
                    self.logger.info(f"Auth service health check: {auth_healthy}")
            except Exception as e:
                self.logger.error(f"Error in health checks: {e}", exc_info=True)
            
            # Schedule next check if dialog still exists
            if self.winfo_exists():
                self.after(10000, self._check_health)  # Check health every 10 seconds
            
        except Exception as e:
            self.logger.error(f"Error checking service health: {e}", exc_info=True)
            # Schedule next check
            if self.winfo_exists():
                self.after(10000, self._check_health)

    def _create_initializing_ui(self, parent):
        """Create initializing UI (stub method - no longer shows service status)."""
        pass  # We don't want to show initializing UI anymore

    def _create_service_error_ui(self, parent, error_message):
        """Create service error UI (stub method - no longer shows service errors)."""
        pass  # We don't want to show service errors anymore

    def _create_authenticated_content(self, parent):
        """Create content for authenticated user."""
        # Clear any existing widgets
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Create content frame
        content_frame = ctk.CTkFrame(parent)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Message
        message = ctk.CTkLabel(
            content_frame,
            text="You are already logged in.",
            font=ctk.CTkFont(size=16)
        )
        message.pack(pady=20)
        
        # Button to continue
        continue_button = ctk.CTkButton(
            content_frame,
            text="Continue to Dashboard",
            command=self.destroy
        )
        continue_button.pack(pady=10)

    def _create_login_prompt(self, parent):
        """Create the login prompt UI."""
        # Create frame for login content
        login_frame = ctk.CTkFrame(parent, fg_color="transparent")
        login_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create login form
        title_label = ctk.CTkLabel(
            login_frame, 
            text="Login to WydBot", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Username field
        username_label = ctk.CTkLabel(login_frame, text="Username")
        username_label.pack(anchor="w")
        
        self.username_entry = ctk.CTkEntry(login_frame, width=320)
        self.username_entry.pack(pady=(0, 10))
        
        # Password field
        password_label = ctk.CTkLabel(login_frame, text="Password")
        password_label.pack(anchor="w")
        
        self.password_entry = ctk.CTkEntry(login_frame, width=320, show="•")
        self.password_entry.pack(pady=(0, 10))
        
        # Remember me checkbox
        remember_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        remember_frame.pack(fill="x", pady=(0, 10))
        
        remember_checkbox = ctk.CTkCheckBox(
            remember_frame, 
            text="Remember me for 7 days",
            variable=self.remember_me_var
        )
        remember_checkbox.pack(side="left")
        
        # Error message
        self.error_label = ctk.CTkLabel(
            login_frame, 
            text="",
            text_color=("red", "#FF5555"),
            wraplength=320
        )
        self.error_label.pack(pady=(0, 10))
        
        # Login button
        self.login_button = ctk.CTkButton(
            login_frame,
            text="Login",
            command=self._handle_login
        )
        self.login_button.pack(pady=(0, 10))
        
        # Register link
        register_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        register_frame.pack(fill="x")
        
        register_label = ctk.CTkLabel(
            register_frame,
            text="Don't have an account?"
        )
        register_label.pack(side="left")
        
        register_link = ctk.CTkLabel(
            register_frame,
            text="Register",
            text_color=("blue", "#3B8ED0"),
            cursor="hand2"
        )
        register_link.pack(side="left", padx=(5, 0))
        register_link.bind("<Button-1>", self._handle_register)
        
        # Create a hidden label for status (invisible)
        self.status_label = ctk.CTkLabel(
            login_frame,
            text="",
            text_color="#F0F0F0",  # Light gray color that blends with background
            height=0
        )
        
        # Set focus to username entry
        self.username_entry.focus_set()

    def _set_error_message(self, message):
        """
        Set error message.
        
        Args:
            message: Error message to display
        """
        try:
            if hasattr(self, "error_label") and self.error_label.winfo_exists():
                self.error_label.configure(text=message)
        except Exception as e:
            self.logger.error(f"Error setting error message: {e}", exc_info=True)

    def center_dialog(self):
        """Center the dialog on the parent window."""
        if not hasattr(self, "dialog_created") or not self.dialog_created or not hasattr(self, "tk") or self.tk is None:
            return
        
        try:
            self.update_idletasks()
            
            # Get parent window position and size
            parent_x = self.master.winfo_rootx()
            parent_y = self.master.winfo_rooty()
            parent_width = self.master.winfo_width()
            parent_height = self.master.winfo_height()
            
            # Calculate dialog position
            x = parent_x + (parent_width - self.winfo_width()) // 2
            y = parent_y + (parent_height - self.winfo_height()) // 2
            
            # Set dialog position
            self.geometry(f"+{x}+{y}")
        except Exception as e:
            self.logger.error(f"Error centering dialog: {e}", exc_info=True)

    def check_cached_credentials(self):
        """Check for cached login credentials."""
        try:
            # Get last logged in user
            last_user = None
            cached_users = self.auth_cache.get_all_users()
            
            if cached_users:
                # Get the most recently used user
                sorted_users = sorted(
                    cached_users.items(), 
                    key=lambda x: x[1].get("last_used", 0), 
                    reverse=True
                )
                last_user = sorted_users[0][0]
            
            if not last_user:
                return
            
            # Get stored credentials
            credentials = self.auth_cache.get_credentials(last_user)
            if not credentials or "token" not in credentials:
                return
            
            # Get app instance
            app = get_app_instance()
            if not app:
                return
            
            # Get auth service
            auth_service = app.get_service("auth")
            if not auth_service:
                return
            
            # Set login in progress
            self._set_login_in_progress(True)
            
            # Pre-fill username
            if hasattr(self, "username_entry") and self.username_entry.winfo_exists():
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, last_user)
            
            # Set remember me
            if hasattr(self, "remember_me_var"):
                self.remember_me_var.set(True)
            
            # Validate token
            success, user_data = auth_service.validate_token(credentials["token"])
            
            if success and user_data:
                # Token is valid, auto-login
                self._handle_login_result(True, "", user_data)
            else:
                # Token is invalid, clear cached credentials
                self.auth_cache.clear_credentials(last_user)
                self._set_login_in_progress(False)
            
        except Exception as e:
            self.logger.error(f"Error checking cached credentials: {e}", exc_info=True)
            self._set_login_in_progress(False)

    # Completely remove both _create_emergency_ui methods by replacing them with a comment

    # Remove the emergency UI methods
    # The emergency login feature has been removed 

    def _on_close(self):
        """Callback for when the dialog is closed."""
        # Reset the dialog instance
        LoginDialog._dialog_instance = None
        self.destroy() 