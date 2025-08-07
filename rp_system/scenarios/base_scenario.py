"""Base scenario class and scenario configuration."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
import yaml


@dataclass
class ScenarioConfig:
    """Configuration for a roleplay scenario."""
    name: str
    description: str
    
    # World settings
    setting: str  # e.g., "fantasy", "modern", "sci-fi", "historical"
    world_rules: List[str] = field(default_factory=list)
    danger_level: float = 0.5  # 0.0 = safe, 1.0 = constant peril
    
    # Narrative settings
    narrative_focus: str = "balanced"  # "character", "plot", "world", "balanced"
    response_length: str = "medium"  # "brief", "medium", "detailed", "verbose"
    nsfw_level: int = 0  # 0 = none, 1 = mild, 2 = moderate, 3 = explicit
    
    # Character settings
    characters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    protagonist: Optional[str] = None
    
    # Plot settings
    plot_hooks: List[str] = field(default_factory=list)
    current_scene: str = ""
    objectives: List[str] = field(default_factory=list)
    
    # Tone and style
    tone: str = "balanced"  # "serious", "lighthearted", "dark", "comedic", "balanced"
    style_notes: List[str] = field(default_factory=list)
    
    # Memory and context
    important_facts: List[str] = field(default_factory=list)
    relationship_dynamics: Dict[str, str] = field(default_factory=dict)
    
    # Custom instructions
    system_prompt_additions: List[str] = field(default_factory=list)
    ai_personality_traits: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "setting": self.setting,
            "world_rules": self.world_rules,
            "danger_level": self.danger_level,
            "narrative_focus": self.narrative_focus,
            "response_length": self.response_length,
            "nsfw_level": self.nsfw_level,
            "characters": self.characters,
            "protagonist": self.protagonist,
            "plot_hooks": self.plot_hooks,
            "current_scene": self.current_scene,
            "objectives": self.objectives,
            "tone": self.tone,
            "style_notes": self.style_notes,
            "important_facts": self.important_facts,
            "relationship_dynamics": self.relationship_dynamics,
            "system_prompt_additions": self.system_prompt_additions,
            "ai_personality_traits": self.ai_personality_traits
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioConfig":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            setting=data.get("setting", "fantasy"),
            world_rules=data.get("world_rules", []),
            danger_level=data.get("danger_level", 0.5),
            narrative_focus=data.get("narrative_focus", "balanced"),
            response_length=data.get("response_length", "medium"),
            nsfw_level=data.get("nsfw_level", 0),
            characters=data.get("characters", {}),
            protagonist=data.get("protagonist"),
            plot_hooks=data.get("plot_hooks", []),
            current_scene=data.get("current_scene", ""),
            objectives=data.get("objectives", []),
            tone=data.get("tone", "balanced"),
            style_notes=data.get("style_notes", []),
            important_facts=data.get("important_facts", []),
            relationship_dynamics=data.get("relationship_dynamics", {}),
            system_prompt_additions=data.get("system_prompt_additions", []),
            ai_personality_traits=data.get("ai_personality_traits", [])
        )


class BaseScenario(ABC):
    """Abstract base class for all roleplay scenarios."""
    
    def __init__(self, config: ScenarioConfig):
        """Initialize scenario with configuration.
        
        Args:
            config: Scenario configuration
        """
        self.config = config
        self.active_characters = set()
        self.scene_history = []
        self.current_objectives = config.objectives.copy()
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Generate the system prompt for this scenario.
        
        Returns:
            System prompt text
        """
        pass
    
    @abstractmethod
    def get_character_sheet(self, character_name: str) -> Optional[str]:
        """Get character sheet for a specific character.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Character sheet text or None if not found
        """
        pass
    
    @abstractmethod
    def get_world_state(self) -> str:
        """Get current world state description.
        
        Returns:
            World state text
        """
        pass
    
    def add_character(self, name: str, character_data: Dict[str, Any]) -> None:
        """Add or update a character in the scenario.
        
        Args:
            name: Character name
            character_data: Character information
        """
        self.config.characters[name] = character_data
        self.active_characters.add(name)
    
    def set_scene(self, scene_description: str) -> None:
        """Set the current scene.
        
        Args:
            scene_description: Description of current scene
        """
        if self.config.current_scene:
            self.scene_history.append(self.config.current_scene)
        self.config.current_scene = scene_description
    
    def add_objective(self, objective: str) -> None:
        """Add a new objective.
        
        Args:
            objective: Objective description
        """
        self.current_objectives.append(objective)
    
    def complete_objective(self, objective: str) -> bool:
        """Mark an objective as complete.
        
        Args:
            objective: Objective to complete
            
        Returns:
            True if objective was found and removed
        """
        if objective in self.current_objectives:
            self.current_objectives.remove(objective)
            return True
        return False
    
    def get_response_length_guidance(self) -> str:
        """Get guidance for response length based on config.
        
        Returns:
            Length guidance text
        """
        length_map = {
            "brief": "Keep responses concise and to the point (1-2 paragraphs).",
            "medium": "Provide detailed but focused responses (2-3 paragraphs).",
            "detailed": "Give comprehensive, immersive responses (3-4 paragraphs).",
            "verbose": "Provide rich, elaborate descriptions and dialogue (4+ paragraphs)."
        }
        
        return length_map.get(self.config.response_length, length_map["medium"])
    
    def get_tone_guidance(self) -> str:
        """Get guidance for tone based on config.
        
        Returns:
            Tone guidance text
        """
        tone_map = {
            "serious": "Maintain a serious, dramatic tone. Focus on meaningful character development and weighty themes.",
            "lighthearted": "Keep the tone light and fun. Include humor and playful interactions.",
            "dark": "Embrace darker themes and atmosphere. Show the harsh realities of the world.",
            "comedic": "Prioritize humor and entertainment. Use comedic timing and funny situations.",
            "balanced": "Adapt tone to match the current situation and character emotions."
        }
        
        return tone_map.get(self.config.tone, tone_map["balanced"])
    
    def get_nsfw_guidance(self) -> str:
        """Get NSFW content guidance based on config.
        
        Returns:
            NSFW guidance text
        """
        nsfw_map = {
            0: "Keep content completely family-friendly. Avoid any sexual or explicit content.",
            1: "Allow mild romantic content and innuendo. Keep things tasteful.",
            2: "Allow moderate romantic and suggestive content. Fade to black for explicit scenes.",
            3: "Allow explicit content as appropriate to the story and characters."
        }
        
        return nsfw_map.get(self.config.nsfw_level, nsfw_map[0])
    
    def build_context_prompt(self) -> str:
        """Build the complete context prompt for this scenario.
        
        Returns:
            Complete context prompt
        """
        sections = []
        
        # System prompt
        sections.append(self.get_system_prompt())
        
        # World state
        world_state = self.get_world_state()
        if world_state:
            sections.append(f"[WORLD STATE]\n{world_state}")
        
        # Active character sheets
        for character in self.active_characters:
            sheet = self.get_character_sheet(character)
            if sheet:
                sections.append(f"[CHARACTER: {character.upper()}]\n{sheet}")
        
        # Current scene and objectives
        if self.config.current_scene:
            sections.append(f"[CURRENT SCENE]\n{self.config.current_scene}")
        
        if self.current_objectives:
            objectives_text = "\n".join(f"- {obj}" for obj in self.current_objectives)
            sections.append(f"[CURRENT OBJECTIVES]\n{objectives_text}")
        
        # Important facts
        if self.config.important_facts:
            facts_text = "\n".join(f"- {fact}" for fact in self.config.important_facts)
            sections.append(f"[IMPORTANT FACTS]\n{facts_text}")
        
        # Relationship dynamics
        if self.config.relationship_dynamics:
            dynamics_text = "\n".join(
                f"- {rel}: {desc}" 
                for rel, desc in self.config.relationship_dynamics.items()
            )
            sections.append(f"[RELATIONSHIP DYNAMICS]\n{dynamics_text}")
        
        # Style guidance
        guidance_parts = []
        guidance_parts.append(self.get_response_length_guidance())
        guidance_parts.append(self.get_tone_guidance())
        guidance_parts.append(self.get_nsfw_guidance())
        
        if self.config.style_notes:
            guidance_parts.extend(self.config.style_notes)
        
        if guidance_parts:
            sections.append(f"[STYLE GUIDANCE]\n" + "\n".join(guidance_parts))
        
        # Additional system prompt additions
        if self.config.system_prompt_additions:
            sections.append("\n".join(self.config.system_prompt_additions))
        
        return "\n\n".join(sections)
    
    def save_to_file(self, filepath: str) -> None:
        """Save scenario configuration to file.
        
        Args:
            filepath: Path to save file
        """
        config_dict = self.config.to_dict()
        
        if filepath.endswith('.yaml') or filepath.endswith('.yml'):
            with open(filepath, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        else:
            with open(filepath, 'w') as f:
                json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "BaseScenario":
        """Load scenario from file.
        
        Args:
            filepath: Path to load from
            
        Returns:
            Loaded scenario instance
        """
        if filepath.endswith('.yaml') or filepath.endswith('.yml'):
            with open(filepath) as f:
                config_dict = yaml.safe_load(f)
        else:
            with open(filepath) as f:
                config_dict = json.load(f)
        
        config = ScenarioConfig.from_dict(config_dict)
        return cls(config)