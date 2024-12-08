import os
import yaml
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'config'):
            self.config_path = Path(__file__).parent / 'default_config.yaml'
            self.config = self._load_config()
            self._override_from_env()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def _override_from_env(self):
        """Override configuration with environment variables."""
        env_prefix = "BIOREACTOR_"
        for key in os.environ:
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                self._set_nested_config(config_key.split('_'), os.environ[key])
    
    def _set_nested_config(self, key_parts: list, value: str):
        """Set nested configuration value."""
        current = self.config
        for part in key_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[key_parts[-1]] = self._convert_value(value)
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        try:
            value = self.config
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return self.get(f'features.{feature_name}', False)
    
    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        self._override_from_env()
