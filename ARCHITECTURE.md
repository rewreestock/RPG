# RPG System Architecture and Design

## Overview

The RPG Roleplay System is a production-ready framework for creating immersive AI-driven roleplay experiences using Google's Gemini Flash 2.5 model. The system is designed around intelligent context management, leveraging the full 1M token context window for superior narrative coherence across long sessions.

## Core Architecture

### 1. Context Management (`core/context_manager.py`)

**Purpose**: Intelligent optimization of the 1M token context window
- **Hierarchical Memory**: Recent > Important > Background priority
- **Smart Compression**: Preserves character personalities, world state, and conversation flow
- **Auto-Summarization**: Compresses old interactions while maintaining emotional beats
- **Token Optimization**: Maintains context under limits while preserving narrative quality

**Key Features**:
```python
context_manager = ContextManager(max_tokens=950000)
context_manager.add_message(content, tokens, importance=0.5)
context_manager.set_character_sheet(name, sheet, tokens)
context = context_manager.build_context(system_prompt)
```

### 2. Memory System (`core/memory_system.py`)

**Purpose**: Long-term storage with hierarchical organization
- **Recent Memories**: Last 24 hours of interactions
- **Important Memories**: High-importance events and interactions
- **Character-Specific**: Memories tagged by character involvement
- **Auto-Compression**: Summarizes old memories while preserving key details

**Key Features**:
```python
memory_system = MemorySystem(storage_path="./memories")
memory_system.add_memory(content, characters=["Alice"], importance=0.8)
memories = memory_system.retrieve_memories(characters=["Alice"], min_importance=0.7)
```

### 3. Smart Search Integration (`core/search_integration.py`)

**Purpose**: Contextual web search for RP enhancement
- **Selective Triggering**: Only searches for RP-relevant information
- **DuckDuckGo Integration**: Uses instant answer API for quick results
- **Cache Management**: Prevents redundant searches
- **Context Filtering**: Integrates results seamlessly into narrative

**Triggers Search For**:
- Unknown characters in established fictional universes
- World-building details and lore
- Technical information for sci-fi scenarios
- Historical/cultural context for period RPs

**Does NOT Search For**:
- Basic conversation
- Personal user information
- Non-RP related queries

### 4. Gemini Client (`core/gemini_client.py`)

**Purpose**: Production-ready API wrapper with robust error handling
- **Exponential Backoff**: Intelligent retry logic for API failures
- **Safety Settings**: Configured for RP content generation
- **Token Counting**: Accurate token usage tracking
- **Health Monitoring**: Connection status and error recovery

## Character & World Systems

### 5. Character Management (`characters/character_system.py`)

**Purpose**: Complete character state and relationship tracking
- **Character States**: Health, emotions, location, goals, knowledge
- **Relationship Dynamics**: Bidirectional relationship tracking with history
- **Active Management**: Scene-based character activation
- **Persistence**: Automatic saving and loading of character data

### 6. Personality Engine (`characters/personality_engine.py`)

**Purpose**: Consistent character behavior generation
- **Big Five Model**: Openness, conscientiousness, extraversion, agreeableness, neuroticism
- **Speech Patterns**: Formality, verbosity, emotional expression
- **Behavioral Tendencies**: Consistent character responses
- **Consistency Checking**: Validates actions against personality

### 7. World State (`world/world_state.py`)

**Purpose**: Dynamic world simulation and consistency management
- **Location System**: Connected locations with character tracking
- **World Facts**: Importance-weighted fact database
- **Global Events**: Time-based world events with consequences
- **Consistency Validation**: Prevents contradictions in world state

### 8. Event System (`world/event_system.py`)

**Purpose**: Plot progression and random event generation
- **Flexible Triggers**: Time, action, location, relationship-based
- **Condition System**: Complex event prerequisites
- **Outcome Handlers**: Pluggable consequence system
- **Scenario-Specific**: Events tailored to different RP genres

## Scenario System

### 9. Scenario Framework (`scenarios/`)

**Purpose**: Modular, configurable roleplay scenarios
- **Base Classes**: Abstract scenario framework
- **Dynamic Loading**: Runtime scenario switching
- **Configuration-Driven**: JSON/YAML scenario definitions
- **Built-in Presets**: Professional-quality scenario templates

**Available Scenarios**:
- **Re:Zero**: Complete with Return by Death mechanics and Witch Cult
- **Fantasy**: D&D-style adventures with magic systems
- **Modern Supernatural**: Urban fantasy with hidden world elements
- **Sci-Fi Space**: Interstellar exploration and alien diplomacy
- **Historical**: Period-accurate scenarios with cultural constraints

## Interface & Configuration

### 10. CLI Interface (`interface/cli_interface.py`)

**Purpose**: Production-ready command-line interface
- **Rich Output**: Enhanced terminal experience with colors and panels
- **Real-time Commands**: Live session management and customization
- **Session Management**: Save/load functionality
- **Status Monitoring**: System health and statistics

**Available Commands**:
```bash
/help              # Show command help
/status            # System status and statistics
/characters        # Show character information
/world             # Show world state
/save <name>       # Save current session
/load <name>       # Load saved session
/scenario <type>   # Load or list scenarios
```

### 11. Configuration Management (`interface/config_manager.py`)

**Purpose**: Comprehensive system and session configuration
- **System Config**: API keys, token limits, performance settings
- **Session Config**: Scenario type, character settings, AI behavior
- **Validation**: Configuration validation with helpful error messages
- **Presets**: Scenario and session presets for quick setup

## Data Flow

```
User Input → Context Manager → Gemini API → Response Processing
     ↓              ↓              ↓              ↓
Memory System ← Character Updates ← World Events ← Search Integration
```

1. **User Input**: Processed and added to context with importance scoring
2. **Context Building**: Intelligent assembly of relevant context segments
3. **Search Check**: Determines if web search would enhance the response
4. **API Call**: Gemini generation with optimized context and parameters
5. **Response Processing**: Parse and store response, update character/world state
6. **Memory Storage**: Archive interaction with appropriate importance and tags

## Token Optimization Strategy

### Context Hierarchy (Priority Order):
1. **System Prompt**: Scenario rules and AI instructions (always included)
2. **Character Sheets**: Active character descriptions and stats
3. **World State**: Current location, important facts, active events
4. **Recent Context**: Last 20-30k tokens of conversation
5. **Important Memories**: High-importance past events
6. **Summaries**: Compressed historical context

### Compression Algorithm:
- Preserve last 20 messages or 30k tokens (whichever is more)
- Move older messages to summary if important enough
- Combine similar memories into compressed summaries
- Remove lowest importance content as last resort
- Always preserve character sheets and world state

## Error Handling & Reliability

### Graceful Degradation:
- **API Failures**: Exponential backoff with informative error messages
- **Search Failures**: Continue operation without search enhancement
- **Memory Errors**: Log issues but don't interrupt conversation flow
- **Context Overflow**: Intelligent compression maintains narrative coherence

### Data Persistence:
- **Automatic Saving**: Context, characters, and world state auto-save
- **Recovery**: Robust loading with error recovery for corrupted data
- **Backup Strategy**: Multiple save points and rollback capability

## Performance Characteristics

### Optimizations:
- **Fast Startup**: Sub-5 second initialization
- **Response Time**: Sub-3 second response for standard interactions
- **Memory Efficiency**: Intelligent caching and compression
- **Token Efficiency**: Maximum narrative content within token limits

### Scalability:
- **Long Sessions**: Supports 50+ message conversations without degradation
- **Multiple Characters**: Efficient management of complex character relationships
- **Large Worlds**: Handles extensive world building with consistency checking

## Extension Points

### Custom Scenarios:
```python
# Create custom scenario
scenario = scenario_loader.create_custom_scenario(
    name="My Scenario",
    description="Custom roleplay scenario", 
    setting="fantasy",
    characters={...},
    world_rules=[...]
)
```

### Custom Event Handlers:
```python
# Register custom outcome handler
event_system.register_outcome_handler(
    "custom_outcome",
    my_custom_handler_function
)
```

### Custom Personality Traits:
```python
# Extend personality engine
personality_profile = personality_engine.create_personality_profile(
    traits={"custom_trait": 0.8},
    background_factors=["custom_background"]
)
```

This architecture provides a robust, extensible foundation for creating sophisticated AI-driven roleplay experiences that maintain narrative coherence and character consistency across extended interactions.