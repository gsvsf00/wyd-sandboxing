import tkinter as tk
import customtkinter as ctk
from typing import Any, Dict, Optional

from app.utils.logger import LoggerWrapper

class BaseFrame(ctk.CTkFrame):
    """
    Base frame class that all application frames should inherit from.
    Provides lifecycle methods and common functionality.
    """
    
    def __init__(self, master, **kwargs):
        """
        Initialize the base frame.
        
        Args:
            master: Parent widget
            **kwargs: Additional arguments to pass to the superclass constructor
        """
        super().__init__(master, **kwargs)
        self.logger = LoggerWrapper(name=f"frame.{self.__class__.__name__}")
        
        # Frame state
        self._initialized = False
        self._active = False
        
        # Config
        self.configure(corner_radius=0)
        
    def on_init(self):
        """
        Called when the frame is first created.
        Use this for one-time initialization.
        """
        if self._initialized:
            return
            
        try:
            self.logger.debug(f"Initializing {self.__class__.__name__}")
            # Base implementation does nothing, but marks as initialized
            self._initialized = True
        except Exception as e:
            self.logger.error(f"Error in on_init: {e}", exc_info=True)
        
    def on_enter(self):
        """
        Called when the frame becomes visible.
        Use this to refresh data, update UI, etc.
        """
        try:
            self.logger.debug(f"Entering {self.__class__.__name__}")
            self._active = True
            # Base implementation does nothing
        except Exception as e:
            self.logger.error(f"Error in on_enter: {e}", exc_info=True)
        
    def on_exit(self):
        """
        Called when the frame is about to be hidden.
        Use this to save data, stop timers, etc.
        """
        try:
            self.logger.debug(f"Exiting {self.__class__.__name__}")
            self._active = False
            # Base implementation does nothing
        except Exception as e:
            self.logger.error(f"Error in on_exit: {e}", exc_info=True)
        
    def is_active(self) -> bool:
        """
        Check if the frame is currently active/visible.
        
        Returns:
            bool: True if the frame is active, False otherwise
        """
        return self._active
        
    def is_initialized(self) -> bool:
        """
        Check if the frame has been initialized.
        
        Returns:
            bool: True if the frame has been initialized, False otherwise
        """
        return self._initialized
        
    def refresh(self):
        """
        Refresh the frame's content.
        Call this when data has changed and the UI needs to be updated.
        """
        try:
            self.logger.debug(f"Refreshing {self.__class__.__name__}")
            # Base implementation does nothing
        except Exception as e:
            self.logger.error(f"Error in refresh: {e}", exc_info=True)
            
    def get_frame_id(self) -> str:
        """
        Get the frame's ID.
        
        Returns:
            str: The frame ID
        """
        # By default, use the lowercase class name without "frame"
        class_name = self.__class__.__name__.lower()
        if class_name.endswith("frame"):
            return class_name[:-5]
        return class_name 