# RPG Roleplay System

A production-ready, extensible roleplay system using Gemini Flash 2.5's full 1M token context window for superior RP experiences through intelligent context management and dynamic world simulation.

## Features

- **Intelligent Context Management**: Optimizes 1M token context window preserving character personalities, world state, and conversation flow
- **Multi-Character Support**: Distinct personalities with relationship tracking and consistent voice across long sessions
- **Smart Web Search**: Contextual search for character lore, world-building facts, and technical details
- **Dynamic Scenarios**: Fully customizable via JSON/YAML configs with easy mid-session switching
- **Built-in Presets**: Re:Zero, Fantasy, Modern Supernatural, Sci-Fi, and Historical scenarios

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd RPG

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Setup

1. Set your Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
GEMINI_API_KEY=your-api-key-here
```

2. Run the system:
```bash
rp-system
```

### Basic Usage

```bash
# Start with a built-in scenario
rp-system --scenario rezero

# Start with custom configuration
rp-system --config my_scenario.yaml

# Resume a saved session
rp-system --load my_session.json
```

## Architecture

```
rp_system/
├── core/
│   ├── gemini_client.py      # API wrapper with retry logic
│   ├── context_manager.py    # Smart context window management
│   ├── memory_system.py      # Long-term memory & summarization
│   └── search_integration.py # Contextual web search
├── scenarios/
│   ├── base_scenario.py      # Abstract scenario class
│   ├── scenario_loader.py    # Dynamic scenario loading
│   └── presets/             # Built-in scenario configurations
├── characters/
│   ├── character_system.py   # Character state management
│   └── personality_engine.py # Consistent character behavior
├── world/
│   ├── world_state.py        # Dynamic world simulation
│   └── event_system.py       # Plot progression & random events
└── interface/
    ├── cli_interface.py      # Clean command-line interface
    └── config_manager.py     # Runtime customization
```

## Configuration

The system supports extensive customization through YAML configuration files. See `docs/configuration.md` for detailed options.

## Contributing

1. Follow the established architecture patterns
2. Include type hints and comprehensive error handling
3. Write tests for new functionality
4. Maintain the focus on production-ready, robust code

## License

MIT License - see LICENSE file for details.