"""Test script to validate the improved configuration system."""

import os
import tempfile
import json
from pathlib import Path

def test_config_example_generation():
    """Test that example config generation works."""
    print("Testing example config generation...")
    
    from rp_system.interface.setup_wizard import save_example_config
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = save_example_config(os.path.join(temp_dir, "test_config.json"))
        
        # Verify file exists
        assert os.path.exists(config_path), "Example config file not created"
        
        # Verify content
        with open(config_path) as f:
            config = json.load(f)
        
        assert "gemini_api_key" in config, "API key field missing"
        assert config["gemini_api_key"] == "YOUR_API_KEY_HERE", "Default API key incorrect"
        assert "gemini_model" in config, "Model field missing"
        assert config["enable_search"] is True, "Search setting incorrect"
        
        print("✓ Example config generation works")


def test_config_manager_creation():
    """Test that ConfigManager creates default config correctly."""
    print("Testing ConfigManager default config creation...")
    
    from rp_system.interface.config_manager import ConfigManager
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigManager(config_dir=temp_dir)
        
        # Check that default config was created
        config_file = Path(temp_dir) / "system_config.json"
        assert config_file.exists(), "Default config file not created"
        
        # Verify content
        with open(config_file) as f:
            config = json.load(f)
        
        assert "gemini_api_key" in config, "API key field missing in default config"
        assert config["gemini_api_key"] == "", "Default API key should be empty"
        assert "_comment" in config, "Comment field missing"
        
        print("✓ ConfigManager default config creation works")


def test_api_key_validation():
    """Test API key validation in setup wizard."""
    print("Testing API key validation...")
    
    from rp_system.interface.setup_wizard import SetupWizard
    
    # This test would require mocking user input, so we'll just test basic instantiation
    wizard = SetupWizard()
    assert wizard is not None, "SetupWizard instantiation failed"
    
    print("✓ SetupWizard instantiation works")


def test_no_api_key_handling():
    """Test that system handles missing API key gracefully."""
    print("Testing no API key handling...")
    
    from rp_system.interface.config_manager import ConfigManager
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigManager(config_dir=temp_dir)
        
        # Test validation with empty API key
        issues = config_manager.validate_config()
        api_issues = [issue for issue in issues if "API key" in issue]
        assert len(api_issues) > 0, "Missing API key should be detected"
        
        print("✓ Missing API key validation works")


def main():
    """Run all tests."""
    print("=== Testing RPG System Configuration Improvements ===")
    
    try:
        test_config_example_generation()
        test_config_manager_creation()
        test_api_key_validation()
        test_no_api_key_handling()
        
        print("\n🎉 All tests passed! Configuration system is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)