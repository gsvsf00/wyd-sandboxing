from app.ui.base.base_frame import BaseFrame
import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional
import ttk

from app.utils.logger import LoggerWrapper
from app.core.app_instance import get_app_instance

class AccountManagementFrame(BaseFrame):
    """
    Account management frame for administrators.
    Allows administrators to manage user accounts.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.logger = LoggerWrapper(name="account_management_frame")
        
    def on_init(self):
        """Initialize the account management frame."""
        try:
            super().on_init()
            
            # Check if user is admin
            app = get_app_instance()
            self.is_admin = False
            if app and app.current_user:
                self.is_admin = app.current_user.get("role") == "admin"
            
            if not self.is_admin:
                self._show_access_denied()
                return
                
            # Set up layout
            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=0)  # Header
            self.rowconfigure(1, weight=1)  # Content
            
            # Create header
            self._create_header()
            
            # Create content
            self._create_content()
            
            # Load users
            self._load_users()
            
        except Exception as e:
            self.logger.error(f"Error in AccountManagementFrame on_init: {e}", exc_info=True)
            
    def _show_access_denied(self):
        """Show access denied message for non-admin users."""
        # Clear frame
        for widget in self.winfo_children():
            widget.destroy()
            
        # Show access denied message
        frame = ctk.CTkFrame(self)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        message = ctk.CTkLabel(
            frame,
            text="Access Denied",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("red", "#F44336")
        )
        message.pack(pady=(40, 10))
        
        details = ctk.CTkLabel(
            frame,
            text="You do not have permission to access this page.\nOnly administrators can manage user accounts.",
            font=ctk.CTkFont(size=14)
        )
        details.pack(pady=10)
        
        # Back button
        back_button = ctk.CTkButton(
            frame,
            text="Back to Dashboard",
            command=lambda: get_app_instance().frame_manager.show_frame("dashboard")
        )
        back_button.pack(pady=20)
            
    def _create_header(self):
        """Create header section."""
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        title = ctk.CTkLabel(
            header,
            text="Account Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left", padx=20, pady=10)
        
        # Add user button
        add_button = ctk.CTkButton(
            header,
            text="Add New User",
            command=self._show_add_user_dialog
        )
        add_button.pack(side="right", padx=20, pady=10)
        
    def _create_content(self):
        """Create the main content."""
        content = ctk.CTkFrame(self)
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)
        
        # Search bar
        search_frame = ctk.CTkFrame(content, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=(10, 5))
        
        self.search_entry = ctk.CTkEntry(search_frame, width=300)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self._handle_search)
        
        search_button = ctk.CTkButton(
            search_frame,
            text="Search",
            width=100,
            command=self._handle_search
        )
        search_button.pack(side="left", padx=5)
        
        refresh_button = ctk.CTkButton(
            search_frame,
            text="Refresh",
            width=100,
            command=self._load_users
        )
        refresh_button.pack(side="right", padx=10)
        
        # Users table
        table_frame = ctk.CTkFrame(content)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # We'll implement a simple table using a treeview
        # We'd ideally use a more sophisticated component in a real app
        self.users_table = ttk.Treeview(
            table_frame,
            columns=("username", "role", "subscription", "status", "actions"),
            show="headings"
        )
        
        # Define headings
        self.users_table.heading("username", text="Username")
        self.users_table.heading("role", text="Role")
        self.users_table.heading("subscription", text="Subscription")
        self.users_table.heading("status", text="Status")
        self.users_table.heading("actions", text="Actions")
        
        # Define columns
        self.users_table.column("username", width=150)
        self.users_table.column("role", width=100)
        self.users_table.column("subscription", width=150)
        self.users_table.column("status", width=100)
        self.users_table.column("actions", width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.users_table.yview)
        self.users_table.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.users_table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind actions
        self.users_table.bind("<Double-1>", self._handle_row_double_click)
        
    def _load_users(self):
        """Load users from the database."""
        try:
            # Clear table
            for item in self.users_table.get_children():
                self.users_table.delete(item)
                
            # Get auth service
            app = get_app_instance()
            auth_service = app.get_service("auth") if app else None
            
            if not auth_service:
                self.logger.error("Auth service not available")
                return
                
            # Get users
            users = auth_service.get_users()
            
            # Add to table
            for user in users:
                username = user.get("username", "")
                role = user.get("role", "user")
                
                # Get subscription info
                subscription = "None"
                if "subscription" in user:
                    sub = user["subscription"]
                    if sub.get("active", False):
                        expiry = sub.get("expiry_date", "Unknown")
                        plan = sub.get("plan", "Basic")
                        subscription = f"{plan} (Expires: {expiry})"
                        
                # Get status
                status = "Active"
                if user.get("banned", False):
                    status = "Banned"
                elif user.get("suspended", False):
                    status = "Suspended"
                    
                self.users_table.insert("", tk.END, values=(
                    username,
                    role,
                    subscription,
                    status,
                    "Edit | Ban | Delete"  # These would be buttons in a real implementation
                ))
                
        except Exception as e:
            self.logger.error(f"Error loading users: {e}", exc_info=True)
            
    def _handle_search(self, event=None):
        """Handle search input."""
        search_text = self.search_entry.get().lower()
        
        # If empty, reload all users
        if not search_text:
            self._load_users()
            return
            
        # Otherwise, filter existing items
        for item in self.users_table.get_children():
            values = self.users_table.item(item, "values")
            username = values[0].lower()
            
            if search_text in username:
                # Show item
                self.users_table.item(item, tags=())
            else:
                # Hide item
                self.users_table.detach(item)
                
    def _handle_row_double_click(self, event):
        """Handle row double click to edit user."""
        item = self.users_table.identify_row(event.y)
        if not item:
            return
            
        # Get username
        values = self.users_table.item(item, "values")
        username = values[0]
        
        # Show edit dialog
        self._show_edit_user_dialog(username)
            
    def _show_add_user_dialog(self):
        """Show dialog to add a new user."""
        # This would be a dialog to create a new user
        pass
        
    def _show_edit_user_dialog(self, username):
        """Show dialog to edit a user."""
        # This would be a dialog to edit an existing user
        pass
        
    def _extend_subscription(self, username, days, plan):
        """Extend a user's subscription."""
        # This would extend the subscription for a user
        pass
        
    def _ban_user(self, username, reason):
        """Ban a user."""
        # This would ban a user
        pass
        
    def _delete_user(self, username):
        """Delete a user."""
        # This would delete a user
        pass 