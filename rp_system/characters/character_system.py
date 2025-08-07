"""Character state management and tracking system."""

import logging
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import copy
from pathlib import Path


@dataclass
class CharacterState:
    """Represents the current state of a character."""
    name: str
    
    # Basic info
    description: str = ""
    personality: str = ""
    background: str = ""
    
    # Current status
    health: float = 1.0  # 0.0 to 1.0
    emotional_state: str = "neutral"
    current_location: str = ""
    
    # Relationships with other characters
    relationships: Dict[str, float] = field(default_factory=dict)  # -1.0 to 1.0
    
    # Abilities and attributes
    abilities: Dict[str, Any] = field(default_factory=dict)
    equipment: List[str] = field(default_factory=list)
    
    # Goals and motivations
    current_goals: List[str] = field(default_factory=list)
    completed_goals: List[str] = field(default_factory=list)
    
    # Memory and knowledge
    known_facts: Set[str] = field(default_factory=set)
    secrets: Set[str] = field(default_factory=set)
    
    # Conversation and interaction history
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    
    # Custom attributes
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert sets to lists for JSON serialization
        data['known_facts'] = list(self.known_facts)
        data['secrets'] = list(self.secrets)
        # Convert datetime to string
        if self.last_interaction:
            data['last_interaction'] = self.last_interaction.isoformat()
        else:
            data['last_interaction'] = None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterState":
        """Create from dictionary."""
        # Convert lists back to sets
        if 'known_facts' in data:
            data['known_facts'] = set(data['known_facts'])
        if 'secrets' in data:
            data['secrets'] = set(data['secrets'])
        
        # Convert string back to datetime
        if data.get('last_interaction'):
            data['last_interaction'] = datetime.fromisoformat(data['last_interaction'])
        
        return cls(**data)


@dataclass
class RelationshipChange:
    """Tracks a change in character relationship."""
    character1: str
    character2: str
    old_value: float
    new_value: float
    reason: str
    timestamp: datetime


class CharacterSystem:
    """Manages character states, relationships, and interactions."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize character system.
        
        Args:
            storage_path: Path to store character data
        """
        self.storage_path = Path(storage_path) if storage_path else Path("rp_characters")
        self.storage_path.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Character storage
        self.characters: Dict[str, CharacterState] = {}
        self.relationship_history: List[RelationshipChange] = []
        
        # Active characters in current scene
        self.active_characters: Set[str] = set()
        
        # Load existing character data
        self._load_characters()
        
        self.logger.info(f"Initialized character system with storage at {self.storage_path}")
    
    def create_character(
        self,
        name: str,
        description: str = "",
        personality: str = "",
        background: str = "",
        **kwargs
    ) -> CharacterState:
        """Create a new character.
        
        Args:
            name: Character name
            description: Physical description
            personality: Personality traits
            background: Character background
            **kwargs: Additional attributes
            
        Returns:
            Created character state
        """
        if name in self.characters:
            self.logger.warning(f"Character {name} already exists, updating instead")
            return self.update_character(name, description=description, 
                                       personality=personality, background=background, **kwargs)
        
        character = CharacterState(
            name=name,
            description=description,
            personality=personality,
            background=background,
            **kwargs
        )
        
        self.characters[name] = character
        self._save_characters()
        
        self.logger.info(f"Created character: {name}")
        return character
    
    def get_character(self, name: str) -> Optional[CharacterState]:
        """Get a character by name.
        
        Args:
            name: Character name
            
        Returns:
            Character state or None if not found
        """
        return self.characters.get(name)
    
    def update_character(self, name: str, **kwargs) -> Optional[CharacterState]:
        """Update character attributes.
        
        Args:
            name: Character name
            **kwargs: Attributes to update
            
        Returns:
            Updated character state or None if not found
        """
        character = self.characters.get(name)
        if not character:
            self.logger.warning(f"Character {name} not found for update")
            return None
        
        # Update attributes
        for key, value in kwargs.items():
            if hasattr(character, key):
                setattr(character, key, value)
            else:
                character.custom_attributes[key] = value
        
        self._save_characters()
        self.logger.debug(f"Updated character {name}: {list(kwargs.keys())}")
        return character
    
    def set_character_relationship(
        self,
        character1: str,
        character2: str,
        relationship_value: float,
        reason: str = ""
    ) -> None:
        """Set relationship between two characters.
        
        Args:
            character1: First character name
            character2: Second character name
            relationship_value: Relationship strength (-1.0 to 1.0)
            reason: Reason for relationship change
        """
        relationship_value = max(-1.0, min(1.0, relationship_value))
        
        # Get characters
        char1 = self.characters.get(character1)
        char2 = self.characters.get(character2)
        
        if not char1 or not char2:
            self.logger.warning(f"Cannot set relationship: {character1} or {character2} not found")
            return
        
        # Track old values
        old_value1 = char1.relationships.get(character2, 0.0)
        old_value2 = char2.relationships.get(character1, 0.0)
        
        # Set relationships (bidirectional)
        char1.relationships[character2] = relationship_value
        char2.relationships[character1] = relationship_value
        
        # Track changes
        if old_value1 != relationship_value:
            self.relationship_history.append(RelationshipChange(
                character1=character1,
                character2=character2,
                old_value=old_value1,
                new_value=relationship_value,
                reason=reason,
                timestamp=datetime.now()
            ))
        
        self._save_characters()
        self.logger.info(f"Set relationship {character1}-{character2}: {relationship_value}")
    
    def modify_relationship(
        self,
        character1: str,
        character2: str,
        change: float,
        reason: str = ""
    ) -> None:
        """Modify existing relationship between characters.
        
        Args:
            character1: First character name
            character2: Second character name
            change: Change amount
            reason: Reason for change
        """
        char1 = self.characters.get(character1)
        if not char1:
            return
        
        current_value = char1.relationships.get(character2, 0.0)
        new_value = max(-1.0, min(1.0, current_value + change))
        
        self.set_character_relationship(character1, character2, new_value, reason)
    
    def get_relationship(self, character1: str, character2: str) -> float:
        """Get relationship value between two characters.
        
        Args:
            character1: First character name
            character2: Second character name
            
        Returns:
            Relationship value (-1.0 to 1.0)
        """
        char1 = self.characters.get(character1)
        if not char1:
            return 0.0
        
        return char1.relationships.get(character2, 0.0)
    
    def set_active_characters(self, character_names: List[str]) -> None:
        """Set which characters are active in the current scene.
        
        Args:
            character_names: List of character names
        """
        self.active_characters = set(character_names)
        
        # Update last interaction for active characters
        now = datetime.now()
        for name in character_names:
            character = self.characters.get(name)
            if character:
                character.last_interaction = now
                character.interaction_count += 1
        
        self.logger.debug(f"Set active characters: {character_names}")
    
    def add_active_character(self, character_name: str) -> None:
        """Add a character to the active scene.
        
        Args:
            character_name: Character name to add
        """
        self.active_characters.add(character_name)
        
        character = self.characters.get(character_name)
        if character:
            character.last_interaction = datetime.now()
            character.interaction_count += 1
    
    def remove_active_character(self, character_name: str) -> None:
        """Remove a character from the active scene.
        
        Args:
            character_name: Character name to remove
        """
        self.active_characters.discard(character_name)
    
    def get_active_characters(self) -> List[CharacterState]:
        """Get list of active characters.
        
        Returns:
            List of active character states
        """
        return [
            self.characters[name] 
            for name in self.active_characters 
            if name in self.characters
        ]
    
    def add_character_knowledge(self, character_name: str, fact: str, is_secret: bool = False) -> None:
        """Add knowledge to a character.
        
        Args:
            character_name: Character name
            fact: Fact to add
            is_secret: Whether this is secret knowledge
        """
        character = self.characters.get(character_name)
        if not character:
            return
        
        if is_secret:
            character.secrets.add(fact)
        else:
            character.known_facts.add(fact)
        
        self._save_characters()
        self.logger.debug(f"Added {'secret ' if is_secret else ''}knowledge to {character_name}")
    
    def character_knows(self, character_name: str, fact: str) -> bool:
        """Check if a character knows a specific fact.
        
        Args:
            character_name: Character name
            fact: Fact to check
            
        Returns:
            True if character knows the fact
        """
        character = self.characters.get(character_name)
        if not character:
            return False
        
        return fact in character.known_facts or fact in character.secrets
    
    def get_character_sheet(self, character_name: str) -> str:
        """Generate a character sheet for display.
        
        Args:
            character_name: Character name
            
        Returns:
            Formatted character sheet
        """
        character = self.characters.get(character_name)
        if not character:
            return f"Character '{character_name}' not found."
        
        sheet_parts = [f"=== CHARACTER SHEET: {character.name.upper()} ==="]
        
        if character.description:
            sheet_parts.append(f"Description: {character.description}")
        
        if character.personality:
            sheet_parts.append(f"Personality: {character.personality}")
        
        if character.background:
            sheet_parts.append(f"Background: {character.background}")
        
        # Status
        status_parts = []
        if character.health != 1.0:
            status_parts.append(f"Health: {character.health:.1%}")
        if character.emotional_state != "neutral":
            status_parts.append(f"Emotional State: {character.emotional_state}")
        if character.current_location:
            status_parts.append(f"Location: {character.current_location}")
        
        if status_parts:
            sheet_parts.append(f"Status: {', '.join(status_parts)}")
        
        # Abilities
        if character.abilities:
            abilities_text = ", ".join(f"{k}: {v}" for k, v in character.abilities.items())
            sheet_parts.append(f"Abilities: {abilities_text}")
        
        # Equipment
        if character.equipment:
            sheet_parts.append(f"Equipment: {', '.join(character.equipment)}")
        
        # Goals
        if character.current_goals:
            goals_text = "; ".join(character.current_goals)
            sheet_parts.append(f"Current Goals: {goals_text}")
        
        # Relationships
        if character.relationships:
            rel_text = []
            for other_char, value in character.relationships.items():
                if value > 0.7:
                    rel_text.append(f"{other_char} (Close)")
                elif value > 0.3:
                    rel_text.append(f"{other_char} (Friendly)")
                elif value > -0.3:
                    rel_text.append(f"{other_char} (Neutral)")
                elif value > -0.7:
                    rel_text.append(f"{other_char} (Unfriendly)")
                else:
                    rel_text.append(f"{other_char} (Hostile)")
            
            if rel_text:
                sheet_parts.append(f"Relationships: {', '.join(rel_text)}")
        
        # Custom attributes
        for key, value in character.custom_attributes.items():
            sheet_parts.append(f"{key.title()}: {value}")
        
        return "\n".join(sheet_parts)
    
    def get_relationship_summary(self) -> str:
        """Get a summary of all character relationships.
        
        Returns:
            Formatted relationship summary
        """
        if not self.characters:
            return "No characters defined."
        
        summary_parts = ["=== CHARACTER RELATIONSHIPS ==="]
        
        processed_pairs = set()
        
        for char1_name, char1 in self.characters.items():
            for char2_name, relationship_value in char1.relationships.items():
                # Avoid duplicate pairs
                pair = tuple(sorted([char1_name, char2_name]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)
                
                if relationship_value > 0.7:
                    status = "very close"
                elif relationship_value > 0.3:
                    status = "friendly"
                elif relationship_value > -0.3:
                    status = "neutral"
                elif relationship_value > -0.7:
                    status = "unfriendly"
                else:
                    status = "hostile"
                
                summary_parts.append(f"{char1_name} ↔ {char2_name}: {status} ({relationship_value:+.1f})")
        
        return "\n".join(summary_parts)
    
    def _save_characters(self) -> None:
        """Save character data to disk."""
        try:
            character_data = {
                "characters": {
                    name: char.to_dict() 
                    for name, char in self.characters.items()
                },
                "active_characters": list(self.active_characters),
                "relationship_history": [
                    {
                        "character1": change.character1,
                        "character2": change.character2,
                        "old_value": change.old_value,
                        "new_value": change.new_value,
                        "reason": change.reason,
                        "timestamp": change.timestamp.isoformat()
                    }
                    for change in self.relationship_history
                ]
            }
            
            with open(self.storage_path / "characters.json", "w") as f:
                json.dump(character_data, f, indent=2, default=str)
            
            self.logger.debug("Saved character data")
            
        except Exception as e:
            self.logger.error(f"Failed to save character data: {e}")
    
    def _load_characters(self) -> None:
        """Load character data from disk."""
        character_file = self.storage_path / "characters.json"
        
        if not character_file.exists():
            return
        
        try:
            with open(character_file) as f:
                character_data = json.load(f)
            
            # Load characters
            for name, char_dict in character_data.get("characters", {}).items():
                self.characters[name] = CharacterState.from_dict(char_dict)
            
            # Load active characters
            self.active_characters = set(character_data.get("active_characters", []))
            
            # Load relationship history
            for change_dict in character_data.get("relationship_history", []):
                self.relationship_history.append(RelationshipChange(
                    character1=change_dict["character1"],
                    character2=change_dict["character2"],
                    old_value=change_dict["old_value"],
                    new_value=change_dict["new_value"],
                    reason=change_dict["reason"],
                    timestamp=datetime.fromisoformat(change_dict["timestamp"])
                ))
            
            self.logger.info(f"Loaded {len(self.characters)} characters")
            
        except Exception as e:
            self.logger.error(f"Failed to load character data: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get character system statistics.
        
        Returns:
            Statistics dictionary
        """
        active_count = len(self.active_characters)
        total_relationships = sum(len(char.relationships) for char in self.characters.values()) // 2
        
        return {
            "total_characters": len(self.characters),
            "active_characters": active_count,
            "total_relationships": total_relationships,
            "relationship_changes": len(self.relationship_history),
            "storage_path": str(self.storage_path)
        }