#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base Component for WydBot UI.
Provides a foundation for all UI components with state management and lifecycle methods.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional, List, Callable, Type
from uuid import uuid4

# Import utilities
from app.utils.logger import LoggerWrapper
from app.ui.utils import debounce

# Global logger instance
logger = LoggerWrapper(name="base_component")


class BaseComponent:
    """
    Base class for all UI components.
    Provides common functionality for state management, event handling, and lifecycle methods.
    """
    
    def __init__(self, master, **kwargs):
        """
        Initialize the base component.
        
        Args:
            master: Parent widget
            **kwargs: Additional configuration parameters
        """
        self.master = master
        self.id = kwargs.pop("id", f"{self.__class__.__name__}-{uuid4().hex[:8]}")
        self.state = {}
        self.props = kwargs
        self.children = []
        self.event_handlers = {}
        self.is_mounted = False
        self.is_destroyed = False
        self.refresh_scheduled = False
        self.dirty = False
        
        # Default props that can be overridden
        self.default_props = {
            "padx": 5,
            "pady": 5,
            "width": None,
            "height": None,
        }
        
        # Merge default props with provided props
        for key, value in self.default_props.items():
            if key not in self.props:
                self.props[key] = value
        
        # Create the main widget during initialization
        self.widget = self._create_widget()
        
        # If the master is a BaseComponent, register this component as a child
        if hasattr(master, "register_child") and callable(getattr(master, "register_child")):
            master.register_child(self)
    
    def _create_widget(self):
        """
        Create the main widget for this component.
        Override in subclasses to create specific widgets.
        
        Returns:
            The created widget
        """
        # Default implementation creates a frame
        return ctk.CTkFrame(self.master)
    
    def render(self):
        """
        Render the component's visual elements.
        Override in subclasses to implement custom rendering.
        """
        # Default implementation does nothing
        logger.debug(f"Default render method called for component {self.id}")
        pass
    
    def update(self):
        """Update the component based on current state and props."""
        if not self.is_mounted or self.is_destroyed:
            return
        
        # Force a re-render
        self.render()
        
        # Mark as clean
        self.dirty = False
        self.refresh_scheduled = False
    
    def mount(self):
        """Mount the component, initializing its visual elements."""
        if self.is_mounted or self.is_destroyed:
            logger.debug(f"Component {self.id} already mounted or destroyed, skipping mount")
            return
        
        try:
            logger.debug(f"Mounting component {self.id}")
            
            # Call render to initialize visual elements
            self.render()
            
            # Mark as mounted
            self.is_mounted = True
            
            # Mount children
            for child in self.children:
                try:
                    if hasattr(child, "mount") and callable(child.mount):
                        child.mount()
                except Exception as e:
                    logger.error(f"Error mounting child component: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Call on_mount lifecycle method
            self.on_mount()
            
            # Ensure widget is properly packed/placed/gridded if not already
            if hasattr(self.widget, "winfo_ismapped") and not self.widget.winfo_ismapped():
                logger.debug(f"Component {self.id} widget not mapped, attempting to show it")
                # Try default packing if not already managed
                if hasattr(self.master, "pack_propagate"):
                    self.widget.pack(fill=tk.BOTH, expand=True)
            
            logger.debug(f"Component {self.id} mounted successfully")
        except Exception as e:
            logger.error(f"Error mounting component {self.id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def unmount(self):
        """Unmount the component, preparing for destruction."""
        if not self.is_mounted or self.is_destroyed:
            return
        
        # Unmount children first
        for child in self.children:
            if hasattr(child, "unmount") and callable(child.unmount):
                child.unmount()
        
        # Call on_unmount lifecycle method
        self.on_unmount()
        
        # Mark as unmounted
        self.is_mounted = False
    
    def destroy(self):
        """Destroy the component and clean up resources."""
        if self.is_destroyed:
            return
        
        # Unmount first if still mounted
        if self.is_mounted:
            self.unmount()
        
        # Destroy children
        for child in list(self.children):
            if hasattr(child, "destroy") and callable(child.destroy):
                child.destroy()
        
        # Clear children list
        self.children.clear()
        
        # Clear event handlers
        for event_type in list(self.event_handlers.keys()):
            self.remove_all_event_handlers(event_type)
        
        # Call on_destroy lifecycle method
        self.on_destroy()
        
        # Destroy the widget
        if self.widget and hasattr(self.widget, "destroy"):
            self.widget.destroy()
        
        # Mark as destroyed
        self.is_destroyed = True
    
    def request_update(self):
        """Request an update on the next frame."""
        if not self.is_mounted or self.is_destroyed or self.refresh_scheduled:
            return
        
        # Mark as dirty and schedule an update
        self.dirty = True
        self.refresh_scheduled = True
        
        # Schedule the update using after_idle to avoid refresh loops
        if hasattr(self.master, "after_idle"):
            self.master.after_idle(self._deferred_update)
        else:
            # Fallback to immediate update
            self._deferred_update()
    
    @debounce(0.05)  # 50ms debounce to prevent excessive updates
    def _deferred_update(self):
        """Handle deferred updates."""
        if not self.is_mounted or self.is_destroyed:
            return
        
        self.update()
    
    def set_state(self, new_state, request_update=True):
        """
        Update the component state.
        
        Args:
            new_state: Dictionary of state changes
            request_update: Whether to request an update after state change
        """
        # Update state
        self.state.update(new_state)
        
        # Request update if needed
        if request_update:
            self.request_update()
    
    def get_state(self, key=None, default=None):
        """
        Get a state value or the entire state.
        
        Args:
            key: Specific state key to get, or None for entire state
            default: Default value if key not found
            
        Returns:
            The state value or entire state
        """
        if key is None:
            return self.state.copy()
        
        return self.state.get(key, default)
    
    def set_prop(self, key, value, request_update=True):
        """
        Set a component property.
        
        Args:
            key: Property key
            value: Property value
            request_update: Whether to request an update after prop change
        """
        # Update prop
        self.props[key] = value
        
        # Request update if needed
        if request_update:
            self.request_update()
    
    def get_prop(self, key, default=None):
        """
        Get a property value.
        
        Args:
            key: Property key
            default: Default value if key not found
            
        Returns:
            The property value
        """
        return self.props.get(key, default)
    
    def add_event_handler(self, event_type, handler):
        """
        Add an event handler.
        
        Args:
            event_type: Type of event
            handler: Event handler function
            
        Returns:
            The event handler
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        return handler
    
    def remove_event_handler(self, event_type, handler):
        """
        Remove an event handler.
        
        Args:
            event_type: Type of event
            handler: Event handler to remove
            
        Returns:
            True if removed, False otherwise
        """
        if event_type not in self.event_handlers:
            return False
        
        if handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            return True
        
        return False
    
    def remove_all_event_handlers(self, event_type):
        """
        Remove all event handlers for a specific event type.
        
        Args:
            event_type: Type of event
        """
        if event_type in self.event_handlers:
            self.event_handlers[event_type] = []
    
    def trigger_event(self, event_type, event_data=None):
        """
        Trigger an event, calling all handlers.
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            True if any handlers were called, False otherwise
        """
        if event_type not in self.event_handlers:
            return False
        
        for handler in self.event_handlers[event_type]:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
        
        return len(self.event_handlers[event_type]) > 0
    
    def register_child(self, child):
        """
        Register a child component.
        
        Args:
            child: Child component to register
            
        Returns:
            The child component
        """
        if child not in self.children:
            self.children.append(child)
        
        return child
    
    def unregister_child(self, child):
        """
        Unregister a child component.
        
        Args:
            child: Child component to unregister
            
        Returns:
            True if removed, False otherwise
        """
        if child in self.children:
            self.children.remove(child)
            return True
        
        return False
    
    # Lifecycle methods that can be overridden by subclasses
    
    def on_mount(self):
        """Called when the component is mounted."""
        try:
            logger.debug(f"Component {self.id} on_mount called")
            # Subclasses can override this method to perform actions when mounted
        except Exception as e:
            logger.error(f"Error in on_mount for component {self.id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def on_unmount(self):
        """Called when the component is unmounted."""
        pass
    
    def on_destroy(self):
        """Called when the component is destroyed."""
        pass
    
    def on_state_change(self, changed_keys):
        """
        Called when the component state changes.
        
        Args:
            changed_keys: List of state keys that changed
        """
        pass
    
    def on_prop_change(self, changed_keys):
        """
        Called when the component props change.
        
        Args:
            changed_keys: List of prop keys that changed
        """
        pass


class ComponentFactory:
    """
    Factory for creating component instances.
    Provides a central place to register and create components.
    """
    
    _component_registry = {}
    
    @classmethod
    def register_component(cls, component_name, component_class):
        """
        Register a component class.
        
        Args:
            component_name: Name to register the component under
            component_class: Component class to register
            
        Returns:
            The component class
        """
        cls._component_registry[component_name] = component_class
        return component_class
    
    @classmethod
    def create_component(cls, component_name, master, **kwargs):
        """
        Create a component instance.
        
        Args:
            component_name: Name of the component to create
            master: Parent widget
            **kwargs: Additional arguments for the component
            
        Returns:
            The created component
        """
        if component_name not in cls._component_registry:
            logger.error(f"Component {component_name} not registered")
            return None
        
        component_class = cls._component_registry[component_name]
        return component_class(master, **kwargs)
    
    @classmethod
    def get_component_class(cls, component_name):
        """
        Get a component class.
        
        Args:
            component_name: Name of the component class
            
        Returns:
            The component class or None if not found
        """
        return cls._component_registry.get(component_name)


def register_component(component_name):
    """
    Decorator to register a component class.
    
    Args:
        component_name: Name to register the component under
        
    Returns:
        Decorator function
    """
    def decorator(component_class):
        return ComponentFactory.register_component(component_name, component_class)
    return decorator 