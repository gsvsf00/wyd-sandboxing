#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration Utility Module

Provides utilities for loading and managing application configuration.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from app.utils.logging_config import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)

# Default config directory
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config")

# Default config file
DEFAULT_CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_config(config_file: str = DEFAULT_CONFIG_FILE) -> Dict[str, Any]:
    """
    Load configuration from a JSON file and override with environment variables.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = {}
    
    try:
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Check if config file exists
        if not os.path.exists(config_file):
            # Create default config
            config = {
                "application": {
                    "name": "WydBot",
                    "version": "1.0.0",
                    "theme": os.getenv("APP_THEME", "dark"),
                    "language": os.getenv("APP_LANGUAGE", "en"),
                    "debug_mode": os.getenv("APP_DEBUG", "False").lower() == "true"
                },
                "database": {
                    "connection_string": os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017"),
                    "use_mock_db": True  # Use mock database by default
                },
                "logging": {
                    "level": "INFO",
                    "console_level": "INFO",
                    "log_dir": "logs"
                },
                "network": {
                    "use_proxy": os.getenv("USE_PROXY", "False").lower() == "true",
                    "use_vpn": False,
                    "proxy": {
                        "host": os.getenv("PROXY_HOST", ""),
                        "port": int(os.getenv("PROXY_PORT", "0")),
                        "username": os.getenv("PROXY_USERNAME", ""),
                        "password": os.getenv("PROXY_PASSWORD", "")
                    }
                },
                "game": {
                    "paths": {}
                },
                "bot": {
                    "default_interval": float(os.getenv("BOT_DEFAULT_INTERVAL", "1.0")),
                    "health_check_interval": float(os.getenv("BOT_HEALTH_CHECK_INTERVAL", "5.0"))
                }
            }
            
            # Save default config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            logger.info(f"Created default configuration file: {config_file}")
        else:
            # Load existing config
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Override with environment variables
            if "application" in config:
                config["application"]["theme"] = os.getenv("APP_THEME", config["application"].get("theme", "dark"))
                config["application"]["language"] = os.getenv("APP_LANGUAGE", config["application"].get("language", "en"))
                config["application"]["debug_mode"] = os.getenv("APP_DEBUG", str(config["application"].get("debug_mode", False))).lower() == "true"
            
            if "database" in config:
                config["database"]["connection_string"] = os.getenv("MONGODB_CONNECTION_STRING", config["database"].get("connection_string", "mongodb://localhost:27017"))
            
            if "network" in config and "proxy" in config["network"]:
                config["network"]["use_proxy"] = os.getenv("USE_PROXY", str(config["network"].get("use_proxy", False))).lower() == "true"
                config["network"]["proxy"]["host"] = os.getenv("PROXY_HOST", config["network"]["proxy"].get("host", ""))
                config["network"]["proxy"]["port"] = int(os.getenv("PROXY_PORT", str(config["network"]["proxy"].get("port", 0))))
                config["network"]["proxy"]["username"] = os.getenv("PROXY_USERNAME", config["network"]["proxy"].get("username", ""))
                config["network"]["proxy"]["password"] = os.getenv("PROXY_PASSWORD", config["network"]["proxy"].get("password", ""))
            
            if "bot" in config:
                config["bot"]["default_interval"] = float(os.getenv("BOT_DEFAULT_INTERVAL", str(config["bot"].get("default_interval", 1.0))))
                config["bot"]["health_check_interval"] = float(os.getenv("BOT_HEALTH_CHECK_INTERVAL", str(config["bot"].get("health_check_interval", 5.0))))
                
            logger.info(f"Loaded configuration from: {config_file}")
            
        return config
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        return {
            "application": {
                "name": "WydBot",
                "version": "1.0.0",
                "theme": "dark"
            },
            "database": {
                "use_mock": True  # Use mock database in case of error
            }
        }

def save_config(config: Dict[str, Any], config_file: str = DEFAULT_CONFIG_FILE) -> bool:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        config_file: Path to the configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Save config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
            
        logger.info(f"Saved configuration to: {config_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        return False

def get_config_value(key_path, default=None, config=None):
    """
    Get a value from the configuration dictionary using a dot-separated path.
    
    Args:
        key_path: Dot-separated path to the value
        default: Default value to return if the path doesn't exist
        config: Configuration dictionary
        
    Returns:
        Any: Value at the specified path, or the default value if not found
    """
    if config is None:
        return default
        
    keys = key_path.split('.')
    result = config
    
    try:
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError):
        return default

def set_config_value(config: Dict[str, Any], key_path: str, value: Any) -> bool:
    """
    Set a value in the configuration dictionary using a dot-separated path.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path to the value
        value: Value to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    keys = key_path.split('.')
    result = config
    
    try:
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in result:
                result[key] = {}
            result = result[key]
            
        # Set the value
        result[keys[-1]] = value
        return True
    except Exception as e:
        logger.error(f"Error setting configuration value: {e}", exc_info=True)
        return False 