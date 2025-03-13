#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dashboard Frame for WydBot.
Main application view after login.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional, List, Callable
import threading
import time

# Import from core
from app.core.app_instance import get_app_instance

# Import frame manager
from app.ui.frame_manager import BaseFrame

# Import components
from app.ui.components.base_component import BaseComponent, register_component

# Import utilities
from app.utils.logger import LoggerWrapper
from app.utils.thread_manager import run_in_background
from app.ui.utils import get_theme_color, create_tooltip

# Global logger instance
logger = LoggerWrapper(name="dashboard_frame")


@register_component("sidebar_menu")
class SidebarMenu(BaseComponent):
    """Sidebar menu component for navigation."""
    
    def __init__(self, master, **kwargs):
        """Initialize the sidebar menu component."""
        super().__init__(master, **kwargs)
        
        # Set up state
        self.state = {
            "active_item": kwargs.get("active_item", "dashboard"),
            "items": kwargs.get("items", self._get_default_items())
        }
        
        # Default values
        self.on_item_selected = kwargs.get("on_item_selected", None)
        
        # Create UI elements
        self.render()
    
    def _create_widget(self):
        """Create the main widget for this component."""
        return ctk.CTkFrame(
            self.master,
            corner_radius=0,
            fg_color=get_theme_color("bg_secondary")
        )
    
    def _get_default_items(self) -> List[Dict[str, Any]]:
        """Get default menu items."""
        return [
            {
                "id": "dashboard",
                "text": "Dashboard",
                "icon": "home",
                "role": ["user", "admin"]
            },
            {
                "id": "game",
                "text": "Game Launcher",
                "icon": "play",
                "role": ["user", "admin"]
            },
            {
                "id": "bot",
                "text": "Bot Control",
                "icon": "robot",
                "role": ["user", "admin"]
            },
            {
                "id": "settings",
                "text": "Settings",
                "icon": "settings",
                "role": ["user", "admin"]
            },
            {
                "id": "admin",
                "text": "Admin Panel",
                "icon": "shield",
                "role": ["admin"]
            }
        ]
    
    def render(self):
        """Render the component."""
        try:
            logger.debug("SidebarMenu render started")
            # Clear previous widgets
            for widget in self.widget.winfo_children():
                widget.destroy()
            
            # Create layout
            self.widget.grid_columnconfigure(0, weight=1)
            
            # Create logo area
            self.logo_frame = ctk.CTkFrame(
                self.widget,
                corner_radius=0,
                fg_color="transparent"
            )
            self.logo_frame.grid(row=0, column=0, sticky="ew", pady=(20, 10))
            
            self.logo_label = ctk.CTkLabel(
                self.logo_frame,
                text="WydBot",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            self.logo_label.pack(pady=10)
            
            # Create menu items
            menu_frame = ctk.CTkFrame(
                self.widget,
                corner_radius=0,
                fg_color="transparent"
            )
            menu_frame.grid(row=1, column=0, sticky="nsew", pady=10)
            
            # Get current user role
            app = get_app_instance()
            user_role = "user"  # Default role
            if app and app.current_user:
                user_role = app.current_user.get("role", "user")
            
            # Create menu items
            self.menu_items = {}
            row = 0
            
            for item in self.state["items"]:
                # Check if user has permission to see this item
                if user_role not in item.get("role", ["user"]):
                    continue
                
                item_id = item["id"]
                is_active = item_id == self.state["active_item"]
                
                # Create item frame
                item_frame = ctk.CTkFrame(
                    menu_frame,
                    corner_radius=0,
                    fg_color=get_theme_color("bg_tertiary") if is_active else "transparent",
                    height=40
                )
                item_frame.grid(row=row, column=0, sticky="ew", pady=2)
                item_frame.grid_columnconfigure(1, weight=1)
                
                # Create item label
                item_label = ctk.CTkLabel(
                    item_frame,
                    text=item["text"],
                    font=ctk.CTkFont(weight="bold" if is_active else "normal"),
                    anchor="w"
                )
                item_label.grid(row=0, column=1, padx=(10, 10), pady=10, sticky="w")
                
                # Store item frame reference
                self.menu_items[item_id] = item_frame
                
                # Bind click event
                def make_click_handler(item_id):
                    def handler(event):
                        self._handle_item_click(item_id)
                    return handler
                
                item_frame.bind("<Button-1>", make_click_handler(item_id))
                item_label.bind("<Button-1>", make_click_handler(item_id))
                
                row += 1
            
            # Create spacer
            spacer = ctk.CTkFrame(
                menu_frame,
                corner_radius=0,
                fg_color="transparent"
            )
            spacer.grid(row=row, column=0, sticky="ew", pady=10)
            
            # Create user info at bottom
            user_frame = ctk.CTkFrame(
                self.widget,
                corner_radius=0,
                fg_color="transparent"
            )
            user_frame.grid(row=2, column=0, sticky="ew", pady=10)
            
            # Get user info
            username = "User"
            if app and app.current_user:
                username = app.current_user.get("username", "User")
            
            # Create user label
            user_label = ctk.CTkLabel(
                user_frame,
                text=username,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="center"
            )
            user_label.pack(pady=5)
            
            # Create logout button
            logout_button = ctk.CTkButton(
                user_frame,
                text="Logout",
                command=self._handle_logout,
                height=30,
                width=100
            )
            logout_button.pack(pady=10)
            
            # Apply layout
            self.widget.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
            logger.debug("SidebarMenu render completed")
        except Exception as e:
            logger.error(f"Error in SidebarMenu render: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _handle_item_click(self, item_id: str):
        """
        Handle menu item click.
        
        Args:
            item_id: Item ID
        """
        if item_id == self.state["active_item"]:
            return
        
        # Update active item
        self.set_state({"active_item": item_id})
        
        # Call callback
        if self.on_item_selected:
            self.on_item_selected(item_id)
    
    def _handle_logout(self):
        """Handle logout button click."""
        app = get_app_instance()
        if app:
            app.logout()


@register_component("status_bar")
class StatusBar(BaseComponent):
    """Status bar component for displaying system status."""
    
    def __init__(self, master, **kwargs):
        """Initialize the status bar component."""
        super().__init__(master, **kwargs)
        
        # Set up state
        self.state = {
            "status": "Ready",
            "is_bot_running": False,
            "game_status": "Not running",
            "last_update": time.time()
        }
        
        # Create UI elements
        self.render()
        
        # Start status update timer
        self._start_status_update()
    
    def _create_widget(self):
        """Create the main widget for this component."""
        return ctk.CTkFrame(
            self.master,
            corner_radius=0,
            height=30,
            fg_color=get_theme_color("bg_tertiary")
        )
    
    def render(self):
        """Render the component."""
        try:
            logger.debug("StatusBar render started")
            # Clear previous widgets
            for widget in self.widget.winfo_children():
                widget.destroy()
            
            # Create layout with 3 sections
            self.widget.grid_columnconfigure(0, weight=1)
            self.widget.grid_columnconfigure(1, weight=1)
            self.widget.grid_columnconfigure(2, weight=1)
            
            # Left section - Status
            status_label = ctk.CTkLabel(
                self.widget,
                text=f"Status: {self.state['status']}",
                font=ctk.CTkFont(size=10),
                anchor="w"
            )
            status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            # Center section - Bot status
            bot_status = "Running" if self.state["is_bot_running"] else "Stopped"
            bot_color = get_theme_color("success") if self.state["is_bot_running"] else get_theme_color("error")
            
            bot_label = ctk.CTkLabel(
                self.widget,
                text=f"Bot: {bot_status}",
                text_color=bot_color,
                font=ctk.CTkFont(size=10),
                anchor="center"
            )
            bot_label.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
            
            # Right section - Game status
            game_label = ctk.CTkLabel(
                self.widget,
                text=f"Game: {self.state['game_status']}",
                font=ctk.CTkFont(size=10),
                anchor="e"
            )
            game_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")
            
            # Apply layout
            self.widget.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
            logger.debug("StatusBar render completed")
        except Exception as e:
            logger.error(f"Error in StatusBar render: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _start_status_update(self):
        """Start the status update timer."""
        # Update every 5 seconds
        if self.is_mounted and not self.is_destroyed:
            # Schedule the next update
            if hasattr(self.master, "after"):
                self.master.after(5000, self._start_status_update)
            
            # Update status
            self._update_status()
    
    def _update_status(self):
        """Update the status information."""
        # Only update if mounted
        if not self.is_mounted or self.is_destroyed:
            return
        
        # Get app controller
        app = get_app_instance()
        if not app:
            return
        
        # Get services
        bot_service = app.get_service("bot")
        game_service = app.get_service("game_launcher")
        
        # Update bot status
        is_bot_running = False
        if bot_service and hasattr(bot_service, "is_running"):
            is_bot_running = bot_service.is_running
        
        # Update game status
        game_status = "Not running"
        if game_service and hasattr(game_service, "get_status"):
            game_status = game_service.get_status()
        
        # Update state
        self.set_state({
            "is_bot_running": is_bot_running,
            "game_status": game_status,
            "last_update": time.time()
        })


@register_component("dashboard_content")
class DashboardContent(BaseComponent):
    """Main dashboard content component."""
    
    def __init__(self, master, **kwargs):
        """Initialize the dashboard content component."""
        super().__init__(master, **kwargs)
        
        # Set up state
        self.state = {
            "stats": {
                "bot_uptime": 0,
                "tasks_completed": 0,
                "success_rate": 0,
                "last_run": None
            }
        }
        
        # Create UI elements
        self.render()
        
        # Update stats
        self._update_stats()
    
    def _create_widget(self):
        """Create the main widget for this component."""
        return ctk.CTkFrame(
            self.master,
            corner_radius=0,
            fg_color="transparent"
        )
    
    def render(self):
        """Render the component."""
        try:
            logger.debug("DashboardContent render started")
            # Clear previous widgets
            for widget in self.widget.winfo_children():
                widget.destroy()
            
            # Create layout with 2 columns
            self.widget.grid_columnconfigure(0, weight=2)
            self.widget.grid_columnconfigure(1, weight=1)
            self.widget.grid_rowconfigure(0, weight=1)
            
            # Left column - Stats and controls
            left_frame = ctk.CTkFrame(
                self.widget,
                corner_radius=10
            )
            left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            
            # Create title
            title_label = ctk.CTkLabel(
                left_frame,
                text="Dashboard",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.pack(padx=20, pady=(20, 10), anchor="w")
            
            # Create subtitle
            subtitle_label = ctk.CTkLabel(
                left_frame,
                text="Welcome to WydBot! Here's your activity summary.",
                font=ctk.CTkFont(size=12)
            )
            subtitle_label.pack(padx=20, pady=(0, 20), anchor="w")
            
            # Create stats grid
            stats_frame = ctk.CTkFrame(
                left_frame,
                corner_radius=10,
                fg_color="transparent"
            )
            stats_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
            
            # Configure grid
            stats_frame.grid_columnconfigure(0, weight=1)
            stats_frame.grid_columnconfigure(1, weight=1)
            
            # Create stat cards
            self._create_stat_card(
                stats_frame, 0, 0,
                "Bot Uptime",
                f"{self.state['stats']['bot_uptime']} minutes",
                "Time the bot has been running"
            )
            
            self._create_stat_card(
                stats_frame, 0, 1,
                "Tasks Completed",
                str(self.state['stats']['tasks_completed']),
                "Number of tasks completed by the bot"
            )
            
            self._create_stat_card(
                stats_frame, 1, 0,
                "Success Rate",
                f"{self.state['stats']['success_rate']}%",
                "Percentage of successful tasks"
            )
            
            last_run = self.state['stats']['last_run'] or "Never"
            self._create_stat_card(
                stats_frame, 1, 1,
                "Last Run",
                last_run,
                "Last time the bot was run"
            )
            
            # Right column - Quick actions
            right_frame = ctk.CTkFrame(
                self.widget,
                corner_radius=10
            )
            right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
            
            # Create title
            actions_title = ctk.CTkLabel(
                right_frame,
                text="Quick Actions",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            actions_title.pack(padx=20, pady=(20, 10), anchor="w")
            
            # Create action buttons
            start_button = ctk.CTkButton(
                right_frame,
                text="Start Bot",
                command=self._handle_start_bot
            )
            start_button.pack(padx=20, pady=10, fill=tk.X)
            
            stop_button = ctk.CTkButton(
                right_frame,
                text="Stop Bot",
                command=self._handle_stop_bot
            )
            stop_button.pack(padx=20, pady=10, fill=tk.X)
            
            launch_button = ctk.CTkButton(
                right_frame,
                text="Launch Game",
                command=self._handle_launch_game
            )
            launch_button.pack(padx=20, pady=10, fill=tk.X)
            
            settings_button = ctk.CTkButton(
                right_frame,
                text="Settings",
                command=self._handle_settings
            )
            settings_button.pack(padx=20, pady=10, fill=tk.X)
            
            # Apply layout
            self.widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)
            logger.debug("DashboardContent render completed")
        except Exception as e:
            logger.error(f"Error in DashboardContent render: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _create_stat_card(self, parent, row, col, title, value, tooltip=None):
        """
        Create a stat card.
        
        Args:
            parent: Parent widget
            row: Grid row
            col: Grid column
            title: Stat title
            value: Stat value
            tooltip: Tooltip text
        """
        try:
            logger.debug(f"Creating stat card: {title}")
            card = ctk.CTkFrame(
                parent,
                corner_radius=10
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            title_label = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=12)
            )
            title_label.pack(padx=10, pady=(10, 5))
            
            value_label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            value_label.pack(padx=10, pady=(5, 10))
            
            if tooltip:
                try:
                    create_tooltip(card, tooltip)
                    logger.debug(f"Tooltip created for stat card: {title}")
                except Exception as e:
                    logger.error(f"Error creating tooltip for stat card {title}: {e}")
                
            logger.debug(f"Stat card created: {title}")
        except Exception as e:
            logger.error(f"Error creating stat card {title}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _update_stats(self):
        """Update the dashboard statistics."""
        # Get app controller
        app = get_app_instance()
        if not app:
            return
        
        # Get services
        bot_service = app.get_service("bot")
        
        # Get stats from services
        if bot_service and hasattr(bot_service, "get_stats"):
            stats = bot_service.get_stats()
            self.set_state({"stats": stats})
        else:
            # Use dummy data for demonstration
            self.set_state({
                "stats": {
                    "bot_uptime": 120,
                    "tasks_completed": 45,
                    "success_rate": 92,
                    "last_run": "Today, 10:30 AM"
                }
            })
    
    def _handle_start_bot(self):
        """Handle start bot button click."""
        app = get_app_instance()
        if app:
            bot_service = app.get_service("bot")
            if bot_service and hasattr(bot_service, "start"):
                bot_service.start()
                self._update_stats()
    
    def _handle_stop_bot(self):
        """Handle stop bot button click."""
        app = get_app_instance()
        if app:
            bot_service = app.get_service("bot")
            if bot_service and hasattr(bot_service, "stop"):
                bot_service.stop()
                self._update_stats()
    
    def _handle_launch_game(self):
        """Handle launch game button click."""
        app = get_app_instance()
        if app:
            game_service = app.get_service("game_launcher")
            if game_service and hasattr(game_service, "launch"):
                game_service.launch()
    
    def _handle_settings(self):
        """Handle settings button click."""
        # Navigate to settings page
        app = get_app_instance()
        if app and hasattr(app, "frame_manager"):
            app.frame_manager.show_frame("settings")


class DashboardFrame(BaseFrame):
    """
    Dashboard frame for the application.
    This is the main landing page that users see.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.logger = LoggerWrapper(name="dashboard_frame")
    
    def on_init(self):
        """Initialize the dashboard frame."""
        try:
            super().on_init()
            
            # Configure grid layout
            self.columnconfigure(0, weight=1)
            self.rowconfigure(0, weight=1)
            
            # Create content
            content = self._create_content()
            content.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
            # Update UI based on authentication status
            self.refresh()
            
        except Exception as e:
            self.logger.error(f"Error initializing dashboard frame: {e}", exc_info=True)
            self._create_fallback_ui()
    
    def _create_content(self):
        """Create the dashboard content."""
        try:
            # Create content frame
            content_frame = ctk.CTkFrame(self)
            content_frame.grid(row=0, column=0, sticky="nsew")
            content_frame.columnconfigure(0, weight=1)
            
            # Get app instance to check initialization status
            app = get_app_instance()
            
            # Show initialization status if services are still initializing
            if app and hasattr(app, "services_initializing") and app.services_initializing:
                self._create_initializing_ui(content_frame)
            elif app and hasattr(app, "service_status") and app.service_status:
                if "auth" in app.service_status and app.service_status["auth"] == "failed":
                    self._create_service_error_ui(content_frame, "Authentication service initialization failed")
                elif app.current_user:
                    self._create_authenticated_content(content_frame)
                else:
                    self._create_login_prompt(content_frame)
            else:
                # Default content if no specific state is detected
                self._create_login_prompt(content_frame)
                
            return content_frame
        except Exception as e:
            self.logger.error(f"Error creating dashboard content: {e}", exc_info=True)
            return self._create_fallback_ui()
    
    def _create_initializing_ui(self, parent):
        """Create UI for initialization state."""
        # Create initializing frame
        init_frame = ctk.CTkFrame(parent)
        init_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            init_frame,
            text="Application Initializing",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(40, 10))
        
        # Message
        message = ctk.CTkLabel(
            init_frame,
            text="Please wait while the application initializes services...",
            font=ctk.CTkFont(size=14)
        )
        message.pack(pady=10)
        
        # Progress bar
        progress = ctk.CTkProgressBar(init_frame, width=400)
        progress.pack(pady=20)
        progress.set(0.5)  # Indeterminate progress
        
        # Show service status
        status_text = "Service Status:"
        status_label = ctk.CTkLabel(
            init_frame,
            text=status_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        status_label.pack(pady=(20, 5))
        
        # Get app instance
        app = get_app_instance()
        if app and hasattr(app, "service_status"):
            for service_id, status in app.service_status.items():
                service_label = ctk.CTkLabel(
                    init_frame,
                    text=f"{service_id}: {status}",
                    font=ctk.CTkFont(size=12),
                    justify="left"
                )
                service_label.pack(pady=2)
                
        # Update status periodically
        self.after(1000, lambda: self._update_initialization_status(status_label))
    
    def _show_login_dialog(self):
        """Show the login dialog."""
        try:
            # Import here to avoid circular imports
            from app.ui.dialogs.login_dialog import LoginDialog
            
            dialog = LoginDialog(self)
            self.wait_window(dialog)
            
            # Handle login result
            if dialog.success and dialog.user_data:
                self._handle_login_success(dialog.user_data)
        except Exception as e:
            self.logger.error(f"Error showing login dialog: {e}", exc_info=True)
    
    def _create_fallback_ui(self):
        """Create a fallback UI for when initialization fails."""
        # Clear any existing widgets
        for widget in self.winfo_children():
            widget.destroy()
            
        # Create a simple frame with an error message
        fallback = ctk.CTkFrame(self)
        fallback.pack(fill="both", expand=True, padx=20, pady=20)
        
        message = ctk.CTkLabel(
            fallback,
            text="Unable to initialize the dashboard",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("red", "#F44336")
        )
        message.pack(pady=(20, 10))
        
        details = ctk.CTkLabel(
            fallback,
            text="There was an error initializing the dashboard content.\nCheck the logs for more details.",
            font=ctk.CTkFont(size=14)
        )
        details.pack(pady=10)
    
    def on_enter(self, **kwargs):
        """Called when the frame becomes visible."""
        try:
            super().on_enter()
            self.logger.debug("Dashboard frame entered")
            
            # Refresh content when entering
            self.refresh()
        except Exception as e:
            self.logger.error(f"Error in dashboard on_enter: {e}", exc_info=True)
    
    def on_leave(self):
        """Called when the frame is about to be hidden."""
        try:
            super().on_leave()
            self.logger.debug("Dashboard frame exited")
        except Exception as e:
            self.logger.error(f"Error in dashboard on_leave: {e}", exc_info=True)
    
    def refresh(self):
        """Refresh the frame content."""
        try:
            self.logger.debug("Refreshing dashboard frame")
            
            # Remove existing content
            for widget in self.winfo_children():
                widget.destroy()
            
            # Create new content
            content = self._create_content()
            if content:
                content.pack(fill="both", expand=True)
            
            # Schedule next refresh if we're in initialization
            app = get_app_instance()
            if app and hasattr(app, "services_initializing") and app.services_initializing:
                self.after(2000, self.refresh)  # Refresh every 2 seconds during initialization
            
        except Exception as e:
            self.logger.error(f"Error refreshing dashboard: {e}", exc_info=True)
    
    def _update_dashboard_content(self):
        """Update the dashboard content."""
        # Implementation of _update_dashboard_content method
        pass
    
    def _create_login_prompt(self, parent):
        """Create the login prompt."""
        # Create login frame
        login_frame = ctk.CTkFrame(parent)
        login_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Welcome message
        welcome = ctk.CTkLabel(
            login_frame,
            text="Welcome to WydBot",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        welcome.pack(pady=(40, 10))
        
        # Description
        description = ctk.CTkLabel(
            login_frame,
            text="Please log in using the button in the sidebar to access all features.",
            font=ctk.CTkFont(size=14),
            wraplength=400
        )
        description.pack(pady=10)
        
        # Features list
        features_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        features_frame.pack(pady=20)
        
        features = [
            "Automated bot controls",
            "Game launching and management",
            "Account settings and preferences",
            "Network masking capabilities"
        ]
        
        for feature in features:
            feature_label = ctk.CTkLabel(
                features_frame,
                text=f"• {feature}",
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            feature_label.pack(anchor="w", pady=5)

    def _create_authenticated_content(self, parent):
        """Create content for authenticated users."""
        # Import at function level to avoid circular imports
        from app.ui.components.base_component import ComponentFactory
        
        try:
            # Create dashboard content using component
            dashboard = ComponentFactory.create_component(
                "dashboard_content", 
                parent
            )
            dashboard.render()
            
            # Add status bar
            status_bar = ComponentFactory.create_component(
                "status_bar",
                parent
            )
            status_bar.render()
            
            return True
        except Exception as e:
            self.logger.error(f"Error creating authenticated content: {e}", exc_info=True)
            return False

    def _handle_login_success(self, user_data):
        """Handle successful login."""
        try:
            app = get_app_instance()
            if app:
                app.set_authenticated_user(user_data)
                self.logger.info(f"User logged in: {user_data.get('username')}")
                # Force a refresh of the UI
                self.after(100, self.refresh)
        except Exception as e:
            self.logger.error(f"Error handling login success: {e}", exc_info=True)

    def _update_initialization_status(self, status_label):
        """Update the initialization status display."""
        # Check if the label still exists
        if not status_label.winfo_exists():
            return
        
        app = get_app_instance()
        if not app or not hasattr(app, "service_status"):
            return
        
        # Update status label with current service statuses
        status_text = "Service Status:"
        
        try:
            status_label.configure(text=status_text)
            
            # Get parent frame
            parent = status_label.master
            if not parent.winfo_exists():
                return
            
            # Remove existing service labels
            for widget in parent.winfo_children():
                if widget != status_label and isinstance(widget, ctk.CTkLabel):
                    widget.destroy()
            
            # Add updated service labels
            for service_id, status in app.service_status.items():
                service_label = ctk.CTkLabel(
                    parent,
                    text=f"{service_id}: {status}",
                    font=ctk.CTkFont(size=12),
                    justify="left"
                )
                service_label.pack(pady=2)
            
            # Continue updating if still initializing
            if app.services_initializing and status_label.winfo_exists():
                self.after(1000, lambda: self._update_initialization_status(status_label))
        except Exception as e:
            self.logger.error(f"Error updating initialization status: {e}")

    def _create_service_error_ui(self, parent, error_message):
        """Create UI for service error state."""
        # Create error frame
        error_frame = ctk.CTkFrame(parent)
        error_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            error_frame,
            text="Service Error",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("red", "#F44336")
        )
        title.pack(pady=(40, 10))
        
        # Message
        message = ctk.CTkLabel(
            error_frame,
            text=error_message,
            font=ctk.CTkFont(size=14),
            wraplength=400
        )
        message.pack(pady=10)
        
        # Additional info
        info = ctk.CTkLabel(
            error_frame,
            text="The application cannot function properly without this service.\n"
                 "Please check the logs for more details and restart the application.",
            font=ctk.CTkFont(size=12),
            wraplength=400
        )
        info.pack(pady=10)
        
        # Login button - This will attempt to use limited functionality
        login_button = ctk.CTkButton(
            error_frame,
            text="Try Anyway",
            command=self._show_login_dialog
        )
        login_button.pack(pady=20)
        
        # Restart button
        restart_button = ctk.CTkButton(
            error_frame,
            text="Restart Application",
            command=lambda: get_app_instance().exit() if get_app_instance() else None
        )
        restart_button.pack(pady=10) 