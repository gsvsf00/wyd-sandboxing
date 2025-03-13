"""
Authentication Cache Module

Provides utilities for caching authentication tokens and automatically logging in users.
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

class AuthCache:
    """
    Manages authentication token caching for automatic login.
    """
    
    def __init__(self, cache_dir: str = "cache", expiry_days: int = 7):
        """
        Initialize the authentication cache.
        
        Args:
            cache_dir: Directory to store cache files
            expiry_days: Number of days before cache entries expire
        """
        self.cache_dir = cache_dir
        self.expiry_days = expiry_days
        self.cache_file = os.path.join(cache_dir, "auth_cache.json")
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load cache
        self.cache = self._load_cache()
        
        # Clean expired entries
        self._clean_expired()
        
    def _load_cache(self) -> Dict[str, Any]:
        """
        Load the cache from disk.
        
        Returns:
            Dict: Cache data
        """
        if not os.path.exists(self.cache_file):
            return {}
            
        try:
            with open(self.cache_file, "r") as f:
                cache = json.load(f)
                
            logger.debug(f"Loaded auth cache with {len(cache)} entries")
            return cache
        except Exception as e:
            logger.error(f"Error loading auth cache: {e}", exc_info=True)
            # If the cache file is corrupted, rename it and create a new one
            try:
                backup_file = f"{self.cache_file}.bak"
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(self.cache_file, backup_file)
                logger.info(f"Renamed corrupted cache file to {backup_file}")
            except Exception as backup_error:
                logger.error(f"Error backing up corrupted cache file: {backup_error}", exc_info=True)
            
            return {}
            
    def _save_cache(self) -> bool:
        """
        Save the cache to disk.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert datetime objects to timestamps before saving
            serializable_cache = {}
            for username, data in self.cache.items():
                serializable_data = {}
                for key, value in data.items():
                    # Convert datetime objects to timestamps
                    if isinstance(value, datetime):
                        serializable_data[key] = value.timestamp()
                    else:
                        serializable_data[key] = value
                serializable_cache[username] = serializable_data
            
            with open(self.cache_file, "w") as f:
                json.dump(serializable_cache, f, indent=2)
            
            logger.debug(f"Saved auth cache with {len(self.cache)} entries")
            return True
        except Exception as e:
            logger.error(f"Error saving auth cache: {e}", exc_info=True)
            return False
            
    def _clean_expired(self) -> None:
        """Clean expired entries from the cache."""
        now = time.time()
        expired = []
        
        for username, data in self.cache.items():
            if data.get("expiry", 0) < now:
                expired.append(username)
                
        for username in expired:
            logger.debug(f"Removing expired cache entry for {username}")
            del self.cache[username]
            
        if expired:
            self._save_cache()
            
    def store_credentials(self, username: str, token: str, user_data: Dict[str, Any]) -> bool:
        """
        Store user credentials in the cache.
        
        Args:
            username: Username
            token: Authentication token
            user_data: User data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate expiry time
            expiry = time.time() + (self.expiry_days * 24 * 60 * 60)
            
            # Store in cache
            self.cache[username] = {
                "token": token,
                "user_data": user_data,
                "expiry": expiry,
                "last_used": time.time()
            }
            
            # Save cache
            success = self._save_cache()
            
            if success:
                logger.info(f"Stored credentials for {username} (expires in {self.expiry_days} days)")
            
            return success
        except Exception as e:
            logger.error(f"Error storing credentials: {e}", exc_info=True)
            return False
            
    def get_credentials(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get cached credentials for a user.
        
        Args:
            username: Username
            
        Returns:
            Dict: Credentials if found and not expired, None otherwise
        """
        # Clean expired entries first
        self._clean_expired()
        
        if username not in self.cache:
            return None
            
        # Update last used time
        self.cache[username]["last_used"] = time.time()
        self._save_cache()
        
        return {
            "token": self.cache[username]["token"],
            "user_data": self.cache[username]["user_data"]
        }
        
    def clear_credentials(self, username: str = None) -> bool:
        """
        Clear cached credentials.
        
        Args:
            username: Username to clear, or None to clear all
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if username:
                if username in self.cache:
                    del self.cache[username]
                    logger.info(f"Cleared credentials for {username}")
                else:
                    logger.debug(f"No cached credentials found for {username}")
            else:
                self.cache = {}
                logger.info("Cleared all cached credentials")
                
            return self._save_cache()
        except Exception as e:
            logger.error(f"Error clearing credentials: {e}", exc_info=True)
            return False
            
    def refresh_expiry(self, username: str) -> bool:
        """
        Refresh the expiry time for a user's credentials.
        
        Args:
            username: Username
            
        Returns:
            bool: True if successful, False otherwise
        """
        if username not in self.cache:
            return False
            
        try:
            # Calculate new expiry time
            expiry = time.time() + (self.expiry_days * 24 * 60 * 60)
            
            # Update expiry
            self.cache[username]["expiry"] = expiry
            self.cache[username]["last_used"] = time.time()
            
            # Save cache
            success = self._save_cache()
            
            if success:
                logger.debug(f"Refreshed expiry for {username} (expires in {self.expiry_days} days)")
            
            return success
        except Exception as e:
            logger.error(f"Error refreshing expiry: {e}", exc_info=True)
            return False
            
    def get_all_users(self) -> Dict[str, Any]:
        """
        Get all cached users.
        
        Returns:
            Dict: Dictionary of username -> user data
        """
        # Clean expired entries first
        self._clean_expired()
        
        users = {}
        
        for username, data in self.cache.items():
            users[username] = {
                "user_data": data["user_data"],
                "expiry": data["expiry"],
                "last_used": data["last_used"]
            }
            
        return users 