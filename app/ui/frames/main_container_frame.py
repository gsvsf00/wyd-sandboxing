import tkinter as tk
import customtkinter as ctk
from typing import List, Dict, Callable, Optional, Any
import os

from app.ui.base.base_frame import BaseFrame
from app.utils.logger import LoggerWrapper
from app.core.app_instance import get_app_instance

class MainContainerFrame(BaseFrame):
    """
    Main container frame that holds the sidebar and content area.
    """
    
    def __init__(self, master, **kwargs):
        """Initialize the main container frame."""
        super().__init__(master, **kwargs)
        self.logger = LoggerWrapper(name="main_container_frame")
        
        # Initialize state
        self.authenticated = False
        self.is_admin = False
        self.nav_buttons = {}
        
        # Create UI
        self._create_ui()
        
    def _create_ui(self):
        """Initialize the frame layout."""
        try:
            super().on_init()
            
            # Configure the grid layout
            self.grid_columnconfigure(1, weight=1)  # Content area expands
            self.grid_rowconfigure(0, weight=1)     # Both rows expand equally
            
            # Create the sidebar
            self._create_sidebar()
            
            # Create the content area where other frames will be shown
            self._create_content_area()
            
            # Update sidebar based on authentication status
            self._update_sidebar()
            
        except Exception as e:
            self.logger.error(f"Error initializing MainContainerFrame: {e}", exc_info=True)
            
    def _create_sidebar(self):
        """Create the sidebar with navigation buttons."""
        try:
            # Create sidebar frame with dark background
            self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("#1A1B26", "#1A1B26"))
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            
            # Configure rows
            self.sidebar.grid_rowconfigure(0, weight=0)  # Logo area
            self.sidebar.grid_rowconfigure(1, weight=1)  # Navigation area
            self.sidebar.grid_rowconfigure(2, weight=0)  # Bottom area
            self.sidebar.grid_columnconfigure(0, weight=1)
            
            # Prevent the sidebar from resizing
            self.sidebar.grid_propagate(False)
            
            # Add logo at the top
            self.sidebar_logo = self._create_sidebar_logo()
            
            # Create navigation area - use a simple frame instead of scrollable frame
            self.nav_area = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            self.nav_area.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
            
            # Create buttons at the bottom (login/logout)
            self.sidebar_bottom = self._create_sidebar_bottom()
            
        except Exception as e:
            self.logger.error(f"Error creating sidebar: {e}", exc_info=True)
            
    def _create_sidebar_logo(self):
        """Create the logo section in the sidebar."""
        try:
            logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=100)
            logo_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(15, 5))
            
            # App name label with custom styling
            app_name = ctk.CTkLabel(
                logo_frame,
                text="WydBot",
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=("#4B91F1", "#4B91F1")
            )
            app_name.pack(pady=(5, 0))
            
            # Version label
            version_label = ctk.CTkLabel(
                logo_frame,
                text="v1.0.0",
                font=ctk.CTkFont(size=12),
                text_color=("gray70", "gray70")
            )
            version_label.pack(pady=(0, 5))
            
            # Try to add a logo image if available
            try:
                logo_path = os.path.join("app", "resources", "images", "logo.png")
                if os.path.exists(logo_path):
                    logo_image = ctk.CTkImage(light_image=tk.PhotoImage(file=logo_path),
                                              dark_image=tk.PhotoImage(file=logo_path),
                                              size=(80, 80))
                    logo_label = ctk.CTkLabel(logo_frame, image=logo_image, text="")
                    logo_label.pack(pady=5)
            except Exception as e:
                self.logger.warning(f"Could not load logo image: {e}")
                
            # Add a separator
            separator = ctk.CTkFrame(logo_frame, height=1, fg_color=("gray70", "gray30"))
            separator.pack(fill="x", pady=(10, 0))
            
            return logo_frame
            
        except Exception as e:
            self.logger.error(f"Error creating sidebar logo: {e}", exc_info=True)
            # Return a fallback frame
            return ctk.CTkFrame(self.sidebar)
            
    def _create_sidebar_bottom(self):
        """Create the bottom section of the sidebar."""
        try:
            # Clear any existing bottom frame
            if hasattr(self, "sidebar_bottom") and self.sidebar_bottom:
                self.sidebar_bottom.destroy()
                
            # Create bottom frame
            self.sidebar_bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            self.sidebar_bottom.grid(row=2, column=0, sticky="sew", padx=5, pady=10)
            
            # Initialize user info section (hidden by default)
            self.user_info_frame = ctk.CTkFrame(self.sidebar_bottom, fg_color=("gray90", "gray20"))
            
            # User avatar/initials
            self.user_avatar = ctk.CTkLabel(
                self.user_info_frame,
                text="U",
                font=ctk.CTkFont(size=20, weight="bold"),
                width=40,
                height=40,
                corner_radius=20,
                fg_color=("#3B8ED0", "#1F6AA5"),
                text_color=("white", "white")
            )
            self.user_avatar.pack(side="left", padx=10, pady=10)
            
            # User name
            self.user_name = ctk.CTkLabel(
                self.user_info_frame,
                text="User",
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            self.user_name.pack(side="left", padx=5, pady=10, fill="x", expand=True)
            
            # Login/Logout button
            app = get_app_instance()
            is_authenticated = app and app.current_user is not None
            
            self.auth_button = ctk.CTkButton(
                self.sidebar_bottom,
                text="Logout" if is_authenticated else "Login",
                height=32,
                command=self._handle_auth_button
            )
            self.auth_button.pack(fill="x", padx=10, pady=10)
            
            # Show user info if authenticated
            if is_authenticated and app and app.current_user:
                self.user_info_frame.pack(fill="x", pady=(0, 10))
                username = app.current_user.get("username", "User")
                self.user_name.configure(text=username)
                
                # Set avatar initials
                if username:
                    initials = username[0].upper()
                    self.user_avatar.configure(text=initials)
                
        except Exception as e:
            self.logger.error(f"Error creating sidebar bottom: {e}", exc_info=True)
            
    def _create_content_area(self):
        """Create the content area where frames will be displayed."""
        try:
            self.logger.debug("Creating content area in MainContainerFrame")
            
            # Create a frame for the content area
            self.content_area = ctk.CTkFrame(self)
            self.content_area.grid(row=0, column=1, sticky="nsew")
            
            # Configure the content area for frame display
            self.content_area.grid_columnconfigure(0, weight=1)
            self.content_area.grid_rowconfigure(0, weight=1)
            
            # Add a placeholder label to ensure the area is visible
            placeholder = ctk.CTkLabel(
                self.content_area,
                text="Loading content...",
                font=ctk.CTkFont(size=16)
            )
            placeholder.grid(row=0, column=0, sticky="nsew")
            
            # Save reference to the placeholder for later removal
            self.placeholder = placeholder
            
            self.logger.debug("Content area created successfully")
            return self.content_area
            
        except Exception as e:
            self.logger.error(f"Error creating content area: {e}", exc_info=True)
            # Create a basic fallback
            self.content_area = ctk.CTkFrame(self, corner_radius=0)
            self.content_area.grid(row=0, column=1, sticky="nsew")
            
            error_label = ctk.CTkLabel(
                self.content_area,
                text=f"Error initializing content area: {str(e)}",
                text_color=("red", "#F44336")
            )
            error_label.pack(expand=True)
            
            return self.content_area
            
    def set_authenticated(self, authenticated, is_admin=False):
        """
        Set the authentication state.
        
        Args:
            authenticated: Whether the user is authenticated
            is_admin: Whether the user is an admin
        """
        self.authenticated = authenticated
        self.is_admin = is_admin
        self._update_sidebar()
        
        # Refresh current frame if needed
        app = get_app_instance()
        if app and hasattr(app, "frame_manager"):
            current_frame_id = app.frame_manager.get_current_frame_id()
            if current_frame_id:
                app.frame_manager.show_frame(current_frame_id)
            
    def _update_sidebar(self):
        """Update the sidebar based on authentication status."""
        try:
            # Get app instance
            app = get_app_instance()
            if not app:
                self.logger.error("App instance not available")
                return
            
            # Check if navigation area exists
            if not hasattr(self, "nav_area") or not self.nav_area.winfo_exists():
                # Create navigation area if it doesn't exist
                self._create_ui()
                return
            
            # Clear existing buttons
            if hasattr(self, "nav_buttons"):
                for button in self.nav_buttons.values():
                    if button.winfo_exists():
                        button.destroy()
            
            # Create new buttons
            self.nav_buttons = {}
            
            # Get sidebar items
            sidebar_items = self._get_sidebar_items()
            
            # Add buttons for each item
            for i, item in enumerate(sidebar_items):
                button = ctk.CTkButton(
                    self.nav_area,
                    text=item["text"],
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    anchor="w",
                    command=lambda id=item["id"]: self._handle_nav_button(id)
                )
                button.pack(fill="x", padx=10, pady=5)
                self.nav_buttons[item["id"]] = button
            
            # Update authentication button text
            if hasattr(self, "auth_button") and self.auth_button.winfo_exists():
                is_authenticated = app.current_user is not None
                self.auth_button.configure(
                    text="Logout" if is_authenticated else "Login"
                )
            
            # Update user info
            if hasattr(self, "user_name_label") and self.user_name_label.winfo_exists():
                if app.current_user:
                    self.user_name_label.configure(
                        text=app.current_user.get("username", "User")
                    )
                else:
                    self.user_name_label.configure(text="Guest")
                
        except Exception as e:
            self.logger.error(f"Error updating sidebar: {e}", exc_info=True)
            
    def _get_sidebar_items(self):
        """Get sidebar items based on authentication status."""
        items = []
        
        # Get app instance
        app = get_app_instance()
        
        # Check if user is authenticated
        is_authenticated = False
        if app and hasattr(app, "current_user"):
            is_authenticated = app.current_user is not None
        
        # Always add dashboard
        items.append({
            "id": "dashboard",
            "text": "Dashboard",
            "icon": "home"
        })
        
        # Add items that require authentication
        if is_authenticated:
            # Add game launcher if services are ready
            if app and app.is_service_ready("game_launcher"):
                items.append({
                    "id": "game_launcher",
                    "text": "Game Launcher",
                    "icon": "gamepad"
                })
                
            # Add account management
            items.append({
                "id": "account",
                "text": "Account",
                "icon": "user"
            })
        
        # Always add settings
        items.append({
            "id": "settings",
            "text": "Settings",
            "icon": "settings"
        })
        
        # Add admin panel for admin users
        if is_authenticated and app and app.current_user.get("role") == "admin":
            items.append({
                "id": "admin_panel",
                "text": "Admin Panel",
                "icon": "admin"
            })
        
        return items
            
    def _handle_nav_button(self, frame_id):
        """Handle navigation button click."""
        try:
            # Get app instance
            app = get_app_instance()
            if not app:
                self.logger.error("App instance not available")
                return
            
            # Check if user is authenticated for protected frames
            protected_frames = ["account", "admin_panel", "game_launcher"]
            if frame_id in protected_frames and not app.current_user:
                # Show login dialog for protected frames
                self._show_login_dialog()
                return
            
            # Show the requested frame
            if hasattr(app, "frame_manager") and app.frame_manager:
                # Update selected button if the method exists
                if hasattr(self, "_update_selected_button"):
                    self._update_selected_button(frame_id)
                
                # Show the frame
                app.frame_manager.show_frame(frame_id)
            
        except Exception as e:
            self.logger.error(f"Error handling nav button: {e}", exc_info=True)
            
    def _handle_auth_button(self):
        """Handle authentication button click (login/logout)."""
        try:
            # Get app instance
            app = get_app_instance()
            if not app:
                self.logger.error("App instance not available")
                return
            
            # Check if user is authenticated
            is_authenticated = app.current_user is not None
            
            if is_authenticated:
                # Confirm logout
                from app.ui.utils.dialogs import show_question
                if show_question(
                    parent=self,
                    title="Confirm Logout",
                    message="Are you sure you want to log out?"
                ):
                    # Logout
                    app.logout()
                    
                    # Update UI
                    self._update_sidebar()
                    
                    # Show dashboard
                    if hasattr(app, "frame_manager") and app.frame_manager:
                        app.frame_manager.show_frame("dashboard")
            else:
                # Show login dialog
                self._show_login_dialog()
                
        except Exception as e:
            self.logger.error(f"Error handling auth button: {e}", exc_info=True)
            
    def _show_login_dialog(self):
        """Show the login dialog."""
        try:
            # Check if user is already logged in
            app = get_app_instance()
            if app and app.current_user:
                # User is already logged in, no need to show login dialog
                return
            
            # Import login dialog
            from app.ui.dialogs.login_dialog import LoginDialog
            
            # Create and show login dialog
            login_dialog = LoginDialog(self)
            
            # Check if dialog was created (it might not be if user is already logged in)
            if not hasattr(login_dialog, "dialog_created") or not login_dialog.dialog_created:
                return
            
            # Position dialog relative to main window
            if hasattr(login_dialog, "center_dialog") and login_dialog.tk is not None:
                login_dialog.center_dialog()
            
            # Make dialog modal
            login_dialog.grab_set()
            login_dialog.focus_set()
            
        except Exception as e:
            self.logger.error(f"Error showing login dialog: {e}", exc_info=True)
    
    def get_content_area(self):
        """Get the content area frame where other frames are displayed."""
        try:
            # If content_area is not created yet, create it
            if self.content_area is None:
                self.logger.debug("Content area is None, creating it now")
                self._create_content_area()
            else:
                self.logger.debug("Content area already exists")
                
            # Ensure content area exists and is properly configured
            if self.content_area:
                if not self.content_area.winfo_exists():
                    self.logger.warning("Content area widget doesn't exist, recreating it")
                    self._create_content_area()
                    
            return self.content_area
        except Exception as e:
            self.logger.error(f"Error getting content area: {e}", exc_info=True)
            # Create a fallback if needed
            if self.content_area is None:
                self.content_area = ctk.CTkFrame(self)
                self.content_area.grid(row=0, column=1, sticky="nsew")
            return self.content_area 

    def _update_selected_button(self, selected_id):
        """
        Update the selected button in the sidebar.
        
        Args:
            selected_id: ID of the selected button
        """
        try:
            # Reset all buttons to default style
            for button_id, button in self.nav_buttons.items():
                if button.winfo_exists():
                    button.configure(
                        fg_color="transparent",
                        text_color=("gray10", "gray90")
                    )
            
            # Highlight the selected button
            if selected_id in self.nav_buttons and self.nav_buttons[selected_id].winfo_exists():
                self.nav_buttons[selected_id].configure(
                    fg_color=("gray75", "gray25"),
                    text_color=("gray10", "gray90")
                )
        except Exception as e:
            self.logger.error(f"Error updating selected button: {e}", exc_info=True) 