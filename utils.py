"""
Utility functions for common patterns across the codebase
"""

import time
import random


def wait_with_timeout(condition_func, timeout, interval=1.0, on_iteration=None):
    """
    Generic timeout waiting with condition checking.
    
    Args:
        condition_func: Callable that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Time to sleep between checks in seconds
        on_iteration: Optional callable to execute on each iteration (receives elapsed time)
    
    Returns:
        bool: True if condition was met, False if timeout occurred
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        if on_iteration:
            elapsed = time.time() - start_time
            on_iteration(elapsed)
        time.sleep(interval)
    return False


def retry_with_fallback(action_func, check_func, max_attempts=3, delay=1.0, on_retry=None):
    """
    Retry an action with fallback mechanism.
    
    Args:
        action_func: Callable to perform the action
        check_func: Callable to check if action succeeded (returns bool)
        max_attempts: Maximum number of retry attempts
        delay: Delay between attempts in seconds
        on_retry: Optional callable to execute on retry (receives attempt number)
    
    Returns:
        bool: True if action succeeded, False if all attempts failed
    """
    for attempt in range(1, max_attempts + 1):
        action_func()
        
        if check_func():
            return True
        
        if attempt < max_attempts:
            if on_retry:
                on_retry(attempt)
            time.sleep(delay)
    
    return False


def random_delay(min_seconds, max_seconds):
    """
    Sleep for a random duration between min and max seconds.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def exponential_backoff(attempt, base_delay=1.0, max_delay=30.0):
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Current attempt number (1-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap in seconds
    
    Returns:
        float: Calculated delay in seconds
    """
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    # Add jitter to prevent thundering herd
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter
