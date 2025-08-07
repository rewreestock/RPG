"""Dynamic scenario loading and management."""

import logging
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
import importlib
import pkgutil

from .base_scenario import BaseScenario, ScenarioConfig


class GenericScenario(BaseScenario):
    """Generic scenario implementation for custom configs."""
    
    def get_system_prompt(self) -> str:
        """Generate system prompt for generic scenario."""
        prompt_parts = [
            f"You are an AI assistant running a {self.config.setting} roleplay scenario called '{self.config.name}'.",
            f"{self.config.description}",
            "",
            "CORE INSTRUCTIONS:",
            "- Stay in character and maintain narrative consistency",
            "- Respond as the world, NPCs, and environment (not as the user's character)",
            "- Drive the story forward while respecting player agency", 
            "- Use vivid, immersive descriptions",
            "- Maintain established character personalities and relationships",
            "- Follow the world rules and setting constraints",
            f"- Narrative focus: {self.config.narrative_focus}",
            f"- Danger level: {self.config.danger_level:.1f}/1.0"
        ]
        
        if self.config.world_rules:
            prompt_parts.append("\nWORLD RULES:")
            prompt_parts.extend(f"- {rule}" for rule in self.config.world_rules)
        
        if self.config.plot_hooks:
            prompt_parts.append("\nPLOT HOOKS:")
            prompt_parts.extend(f"- {hook}" for hook in self.config.plot_hooks)
        
        if self.config.ai_personality_traits:
            prompt_parts.append("\nAI PERSONALITY:")
            prompt_parts.extend(f"- {trait}" for trait in self.config.ai_personality_traits)
        
        return "\n".join(prompt_parts)
    
    def get_character_sheet(self, character_name: str) -> Optional[str]:
        """Get character sheet for the character."""
        character_data = self.config.characters.get(character_name)
        if not character_data:
            return None
        
        sheet_parts = [f"CHARACTER: {character_name}"]
        
        # Basic info
        if 'description' in character_data:
            sheet_parts.append(f"Description: {character_data['description']}")
        
        if 'personality' in character_data:
            sheet_parts.append(f"Personality: {character_data['personality']}")
        
        if 'background' in character_data:
            sheet_parts.append(f"Background: {character_data['background']}")
        
        # Abilities/Stats
        if 'abilities' in character_data:
            abilities = character_data['abilities']
            if isinstance(abilities, dict):
                abilities_text = ", ".join(f"{k}: {v}" for k, v in abilities.items())
            else:
                abilities_text = str(abilities)
            sheet_parts.append(f"Abilities: {abilities_text}")
        
        # Equipment
        if 'equipment' in character_data:
            equipment = character_data['equipment']
            if isinstance(equipment, list):
                equipment_text = ", ".join(equipment)
            else:
                equipment_text = str(equipment)
            sheet_parts.append(f"Equipment: {equipment_text}")
        
        # Goals
        if 'goals' in character_data:
            goals = character_data['goals']
            if isinstance(goals, list):
                goals_text = "; ".join(goals)
            else:
                goals_text = str(goals)
            sheet_parts.append(f"Goals: {goals_text}")
        
        # Relationships
        if 'relationships' in character_data:
            relationships = character_data['relationships']
            if isinstance(relationships, dict):
                rel_text = "; ".join(f"{k}: {v}" for k, v in relationships.items())
                sheet_parts.append(f"Relationships: {rel_text}")
        
        # Additional custom fields
        for key, value in character_data.items():
            if key not in ['description', 'personality', 'background', 'abilities', 'equipment', 'goals', 'relationships']:
                sheet_parts.append(f"{key.title()}: {value}")
        
        return "\n".join(sheet_parts)
    
    def get_world_state(self) -> str:
        """Get current world state."""
        state_parts = [f"WORLD: {self.config.name}"]
        state_parts.append(f"Setting: {self.config.setting}")
        
        if self.config.current_scene:
            state_parts.append(f"Current Scene: {self.config.current_scene}")
        
        if self.config.world_rules:
            state_parts.append("World Rules:")
            state_parts.extend(f"- {rule}" for rule in self.config.world_rules)
        
        return "\n".join(state_parts)


class ScenarioLoader:
    """Load and manage different RP scenarios."""
    
    def __init__(self, presets_path: Optional[str] = None):
        """Initialize scenario loader.
        
        Args:
            presets_path: Path to scenario presets directory
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up presets path
        if presets_path:
            self.presets_path = Path(presets_path)
        else:
            # Default to package presets
            self.presets_path = Path(__file__).parent / "presets"
        
        self.presets_path.mkdir(exist_ok=True)
        
        # Registry of scenario classes
        self.scenario_classes: Dict[str, Type[BaseScenario]] = {
            'generic': GenericScenario
        }
        
        # Load built-in scenario classes
        self._load_scenario_classes()
        
        self.logger.info(f"Initialized scenario loader with presets at {self.presets_path}")
    
    def _load_scenario_classes(self) -> None:
        """Load built-in scenario classes."""
        try:
            # Try to import preset scenario modules
            preset_modules = [
                'rezero_scenario',
                'fantasy_scenario', 
                'modern_scenario',
                'scifi_scenario',
                'historical_scenario'
            ]
            
            for module_name in preset_modules:
                try:
                    module = importlib.import_module(f'.presets.{module_name}', package='rp_system.scenarios')
                    
                    # Look for scenario classes in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseScenario) and 
                            attr != BaseScenario):
                            
                            scenario_key = module_name.replace('_scenario', '')
                            self.scenario_classes[scenario_key] = attr
                            self.logger.debug(f"Loaded scenario class: {scenario_key}")
                
                except ImportError:
                    # Module doesn't exist yet, that's fine
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Error loading scenario classes: {e}")
    
    def list_available_scenarios(self) -> List[str]:
        """List all available scenario types.
        
        Returns:
            List of scenario type names
        """
        available = list(self.scenario_classes.keys())
        
        # Also check for config files in presets directory
        for config_file in self.presets_path.glob("*.json"):
            name = config_file.stem
            if name not in available:
                available.append(name)
        
        for config_file in self.presets_path.glob("*.yaml"):
            name = config_file.stem
            if name not in available:
                available.append(name)
        
        return sorted(available)
    
    def load_scenario(
        self,
        scenario_type: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> BaseScenario:
        """Load a scenario by type.
        
        Args:
            scenario_type: Type of scenario to load
            custom_config: Optional custom configuration overrides
            
        Returns:
            Loaded scenario instance
            
        Raises:
            ValueError: If scenario type is not found
        """
        # Try to load from scenario classes first
        if scenario_type in self.scenario_classes:
            scenario_class = self.scenario_classes[scenario_type]
            
            # Try to load default config for this scenario type
            config_file = self.presets_path / f"{scenario_type}.json"
            if not config_file.exists():
                config_file = self.presets_path / f"{scenario_type}.yaml"
            
            if config_file.exists():
                config = self._load_config_file(config_file)
            else:
                # Create minimal default config
                config = ScenarioConfig(
                    name=scenario_type.title(),
                    description=f"A {scenario_type} roleplay scenario",
                    setting=scenario_type
                )
            
            # Apply custom overrides
            if custom_config:
                config_dict = config.to_dict()
                config_dict.update(custom_config)
                config = ScenarioConfig.from_dict(config_dict)
            
            return scenario_class(config)
        
        # Try to load from config file
        config_file = self.presets_path / f"{scenario_type}.json"
        if not config_file.exists():
            config_file = self.presets_path / f"{scenario_type}.yaml"
        
        if config_file.exists():
            config = self._load_config_file(config_file)
            
            # Apply custom overrides
            if custom_config:
                config_dict = config.to_dict()
                config_dict.update(custom_config)
                config = ScenarioConfig.from_dict(config_dict)
            
            return GenericScenario(config)
        
        raise ValueError(f"Scenario type '{scenario_type}' not found")
    
    def _load_config_file(self, filepath: Path) -> ScenarioConfig:
        """Load scenario config from file.
        
        Args:
            filepath: Path to config file
            
        Returns:
            Scenario configuration
        """
        if filepath.suffix in ['.yaml', '.yml']:
            with open(filepath) as f:
                config_dict = yaml.safe_load(f)
        else:
            with open(filepath) as f:
                config_dict = json.load(f)
        
        return ScenarioConfig.from_dict(config_dict)
    
    def create_custom_scenario(
        self,
        name: str,
        description: str,
        setting: str = "fantasy",
        **kwargs
    ) -> BaseScenario:
        """Create a custom scenario.
        
        Args:
            name: Scenario name
            description: Scenario description
            setting: Setting type
            **kwargs: Additional configuration options
            
        Returns:
            Custom scenario instance
        """
        config_dict = {
            "name": name,
            "description": description,
            "setting": setting,
            **kwargs
        }
        
        config = ScenarioConfig.from_dict(config_dict)
        return GenericScenario(config)
    
    def save_scenario_preset(
        self,
        scenario: BaseScenario,
        preset_name: str,
        format: str = "yaml"
    ) -> None:
        """Save a scenario as a preset.
        
        Args:
            scenario: Scenario to save
            preset_name: Name for the preset
            format: File format ('json' or 'yaml')
        """
        if format == "yaml":
            filepath = self.presets_path / f"{preset_name}.yaml"
        else:
            filepath = self.presets_path / f"{preset_name}.json"
        
        scenario.save_to_file(str(filepath))
        self.logger.info(f"Saved scenario preset: {filepath}")
    
    def register_scenario_class(
        self,
        scenario_type: str,
        scenario_class: Type[BaseScenario]
    ) -> None:
        """Register a custom scenario class.
        
        Args:
            scenario_type: Type identifier
            scenario_class: Scenario class
        """
        self.scenario_classes[scenario_type] = scenario_class
        self.logger.info(f"Registered scenario class: {scenario_type}")
    
    def get_scenario_info(self, scenario_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a scenario type.
        
        Args:
            scenario_type: Scenario type to get info for
            
        Returns:
            Scenario information or None if not found
        """
        try:
            scenario = self.load_scenario(scenario_type)
            return {
                "name": scenario.config.name,
                "description": scenario.config.description,
                "setting": scenario.config.setting,
                "danger_level": scenario.config.danger_level,
                "narrative_focus": scenario.config.narrative_focus,
                "tone": scenario.config.tone,
                "characters": list(scenario.config.characters.keys()),
                "plot_hooks": scenario.config.plot_hooks
            }
        except Exception as e:
            self.logger.error(f"Error getting scenario info for {scenario_type}: {e}")
            return None