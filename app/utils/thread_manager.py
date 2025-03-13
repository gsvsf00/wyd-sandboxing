#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Thread Manager for the WydBot application.
Handles background tasks and ensures thread safety for UI operations.
"""

import threading
import queue
import time
import traceback
from typing import Callable, Any, Dict, List, Optional, Tuple, Union
from functools import wraps

# Import the logger
from app.utils.logger import LoggerWrapper

# Global logger instance
logger = LoggerWrapper(name="thread_manager")


class ThreadTask:
    """Represents a task to be executed in a background thread."""
    
    def __init__(
        self,
        task_id: str,
        func: Callable,
        args: Tuple = None,
        kwargs: Dict = None,
        callback: Callable = None,
        error_callback: Callable = None
    ):
        """
        Initialize a thread task.
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            callback: Function to call with the result
            error_callback: Function to call on error
        """
        self.task_id = task_id
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.callback = callback
        self.error_callback = error_callback
        self.result = None
        self.error = None
        self.completed = False
        self.cancelled = False
        self.start_time = None
        self.end_time = None


class ThreadManager:
    """
    Manages background threads and ensures thread safety.
    Implements a message queue for thread communication.
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize the thread manager.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
        self.workers: List[threading.Thread] = []
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.tasks: Dict[str, ThreadTask] = {}
        self.tasks_lock = threading.RLock()
        self.shutdown_event = threading.Event()
        self.main_thread_id = threading.current_thread().ident
        
        # Start worker threads
        self._start_workers()
    
    def _start_workers(self):
        """Start worker threads to process tasks."""
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"ThreadManager-Worker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        # Start result processor
        result_processor = threading.Thread(
            target=self._process_results,
            name="ThreadManager-ResultProcessor",
            daemon=True
        )
        result_processor.start()
        self.workers.append(result_processor)
        
        logger.info(f"Started {self.max_workers} worker threads")
    
    def _worker_loop(self):
        """Worker thread loop to process tasks from the queue."""
        while not self.shutdown_event.is_set():
            try:
                # Get a task from the queue with timeout
                try:
                    task = self.task_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Skip if task was cancelled
                if task.cancelled:
                    self.task_queue.task_done()
                    continue
                
                # Execute the task
                task.start_time = time.time()
                try:
                    result = task.func(*task.args, **task.kwargs)
                    task.result = result
                    task.error = None
                except Exception as e:
                    task.result = None
                    task.error = e
                    logger.error(f"Error in task {task.task_id}: {str(e)}")
                    logger.debug(traceback.format_exc())
                
                task.end_time = time.time()
                task.completed = True
                
                # Put the completed task in the result queue
                self.result_queue.put(task)
                
                # Mark the task as done in the queue
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in worker thread: {str(e)}")
    
    def _process_results(self):
        """Process completed tasks and execute callbacks."""
        while not self.shutdown_event.is_set():
            try:
                # Get a completed task from the result queue with timeout
                try:
                    task = self.result_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Remove the task from the active tasks
                with self.tasks_lock:
                    if task.task_id in self.tasks:
                        del self.tasks[task.task_id]
                
                # Execute the appropriate callback
                if task.error is not None and task.error_callback is not None:
                    try:
                        task.error_callback(task.error)
                    except Exception as e:
                        logger.error(f"Error in error callback for task {task.task_id}: {str(e)}")
                
                elif task.error is None and task.callback is not None:
                    try:
                        task.callback(task.result)
                    except Exception as e:
                        logger.error(f"Error in callback for task {task.task_id}: {str(e)}")
                
                # Log task completion
                duration = task.end_time - task.start_time if task.start_time and task.end_time else 0
                if task.error:
                    logger.debug(f"Task {task.task_id} failed after {duration:.3f}s")
                else:
                    logger.debug(f"Task {task.task_id} completed in {duration:.3f}s")
                
                # Mark the result as processed
                self.result_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in result processor: {str(e)}")
    
    def submit_task(
        self,
        func: Callable,
        args: Tuple = None,
        kwargs: Dict = None,
        task_id: str = None,
        callback: Callable = None,
        error_callback: Callable = None
    ) -> str:
        """
        Submit a task to be executed in a background thread.
        
        Args:
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            task_id: Unique identifier for the task (generated if None)
            callback: Function to call with the result
            error_callback: Function to call on error
            
        Returns:
            Task ID
        """
        # Generate a task ID if not provided
        if task_id is None:
            task_id = f"task-{threading.get_ident()}-{time.time()}"
        
        # Create the task
        task = ThreadTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            callback=callback,
            error_callback=error_callback
        )
        
        # Add the task to the active tasks
        with self.tasks_lock:
            self.tasks[task_id] = task
        
        # Add the task to the queue
        self.task_queue.put(task)
        
        logger.debug(f"Submitted task {task_id}")
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task if it hasn't started yet.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if the task was cancelled, False otherwise
        """
        with self.tasks_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if not task.completed:
                    task.cancelled = True
                    del self.tasks[task_id]
                    logger.debug(f"Cancelled task {task_id}")
                    return True
        
        return False
    
    def wait_for_task(self, task_id: str, timeout: float = None) -> bool:
        """
        Wait for a task to complete.
        
        Args:
            task_id: Task ID to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if the task completed, False otherwise
        """
        start_time = time.time()
        
        while True:
            # Check if the task is still active
            with self.tasks_lock:
                if task_id not in self.tasks:
                    return True
            
            # Check timeout
            if timeout is not None and time.time() - start_time > timeout:
                return False
            
            # Sleep a bit to avoid busy waiting
            time.sleep(0.1)
    
    def shutdown(self, wait: bool = True):
        """
        Shut down the thread manager.
        
        Args:
            wait: Whether to wait for all tasks to complete
        """
        logger.info("Shutting down thread manager")
        
        # Signal workers to stop
        self.shutdown_event.set()
        
        # Wait for queues to empty if requested
        if wait:
            logger.debug("Waiting for task queue to empty")
            self.task_queue.join()
            logger.debug("Waiting for result queue to empty")
            self.result_queue.join()
        
        logger.info("Thread manager shutdown complete")


# Global thread manager instance
_thread_manager = None


def get_thread_manager(max_workers: int = 4) -> ThreadManager:
    """
    Get the global thread manager instance.
    
    Args:
        max_workers: Maximum number of worker threads
        
    Returns:
        ThreadManager instance
    """
    global _thread_manager
    
    if _thread_manager is None:
        _thread_manager = ThreadManager(max_workers=max_workers)
    
    return _thread_manager


def run_in_background(
    callback: Callable = None,
    error_callback: Callable = None
) -> Callable:
    """
    Decorator to run a function in a background thread.
    
    Args:
        callback: Function to call with the result
        error_callback: Function to call on error
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            thread_manager = get_thread_manager()
            return thread_manager.submit_task(
                func=func,
                args=args,
                kwargs=kwargs,
                callback=callback,
                error_callback=error_callback
            )
        return wrapper
    return decorator


def run_on_main_thread(func: Callable) -> None:
    """
    Run a function on the main thread.
    If already on the main thread, run immediately.
    Otherwise, schedule to run on the main thread.
    
    Args:
        func: Function to run
    """
    if threading.current_thread().ident == get_thread_manager().main_thread_id:
        # Already on the main thread, run immediately
        func()
    else:
        # Schedule to run on the main thread
        # This implementation depends on the UI framework
        # For Tkinter, we'll implement this in the UI module
        from app.ui.utils import schedule_on_main_thread
        schedule_on_main_thread(func) 