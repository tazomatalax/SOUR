from abc import ABC, abstractmethod
from typing import Optional
from ..config.config_manager import ConfigManager

class Feature(ABC):
    def __init__(self, feature_name: str):
        self.feature_name = feature_name
        self.config = ConfigManager()
        self._enabled = self.config.is_feature_enabled(feature_name)
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled
    
    def enable(self):
        """Enable the feature."""
        if not self._enabled:
            self._enabled = True
            self.on_enable()
    
    def disable(self):
        """Disable the feature."""
        if self._enabled:
            self._enabled = False
            self.on_disable()
    
    @abstractmethod
    def on_enable(self):
        """Called when feature is enabled."""
        pass
    
    @abstractmethod
    def on_disable(self):
        """Called when feature is disabled."""
        pass
    
    def get_config(self, key: str, default: Optional[any] = None) -> any:
        """Get feature-specific configuration."""
        return self.config.get(f"{self.feature_name}.{key}", default)
