"""
Tooltip utilities for the WydBot application.
Provides tooltip functionality for UI components.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Any

class ToolTip:
    """
    Tooltip class for CustomTkinter widgets.
    """
    def __init__(
        self,
        widget: Any,
        text: str,
        delay: int = 500,
        bg_color: Optional[str] = None,
        text_color: Optional[str] = None,
        font: Optional[ctk.CTkFont] = None,
        corner_radius: int = 6,
        padding: int = 6
    ):
        """
        Initialize the tooltip.
        
        Args:
            widget: Widget to attach the tooltip to
            text: Tooltip text
            delay: Delay in milliseconds before showing the tooltip
            bg_color: Background color
            text_color: Text color
            font: Font
            corner_radius: Corner radius
            padding: Padding
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.bg_color = bg_color or ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        self.text_color = text_color or ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        self.font = font or ctk.CTkFont(size=12)
        self.corner_radius = corner_radius
        self.padding = padding
        
        self.tooltip_window = None
        self.timer_id = None
        
        # Bind events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<ButtonPress>", self._on_leave)
        
    def _on_enter(self, event=None):
        """Handle mouse enter event."""
        # Cancel any existing timer
        self._cancel_timer()
        
        # Start a new timer
        self.timer_id = self.widget.after(self.delay, self._show_tooltip)
        
    def _on_leave(self, event=None):
        """Handle mouse leave event."""
        # Cancel any existing timer
        self._cancel_timer()
        
        # Hide the tooltip
        self._hide_tooltip()
        
    def _cancel_timer(self):
        """Cancel the timer."""
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None
            
    def _show_tooltip(self):
        """Show the tooltip."""
        # Get widget position
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip frame
        frame = ctk.CTkFrame(
            self.tooltip_window,
            corner_radius=self.corner_radius,
            fg_color=self.bg_color,
            border_width=0
        )
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Create tooltip label
        label = ctk.CTkLabel(
            frame,
            text=self.text,
            text_color=self.text_color,
            font=self.font,
            wraplength=300
        )
        label.pack(padx=self.padding, pady=self.padding)
        
        # Make sure the tooltip is on top
        self.tooltip_window.attributes("-topmost", True)
        self.tooltip_window.update_idletasks()
        
    def _hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
            
    def update_text(self, text: str):
        """
        Update the tooltip text.
        
        Args:
            text: New tooltip text
        """
        self.text = text
        
        # Update the tooltip if it's visible
        if self.tooltip_window:
            self._hide_tooltip()
            self._show_tooltip()


def create_tooltip(
    widget: Any,
    text: str,
    delay: int = 500,
    bg_color: Optional[str] = None,
    text_color: Optional[str] = None,
    font: Optional[ctk.CTkFont] = None,
    corner_radius: int = 6,
    padding: int = 6
) -> ToolTip:
    """
    Create a tooltip for a widget.
    
    Args:
        widget: Widget to attach the tooltip to
        text: Tooltip text
        delay: Delay in milliseconds before showing the tooltip
        bg_color: Background color
        text_color: Text color
        font: Font
        corner_radius: Corner radius
        padding: Padding
        
    Returns:
        ToolTip: Tooltip object
    """
    return ToolTip(
        widget=widget,
        text=text,
        delay=delay,
        bg_color=bg_color,
        text_color=text_color,
        font=font,
        corner_radius=corner_radius,
        padding=padding
    ) 