import logging
from typing import Dict, Type, Optional
from .feature import Feature

logger = logging.getLogger(__name__)

class FeatureRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_features'):
            self._features: Dict[str, Feature] = {}
            self._feature_classes: Dict[str, Type[Feature]] = {}
    
    def register_feature_class(self, feature_name: str, feature_class: Type[Feature]):
        """Register a feature class for later instantiation."""
        self._feature_classes[feature_name] = feature_class
        logger.info(f"Registered feature class: {feature_name}")
    
    def get_feature(self, feature_name: str) -> Optional[Feature]:
        """Get an instance of a feature by name."""
        return self._features.get(feature_name)
    
    def initialize_feature(self, feature_name: str, **kwargs) -> Optional[Feature]:
        """Initialize a feature from its registered class."""
        if feature_name not in self._feature_classes:
            logger.error(f"No feature class registered for: {feature_name}")
            return None
            
        try:
            if feature_name not in self._features:
                feature_class = self._feature_classes[feature_name]
                feature = feature_class(**kwargs)
                self._features[feature_name] = feature
                logger.info(f"Initialized feature: {feature_name}")
            return self._features[feature_name]
        except Exception as e:
            logger.error(f"Error initializing feature {feature_name}: {e}")
            return None
    
    def enable_feature(self, feature_name: str) -> bool:
        """Enable a feature by name."""
        feature = self.get_feature(feature_name)
        if feature:
            feature.enable()
            return True
        return False
    
    def disable_feature(self, feature_name: str) -> bool:
        """Disable a feature by name."""
        feature = self.get_feature(feature_name)
        if feature:
            feature.disable()
            return True
        return False
    
    def cleanup(self):
        """Clean up all registered features."""
        for feature in self._features.values():
            try:
                feature.disable()
            except Exception as e:
                logger.error(f"Error cleaning up feature: {e}")
        self._features.clear()
