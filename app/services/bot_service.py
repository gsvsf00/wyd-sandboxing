"""
Bot Service Module

This module provides functionality for managing the bot operations.
It handles bot initialization, control, monitoring, and state management.
"""

import logging
import threading
import time
from typing import Dict, Optional, List, Tuple, Any, Callable

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

class BotService:
    """
    Service for managing bot operations.
    """
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the bot service.
        
        Args:
            config: Application configuration
        """
        self.config = config or {}
        self.is_running = False
        self.is_paused = False
        self.bot_thread: Optional[threading.Thread] = None
        self.stop_bot = threading.Event()
        self.pause_bot = threading.Event()
        self.bot_config: Dict[str, Any] = {}
        self.bot_stats: Dict[str, Any] = {
            'start_time': None,
            'run_duration': 0,
            'actions_performed': 0,
            'success_rate': 0.0,
            'errors': 0,
            'status': 'stopped'
        }
        self.status_callbacks: List[Callable] = []
        
        # Apply settings from config if available
        if self.config and 'bot' in self.config:
            bot_config = self.config['bot']
            
            # Set default configuration
            self.configure({
                'target_game': bot_config.get('target_game', ''),
                'actions': bot_config.get('actions', []),
                'intervals': {
                    'action': bot_config.get('default_interval', 1.0),
                    'health_check': bot_config.get('health_check_interval', 5.0)
                }
            })
        
        logger.info("Bot service initialized")
        
    def register_status_callback(self, callback: Callable) -> None:
        """
        Register a callback function to be called when bot status changes.
        
        Args:
            callback: Function to call when status changes
        """
        self.status_callbacks.append(callback)
        logger.info(f"Status callback registered: {callback.__name__}")
        
    def _notify_status_change(self) -> None:
        """Notify all registered callbacks about status change."""
        status = self.get_status()
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in status callback {callback.__name__}: {str(e)}")
                
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure the bot with the provided settings.
        
        Args:
            config: Dictionary containing bot configuration
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        try:
            # Validate configuration
            required_keys = ['target_game', 'actions', 'intervals']
            for key in required_keys:
                if key not in config:
                    logger.error(f"Missing required configuration key: {key}")
                    return False
                    
            self.bot_config = config
            logger.info("Bot configured successfully")
            return True
        except Exception as e:
            logger.error(f"Error configuring bot: {str(e)}")
            return False
            
    def start(self) -> bool:
        """
        Start the bot.
        
        Returns:
            bool: True if bot was started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Bot is already running")
            return False
            
        if not self.bot_config:
            logger.error("Bot is not configured")
            return False
            
        logger.info("Starting bot")
        
        self.stop_bot.clear()
        self.pause_bot.clear()
        self.is_running = True
        self.is_paused = False
        
        # Update stats
        self.bot_stats['start_time'] = time.time()
        self.bot_stats['run_duration'] = 0
        self.bot_stats['actions_performed'] = 0
        self.bot_stats['errors'] = 0
        self.bot_stats['status'] = 'running'
        
        # Start the bot thread
        self.bot_thread = threading.Thread(target=self._bot_loop)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        
        self._notify_status_change()
        logger.info("Bot started")
        return True
        
    def stop(self) -> bool:
        """
        Stop the bot.
        
        Returns:
            bool: True if bot was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("Bot is not running")
            return False
            
        logger.info("Stopping bot")
        
        self.stop_bot.set()
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=5.0)
            
        self.is_running = False
        self.is_paused = False
        
        # Update stats
        if self.bot_stats['start_time']:
            self.bot_stats['run_duration'] += time.time() - self.bot_stats['start_time']
        self.bot_stats['status'] = 'stopped'
        
        self._notify_status_change()
        logger.info("Bot stopped")
        return True
        
    def pause(self) -> bool:
        """
        Pause the bot.
        
        Returns:
            bool: True if bot was paused successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("Bot is not running")
            return False
            
        if self.is_paused:
            logger.warning("Bot is already paused")
            return False
            
        logger.info("Pausing bot")
        
        self.pause_bot.set()
        self.is_paused = True
        
        # Update stats
        self.bot_stats['status'] = 'paused'
        
        self._notify_status_change()
        logger.info("Bot paused")
        return True
        
    def resume(self) -> bool:
        """
        Resume the bot.
        
        Returns:
            bool: True if bot was resumed successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("Bot is not running")
            return False
            
        if not self.is_paused:
            logger.warning("Bot is not paused")
            return False
            
        logger.info("Resuming bot")
        
        self.pause_bot.clear()
        self.is_paused = False
        
        # Update stats
        self.bot_stats['status'] = 'running'
        
        self._notify_status_change()
        logger.info("Bot resumed")
        return True
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current bot status.
        
        Returns:
            Dict[str, Any]: Dictionary containing bot status information
        """
        # Update run duration if bot is running
        if self.is_running and self.bot_stats['start_time'] and not self.is_paused:
            current_duration = time.time() - self.bot_stats['start_time']
            self.bot_stats['run_duration'] = current_duration
            
        # Calculate success rate
        if self.bot_stats['actions_performed'] > 0:
            success_count = self.bot_stats['actions_performed'] - self.bot_stats['errors']
            self.bot_stats['success_rate'] = (success_count / self.bot_stats['actions_performed']) * 100
            
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'config': self.bot_config,
            'stats': self.bot_stats
        }
        
    def _bot_loop(self) -> None:
        """Main bot execution loop."""
        logger.info("Bot loop started")
        
        try:
            while not self.stop_bot.is_set():
                # Check if paused
                if self.pause_bot.is_set():
                    time.sleep(0.5)
                    continue
                    
                # Perform bot actions
                try:
                    self._perform_action()
                    self.bot_stats['actions_performed'] += 1
                except Exception as e:
                    logger.error(f"Error performing bot action: {str(e)}")
                    self.bot_stats['errors'] += 1
                    
                # Sleep for the configured interval
                interval = self.bot_config.get('intervals', {}).get('action', 1.0)
                time.sleep(interval)
                
        except Exception as e:
            logger.error(f"Error in bot loop: {str(e)}")
            self.bot_stats['errors'] += 1
            
        finally:
            logger.info("Bot loop ended")
            
    def _perform_action(self) -> None:
        """Perform a bot action based on configuration."""
        # This is a placeholder for actual bot actions
        # In a real implementation, this would perform game-specific actions
        
        logger.debug("Performing bot action")
        
        # Simulate action
        time.sleep(0.5)
        
    def shutdown(self) -> None:
        """Shutdown the bot service."""
        logger.info("Shutting down bot service")
        
        # Stop the bot if running
        if self.is_running:
            self.stop()
            
        logger.info("Bot service shutdown complete") 