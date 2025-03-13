"""
Game Launcher Service Module

This module provides functionality for launching and managing game processes.
It handles game process creation, monitoring, and termination.
"""

import os
import subprocess
import threading
import time
import logging
import uuid
import psutil
from typing import Dict, Optional, List, Tuple, Any

from app.utils.logging_config import get_logger
from app.utils.sandbox_manager import SandboxManager
from app.utils.dependency_installer import ensure_dependencies

logger = get_logger(__name__)

class GameLauncherService:
    """
    Service for launching and managing game processes.
    """
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the game launcher service.
        
        Args:
            config: Application configuration
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # Check for required dependencies
        success, failed_deps = ensure_dependencies(["psutil", "pywin32"])
        
        if not success:
            self.logger.error(f"Failed to install required dependencies: {failed_deps}")
            self.initialized = False
            return
        
        # Initialize service state
        self.initialized = True
        self.games = {}  # game_id -> game_path
        self.running_games = {}  # game_id -> process
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()
        
        # Load registered games from config
        if self.config and "games" in self.config:
            for game_id, game_path in self.config["games"].items():
                self.register_game(game_id, game_path)
            
        self.sandbox_manager = SandboxManager(config)
        
        self.logger.info("Game launcher service initialized")
        
    def register_game(self, game_id: str, game_path: str) -> bool:
        """
        Register a game with the launcher service.
        
        Args:
            game_id: Unique identifier for the game
            game_path: Path to the game executable
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        if not os.path.exists(game_path):
            logger.error(f"Game path does not exist: {game_path}")
            return False
            
        self.games[game_id] = game_path
        logger.info(f"Game registered: {game_id} at {game_path}")
        return True
        
    def launch_game(self, game_id: str, args: List[str] = None) -> bool:
        """
        Launch a registered game.
        
        Args:
            game_id: ID of the game to launch
            args: Additional command line arguments for the game
            
        Returns:
            bool: True if the game was launched successfully, False otherwise
        """
        if game_id not in self.games:
            logger.error(f"Game not registered: {game_id}")
            return False
            
        if game_id in self.running_games:
            logger.warning(f"Game already running: {game_id}")
            return False
            
        game_path = self.games[game_id]
        cmd = [game_path]
        
        if args:
            cmd.extend(args)
            
        try:
            # Start the game process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.running_games[game_id] = process
            logger.info(f"Game launched: {game_id}")
            
            # Start monitoring thread if not already running
            if not self.monitor_thread or not self.monitor_thread.is_alive():
                self.start_monitoring()
                
            return True
        except Exception as e:
            logger.error(f"Failed to launch game {game_id}: {str(e)}")
            return False
            
    def terminate_game(self, instance_id: str) -> bool:
        """
        Terminate a running game.
        
        Args:
            instance_id: ID of the game instance to terminate
            
        Returns:
            bool: True if termination was successful, False otherwise
        """
        if instance_id not in self.running_games:
            self.logger.warning(f"Game instance {instance_id} not found")
            return False
            
        game_info = self.running_games[instance_id]
        
        # Handle different types of game info
        if isinstance(game_info, bool):
            self.logger.warning(f"Game info for {instance_id} is a boolean, cannot terminate")
            return False
        
        try:
            # Terminate process
            terminated = False
            
            # Handle different ways of storing process info
            if "process" in game_info:
                process = game_info["process"]
                
                # Handle psutil.Process objects
                if isinstance(process, psutil.Process):
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                        terminated = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        try:
                            process.kill()
                            terminated = True
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                # Handle subprocess.Popen objects
                elif hasattr(process, "terminate"):
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                        terminated = True
                    except:
                        try:
                            process.kill()
                            terminated = True
                        except:
                            pass
            
            # If process termination failed or no process info, try by PID
            if not terminated and "pid" in game_info:
                try:
                    # Use the global psutil import instead of importing it locally
                    process = psutil.Process(game_info["pid"])
                    process.terminate()
                    process.wait(timeout=5)
                    terminated = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    try:
                        process.kill()
                        terminated = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            # For sandbox games, terminate the sandbox
            if game_info.get("in_sandbox", False) and "sandbox" in game_info:
                sandbox_name = game_info["sandbox"]
                sandbox_type = game_info.get("sandbox_type", "unknown")
                
                # Terminate sandbox
                if hasattr(self.sandbox_manager, "terminate_sandbox"):
                    self.sandbox_manager.terminate_sandbox(sandbox_name)
                    terminated = True
            
            # Mark as terminated
            game_info["terminated"] = True
            game_info["end_time"] = time.time()
            
            # Remove from running games
            del self.running_games[instance_id]
            
            self.logger.info(f"Game {instance_id} terminated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error terminating game {instance_id}: {e}", exc_info=True)
            return False
            
    def is_game_running(self, game_id: str) -> bool:
        """
        Check if any instance of a game is currently running.
        
        Args:
            game_id: ID of the game to check
            
        Returns:
            bool: True if any instance of the game is running, False otherwise
        """
        # Update running games first
        self._update_running_games()
        
        # Check if any instance of this game is running
        for instance_id, game_info in self.running_games.items():
            if isinstance(game_info, dict) and game_info.get("game_id") == game_id:
                return True
            elif instance_id == game_id:  # For backward compatibility
                return True
            
        return False
        
    def get_running_games(self) -> List[str]:
        """
        Get a list of currently running game instances.
        
        Returns:
            List[str]: List of instance IDs that are currently running
        """
        # Update the status of running games
        self._update_running_games()
        return list(self.running_games.keys())
        
    def _update_running_games(self) -> None:
        """Update the list of running games."""
        try:
            import psutil
            
            # Create a copy of the keys to avoid modification during iteration
            instance_ids = list(self.running_games.keys())
            
            for instance_id in instance_ids:
                game_info = self.running_games[instance_id]
                
                # Skip if already marked as terminated
                if game_info.get("terminated", False):
                    continue
                
                # Handle different types of game info
                if isinstance(game_info, bool):
                    # Convert boolean game info to dictionary for consistency
                    self.logger.warning(f"Game info for {instance_id} is a boolean, converting to dictionary")
                    self.running_games[instance_id] = {
                        "game_id": instance_id.split('_')[0],
                        "start_time": time.time(),
                        "in_sandbox": False
                    }
                    game_info = self.running_games[instance_id]
                
                # Check if process is still running
                is_running = False
                
                # Handle different ways of storing process info
                if "process" in game_info:
                    process = game_info["process"]
                    
                    # Handle psutil.Process objects
                    if isinstance(process, psutil.Process):
                        try:
                            is_running = process.is_running() and process.status() != psutil.STATUS_ZOMBIE
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            is_running = False
                    # Handle subprocess.Popen objects
                    elif hasattr(process, "poll"):
                        is_running = process.poll() is None
                    # Handle other process objects
                    else:
                        is_running = False
                        
                elif "pid" in game_info:
                    # Try to get process by PID
                    try:
                        process = psutil.Process(game_info["pid"])
                        is_running = process.is_running() and process.status() != psutil.STATUS_ZOMBIE
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        is_running = False
                
                # For sandbox games, check sandbox health
                if not is_running and game_info.get("in_sandbox", False) and "sandbox" in game_info:
                    sandbox_name = game_info["sandbox"]
                    sandbox_type = game_info.get("sandbox_type", "unknown")
                    
                    # For built-in sandbox, try to find the game process by name
                    if sandbox_type == "built_in":
                        game_id = game_info.get("game_id")
                        if game_id in self.games:
                            executable_path = self.games[game_id]
                            executable_name = os.path.basename(executable_path).lower()
                            
                            # Look for processes with the same name
                            for proc in psutil.process_iter(['pid', 'name']):
                                try:
                                    if proc.info['name'].lower() == executable_name:
                                        # Update process info
                                        game_info["process"] = proc
                                        game_info["pid"] = proc.pid
                                        is_running = True
                                        break
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    continue
                    
                    # For other sandbox types, check sandbox health
                    elif hasattr(self.sandbox_manager, "check_sandbox_health"):
                        health = self.sandbox_manager.check_sandbox_health(sandbox_name)
                        is_running = health.get("status") == "running"
                
                # Remove from running games if not running
                if not is_running:
                    # Mark as terminated
                    game_info["terminated"] = True
                    game_info["end_time"] = time.time()
                    
                    # Log termination
                    self.logger.info(f"Game {instance_id} is no longer running, removing from active games")
                    
                    # Remove from running games after a short delay to allow for cleanup
                    def remove_after_delay(instance_id):
                        time.sleep(2)  # Short delay
                        if instance_id in self.running_games:
                            del self.running_games[instance_id]
                    
                    # Start a thread to remove the game after a delay
                    threading.Thread(target=remove_after_delay, args=(instance_id,), daemon=True).start()
        
        except Exception as e:
            self.logger.error(f"Error updating running games: {e}", exc_info=True)
            
    def start_monitoring(self) -> None:
        """Start the game monitoring thread."""
        self.stop_monitoring.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_games)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Game monitoring started")
        
    def stop_monitoring(self) -> None:
        """Stop the game monitoring thread."""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.stop_monitoring.set()
            self.monitor_thread.join(timeout=2.0)
            logger.info("Game monitoring stopped")
            
    def _monitor_games(self) -> None:
        """Monitor running games and update their status."""
        while not self.stop_monitoring.is_set():
            self._update_running_games()
            time.sleep(1.0)
            
    def launch_game_in_sandbox(self, game_id: str, sandbox_type: str, args: List[str] = None) -> bool:
        """
        Launch a game in a sandbox environment.
        
        Args:
            game_id: ID of the game to launch
            sandbox_type: Type of sandbox to use
            args: Additional command line arguments
            
        Returns:
            bool: True if launch was successful, False otherwise
        """
        if game_id not in self.games:
            logger.error(f"Game not registered: {game_id}")
            return False
            
        # Generate a unique instance ID for this launch
        instance_id = f"{game_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        game_path = self.games[game_id]
        
        # Generate a sandbox name
        sandbox_name = f"{game_id}_{int(time.time())}"
        
        # Add game-specific arguments if needed
        game_args = args or []
        
        # For old games that might need special handling
        if game_id.lower() == "wyd":
            # Add any WYD-specific arguments here if needed
            self.logger.info("Applying WYD-specific launch settings")
        
        # Launch in sandbox
        result = self.sandbox_manager.launch_in_sandbox(
            sandbox_type,
            game_path,
            game_args,
            sandbox_name
        )
        
        # Handle different types of results
        if result:
            # Check if result is a dictionary (from built-in sandbox)
            if isinstance(result, dict):
                # Check if it's an error result
                if result.get("success") is False:
                    self.logger.error(f"Failed to launch game in sandbox: {result.get('error', 'Unknown error')}")
                    return False
                    
                # Store sandbox info with the game
                self.running_games[instance_id] = {
                    "game_id": game_id,  # Store the original game ID
                    "sandbox": sandbox_name,
                    "sandbox_type": sandbox_type,
                    "start_time": time.time(),
                    "in_sandbox": True
                }
                
                # Add process info if available
                if "process" in result:
                    self.running_games[instance_id]["process"] = result["process"]
                if "pid" in result:
                    self.running_games[instance_id]["pid"] = result["pid"]
            else:
                # For other sandbox types that return boolean, create a proper dictionary
                self.running_games[instance_id] = {
                    "game_id": game_id,  # Store the original game ID
                    "sandbox": sandbox_name,
                    "sandbox_type": sandbox_type,
                    "start_time": time.time(),
                    "in_sandbox": True,
                    "process_info_pending": True  # Flag to indicate we need to find the process later
                }
            
            logger.info(f"Game {game_id} (instance {instance_id}) launched in sandbox {sandbox_name}")
            
            # Start monitoring thread if not already running
            if not self.monitor_thread or not self.monitor_thread.is_alive():
                self.start_monitoring()
            
            return True
        
        return False

    def check_sandbox_network(self, instance_id: str) -> Dict[str, Any]:
        """
        Check if a game's sandbox has proper network isolation.
        
        Args:
            instance_id: ID of the game instance to check
            
        Returns:
            Dict: Network status information
        """
        if instance_id not in self.running_games:
            logger.warning(f"Game instance not running: {instance_id}")
            return {"status": "not_running"}
        
        game_info = self.running_games[instance_id]
        
        # Skip if game_info is None or not a dictionary
        if game_info is None or not isinstance(game_info, dict):
            logger.warning(f"Invalid game info for {instance_id}")
            return {"status": "invalid_info"}
        
        # Skip if game is marked as terminated
        if game_info.get("terminated", False):
            logger.warning(f"Game instance {instance_id} is terminated")
            return {"status": "not_running"}
        
        # Check if running in sandbox
        if not game_info.get("in_sandbox", False):
            logger.warning(f"Game instance {instance_id} not running in a sandbox")
            return {"status": "no_sandbox"}
        
        # Get sandbox name
        sandbox_name = game_info.get("sandbox")
        if not sandbox_name:
            logger.warning(f"No sandbox name for game instance {instance_id}")
            return {"status": "no_sandbox_name"}
        
        # Get sandbox type
        sandbox_type = game_info.get("sandbox_type", "unknown")
        
        # Check sandbox health
        try:
            if sandbox_type == "built_in" and hasattr(self.sandbox_manager, "built_in_sandbox"):
                health = self.sandbox_manager.built_in_sandbox.check_sandbox_health(sandbox_name)
            elif sandbox_type == "windows_sandbox" and hasattr(self.sandbox_manager, "windows_sandbox"):
                health = self.sandbox_manager.windows_sandbox.check_sandbox_health(sandbox_name)
            else:
                health = self.sandbox_manager.check_sandbox_health(sandbox_name)
            
            if health.get("status") != "running":
                return {"status": "sandbox_not_running", "details": health}
            
            # Check network isolation
            network_isolated = health.get("network_isolated", False)
            
            # For built-in sandbox, always report as isolated if enabled
            if sandbox_type == "built_in" and game_info.get("network_isolation", False):
                network_isolated = True
            
            return {
                "status": "ok" if network_isolated else "network_not_isolated",
                "network_isolated": network_isolated,
                "sandbox_status": health,
                "accessible": [] if network_isolated else ["Internet"],
                "sandbox_type": sandbox_type
            }
        except Exception as e:
            logger.error(f"Error checking sandbox health: {e}")
            return {"status": "error", "error": str(e)}

    def terminate_sandbox(self, game_id: str) -> bool:
        """
        Terminate a game's sandbox.
        
        Args:
            game_id: ID of the game to terminate
            
        Returns:
            bool: True if the sandbox was terminated successfully, False otherwise
        """
        if game_id not in self.running_games:
            logger.warning(f"Game not running: {game_id}")
            return False
        
        game_info = self.running_games[game_id]
        
        if "sandbox" not in game_info:
            logger.warning(f"Game {game_id} not running in a sandbox")
            return False
        
        sandbox_name = game_info["sandbox"]
        
        # Terminate sandbox
        success = self.sandbox_manager.terminate_sandbox(sandbox_name)
        
        if success:
            # Remove sandbox info
            del self.running_games[game_id]["sandbox"]
            
            # If no other processes for this game, remove it from running games
            if not self.running_games[game_id]:
                del self.running_games[game_id]
            
            logger.info(f"Sandbox {sandbox_name} for game {game_id} terminated")
        
        return success

    def get_available_sandbox_types(self) -> List[str]:
        """
        Get a list of available sandbox types.
        
        Returns:
            List[str]: List of available sandbox types
        """
        return self.sandbox_manager.get_available_sandboxes()

    def shutdown(self) -> None:
        """Shutdown the game launcher service and terminate all running games."""
        logger.info("Shutting down game launcher service")
        
        # Stop the monitoring thread
        self.stop_monitoring.set()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
            
        # Terminate all sandboxes
        self.sandbox_manager.terminate_all_sandboxes()
        
        # Terminate all running games
        game_ids = list(self.running_games.keys())
        for game_id in game_ids:
            self.terminate_game(game_id)
            
        logger.info("Game launcher service shutdown complete")

    def take_screenshot(self, instance_id: str) -> Optional[str]:
        """
        Take a screenshot of a running game.
        
        Args:
            instance_id: ID of the game instance
            
        Returns:
            Optional[str]: Path to the screenshot file, or None if failed
        """
        try:
            if instance_id not in self.running_games:
                self.logger.warning(f"Game instance {instance_id} not running")
                return None
            
            game_info = self.running_games[instance_id]
            
            # Get the original game ID for logging
            game_id = game_info.get("game_id", instance_id) if isinstance(game_info, dict) else instance_id
            
            # Get process ID
            pid = None
            if isinstance(game_info, dict) and "pid" in game_info:
                pid = game_info["pid"]
            elif isinstance(game_info, dict) and "process" in game_info:
                process = game_info["process"]
                if hasattr(process, "pid"):
                    pid = process.pid
            elif hasattr(game_info, "pid"):
                pid = game_info.pid
            
            if not pid:
                self.logger.error(f"No PID found for game {game_id}")
                return None
            
            # Import required modules
            try:
                import win32gui
                import win32process
                import win32ui
                import win32con
                from PIL import Image
            except ImportError:
                self.logger.error("Required modules not found, installing dependencies...")
                from app.utils.dependency_installer import install_dependency
                
                # Install required dependencies
                install_dependency("pywin32")
                install_dependency("pillow")
                
                # Try importing again
                try:
                    import win32gui
                    import win32process
                    import win32ui
                    import win32con
                    from PIL import Image
                except ImportError:
                    self.logger.error("Failed to install required dependencies")
                    return None
                
            # Find windows belonging to this process
            hwnds = []
            
            def callback(hwnd, hwnds):
                if win32gui.IsWindowVisible(hwnd):
                    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if found_pid == pid:
                        hwnds.append(hwnd)
                return True
            
            win32gui.EnumWindows(callback, hwnds)
            
            if not hwnds:
                self.logger.warning(f"No visible windows found for game {game_id}")
                return None
            
            # Take screenshot of the first window
            hwnd = hwnds[0]
            
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Create device context
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # Create bitmap
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # Copy window contents to bitmap
            result = win32gui.PrintWindow(hwnd, save_dc.GetSafeHdc(), 0)
            
            # Convert to PIL Image
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # Clean up
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            if not result:
                self.logger.warning(f"PrintWindow failed for game {game_id}")
                return None
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Save screenshot
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{game_id}_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            img.save(filepath)
            
            self.logger.info(f"Screenshot saved for game {game_id}: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}", exc_info=True)
            return None

    def focus_game_window(self, instance_id: str) -> bool:
        """
        Focus on a running game window.
        
        Args:
            instance_id: ID of the game instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if instance_id not in self.running_games:
                self.logger.warning(f"Game instance {instance_id} not running")
                return False
            
            game_info = self.running_games[instance_id]
            
            # Get the original game ID for logging
            game_id = game_info.get("game_id", instance_id) if isinstance(game_info, dict) else instance_id
            
            # Get process ID
            pid = None
            if isinstance(game_info, dict) and "pid" in game_info:
                pid = game_info["pid"]
            elif isinstance(game_info, dict) and "process" in game_info:
                process = game_info["process"]
                if hasattr(process, "pid"):
                    pid = process.pid
            elif hasattr(game_info, "pid"):
                pid = game_info.pid
            
            if not pid:
                self.logger.error(f"No PID found for game {game_id}")
                return False
            
            # Import required modules
            try:
                import win32gui
                import win32process
                import win32con
            except ImportError:
                self.logger.error("Required modules not found, installing dependencies...")
                from app.utils.dependency_installer import install_dependency
                
                # Install required dependencies
                install_dependency("pywin32")
                
                # Try importing again
                try:
                    import win32gui
                    import win32process
                    import win32con
                except ImportError:
                    self.logger.error("Failed to install required dependencies")
                    return False
                
            # Find windows belonging to this process
            hwnds = []
            
            def callback(hwnd, hwnds):
                if win32gui.IsWindowVisible(hwnd):
                    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if found_pid == pid:
                        hwnds.append(hwnd)
                return True
            
            win32gui.EnumWindows(callback, hwnds)
            
            if not hwnds:
                self.logger.warning(f"No visible windows found for game {game_id}")
                return False
            
            # Focus the first window
            hwnd = hwnds[0]
            
            # If the window is minimized, restore it
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # Bring the window to the foreground
            win32gui.SetForegroundWindow(hwnd)
            
            self.logger.info(f"Focused window for game {game_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error focusing game window: {e}", exc_info=True)
            return False

    def get_game_info(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a running game instance.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            Optional[Dict[str, Any]]: Game information, or None if not running
        """
        try:
            if instance_id not in self.running_games:
                return None
            
            game_info = self.running_games[instance_id]
            
            # If the game is already marked as terminated, return None
            if isinstance(game_info, dict) and game_info.get("terminated", False):
                return None
            
            # Get the original game ID
            game_id = game_info.get("game_id", instance_id)
            if "game_id" not in game_info:
                # For backward compatibility with older entries
                game_info["game_id"] = game_id
            
            # Handle different types of game_info
            if isinstance(game_info, dict):
                # For sandbox or complex launches
                process = game_info.get("process")
                in_sandbox = game_info.get("in_sandbox", False)
                sandbox_type = game_info.get("sandbox_type")
                
                # If no process but in sandbox, it might still be running
                if not process and in_sandbox and "sandbox" in game_info:
                    # Return basic info for sandbox
                    return {
                        "instance_id": instance_id,
                        "game_id": game_id,
                        "path": self.games.get(game_id, "Unknown"),
                        "start_time": game_info.get("start_time", time.time() - 60),
                        "in_sandbox": True,
                        "sandbox_type": sandbox_type,
                        "sandbox_name": game_info.get("sandbox")
                    }
            else:
                # For simple process launches
                process = game_info
            
            if not process:
                return None
            
            # Check if process is still running
            if hasattr(process, "poll") and process.poll() is not None:
                # Process has terminated
                if isinstance(game_info, dict):
                    game_info["terminated"] = True
                else:
                    # Mark for removal
                    self.running_games[instance_id] = {"terminated": True, "game_id": game_id}
                
                # Schedule removal after a delay
                def remove_after_delay(instance_id):
                    time.sleep(2)  # Short delay
                    if instance_id in self.running_games:
                        del self.running_games[instance_id]
                
                threading.Thread(target=remove_after_delay, args=(instance_id,), daemon=True).start()
                return None
            
            # Get process information
            try:
                # Get the PID
                if isinstance(game_info, dict):
                    pid = game_info.get("pid")
                    if not pid and hasattr(process, "pid"):
                        pid = process.pid
                else:
                    pid = process.pid if hasattr(process, "pid") else None
                
                if not pid:
                    # Return basic info without PID
                    return {
                        "instance_id": instance_id,
                        "game_id": game_id,
                        "path": self.games.get(game_id, "Unknown"),
                        "start_time": time.time() - 60,
                        "in_sandbox": isinstance(game_info, dict) and game_info.get("in_sandbox", False),
                        "sandbox_type": game_info.get("sandbox_type") if isinstance(game_info, dict) else None
                    }
                
                # Check if the process exists before trying to get detailed info
                if not psutil.pid_exists(pid):
                    # Process no longer exists, mark for removal
                    if isinstance(game_info, dict):
                        game_info["terminated"] = True
                    else:
                        # Mark for removal
                        self.running_games[instance_id] = {"terminated": True, "game_id": game_id}
                    
                    # Schedule removal after a delay
                    def remove_after_delay(instance_id):
                        time.sleep(2)  # Short delay
                        if instance_id in self.running_games:
                            del self.running_games[instance_id]
                    
                    threading.Thread(target=remove_after_delay, args=(instance_id,), daemon=True).start()
                    return None
                
                # Get detailed process info
                try:
                    p = psutil.Process(pid)
                    
                    # Check if process is still running
                    if not p.is_running():
                        # Process is not running, mark for removal
                        if isinstance(game_info, dict):
                            game_info["terminated"] = True
                        else:
                            # Mark for removal
                            self.running_games[instance_id] = {"terminated": True, "game_id": game_id}
                        
                        # Schedule removal after a delay
                        def remove_after_delay(instance_id):
                            time.sleep(2)  # Short delay
                            if instance_id in self.running_games:
                                del self.running_games[instance_id]
                        
                        threading.Thread(target=remove_after_delay, args=(instance_id,), daemon=True).start()
                        return None
                    
                    # Get memory and CPU usage
                    try:
                        memory_info = p.memory_info()
                        cpu_percent = p.cpu_percent(interval=0.1)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process might have terminated while we were checking
                        memory_info = None
                        cpu_percent = 0
                    
                    # Get window title
                    window_title = "Unknown"
                    try:
                        import win32gui
                        import win32process
                        
                        def callback(hwnd, result):
                            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                                if found_pid == pid:
                                    result.append(win32gui.GetWindowText(hwnd))
                            return True
                        
                        window_titles = []
                        win32gui.EnumWindows(callback, window_titles)
                        
                        if window_titles:
                            window_title = window_titles[0]
                    except Exception:
                        # Ignore errors getting window title
                        pass
                    
                    # Return detailed info
                    return {
                        "instance_id": instance_id,
                        "game_id": game_id,
                        "pid": pid,
                        "path": self.games.get(game_id, "Unknown"),
                        "memory_mb": memory_info.rss / 1024 / 1024 if memory_info else 0,
                        "cpu_percent": cpu_percent,
                        "window_title": window_title,
                        "start_time": game_info.get("start_time", time.time() - 60) if isinstance(game_info, dict) else time.time() - 60,
                        "in_sandbox": isinstance(game_info, dict) and game_info.get("in_sandbox", False),
                        "sandbox_type": game_info.get("sandbox_type") if isinstance(game_info, dict) else None
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process no longer exists or can't be accessed, mark for removal
                    if isinstance(game_info, dict):
                        game_info["terminated"] = True
                    else:
                        # Mark for removal
                        self.running_games[instance_id] = {"terminated": True, "game_id": game_id}
                    
                    # Schedule removal after a delay
                    def remove_after_delay(instance_id):
                        time.sleep(2)  # Short delay
                        if instance_id in self.running_games:
                            del self.running_games[instance_id]
                    
                    threading.Thread(target=remove_after_delay, args=(instance_id,), daemon=True).start()
                    return None
            except Exception as e:
                # Log error but don't spam the log with the same error repeatedly
                if not hasattr(self, "_last_error_pids"):
                    self._last_error_pids = {}
                
                # Only log if we haven't seen this PID error recently
                if pid not in self._last_error_pids or time.time() - self._last_error_pids.get(pid, 0) > 30:
                    self.logger.error(f"Error getting detailed process info: {e}")
                    self._last_error_pids[pid] = time.time()
                
                # Return basic info without detailed process info
                return {
                    "instance_id": instance_id,
                    "game_id": game_id,
                    "pid": pid,
                    "path": self.games.get(game_id, "Unknown"),
                    "start_time": game_info.get("start_time", time.time() - 60) if isinstance(game_info, dict) else time.time() - 60,
                    "in_sandbox": isinstance(game_info, dict) and game_info.get("in_sandbox", False),
                    "sandbox_type": game_info.get("sandbox_type") if isinstance(game_info, dict) else None
                }
        except Exception as e:
            # Log error but don't spam the log
            if not hasattr(self, "_last_general_error_time"):
                self._last_general_error_time = 0
            
            if time.time() - self._last_general_error_time > 30:
                self.logger.error(f"Error getting game info for {instance_id}: {e}")
                self._last_general_error_time = time.time()
            
            return None

    def get_all_game_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all running games.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping game IDs to game information
        """
        result = {}
        
        # Update running games first
        self._update_running_games()
        
        # Get info for each running game
        for game_id in list(self.running_games.keys()):
            game_info = self.get_game_info(game_id)
            if game_info:
                result[game_id] = game_info
                
        return result

    def get_registered_games(self) -> Dict[str, str]:
        """
        Get all registered games.
        
        Returns:
            Dict[str, str]: Dictionary mapping game IDs to game paths
        """
        return self.games.copy()

    def unregister_game(self, game_id: str) -> bool:
        """
        Unregister a game.
        
        Args:
            game_id: Game identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if game_id not in self.games:
                logger.warning(f"Game '{game_id}' is not registered")
                return False
            
            # Check if game is running
            if game_id in self.running_games:
                logger.warning(f"Game '{game_id}' is still running, terminating first")
                self.terminate_game(game_id)
            
            # Remove from registered games
            del self.games[game_id]
            
            logger.info(f"Game '{game_id}' unregistered")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering game: {e}", exc_info=True)
            return False

    def is_game_registered(self, game_id: str) -> bool:
        """
        Check if a game is registered with the launcher service.
        
        Args:
            game_id: Unique identifier for the game
            
        Returns:
            bool: True if the game is registered, False otherwise
        """
        return game_id in self.games

    def launch_game_with_bot(self, game_id: str, args: List[str] = None) -> bool:
        """
        Launch a game with bot monitoring.
        
        Args:
            game_id: ID of the game to launch
            args: Additional command line arguments
            
        Returns:
            bool: True if launch was successful, False otherwise
        """
        try:
            # First launch the game normally
            success = self.launch_game(game_id, args)
            if not success:
                return False
            
            # Mark this game as running with a bot
            if game_id in self.running_games:
                game_info = self.running_games[game_id]
                if isinstance(game_info, dict):
                    game_info["with_bot"] = True
                else:
                    # Convert to dict if it's just a process
                    process = self.running_games[game_id]
                    self.running_games[game_id] = {
                        "process": process,
                        "pid": process.pid,
                        "start_time": time.time(),
                        "with_bot": True
                    }
            
            # Update the window title to indicate bot is running
            # Try multiple times with increasing delays to ensure we catch the window after it's fully loaded
            for delay in [2, 4, 6, 8, 10, 15]:
                threading.Timer(
                    delay, 
                    self._update_window_title,
                    args=(game_id,)
                ).start()
            
            return True
        except Exception as e:
            self.logger.error(f"Error launching game with bot: {e}")
            return False
        
    def _update_window_title(self, game_id: str):
        """
        Update the window title to indicate bot is running.
        
        Args:
            game_id: ID of the game
        """
        try:
            # Check if game is still running
            if game_id not in self.running_games:
                self.logger.error(f"Game {game_id} not found in running games")
                return
            
            # Import required modules
            try:
                import win32gui
                import win32process
                import win32con
            except ImportError:
                self.logger.error("Required modules not found, installing dependencies...")
                from app.utils.dependency_installer import install_dependency
                
                # Install required dependencies
                install_dependency("pywin32")
                
                # Try importing again
                try:
                    import win32gui
                    import win32process
                    import win32con
                except ImportError:
                    self.logger.error("Failed to install required dependencies for window title update")
                    return
            
            # Get the game info
            game_info = self.running_games[game_id]
            
            # Get the process
            if isinstance(game_info, dict):
                process = game_info.get("process")
            else:
                process = game_info
            
            if not process:
                self.logger.error(f"No process found for game {game_id}")
                return
            
            # Get the PID
            pid = process.pid if hasattr(process, "pid") else None
            
            if not pid:
                self.logger.error(f"No PID found for game {game_id}")
                return
            
            self.logger.info(f"Attempting to update window title for game {game_id} with PID {pid}")
            
            # First approach: Find windows by PID
            def find_windows_by_pid(hwnd, result):
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                
                try:
                    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if found_pid == pid:
                        title = win32gui.GetWindowText(hwnd)
                        if title and not title.startswith(f"Bot #{game_id}"):
                            new_title = f"Bot #{game_id} - {title}"
                            self.logger.info(f"Found window by PID: '{title}' -> '{new_title}'")
                            win32gui.SetWindowText(hwnd, new_title)
                            result.append(hwnd)
                except Exception as e:
                    self.logger.error(f"Error in find_windows_by_pid: {e}")
                return True
            
            pid_result = []
            win32gui.EnumWindows(find_windows_by_pid, pid_result)
            
            if pid_result:
                self.logger.info(f"Updated {len(pid_result)} window titles by PID for game {game_id}")
                return
            
            # Second approach: Find windows by executable name
            game_path = self.games.get(game_id, "")
            exe_name = os.path.basename(game_path).split('.')[0] if game_path else ""
            
            if not exe_name:
                self.logger.error(f"No executable name found for game {game_id}")
                return
            
            def find_windows_by_name(hwnd, result):
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                
                try:
                    title = win32gui.GetWindowText(hwnd)
                    if title and exe_name.lower() in title.lower() and not title.startswith(f"Bot #{game_id}"):
                        new_title = f"Bot #{game_id} - {title}"
                        self.logger.info(f"Found window by name: '{title}' -> '{new_title}'")
                        win32gui.SetWindowText(hwnd, new_title)
                        result.append(hwnd)
                except Exception as e:
                    self.logger.error(f"Error in find_windows_by_name: {e}")
                return True
            
            name_result = []
            win32gui.EnumWindows(find_windows_by_name, name_result)
            
            if name_result:
                self.logger.info(f"Updated {len(name_result)} window titles by name for game {game_id}")
                return
            
            # Third approach: Find any window that might be related
            def find_any_game_window(hwnd, result):
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                
                try:
                    title = win32gui.GetWindowText(hwnd)
                    # Look for common game window indicators
                    if title and ("WYD" in title or "Game" in title) and not title.startswith(f"Bot #{game_id}"):
                        new_title = f"Bot #{game_id} - {title}"
                        self.logger.info(f"Found potential game window: '{title}' -> '{new_title}'")
                        win32gui.SetWindowText(hwnd, new_title)
                        result.append(hwnd)
                except Exception as e:
                    self.logger.error(f"Error in find_any_game_window: {e}")
                return True
            
            any_result = []
            win32gui.EnumWindows(find_any_game_window, any_result)
            
            if any_result:
                self.logger.info(f"Updated {len(any_result)} potential game windows for game {game_id}")
            else:
                self.logger.warning(f"Could not find any window to update for game {game_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating window title: {e}", exc_info=True)

    def is_game_in_sandbox(self, instance_id: str) -> bool:
        """
        Check if a game instance is running in a sandbox.
        
        Args:
            instance_id: ID of the game instance to check
            
        Returns:
            bool: True if the game instance is running in a sandbox, False otherwise
        """
        if instance_id not in self.running_games:
            return False
        
        game_info = self.running_games[instance_id]
        
        # If game_info is a dictionary, check for sandbox indicators
        if isinstance(game_info, dict):
            return game_info.get("in_sandbox", False)
        
        # If it's not a dictionary, it's a direct process object, which is not in a sandbox
        return False

    def launch_game_with_network_wrapper(self, game_id: str, network_profile_type: str = "random", args: List[str] = None) -> bool:
        """
        Launch a game with a network wrapper that makes it appear as if running on another machine.
        
        Args:
            game_id: ID of the game to launch
            network_profile_type: Type of network profile to use
            args: Additional command line arguments
            
        Returns:
            bool: True if launch was successful, False otherwise
        """
        if game_id not in self.games:
            logger.error(f"Game not registered: {game_id}")
            return False
        
        # Get network mask service
        app = get_app_instance()
        network_service = app.get_service("network_mask")
        if not network_service:
            logger.error("Network mask service not available")
            return False
        
        # Generate a unique instance ID for this launch
        instance_id = f"{game_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        game_path = self.games[game_id]
        
        # Create network profile
        network_profile = network_service.create_game_network_profile(game_id, network_profile_type)
        
        # Apply network profile
        if not network_service.apply_network_profile(network_profile["profile_id"]):
            logger.error(f"Failed to apply network profile for game {game_id}")
            return False
        
        # Launch the game in a sandbox with network isolation
        result = self.sandbox_manager.launch_in_sandbox(
            "built_in",  # Use built-in sandbox for best network control
            game_path,
            args or [],
            f"network_wrapper_{instance_id}"
        )
        
        # Handle launch result
        if isinstance(result, dict) and result.get("success") is not False:
            # Store game info
            self.running_games[instance_id] = {
                "game_id": game_id,
                "sandbox": f"network_wrapper_{instance_id}",
                "sandbox_type": "built_in",
                "start_time": time.time(),
                "in_sandbox": True,
                "network_profile": network_profile,
                "network_wrapped": True
            }
            
            # Add process info if available
            if "process" in result:
                self.running_games[instance_id]["process"] = result["process"]
            if "pid" in result:
                self.running_games[instance_id]["pid"] = result["pid"]
            
            logger.info(f"Game {game_id} (instance {instance_id}) launched with network wrapper")
            
            # Start monitoring thread if not already running
            if not self.monitor_thread or not self.monitor_thread.is_alive():
                self.start_monitoring()
            
            return True
        else:
            # Launch failed, clean up network profile
            logger.error(f"Failed to launch game {game_id} with network wrapper")
            return False 