#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Login Frame for WydBot.
Handles user authentication UI.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional, Callable
import threading
from PIL import Image
import os

# Import from core
from app.core.app_controller import get_app_instance

# Import frame manager
from app.ui.frame_manager import BaseFrame, TransitionAnimation

# Import components
from app.ui.components.base_component import BaseComponent, register_component

# Import utilities
from app.utils.logger import LoggerWrapper
from app.utils.thread_manager import run_in_background
from app.ui.utils import center_window, get_theme_color, create_tooltip

# Global logger instance
logger = LoggerWrapper(name="login_frame")


@register_component("login_input")
class LoginInput(BaseComponent):
    """Login input component with username and password fields."""
    
    def __init__(self, master, **kwargs):
        """Initialize the login input component."""
        super().__init__(master, **kwargs)
        
        # Set up state
        self.state = {
            "username": "",
            "password": "",
            "login_in_progress": False,
            "error_message": ""
        }
        
        # Default values
        self.on_login = kwargs.get("on_login", None)
        self.on_register = kwargs.get("on_register", None)
        
        # Initialize auth service
        self.auth_service = None
        app_instance = get_app_instance()
        if app_instance:
            self.auth_service = app_instance.get_service("auth")
            if not self.auth_service:
                logger.error("Auth service not found in app instance")
        else:
            logger.error("Unable to get app instance")
        
        # Create UI elements
        self.render()
    
    def _create_widget(self):
        """Create the main widget for this component."""
        return ctk.CTkFrame(self.master, corner_radius=10, fg_color="transparent")
    
    def render(self):
        """Render the component."""
        # Clear previous widgets
        for widget in self.widget.winfo_children():
            widget.destroy()
        
        # Try to set background image
        try:
            # Try multiple possible paths for the background image
            possible_paths = [
                'resources/images/background.jpg',
                'app/resources/images/background.jpg',
                '../resources/images/background.jpg',
                'resources/images/background.webp',
                'app/resources/images/background.webp',
                '../resources/images/background.webp'
            ]
            
            background_image = None
            background_path = None
            
            for path in possible_paths:
                try:
                    background_image = Image.open(path)
                    background_path = path
                    logger.debug(f"Successfully loaded background image from: {path}")
                    break
                except Exception as e:
                    logger.debug(f"Could not load image from {path}: {e}")
            
            if background_image:
                self.background_image = ctk.CTkImage(background_image)
                self.background_label = ctk.CTkLabel(self.widget, image=self.background_image)
                self.background_label.place(relwidth=1, relheight=1)
                logger.debug("Background image set successfully")
            else:
                logger.error("Failed to load background image from any path")
        except Exception as e:
            logger.error(f"Error setting background image: {e}")
        
        # Create layout
        self.widget.grid_columnconfigure(0, weight=1)
        
        # Create title
        self.title_label = ctk.CTkLabel(
            self.widget,
            text="Welcome User",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 30), sticky="ew")
        
        # Username field
        self.username_label = ctk.CTkLabel(
            self.widget,
            text="Username",
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color="#FFFFFF"
        )
        self.username_label.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="w")
        
        self.username_entry = ctk.CTkEntry(
            self.widget,
            placeholder_text="Enter your username",
            width=300,
            height=40,
            border_width=1,
            fg_color="#2B2B2B",
            border_color="#3A7EBF",
            text_color="#FFFFFF"
        )
        self.username_entry.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.username_entry.insert(0, self.state["username"])
        self.username_entry.bind("<Return>", lambda event: self.password_entry.focus())
        
        # Password field
        self.password_label = ctk.CTkLabel(
            self.widget,
            text="Password",
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color="#FFFFFF"
        )
        self.password_label.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="w")
        
        self.password_entry = ctk.CTkEntry(
            self.widget,
            placeholder_text="Enter your password",
            show="•",
            width=300,
            height=40,
            border_width=1,
            fg_color="#2B2B2B",
            border_color="#3A7EBF",
            text_color="#FFFFFF"
        )
        self.password_entry.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.password_entry.insert(0, self.state["password"])
        self.password_entry.bind("<Return>", lambda event: self._handle_login())
        
        # Create error message
        self.error_label = ctk.CTkLabel(
            self.widget,
            text=self.state["error_message"],
            text_color=get_theme_color("error"),
            anchor="w"
        )
        self.error_label.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        if not self.state["error_message"]:
            self.error_label.grid_remove()
        
        # Create login button
        self.login_button = ctk.CTkButton(
            self.widget,
            text="LOGIN",
            command=self._handle_login,
            state="normal" if not self.state["login_in_progress"] else "disabled",
            height=40,
            fg_color="#3A7EBF",
            hover_color="#2A5A8A",
            text_color="#FFFFFF"
        )
        self.login_button.grid(row=6, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        # Create register link
        self.register_label = ctk.CTkLabel(
            self.widget,
            text="Register Here",
            font=ctk.CTkFont(size=12),
            cursor="hand2",
            text_color="#4D8CC9"
        )
        self.register_label.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.register_label.bind("<Button-1>", self._handle_register_click)
        
        # Apply layout
        self.widget.pack(padx=40, pady=40, fill=tk.BOTH, expand=True)
    
    def _handle_login(self):
        """Handle login button click."""
        # Get values
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Validate
        if not username:
            self.set_error_message("Username is required")
            self.username_entry.focus()
            return
        
        if not password:
            self.set_error_message("Password is required")
            self.password_entry.focus()
            return
        
        # Clear error message
        self.set_error_message("")
        
        # Set login in progress
        self.set_login_in_progress(True)
        
        try:
            # Check if auth_service is available
            if not self.auth_service:
                app_instance = get_app_instance()
                if app_instance:
                    self.auth_service = app_instance.get_service("auth")
                
                if not self.auth_service:
                    self.set_error_message("Authentication service unavailable")
                    self.set_login_in_progress(False)
                    return
            
            # Attempt to authenticate directly
            success, message, user_data = self.auth_service.authenticate(username, password)
            
            # Reset login in progress
            self.set_login_in_progress(False)
            
            if success:
                logger.info(f"User {username} logged in successfully.")
                # Call on_login callback with username and password
                if self.on_login:
                    self.on_login(username, password)
            else:
                # Show error message
                self.set_error_message(message)
                logger.warning(f"Failed login attempt for user {username}: {message}")
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            self.set_error_message("An error occurred during login")
            self.set_login_in_progress(False)
    
    def set_error_message(self, message: str):
        """Set the error message."""
        self.set_state({"error_message": message})
        
        if message:
            self.error_label.configure(text=message)
            self.error_label.grid()
        else:
            self.error_label.grid_remove()
    
    def set_login_in_progress(self, in_progress: bool):
        """Set the login in progress state."""
        self.set_state({"login_in_progress": in_progress})
        
        self.login_button.configure(
            state="disabled" if in_progress else "normal",
            text="Logging in..." if in_progress else "Login"
        )

    def _handle_register_click(self, event=None):
        """Handle register link click."""
        if self.on_register:
            self.on_register()


class LoginFrame(BaseFrame):
    """
    Login frame for user authentication.
    Allows users to log in to the application.
    """
    
    def __init__(self, master, **kwargs):
        """
        Initialize the login frame.
        
        Args:
            master: Parent widget
            **kwargs: Additional arguments for BaseFrame
        """
        super().__init__(master, **kwargs)
        
        # Set up state
        self.login_in_progress = False
        self.login_input = None
        
        # Configure frame
        self.configure(corner_radius=0)
    
    def on_init(self):
        """Initialize the frame when first created."""
        super().on_init()
        
        # Configure layout
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create left panel for illustration
        self.left_panel = ctk.CTkFrame(self, corner_radius=0, fg_color="#1A1A1A")
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        
        # Add illustration placeholder
        self.illustration_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.illustration_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Load illustration or create placeholder
        try:
            # Get image path
            image_path = os.path.join("app", "resources", "images", "background.webp")
            
            # Load the image
            from PIL import Image
            img = Image.open(image_path)
            
            # Resize image to fill the panel (adjust dimensions as needed)
            img = img.resize((600, 800), Image.LANCZOS)
            
            # Create CTkImage
            self.bg_image = ctk.CTkImage(light_image=img, dark_image=img, size=(600, 800))
            
            # Create background label
            bg_label = ctk.CTkLabel(self.illustration_frame, image=self.bg_image, text="")
            bg_label.pack(expand=True, fill="both")
            
            logger.info(f"Loaded background image: {image_path}")
        except Exception as e:
            logger.error(f"Error loading background image: {e}")
            self.create_illustration_placeholder()
        
        # Create right panel for login form
        self.right_panel = ctk.CTkFrame(self, corner_radius=0, fg_color="#212121")
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Create login input
        self.login_input = self.register_child(
            LoginInput(
                self.right_panel,
                on_login=self._handle_login,
                on_register=self._handle_register_click
            )
        )
        self.login_input.mount()
    
    def create_illustration_placeholder(self):
        """Create a placeholder illustration with shapes."""
        canvas = tk.Canvas(self.illustration_frame, bg="#1A1A1A", highlightthickness=0)
        canvas.pack(expand=True, fill="both")
        
        # Draw some shapes to mimic a dashboard illustration
        # Circle
        canvas.create_oval(50, 50, 150, 150, fill="#3A7EBF", outline="")
        # Rectangle
        canvas.create_rectangle(200, 80, 350, 180, fill="#2A5A8A", outline="")
        # Another circle
        canvas.create_oval(100, 200, 170, 270, fill="#4D8CC9", outline="")
        # Line chart-like shape
        points = [50, 300, 100, 250, 150, 280, 200, 220, 250, 260, 300, 200, 350, 230]
        canvas.create_line(points, fill="#6D9DD1", width=3, smooth=True)
    
    def on_enter(self, **kwargs):
        """Handle when the frame becomes active."""
        super().on_enter(**kwargs)
        
        # Focus the username entry
        if self.login_input and hasattr(self.login_input, "username_entry"):
            self.login_input.username_entry.focus()
        
        # Check if there's an error message
        if "error" in kwargs and self.login_input:
            self.login_input.set_error_message(kwargs["error"])
            
        # Check if there's a success message
        if "message" in kwargs and kwargs["message"]:
            self.show_success_message(kwargs["message"])
    
    def show_success_message(self, message):
        """
        Show a success message.
        
        Args:
            message: Success message
        """
        # Create success message frame if it doesn't exist
        if not hasattr(self, "success_message_frame"):
            self.success_message_frame = ctk.CTkFrame(
                self,
                corner_radius=8,
                border_width=1,
                border_color=get_theme_color("success"),
                fg_color=get_theme_color("success_bg")
            )
            
            self.success_message_label = ctk.CTkLabel(
                self.success_message_frame,
                text=message,
                text_color=get_theme_color("success"),
                font=ctk.CTkFont(size=12)
            )
            self.success_message_label.pack(padx=10, pady=10)
            
            # Show message above the form
            self.success_message_frame.place(
                relx=0.5, 
                rely=0.1, 
                anchor="center",
                relwidth=0.8
            )
        else:
            # Update existing message
            self.success_message_label.configure(text=message)
            self.success_message_frame.place(
                relx=0.5, 
                rely=0.1, 
                anchor="center",
                relwidth=0.8
            )
        
        # Schedule message to disappear
        self.after(5000, self.hide_success_message)
    
    def hide_success_message(self):
        """Hide the success message."""
        if hasattr(self, "success_message_frame"):
            self.success_message_frame.place_forget()
    
    def on_leave(self):
        """Handle when the frame becomes inactive."""
        super().on_leave()
        
        # Reset the login form
        if self.login_input:
            self.login_input.set_state({
                "login_in_progress": False,
                "error_message": ""
            })
    
    def _handle_login(self, username: str, password: str):
        """
        Handle login attempt.
        
        Args:
            username: Username
            password: Password
        """
        if self.login_in_progress:
            return
        
        # Set login in progress
        self.login_in_progress = True
        if self.login_input:
            self.login_input.set_login_in_progress(True)
        
        # Get app controller
        app = get_app_instance()
        if not app:
            logger.error("App controller not found")
            self._handle_login_error("Application error")
            return
        
        # Get auth service
        auth_service = app.get_service("auth")
        if not auth_service:
            logger.error("Auth service not found")
            self._handle_login_error("Authentication service not available")
            return
        
        # Perform login in background
        def do_login():
            try:
                success, result, user_data = auth_service.authenticate(username, password)
                
                # Check result and handle accordingly
                if success:
                    # Login successful, show main screen
                    self._handle_login_success(user_data)
                else:
                    # Login failed, show error
                    self._handle_login_error(result)
                
            except Exception as e:
                logger.error(f"Login error: {e}")
                self._handle_login_error("An error occurred during login")
        
        # Use run_in_background instead of manual thread creation
        run_in_background()(do_login)
    
    def _handle_login_success(self, user_data: Dict[str, Any]):
        """Handle successful login."""
        logger.info(f"User {user_data.get('username')} logged in successfully.")
        
        # Reset login state
        self.login_in_progress = False
        if self.login_input:
            self.login_input.set_login_in_progress(False)
        
        # Update app state
        app = get_app_instance()
        if app:
            try:
                # Set authenticated user
                logger.info(f"Setting authenticated user: {user_data.get('username')}")
                app.set_authenticated_user(user_data)
                logger.info("set_authenticated_user called successfully")
                
                # Ensure the dashboard frame is registered
                logger.info(f"Available frames: {list(app.frame_manager.frames.keys())}")
                
                if "dashboard" not in app.frame_manager.frames:
                    logger.error("Dashboard frame not registered in frame manager")
                    # Import and register the dashboard frame
                    try:
                        from app.ui.frames.dashboard_frame import DashboardFrame
                        logger.info("Manually registering dashboard frame")
                        app.frame_manager.register_frame("dashboard", DashboardFrame)
                        logger.info(f"Dashboard frame registered. Frames now: {list(app.frame_manager.frames.keys())}")
                    except Exception as e:
                        logger.error(f"Error registering dashboard frame: {e}")
                        import traceback
                        logger.error(f"Registration traceback: {traceback.format_exc()}")
                        return
                
                # Explicitly show dashboard frame on the main thread
                logger.info("About to request dashboard frame show")
                self.after(100, lambda: app.frame_manager.show_frame("dashboard", animation_type=TransitionAnimation.NONE))
                logger.info("Dashboard frame show requested")
            except Exception as e:
                logger.error(f"Error in set_authenticated_user: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            logger.error("Failed to get app instance in _handle_login_success")
    
    def _handle_login_error(self, error_message: str):
        """
        Handle login error.
        
        Args:
            error_message: Error message to display
        """
        logger.warning(f"Login error: {error_message}")
        
        # Reset login state
        self.login_in_progress = False
        if self.login_input:
            self.login_input.set_login_in_progress(False)
            self.login_input.set_error_message(error_message)
    
    def _handle_register_click(self):
        """Handle register link click."""
        # Get app instance
        app = get_app_instance()
        if not app:
            return
        
        # Navigate to register frame
        app.frame_manager.show_frame("register")

