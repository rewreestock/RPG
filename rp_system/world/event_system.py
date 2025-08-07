"""Event system for plot progression and random events."""

import logging
import random
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class EventTrigger(Enum):
    """Types of event triggers."""
    TIME_BASED = "time"
    CHARACTER_ACTION = "character_action"
    LOCATION_VISIT = "location_visit"
    RELATIONSHIP_CHANGE = "relationship_change"
    WORLD_STATE_CHANGE = "world_state"
    RANDOM = "random"
    MANUAL = "manual"


@dataclass
class EventCondition:
    """Condition that must be met for an event to trigger."""
    type: str  # location, character_present, relationship, world_fact, etc.
    target: str
    operator: str  # equals, greater_than, less_than, contains, etc.
    value: Any
    
    def check(self, context: Dict[str, Any]) -> bool:
        """Check if condition is met given context."""
        try:
            if self.type == "location":
                return context.get("current_location") == self.value
            
            elif self.type == "character_present":
                characters_present = context.get("characters_present", set())
                return self.target in characters_present
            
            elif self.type == "relationship":
                relationships = context.get("relationships", {})
                rel_value = relationships.get(self.target, 0.0)
                
                if self.operator == "greater_than":
                    return rel_value > self.value
                elif self.operator == "less_than":
                    return rel_value < self.value
                elif self.operator == "equals":
                    return abs(rel_value - self.value) < 0.1
            
            elif self.type == "world_fact":
                world_facts = context.get("world_facts", {})
                fact = world_facts.get(self.target)
                
                if self.operator == "exists":
                    return fact is not None
                elif self.operator == "contains" and fact:
                    return str(self.value).lower() in fact.content.lower()
            
            elif self.type == "time_passed":
                event_start = context.get("event_start_time")
                current_time = context.get("current_time", datetime.now())
                
                if event_start:
                    time_passed = current_time - event_start
                    
                    if self.operator == "greater_than":
                        return time_passed > timedelta(hours=self.value)
                    elif self.operator == "less_than":
                        return time_passed < timedelta(hours=self.value)
            
            elif self.type == "random":
                # Random chance (value should be 0.0 to 1.0)
                return random.random() < self.value
            
            return False
            
        except Exception:
            return False


@dataclass
class EventOutcome:
    """Outcome/consequence of an event."""
    type: str  # dialogue, world_change, character_change, etc.
    target: Optional[str] = None
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GameEvent:
    """Represents a game event with conditions and outcomes."""
    id: str
    name: str
    description: str
    trigger_type: EventTrigger
    
    # Conditions for event to fire
    conditions: List[EventCondition] = field(default_factory=list)
    
    # What happens when event fires
    outcomes: List[EventOutcome] = field(default_factory=list)
    
    # Event properties
    priority: int = 1  # Higher priority events fire first
    repeatable: bool = False
    cooldown_hours: float = 0.0
    
    # Tracking
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    is_active: bool = True


class EventSystem:
    """Manages plot progression and random events."""
    
    def __init__(self):
        """Initialize event system."""
        self.logger = logging.getLogger(__name__)
        
        # Event storage
        self.events: Dict[str, GameEvent] = {}
        self.event_queue: List[str] = []  # Events waiting to be processed
        
        # Event handlers
        self.outcome_handlers: Dict[str, Callable] = {}
        
        # Default outcome handlers
        self._register_default_handlers()
        
        self.logger.info("Initialized event system")
    
    def _register_default_handlers(self) -> None:
        """Register default outcome handlers."""
        self.outcome_handlers.update({
            "dialogue": self._handle_dialogue_outcome,
            "world_change": self._handle_world_change_outcome,
            "character_change": self._handle_character_change_outcome,
            "relationship_change": self._handle_relationship_change_outcome,
            "location_change": self._handle_location_change_outcome,
            "item_change": self._handle_item_change_outcome,
            "plot_advancement": self._handle_plot_advancement_outcome
        })
    
    def register_event(self, event: GameEvent) -> None:
        """Register a new event.
        
        Args:
            event: Event to register
        """
        self.events[event.id] = event
        self.logger.info(f"Registered event: {event.name}")
    
    def create_event(
        self,
        event_id: str,
        name: str,
        description: str,
        trigger_type: EventTrigger,
        conditions: List[EventCondition] = None,
        outcomes: List[EventOutcome] = None,
        **kwargs
    ) -> GameEvent:
        """Create and register a new event.
        
        Args:
            event_id: Unique event identifier
            name: Event name
            description: Event description
            trigger_type: How the event is triggered
            conditions: List of conditions
            outcomes: List of outcomes
            **kwargs: Additional event properties
            
        Returns:
            Created event
        """
        event = GameEvent(
            id=event_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            conditions=conditions or [],
            outcomes=outcomes or [],
            **kwargs
        )
        
        self.register_event(event)
        return event
    
    def check_events(self, context: Dict[str, Any]) -> List[str]:
        """Check all events and return those that should trigger.
        
        Args:
            context: Current game context
            
        Returns:
            List of event IDs that should trigger
        """
        triggered_events = []
        current_time = context.get("current_time", datetime.now())
        
        # Sort events by priority (higher first)
        sorted_events = sorted(
            self.events.values(),
            key=lambda e: e.priority,
            reverse=True
        )
        
        for event in sorted_events:
            if not event.is_active:
                continue
            
            # Check cooldown
            if event.last_triggered and event.cooldown_hours > 0:
                time_since_last = current_time - event.last_triggered
                if time_since_last < timedelta(hours=event.cooldown_hours):
                    continue
            
            # Check if event can repeat
            if not event.repeatable and event.trigger_count > 0:
                continue
            
            # Check all conditions
            if self._check_conditions(event, context):
                triggered_events.append(event.id)
        
        return triggered_events
    
    def _check_conditions(self, event: GameEvent, context: Dict[str, Any]) -> bool:
        """Check if all conditions for an event are met.
        
        Args:
            event: Event to check
            context: Current context
            
        Returns:
            True if all conditions are met
        """
        if not event.conditions:
            return True  # No conditions means always triggers (if other criteria met)
        
        for condition in event.conditions:
            if not condition.check(context):
                return False
        
        return True
    
    def trigger_event(self, event_id: str, context: Dict[str, Any]) -> List[str]:
        """Trigger a specific event and return its outcomes.
        
        Args:
            event_id: Event to trigger
            context: Current context
            
        Returns:
            List of outcome descriptions
        """
        event = self.events.get(event_id)
        if not event:
            self.logger.warning(f"Cannot trigger unknown event: {event_id}")
            return []
        
        # Update event tracking
        event.last_triggered = context.get("current_time", datetime.now())
        event.trigger_count += 1
        
        self.logger.info(f"Triggering event: {event.name}")
        
        # Process outcomes
        outcome_descriptions = []
        for outcome in event.outcomes:
            handler = self.outcome_handlers.get(outcome.type)
            if handler:
                try:
                    result = handler(outcome, context)
                    if result:
                        outcome_descriptions.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing outcome {outcome.type}: {e}")
            else:
                self.logger.warning(f"No handler for outcome type: {outcome.type}")
        
        return outcome_descriptions
    
    def _handle_dialogue_outcome(self, outcome: EventOutcome, context: Dict[str, Any]) -> str:
        """Handle dialogue outcome."""
        character = outcome.target or "Narrator"
        dialogue = outcome.description
        
        return f"{character}: {dialogue}"
    
    def _handle_world_change_outcome(self, outcome: EventOutcome, context: Dict[str, Any]) -> str:
        """Handle world state change outcome."""
        # This would integrate with WorldState
        change_type = outcome.parameters.get("change_type", "fact")
        
        if change_type == "fact":
            fact_content = outcome.description
            return f"World fact updated: {fact_content}"
        elif change_type == "rule":
            rule_content = outcome.description
            return f"World rule established: {rule_content}"
        
        return f"World changed: {outcome.description}"
    
    def _handle_character_change_outcome(self, outcome: EventOutcome, context: Dict[str, Any]) -> str:
        """Handle character change outcome."""
        character = outcome.target
        change_type = outcome.parameters.get("change_type", "state")
        
        if change_type == "emotion":
            emotion = outcome.parameters.get("emotion", "neutral")
            return f"{character} feels {emotion}: {outcome.description}"
        elif change_type == "health":
            health_change = outcome.parameters.get("change", 0)
            return f"{character} health changed by {health_change}: {outcome.description}"
        elif change_type == "goal":
            goal = outcome.parameters.get("goal", "")
            return f"{character} new goal: {goal}"
        
        return f"{character} changed: {outcome.description}"
    
    def _handle_relationship_change_outcome(self, outcome: EventOutcome, context: Dict[str, Any]) -> str:
        """Handle relationship change outcome."""
        characters = outcome.target.split("-") if outcome.target else []
        change = outcome.parameters.get("change", 0.0)
        
        if len(characters) == 2:
            return f"Relationship between {characters[0]} and {characters[1]} changed by {change:+.1f}: {outcome.description}"
        
        return f"Relationship changed: {outcome.description}"
    
    def _handle_location_change_outcome(self, outcome: EventOutcome, context: Dict[str, Any]) -> str:
        """Handle location change outcome."""
        location = outcome.target
        change_type = outcome.parameters.get("change_type", "description")
        
        if change_type == "new_location":
            return f"New location discovered: {location}"
        elif change_type == "location_change":
            return f"Location changed: {outcome.description}"
        
        return f"Location {location} updated: {outcome.description}"
    
    def _handle_item_change_outcome(self, outcome: EventOutcome, context: Dict[str, Any]) -> str:
        """Handle item change outcome."""
        item = outcome.target
        change_type = outcome.parameters.get("change_type", "acquire")
        
        if change_type == "acquire":
            return f"Item acquired: {item}"
        elif change_type == "lose":
            return f"Item lost: {item}"
        
        return f"Item {item}: {outcome.description}"
    
    def _handle_plot_advancement_outcome(self, outcome: EventOutcome, context: Dict[str, Any]) -> str:
        """Handle plot advancement outcome."""
        plot_point = outcome.target or "main plot"
        return f"Plot advanced ({plot_point}): {outcome.description}"
    
    def register_outcome_handler(self, outcome_type: str, handler: Callable) -> None:
        """Register a custom outcome handler.
        
        Args:
            outcome_type: Type of outcome to handle
            handler: Handler function
        """
        self.outcome_handlers[outcome_type] = handler
        self.logger.debug(f"Registered outcome handler: {outcome_type}")
    
    def create_random_events(self, scenario_type: str = "generic") -> None:
        """Create a set of random events for a scenario.
        
        Args:
            scenario_type: Type of scenario to create events for
        """
        if scenario_type == "fantasy":
            self._create_fantasy_events()
        elif scenario_type == "modern":
            self._create_modern_events()
        elif scenario_type == "rezero":
            self._create_rezero_events()
        else:
            self._create_generic_events()
    
    def _create_generic_events(self) -> None:
        """Create generic random events."""
        events = [
            {
                "id": "random_encounter",
                "name": "Random Encounter",
                "description": "An unexpected encounter occurs",
                "trigger_type": EventTrigger.RANDOM,
                "conditions": [EventCondition("random", "", "equals", 0.1)],
                "outcomes": [EventOutcome("dialogue", "Stranger", "A mysterious figure approaches...")],
                "repeatable": True,
                "cooldown_hours": 2.0
            },
            {
                "id": "weather_change",
                "name": "Weather Change",
                "description": "The weather suddenly changes",
                "trigger_type": EventTrigger.TIME_BASED,
                "conditions": [EventCondition("random", "", "equals", 0.15)],
                "outcomes": [EventOutcome("world_change", None, "The weather shifts dramatically")],
                "repeatable": True,
                "cooldown_hours": 1.0
            }
        ]
        
        for event_data in events:
            conditions = event_data.pop("conditions", [])
            outcomes = event_data.pop("outcomes", [])
            event = GameEvent(**event_data, conditions=conditions, outcomes=outcomes)
            self.register_event(event)
    
    def _create_fantasy_events(self) -> None:
        """Create fantasy-themed events."""
        events = [
            {
                "id": "magic_surge",
                "name": "Magic Surge",
                "description": "Magical energies fluctuate wildly",
                "trigger_type": EventTrigger.RANDOM,
                "conditions": [EventCondition("random", "", "equals", 0.05)],
                "outcomes": [EventOutcome("world_change", None, "Magic surges through the area, causing unpredictable effects")],
                "repeatable": True,
                "cooldown_hours": 6.0
            },
            {
                "id": "monster_sighting",
                "name": "Monster Sighting",
                "description": "A dangerous creature is spotted nearby",
                "trigger_type": EventTrigger.LOCATION_VISIT,
                "conditions": [
                    EventCondition("location", "", "equals", "wilderness"),
                    EventCondition("random", "", "equals", 0.2)
                ],
                "outcomes": [EventOutcome("dialogue", "Scout", "Danger! A large beast was seen in these parts!")],
                "repeatable": True,
                "cooldown_hours": 4.0
            }
        ]
        
        for event_data in events:
            conditions = event_data.pop("conditions", [])
            outcomes = event_data.pop("outcomes", [])
            event = GameEvent(**event_data, conditions=conditions, outcomes=outcomes)
            self.register_event(event)
    
    def _create_rezero_events(self) -> None:
        """Create Re:Zero specific events."""
        events = [
            {
                "id": "witch_cult_activity",
                "name": "Witch Cult Activity",
                "description": "Signs of Witch Cult presence are detected",
                "trigger_type": EventTrigger.RANDOM,
                "conditions": [EventCondition("random", "", "equals", 0.03)],
                "outcomes": [EventOutcome("world_change", None, "Disturbing reports of Witch Cult activity reach your ears")],
                "repeatable": True,
                "cooldown_hours": 12.0,
                "priority": 3
            },
            {
                "id": "return_by_death_hint",
                "name": "Return by Death Hint",
                "description": "Something feels familiar, like déjà vu",
                "trigger_type": EventTrigger.RANDOM,
                "conditions": [EventCondition("random", "", "equals", 0.08)],
                "outcomes": [EventOutcome("character_change", "Subaru", "A strange feeling of having experienced this before washes over Subaru")],
                "repeatable": True,
                "cooldown_hours": 8.0
            }
        ]
        
        for event_data in events:
            conditions = event_data.pop("conditions", [])
            outcomes = event_data.pop("outcomes", [])
            event = GameEvent(**event_data, conditions=conditions, outcomes=outcomes)
            self.register_event(event)
    
    def get_event_summary(self) -> str:
        """Get a summary of all registered events.
        
        Returns:
            Event summary text
        """
        if not self.events:
            return "No events registered."
        
        summary_parts = ["=== EVENT SYSTEM SUMMARY ==="]
        
        active_events = [e for e in self.events.values() if e.is_active]
        summary_parts.append(f"Active Events: {len(active_events)}/{len(self.events)}")
        
        # Group by trigger type
        by_trigger = {}
        for event in active_events:
            trigger_type = event.trigger_type.value
            if trigger_type not in by_trigger:
                by_trigger[trigger_type] = []
            by_trigger[trigger_type].append(event)
        
        for trigger_type, events in by_trigger.items():
            summary_parts.append(f"\n{trigger_type.title()} Events:")
            for event in events:
                triggered_text = f" (triggered {event.trigger_count}x)" if event.trigger_count > 0 else ""
                summary_parts.append(f"  - {event.name}{triggered_text}")
        
        return "\n".join(summary_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event system statistics.
        
        Returns:
            Statistics dictionary
        """
        active_events = len([e for e in self.events.values() if e.is_active])
        triggered_events = len([e for e in self.events.values() if e.trigger_count > 0])
        
        return {
            "total_events": len(self.events),
            "active_events": active_events,
            "triggered_events": triggered_events,
            "outcome_handlers": len(self.outcome_handlers),
            "queued_events": len(self.event_queue)
        }