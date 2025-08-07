"""Interactive setup wizard for first-time configuration."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .config_manager import ConfigManager, SystemConfig


class SetupWizard:
    """Interactive setup wizard for configuring the RP system."""
    
    def __init__(self):
        """Initialize setup wizard."""
        self.console = Console() if RICH_AVAILABLE else None
        self.logger = logging.getLogger(__name__)
        
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
    
    def _prompt(self, message: str, default: str = "", password: bool = False) -> str:
        """Prompt user for input."""
        if RICH_AVAILABLE:
            return Prompt.ask(message, default=default, password=password)
        else:
            if password:
                import getpass
                response = getpass.getpass(f"{message}: ")
                return response if response else default
            else:
                response = input(f"{message} [{default}]: " if default else f"{message}: ")
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
    
    def run_setup(self, force: bool = False) -> bool:
        """Run the interactive setup process.
        
        Args:
            force: Force setup even if config already exists
            
        Returns:
            True if setup completed successfully
        """
        try:
            self._print_panel(
                "Welcome to the RPG System Setup Wizard!\n\n"
                "This wizard will help you configure your API keys and preferences.\n"
                "You can run this setup again anytime using: rp-system --setup",
                "🎭 RPG System Setup",
                "cyan"
            )
            
            # Check if config already exists
            config_manager = ConfigManager()
            config_exists = self._check_existing_config(config_manager)
            
            if config_exists and not force:
                if not self._confirm("Configuration already exists. Do you want to reconfigure?", False):
                    self._print("Setup cancelled. Your existing configuration is unchanged.", "yellow")
                    return True
            
            # API Key Configuration
            if not self._setup_api_key(config_manager):
                return False
            
            # System Preferences
            if not self._setup_preferences(config_manager):
                return False
            
            # Test Configuration
            if not self._test_configuration(config_manager):
                self._print("Configuration saved, but API test failed. You can test manually later.", "yellow")
            
            self._print_panel(
                "🎉 Setup completed successfully!\n\n"
                "You can now start using the RP system:\n"
                "• rp-system --scenario fantasy\n"
                "• rp-system --help\n\n"
                "To reconfigure later: rp-system --setup",
                "Setup Complete",
                "green"
            )
            
            return True
            
        except KeyboardInterrupt:
            self._print("\nSetup cancelled by user.", "yellow")
            return False
        except Exception as e:
            self._print(f"Setup failed: {e}", "red")
            self.logger.error(f"Setup wizard failed: {e}")
            return False
    
    def _check_existing_config(self, config_manager: ConfigManager) -> bool:
        """Check if configuration already exists."""
        try:
            config_file = config_manager.config_dir / "system_config.json"
            if config_file.exists():
                with open(config_file) as f:
                    config_data = json.load(f)
                    return bool(config_data.get("gemini_api_key"))
            return False
        except Exception:
            return False
    
    def _setup_api_key(self, config_manager: ConfigManager) -> bool:
        """Setup API key configuration."""
        self._print_panel(
            "API Key Configuration\n\n"
            "You need a Google Gemini API key to use this system.\n"
            "Get one at: https://ai.google.dev/\n\n"
            "Your API key will be stored securely in a local config file.",
            "Step 1: API Key",
            "blue"
        )
        
        # Check for existing API key
        current_key = config_manager.system_config.gemini_api_key
        if current_key:
            masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
            self._print(f"Current API key: {masked_key}", "cyan")
            
            if not self._confirm("Do you want to update your API key?", False):
                return True
        
        # Get new API key
        while True:
            api_key = self._prompt(
                "Enter your Gemini API key",
                password=True
            ).strip()
            
            if not api_key:
                if not self._confirm("API key is required. Continue without setting it?", False):
                    continue
                else:
                    self._print("You can set the API key later using --setup", "yellow")
                    return True
            
            # Basic validation
            if len(api_key) < 20:
                self._print("API key seems too short. Please check and try again.", "red")
                continue
            
            if not api_key.startswith("AI"):
                if not self._confirm("API key doesn't start with 'AI'. Continue anyway?", False):
                    continue
            
            # Save API key
            config_manager.update_system_config({"gemini_api_key": api_key})
            self._print("✓ API key saved successfully!", "green")
            return True
    
    def _setup_preferences(self, config_manager: ConfigManager) -> bool:
        """Setup system preferences."""
        self._print_panel(
            "System Preferences\n\n"
            "Configure optional settings for your experience.",
            "Step 2: Preferences",
            "blue"
        )
        
        updates = {}
        
        # Model selection
        current_model = config_manager.system_config.gemini_model
        self._print(f"Current model: {current_model}", "cyan")
        
        if self._confirm("Do you want to change the AI model?", False):
            model_options = [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ]
            
            self._print("Available models:")
            for i, model in enumerate(model_options, 1):
                self._print(f"  {i}. {model}")
            
            while True:
                choice = self._prompt("Select model (1-3)", "1")
                try:
                    model_idx = int(choice) - 1
                    if 0 <= model_idx < len(model_options):
                        updates["gemini_model"] = model_options[model_idx]
                        break
                    else:
                        self._print("Invalid choice. Please enter 1-3.", "red")
                except ValueError:
                    self._print("Invalid choice. Please enter a number.", "red")
        
        # Storage location
        current_storage = config_manager.system_config.storage_base_path
        self._print(f"Current storage path: {current_storage}", "cyan")
        
        if self._confirm("Do you want to change the storage location?", False):
            new_path = self._prompt("Enter storage path", current_storage)
            if new_path and new_path != current_storage:
                # Validate path
                try:
                    storage_path = Path(new_path)
                    storage_path.mkdir(parents=True, exist_ok=True)
                    updates["storage_base_path"] = str(storage_path)
                    self._print(f"✓ Storage path set to: {storage_path}", "green")
                except Exception as e:
                    self._print(f"Invalid storage path: {e}", "red")
        
        # Search integration
        current_search = config_manager.system_config.enable_search
        self._print(f"Web search enabled: {current_search}", "cyan")
        
        if self._confirm("Do you want to change search settings?", False):
            enable_search = self._confirm("Enable web search for character lore and facts?", current_search)
            updates["enable_search"] = enable_search
        
        # Apply updates
        if updates:
            config_manager.update_system_config(updates)
            self._print("✓ Preferences saved!", "green")
        
        return True
    
    def _test_configuration(self, config_manager: ConfigManager) -> bool:
        """Test the configuration."""
        if not config_manager.system_config.gemini_api_key:
            self._print("⚠ Skipping API test (no API key configured)", "yellow")
            return False
        
        self._print("Testing API connection...", "blue")
        
        try:
            from ..core.gemini_client import GeminiClient
            
            client = GeminiClient(
                api_key=config_manager.system_config.gemini_api_key,
                model=config_manager.system_config.gemini_model
            )
            
            if client.is_healthy():
                self._print("✓ API connection test passed!", "green")
                return True
            else:
                self._print("✗ API connection test failed", "red")
                return False
                
        except Exception as e:
            self._print(f"✗ API test failed: {e}", "red")
            return False
    
    def quick_setup(self, api_key: str) -> bool:
        """Quick setup with just an API key.
        
        Args:
            api_key: The API key to configure
            
        Returns:
            True if setup completed successfully
        """
        try:
            config_manager = ConfigManager()
            config_manager.update_system_config({"gemini_api_key": api_key})
            
            self._print("API key saved to configuration file.", "green")
            
            # Test the API key (with timeout)
            try:
                self._print("Testing API key...", "blue")
                from ..core.gemini_client import GeminiClient
                client = GeminiClient(api_key=api_key)
                
                if client.is_healthy():
                    self._print("✓ API key test successful!", "green")
                else:
                    self._print("⚠ API key saved but test failed - please verify your key", "yellow")
                    
            except Exception as e:
                self._print(f"⚠ API key saved but test failed: {e}", "yellow")
                self._print("You can test manually with: rp-system --scenario fantasy", "cyan")
            
            return True
                
        except Exception as e:
            self._print(f"Quick setup failed: {e}", "red")
            return False


def get_config_file_path() -> Path:
    """Get the path to the main config file."""
    return Path("rp_config") / "system_config.json"


def create_example_config() -> Dict[str, Any]:
    """Create an example configuration dictionary."""
    return {
        "gemini_api_key": "YOUR_API_KEY_HERE",
        "gemini_model": "gemini-2.0-flash-exp",
        "max_tokens": 950000,
        "enable_search": True,
        "storage_base_path": "rp_data",
        "log_level": "INFO"
    }


def save_example_config(filepath: Optional[str] = None) -> str:
    """Save an example configuration file.
    
    Args:
        filepath: Optional path to save config file
        
    Returns:
        Path where config was saved
    """
    if filepath is None:
        filepath = "rp_config_example.json"
    
    config_path = Path(filepath)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    example_config = create_example_config()
    
    with open(config_path, 'w') as f:
        json.dump(example_config, f, indent=2)
    
    return str(config_path)