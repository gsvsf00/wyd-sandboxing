"""
Built-in Sandbox Module

Provides a lightweight sandbox implementation that doesn't require external programs.
Focuses on identity spoofing while allowing full network access.
"""

import os
import subprocess
import tempfile
import random
import string
import logging
import time
import uuid
import json
import shutil
import glob
import winreg
import psutil
from typing import Dict, Any, List, Optional

# Try to import win32 modules, but don't fail if they're not available
try:
    import win32gui
    import win32process
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logger.warning("win32 modules not available, some sandbox features will be limited")

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

class BuiltInSandbox:
    """
    A lightweight sandbox implementation focusing on identity spoofing.
    """
    
    def __init__(self):
        """Initialize the built-in sandbox."""
        self.sandboxes = {}
        self.logger = get_logger(__name__)
        
    def create_sandbox(self, name: str) -> bool:
        """
        Create a new sandbox environment.
        
        Args:
            name: Name for the sandbox
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a unique sandbox ID
            sandbox_id = str(uuid.uuid4())
            
            # Generate random identifiers
            hw_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
            mac_address = ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)])
            computer_name = ''.join(random.choices(string.ascii_uppercase, k=8))
            
            # Store sandbox info
            self.sandboxes[name] = {
                "id": sandbox_id,
                "running": False,
                "processes": [],
                "hwid": hw_id,
                "mac": mac_address,
                "computer_name": computer_name,
                "creation_time": time.time()
            }
            
            self.logger.info(f"Created built-in sandbox: {name} (ID: {sandbox_id})")
            return True
        except Exception as e:
            self.logger.error(f"Error creating built-in sandbox: {e}")
            return False
            
    def launch_in_sandbox(self, name: str, executable_path: str, args: List[str] = None) -> Dict[str, Any]:
        """
        Launch an application with identity spoofing.
        
        Args:
            name: Name of the sandbox
            executable_path: Path to the executable to launch
            args: Additional command line arguments
            
        Returns:
            Dict[str, Any]: Process information dictionary if successful, error info otherwise
        """
        try:
            # Create sandbox if it doesn't exist
            if name not in self.sandboxes:
                if not self.create_sandbox(name):
                    return {"success": False, "error": "Failed to create sandbox"}
                    
            sandbox = self.sandboxes[name]
            
            # Create a temporary directory for identity files
            temp_dir = os.path.join(tempfile.gettempdir(), f"wydbot_identity_{name}_{sandbox['id']}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate additional random identifiers for better spoofing
            ip_address = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
            disk_serial = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            bios_uuid = str(uuid.uuid4())
            motherboard_serial = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            cpu_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
            
            # Create identity files with more detailed information
            identity_data = {
                "hwid": sandbox["hwid"],
                "mac": sandbox["mac"],
                "computer_name": sandbox["computer_name"],
                "ip_address": ip_address,
                "disk_serial": disk_serial,
                "bios_uuid": bios_uuid,
                "motherboard_serial": motherboard_serial,
                "cpu_id": cpu_id,
                "user_name": f"User_{random.randint(1000, 9999)}",
                "sandbox_id": sandbox["id"],
                "machine_guid": str(uuid.uuid4()),
                "product_id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) + '-' + 
                             ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) + '-' +
                             ''.join(random.choices(string.digits, k=5))
            }
            
            # Write identity data to JSON file
            with open(os.path.join(temp_dir, "identity.json"), "w") as f:
                json.dump(identity_data, f, indent=2)
            
            # Create individual identity files for compatibility
            for key, value in identity_data.items():
                with open(os.path.join(temp_dir, f"{key}.txt"), "w") as f:
                    f.write(str(value))
            
            # Create a simplified batch file to launch the game
            batch_path = os.path.join(temp_dir, "launch_game.bat")
            with open(batch_path, "w") as f:
                f.write('@echo off\n')
                f.write('echo Launching game with identity spoofing...\n')
                
                # Set environment variables for identity spoofing
                f.write(f'set COMPUTERNAME={sandbox["computer_name"]}\n')
                f.write(f'set USERDOMAIN={sandbox["computer_name"]}\n')
                f.write(f'set PROCESSOR_IDENTIFIER=WydBot Virtual Family {cpu_id}\n')
                f.write(f'set NUMBER_OF_PROCESSORS=4\n')
                
                # Create a unique user profile path
                f.write(f'set USERPROFILE=%TEMP%\\{sandbox["computer_name"]}\\Users\\{identity_data["user_name"]}\n')
                f.write(f'set HOMEDRIVE=C:\n')
                f.write(f'set HOMEPATH=\\Users\\{identity_data["user_name"]}\n')
                f.write(f'mkdir "%USERPROFILE%" >nul 2>&1\n')
                
                # Create a unique AppData path
                f.write(f'set APPDATA=%USERPROFILE%\\AppData\\Roaming\n')
                f.write(f'set LOCALAPPDATA=%USERPROFILE%\\AppData\\Local\n')
                f.write(f'mkdir "%APPDATA%" >nul 2>&1\n')
                f.write(f'mkdir "%LOCALAPPDATA%" >nul 2>&1\n')
                
                # Create a unique temp directory
                f.write(f'set TEMP=%USERPROFILE%\\AppData\\Local\\Temp\n')
                f.write(f'set TMP=%USERPROFILE%\\AppData\\Local\\Temp\n')
                f.write(f'mkdir "%TEMP%" >nul 2>&1\n')
                
                # Launch the game with its arguments
                game_cmd = f'"{executable_path}"'
                if args:
                    game_cmd += ' ' + ' '.join(args)
                
                # Use start command with a unique title to help identify the window later
                window_title = f"WydBot_{name}_{sandbox['id'][:8]}"
                f.write(f'start "{window_title}" {game_cmd}\n')
            
            # Prepare environment variables for identity spoofing
            env = os.environ.copy()
            
            # Add identity spoofing variables
            for key, value in identity_data.items():
                env[f"WYDBOT_{key.upper()}"] = str(value)
            
            # Add additional environment variables to spoof common detection methods
            env["COMPUTERNAME"] = sandbox["computer_name"]
            env["USERDOMAIN"] = sandbox["computer_name"]
            env["USERDOMAIN_ROAMINGPROFILE"] = sandbox["computer_name"]
            env["PROCESSOR_IDENTIFIER"] = f"WydBot Virtual Family {cpu_id}"
            env["NUMBER_OF_PROCESSORS"] = "4"
            
            # Create temporary directories for the sandbox
            sandbox_user_dir = os.path.join(temp_dir, "Users", identity_data["user_name"])
            os.makedirs(sandbox_user_dir, exist_ok=True)
            
            sandbox_appdata = os.path.join(sandbox_user_dir, "AppData", "Roaming")
            sandbox_localappdata = os.path.join(sandbox_user_dir, "AppData", "Local")
            sandbox_temp = os.path.join(sandbox_localappdata, "Temp")
            
            os.makedirs(sandbox_appdata, exist_ok=True)
            os.makedirs(sandbox_localappdata, exist_ok=True)
            os.makedirs(sandbox_temp, exist_ok=True)
            
            # Set environment variables to use the sandbox directories
            env["USERPROFILE"] = sandbox_user_dir
            env["HOMEDRIVE"] = "C:"
            env["HOMEPATH"] = f"\\Users\\{identity_data['user_name']}"
            env["APPDATA"] = sandbox_appdata
            env["LOCALAPPDATA"] = sandbox_localappdata
            env["TEMP"] = sandbox_temp
            env["TMP"] = sandbox_temp
            
            # Launch the batch file
            process = subprocess.Popen(
                [batch_path],
                env=env,
                cwd=os.path.dirname(executable_path),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Wait a moment for the batch file to start the game
            time.sleep(2)
            
            # Try to find the actual game process
            game_exe_name = os.path.basename(executable_path).lower()
            game_process = None
            window_title = f"WydBot_{name}_{sandbox['id'][:8]}"
            
            # Look for the game process by name and creation time
            for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                try:
                    if proc.info['name'].lower() == game_exe_name and proc.info['create_time'] > time.time() - 10:
                        game_process = proc
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # If we couldn't find the game process by name, try to find it by window title
            if not game_process and WIN32_AVAILABLE:
                try:
                    def find_window_by_title(title):
                        result = []
                        def callback(hwnd, _):
                            if win32gui.IsWindowVisible(hwnd) and title in win32gui.GetWindowText(hwnd):
                                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                                result.append(pid)
                        win32gui.EnumWindows(callback, None)
                        return result
                    
                    pids = find_window_by_title(window_title)
                    if pids:
                        game_process = psutil.Process(pids[0])
                except Exception as e:
                    self.logger.warning(f"Failed to find game process by window title: {e}")
            
            # Store process info
            sandbox["running"] = True
            sandbox["temp_dir"] = temp_dir
            sandbox["identity"] = identity_data
            
            if "processes" not in sandbox:
                sandbox["processes"] = []
            
            # If we couldn't find the game process, just use the batch process
            if not game_process:
                process_info = {
                    "pid": process.pid,
                    "process": process,
                    "executable": executable_path,
                    "start_time": time.time(),
                    "in_sandbox": True,
                    "sandbox_name": name,
                    "sandbox_type": "built_in",
                    "identity": identity_data,
                    "window_title": window_title
                }
            else:
                # Use the game process if found
                process_info = {
                    "pid": game_process.pid,
                    "process": game_process,
                    "executable": executable_path,
                    "start_time": time.time(),
                    "in_sandbox": True,
                    "sandbox_name": name,
                    "sandbox_type": "built_in",
                    "identity": identity_data,
                    "window_title": window_title
                }
            
            sandbox["processes"].append(process_info)
            
            self.logger.info(f"Launched {executable_path} in built-in sandbox {name} with identity spoofing")
            
            # Return the process info for the game launcher service
            return process_info
        except Exception as e:
            self.logger.error(f"Error launching in built-in sandbox: {e}")
            return {"success": False, "error": str(e), "in_sandbox": True, "sandbox_name": name, "sandbox_type": "built_in"}
    
    def _spoof_mac_address_for_process(self, pid: int, mac_address: str):
        """
        Attempt to spoof MAC address in registry for a specific process.
        This is an experimental feature and may not work for all games.
        
        Args:
            pid: Process ID
            mac_address: Spoofed MAC address
        """
        try:
            # This is a placeholder for a more sophisticated implementation
            # In a real implementation, you would need to use process injection
            # or other advanced techniques to modify how the process reads the MAC address
            self.logger.info(f"MAC address spoofing for PID {pid}: {mac_address}")
        except Exception as e:
            self.logger.error(f"Error spoofing MAC address: {e}")
            
    def terminate_sandbox(self, name: str) -> bool:
        """
        Terminate a sandbox and all processes running in it.
        
        Args:
            name: Name of the sandbox
            
        Returns:
            bool: True if termination was successful, False otherwise
        """
        try:
            if name not in self.sandboxes:
                self.logger.warning(f"Sandbox {name} not found")
                return False
                
            sandbox = self.sandboxes[name]
            
            # Terminate all processes
            for proc_info in sandbox["processes"]:
                try:
                    process = proc_info["process"]
                    if process.poll() is None:  # Process is still running
                        process.terminate()
                        process.wait(timeout=2)
                        
                        # Force kill if still running
                        if process.poll() is None:
                            process.kill()
                except Exception as e:
                    self.logger.error(f"Error terminating process in sandbox {name}: {e}")
                    
            # Clean up temporary directory
            try:
                if "temp_dir" in sandbox and os.path.exists(sandbox["temp_dir"]):
                    shutil.rmtree(sandbox["temp_dir"], ignore_errors=True)
            except Exception as e:
                self.logger.error(f"Error cleaning up temporary directory: {e}")
                
            # Remove sandbox from list
            del self.sandboxes[name]
            
            self.logger.info(f"Terminated built-in sandbox {name}")
            return True
        except Exception as e:
            self.logger.error(f"Error terminating built-in sandbox: {e}")
            return False
            
    def check_sandbox_health(self, name: str) -> Dict[str, Any]:
        """
        Check the health of a sandbox.
        
        Args:
            name: Name of the sandbox
            
        Returns:
            Dict[str, Any]: Health information
        """
        try:
            if name not in self.sandboxes:
                return {"status": "not_found"}
                
            sandbox = self.sandboxes[name]
            
            # Check if any processes are still running
            running_processes = []
            for proc_info in sandbox["processes"]:
                process = proc_info["process"]
                if process.poll() is None:  # Process is still running
                    running_processes.append(proc_info)
                    
            return {
                "status": "running" if running_processes else "stopped",
                "process_count": len(running_processes),
                "network_isolated": False,  # We're allowing full network access
                "identity_spoofed": True,   # But we're spoofing identity
                "uptime": time.time() - sandbox.get("creation_time", time.time())
            }
        except Exception as e:
            self.logger.error(f"Error checking sandbox health: {e}")
            return {"status": "error", "error": str(e)} 