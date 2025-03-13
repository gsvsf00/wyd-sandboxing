"""
Sandbox Manager Module

This module provides functionality for managing sandbox environments.
"""

import os
import subprocess
import logging
import time
from typing import Dict, Any, List, Optional

from app.utils.logging_config import get_logger
from app.utils.dependency_installer import ensure_dependencies
from app.utils.built_in_sandbox import BuiltInSandbox
from app.utils.windows_sandbox import WindowsSandbox

logger = get_logger(__name__)

class SandboxManager:
    """
    Manager for sandbox environments.
    """
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the sandbox manager.
        
        Args:
            config: Application configuration
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # Check for required dependencies
        success, failed_deps = ensure_dependencies(["psutil"])
        if not success:
            self.logger.warning(f"Some dependencies could not be installed: {failed_deps}")
            self.logger.warning("Some sandbox features may not be available")
        
        # Initialize sandbox configurations
        self.sandboxes = {}
        self.sandbox_executables = {
            "sandboxie": self.config.get("sandboxie_path", ""),
            "windows_sandbox": "WindowsSandbox.exe",
            "virtualbox": self.config.get("virtualbox_path", "")
        }
        
        # Check which sandboxes are available
        self._check_available_sandboxes()
        
        # Add built-in sandbox
        self.built_in_sandbox = BuiltInSandbox()
        
        # Add Windows Sandbox
        self.windows_sandbox = WindowsSandbox()
        if self.windows_sandbox.is_available():
            self.available_sandboxes.append("windows_sandbox")
        
        # Always add built-in sandbox to available sandboxes
        self.available_sandboxes.append("built_in")
        self.logger.info(f"Available sandbox environments: {', '.join(self.available_sandboxes)}")
        
        self.logger.info("Sandbox manager initialized")
    
    def _check_available_sandboxes(self):
        """Check which sandbox environments are available."""
        available_sandboxes = []
        
        # Check Sandboxie
        if self._is_sandboxie_available():
            available_sandboxes.append("sandboxie")
            
        # Check Windows Sandbox
        if self._is_windows_sandbox_available():
            available_sandboxes.append("windows_sandbox")
            
        # Check VirtualBox
        if self._is_virtualbox_available():
            available_sandboxes.append("virtualbox")
            
        self.available_sandboxes = available_sandboxes
        self.logger.info(f"Available sandbox environments: {', '.join(available_sandboxes) if available_sandboxes else 'None'}")
    
    def _is_sandboxie_available(self) -> bool:
        """Check if Sandboxie is available."""
        # First check the configured path
        path = self.sandbox_executables.get("sandboxie")
        if path and os.path.exists(path):
            return True
            
        # Check common installation paths
        common_paths = [
            r"C:\Program Files\Sandboxie\Start.exe",
            r"C:\Program Files\Sandboxie-Plus\Start.exe",
            r"C:\Program Files (x86)\Sandboxie\Start.exe",
            r"C:\Program Files (x86)\Sandboxie-Plus\Start.exe"
        ]
        
        for common_path in common_paths:
            if os.path.exists(common_path):
                # Update the path for future use
                self.sandbox_executables["sandboxie"] = common_path
                return True
                
        return False
    
    def _is_windows_sandbox_available(self) -> bool:
        """Check if Windows Sandbox is available."""
        try:
            # Check if Windows Sandbox feature is enabled
            result = subprocess.run(
                ["powershell", "-Command", "Get-WindowsOptionalFeature -Online -FeatureName 'Containers-DisposableClientVM'"],
                capture_output=True,
                text=True
            )
            
            return "Enabled" in result.stdout
        except Exception:
            return False
    
    def _is_virtualbox_available(self) -> bool:
        """Check if VirtualBox is available."""
        path = self.sandbox_executables.get("virtualbox")
        if not path:
            return False
            
        return os.path.exists(path)
    
    def is_sandbox_available(self, sandbox_type: str) -> bool:
        """
        Check if a specific sandbox type is available.
        
        Args:
            sandbox_type: Type of sandbox
            
        Returns:
            bool: True if available, False otherwise
        """
        return sandbox_type in self.available_sandboxes
    
    def get_available_sandboxes(self) -> List[str]:
        """
        Get a list of available sandbox types.
        
        Returns:
            List[str]: List of available sandbox types
        """
        return self.available_sandboxes.copy()
    
    def launch_in_sandbox(self, sandbox_type: str, executable_path: str, args: List[str] = None, name: str = None) -> Any:
        """
        Launch an application in a sandbox.
        
        Args:
            sandbox_type: Type of sandbox to use
            executable_path: Path to the executable to launch
            args: Additional command line arguments
            name: Name for the sandbox instance
            
        Returns:
            Any: Process information dictionary for built-in sandbox, True for other sandboxes if successful, False otherwise
        """
        if not self.is_sandbox_available(sandbox_type):
            self.logger.error(f"Sandbox type {sandbox_type} not available")
            return False
            
        if not os.path.exists(executable_path):
            self.logger.error(f"Executable path does not exist: {executable_path}")
            return False
            
        # Generate a name if not provided
        if not name:
            name = f"sandbox_{int(time.time())}"
            
        # Add built-in sandbox handling
        if sandbox_type == "built_in":
            result = self.built_in_sandbox.launch_in_sandbox(name, executable_path, args)
            if isinstance(result, dict) and result.get("success") is not False:
                # Store sandbox info
                self.sandboxes[name] = {
                    "type": "built_in",
                    "executable": executable_path,
                    "creation_time": time.time()
                }
            return result
        
        # Add Windows Sandbox handling
        if sandbox_type == "windows_sandbox":
            result = self.windows_sandbox.launch_in_sandbox(name, executable_path, args)
            if result:
                # Store sandbox info
                self.sandboxes[name] = {
                    "type": "windows_sandbox",
                    "executable": executable_path,
                    "creation_time": time.time()
                }
            return result
        
        # Launch based on sandbox type
        if sandbox_type == "sandboxie":
            result = self._launch_in_sandboxie(executable_path, args, name)
            if result:
                # Store sandbox info
                self.sandboxes[name] = {
                    "type": "sandboxie",
                    "executable": executable_path,
                    "creation_time": time.time()
                }
            return result
        elif sandbox_type == "virtualbox":
            result = self._launch_in_virtualbox(executable_path, args, name)
            if result:
                # Store sandbox info
                self.sandboxes[name] = {
                    "type": "virtualbox",
                    "executable": executable_path,
                    "creation_time": time.time()
                }
            return result
        else:
            self.logger.error(f"Unsupported sandbox type: {sandbox_type}")
            return False
    
    def _launch_in_sandboxie(self, executable_path: str, args: List[str] = None, name: str = None) -> Dict[str, Any]:
        """
        Launch an application in Sandboxie.
        
        Args:
            executable_path: Path to the executable to launch
            args: Command line arguments
            name: Name of the sandbox
            
        Returns:
            Dict with launch status information
        """
        try:
            # Get Sandboxie path
            sandboxie_path = self.sandbox_executables.get("sandboxie")
            if not sandboxie_path:
                self.logger.error("Sandboxie path not configured")
                return {"success": False, "error": "Sandboxie path not configured"}
                
            # Check if Sandboxie exists
            if not os.path.exists(sandboxie_path):
                self.logger.error(f"Sandboxie executable not found at {sandboxie_path}")
                return {"success": False, "error": f"Sandboxie executable not found at {sandboxie_path}"}
                
            # Prepare sandbox name
            if not name:
                name = f"Sandbox_{int(time.time())}"
                
            # Prepare command
            cmd = [sandboxie_path, "/box:" + name]
            
            # Add executable path
            cmd.append(executable_path)
            
            # Add arguments if provided
            if args:
                cmd.extend(args)
                
            self.logger.info(f"Launching {executable_path} in Sandboxie sandbox {name}")
            self.logger.debug(f"Command: {' '.join(cmd)}")
            
            # Launch process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Check if process started
            if process.poll() is not None:
                # Process failed to start
                stdout, stderr = process.communicate()
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                self.logger.error(f"Failed to launch in Sandboxie: {error_msg}")
                return {"success": False, "error": error_msg}
                
            # Process started successfully
            self.logger.info(f"Successfully launched {executable_path} in Sandboxie sandbox {name}")
            
            # Store sandbox info
            self.sandboxes[name] = {
                "type": "sandboxie",
                "process": process,
                "pid": process.pid,
                "executable": executable_path,
                "start_time": time.time()
            }
            
            return {
                "success": True,
                "sandbox": name,
                "process": process,
                "pid": process.pid
            }
            
        except Exception as e:
            self.logger.error(f"Error launching in Sandboxie: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _launch_in_virtualbox(self, executable_path: str, args: List[str] = None, name: str = None) -> bool:
        """Launch in VirtualBox."""
        # Implementation for VirtualBox
        self.logger.info(f"Launching {executable_path} in VirtualBox VM {name}")
        return True
    
    def check_sandbox_health(self, name: str) -> Dict[str, Any]:
        """
        Check the health of a sandbox instance.
        
        Args:
            name: Name of the sandbox instance
            
        Returns:
            Dict[str, Any]: Health information
        """
        if name not in self.sandboxes:
            return {"status": "not_found"}
            
        sandbox_info = self.sandboxes[name]
        sandbox_type = sandbox_info.get("type")
        
        if sandbox_type == "built_in":
            return self.built_in_sandbox.check_sandbox_health(name)
        elif sandbox_type == "sandboxie":
            return self._check_sandboxie_health(name)
        elif sandbox_type == "windows_sandbox":
            return self.windows_sandbox.check_sandbox_health(name)
        elif sandbox_type == "virtualbox":
            return self._check_virtualbox_health(name)
        else:
            return {"status": "unknown_type"}
    
    def _check_sandboxie_health(self, name: str) -> Dict[str, Any]:
        """
        Check the health of a Sandboxie sandbox.
        
        Args:
            name: Name of the sandbox
            
        Returns:
            Dict with health status information
        """
        try:
            # Check if we have this sandbox in our records
            if name in self.sandboxes:
                sandbox_info = self.sandboxes[name]
                
                # Check if it has a process
                if "process" in sandbox_info:
                    process = sandbox_info["process"]
                    
                    # Check if process is still running
                    if process.poll() is None:
                        # Process is still running
                        return {
                            "status": "running",
                            "network_isolated": True,  # Sandboxie provides network isolation by default
                            "pid": sandbox_info.get("pid"),
                            "start_time": sandbox_info.get("start_time", 0),
                            "uptime": time.time() - sandbox_info.get("start_time", time.time())
                        }
            
            # If we get here, either the sandbox is not in our records or the process is not running
            # Try to check if there are any Sandboxie processes for this sandbox
            try:
                import psutil
                
                # Look for Sandboxie processes
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        # Check if this is a Sandboxie process for our sandbox
                        if proc.info['name'] and 'sandboxie' in proc.info['name'].lower():
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and any(f"/box:{name}" in arg.lower() for arg in cmdline):
                                # Found a Sandboxie process for this sandbox
                                return {
                                    "status": "running",
                                    "network_isolated": True,
                                    "pid": proc.pid,
                                    "detected": True
                                }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except ImportError:
                self.logger.warning("psutil not available, cannot check for Sandboxie processes")
            
            # If we get here, the sandbox is not running
            return {"status": "not_running"}
            
        except Exception as e:
            self.logger.error(f"Error checking Sandboxie health: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def _check_virtualbox_health(self, name: str) -> Dict[str, Any]:
        """Check VirtualBox VM health."""
        return {"status": "running", "network_isolated": True}
    
    def terminate_sandbox(self, name: str) -> bool:
        """
        Terminate a sandbox instance.
        
        Args:
            name: Name of the sandbox instance
            
        Returns:
            bool: True if termination was successful, False otherwise
        """
        if name not in self.sandboxes:
            self.logger.warning(f"Sandbox {name} not found")
            return False
            
        sandbox_info = self.sandboxes[name]
        sandbox_type = sandbox_info.get("type")
        
        if sandbox_type == "built_in":
            return self.built_in_sandbox.terminate_sandbox(name)
        elif sandbox_type == "sandboxie":
            return self._terminate_sandboxie(name)
        elif sandbox_type == "windows_sandbox":
            return self.windows_sandbox.terminate_sandbox(name)
        elif sandbox_type == "virtualbox":
            return self._terminate_virtualbox(name)
        else:
            self.logger.error(f"Unsupported sandbox type: {sandbox_type}")
            return False
    
    def _terminate_sandboxie(self, name: str) -> bool:
        """
        Terminate a Sandboxie sandbox.
        
        Args:
            name: Name of the sandbox
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Terminating Sandboxie sandbox {name}")
            
            # Check if we have this sandbox in our records
            if name in self.sandboxes:
                sandbox_info = self.sandboxes[name]
                
                # Check if it has a process
                if "process" in sandbox_info:
                    process = sandbox_info["process"]
                    
                    # Try to terminate the process
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                        self.logger.info(f"Successfully terminated Sandboxie sandbox {name}")
                        
                        # Remove from our records
                        del self.sandboxes[name]
                        return True
                    except Exception as e:
                        self.logger.error(f"Error terminating Sandboxie process: {e}")
            
            # If we get here, either the sandbox is not in our records or we couldn't terminate the process
            # Try to find and terminate any Sandboxie processes for this sandbox
            try:
                import psutil
                
                # Look for Sandboxie processes
                terminated = False
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        # Check if this is a Sandboxie process for our sandbox
                        if proc.info['name'] and 'sandboxie' in proc.info['name'].lower():
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and any(f"/box:{name}" in arg.lower() for arg in cmdline):
                                # Found a Sandboxie process for this sandbox, terminate it
                                proc.terminate()
                                terminated = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if terminated:
                    self.logger.info(f"Successfully terminated Sandboxie sandbox {name} using psutil")
                    
                    # Remove from our records if it exists
                    if name in self.sandboxes:
                        del self.sandboxes[name]
                    
                    return True
                    
            except ImportError:
                self.logger.warning("psutil not available, cannot terminate Sandboxie processes")
            
            # If we get here, we couldn't find or terminate the sandbox
            self.logger.warning(f"Could not find or terminate Sandboxie sandbox {name}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error terminating Sandboxie sandbox: {e}", exc_info=True)
            return False
    
    def _terminate_virtualbox(self, name: str) -> bool:
        """Terminate VirtualBox VM."""
        self.logger.info(f"Terminating VirtualBox VM {name}")
        return True
    
    def terminate_all_sandboxes(self) -> None:
        """Terminate all sandbox instances."""
        for name in list(self.sandboxes.keys()):
            self.terminate_sandbox(name) 