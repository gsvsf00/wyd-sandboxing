from app.ui.base.base_frame import BaseFrame
import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional

from app.utils.logger import LoggerWrapper
from app.core.app_instance import get_app_instance

class AccountFrame(BaseFrame):
    """
    Account frame for personal account management.
    Available to all authenticated users.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.logger = LoggerWrapper(name="account_frame")
        
    def on_init(self):
        """Initialize the account frame."""
        try:
            super().on_init()
            
            # Get user data
            app = get_app_instance()
            self.user_data = app.current_user if app else None
            
            # Set up layout
            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=0)  # Header
            self.rowconfigure(1, weight=1)  # Content
            
            # Create header
            self._create_header()
            
            # Create content
            self._create_content()
            
        except Exception as e:
            self.logger.error(f"Error in AccountFrame on_init: {e}", exc_info=True)
            
    def _create_header(self):
        """Create header section."""
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        title = ctk.CTkLabel(
            header,
            text="My Account",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=10)
        
    def _create_content(self):
        """Create the main content."""
        content = ctk.CTkFrame(self)
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content.columnconfigure(0, weight=1)
        
        # Profile section
        self._create_profile_section(content)
        
        # Subscription section
        self._create_subscription_section(content)
        
        # Password change section
        self._create_password_section(content)
        
    def _create_profile_section(self, parent):
        """Create profile information section."""
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Section title
        title = ctk.CTkLabel(
            frame,
            text="Profile Information",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        # Username (read-only)
        username_label = ctk.CTkLabel(frame, text="Username:")
        username_label.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        username_value = ctk.CTkLabel(
            frame,
            text=self.user_data.get("username", "Unknown") if self.user_data else "Not logged in"
        )
        username_value.grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        # Character name (editable)
        char_label = ctk.CTkLabel(frame, text="Character Name:")
        char_label.grid(row=2, column=0, sticky="w", padx=15, pady=5)
        
        self.char_entry = ctk.CTkEntry(frame, width=200)
        self.char_entry.grid(row=2, column=1, sticky="w", padx=15, pady=5)
        if self.user_data:
            self.char_entry.insert(0, self.user_data.get("character_name", ""))
        
        # Server (editable)
        server_label = ctk.CTkLabel(frame, text="Server:")
        server_label.grid(row=3, column=0, sticky="w", padx=15, pady=5)
        
        self.server_entry = ctk.CTkEntry(frame, width=200)
        self.server_entry.grid(row=3, column=1, sticky="w", padx=15, pady=5)
        if self.user_data:
            self.server_entry.insert(0, self.user_data.get("server", ""))
        
        # Save button
        save_button = ctk.CTkButton(
            frame,
            text="Save Changes",
            command=self._save_profile
        )
        save_button.grid(row=4, column=0, columnspan=2, padx=15, pady=15)
        
    def _create_subscription_section(self, parent):
        """Create subscription information section."""
        frame = ctk.CTkFrame(parent)
        frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # Section title
        title = ctk.CTkLabel(
            frame,
            text="Subscription Status",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 5))
        
        # Get subscription info
        if self.user_data and "subscription" in self.user_data:
            sub = self.user_data["subscription"]
            active = sub.get("active", False)
            expiry = sub.get("expiry_date", "Unknown")
            plan = sub.get("plan", "Basic")
        else:
            active = False
            expiry = "No active subscription"
            plan = "None"
        
        # Status
        status_label = ctk.CTkLabel(frame, text="Status:")
        status_label.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        status_value = ctk.CTkLabel(
            frame,
            text="Active" if active else "Inactive",
            text_color=("green", "#4CAF50") if active else ("red", "#F44336")
        )
        status_value.grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        # Expiry
        expiry_label = ctk.CTkLabel(frame, text="Expires:")
        expiry_label.grid(row=2, column=0, sticky="w", padx=15, pady=5)
        
        expiry_value = ctk.CTkLabel(frame, text=expiry)
        expiry_value.grid(row=2, column=1, sticky="w", padx=15, pady=5)
        
        # Plan type
        plan_label = ctk.CTkLabel(frame, text="Plan:")
        plan_label.grid(row=3, column=0, sticky="w", padx=15, pady=5)
        
        plan_value = ctk.CTkLabel(frame, text=plan)
        plan_value.grid(row=3, column=1, sticky="w", padx=15, pady=5)
        
    def _create_password_section(self, parent):
        """Create password change section."""
        frame = ctk.CTkFrame(parent)
        frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Section title
        title = ctk.CTkLabel(
            frame,
            text="Change Password",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 5))
        
        # Current password
        current_label = ctk.CTkLabel(frame, text="Current Password:")
        current_label.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        self.current_password = ctk.CTkEntry(frame, width=200, show="•")
        self.current_password.grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        # New password
        new_label = ctk.CTkLabel(frame, text="New Password:")
        new_label.grid(row=2, column=0, sticky="w", padx=15, pady=5)
        
        self.new_password = ctk.CTkEntry(frame, width=200, show="•")
        self.new_password.grid(row=2, column=1, sticky="w", padx=15, pady=5)
        
        # Confirm new password
        confirm_label = ctk.CTkLabel(frame, text="Confirm Password:")
        confirm_label.grid(row=3, column=0, sticky="w", padx=15, pady=5)
        
        self.confirm_password = ctk.CTkEntry(frame, width=200, show="•")
        self.confirm_password.grid(row=3, column=1, sticky="w", padx=15, pady=5)
        
        # Error message
        self.password_error = ctk.CTkLabel(
            frame,
            text="",
            text_color=("red", "#F44336")
        )
        self.password_error.grid(row=4, column=0, columnspan=2, padx=15, pady=5)
        
        # Change button
        change_button = ctk.CTkButton(
            frame,
            text="Change Password",
            command=self._change_password
        )
        change_button.grid(row=5, column=0, columnspan=2, padx=15, pady=15)
        
    def _save_profile(self):
        """Save profile changes."""
        # Get values
        character_name = self.char_entry.get().strip()
        server = self.server_entry.get().strip()
        
        try:
            # Get auth service
            app = get_app_instance()
            auth_service = app.get_service("auth") if app else None
            
            if not auth_service:
                self.logger.error("Auth service not available")
                from app.ui.utils.dialogs import show_error
                show_error(self, "Error", "Authentication service not available.")
                return
                
            # Update user data
            user_id = self.user_data.get("_id")
            if not user_id:
                self.logger.error("User ID not found in user data")
                from app.ui.utils.dialogs import show_error
                show_error(self, "Error", "User ID not found.")
                return
                
            # Call service to update profile
            success = auth_service.update_profile(user_id, character_name, server)
            
            if success:
                from app.ui.utils.dialogs import show_info
                show_info(self, "Success", "Profile updated successfully.")
            else:
                from app.ui.utils.dialogs import show_error
                show_error(self, "Error", "Failed to update profile.")
                
        except Exception as e:
            self.logger.error(f"Error saving profile: {e}", exc_info=True)
            from app.ui.utils.dialogs import show_error
            show_error(self, "Error", f"An error occurred: {str(e)}")
            
    def _change_password(self):
        """Change user password."""
        # Clear error message
        self.password_error.configure(text="")
        
        # Get values
        current = self.current_password.get()
        new = self.new_password.get()
        confirm = self.confirm_password.get()
        
        # Validate
        if not current:
            self.password_error.configure(text="Current password is required")
            return
            
        if not new:
            self.password_error.configure(text="New password is required")
            return
            
        if new != confirm:
            self.password_error.configure(text="Passwords do not match")
            return
            
        if len(new) < 8:
            self.password_error.configure(text="Password must be at least 8 characters")
            return
            
        try:
            # Get auth service
            app = get_app_instance()
            auth_service = app.get_service("auth") if app else None
            
            if not auth_service:
                self.logger.error("Auth service not available")
                self.password_error.configure(text="Authentication service not available")
                return
                
            # Get user ID
            user_id = self.user_data.get("_id")
            if not user_id:
                self.logger.error("User ID not found in user data")
                self.password_error.configure(text="User ID not found")
                return
                
            # Call service to change password
            success, message = auth_service.change_password(user_id, current, new)
            
            if success:
                # Clear fields
                self.current_password.delete(0, tk.END)
                self.new_password.delete(0, tk.END)
                self.confirm_password.delete(0, tk.END)
                
                from app.ui.utils.dialogs import show_info
                show_info(self, "Success", "Password changed successfully.")
            else:
                self.password_error.configure(text=message)
                
        except Exception as e:
            self.logger.error(f"Error changing password: {e}", exc_info=True)
            self.password_error.configure(text=f"An error occurred: {str(e)}") 