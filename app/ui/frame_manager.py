#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame Manager for the WydBot application.
Handles frame transitions and ensures proper frame lifecycle management.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Type, Optional, Callable, Any, List, Tuple
import time

# Import the logger
from app.utils.logger import LoggerWrapper

# Global logger instance
logger = LoggerWrapper(name="frame_manager")


class BaseFrame(ctk.CTkFrame):
    """
    Base frame class for all application frames.
    Provides lifecycle methods and common functionality.
    """
    
    def __init__(self, master, frame_manager=None, **kwargs):
        """Initialize the base frame."""
        super().__init__(master, **kwargs)
        
        # Store frame manager reference
        self.frame_manager = frame_manager
        
        # Store child components
        self.children_components = {}
        
        # Flag to track if the frame is active
        self.is_active = False
        
        # Flag to track if the frame has been initialized
        self.is_initialized = False
        
        # Flag to track if the frame is being destroyed
        self.is_being_destroyed = False
    
    def on_init(self):
        """
        Initialize the frame when first created.
        This is called once when the frame is created.
        """
        self.is_initialized = True
        logger.debug(f"Frame {self.__class__.__name__} initialized")
    
    def on_enter(self, **kwargs):
        """
        Handle when the frame becomes active.
        This is called each time the frame is shown.
        """
        self.is_active = True
        logger.debug(f"Frame {self.__class__.__name__} entered")
    
    def on_leave(self):
        """
        Handle when the frame becomes inactive.
        This is called each time the frame is hidden.
        """
        self.is_active = False
        logger.debug(f"Frame {self.__class__.__name__} left")
    
    def on_update(self, **kwargs):
        """
        Handle when the frame needs to be updated.
        This is called when the frame is already active and needs to be updated.
        """
        logger.debug(f"Frame {self.__class__.__name__} updated")
    
    def clean_up(self):
        """
        Clean up resources when the frame is destroyed.
        This is called when the frame is about to be destroyed.
        """
        self.is_being_destroyed = True
        
        # Clean up child components
        for component_id, component in list(self.children_components.items()):
            try:
                if hasattr(component, 'clean_up') and callable(component.clean_up):
                    component.clean_up()
                if hasattr(component, 'destroy') and callable(component.destroy):
                    component.destroy()
            except Exception as e:
                logger.error(f"Error cleaning up component {component_id}: {e}")
        
        # Clear child components
        self.children_components.clear()
        
        logger.debug(f"Frame {self.__class__.__name__} cleaned up")
    
    def register_child(self, component):
        """
        Register a child component with this frame.
        
        Args:
            component: Child component to register
            
        Returns:
            The registered component
        """
        if self.is_being_destroyed:
            logger.warning(f"Attempted to register child component while frame {self.__class__.__name__} is being destroyed")
            return component
            
        # Generate a unique ID for the component
        component_id = f"{component.__class__.__name__}_{id(component)}"
        
        # Store the component
        self.children_components[component_id] = component
        
        return component
    
    def unregister_child(self, component):
        """
        Unregister a child component from this frame.
        
        Args:
            component: Child component to unregister
            
        Returns:
            bool: True if the component was unregistered, False otherwise
        """
        # Find the component ID
        component_id = None
        for cid, comp in self.children_components.items():
            if comp == component:
                component_id = cid
                break
        
        if component_id:
            # Remove the component
            del self.children_components[component_id]
            return True
        
        return False
    
    def destroy(self):
        """Override destroy to ensure clean up is called."""
        try:
            if not self.is_being_destroyed:
                self.clean_up()
        except Exception as e:
            logger.error(f"Error during frame destruction: {e}")
        finally:
            try:
                super().destroy()
            except Exception as e:
                logger.error(f"Error calling parent destroy: {e}")


class TransitionAnimation:
    """Handles frame transition animations."""
    
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    NONE = "none"
    
    def __init__(self, root, animation_type=FADE, duration=300):
        """Initialize a transition animation."""
        self.root = root
        self.animation_type = animation_type
        self.duration = duration
        self.frame_to_hide = None
        self.frame_to_show = None
        self.on_complete = None
        self.start_time = 0
        self.animation_id = None
    
    def start(self, frame_to_hide, frame_to_show, on_complete=None):
        """Start the transition animation."""
        # Cancel any running animation
        self.stop()
        
        self.frame_to_hide = frame_to_hide
        self.frame_to_show = frame_to_show
        self.on_complete = on_complete
        self.start_time = time.time() * 1000  # milliseconds
        
        # Configure initial state
        if self.animation_type == self.FADE:
            if self.frame_to_hide:
                self.frame_to_hide.configure(fg_color="transparent")
            if self.frame_to_show:
                self.frame_to_show.configure(fg_color="transparent")
                self.frame_to_show.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        elif self.animation_type in [self.SLIDE_LEFT, self.SLIDE_RIGHT, self.SLIDE_UP, self.SLIDE_DOWN]:
            if self.frame_to_hide:
                self.frame_to_hide.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # Set initial position for the new frame
            if self.frame_to_show:
                if self.animation_type == self.SLIDE_LEFT:
                    self.frame_to_show.place(relx=1, rely=0, relwidth=1, relheight=1)
                elif self.animation_type == self.SLIDE_RIGHT:
                    self.frame_to_show.place(relx=-1, rely=0, relwidth=1, relheight=1)
                elif self.animation_type == self.SLIDE_UP:
                    self.frame_to_show.place(relx=0, rely=1, relwidth=1, relheight=1)
                elif self.animation_type == self.SLIDE_DOWN:
                    self.frame_to_show.place(relx=0, rely=-1, relwidth=1, relheight=1)
        
        elif self.animation_type == self.NONE:
            # No animation, just show the new frame
            if self.frame_to_hide:
                self.frame_to_hide.place_forget()
            if self.frame_to_show:
                self.frame_to_show.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            if self.on_complete:
                self.on_complete()
            
            return
        
        # Start the animation loop
        self._animate()
    
    def _animate(self):
        """Handle animation updates."""
        current_time = time.time() * 1000
        elapsed = current_time - self.start_time
        progress = min(1.0, elapsed / self.duration)
        
        if self.animation_type == self.FADE:
            if self.frame_to_hide:
                opacity = 1.0 - progress
                # Use RGB values with opacity multiplier instead of hex with alpha
                light_color = (240, 240, 240)  # Light theme color
                dark_color = (50, 50, 50)      # Dark theme color
                light_color_with_opacity = tuple(int(c * opacity) for c in light_color)
                dark_color_with_opacity = tuple(int(c * opacity) for c in dark_color)
                self.frame_to_hide.configure(fg_color=(
                    f"#{light_color_with_opacity[0]:02x}{light_color_with_opacity[1]:02x}{light_color_with_opacity[2]:02x}", 
                    f"#{dark_color_with_opacity[0]:02x}{dark_color_with_opacity[1]:02x}{dark_color_with_opacity[2]:02x}"
                ))
            
            if self.frame_to_show:
                opacity = progress
                # Use RGB values with opacity multiplier instead of hex with alpha
                light_color = (240, 240, 240)  # Light theme color
                dark_color = (50, 50, 50)      # Dark theme color
                light_color_with_opacity = tuple(int(c * opacity) for c in light_color)
                dark_color_with_opacity = tuple(int(c * opacity) for c in dark_color)
                self.frame_to_show.configure(fg_color=(
                    f"#{light_color_with_opacity[0]:02x}{light_color_with_opacity[1]:02x}{light_color_with_opacity[2]:02x}", 
                    f"#{dark_color_with_opacity[0]:02x}{dark_color_with_opacity[1]:02x}{dark_color_with_opacity[2]:02x}"
                ))
        
        elif self.animation_type in [self.SLIDE_LEFT, self.SLIDE_RIGHT, self.SLIDE_UP, self.SLIDE_DOWN]:
            if self.animation_type == self.SLIDE_LEFT:
                if self.frame_to_hide:
                    self.frame_to_hide.place(relx=-progress, rely=0, relwidth=1, relheight=1)
                if self.frame_to_show:
                    self.frame_to_show.place(relx=1 - progress, rely=0, relwidth=1, relheight=1)
            
            elif self.animation_type == self.SLIDE_RIGHT:
                if self.frame_to_hide:
                    self.frame_to_hide.place(relx=progress, rely=0, relwidth=1, relheight=1)
                if self.frame_to_show:
                    self.frame_to_show.place(relx=progress - 1, rely=0, relwidth=1, relheight=1)
            
            elif self.animation_type == self.SLIDE_UP:
                if self.frame_to_hide:
                    self.frame_to_hide.place(relx=0, rely=-progress, relwidth=1, relheight=1)
                if self.frame_to_show:
                    self.frame_to_show.place(relx=0, rely=1 - progress, relwidth=1, relheight=1)
            
            elif self.animation_type == self.SLIDE_DOWN:
                if self.frame_to_hide:
                    self.frame_to_hide.place(relx=0, rely=progress, relwidth=1, relheight=1)
                if self.frame_to_show:
                    self.frame_to_show.place(relx=0, rely=progress - 1, relwidth=1, relheight=1)
        
        # Continue animation or complete
        if progress < 1.0:
            self.animation_id = self.root.after(16, self._animate)  # ~60 FPS
        else:
            self._animation_complete()
    
    def _animation_complete(self):
        """Handle animation completion."""
        # Reset frame positions
        if self.frame_to_hide:
            self.frame_to_hide.place_forget()
        
        if self.frame_to_show:
            self.frame_to_show.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.frame_to_show.configure(fg_color="transparent")  # Reset to default
        
        # Call completion callback
        if self.on_complete:
            self.on_complete()
    
    def stop(self):
        """Stop the current animation."""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None


class FrameManager:
    """
    Manages frames and transitions between them.
    Ensures proper frame lifecycle management.
    """
    
    def __init__(self, container, default_frame=None):
        """Initialize the frame manager."""
        self.container = container
        self.root = container.winfo_toplevel()
        self.frames = {}
        self.frame_history = []
        self.current_frame_id = None
        self.default_frame = default_frame
        self.animation_enabled = True
        self.default_animation = TransitionAnimation.FADE
        self.animation_duration = 300
        self.current_animation = None
        
        logger.info("Frame manager initialized")
    
    def register_frame(self, frame_id, frame_class, **kwargs):
        """Register a frame class with the manager."""
        logger.debug(f"Registering frame: {frame_id}")
        
        if frame_id in self.frames:
            logger.warning(f"Frame {frame_id} already registered, replacing")
            # Clean up existing frame
            self.destroy_frame(frame_id)
        
        self.frames[frame_id] = {
            "class": frame_class,
            "instance": None,
            "kwargs": kwargs
        }
        
        return frame_id
    
    def create_frame(self, frame_id, **kwargs):
        """Create an instance of a registered frame."""
        if frame_id not in self.frames:
            logger.error(f"Frame {frame_id} not registered")
            return False
        
        if self.frames[frame_id]["instance"] is not None:
            logger.warning(f"Frame {frame_id} already created, returning existing instance")
            return True
        
        logger.info(f"=== FRAME CREATION START: {frame_id} ===")
        
        frame_class = self.frames[frame_id]["class"]
        kwargs = self.frames[frame_id]["kwargs"].copy()
        
        try:
            # Create the frame instance
            logger.info(f"Instantiating frame {frame_id} with class {frame_class.__name__}")
            frame = frame_class(self.container, frame_manager=self, **kwargs)
            logger.info(f"Frame {frame_id} instantiated successfully")
            
            self.frames[frame_id]["instance"] = frame
            
            # Initialize the frame
            logger.info(f"Calling on_init for frame {frame_id}")
            frame.on_init()
            logger.info(f"on_init completed for frame {frame_id}")
            
            logger.info(f"=== FRAME CREATION COMPLETE: {frame_id} ===")
            return True
        except Exception as e:
            logger.error(f"Error creating frame {frame_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.info(f"=== FRAME CREATION FAILED: {frame_id} ===")
            return False
    
    def destroy_frame(self, frame_id):
        """Destroy a frame instance."""
        if frame_id not in self.frames:
            logger.error(f"Frame {frame_id} not registered")
            return False
        
        if self.frames[frame_id]["instance"] is None:
            logger.warning(f"Frame {frame_id} not created, nothing to destroy")
            return True
        
        logger.info(f"=== FRAME DESTRUCTION START: {frame_id} ===")
        logger.info(f"Frame {frame_id} will be destroyed")
        
        frame = self.frames[frame_id]["instance"]
        
        # Log frame properties before destruction
        if hasattr(frame, "winfo_ismapped") and callable(frame.winfo_ismapped):
            logger.info(f"Frame {frame_id} is mapped: {frame.winfo_ismapped()}")
        
        if hasattr(frame, "winfo_exists") and callable(frame.winfo_exists):
            logger.info(f"Frame {frame_id} exists: {frame.winfo_exists()}")
        
        if hasattr(frame, "winfo_children") and callable(frame.winfo_children):
            logger.info(f"Frame {frame_id} has {len(frame.winfo_children())} children")
        
        # Call cleanup method
        try:
            logger.info(f"Calling clean_up on frame {frame_id}")
            frame.clean_up()
            logger.info(f"clean_up completed for frame {frame_id}")
        except Exception as e:
            logger.error(f"Error in frame.clean_up(): {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Remove from container
        try:
            logger.info(f"Calling place_forget on frame {frame_id}")
            frame.place_forget()
            logger.info(f"place_forget completed for frame {frame_id}")
        except Exception as e:
            logger.error(f"Error in frame.place_forget(): {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Destroy the frame
        try:
            logger.info(f"Calling destroy on frame {frame_id}")
            frame.destroy()
            logger.info(f"destroy completed for frame {frame_id}")
        except Exception as e:
            logger.error(f"Error in frame.destroy(): {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Remove the instance reference
        logger.info(f"Setting instance to None for frame {frame_id}")
        self.frames[frame_id]["instance"] = None
        
        # Force update to reflect changes
        try:
            self.container.update_idletasks()
            logger.info("Container updated after frame destruction")
        except Exception as e:
            logger.error(f"Error updating container: {e}")
        
        logger.info(f"=== FRAME DESTRUCTION COMPLETE: {frame_id} ===")
        return True
    
    def show_frame(self, frame_id, animation_type=None, animation_duration=None, add_to_history=True, **kwargs):
        """Show a frame by its ID."""
        logger.info(f"Request to show frame: {frame_id}")
        
        # Check if frame is registered
        if frame_id not in self.frames:
            logger.error(f"Frame {frame_id} is not registered")
            return False
        
        # Special handling for dashboard transitions
        if frame_id == "dashboard":
            logger.info("Dashboard transition detected - ensuring direct frame switch")
            # Force no animation for dashboard transitions
            animation_type = TransitionAnimation.NONE
            
            # Additional debugging for dashboard transitions
            logger.info(f"Dashboard frame instance exists: {self.frames[frame_id]['instance'] is not None}")
            if self.frames[frame_id]["instance"] is None:
                logger.info("Dashboard frame needs to be created")
            
        # If we're already showing this frame, just update it
        if self.current_frame_id == frame_id:
            logger.info(f"Frame {frame_id} is already showing, updating it")
            current_frame = self.frames[frame_id]["instance"]
            if current_frame:
                try:
                    current_frame.on_update(**kwargs)
                    logger.info(f"Frame {frame_id} updated successfully")
                except Exception as e:
                    logger.error(f"Error updating frame {frame_id}: {e}")
            return True
        
        # Stop any current animation
        if self.current_animation:
            logger.info("Stopping current animation")
            try:
                self.current_animation.stop()
                self.current_animation = None
            except Exception as e:
                logger.error(f"Error stopping animation: {e}")
                self.current_animation = None
        
        # Get animation settings
        animation_type = animation_type or self.default_animation
        animation_duration = animation_duration or self.animation_duration
        
        # Get current frame (if any)
        current_frame = None
        old_frame_id = self.current_frame_id
        if self.current_frame_id:
            try:
                current_frame = self.frames[self.current_frame_id]["instance"]
                logger.info(f"Current frame is {self.current_frame_id}")
                
                # CRITICAL FIX: Always hide the current frame first
                if current_frame and hasattr(current_frame, 'place_forget'):
                    try:
                        logger.info(f"Explicitly hiding current frame: {self.current_frame_id}")
                        current_frame.place_forget()
                        logger.info(f"Current frame {self.current_frame_id} hidden")
                        # Force update to ensure the frame is hidden
                        self.root.update_idletasks()
                    except Exception as e:
                        logger.error(f"Error hiding current frame: {e}")
            except Exception as e:
                logger.error(f"Error getting current frame: {e}")
        
        # Create frame if it doesn't exist
        if self.frames[frame_id]["instance"] is None:
            logger.info(f"Creating frame instance for {frame_id}")
            success = self.create_frame(frame_id, **kwargs)
            if not success:
                logger.error(f"Failed to create frame {frame_id}")
                return False
            logger.info(f"Frame {frame_id} created successfully")
        
        # Update history
        if add_to_history and self.current_frame_id:
            self.frame_history.append(self.current_frame_id)
            logger.info(f"Added {self.current_frame_id} to frame history")
        
        # Set new current frame
        self.current_frame_id = frame_id
        logger.info(f"Current frame changed from {old_frame_id} to {frame_id}")
        
        # Call lifecycle methods for old frame (on_leave)
        if current_frame:
            try:
                logger.info(f"Calling on_leave for frame {old_frame_id}")
                current_frame.on_leave()
            except Exception as e:
                logger.error(f"Error calling on_leave for frame {old_frame_id}: {e}")
        
        # No animation path
        if not self.animation_enabled or animation_type == TransitionAnimation.NONE:
            logger.info("No animation, directly switching frames")
            try:
                # Place the new frame
                logger.info(f"Showing new frame: {frame_id}")
                new_frame = self.frames[frame_id]["instance"]
                new_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                
                # Ensure it's visible on top
                new_frame.lift()
                logger.info(f"New frame placed and lifted")
                
                # Call on_enter
                try:
                    logger.info(f"Calling on_enter for frame {frame_id}")
                    new_frame.on_enter(**kwargs)
                    logger.info(f"on_enter completed for frame {frame_id}")
                except Exception as e:
                    logger.error(f"Error calling on_enter for frame {frame_id}: {e}")
                    
                # Force update
                try:
                    self.root.update_idletasks()
                    logger.info("UI updated after frame transition")
                except Exception as e:
                    logger.error(f"Error updating UI: {e}")
            except Exception as e:
                logger.error(f"Frame transition error: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return False
        else:
            # With animation path - implement this as needed
            logger.info(f"Animation path not fully implemented yet")
            # Fallback to no animation
            try:
                # Place the new frame
                logger.info(f"Showing new frame: {frame_id}")
                new_frame = self.frames[frame_id]["instance"]
                new_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                
                # Call on_enter
                try:
                    logger.info(f"Calling on_enter for frame {frame_id}")
                    new_frame.on_enter(**kwargs)
                    logger.info(f"on_enter completed for frame {frame_id}")
                except Exception as e:
                    logger.error(f"Error calling on_enter for frame {frame_id}: {e}")
            except Exception as e:
                logger.error(f"Frame transition error: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return False
            
        logger.info(f"Frame transition completed: {old_frame_id} -> {frame_id}")
        return True
    
    def go_back(self, **kwargs):
        """Go back to the previous frame."""
        if not self.frame_history:
            logger.warning("No frame history to go back to")
            return False
        
        # Get the previous frame ID
        previous_frame_id = self.frame_history.pop()
        
        # Show the previous frame
        return self.show_frame(
            previous_frame_id,
            animation_type=TransitionAnimation.SLIDE_RIGHT,
            add_to_history=False,
            **kwargs
        )
    
    def clear_history(self):
        """Clear the frame history."""
        self.frame_history.clear()
        logger.debug("Frame history cleared")
    
    def get_frame_instance(self, frame_id):
        """Get a frame instance if it exists."""
        if frame_id not in self.frames:
            return None
        
        return self.frames[frame_id]["instance"]
    
    def initialize(self):
        """Initialize the frame manager and show the default frame."""
        logger.info("Initializing frame manager")
        
        if self.default_frame:
            # Register the default frame if it's not already registered
            default_id = None
            for frame_id, frame_data in self.frames.items():
                if frame_data["class"] == self.default_frame:
                    default_id = frame_id
                    break
            
            if default_id is None:
                default_id = "default_frame"
                self.register_frame(default_id, self.default_frame)
            
            # Show the default frame
            self.show_frame(default_id, animation_type=TransitionAnimation.NONE)
    
    def cleanup(self):
        """Clean up all frames and resources."""
        logger.info("Cleaning up frame manager")
        
        # Stop any current animation
        if self.current_animation:
            self.current_animation.stop()
            self.current_animation = None
        
        # Destroy all frame instances
        for frame_id in list(self.frames.keys()):
            self.destroy_frame(frame_id)
        
        # Clear history
        self.frame_history.clear()
        self.current_frame_id = None

    def animation_complete(self):
        """Called when the animation is complete."""
        try:
            # Force current frame to update
            logger.info("Animation complete, updating idletasks")
            self.root.update_idletasks()
            logger.info("UI update completed after animation")
        except Exception as e:
            logger.error(f"Error updating idletasks after animation: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            self.current_animation = None 