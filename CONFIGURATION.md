# Configuration Guide

The RPG System uses a config file-based approach for managing API keys and settings, making it much easier to set up and use.

## Quick Setup

### Option 1: Interactive Setup Wizard (Recommended)
```bash
rp-system --setup
```
This will guide you through setting up your API key and preferences with a user-friendly wizard.

### Option 2: Quick API Key Setup
```bash
rp-system --api-key "your-gemini-api-key-here"
```

### Option 3: Manual Configuration
1. Create an example config file:
```bash
rp-system --create-example-config my_config.json
```

2. Edit the file and set your API key:
```json
{
  "gemini_api_key": "your-actual-api-key-here",
  "gemini_model": "gemini-2.0-flash-exp",
  "enable_search": true
}
```

3. Copy to the config directory:
```bash
mkdir -p rp_config
cp my_config.json rp_config/system_config.json
```

## Getting Your API Key

1. Go to [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key (it starts with "AI")

## Configuration File Location

The system stores configuration in:
- **Config directory**: `rp_config/`
- **System config**: `rp_config/system_config.json`
- **Session config**: `rp_config/session_config.json`

## Configuration Options

### System Configuration (`system_config.json`)
```json
{
  "gemini_api_key": "your-api-key",
  "gemini_model": "gemini-2.0-flash-exp",
  "max_tokens": 950000,
  "enable_search": true,
  "storage_base_path": "rp_data",
  "log_level": "INFO"
}
```

### Key Settings
- **gemini_api_key**: Your Google Gemini API key (required)
- **gemini_model**: AI model to use (gemini-2.0-flash-exp, gemini-1.5-pro, etc.)
- **max_tokens**: Maximum context window size
- **enable_search**: Enable web search for character lore
- **storage_base_path**: Where to store game data
- **log_level**: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Troubleshooting

### "API key not set" Error
Run the setup wizard: `rp-system --setup`

### "API connection test failed" Warning
1. Check your internet connection
2. Verify your API key is correct
3. Check if you have API quota remaining

### Config File Issues
1. Delete the config directory: `rm -rf rp_config/`
2. Run setup again: `rp-system --setup`

## Environment Variables (Fallback)

The system also supports environment variables as fallback:
```bash
export GEMINI_API_KEY="your-api-key"
export GEMINI_MODEL="gemini-2.0-flash-exp"
```

However, config files are the recommended approach as they're easier to manage and persist across sessions.