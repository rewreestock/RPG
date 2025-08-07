"""Simple example demonstrating the RP system functionality."""

import os
import sys
from pathlib import Path

# Add the package to path for demo
sys.path.insert(0, str(Path(__file__).parent.parent))

from rp_system.core.gemini_client import GeminiClient
from rp_system.core.context_manager import ContextManager
from rp_system.core.memory_system import MemorySystem
from rp_system.scenarios.scenario_loader import ScenarioLoader
from rp_system.characters.character_system import CharacterSystem
from rp_system.world.world_state import WorldState
from rp_system.interface.config_manager import ConfigManager


def demo_basic_functionality():
    """Demonstrate basic RP system functionality without API calls."""
    print("=== RPG System Demo ===")
    print("Demonstrating core functionality without requiring API keys...\n")
    
    # 1. Configuration Management
    print("1. Configuration Management")
    config_manager = ConfigManager()
    print(f"   - Default max tokens: {config_manager.system_config.max_tokens:,}")
    print(f"   - Default scenario: {config_manager.session_config.scenario_type}")
    print(f"   - Search enabled: {config_manager.system_config.enable_search}")
    
    # 2. Scenario Loading
    print("\n2. Scenario System")
    scenario_loader = ScenarioLoader()
    available_scenarios = scenario_loader.list_available_scenarios()
    print(f"   - Available scenarios: {', '.join(available_scenarios)}")
    
    # Load Re:Zero scenario
    rezero_scenario = scenario_loader.load_scenario("rezero")
    print(f"   - Loaded scenario: {rezero_scenario.config.name}")
    print(f"   - Characters: {list(rezero_scenario.config.characters.keys())}")
    
    # 3. Character System
    print("\n3. Character Management")
    character_system = CharacterSystem()
    
    # Create characters from scenario
    for char_name, char_data in rezero_scenario.config.characters.items():
        character_system.create_character(
            name=char_name,
            description=char_data.get("description", ""),
            personality=char_data.get("personality", ""),
            background=char_data.get("background", "")
        )
    
    print(f"   - Created {len(character_system.characters)} characters")
    
    # Set up relationships
    character_system.set_character_relationship("Subaru", "Emilia", 0.9, "Deep love and devotion")
    character_system.set_character_relationship("Subaru", "Rem", 0.7, "Complex but caring relationship")
    character_system.set_character_relationship("Rem", "Ram", 0.8, "Twin sisters")
    
    print("   - Set up character relationships")
    
    # 4. World State Management
    print("\n4. World State System")
    world_state = WorldState()
    
    # Add locations
    world_state.add_location(
        "Roswaal Mansion",
        "A grand mansion in the countryside, home to Roswaal and his staff",
        location_type="mansion"
    )
    world_state.add_location(
        "Capital City",
        "The bustling capital of the Kingdom of Lugnica",
        location_type="city"
    )
    
    # Add world facts
    world_state.add_world_fact(
        "royal_selection",
        "The Kingdom of Lugnica is currently selecting a new ruler",
        category="politics",
        importance=0.9
    )
    
    print(f"   - Created {len(world_state.locations)} locations")
    print(f"   - Added {len(world_state.world_facts)} world facts")
    
    # 5. Memory System
    print("\n5. Memory System")
    memory_system = MemorySystem()
    
    # Add some memories
    memory_system.add_memory(
        "Subaru arrived in this world mysteriously",
        characters=["Subaru"],
        importance=1.0,
        tags=["origin", "mystery"]
    )
    
    memory_system.add_memory(
        "Emilia is a candidate in the royal selection",
        characters=["Emilia"],
        importance=0.9,
        tags=["politics", "royal"]
    )
    
    print(f"   - Added memories: {memory_system.get_stats()['total_memories']}")
    
    # 6. Context Management
    print("\n6. Context Management")
    context_manager = ContextManager(max_tokens=10000)  # Smaller for demo
    
    # Add scenario context
    system_prompt = rezero_scenario.build_context_prompt()
    
    # Add character sheets
    for character in character_system.characters.values():
        sheet = character_system.get_character_sheet(character.name)
        context_manager.set_character_sheet(character.name, sheet, len(sheet) // 4)
    
    # Add a conversation
    context_manager.add_message("User: Hello everyone, what's the situation?", 15)
    context_manager.add_message("AI: Subaru looks around the mansion's main hall...", 20)
    
    stats = context_manager.get_stats()
    print(f"   - Context tokens: {stats['total_tokens']:,}/{stats['max_tokens']:,}")
    print(f"   - Context segments: {sum(stats['segments'].values())}")
    
    # 7. Full Context Building
    print("\n7. Complete System Integration")
    full_context = context_manager.build_context(system_prompt)
    print(f"   - Generated complete context: {len(full_context):,} characters")
    print(f"   - Context includes character sheets, world state, and conversation history")
    
    print("\n=== Demo Complete ===")
    print("The RP system is ready for use with a Gemini API key!")
    print("\nTo use the full system:")
    print("1. Set GEMINI_API_KEY environment variable")
    print("2. Run: python -m rp_system.main --scenario rezero")
    print("3. Start chatting with the AI!")


def demo_with_api():
    """Demonstrate with actual API calls (requires API key)."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("No GEMINI_API_KEY found. Skipping API demo.")
        return
    
    print("\n=== API Demo ===")
    print("Testing actual Gemini API integration...\n")
    
    try:
        # Initialize Gemini client
        gemini_client = GeminiClient(api_key=api_key)
        
        # Test health check
        is_healthy = gemini_client.is_healthy()
        print(f"API Health Check: {'✓ Passed' if is_healthy else '✗ Failed'}")
        
        if is_healthy:
            # Test token counting
            test_text = "This is a test message for token counting."
            tokens = gemini_client.count_tokens(test_text)
            print(f"Token count test: '{test_text}' = {tokens} tokens")
            
            # Test simple generation
            response = gemini_client.generate_response(
                "Please respond with exactly: 'RP System test successful!'",
                max_tokens=20,
                temperature=0.1
            )
            
            print(f"Generation test: {response.text}")
            print(f"Token usage: {response.usage}")
        
    except Exception as e:
        print(f"API demo failed: {e}")


if __name__ == "__main__":
    demo_basic_functionality()
    demo_with_api()