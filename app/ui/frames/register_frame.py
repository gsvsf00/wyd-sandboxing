#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Registration Frame for WydBot.
Handles user registration UI.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional, Callable
import threading
from PIL import Image

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

# Import necessary modules for MongoDB
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Global logger instance
logger = LoggerWrapper(name="register_frame")


@register_component("register_input")
class RegisterInput(BaseComponent):
    """Registration input component with username, password and other fields."""
    
    def __init__(self, master, **kwargs):
        """Initialize the registration input component."""
        super().__init__(master, **kwargs)
        
        # Set up state
        self.state = {
            "username": "",
            "password": "",
            "confirm_password": "",
            "character_name": "",
            "server": "",
            "registration_in_progress": False,
            "error_message": ""
        }
        
        # Default values
        self.on_register = kwargs.get("on_register", None)
        self.on_cancel = kwargs.get("on_cancel", None)
        
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
        return ctk.CTkFrame(self.master, corner_radius=10)
    
    def render(self):
        """Render the component with a background image."""
        # Clear previous widgets
        for widget in self.widget.winfo_children():
            widget.destroy()
        
        # Set background image
        try:
            # Try multiple possible paths for the background image (both jpg and webp formats)
            possible_paths = [
                'resources/images/background.jpg',
                'app/resources/images/background.jpg',
                '../resources/images/background.jpg',
                'resources/images/background.webp',
                'app/resources/images/background.webp',
                '../resources/images/background.webp'
            ]
            
            bg_image = None
            for path in possible_paths:
                try:
                    bg_image = Image.open(path)
                    logger.debug(f"Successfully loaded background image from: {path}")
                    break
                except Exception as e:
                    logger.debug(f"Could not load image from {path}: {e}")
            
            if bg_image:
                bg_photo = ctk.CTkImage(bg_image)
                self.bg_label = ctk.CTkLabel(self.widget, image=bg_photo)
                self.bg_label.place(relwidth=1, relheight=1)
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
            text="Create New Account",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Create subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.widget,
            text="Please fill in all required fields",
            font=ctk.CTkFont(size=12)
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Create username field
        self.username_label = ctk.CTkLabel(
            self.widget,
            text="Username *",
            anchor="w"
        )
        self.username_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.username_entry = ctk.CTkEntry(
            self.widget,
            placeholder_text="Enter your username",
            width=300
        )
        self.username_entry.grid(row=3, column=0, padx=20, pady=(5, 10), sticky="ew")
        self.username_entry.insert(0, self.state["username"])
        create_tooltip(self.username_entry, "Username must be unique and at least 3 characters")
        
        # Create password field
        self.password_label = ctk.CTkLabel(
            self.widget,
            text="Password *",
            anchor="w"
        )
        self.password_label.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.password_entry = ctk.CTkEntry(
            self.widget,
            placeholder_text="Enter your password",
            show="•",
            width=300
        )
        self.password_entry.grid(row=5, column=0, padx=20, pady=(5, 10), sticky="ew")
        self.password_entry.insert(0, self.state["password"])
        create_tooltip(self.password_entry, "Password must be at least 8 characters")
        
        # Create confirm password field
        self.confirm_password_label = ctk.CTkLabel(
            self.widget,
            text="Confirm Password *",
            anchor="w"
        )
        self.confirm_password_label.grid(row=6, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.confirm_password_entry = ctk.CTkEntry(
            self.widget,
            placeholder_text="Confirm your password",
            show="•",
            width=300
        )
        self.confirm_password_entry.grid(row=7, column=0, padx=20, pady=(5, 10), sticky="ew")
        self.confirm_password_entry.insert(0, self.state["confirm_password"])
        
        # Create character name field
        self.character_label = ctk.CTkLabel(
            self.widget,
            text="Character Name *",
            anchor="w"
        )
        self.character_label.grid(row=8, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.character_entry = ctk.CTkEntry(
            self.widget,
            placeholder_text="Enter your in-game character name",
            width=300
        )
        self.character_entry.grid(row=9, column=0, padx=20, pady=(5, 10), sticky="ew")
        self.character_entry.insert(0, self.state["character_name"])
        
        # Create server field
        self.server_label = ctk.CTkLabel(
            self.widget,
            text="Server *",
            anchor="w"
        )
        self.server_label.grid(row=10, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.server_entry = ctk.CTkEntry(
            self.widget,
            placeholder_text="Enter your game server",
            width=300
        )
        self.server_entry.grid(row=11, column=0, padx=20, pady=(5, 10), sticky="ew")
        self.server_entry.insert(0, self.state["server"])
        
        # Create error message
        self.error_label = ctk.CTkLabel(
            self.widget,
            text=self.state["error_message"],
            text_color=get_theme_color("error"),
            anchor="w"
        )
        self.error_label.grid(row=12, column=0, padx=20, pady=(5, 10), sticky="ew")
        if not self.state["error_message"]:
            self.error_label.grid_remove()
        
        # Create button frame
        self.button_frame = ctk.CTkFrame(
            self.widget,
            fg_color="transparent"
        )
        self.button_frame.grid(row=13, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        
        # Create cancel button
        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            command=self.toggle_login,
            fg_color=get_theme_color("secondary")
        )
        self.cancel_button.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ew")
        
        # Create register button
        self.register_button = ctk.CTkButton(
            self.button_frame,
            text="Register",
            command=self._handle_register,
            state="normal" if not self.state["registration_in_progress"] else "disabled"
        )
        self.register_button.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="ew")
        
        # Apply layout
        self.widget.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
    
    def _handle_register(self):
        """Handle register button click with MongoDB storage."""
        # Get values
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm_password = self.confirm_password_entry.get().strip()
        character_name = self.character_entry.get().strip()
        server = self.server_entry.get().strip()
        
        # Validate
        if not username:
            self.set_error_message("Username is required")
            return
        
        if len(username) < 3:
            self.set_error_message("Username must be at least 3 characters")
            return
        
        if not password:
            self.set_error_message("Password is required")
            return
        
        if len(password) < 8:
            self.set_error_message("Password must be at least 8 characters")
            return
        
        if password != confirm_password:
            self.set_error_message("Passwords do not match")
            return
        
        if not character_name:
            self.set_error_message("Character name is required")
            return
            
        if not server:
            self.set_error_message("Server is required")
            return
        
        # Set registration in progress
        self.set_registration_in_progress(True)
        
        # Check if auth_service is available
        if not self.auth_service:
            app_instance = get_app_instance()
            if app_instance:
                self.auth_service = app_instance.get_service("auth")
            
            if not self.auth_service:
                self.set_error_message("Authentication service unavailable")
                self.set_registration_in_progress(False)
                return
        
        # Use auth_service to register user
        try:
            # Attempt to register
            logger.info("Registering user...")
            success, message, user_id = self.auth_service.register_user(
                username=username,
                password=password,
                character_name=character_name,
                server=server
            )
            
            # Reset registration in progress
            self.set_registration_in_progress(False)
            
            if success:
                # Clear error message
                self.set_error_message("")
                
                # Show success message and redirect to login
                if self.on_register:
                    self.on_register(username, character_name, server)
            else:
                # Show error message
                self.set_error_message(message)
                
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            self.set_error_message("An error occurred during registration")
            self.set_registration_in_progress(False)
    
    def toggle_login(self):
        """Toggle back to the login form."""
        if self.on_cancel:
            self.on_cancel()
    
    def set_error_message(self, message: str):
        """Set the error message."""
        self.set_state({"error_message": message})
        
        if message:
            self.error_label.configure(text=message)
            self.error_label.grid()
        else:
            self.error_label.grid_remove()
    
    def set_registration_in_progress(self, in_progress: bool):
        """Set the registration in progress state."""
        self.set_state({"registration_in_progress": in_progress})
        
        self.register_button.configure(
            state="disabled" if in_progress else "normal",
            text="Registering..." if in_progress else "Register"
        )


class RegisterFrame(BaseFrame):
    """
    Registration frame for creating new user accounts.
    Allows users to register for the application.
    """
    
    def __init__(self, master, **kwargs):
        """
        Initialize the registration frame.
        
        Args:
            master: Parent widget
            **kwargs: Additional arguments for BaseFrame
        """
        super().__init__(master, **kwargs)
        
        # Set up state
        self.registration_in_progress = False
        self.register_input = None
        
        # Configure frame
        self.configure(corner_radius=0)
    
    def on_init(self):
        """Initialize the frame when first created."""
        super().on_init()
        
        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create center frame for registration
        self.center_frame = ctk.CTkFrame(self, corner_radius=0)
        self.center_frame.grid(row=0, column=0, sticky="nsew")
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure(0, weight=1)
        
        # Create registration input
        self.register_input = self.register_child(
            RegisterInput(
                self.center_frame,
                on_register=self._handle_register,
                on_cancel=self._handle_cancel
            )
        )
        self.register_input.mount()
    
    def on_enter(self, **kwargs):
        """Handle when the frame becomes active."""
        super().on_enter(**kwargs)
        
        # Center the window
        app = get_app_instance()
        if app:
            center_window(app.root, 500, 650)
    
    def on_leave(self):
        """Handle when the frame becomes inactive."""
        super().on_leave()
        
        # Reset state
        if self.register_input:
            self.register_input.set_state({
                "username": "",
                "password": "",
                "confirm_password": "",
                "character_name": "",
                "server": "",
                "registration_in_progress": False,
                "error_message": ""
            })
    
    def _handle_register(self, username: str, character_name: str, server: str):
        """
        Handle registration.
        
        Args:
            username: Username
            character_name: Character name
            server: Server name
        """
        # Set in progress
        if self.register_input:
            self.register_input.set_registration_in_progress(True)
            self.register_input.set_error_message("")
        
        # Get app instance
        app = get_app_instance()
        if not app:
            if self.register_input:
                self.register_input.set_registration_in_progress(False)
                self.register_input.set_error_message("Application error")
            return
        
        # Get auth service
        auth_service = app.get_service("auth")
        if not auth_service:
            if self.register_input:
                self.register_input.set_registration_in_progress(False)
                self.register_input.set_error_message("Authentication service not available")
            return
        
        # Get password from the register_input
        password = ""
        if self.register_input:
            password = self.register_input.password_entry.get().strip()
        
        # Register in background
        def do_register():
            # Register user
            success, message, user_data = auth_service.register_user(
                username=username,
                password=password,
                character_name=character_name,
                server=server
            )
            
            # Handle result
            if success:
                self._handle_register_success(user_data)
            else:
                self._handle_register_error(message)
        
        # Use run_in_background function properly
        run_in_background()(do_register)
    
    def _handle_register_success(self, user_data: Dict[str, Any]):
        """
        Handle successful registration.
        
        Args:
            user_data: User data
        """
        username = user_data.get('username', 'user')
        logger.info(f"Registration successful: {username}")
        
        # Reset registration state
        self.registration_in_progress = False
        
        # Get app controller
        app = get_app_instance()
        if not app:
            logger.error("App controller not found")
            return
        
        # Show success message
        if self.register_input:
            self.register_input.set_registration_in_progress(False)
            self.register_input.set_state({
                "error_message": "",
                "success_message": f"Account created successfully! Redirecting to login..."
            })
        
        # Navigate back to login after a delay
        def navigate_to_login():
            try:
                # Ensure login frame is registered
                if "login" not in app.frame_manager.frames:
                    logger.error("Login frame not registered")
                    return
                
                # Show login frame with success message
                app.frame_manager.show_frame(
                    "login", 
                    animation_type=TransitionAnimation.SLIDE_RIGHT,
                    message="Account created successfully! You can now log in."
                )
            except Exception as e:
                logger.error(f"Error navigating to login: {e}")
        
        # Schedule navigation with a delay
        self.after(2000, navigate_to_login)
    
    def _handle_register_error(self, error_message: str):
        """
        Handle registration error.
        
        Args:
            error_message: Error message
        """
        # Set error message
        if self.register_input:
            self.register_input.set_registration_in_progress(False)
            self.register_input.set_error_message(error_message)
    
    def _handle_cancel(self):
        """Handle cancel button click."""
        # Get app instance
        app = get_app_instance()
        if not app:
            return
        
        # Navigate to login frame
        app.frame_manager.show_frame("login") 