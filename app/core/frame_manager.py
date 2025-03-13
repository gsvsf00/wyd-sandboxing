import tkinter as tk
import customtkinter as ctk
import time
import threading
from typing import Dict, Type, Optional, Any

from app.utils.logger import LoggerWrapper

class FrameManager:
    """
    Manages frame transitions and lifecycle in the application.
    Handles frame registration, creation, destruction, and transitions.
    """
    
    def __init__(self, container: ctk.CTkFrame):
        """
        Initialize the frame manager.
        
        Args:
            container: The container frame where frames will be displayed
        """
        self.logger = LoggerWrapper(name="frame_manager")
        self.container = container
        self.frames = {}  # Registered frame classes
        self.frame_instances = {}  # Currently instantiated frame instances
        self.current_frame = None  # Currently visible frame
        self.transitions_enabled = True  # For preventing race conditions
        self.transition_in_progress = False  # Flag to prevent concurrent transitions
        
    def register_frame(self, frame_id: str, frame_class: Type):
        """
        Register a frame class with the manager.
        
        Args:
            frame_id: Unique identifier for the frame
            frame_class: The frame class to register
        """
        try:
            self.logger.debug(f"Registering frame: {frame_id}")
            self.frames[frame_id] = frame_class
        except Exception as e:
            self.logger.error(f"Error registering frame {frame_id}: {e}", exc_info=True)
    
    def is_frame_registered(self, frame_id: str) -> bool:
        """
        Check if a frame is registered.
        
        Args:
            frame_id: The frame ID to check
            
        Returns:
            bool: True if the frame is registered, False otherwise
        """
        return frame_id in self.frames
    
    def create_frame(self, frame_id: str, **kwargs) -> Optional[ctk.CTkFrame]:
        """
        Create a frame instance.
        
        Args:
            frame_id: The ID of the frame to create
            **kwargs: Additional arguments to pass to the frame constructor
            
        Returns:
            The created frame instance or None if creation failed
        """
        try:
            if frame_id not in self.frames:
                self.logger.error(f"Frame {frame_id} not registered")
                return None
                
            # Create the frame instance
            self.logger.debug(f"Creating frame instance: {frame_id}")
            frame_class = self.frames[frame_id]
            frame = frame_class(self.container, **kwargs)
            
            # Call lifecycle method for initialization
            if hasattr(frame, 'on_init'):
                frame.on_init()
                
            # Store the instance
            self.frame_instances[frame_id] = frame
            return frame
            
        except Exception as e:
            self.logger.error(f"Error creating frame {frame_id}: {e}", exc_info=True)
            return None
    
    def destroy_frame(self, frame_id: str) -> bool:
        """
        Destroy a frame instance.
        
        Args:
            frame_id: The ID of the frame to destroy
            
        Returns:
            bool: True if the frame was destroyed, False otherwise
        """
        try:
            if frame_id not in self.frame_instances:
                self.logger.warning(f"Frame {frame_id} not instantiated, can't destroy")
                return False
                
            frame = self.frame_instances[frame_id]
            
            # Call lifecycle method for cleanup
            if hasattr(frame, 'on_exit'):
                frame.on_exit()
                
            # Destroy the frame widget
            frame.destroy()
            
            # Remove from instances
            del self.frame_instances[frame_id]
            return True
            
        except Exception as e:
            self.logger.error(f"Error destroying frame {frame_id}: {e}", exc_info=True)
            return False
    
    def show_frame(self, frame_id: str, **kwargs) -> bool:
        """
        Show a frame by ID.
        
        Args:
            frame_id: ID of the frame to show
            **kwargs: Additional arguments to pass to the frame's on_enter method
            
        Returns:
            bool: True if the frame was shown successfully, False otherwise
        """
        try:
            self.logger.info(f"Request to show frame: {frame_id}")
            
            # Check if frame is registered
            if not self.is_frame_registered(frame_id):
                self.logger.error(f"Frame {frame_id} is not registered")
                return False
            
            # Get current frame
            current_frame = self.get_current_frame()
            
            # If current frame exists, call on_leave method
            if current_frame:
                try:
                    if hasattr(current_frame, "on_leave"):
                        current_frame.on_leave()
                except Exception as e:
                    self.logger.error(f"Error in frame {frame_id} on_leave: {e}", exc_info=True)
            
            # Create the new frame if it doesn't exist
            new_frame = self.get_frame(frame_id)
            if not new_frame:
                new_frame = self.create_frame(frame_id, **kwargs)
                if not new_frame:
                    self.logger.error(f"Failed to create frame {frame_id}")
                    return False
            
            # Hide current frame
            if current_frame:
                current_frame.grid_forget()  # Use grid_forget instead of pack_forget
            
            # Show new frame
            new_frame.grid(row=0, column=0, sticky="nsew")  # Use grid instead of pack
            
            # Call on_enter method
            try:
                if hasattr(new_frame, "on_enter"):
                    new_frame.on_enter(**kwargs)
            except Exception as e:
                self.logger.error(f"Error in frame {frame_id} on_enter: {e}", exc_info=True)
            
            # Update current frame
            self.current_frame = frame_id
            
            return True
        except Exception as e:
            self.logger.error(f"Error showing frame {frame_id}: {e}", exc_info=True)
            return False
    
    def transition_to_frame(self, frame_id: str, transition_time: float = 0.3, **kwargs) -> bool:
        """
        Transition to a frame with animation.
        
        Args:
            frame_id: The ID of the frame to transition to
            transition_time: The time for the transition animation
            **kwargs: Additional arguments to pass to the frame constructor if it needs to be created
            
        Returns:
            bool: True if the transition was initiated successfully, False otherwise
        """
        if not self.transitions_enabled:
            # Fall back to regular show if transitions are disabled
            return self.show_frame(frame_id, **kwargs)
            
        try:
            self.logger.info(f"Request to transition to frame: {frame_id}")
            
            # Check if a transition is already in progress
            if self.transition_in_progress:
                self.logger.warning(f"Transition already in progress, ignoring request to transition to {frame_id}")
                return False
                
            self.transition_in_progress = True
            
            # Run the transition in a separate thread to avoid blocking the UI
            def transition_thread():
                try:
                    # Create the new frame if needed but don't show it yet
                    if frame_id not in self.frame_instances:
                        new_frame = self.create_frame(frame_id, **kwargs)
                        if not new_frame:
                            self.logger.error(f"Failed to create frame {frame_id}")
                            self.transition_in_progress = False
                            return False
                    
                    # Use the main thread for the actual transition
                    self.container.after(0, lambda: self._perform_transition(frame_id, transition_time))
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Error in transition thread: {e}", exc_info=True)
                    self.transition_in_progress = False
                    return False
            
            # Start the transition thread
            threading.Thread(target=transition_thread).start()
            return True
            
        except Exception as e:
            self.logger.error(f"Error initiating transition to {frame_id}: {e}", exc_info=True)
            self.transition_in_progress = False
            return False
    
    def _perform_transition(self, frame_id: str, transition_time: float):
        """
        Perform the actual transition animation.
        This should be called from the main thread.
        
        Args:
            frame_id: The ID of the frame to transition to
            transition_time: The time for the transition animation
        """
        try:
            # Get the frames
            old_frame_id = self.current_frame
            old_frame = self.frame_instances.get(old_frame_id)
            new_frame = self.frame_instances.get(frame_id)
            
            if not new_frame:
                self.logger.error(f"Frame {frame_id} not instantiated for transition")
                self.transition_in_progress = False
                return
                
            # Call lifecycle methods
            if old_frame and hasattr(old_frame, 'on_exit'):
                old_frame.on_exit()
                
            if hasattr(new_frame, 'on_enter'):
                new_frame.on_enter()
                
            # Simple fade-out/fade-in transition
            # Note: In a real app, you'd want to use proper animation frameworks
            # For now we'll just use a simple delay to simulate a transition
            
            # Hide old frame
            if old_frame:
                old_frame.pack_forget()
                
            # Show new frame
            new_frame.pack(side="top", fill="both", expand=True)
            
            # Update current frame
            self.current_frame = frame_id
            
            # Release transition lock
            self.transition_in_progress = False
            
            self.logger.info(f"Transition to frame {frame_id} complete")
            
        except Exception as e:
            self.logger.error(f"Error performing transition to {frame_id}: {e}", exc_info=True)
            self.transition_in_progress = False
    
    def get_current_frame_id(self) -> Optional[str]:
        """
        Get the ID of the currently visible frame.
        
        Returns:
            str: The ID of the current frame, or None if no frame is visible
        """
        return self.current_frame
    
    def get_current_frame(self) -> Optional[ctk.CTkFrame]:
        """
        Get the instance of the currently visible frame.
        
        Returns:
            The current frame instance, or None if no frame is visible
        """
        if not self.current_frame:
            return None
        return self.frame_instances.get(self.current_frame)
    
    def get_frame(self, frame_id: str) -> Optional[ctk.CTkFrame]:
        """
        Get a frame instance by ID.
        
        Args:
            frame_id: The ID of the frame to get
            
        Returns:
            The frame instance, or None if not found
        """
        return self.frame_instances.get(frame_id) 