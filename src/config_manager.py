"""
Configuration Manager

Handles loading and managing application configuration.
"""

import json
import os
from pathlib import Path

class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_dir=None):
        """Initialize the configuration manager."""
        if config_dir is None:
            # Default to config directory relative to project root
            project_root = Path(__file__).parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.default_config_file = self.config_dir / "default.json"
        self.local_config_file = self.config_dir / "local.json"
    
    def load_config(self):
        """Load configuration from files."""
        config = {}
        
        # Load default configuration
        if self.default_config_file.exists():
            with open(self.default_config_file, 'r') as f:
                config = json.load(f)
        
        # Override with local configuration if it exists
        if self.local_config_file.exists():
            with open(self.local_config_file, 'r') as f:
                local_config = json.load(f)
                config = self._merge_configs(config, local_config)
        
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        return config
    
    def _merge_configs(self, base_config, override_config):
        """Merge two configuration dictionaries."""
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _apply_env_overrides(self, config):
        """Apply environment variable overrides."""
        # Example: SALE_TRACKER_DB_FILENAME overrides database.filename
        env_prefix = "SALE_TRACKER_"
        
        for env_var, value in os.environ.items():
            if env_var.startswith(env_prefix):
                # Convert env var to config path
                config_path = env_var[len(env_prefix):].lower().split('_')
                self._set_nested_value(config, config_path, value)
        
        return config
    
    def _set_nested_value(self, config, path, value):
        """Set a nested value in the configuration dictionary."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[path[-1]] = value
    
    def save_local_config(self, config):
        """Save configuration to local config file."""
        os.makedirs(self.config_dir, exist_ok=True)
        
        with open(self.local_config_file, 'w') as f:
            json.dump(config, f, indent=2)