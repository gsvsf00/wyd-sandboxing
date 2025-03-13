"""
Debounce utility for UI operations.
Prevents functions from being called too frequently.
"""

import time
import threading
from functools import wraps
from typing import Callable, Any, Dict, Optional

# Dictionary to store the last call time for each function
_last_call_time: Dict[Callable, float] = {}
_timers: Dict[Callable, threading.Timer] = {}


def debounce(wait_time: float = 0.3):
    """
    Decorator to debounce a function call.
    
    Args:
        wait_time: Time to wait before allowing the function to be called again
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def debounced(*args, **kwargs) -> Any:
            def call_func():
                _last_call_time[func] = time.time()
                return func(*args, **kwargs)
                
            # Cancel any existing timer
            if func in _timers:
                _timers[func].cancel()
                
            # Create a new timer
            timer = threading.Timer(wait_time, call_func)
            timer.daemon = True
            _timers[func] = timer
            timer.start()
            
        return debounced
    return decorator


def throttle(wait_time: float = 0.3):
    """
    Decorator to throttle a function call.
    
    Args:
        wait_time: Minimum time between function calls
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def throttled(*args, **kwargs) -> Optional[Any]:
            current_time = time.time()
            
            # Check if enough time has passed since the last call
            if func in _last_call_time:
                elapsed = current_time - _last_call_time[func]
                if elapsed < wait_time:
                    return None
                    
            # Call the function and update the last call time
            _last_call_time[func] = current_time
            return func(*args, **kwargs)
            
        return throttled
    return decorator 