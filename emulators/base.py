"""
Base emulator controller interface
"""

import numpy as np
from abc import ABC, abstractmethod


class BaseEmulatorController(ABC):
    """
    Abstract base class for emulator controllers.
    This class defines the interface for all emulator controllers.
    """

    def __init__(self, device_id: str, instance_name: str):
        self.device_id = device_id
        self.instance_name = instance_name
        self.running = True

    @abstractmethod
    def click(self, x: int, y: int, clicks: int = 1, interval: float = 0.1) -> bool:
        """
        Click on the emulator screen at specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            clicks: Number of clicks (default: 1)
            interval: Interval between clicks (default: 0.1)

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 1000) -> bool:
        """
        Swipe on the emulator screen.

        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            duration: Swipe duration in milliseconds

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def screenshot(self) -> np.ndarray | None:
        """
        Take a screenshot of the emulator screen.

        Returns:
            numpy.ndarray: Screenshot image or None if failed
        """
        pass

    @abstractmethod
    def start_app(self, package_name: str) -> bool:
        """
        Start an application on the emulator.

        Args:
            package_name: Package name of the app to start

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def restart_app(self, package_name: str) -> bool:
        """
        Restart an application on the emulator.

        Args:
            package_name: Package name of the app to restart

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    def stop(self):
        """Stop the emulator controller"""
        self.running = False
