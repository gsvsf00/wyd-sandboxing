"""
Dependency Installer Module

This module provides functionality to check and install required dependencies.
"""

import importlib
import subprocess
import sys
import logging
import os
from typing import List, Tuple

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

def is_dependency_installed(module_name: str) -> bool:
    """
    Check if a dependency is installed.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        bool: True if the module is installed, False otherwise
    """
    try:
        # Special case for pywin32
        if module_name == "pywin32":
            try:
                import win32gui
                import win32process
                import win32con
                return True
            except ImportError:
                return False
        
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def install_dependency(module_name: str) -> bool:
    """
    Install a dependency using pip.
    
    Args:
        module_name: Name of the module to install
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        logger.info(f"Installing dependency: {module_name}")
        
        # Special case for pywin32
        if module_name == "pywin32":
            # First try to install pywin32
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
            
            # Then try to run the post-install script
            try:
                python_path = sys.executable
                scripts_path = os.path.join(os.path.dirname(os.path.dirname(python_path)), "Scripts")
                post_install_script = os.path.join(scripts_path, "pywin32_postinstall.py")
                
                if os.path.exists(post_install_script):
                    logger.info(f"Running pywin32 post-install script: {post_install_script}")
                    subprocess.check_call([python_path, post_install_script, "-install"])
            except Exception as e:
                logger.warning(f"Failed to run pywin32 post-install script: {e}")
                # Continue anyway, as the main package might still work
            
            return True
        else:
            # Normal installation for other packages
            subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            
        logger.info(f"Successfully installed {module_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {module_name}: {e}")
        return False

def ensure_dependencies(dependencies: List[str]) -> Tuple[bool, List[str]]:
    """
    Ensure all required dependencies are installed.
    
    Args:
        dependencies: List of dependencies to check and install
        
    Returns:
        Tuple[bool, List[str]]: (Success status, List of failed dependencies)
    """
    failed_dependencies = []
    
    for dependency in dependencies:
        if not is_dependency_installed(dependency):
            logger.warning(f"Dependency {dependency} not found, attempting to install")
            if not install_dependency(dependency):
                failed_dependencies.append(dependency)
                
    return len(failed_dependencies) == 0, failed_dependencies 