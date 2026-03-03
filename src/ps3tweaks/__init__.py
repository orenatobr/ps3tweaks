"""
PS3 Emulator Configuration Manager
Auto-configures memory cards, video, and input for PS1/PS2 emulators
"""

__version__ = "1.0.0"
__author__ = "Renato Pereira"
__all__ = ["PS3EmulatorManager", "EmulatorConfig"]

from .config import EmulatorConfig
from .manager import PS3EmulatorManager
