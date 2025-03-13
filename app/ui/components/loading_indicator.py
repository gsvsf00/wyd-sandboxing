"""
Loading Indicator Component

Provides a visual indicator when the application is loading or processing.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Any, Dict
import time
import threading

from app.ui.components.base_component import BaseComponent, register_component

@register_component("loading_indicator")
class LoadingIndicator(BaseComponent):
    """
    Loading indicator component.
    Shows a spinner or progress bar while tasks are in progress.
    """
    
    def __init__(self, master, **kwargs):
        """Initialize the loading indicator."""
        self.spinner_speed = kwargs.pop("spinner_speed", 0.1)
        self.mode = kwargs.pop("mode", "spinner")  # spinner or progress
        self.size = kwargs.pop("size", 40)
        self.indeterminate = kwargs.pop("indeterminate", True)
        self.progress_value = kwargs.pop("progress", 0.0)
        self.text = kwargs.pop("text", "Loading...")
        self.show_text = kwargs.pop("show_text", True)
        
        # Initialize base component
        super().__init__(master, **kwargs)
        
        # For spinner animation
        self.angle = 0
        self.animation_running = False
        self.animation_thread = None
        
    def _create_widget(self):
        """Create the component widget."""
        # Create the main frame
        self.widget = ctk.CTkFrame(self.master)
        
        # Progress mode uses CTkProgressBar
        if self.mode == "progress":
            self.progress = ctk.CTkProgressBar(self.widget, width=self.size * 5)
            self.progress.pack(pady=10)
            
            if self.indeterminate:
                self.progress.configure(mode="indeterminate")
                self.progress.start()
            else:
                self.progress.set(self.progress_value)
                
        # Text label (optional)
        if self.show_text:
            self.label = ctk.CTkLabel(
                self.widget,
                text=self.text,
                font=ctk.CTkFont(size=14)
            )
            self.label.pack(pady=(5, 0))
            
        return self.widget
        
    def render(self):
        """Render the component."""
        super().render()
        
        # Start spinner animation if in spinner mode
        if self.mode == "spinner" and not self.animation_running:
            self.start_animation()
            
    def _create_spinner_canvas(self):
        """Create the spinner canvas for custom drawing."""
        self.canvas = tk.Canvas(
            self.widget,
            width=self.size,
            height=self.size,
            bg=self.widget.cget("fg_color"),
            highlightthickness=0
        )
        self.canvas.pack(pady=10)
        self._draw_spinner()
        
    def _draw_spinner(self):
        """Draw the spinner at the current angle."""
        # Clear canvas
        self.canvas.delete("all")
        
        # Calculate center and radius
        center_x = self.size / 2
        center_y = self.size / 2
        outer_radius = (self.size / 2) - 5
        inner_radius = outer_radius - 8
        
        # Draw spinning arc
        start_angle = self.angle
        extent = 60
        
        # Convert to oval coordinates
        x0 = center_x - outer_radius
        y0 = center_y - outer_radius
        x1 = center_x + outer_radius
        y1 = center_y + outer_radius
        
        # Draw arc
        self.canvas.create_arc(
            x0, y0, x1, y1,
            start=start_angle,
            extent=extent,
            style="arc",
            width=4,
            outline="#3a7ebf"
        )
        
    def start_animation(self):
        """Start the spinner animation."""
        if self.animation_running:
            return
            
        self.animation_running = True
        self.animation_thread = threading.Thread(target=self._animate_spinner, daemon=True)
        self.animation_thread.start()
        
    def stop_animation(self):
        """Stop the spinner animation."""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=0.2)
            
    def _animate_spinner(self):
        """Animate the spinner in a separate thread."""
        while self.animation_running and hasattr(self, "canvas"):
            # Update angle
            self.angle = (self.angle + 10) % 360
            
            # Schedule drawing on main thread
            if hasattr(self, "widget") and hasattr(self.widget, "after"):
                self.widget.after(0, self._draw_spinner)
                
            # Sleep for a bit
            time.sleep(self.spinner_speed)
            
    def set_progress(self, value):
        """Set the progress value (0.0 to 1.0)."""
        if self.mode == "progress" and not self.indeterminate:
            self.progress_value = max(0.0, min(1.0, value))
            if hasattr(self, "progress"):
                self.progress.set(self.progress_value)
                
    def set_text(self, text):
        """Set the loading text."""
        self.text = text
        if self.show_text and hasattr(self, "label"):
            self.label.configure(text=text)
            
    def on_unmount(self):
        """Handle component unmounting."""
        # Stop animation when component is unmounted
        self.stop_animation()
        super().on_unmount() 