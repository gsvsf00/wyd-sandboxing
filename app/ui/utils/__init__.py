"""
UI Utilities

Provides common UI utility functions.
"""

from app.ui.utils.dialogs import (
    CTkDialog,
    show_info,
    show_error,
    show_warning,
    show_question,
    show_input_dialog,
    show_options
)

from app.ui.utils.debounce import debounce, throttle
from app.ui.utils.tooltips import create_tooltip, ToolTip

# Function to get theme color
def get_theme_color(color_name: str, mode: str = None) -> str:
    """
    Get a theme color based on the current theme mode.
    
    Args:
        color_name: The name of the color
        mode: Optional theme mode to use (light/dark)
        
    Returns:
        The color value for the current theme mode
    """
    import customtkinter as ctk
    
    # Define color mappings
    colors = {
        "primary": ("#3B8ED0", "#1F6AA5"),  # Light mode, Dark mode
        "secondary": ("#5A6268", "#6C757D"),
        "success": ("#28A745", "#5CB85C"),
        "danger": ("#DC3545", "#D9534F"),
        "warning": ("#FFC107", "#F0AD4E"),
        "info": ("#17A2B8", "#5BC0DE"),
        "light": ("#F8F9FA", "#FFFFFF"),
        "dark": ("#343A40", "#212529"),
        "background": ("#FFFFFF", "#2B2B2B"),
        "foreground": ("#212529", "#DCE4EE"),
        "border": ("#DEE2E6", "#444444"),
    }
    
    # Get current appearance mode if not specified
    if mode is None:
        mode = ctk.get_appearance_mode()
    
    # Return color based on mode
    color_pair = colors.get(color_name.lower(), ("#000000", "#FFFFFF"))
    return color_pair[0] if mode.lower() == "light" else color_pair[1]

# Function to center a window
def center_window(window, width: int = None, height: int = None) -> None:
    """
    Center a window on the screen.
    
    Args:
        window: The window to center
        width: Optional width to use instead of window's width
        height: Optional height to use instead of window's height
    """
    window.update_idletasks()
    
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Get window dimensions
    window_width = width or window.winfo_width()
    window_height = height or window.winfo_height()
    
    # Calculate position
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    # Set position
    window.geometry(f"{window_width}x{window_height}+{x}+{y}") 

# Function to center a window
def center_window(window, width: int = None, height: int = None) -> None:
    """
    Center a window on the screen.
    
    Args:
        window: Window to center
        width: Window width (default: current width)
        height: Window height (default: current height)
    """
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Use current dimensions if not specified
    if width is None:
        width = window.winfo_width()
    if height is None:
        height = window.winfo_height()
        
    # Calculate position
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    # Set window position
    window.geometry(f"{width}x{height}+{x}+{y}") 