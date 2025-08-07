"""RPG Roleplay System - A production-ready roleplay system using Gemini Flash 2.5."""

__version__ = "1.0.0"
__author__ = "RPG System"

from .core.gemini_client import GeminiClient
from .core.context_manager import ContextManager
from .core.memory_system import MemorySystem
from .scenarios.scenario_loader import ScenarioLoader
from .characters.character_system import CharacterSystem
from .world.world_state import WorldState
from .interface.cli_interface import CLIInterface

__all__ = [
    "GeminiClient",
    "ContextManager", 
    "MemorySystem",
    "ScenarioLoader",
    "CharacterSystem",
    "WorldState",
    "CLIInterface"
]