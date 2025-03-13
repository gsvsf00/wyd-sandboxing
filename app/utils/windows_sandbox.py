"""
Windows Sandbox Module

Provides functionality for running applications in Windows Sandbox.
"""

import os
import subprocess
import tempfile
import logging
import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import random
import string

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

class WindowsSandbox:
    """
    Windows Sandbox implementation.
    """
    
    def __init__(self):
        """Initialize the Windows Sandbox manager."""
        self.sandboxes = {}
        self.logger = get_logger(__name__)
        self.sandbox_path = "C:\\Windows\\System32\\WindowsSandbox.exe"
        
    def is_available(self) -> bool:
        """
        Check if Windows Sandbox is available on the system.
        
        Returns:
            bool: True if Windows Sandbox is available, False otherwise
        """
        try:
            # Check if Windows Sandbox executable exists
            if not os.path.exists(self.sandbox_path):
                return False
                
            # Instead of running the executable with a timeout (which causes errors),
            # just check if the feature is enabled in Windows
            
            # Check if Windows Sandbox feature is enabled using PowerShell
            result = subprocess.run(
                ["powershell", "-Command", "Get-WindowsOptionalFeature -Online -FeatureName 'Containers-DisposableClientVM'"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # If the feature is enabled, the output will contain "Enabled : True"
            return "State : Enabled" in result.stdout
        except Exception as e:
            self.logger.error(f"Error checking Windows Sandbox availability: {e}")
            return False
            
    def create_sandbox_config(self, name: str, executable_path: str, args: List[str] = None) -> str:
        """
        Create a Windows Sandbox configuration file.
        
        Args:
            name: Name for the sandbox
            executable_path: Path to the executable to launch
            args: Additional command line arguments
            
        Returns:
            str: Path to the configuration file, or None if failed
        """
        try:
            # Create a temporary directory for sandbox files
            sandbox_dir = os.path.join(tempfile.gettempdir(), f"wydbot_winsandbox_{name}")
            os.makedirs(sandbox_dir, exist_ok=True)
            
            # Create a unique identity for this sandbox
            computer_name = ''.join(random.choices(string.ascii_uppercase, k=8))
            mac_address = ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)])
            ip_address = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
            
            # Create a setup script to run before the game
            setup_script_path = os.path.join(sandbox_dir, "setup.ps1")
            with open(setup_script_path, "w") as f:
                f.write("# Setup script for Windows Sandbox\n")
                f.write(f"$ComputerName = '{computer_name}'\n")
                f.write(f"$MacAddress = '{mac_address}'\n")
                f.write(f"$IpAddress = '{ip_address}'\n\n")
                
                # Change computer name
                f.write("# Change computer name\n")
                f.write("Rename-Computer -NewName $ComputerName -Force\n\n")
                
                # Spoof MAC address
                f.write("# Spoof MAC address\n")
                f.write("Get-NetAdapter | ForEach-Object {\n")
                f.write("    $adapterName = $_.Name\n")
                f.write("    $registryPath = \"HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4D36E972-E325-11CE-BFC1-08002BE10318}\\\" + $_.DeviceID\n")
                f.write("    Set-ItemProperty -Path $registryPath -Name \"NetworkAddress\" -Value ($MacAddress -replace ':', '')\n")
                f.write("}\n\n")
                
                # Spoof IP address
                f.write("# Spoof IP address\n")
                f.write("Get-NetAdapter | ForEach-Object {\n")
                f.write("    $adapterName = $_.Name\n")
                f.write("    New-NetIPAddress -InterfaceAlias $adapterName -IPAddress $IpAddress -PrefixLength 24 -DefaultGateway \"192.168.1.1\" -ErrorAction SilentlyContinue\n")
                f.write("}\n\n")
                
                # Modify registry to spoof hardware identifiers
                f.write("# Spoof hardware identifiers\n")
                f.write("$biosGuid = [System.Guid]::NewGuid().ToString()\n")
                f.write("$diskSerial = -join ((65..90) + (48..57) | Get-Random -Count 12 | ForEach-Object {[char]$_})\n")
                f.write("$motherboardSerial = -join ((65..90) + (48..57) | Get-Random -Count 16 | ForEach-Object {[char]$_})\n\n")
                
                f.write("# BIOS information\n")
                f.write("New-Item -Path \"HKLM:\\HARDWARE\\DESCRIPTION\\System\\BIOS\" -Force | Out-Null\n")
                f.write("Set-ItemProperty -Path \"HKLM:\\HARDWARE\\DESCRIPTION\\System\\BIOS\" -Name \"SystemManufacturer\" -Value \"WydBot VM\" -Type String\n")
                f.write("Set-ItemProperty -Path \"HKLM:\\HARDWARE\\DESCRIPTION\\System\\BIOS\" -Name \"SystemProductName\" -Value \"WydBot Virtual System\" -Type String\n")
                f.write("Set-ItemProperty -Path \"HKLM:\\HARDWARE\\DESCRIPTION\\System\\BIOS\" -Name \"SystemFamily\" -Value \"Virtual System\" -Type String\n")
                f.write("Set-ItemProperty -Path \"HKLM:\\HARDWARE\\DESCRIPTION\\System\\BIOS\" -Name \"SystemSKU\" -Value $biosGuid -Type String\n")
                f.write("Set-ItemProperty -Path \"HKLM:\\HARDWARE\\DESCRIPTION\\System\\BIOS\" -Name \"SystemUUID\" -Value $biosGuid -Type String\n\n")
                
                f.write("# Disk information\n")
                f.write("New-Item -Path \"HKLM:\\HARDWARE\\DEVICEMAP\\Scsi\\Scsi Port 0\\Scsi Bus 0\\Target Id 0\\Logical Unit Id 0\" -Force | Out-Null\n")
                f.write("Set-ItemProperty -Path \"HKLM:\\HARDWARE\\DEVICEMAP\\Scsi\\Scsi Port 0\\Scsi Bus 0\\Target Id 0\\Logical Unit Id 0\" -Name \"SerialNumber\" -Value $diskSerial -Type String\n")
                f.write("Set-ItemProperty -Path \"HKLM:\\HARDWARE\\DEVICEMAP\\Scsi\\Scsi Port 0\\Scsi Bus 0\\Target Id 0\\Logical Unit Id 0\" -Name \"Identifier\" -Value \"WydBot_VirtualDisk_$diskSerial\" -Type String\n\n")
                
                # Create a batch file to launch the game
                game_exe = os.path.basename(executable_path)
                game_args_str = " ".join(args) if args else ""
                
                f.write("# Create a batch file to launch the game\n")
                f.write("$gameScript = @\"\n")
                f.write("@echo off\n")
                f.write("echo Starting game with spoofed identity...\n")
                f.write(f"cd /d C:\\Game\n")
                f.write(f"start \"\" \"{game_exe}\" {game_args_str}\n")
                f.write("\"@\n\n")
                
                f.write("$gameScriptPath = \"C:\\Game\\launch_game.bat\"\n")
                f.write("Set-Content -Path $gameScriptPath -Value $gameScript\n")
                
                # Make the script executable
                f.write("# Make the script executable\n")
                f.write("icacls $gameScriptPath /grant Everyone:F\n")
            
            # Create the XML structure for the WSB file
            root = ET.Element("Configuration")
            
            # Add sandbox settings
            ET.SubElement(root, "VGpu").text = "Enable"
            ET.SubElement(root, "Networking").text = "Default"
            ET.SubElement(root, "MemoryInMB").text = "4096"
            
            # Create a mapped folder for the game
            mapped_folders = ET.SubElement(root, "MappedFolders")
            
            # Map the game folder
            game_folder = ET.SubElement(mapped_folders, "MappedFolder")
            ET.SubElement(game_folder, "HostFolder").text = os.path.dirname(executable_path)
            ET.SubElement(game_folder, "SandboxFolder").text = "C:\\Game"
            ET.SubElement(game_folder, "ReadOnly").text = "false"
            
            # Map the setup script folder
            script_folder = ET.SubElement(mapped_folders, "MappedFolder")
            ET.SubElement(script_folder, "HostFolder").text = sandbox_dir
            ET.SubElement(script_folder, "SandboxFolder").text = "C:\\Setup"
            ET.SubElement(script_folder, "ReadOnly").text = "false"
            
            # Create a logon command that runs the setup script and then launches the game
            logon_command = "powershell.exe -ExecutionPolicy Bypass -File C:\\Setup\\setup.ps1; C:\\Game\\launch_game.bat"
            ET.SubElement(root, "LogonCommand").text = logon_command
            
            # Write the configuration to file
            config_path = os.path.join(sandbox_dir, f"{name}_config.wsb")
            tree = ET.ElementTree(root)
            tree.write(config_path, encoding="utf-8", xml_declaration=True)
            
            # Store sandbox info
            self.sandboxes[name] = {
                "dir": sandbox_dir,
                "config": config_path,
                "running": False,
                "computer_name": computer_name,
                "mac_address": mac_address,
                "ip_address": ip_address
            }
            
            self.logger.info(f"Created Windows Sandbox configuration: {config_path} with identity spoofing")
            return config_path
        except Exception as e:
            self.logger.error(f"Error creating Windows Sandbox configuration: {e}")
            return None
            
    def _create_logon_command(self, executable_path: str, args: List[str] = None) -> str:
        """
        Create the logon command for Windows Sandbox.
        
        Args:
            executable_path: Path to the executable to launch
            args: Additional command line arguments
            
        Returns:
            str: Logon command
        """
        # Get the executable name
        exe_name = os.path.basename(executable_path)
        
        # Create the command
        command = f"C:\\Game\\{exe_name}"
        
        # Add arguments if provided
        if args and len(args) > 0:
            args_str = " ".join(args)
            command = f"{command} {args_str}"
            
        # Wrap in cmd.exe to keep the window open
        return f"cmd.exe /c start \"\" \"{command}\""
            
    def launch_in_sandbox(self, name: str, executable_path: str, args: List[str] = None) -> bool:
        """
        Launch an application in Windows Sandbox.
        
        Args:
            name: Name of the sandbox
            executable_path: Path to the executable to launch
            args: Additional command line arguments
            
        Returns:
            bool: True if launch was successful, False otherwise
        """
        try:
            # Create sandbox configuration
            config_path = self.create_sandbox_config(name, executable_path, args)
            if not config_path:
                return False
                
            # Launch Windows Sandbox with the configuration
            process = subprocess.Popen(
                [self.sandbox_path, config_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Update sandbox status
            sandbox = self.sandboxes[name]
            sandbox["running"] = True
            sandbox["process"] = process
            
            self.logger.info(f"Launched {executable_path} in Windows Sandbox {name}")
            return True
        except Exception as e:
            self.logger.error(f"Error launching in Windows Sandbox: {e}")
            return False
            
    def terminate_sandbox(self, name: str) -> bool:
        """
        Terminate a Windows Sandbox.
        
        Args:
            name: Name of the sandbox
            
        Returns:
            bool: True if termination was successful, False otherwise
        """
        try:
            if name not in self.sandboxes:
                self.logger.warning(f"Windows Sandbox {name} not found")
                return False
                
            sandbox = self.sandboxes[name]
            
            # Terminate the process if it's running
            if sandbox.get("running", False) and sandbox.get("process"):
                process = sandbox["process"]
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    process.wait(timeout=5)
                    
                    # Force kill if still running
                    if process.poll() is None:
                        process.kill()
                        
            # Clean up sandbox directory
            try:
                import shutil
                shutil.rmtree(sandbox["dir"], ignore_errors=True)
            except Exception as e:
                self.logger.error(f"Error cleaning up Windows Sandbox directory: {e}")
                
            # Remove sandbox from list
            del self.sandboxes[name]
            
            self.logger.info(f"Terminated Windows Sandbox {name}")
            return True
        except Exception as e:
            self.logger.error(f"Error terminating Windows Sandbox: {e}")
            return False
            
    def check_sandbox_health(self, name: str) -> Dict[str, Any]:
        """
        Check the health of a Windows Sandbox.
        
        Args:
            name: Name of the sandbox
            
        Returns:
            Dict[str, Any]: Health information
        """
        try:
            if name not in self.sandboxes:
                return {"status": "not_found"}
                
            sandbox = self.sandboxes[name]
            
            # Check if process is still running
            running = False
            if sandbox.get("process"):
                running = sandbox["process"].poll() is None
                
            return {
                "status": "running" if running else "stopped",
                "network_isolated": False,  # Windows Sandbox has network access by default
                "directory": sandbox["dir"]
            }
        except Exception as e:
            self.logger.error(f"Error checking Windows Sandbox health: {e}")
            return {"status": "error", "error": str(e)} 