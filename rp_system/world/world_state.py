"""Dynamic world state management and simulation."""

import logging
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import random


@dataclass
class Location:
    """Represents a location in the world."""
    name: str
    description: str
    type: str = "generic"  # town, dungeon, wilderness, etc.
    connections: List[str] = field(default_factory=list)
    characters_present: Set[str] = field(default_factory=set)
    items: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.characters_present, list):
            self.characters_present = set(self.characters_present)


@dataclass
class WorldFact:
    """Represents a fact about the world state."""
    id: str
    content: str
    category: str  # politics, magic, technology, etc.
    importance: float  # 0.0 to 1.0
    last_updated: datetime
    dependencies: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)


@dataclass
class GlobalEvent:
    """Represents a world-level event that affects the global state."""
    id: str
    name: str
    description: str
    type: str  # political, natural, magical, etc.
    start_time: datetime
    duration: Optional[timedelta] = None
    affected_locations: List[str] = field(default_factory=list)
    affected_characters: List[str] = field(default_factory=list)
    consequences: List[str] = field(default_factory=list)
    is_active: bool = True


class WorldState:
    """Manages the dynamic state of the game world."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize world state manager.
        
        Args:
            storage_path: Path to store world data
        """
        self.storage_path = Path(storage_path) if storage_path else Path("rp_world")
        self.storage_path.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # World components
        self.locations: Dict[str, Location] = {}
        self.world_facts: Dict[str, WorldFact] = {}
        self.global_events: Dict[str, GlobalEvent] = {}
        
        # Current state
        self.current_location: Optional[str] = None
        self.world_time: datetime = datetime.now()
        self.time_scale: float = 1.0  # How fast time passes
        
        # World rules and properties
        self.world_rules: List[str] = []
        self.world_properties: Dict[str, Any] = {}
        
        # Load existing world data
        self._load_world_data()
        
        self.logger.info(f"Initialized world state with storage at {self.storage_path}")
    
    def add_location(
        self,
        name: str,
        description: str,
        location_type: str = "generic",
        connections: List[str] = None,
        **properties
    ) -> Location:
        """Add a new location to the world.
        
        Args:
            name: Location name
            description: Location description
            location_type: Type of location
            connections: Connected locations
            **properties: Additional properties
            
        Returns:
            Created location
        """
        location = Location(
            name=name,
            description=description,
            type=location_type,
            connections=connections or [],
            properties=properties
        )
        
        self.locations[name] = location
        self._save_world_data()
        
        self.logger.info(f"Added location: {name}")
        return location
    
    def get_location(self, name: str) -> Optional[Location]:
        """Get a location by name.
        
        Args:
            name: Location name
            
        Returns:
            Location or None if not found
        """
        return self.locations.get(name)
    
    def set_current_location(self, location_name: str) -> None:
        """Set the current location.
        
        Args:
            location_name: Name of the location
        """
        if location_name in self.locations:
            self.current_location = location_name
            self.logger.debug(f"Current location set to: {location_name}")
        else:
            self.logger.warning(f"Location {location_name} not found")
    
    def move_character_to_location(
        self,
        character_name: str,
        location_name: str,
        remove_from_previous: bool = True
    ) -> bool:
        """Move a character to a location.
        
        Args:
            character_name: Character to move
            location_name: Destination location
            remove_from_previous: Whether to remove from previous location
            
        Returns:
            True if successful
        """
        location = self.locations.get(location_name)
        if not location:
            self.logger.warning(f"Cannot move {character_name} to unknown location {location_name}")
            return False
        
        # Remove from previous locations if requested
        if remove_from_previous:
            for loc in self.locations.values():
                loc.characters_present.discard(character_name)
        
        # Add to new location
        location.characters_present.add(character_name)
        self._save_world_data()
        
        self.logger.debug(f"Moved {character_name} to {location_name}")
        return True
    
    def get_characters_at_location(self, location_name: str) -> Set[str]:
        """Get all characters at a specific location.
        
        Args:
            location_name: Location name
            
        Returns:
            Set of character names
        """
        location = self.locations.get(location_name)
        return location.characters_present if location else set()
    
    def add_world_fact(
        self,
        fact_id: str,
        content: str,
        category: str = "general",
        importance: float = 0.5,
        dependencies: List[str] = None,
        conflicts_with: List[str] = None
    ) -> WorldFact:
        """Add a fact about the world state.
        
        Args:
            fact_id: Unique identifier for the fact
            content: Fact content
            category: Fact category
            importance: Importance level (0.0-1.0)
            dependencies: Facts this depends on
            conflicts_with: Facts this conflicts with
            
        Returns:
            Created world fact
        """
        fact = WorldFact(
            id=fact_id,
            content=content,
            category=category,
            importance=importance,
            last_updated=datetime.now(),
            dependencies=dependencies or [],
            conflicts_with=conflicts_with or []
        )
        
        # Check for conflicts
        for conflict_id in fact.conflicts_with:
            if conflict_id in self.world_facts:
                self.logger.warning(f"Fact {fact_id} conflicts with existing fact {conflict_id}")
        
        self.world_facts[fact_id] = fact
        self._save_world_data()
        
        self.logger.info(f"Added world fact: {fact_id}")
        return fact
    
    def update_world_fact(
        self,
        fact_id: str,
        new_content: str,
        importance: Optional[float] = None
    ) -> bool:
        """Update an existing world fact.
        
        Args:
            fact_id: Fact identifier
            new_content: New content
            importance: New importance level
            
        Returns:
            True if successful
        """
        fact = self.world_facts.get(fact_id)
        if not fact:
            self.logger.warning(f"Cannot update unknown fact {fact_id}")
            return False
        
        fact.content = new_content
        fact.last_updated = datetime.now()
        
        if importance is not None:
            fact.importance = max(0.0, min(1.0, importance))
        
        self._save_world_data()
        self.logger.info(f"Updated world fact: {fact_id}")
        return True
    
    def get_world_facts_by_category(self, category: str) -> List[WorldFact]:
        """Get all facts in a specific category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of facts in the category
        """
        return [
            fact for fact in self.world_facts.values()
            if fact.category == category
        ]
    
    def get_important_facts(self, min_importance: float = 0.7) -> List[WorldFact]:
        """Get facts above a certain importance threshold.
        
        Args:
            min_importance: Minimum importance level
            
        Returns:
            List of important facts
        """
        return [
            fact for fact in self.world_facts.values()
            if fact.importance >= min_importance
        ]
    
    def create_global_event(
        self,
        event_id: str,
        name: str,
        description: str,
        event_type: str = "general",
        duration: Optional[timedelta] = None,
        affected_locations: List[str] = None,
        affected_characters: List[str] = None,
        consequences: List[str] = None
    ) -> GlobalEvent:
        """Create a new global event.
        
        Args:
            event_id: Unique event identifier
            name: Event name
            description: Event description
            event_type: Type of event
            duration: How long the event lasts
            affected_locations: Locations affected by the event
            affected_characters: Characters affected by the event
            consequences: Consequences of the event
            
        Returns:
            Created global event
        """
        event = GlobalEvent(
            id=event_id,
            name=name,
            description=description,
            type=event_type,
            start_time=self.world_time,
            duration=duration,
            affected_locations=affected_locations or [],
            affected_characters=affected_characters or [],
            consequences=consequences or []
        )
        
        self.global_events[event_id] = event
        self._save_world_data()
        
        self.logger.info(f"Created global event: {name}")
        return event
    
    def end_global_event(self, event_id: str) -> bool:
        """End a global event.
        
        Args:
            event_id: Event identifier
            
        Returns:
            True if successful
        """
        event = self.global_events.get(event_id)
        if not event:
            self.logger.warning(f"Cannot end unknown event {event_id}")
            return False
        
        event.is_active = False
        self._save_world_data()
        
        self.logger.info(f"Ended global event: {event.name}")
        return True
    
    def get_active_events(self) -> List[GlobalEvent]:
        """Get all currently active global events.
        
        Returns:
            List of active events
        """
        active_events = []
        
        for event in self.global_events.values():
            if not event.is_active:
                continue
            
            # Check if event has expired
            if event.duration:
                end_time = event.start_time + event.duration
                if self.world_time >= end_time:
                    event.is_active = False
                    continue
            
            active_events.append(event)
        
        return active_events
    
    def advance_time(self, hours: float = 1.0) -> None:
        """Advance world time.
        
        Args:
            hours: Hours to advance
        """
        time_delta = timedelta(hours=hours * self.time_scale)
        self.world_time += time_delta
        
        # Update active events
        self.get_active_events()  # This will deactivate expired events
        
        self.logger.debug(f"Advanced world time by {hours} hours to {self.world_time}")
    
    def set_world_rule(self, rule: str) -> None:
        """Add or update a world rule.
        
        Args:
            rule: Rule description
        """
        if rule not in self.world_rules:
            self.world_rules.append(rule)
            self._save_world_data()
            self.logger.info(f"Added world rule: {rule}")
    
    def set_world_property(self, key: str, value: Any) -> None:
        """Set a world property.
        
        Args:
            key: Property key
            value: Property value
        """
        self.world_properties[key] = value
        self._save_world_data()
        self.logger.debug(f"Set world property {key}: {value}")
    
    def get_world_summary(self) -> str:
        """Generate a summary of the current world state.
        
        Returns:
            World state summary
        """
        summary_parts = ["=== WORLD STATE SUMMARY ==="]
        
        # Current time and location
        summary_parts.append(f"Current Time: {self.world_time.strftime('%Y-%m-%d %H:%M')}")
        if self.current_location:
            summary_parts.append(f"Current Location: {self.current_location}")
        
        # World rules
        if self.world_rules:
            summary_parts.append("\nWorld Rules:")
            for rule in self.world_rules:
                summary_parts.append(f"- {rule}")
        
        # Important facts
        important_facts = self.get_important_facts()
        if important_facts:
            summary_parts.append("\nImportant Facts:")
            for fact in important_facts[:5]:  # Top 5 most important
                summary_parts.append(f"- {fact.content}")
        
        # Active events
        active_events = self.get_active_events()
        if active_events:
            summary_parts.append("\nActive Events:")
            for event in active_events:
                summary_parts.append(f"- {event.name}: {event.description}")
        
        # Locations
        if self.locations:
            summary_parts.append(f"\nLocations: {len(self.locations)} defined")
            if self.current_location and self.current_location in self.locations:
                current_loc = self.locations[self.current_location]
                if current_loc.characters_present:
                    summary_parts.append(f"Characters at {self.current_location}: {', '.join(current_loc.characters_present)}")
        
        return "\n".join(summary_parts)
    
    def get_location_description(self, location_name: str, include_characters: bool = True) -> str:
        """Get a detailed description of a location.
        
        Args:
            location_name: Location name
            include_characters: Whether to include character presence
            
        Returns:
            Location description
        """
        location = self.locations.get(location_name)
        if not location:
            return f"Location '{location_name}' not found."
        
        desc_parts = [f"=== {location.name.upper()} ==="]
        desc_parts.append(location.description)
        
        if location.type != "generic":
            desc_parts.append(f"Type: {location.type}")
        
        if location.connections:
            desc_parts.append(f"Connections: {', '.join(location.connections)}")
        
        if include_characters and location.characters_present:
            desc_parts.append(f"Characters present: {', '.join(location.characters_present)}")
        
        if location.items:
            desc_parts.append(f"Items: {', '.join(location.items)}")
        
        if location.events:
            desc_parts.append(f"Current events: {', '.join(location.events)}")
        
        # Custom properties
        for key, value in location.properties.items():
            desc_parts.append(f"{key.title()}: {value}")
        
        return "\n".join(desc_parts)
    
    def check_consistency(self) -> List[str]:
        """Check for inconsistencies in world state.
        
        Returns:
            List of consistency issues found
        """
        issues = []
        
        # Check fact conflicts
        for fact in self.world_facts.values():
            for conflict_id in fact.conflicts_with:
                if conflict_id in self.world_facts:
                    issues.append(f"Fact conflict: {fact.id} vs {conflict_id}")
        
        # Check location connections
        for loc_name, location in self.locations.items():
            for connection in location.connections:
                if connection not in self.locations:
                    issues.append(f"Location {loc_name} connects to unknown location {connection}")
                else:
                    # Check if connection is bidirectional
                    connected_loc = self.locations[connection]
                    if loc_name not in connected_loc.connections:
                        issues.append(f"Non-bidirectional connection: {loc_name} -> {connection}")
        
        # Check event consistency
        for event in self.global_events.values():
            for location in event.affected_locations:
                if location not in self.locations:
                    issues.append(f"Event {event.name} affects unknown location {location}")
        
        return issues
    
    def _save_world_data(self) -> None:
        """Save world data to disk."""
        try:
            # Convert locations to serializable format
            locations_data = {}
            for name, location in self.locations.items():
                loc_dict = asdict(location)
                loc_dict['characters_present'] = list(location.characters_present)
                locations_data[name] = loc_dict
            
            # Convert world facts to serializable format
            facts_data = {}
            for fact_id, fact in self.world_facts.items():
                fact_dict = asdict(fact)
                fact_dict['last_updated'] = fact.last_updated.isoformat()
                facts_data[fact_id] = fact_dict
            
            # Convert global events to serializable format
            events_data = {}
            for event_id, event in self.global_events.items():
                event_dict = asdict(event)
                event_dict['start_time'] = event.start_time.isoformat()
                if event.duration:
                    event_dict['duration'] = event.duration.total_seconds()
                else:
                    event_dict['duration'] = None
                events_data[event_id] = event_dict
            
            world_data = {
                "locations": locations_data,
                "world_facts": facts_data,
                "global_events": events_data,
                "current_location": self.current_location,
                "world_time": self.world_time.isoformat(),
                "time_scale": self.time_scale,
                "world_rules": self.world_rules,
                "world_properties": self.world_properties
            }
            
            with open(self.storage_path / "world_state.json", "w") as f:
                json.dump(world_data, f, indent=2, default=str)
            
            self.logger.debug("Saved world data")
            
        except Exception as e:
            self.logger.error(f"Failed to save world data: {e}")
    
    def _load_world_data(self) -> None:
        """Load world data from disk."""
        world_file = self.storage_path / "world_state.json"
        
        if not world_file.exists():
            return
        
        try:
            with open(world_file) as f:
                world_data = json.load(f)
            
            # Load locations
            for name, loc_dict in world_data.get("locations", {}).items():
                loc_dict['characters_present'] = set(loc_dict.get('characters_present', []))
                self.locations[name] = Location(**loc_dict)
            
            # Load world facts
            for fact_id, fact_dict in world_data.get("world_facts", {}).items():
                fact_dict['last_updated'] = datetime.fromisoformat(fact_dict['last_updated'])
                self.world_facts[fact_id] = WorldFact(**fact_dict)
            
            # Load global events
            for event_id, event_dict in world_data.get("global_events", {}).items():
                event_dict['start_time'] = datetime.fromisoformat(event_dict['start_time'])
                if event_dict.get('duration') is not None:
                    event_dict['duration'] = timedelta(seconds=event_dict['duration'])
                else:
                    event_dict['duration'] = None
                self.global_events[event_id] = GlobalEvent(**event_dict)
            
            # Load other properties
            self.current_location = world_data.get("current_location")
            if world_data.get("world_time"):
                self.world_time = datetime.fromisoformat(world_data["world_time"])
            self.time_scale = world_data.get("time_scale", 1.0)
            self.world_rules = world_data.get("world_rules", [])
            self.world_properties = world_data.get("world_properties", {})
            
            self.logger.info(f"Loaded world data: {len(self.locations)} locations, "
                           f"{len(self.world_facts)} facts, {len(self.global_events)} events")
            
        except Exception as e:
            self.logger.error(f"Failed to load world data: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get world state statistics.
        
        Returns:
            Statistics dictionary
        """
        active_events = self.get_active_events()
        important_facts = self.get_important_facts()
        
        return {
            "locations": len(self.locations),
            "world_facts": len(self.world_facts),
            "important_facts": len(important_facts),
            "global_events": len(self.global_events),
            "active_events": len(active_events),
            "world_rules": len(self.world_rules),
            "current_location": self.current_location,
            "world_time": self.world_time.isoformat(),
            "storage_path": str(self.storage_path)
        }