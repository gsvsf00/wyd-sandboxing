#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Authentication Service for WydBot.
Handles user authentication and session management.
"""

import hashlib
import secrets
import time
import threading
import bcrypt
import base64
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from bson import Binary
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import logging

# Import utilities
from app.utils.logger import LoggerWrapper
from app.utils.config import get_config_value

# Global logger instance
logger = LoggerWrapper(name="auth_service")


class AuthService:
    """
    Service for user authentication and session management.
    Provides methods for login, logout, and session validation.
    """
    
    def __init__(self, db_service, config=None):
        """
        Initialize the authentication service.
        
        Args:
            db_service: Database service
            config: Configuration dictionary
        """
        self.db_service = db_service
        self.config = config or {}
        self.active_sessions = {}
        self.sessions_lock = threading.RLock()
        self.token_expiry_days = get_config_value("security.token_expiry_days", 7, self.config)
        
        # Start session cleanup task
        self._start_session_cleanup()
        
        logger.info("Authentication service initialized")

        # Initialize MongoDB client
        self.client = MongoClient('mongodb+srv://gsvsf00:Wf7CZnz6e6mXIpre@cluster0.dbcwlcg.mongodb.net/?retryWrites=true&w=majority')
        self.db = self.client['wydbot']
        self.users_collection = self.db['users']
    
    def _start_session_cleanup(self):
        """Start the session cleanup task."""
        # Create and start the session cleanup thread
        cleanup_thread = threading.Thread(
            target=self._session_cleanup_task,
            name="SessionCleanupThread",
            daemon=True
        )
        cleanup_thread.start()
    
    def _session_cleanup_task(self):
        """Periodically clean up expired sessions."""
        while True:
            try:
                # Sleep for an hour
                time.sleep(3600)
                
                # Clean up expired sessions
                self._cleanup_expired_sessions()
                
            except Exception as e:
                logger.error(f"Error in session cleanup task: {e}")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        with self.sessions_lock:
            now = time.time()
            expired_tokens = []
            
            # Find expired tokens
            for token, session_data in self.active_sessions.items():
                if session_data["expiry"] < now:
                    expired_tokens.append(token)
            
            # Remove expired tokens
            for token in expired_tokens:
                del self.active_sessions[token]
            
            if expired_tokens:
                logger.debug(f"Cleaned up {len(expired_tokens)} expired sessions")
    
    def _encrypt_password(self, password: str) -> Binary:
        """
        Encrypt a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Binary: Encrypted password as Binary object
        """
        # Generate a salt and hash the password
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Convert to Binary for MongoDB storage
        return Binary(hashed)
    
    def _verify_password(self, password: str, hashed_password: Binary) -> bool:
        """
        Verify a password against its hashed version.
        
        Args:
            password: Plain text password to verify
            hashed_password: Binary object containing hashed password
            
        Returns:
            bool: True if password matches, False otherwise
        """
        password_bytes = password.encode('utf-8')
        stored_hash = hashed_password
        
        try:
            return bcrypt.checkpw(password_bytes, stored_hash)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def _generate_token(self) -> str:
        """
        Generate a secure session token.
        
        Returns:
            Secure token
        """
        return secrets.token_hex(32)
    
    def register_user(
        self,
        username: str,
        password: str,
        character_name: str = None,
        server: str = None,
        role: str = "user"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Register a new user.
        
        Args:
            username: Username
            password: Password
            character_name: Character name in game
            server: Game server name
            role: User role (default: user)
            
        Returns:
            Tuple of (success, message, user_id)
        """
        try:
            # Check if username already exists
            existing_user = self.users_collection.find_one({"username": username})
            if existing_user:
                return False, "Username already exists", None
            
            # Encrypt password
            encrypted_password = self._encrypt_password(password)
            
            # Create user document
            user = {
                "username": username,
                "password": encrypted_password,
                "character_name": character_name,
                "server": server,
                "role": role,
                "subscription_end": None,
                "created_at": datetime.utcnow(),
                "last_used": None,
                "is_active": True,
                "notes": None
            }
            
            # Insert into database
            user_id = self.users_collection.insert_one(user).inserted_id
            
            if user_id:
                logger.info(f"User registered: {username} ({role})")
                return True, "User registered successfully", str(user_id)
            else:
                return False, "Failed to register user", None
                
        except PyMongoError as e:
            logger.error(f"Database error: {e}")
            return False, f"Database error: {str(e)}", None
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate a user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Tuple of (success, token/message, user data)
        """
        try:
            # Find user by username
            user = self.users_collection.find_one({"username": username})
            
            if not user:
                logger.warning(f"Login attempt with invalid username: {username}")
                return False, "Invalid username or password", None
            
            # Verify password
            if not self._verify_password(password, user["password"]):
                logger.warning(f"Failed login attempt for user {username}: Invalid password")
                return False, "Invalid username or password", None
            
            # Check if user is active
            if not user.get("is_active", True):
                logger.warning(f"Login attempt for inactive account: {username}")
                return False, "Account is inactive", None
            
            # Check subscription if applicable
            subscription_end = user.get("subscription_end")
            if subscription_end and isinstance(subscription_end, datetime) and subscription_end < datetime.utcnow():
                logger.warning(f"Login attempt for expired subscription: {username}")
                return False, "Subscription has expired", None
            
            # Generate token
            token = self._generate_token()
            
            # Create session data
            expiry = time.time() + (self.token_expiry_days * 24 * 60 * 60)
            session_data = {
                "user_id": str(user["_id"]),
                "username": username,
                "role": user.get("role", "user"),
                "created": time.time(),
                "expiry": expiry,
                "ip": None,  # Will be set by caller
                "user_agent": None  # Will be set by caller
            }
            
            # Store session
            with self.sessions_lock:
                self.active_sessions[token] = session_data
            
            # Update last login
            self.users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_used": datetime.utcnow()}}
            )
            
            # Create safe user data
            safe_user = {
                "id": str(user["_id"]),
                "username": user["username"],
                "character_name": user.get("character_name"),
                "server": user.get("server"),
                "role": user.get("role", "user"),
                "subscription_end": user.get("subscription_end"),
                "created_at": user.get("created_at"),
                "is_active": user.get("is_active", True)
            }
            
            logger.info(f"User authenticated: {username}")
            return True, token, safe_user
            
        except PyMongoError as e:
            logger.error(f"Database error: {e}")
            return False, f"Database error: {str(e)}", None
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a session token.
        
        Args:
            token: Session token
            
        Returns:
            Tuple of (valid, user data)
        """
        with self.sessions_lock:
            session_data = self.active_sessions.get(token)
            
            if not session_data:
                return False, None
            
            # Check if expired
            if session_data["expiry"] < time.time():
                # Remove expired session
                del self.active_sessions[token]
                return False, None
            
            # Get user data
            user_id = session_data["user_id"]
            user = self.users_collection.find_one({"_id": user_id})
            
            if not user:
                # Remove invalid session
                del self.active_sessions[token]
                return False, None
            
            # Check if user is still active
            if user.get("status") != "active":
                # Remove session for inactive user
                del self.active_sessions[token]
                return False, None
            
            # Create safe user data
            safe_user = {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "subscription": user.get("subscription", {})
            }
            
            return True, safe_user
    
    def invalidate_token(self, token: str) -> bool:
        """
        Invalidate a session token.
        
        Args:
            token: Session token
            
        Returns:
            True if the token was invalidated, False otherwise
        """
        with self.sessions_lock:
            if token in self.active_sessions:
                del self.active_sessions[token]
                return True
            
            return False
    
    def invalidate_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of invalidated sessions
        """
        with self.sessions_lock:
            # Find all sessions for the user
            tokens_to_remove = []
            
            for token, session_data in self.active_sessions.items():
                if session_data["user_id"] == user_id:
                    tokens_to_remove.append(token)
            
            # Remove the sessions
            for token in tokens_to_remove:
                del self.active_sessions[token]
            
            return len(tokens_to_remove)
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change a user's password.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            Tuple of (success, message)
        """
        # Get user
        user = self.users_collection.find_one({"_id": user_id})
        
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not self._verify_password(current_password, user["password"]):
            return False, "Current password is incorrect"
        
        # Hash new password
        hashed_new = self._encrypt_password(new_password)
        
        # Update password
        result = self.users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "password": hashed_new,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result and result.get("modified_count", 0) > 0:
            # Invalidate all sessions
            self.invalidate_user_sessions(user_id)
            
            logger.info(f"Password changed for user: {user['username']}")
            return True, "Password changed successfully"
        else:
            return False, "Failed to change password"
    
    def update_subscription(
        self,
        user_id: str,
        active: bool,
        expiry_days: int,
        plan: str
    ) -> Tuple[bool, str]:
        """
        Update a user's subscription.
        
        Args:
            user_id: User ID
            active: Whether the subscription is active
            expiry_days: Number of days until expiry
            plan: Subscription plan
            
        Returns:
            Tuple of (success, message)
        """
        # Calculate expiry date
        expiry = datetime.utcnow() + timedelta(days=expiry_days)
        
        # Update subscription
        result = self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "subscription.active": active,
                "subscription.expiry": expiry,
                "subscription.plan": plan,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result and result.get("modified_count", 0) > 0:
            logger.info(f"Subscription updated for user ID {user_id}: {plan}, active={active}, expiry={expiry_days} days")
            return True, "Subscription updated successfully"
        else:
            return False, "Failed to update subscription"
    
    def get_active_sessions(self) -> List[Dict]:
        """
        Get all active sessions.
        
        Returns:
            List of session data
        """
        with self.sessions_lock:
            # Create a safe copy
            sessions = []
            
            for token, session_data in self.active_sessions.items():
                # Add masked token
                masked_token = token[:8] + "..." + token[-8:]
                
                session = session_data.copy()
                session["token"] = masked_token
                sessions.append(session)
            
            return sessions
    
    def update_user_status(self, user_id: str, status: str) -> Tuple[bool, str]:
        """
        Update a user's status.
        
        Args:
            user_id: User ID
            status: New status (active, suspended, banned)
            
        Returns:
            Tuple of (success, message)
        """
        # Validate status
        valid_statuses = ["active", "suspended", "banned"]
        if status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        
        # Update status
        result = self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }}
        )
        
        if result and result.get("modified_count", 0) > 0:
            # If status is not active, invalidate all sessions
            if status != "active":
                self.invalidate_user_sessions(user_id)
            
            logger.info(f"Status updated for user ID {user_id}: {status}")
            return True, f"User status updated to {status}"
        else:
            return False, "Failed to update user status"
    
    def check_health(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check if we're using a mock database
            if hasattr(self.db_service, 'use_mock_db') and self.db_service.use_mock_db:
                return True
                
            # Check if database is accessible
            if hasattr(self, 'client') and self.client:
                return self.client.server_info() is not None
            
            # If we don't have a client, check the database service
            return self.db_service.check_health()
        except Exception as e:
            logger.error(f"Database error: {e}")
            return False
    
    def shutdown(self):
        """Shut down the authentication service."""
        # Nothing to clean up
        pass 