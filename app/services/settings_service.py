"""
Settings Service Module

This module provides functionality for managing application settings.
It handles loading, saving, and validating settings from configuration files.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

class SettingsService:
    """
    Service for managing application settings.
    """
    def __init__(self, config: Dict[str, Any] = None, config_dir: str = "config"):
        """
        Initialize the settings service.
        
        Args:
            config: Application configuration
            config_dir: Directory containing configuration files
        """
        self.app_config = config or {}
        self.config_dir = config_dir
        self.settings: Dict[str, Any] = {}
        self.default_settings: Dict[str, Any] = {}
        self.observers: Dict[str, List[callable]] = {}
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load default settings
        self._load_default_settings()
        
        # Load user settings
        self._load_settings()
        
        logger.info("Settings service initialized")
        
    def _load_default_settings(self) -> None:
        """Load default settings."""
        default_settings_path = os.path.join(self.config_dir, "default_settings.yaml")
        
        # Create default settings file if it doesn't exist
        if not os.path.exists(default_settings_path):
            self._create_default_settings_file(default_settings_path)
            
        try:
            with open(default_settings_path, 'r') as file:
                self.default_settings = yaml.safe_load(file) or {}
                logger.info("Default settings loaded")
        except Exception as e:
            logger.error(f"Error loading default settings: {str(e)}")
            self.default_settings = {}
            
    def _create_default_settings_file(self, path: str) -> None:
        """
        Create a default settings file.
        
        Args:
            path: Path to the default settings file
        """
        default_settings = {
            "app": {
                "theme": "dark",
                "language": "en",
                "log_level": "INFO",
                "auto_update": True,
                "startup_frame": "login"
            },
            "ui": {
                "font_size": 12,
                "animation_speed": 0.3,
                "show_tooltips": True,
                "compact_mode": False
            },
            "database": {
                "host": "localhost",
                "port": 27017,
                "name": "wydbot_db",
                "auth_enabled": False
            },
            "bot": {
                "default_interval": 1.0,
                "max_retries": 3,
                "timeout": 10.0,
                "auto_restart": False
            },
            "network": {
                "use_vpn": False,
                "use_proxy": False,
                "connection_timeout": 30.0
            },
            "game": {
                "launch_parameters": "",
                "window_mode": "windowed",
                "resolution": "1280x720"
            }
        }
        
        try:
            with open(path, 'w') as file:
                yaml.dump(default_settings, file, default_flow_style=False)
                logger.info(f"Default settings file created at {path}")
        except Exception as e:
            logger.error(f"Error creating default settings file: {str(e)}")
            
    def _load_settings(self) -> None:
        """Load user settings."""
        settings_path = os.path.join(self.config_dir, "settings.yaml")
        
        # If settings file doesn't exist, create it with default settings
        if not os.path.exists(settings_path):
            self.settings = self.default_settings.copy()
            self._save_settings()
            return
            
        try:
            with open(settings_path, 'r') as file:
                user_settings = yaml.safe_load(file) or {}
                
            # Merge user settings with default settings
            self.settings = self.default_settings.copy()
            self._merge_settings(self.settings, user_settings)
            
            logger.info("User settings loaded")
        except Exception as e:
            logger.error(f"Error loading user settings: {str(e)}")
            self.settings = self.default_settings.copy()
            
    def _merge_settings(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively merge source dictionary into target dictionary.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_settings(target[key], value)
            else:
                target[key] = value
                
    def _save_settings(self) -> bool:
        """
        Save current settings to file.
        
        Returns:
            bool: True if settings were saved successfully, False otherwise
        """
        settings_path = os.path.join(self.config_dir, "settings.yaml")
        
        try:
            with open(settings_path, 'w') as file:
                yaml.dump(self.settings, file, default_flow_style=False)
                logger.info("Settings saved")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
            
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a setting value by key path.
        
        Args:
            key_path: Dot-separated path to the setting (e.g., 'app.theme')
            default: Default value to return if setting is not found
            
        Returns:
            Any: Setting value or default if not found
        """
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
        
    def set(self, key_path: str, value: Any) -> bool:
        """
        Set a setting value by key path.
        
        Args:
            key_path: Dot-separated path to the setting (e.g., 'app.theme')
            value: Value to set
            
        Returns:
            bool: True if setting was set successfully, False otherwise
        """
        keys = key_path.split('.')
        target = self.settings
        
        # Navigate to the nested dictionary
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            elif not isinstance(target[key], dict):
                target[key] = {}
            target = target[key]
            
        # Set the value
        target[keys[-1]] = value
        
        # Save settings
        result = self._save_settings()
        
        # Notify observers
        if result:
            self._notify_observers(key_path, value)
            
        return result
        
    def reset(self, key_path: Optional[str] = None) -> bool:
        """
        Reset settings to default values.
        
        Args:
            key_path: Optional dot-separated path to reset specific setting
            
        Returns:
            bool: True if settings were reset successfully, False otherwise
        """
        if key_path:
            # Reset specific setting
            keys = key_path.split('.')
            default_value = self.default_settings
            current = self.settings
            
            # Navigate to the default value
            for key in keys:
                if isinstance(default_value, dict) and key in default_value:
                    default_value = default_value[key]
                else:
                    default_value = None
                    break
                    
            # Set the default value
            return self.set(key_path, default_value)
        else:
            # Reset all settings
            self.settings = self.default_settings.copy()
            result = self._save_settings()
            
            # Notify observers
            if result:
                for key_path in self.observers.keys():
                    value = self.get(key_path)
                    self._notify_observers(key_path, value)
                    
            return result
            
    def register_observer(self, key_path: str, callback: callable) -> None:
        """
        Register an observer for a setting.
        
        Args:
            key_path: Dot-separated path to the setting to observe
            callback: Function to call when setting changes
        """
        if key_path not in self.observers:
            self.observers[key_path] = []
            
        self.observers[key_path].append(callback)
        logger.info(f"Observer registered for setting: {key_path}")
        
    def unregister_observer(self, key_path: str, callback: callable) -> bool:
        """
        Unregister an observer for a setting.
        
        Args:
            key_path: Dot-separated path to the setting
            callback: Function to unregister
            
        Returns:
            bool: True if observer was unregistered successfully, False otherwise
        """
        if key_path in self.observers and callback in self.observers[key_path]:
            self.observers[key_path].remove(callback)
            logger.info(f"Observer unregistered for setting: {key_path}")
            return True
        return False
        
    def _notify_observers(self, key_path: str, value: Any) -> None:
        """
        Notify observers of a setting change.
        
        Args:
            key_path: Dot-separated path to the setting
            value: New setting value
        """
        if key_path in self.observers:
            for callback in self.observers[key_path]:
                try:
                    callback(value)
                except Exception as e:
                    logger.error(f"Error in observer callback for {key_path}: {str(e)}")
                    
    def export_settings(self, path: str) -> bool:
        """
        Export settings to a file.
        
        Args:
            path: Path to export settings to
            
        Returns:
            bool: True if settings were exported successfully, False otherwise
        """
        try:
            with open(path, 'w') as file:
                yaml.dump(self.settings, file, default_flow_style=False)
                logger.info(f"Settings exported to {path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting settings: {str(e)}")
            return False
            
    def import_settings(self, path: str) -> bool:
        """
        Import settings from a file.
        
        Args:
            path: Path to import settings from
            
        Returns:
            bool: True if settings were imported successfully, False otherwise
        """
        try:
            with open(path, 'r') as file:
                imported_settings = yaml.safe_load(file) or {}
                
            # Merge imported settings with default settings
            self.settings = self.default_settings.copy()
            self._merge_settings(self.settings, imported_settings)
            
            # Save settings
            result = self._save_settings()
            
            # Notify observers
            if result:
                for key_path in self.observers.keys():
                    value = self.get(key_path)
                    self._notify_observers(key_path, value)
                    
            logger.info(f"Settings imported from {path}")
            return result
        except Exception as e:
            logger.error(f"Error importing settings: {str(e)}")
            return False
            
    def shutdown(self) -> None:
        """Shutdown the settings service."""
        logger.info("Shutting down settings service")
        
        # Save settings
        self._save_settings()
        
        logger.info("Settings service shutdown complete") 