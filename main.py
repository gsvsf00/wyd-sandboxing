#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WydBot - Desktop Application

Main entry point for the WydBot desktop application.
"""

import os
import sys
import logging
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
import traceback

# Add app to path
app_path = os.path.dirname(os.path.abspath(__file__))
if app_path not in sys.path:
    sys.path.append(app_path)

# Import app modules
from app.utils.logging_config import setup_logging, get_logger
from app.utils.config import load_config
from app.core.app_controller import AppController

# Set up logging
setup_logging()
logger = get_logger("main")

def main():
    """Main entry point for the application."""
    try:
        logger.info("Starting WydBot application")
        
        # Set appearance mode and default theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create root window
        root = ctk.CTk()
        
        # Set window icon if available
        try:
            icon_path = os.path.join(app_path, "app", "resources", "images", "icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Could not set application icon: {e}")
        
        # Load configuration
        config = load_config()
        
        # Create app controller
        app_controller = AppController(root, config)
        
        # Run the application
        app_controller.run()
        
        logger.info("Application exited normally")
        return 0
        
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        
        # Show error message
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Critical Error",
                f"An unhandled exception occurred:\n\n{str(e)}\n\n"
                "The application will now exit. Please check the logs for details."
            )
        except:
            pass
            
        return 1
        
if __name__ == "__main__":
    sys.exit(main()) 