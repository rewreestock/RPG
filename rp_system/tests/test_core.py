"""Basic tests for the RP system components."""

import unittest
from unittest.mock import Mock, patch
import tempfile
import shutil
from pathlib import Path

from ..core.context_manager import ContextManager, ContextSegment
from ..core.memory_system import MemorySystem, MemoryEntry
from ..scenarios.scenario_loader import ScenarioLoader
from ..characters.character_system import CharacterSystem
from ..world.world_state import WorldState
from ..interface.config_manager import ConfigManager


class TestContextManager(unittest.TestCase):
    """Test context management functionality."""
    
    def setUp(self):
        self.context_manager = ContextManager(max_tokens=1000)
    
    def test_add_message(self):
        """Test adding a message to context."""
        self.context_manager.add_message("Test message", 10)
        self.assertEqual(len(self.context_manager.recent_context), 1)
        self.assertEqual(self.context_manager.recent_context[0].content, "Test message")
    
    def test_token_counting(self):
        """Test token counting and limits."""
        self.context_manager.add_message("Message 1", 300)
        self.context_manager.add_message("Message 2", 300)
        self.context_manager.add_message("Message 3", 500)
        
        # Check that tokens are tracked correctly
        total_tokens = self.context_manager._total_tokens()
        self.assertEqual(total_tokens, 1100)  # Should have all the tokens
        
        # Test that compression can be triggered manually
        self.context_manager._compress_context()
        # After compression, should still have the recent messages preserved
        self.assertGreater(len(self.context_manager.recent_context), 0)
    
    def test_character_sheet_priority(self):
        """Test that character sheets are preserved."""
        self.context_manager.set_character_sheet("TestChar", "Character description", 100)
        
        # Add lots of messages to trigger compression
        for i in range(20):
            self.context_manager.add_message(f"Message {i}", 50)
        
        # Character sheet should still be there
        self.assertEqual(len(self.context_manager.character_sheets), 1)
        self.assertEqual(self.context_manager.character_sheets[0].characters[0], "TestChar")


class TestMemorySystem(unittest.TestCase):
    """Test memory system functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_system = MemorySystem(storage_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_add_memory(self):
        """Test adding memories."""
        memory = self.memory_system.add_memory(
            "Test memory content",
            characters=["Alice"],
            importance=0.8
        )
        
        self.assertIsNotNone(memory)
        self.assertEqual(memory.content, "Test memory content")
        self.assertIn("Alice", memory.characters)
        self.assertEqual(memory.importance, 0.8)
    
    def test_retrieve_memories(self):
        """Test memory retrieval."""
        # Add some memories
        self.memory_system.add_memory("Memory about Alice", characters=["Alice"], importance=0.7)
        self.memory_system.add_memory("Memory about Bob", characters=["Bob"], importance=0.5)
        self.memory_system.add_memory("Important memory", importance=0.9)
        
        # Retrieve memories about Alice
        alice_memories = self.memory_system.retrieve_memories(characters=["Alice"])
        self.assertEqual(len(alice_memories), 1)
        self.assertIn("Alice", alice_memories[0].characters)
        
        # Retrieve important memories
        important_memories = self.memory_system.retrieve_memories(min_importance=0.8)
        self.assertEqual(len(important_memories), 1)
        self.assertEqual(important_memories[0].importance, 0.9)
    
    def test_memory_persistence(self):
        """Test that memories persist across sessions."""
        # Add a memory
        self.memory_system.add_memory("Persistent memory", importance=0.8)
        
        # Create new memory system with same storage
        new_memory_system = MemorySystem(storage_path=self.temp_dir)
        
        # Should have loaded the memory
        memories = new_memory_system.retrieve_memories()
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0].content, "Persistent memory")


class TestScenarioLoader(unittest.TestCase):
    """Test scenario loading functionality."""
    
    def setUp(self):
        self.scenario_loader = ScenarioLoader()
    
    def test_list_scenarios(self):
        """Test listing available scenarios."""
        scenarios = self.scenario_loader.list_available_scenarios()
        self.assertIsInstance(scenarios, list)
        self.assertIn("generic", scenarios)
    
    def test_load_generic_scenario(self):
        """Test loading generic scenario."""
        scenario = self.scenario_loader.load_scenario("generic")
        self.assertIsNotNone(scenario)
        self.assertEqual(scenario.config.setting, "generic")
    
    def test_create_custom_scenario(self):
        """Test creating custom scenario."""
        scenario = self.scenario_loader.create_custom_scenario(
            "Test Scenario",
            "A test scenario",
            setting="test"
        )
        
        self.assertEqual(scenario.config.name, "Test Scenario")
        self.assertEqual(scenario.config.setting, "test")


class TestCharacterSystem(unittest.TestCase):
    """Test character management functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.character_system = CharacterSystem(storage_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_character(self):
        """Test character creation."""
        character = self.character_system.create_character(
            "Alice",
            description="A brave adventurer",
            personality="Courageous and kind"
        )
        
        self.assertEqual(character.name, "Alice")
        self.assertEqual(character.description, "A brave adventurer")
        self.assertEqual(character.personality, "Courageous and kind")
    
    def test_character_relationships(self):
        """Test character relationship management."""
        # Create characters
        self.character_system.create_character("Alice")
        self.character_system.create_character("Bob")
        
        # Set relationship
        self.character_system.set_character_relationship("Alice", "Bob", 0.8, "They are friends")
        
        # Check relationship
        relationship = self.character_system.get_relationship("Alice", "Bob")
        self.assertEqual(relationship, 0.8)
        
        # Should be bidirectional
        reverse_relationship = self.character_system.get_relationship("Bob", "Alice")
        self.assertEqual(reverse_relationship, 0.8)
    
    def test_active_characters(self):
        """Test active character management."""
        # Create characters
        self.character_system.create_character("Alice")
        self.character_system.create_character("Bob")
        self.character_system.create_character("Charlie")
        
        # Set active characters
        self.character_system.set_active_characters(["Alice", "Bob"])
        
        active = self.character_system.get_active_characters()
        self.assertEqual(len(active), 2)
        self.assertEqual({char.name for char in active}, {"Alice", "Bob"})


class TestWorldState(unittest.TestCase):
    """Test world state management functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.world_state = WorldState(storage_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_add_location(self):
        """Test adding locations."""
        location = self.world_state.add_location(
            "Test Town",
            "A small test town",
            location_type="town"
        )
        
        self.assertEqual(location.name, "Test Town")
        self.assertEqual(location.type, "town")
    
    def test_character_movement(self):
        """Test character movement between locations."""
        # Add locations
        self.world_state.add_location("Town A", "First town")
        self.world_state.add_location("Town B", "Second town")
        
        # Move character
        success = self.world_state.move_character_to_location("Alice", "Town A")
        self.assertTrue(success)
        
        # Check character is there
        characters = self.world_state.get_characters_at_location("Town A")
        self.assertIn("Alice", characters)
        
        # Move to another location
        self.world_state.move_character_to_location("Alice", "Town B")
        
        # Should be removed from old location
        characters_a = self.world_state.get_characters_at_location("Town A")
        characters_b = self.world_state.get_characters_at_location("Town B")
        
        self.assertNotIn("Alice", characters_a)
        self.assertIn("Alice", characters_b)
    
    def test_world_facts(self):
        """Test world fact management."""
        fact = self.world_state.add_world_fact(
            "test_fact",
            "This is a test fact",
            importance=0.8
        )
        
        self.assertEqual(fact.content, "This is a test fact")
        self.assertEqual(fact.importance, 0.8)
        
        # Test retrieval
        important_facts = self.world_state.get_important_facts(min_importance=0.7)
        self.assertEqual(len(important_facts), 1)
        self.assertEqual(important_facts[0].id, "test_fact")


class TestConfigManager(unittest.TestCase):
    """Test configuration management functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(config_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_system_config_updates(self):
        """Test system configuration updates."""
        initial_tokens = self.config_manager.system_config.max_tokens
        
        self.config_manager.update_system_config({"max_tokens": 500000})
        
        self.assertEqual(self.config_manager.system_config.max_tokens, 500000)
        self.assertNotEqual(self.config_manager.system_config.max_tokens, initial_tokens)
    
    def test_session_config_updates(self):
        """Test session configuration updates."""
        self.config_manager.update_session_config({
            "scenario_type": "test_scenario",
            "response_length": "brief"
        })
        
        self.assertEqual(self.config_manager.session_config.scenario_type, "test_scenario")
        self.assertEqual(self.config_manager.session_config.response_length, "brief")
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Set invalid values
        self.config_manager.system_config.max_tokens = -1
        self.config_manager.session_config.nsfw_level = 10
        
        issues = self.config_manager.validate_config()
        self.assertTrue(len(issues) > 0)
        
        # Should have issues for negative tokens and invalid NSFW level
        self.assertTrue(any("tokens" in issue.lower() for issue in issues))
        self.assertTrue(any("nsfw" in issue.lower() for issue in issues))


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('rp_system.core.gemini_client.GeminiClient')
    def test_basic_scenario_flow(self, mock_gemini):
        """Test basic scenario loading and character interaction flow."""
        # Mock Gemini client
        mock_gemini.return_value.count_tokens.return_value = 10
        mock_gemini.return_value.is_healthy.return_value = True
        
        # Set up components
        config_manager = ConfigManager(config_dir=self.temp_dir)
        scenario_loader = ScenarioLoader()
        character_system = CharacterSystem(storage_path=self.temp_dir)
        context_manager = ContextManager()
        
        # Load a scenario
        scenario = scenario_loader.load_scenario("fantasy")
        self.assertIsNotNone(scenario)
        
        # Add characters from scenario
        for char_name, char_data in scenario.config.characters.items():
            character_system.create_character(
                name=char_name,
                description=char_data.get("description", ""),
                personality=char_data.get("personality", "")
            )
        
        # Set active characters
        character_system.set_active_characters(list(scenario.config.characters.keys()))
        
        # Add some context
        context_manager.add_message("Test user message", 10)
        system_prompt = scenario.build_context_prompt()
        context = context_manager.build_context(system_prompt)
        
        self.assertIsInstance(context, str)
        self.assertTrue(len(context) > 0)


if __name__ == "__main__":
    unittest.main()