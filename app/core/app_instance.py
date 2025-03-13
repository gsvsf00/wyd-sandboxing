"""
Module for managing the global application instance.
This breaks the circular dependency between app_controller and frames.
"""

# App instance singleton
_app_instance = None

def get_app_instance():
    """Get the global application instance."""
    global _app_instance
    return _app_instance

def set_app_instance(instance):
    """Set the global application instance."""
    global _app_instance
    _app_instance = instance
    print(f"App instance set: {_app_instance is not None}")  # Debug print 