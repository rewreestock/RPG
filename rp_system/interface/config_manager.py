"""Configuration management for runtime customization."""

import logging
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
import os


@dataclass
class SystemConfig:
    """System-wide configuration."""
    # API Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash-exp"
    max_tokens: int = 950000
    
    # Context Management
    recent_token_reserve: int = 30000
    character_token_reserve: int = 20000
    world_token_reserve: int = 15000
    
    # Memory System
    max_recent_memories: int = 100
    max_important_memories: int = 50
    max_character_memories: int = 30
    memory_compression_days: int = 7
    
    # Search Integration
    enable_search: bool = True
    search_cache_hours: int = 1
    min_search_interval: float = 2.0
    
    # Interface
    response_delay: float = 0.5
    auto_save_interval: int = 300  # seconds
    log_level: str = "INFO"
    
    # Paths
    storage_base_path: str = "rp_data"
    log_file_path: str = "rp_system.log"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class SessionConfig:
    """Per-session configuration."""
    # Current scenario
    scenario_type: str = "fantasy"
    scenario_config: Dict[str, Any] = None
    
    # Active characters
    active_characters: List[str] = None
    protagonist: Optional[str] = None
    
    # Current state
    current_location: str = ""
    session_name: str = ""
    
    # AI behavior
    response_temperature: float = 0.7
    response_top_p: float = 0.95
    max_response_tokens: int = 800
    
    # Roleplay settings
    nsfw_level: int = 0
    response_length: str = "medium"
    narrative_focus: str = "balanced"
    tone: str = "balanced"
    
    def __post_init__(self):
        if self.scenario_config is None:
            self.scenario_config = {}
        if self.active_characters is None:
            self.active_characters = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class ConfigManager:
    """Manages system and session configuration."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path("rp_config")
        self.config_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Configuration objects
        self.system_config = SystemConfig()
        self.session_config = SessionConfig()
        
        # Load existing configurations
        self._load_system_config()
        self._load_session_config()
        
        # Apply environment variables
        self._apply_env_vars()
        
        self.logger.info(f"Initialized config manager at {self.config_dir}")
    
    def _apply_env_vars(self) -> None:
        """Apply environment variable overrides."""
        # API key from environment
        if os.getenv("GEMINI_API_KEY"):
            self.system_config.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Model override
        if os.getenv("GEMINI_MODEL"):
            self.system_config.gemini_model = os.getenv("GEMINI_MODEL")
        
        # Log level override
        if os.getenv("LOG_LEVEL"):
            self.system_config.log_level = os.getenv("LOG_LEVEL")
        
        # Storage path override
        if os.getenv("RP_STORAGE_PATH"):
            self.system_config.storage_base_path = os.getenv("RP_STORAGE_PATH")
    
    def get_system_config(self) -> SystemConfig:
        """Get current system configuration.
        
        Returns:
            System configuration
        """
        return self.system_config
    
    def get_session_config(self) -> SessionConfig:
        """Get current session configuration.
        
        Returns:
            Session configuration
        """
        return self.session_config
    
    def update_system_config(self, updates: Dict[str, Any]) -> None:
        """Update system configuration.
        
        Args:
            updates: Configuration updates
        """
        for key, value in updates.items():
            if hasattr(self.system_config, key):
                setattr(self.system_config, key, value)
                self.logger.debug(f"Updated system config {key}: {value}")
        
        self._save_system_config()
    
    def update_session_config(self, updates: Dict[str, Any]) -> None:
        """Update session configuration.
        
        Args:
            updates: Configuration updates
        """
        for key, value in updates.items():
            if hasattr(self.session_config, key):
                setattr(self.session_config, key, value)
                self.logger.debug(f"Updated session config {key}: {value}")
        
        self._save_session_config()
    
    def reset_system_config(self) -> None:
        """Reset system configuration to defaults."""
        self.system_config = SystemConfig()
        self._apply_env_vars()
        self._save_system_config()
        self.logger.info("Reset system configuration to defaults")
    
    def reset_session_config(self) -> None:
        """Reset session configuration to defaults."""
        self.session_config = SessionConfig()
        self._save_session_config()
        self.logger.info("Reset session configuration to defaults")
    
    def load_session_from_file(self, filepath: str) -> None:
        """Load session configuration from file.
        
        Args:
            filepath: Path to session file
        """
        try:
            path = Path(filepath)
            
            if path.suffix.lower() in ['.yaml', '.yml']:
                with open(path) as f:
                    session_data = yaml.safe_load(f)
            else:
                with open(path) as f:
                    session_data = json.load(f)
            
            self.session_config = SessionConfig.from_dict(session_data)
            self.logger.info(f"Loaded session config from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to load session config from {filepath}: {e}")
            raise
    
    def save_session_to_file(self, filepath: str) -> None:
        """Save session configuration to file.
        
        Args:
            filepath: Path to save session file
        """
        try:
            path = Path(filepath)
            session_data = self.session_config.to_dict()
            
            if path.suffix.lower() in ['.yaml', '.yml']:
                with open(path, 'w') as f:
                    yaml.dump(session_data, f, default_flow_style=False, indent=2)
            else:
                with open(path, 'w') as f:
                    json.dump(session_data, f, indent=2)
            
            self.logger.info(f"Saved session config to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save session config to {filepath}: {e}")
            raise
    
    def get_storage_paths(self) -> Dict[str, Path]:
        """Get storage paths for different components.
        
        Returns:
            Dictionary of component storage paths
        """
        base_path = Path(self.system_config.storage_base_path)
        
        return {
            "base": base_path,
            "memory": base_path / "memory",
            "characters": base_path / "characters",
            "world": base_path / "world",
            "sessions": base_path / "sessions"
        }
    
    def create_session_preset(
        self,
        preset_name: str,
        description: str = "",
        scenario_type: str = "fantasy"
    ) -> None:
        """Create a session preset.
        
        Args:
            preset_name: Name for the preset
            description: Preset description
            scenario_type: Type of scenario
        """
        preset_data = {
            "name": preset_name,
            "description": description,
            "scenario_type": scenario_type,
            "config": self.session_config.to_dict()
        }
        
        preset_file = self.config_dir / "presets" / f"{preset_name}.json"
        preset_file.parent.mkdir(exist_ok=True)
        
        with open(preset_file, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        self.logger.info(f"Created session preset: {preset_name}")
    
    def list_session_presets(self) -> List[Dict[str, str]]:
        """List available session presets.
        
        Returns:
            List of preset information
        """
        presets = []
        preset_dir = self.config_dir / "presets"
        
        if not preset_dir.exists():
            return presets
        
        for preset_file in preset_dir.glob("*.json"):
            try:
                with open(preset_file) as f:
                    preset_data = json.load(f)
                
                presets.append({
                    "name": preset_data.get("name", preset_file.stem),
                    "description": preset_data.get("description", ""),
                    "scenario_type": preset_data.get("scenario_type", "unknown"),
                    "file": str(preset_file)
                })
                
            except Exception as e:
                self.logger.warning(f"Failed to load preset {preset_file}: {e}")
        
        return presets
    
    def load_session_preset(self, preset_name: str) -> None:
        """Load a session preset.
        
        Args:
            preset_name: Name of preset to load
        """
        preset_file = self.config_dir / "presets" / f"{preset_name}.json"
        
        if not preset_file.exists():
            raise FileNotFoundError(f"Session preset '{preset_name}' not found")
        
        try:
            with open(preset_file) as f:
                preset_data = json.load(f)
            
            config_data = preset_data.get("config", {})
            self.session_config = SessionConfig.from_dict(config_data)
            
            self.logger.info(f"Loaded session preset: {preset_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to load session preset {preset_name}: {e}")
            raise
    
    def get_config_summary(self) -> str:
        """Get a summary of current configuration.
        
        Returns:
            Configuration summary text
        """
        summary_parts = ["=== CONFIGURATION SUMMARY ==="]
        
        # System config highlights
        summary_parts.append(f"Model: {self.system_config.gemini_model}")
        summary_parts.append(f"Max Tokens: {self.system_config.max_tokens:,}")
        summary_parts.append(f"Search Enabled: {self.system_config.enable_search}")
        summary_parts.append(f"Log Level: {self.system_config.log_level}")
        
        # Session config highlights
        summary_parts.append(f"\nSession: {self.session_config.session_name or 'Unnamed'}")
        summary_parts.append(f"Scenario: {self.session_config.scenario_type}")
        summary_parts.append(f"Response Length: {self.session_config.response_length}")
        summary_parts.append(f"Tone: {self.session_config.tone}")
        summary_parts.append(f"NSFW Level: {self.session_config.nsfw_level}")
        
        if self.session_config.active_characters:
            summary_parts.append(f"Active Characters: {', '.join(self.session_config.active_characters)}")
        
        if self.session_config.current_location:
            summary_parts.append(f"Current Location: {self.session_config.current_location}")
        
        # Storage paths
        storage_paths = self.get_storage_paths()
        summary_parts.append(f"\nStorage Path: {storage_paths['base']}")
        
        return "\n".join(summary_parts)
    
    def validate_config(self) -> List[str]:
        """Validate current configuration and return any issues.
        
        Returns:
            List of validation issues
        """
        issues = []
        
        # System config validation
        if not self.system_config.gemini_api_key:
            issues.append("Gemini API key not set")
        
        if self.system_config.max_tokens <= 0:
            issues.append("Max tokens must be positive")
        
        if self.system_config.recent_token_reserve >= self.system_config.max_tokens:
            issues.append("Recent token reserve is too large")
        
        # Session config validation
        if self.session_config.response_temperature < 0 or self.session_config.response_temperature > 2:
            issues.append("Response temperature should be between 0 and 2")
        
        if self.session_config.response_top_p < 0 or self.session_config.response_top_p > 1:
            issues.append("Response top_p should be between 0 and 1")
        
        if self.session_config.nsfw_level < 0 or self.session_config.nsfw_level > 3:
            issues.append("NSFW level should be between 0 and 3")
        
        # Path validation
        try:
            storage_paths = self.get_storage_paths()
            base_path = storage_paths["base"]
            if not base_path.parent.exists():
                issues.append(f"Storage base directory parent does not exist: {base_path.parent}")
        except Exception as e:
            issues.append(f"Storage path configuration error: {e}")
        
        return issues
    
    def _load_system_config(self) -> None:
        """Load system configuration from file."""
        config_file = self.config_dir / "system_config.json"
        
        if not config_file.exists():
            return
        
        try:
            with open(config_file) as f:
                config_data = json.load(f)
            
            self.system_config = SystemConfig.from_dict(config_data)
            self.logger.debug("Loaded system configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to load system config: {e}")
    
    def _save_system_config(self) -> None:
        """Save system configuration to file."""
        config_file = self.config_dir / "system_config.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.system_config.to_dict(), f, indent=2)
            
            self.logger.debug("Saved system configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to save system config: {e}")
    
    def _load_session_config(self) -> None:
        """Load session configuration from file."""
        config_file = self.config_dir / "session_config.json"
        
        if not config_file.exists():
            return
        
        try:
            with open(config_file) as f:
                config_data = json.load(f)
            
            self.session_config = SessionConfig.from_dict(config_data)
            self.logger.debug("Loaded session configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to load session config: {e}")
    
    def _save_session_config(self) -> None:
        """Save session configuration to file."""
        config_file = self.config_dir / "session_config.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.session_config.to_dict(), f, indent=2)
            
            self.logger.debug("Saved session configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to save session config: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get configuration manager statistics.
        
        Returns:
            Statistics dictionary
        """
        presets = self.list_session_presets()
        validation_issues = self.validate_config()
        
        return {
            "config_dir": str(self.config_dir),
            "system_config_valid": len([i for i in validation_issues if "system" in i.lower()]) == 0,
            "session_config_valid": len([i for i in validation_issues if "session" in i.lower()]) == 0,
            "available_presets": len(presets),
            "validation_issues": len(validation_issues),
            "api_key_set": bool(self.system_config.gemini_api_key)
        }