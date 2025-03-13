#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI utilities for the WydBot application.
Provides helper functions for Tkinter operations.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Callable, Dict, Any, Optional
import time
from functools import wraps

# Import the logger
from app.utils.logger import LoggerWrapper

# Global logger instance
logger = LoggerWrapper(name="ui_utils")


def debounce(wait_time: float):
    """
    Decorator to debounce a function call.
    
    Args:
        wait_time: Time to wait in seconds before allowing another call
        
    Returns:
        Decorated function
    """
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            time_diff = current_time - last_called[0]
            
            if time_diff >= wait_time:
                last_called[0] = current_time
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def throttle(wait_time: float):
    """
    Decorator to throttle a function call.
    
    Args:
        wait_time: Minimum time between calls in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_called
            current_time = time.time()
            time_diff = current_time - last_called[0]
            
            result = func(*args, **kwargs)
            
            if time_diff >= wait_time:
                last_called[0] = current_time
            
            return result
        
        return wrapper
    
    return decorator


def schedule_on_main_thread(func: Callable, delay: int = 0):
    """
    Schedule a function to run on the main thread using Tkinter's after method.
    
    Args:
        func: Function to run
        delay: Delay in milliseconds
    """
    from app.core.app_controller import get_app_root
    root = get_app_root()
    
    if root:
        root.after(delay, func)
    else:
        logger.warning("No root window available to schedule function")


def create_tooltip(widget, text: str, delay: int = 500):
    """
    Create a tooltip for a widget.
    
    Args:
        widget: Widget to add tooltip to
        text: Tooltip text
        delay: Delay in milliseconds before showing tooltip
    """
    tooltip = None
    tooltip_id = None
    
    def enter(event):
        nonlocal tooltip, tooltip_id
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        
        # Create a toplevel window
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            tooltip,
            text=text,
            justify=tk.LEFT,
            background="#ffffff",
            relief=tk.SOLID,
            borderwidth=1,
            padx=5,
            pady=2
        )
        label.pack(ipadx=1)
        
        tooltip.withdraw()
        tooltip_id = widget.after(delay, lambda: tooltip.deiconify())
    
    def leave(event):
        nonlocal tooltip, tooltip_id
        if tooltip_id:
            widget.after_cancel(tooltip_id)
            tooltip_id = None
        if tooltip:
            tooltip.destroy()
            tooltip = None
    
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)


def get_theme_color(name: str, mode: Optional[str] = None) -> str:
    """
    Get a color from the current theme.
    
    Args:
        name: Color name
        mode: Appearance mode (None for current)
        
    Returns:
        Color hex code
    """
    mode = mode or ctk.get_appearance_mode()
    
    # Color mapping (light mode, dark mode)
    theme_colors = {
        "bg_primary": ("#F5F5F5", "#1A1A1A"),
        "bg_secondary": ("#EBEBEB", "#2A2A2A"),
        "bg_tertiary": ("#DADADA", "#3A3A3A"),
        "fg_primary": ("#000000", "#FFFFFF"),
        "fg_secondary": ("#444444", "#BBBBBB"),
        "accent": ("#1E88E5", "#1E88E5"),
        "success": ("#4CAF50", "#4CAF50"),
        "warning": ("#FFC107", "#FFC107"),
        "error": ("#F44336", "#F44336"),
        "border": ("#CCCCCC", "#555555"),
    }
    
    index = 0 if mode.lower() == "light" else 1
    return theme_colors.get(name.lower(), ("#000000", "#FFFFFF"))[index]


def center_window(window, width: int = None, height: int = None):
    """
    Center a window on the screen.
    
    Args:
        window: Window to center
        width: Window width (uses current width if None)
        height: Window height (uses current height if None)
    """
    width = width or window.winfo_width()
    height = height or window.winfo_height()
    
    # Make sure window size is updated
    window.update_idletasks()
    
    # Calculate position
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    # Set geometry
    window.geometry(f"{width}x{height}+{x}+{y}")


def load_image(path: str, size: tuple = None):
    """
    Load an image for use in Tkinter.
    
    Args:
        path: Path to the image file
        size: Tuple of (width, height) to resize to
        
    Returns:
        PhotoImage or None if loading fails
    """
    try:
        from PIL import Image, ImageTk
        
        image = Image.open(path)
        
        if size:
            image = image.resize(size, Image.LANCZOS)
        
        return ImageTk.PhotoImage(image)
    except Exception as e:
        logger.error(f"Error loading image {path}: {e}")
        return None 