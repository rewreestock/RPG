"""Clean command-line interface for the RP system."""

import logging
import asyncio
import time
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path
import argparse
import os

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.live import Live
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..core.gemini_client import GeminiClient
from ..core.context_manager import ContextManager
from ..core.memory_system import MemorySystem
from ..core.search_integration import SearchIntegration
from ..scenarios.scenario_loader import ScenarioLoader
from ..characters.character_system import CharacterSystem
from ..characters.personality_engine import PersonalityEngine
from ..world.world_state import WorldState
from ..world.event_system import EventSystem
from .config_manager import ConfigManager


class CLIInterface:
    """Clean command-line interface for the RP system."""
    
    def __init__(self):
        """Initialize CLI interface."""
        # Set up logging first
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Rich console for enhanced output
        self.console = Console() if RICH_AVAILABLE else None
        
        # Core components
        self.config_manager = ConfigManager()
        self.gemini_client: Optional[GeminiClient] = None
        self.context_manager: Optional[ContextManager] = None
        self.memory_system: Optional[MemorySystem] = None
        self.search_integration: Optional[SearchIntegration] = None
        self.scenario_loader: Optional[ScenarioLoader] = None
        self.character_system: Optional[CharacterSystem] = None
        self.personality_engine: Optional[PersonalityEngine] = None
        self.world_state: Optional[WorldState] = None
        self.event_system: Optional[EventSystem] = None
        
        # Current scenario
        self.current_scenario = None
        
        # Runtime state
        self.running = False
        self.session_start_time = time.time()
        
        self.logger.info("Initialized CLI interface")
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rp_system.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _print(self, message: str, style: Optional[str] = None) -> None:
        """Print message with optional Rich styling."""
        if self.console and RICH_AVAILABLE:
            if style:
                self.console.print(message, style=style)
            else:
                self.console.print(message)
        else:
            print(message)
    
    def _print_panel(self, content: str, title: str = "", border_style: str = "blue") -> None:
        """Print content in a panel."""
        if self.console and RICH_AVAILABLE:
            panel = Panel(content, title=title, border_style=border_style)
            self.console.print(panel)
        else:
            print(f"\n=== {title} ===")
            print(content)
            print("=" * (len(title) + 8))
    
    def _prompt(self, message: str, default: str = "") -> str:
        """Prompt user for input."""
        if RICH_AVAILABLE:
            return Prompt.ask(message, default=default)
        else:
            response = input(f"{message}: ")
            return response if response else default
    
    def _confirm(self, message: str, default: bool = False) -> bool:
        """Prompt user for confirmation."""
        if RICH_AVAILABLE:
            return Confirm.ask(message, default=default)
        else:
            response = input(f"{message} ({'Y/n' if default else 'y/N'}): ").lower()
            if default:
                return response != 'n'
            else:
                return response == 'y'
    
    def initialize_system(self) -> bool:
        """Initialize all system components.
        
        Returns:
            True if successful
        """
        try:
            self._print("Initializing RP system...", "blue")
            
            # Validate configuration
            config_issues = self.config_manager.validate_config()
            if config_issues:
                self._print("Configuration issues found:", "red")
                for issue in config_issues:
                    self._print(f"  - {issue}", "red")
                
                if not self._confirm("Continue anyway?", False):
                    return False
            
            # Get configurations
            system_config = self.config_manager.get_system_config()
            session_config = self.config_manager.get_session_config()
            storage_paths = self.config_manager.get_storage_paths()
            
            # Create storage directories
            for path in storage_paths.values():
                path.mkdir(parents=True, exist_ok=True)
            
            # Initialize core components
            self.gemini_client = GeminiClient(
                api_key=system_config.gemini_api_key,
                model=system_config.gemini_model
            )
            
            self.context_manager = ContextManager(
                max_tokens=system_config.max_tokens
            )
            
            self.memory_system = MemorySystem(
                storage_path=str(storage_paths["memory"])
            )
            
            self.search_integration = SearchIntegration(
                enable_search=system_config.enable_search
            )
            
            self.scenario_loader = ScenarioLoader()
            
            self.character_system = CharacterSystem(
                storage_path=str(storage_paths["characters"])
            )
            
            self.personality_engine = PersonalityEngine()
            
            self.world_state = WorldState(
                storage_path=str(storage_paths["world"])
            )
            
            self.event_system = EventSystem()
            
            # Test Gemini connection
            if not self.gemini_client.is_healthy():
                self._print("Warning: Gemini API connection test failed", "yellow")
            
            self._print("System initialized successfully!", "green")
            return True
            
        except Exception as e:
            self._print(f"Failed to initialize system: {e}", "red")
            self.logger.error(f"System initialization failed: {e}")
            return False
    
    def load_scenario(self, scenario_type: str) -> bool:
        """Load a scenario.
        
        Args:
            scenario_type: Type of scenario to load
            
        Returns:
            True if successful
        """
        try:
            self._print(f"Loading scenario: {scenario_type}", "blue")
            
            # Load scenario
            self.current_scenario = self.scenario_loader.load_scenario(scenario_type)
            
            # Update session config
            session_config = self.config_manager.get_session_config()
            session_config.scenario_type = scenario_type
            
            # Load characters from scenario
            for char_name, char_data in self.current_scenario.config.characters.items():
                self.character_system.create_character(
                    name=char_name,
                    description=char_data.get("description", ""),
                    personality=char_data.get("personality", ""),
                    background=char_data.get("background", ""),
                    abilities=char_data.get("abilities", {}),
                    equipment=char_data.get("equipment", []),
                    current_goals=char_data.get("goals", [])
                )
            
            # Set active characters
            active_chars = list(self.current_scenario.config.characters.keys())
            self.character_system.set_active_characters(active_chars)
            session_config.active_characters = active_chars
            
            # Load world rules
            for rule in self.current_scenario.config.world_rules:
                self.world_state.set_world_rule(rule)
            
            # Set current scene
            if self.current_scenario.config.current_scene:
                self.world_state.set_world_property("current_scene", self.current_scenario.config.current_scene)
            
            # Create scenario-specific events
            self.event_system.create_random_events(scenario_type)
            
            self._print(f"Scenario '{self.current_scenario.config.name}' loaded successfully!", "green")
            return True
            
        except Exception as e:
            self._print(f"Failed to load scenario: {e}", "red")
            self.logger.error(f"Scenario loading failed: {e}")
            return False
    
    def start_conversation(self) -> None:
        """Start the main conversation loop."""
        if not self.current_scenario:
            self._print("No scenario loaded! Use 'load <scenario>' first.", "red")
            return
        
        self._print_panel(
            f"Starting conversation in scenario: {self.current_scenario.config.name}\n"
            f"Description: {self.current_scenario.config.description}\n\n"
            f"Type your message to begin. Use '/help' for commands.",
            "RP Session Started",
            "green"
        )
        
        self.running = True
        
        while self.running:
            try:
                # Get user input
                user_input = self._prompt("\n[bold cyan]You[/bold cyan]" if RICH_AVAILABLE else "You")
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    self._handle_command(user_input[1:])
                    continue
                
                # Process user message
                response = self._process_user_message(user_input)
                
                if response:
                    self._print_panel(response, "AI Response", "blue")
                
                # Check for events
                self._check_and_trigger_events()
                
            except KeyboardInterrupt:
                self._print("\nSession interrupted by user.", "yellow")
                break
            except Exception as e:
                self._print(f"Error during conversation: {e}", "red")
                self.logger.error(f"Conversation error: {e}")
    
    def _process_user_message(self, message: str) -> str:
        """Process a user message and generate AI response.
        
        Args:
            message: User message
            
        Returns:
            AI response
        """
        try:
            # Add user message to context
            message_tokens = self.gemini_client.count_tokens(message)
            self.context_manager.add_message(
                content=f"User: {message}",
                tokens=message_tokens,
                message_type="user_input"
            )
            
            # Add to memory
            self.memory_system.add_memory(
                content=f"User said: {message}",
                importance=0.5
            )
            
            # Check if search is needed
            active_chars = [char.name for char in self.character_system.get_active_characters()]
            
            if self.search_integration.should_search(message, "", active_chars):
                search_results = self.search_integration.search(message, max_results=2)
                if search_results:
                    search_info = self.search_integration.format_search_results(search_results)
                    search_tokens = self.gemini_client.count_tokens(search_info)
                    self.context_manager.add_message(
                        content=search_info,
                        tokens=search_tokens,
                        message_type="search_results",
                        importance=0.7
                    )
            
            # Build context
            system_prompt = self.current_scenario.build_context_prompt()
            full_context = self.context_manager.build_context(system_prompt)
            
            # Generate response
            session_config = self.config_manager.get_session_config()
            
            response = self.gemini_client.generate_response(
                prompt=full_context,
                temperature=session_config.response_temperature,
                top_p=session_config.response_top_p,
                max_tokens=session_config.max_response_tokens
            )
            
            # Add AI response to context
            ai_tokens = response.usage.get("completion_tokens", len(response.text) // 4)
            self.context_manager.add_message(
                content=f"AI: {response.text}",
                tokens=ai_tokens,
                message_type="ai_response",
                importance=0.6
            )
            
            # Add to memory
            self.memory_system.add_memory(
                content=f"AI responded: {response.text}",
                characters=self.config_manager.get_session_config().active_characters,
                importance=0.6
            )
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"I apologize, but I encountered an error processing your message: {e}"
    
    def _check_and_trigger_events(self) -> None:
        """Check for and trigger any applicable events."""
        try:
            # Build event context
            context = {
                "current_time": self.world_state.world_time,
                "current_location": self.world_state.current_location,
                "characters_present": set(self.config_manager.get_session_config().active_characters),
                "relationships": {},  # Would populate from character system
                "world_facts": self.world_state.world_facts,
                "event_start_time": self.world_state.world_time
            }
            
            # Check for triggered events
            triggered_events = self.event_system.check_events(context)
            
            # Process triggered events
            for event_id in triggered_events:
                outcomes = self.event_system.trigger_event(event_id, context)
                
                if outcomes:
                    self._print_panel(
                        "\n".join(outcomes),
                        "Event Triggered",
                        "yellow"
                    )
            
        except Exception as e:
            self.logger.error(f"Error checking events: {e}")
    
    def _handle_command(self, command: str) -> None:
        """Handle slash commands.
        
        Args:
            command: Command string (without the /)
        """
        parts = command.split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == "help":
            self._show_help()
        elif cmd == "quit" or cmd == "exit":
            self.running = False
        elif cmd == "status":
            self._show_status()
        elif cmd == "characters":
            self._show_characters()
        elif cmd == "world":
            self._show_world()
        elif cmd == "memory":
            self._show_memory()
        elif cmd == "config":
            self._show_config()
        elif cmd == "save":
            self._save_session(args[0] if args else "default")
        elif cmd == "load":
            if args:
                self._load_session(args[0])
            else:
                self._print("Usage: /load <session_name>", "red")
        elif cmd == "scenario":
            if args:
                self.load_scenario(args[0])
            else:
                self._show_available_scenarios()
        else:
            self._print(f"Unknown command: {cmd}. Type '/help' for available commands.", "red")
    
    def _show_help(self) -> None:
        """Show help information."""
        help_text = """
Available Commands:
  /help                 - Show this help message
  /quit, /exit         - End the session
  /status              - Show system status
  /characters          - Show character information
  /world               - Show world state
  /memory              - Show memory statistics
  /config              - Show configuration
  /save <name>         - Save current session
  /load <name>         - Load a saved session
  /scenario [type]     - Load scenario or show available scenarios

During conversation:
  - Type normally to interact with the AI
  - The AI will respond as characters and the world
  - Use descriptive actions in your messages
  - The system automatically manages context and memory
        """
        self._print_panel(help_text.strip(), "Help", "cyan")
    
    def _show_status(self) -> None:
        """Show system status."""
        uptime = time.time() - self.session_start_time
        uptime_str = f"{uptime//3600:.0f}h {(uptime%3600)//60:.0f}m {uptime%60:.0f}s"
        
        context_stats = self.context_manager.get_stats()
        memory_stats = self.memory_system.get_stats()
        char_stats = self.character_system.get_stats()
        world_stats = self.world_state.get_stats()
        
        status_text = f"""
Uptime: {uptime_str}
Scenario: {self.current_scenario.config.name if self.current_scenario else "None"}

Context: {context_stats['total_tokens']:,}/{context_stats['max_tokens']:,} tokens ({context_stats['utilization']:.1%})
Memory: {memory_stats['total_memories']} memories
Characters: {char_stats['total_characters']} total, {char_stats['active_characters']} active
World: {world_stats['locations']} locations, {world_stats['active_events']} active events
        """
        self._print_panel(status_text.strip(), "System Status", "blue")
    
    def _show_characters(self) -> None:
        """Show character information."""
        active_chars = self.character_system.get_active_characters()
        
        if not active_chars:
            self._print("No active characters.", "yellow")
            return
        
        for character in active_chars:
            char_sheet = self.character_system.get_character_sheet(character.name)
            self._print_panel(char_sheet, f"Character: {character.name}", "green")
    
    def _show_world(self) -> None:
        """Show world state."""
        world_summary = self.world_state.get_world_summary()
        self._print_panel(world_summary, "World State", "blue")
    
    def _show_memory(self) -> None:
        """Show memory statistics."""
        memory_stats = self.memory_system.get_stats()
        
        memory_text = f"""
Total Memories: {memory_stats['total_memories']}
Recent: {memory_stats['recent_memories']}
Important: {memory_stats['important_memories']}
Summaries: {memory_stats['summaries']}
Characters: {memory_stats['characters']}

Storage: {memory_stats['storage_path']}
        """
        self._print_panel(memory_text.strip(), "Memory System", "magenta")
    
    def _show_config(self) -> None:
        """Show configuration summary."""
        config_summary = self.config_manager.get_config_summary()
        self._print_panel(config_summary, "Configuration", "cyan")
    
    def _show_available_scenarios(self) -> None:
        """Show available scenarios."""
        scenarios = self.scenario_loader.list_available_scenarios()
        
        if RICH_AVAILABLE and self.console:
            table = Table(title="Available Scenarios")
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="white")
            
            for scenario_type in scenarios:
                info = self.scenario_loader.get_scenario_info(scenario_type)
                if info:
                    table.add_row(scenario_type, info.get("description", "No description"))
                else:
                    table.add_row(scenario_type, "Unknown scenario")
            
            self.console.print(table)
        else:
            self._print("Available scenarios:")
            for scenario_type in scenarios:
                self._print(f"  - {scenario_type}")
    
    def _save_session(self, session_name: str) -> None:
        """Save current session."""
        try:
            session_file = f"session_{session_name}.json"
            self.config_manager.save_session_to_file(session_file)
            self._print(f"Session saved as '{session_name}'", "green")
        except Exception as e:
            self._print(f"Failed to save session: {e}", "red")
    
    def _load_session(self, session_name: str) -> None:
        """Load a saved session."""
        try:
            session_file = f"session_{session_name}.json"
            self.config_manager.load_session_from_file(session_file)
            
            # Reload scenario if specified
            session_config = self.config_manager.get_session_config()
            if session_config.scenario_type:
                self.load_scenario(session_config.scenario_type)
            
            self._print(f"Session '{session_name}' loaded", "green")
        except Exception as e:
            self._print(f"Failed to load session: {e}", "red")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="RPG Roleplay System")
    parser.add_argument("--scenario", "-s", help="Scenario to load on startup")
    parser.add_argument("--config", "-c", help="Configuration file to load")
    parser.add_argument("--load", "-l", help="Session file to load")
    parser.add_argument("--no-init", action="store_true", help="Skip system initialization")
    
    args = parser.parse_args()
    
    # Create CLI interface
    cli = CLIInterface()
    
    # Load configuration if specified
    if args.config:
        try:
            cli.config_manager.load_session_from_file(args.config)
            print(f"Loaded configuration from {args.config}")
        except Exception as e:
            print(f"Failed to load config: {e}")
            return 1
    
    # Initialize system unless skipped
    if not args.no_init:
        if not cli.initialize_system():
            print("System initialization failed")
            return 1
    
    # Load session if specified
    if args.load:
        cli._load_session(args.load)
    
    # Load scenario if specified
    if args.scenario:
        if not cli.load_scenario(args.scenario):
            print(f"Failed to load scenario: {args.scenario}")
            return 1
    
    # Start conversation
    try:
        cli.start_conversation()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())