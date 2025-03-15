import importlib
import pkgutil
from typing import Dict, List, Any, Union, Optional
from webscout.AIbase import Provider

class _LLMModels:
    """
    A class for managing LLM provider models in the webscout package.
    """
    
    def list(self) -> Dict[str, List[str]]:
        """
        Gets all available models from each provider that has an AVAILABLE_MODELS attribute.
        
        Returns:
            Dictionary mapping provider names to their available models
        """
        return self._get_provider_models()
    
    def get(self, provider_name: str) -> List[str]:
        """
        Gets all available models for a specific provider.
        
        Args:
            provider_name: The name of the provider
            
        Returns:
            List of available models for the provider
        """
        all_models = self._get_provider_models()
        return all_models.get(provider_name, [])
    
    def summary(self) -> Dict[str, int]:
        """
        Returns a summary of available providers and models.
        
        Returns:
            Dictionary with provider and model counts
        """
        provider_models = self._get_provider_models()
        total_providers = len(provider_models)
        total_models = sum(len(models) if isinstance(models, (list, tuple, set)) 
                          else 1 for models in provider_models.values())
        
        return {
            "providers": total_providers,
            "models": total_models,
            "provider_model_counts": {
                provider: len(models) if isinstance(models, (list, tuple, set)) else 1
                for provider, models in provider_models.items()
            }
        }
    
    def _get_provider_models(self) -> Dict[str, List[str]]:
        """
        Internal method to get all available models from each provider.
        
        Returns:
            Dictionary mapping provider names to their available models
        """
        provider_models = {}
        provider_package = importlib.import_module("webscout.Provider")
        
        for _, module_name, _ in pkgutil.iter_modules(provider_package.__path__):
            try:
                module = importlib.import_module(f"webscout.Provider.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Provider) and attr != Provider:
                        if hasattr(attr, 'AVAILABLE_MODELS'):
                            # Convert any sets to lists to ensure serializability
                            models = attr.AVAILABLE_MODELS
                            if isinstance(models, set):
                                models = list(models)
                            provider_models[attr_name] = models
            except Exception:
                pass
        
        return provider_models

# Create a singleton instance for LLM models
llm = _LLMModels()

# Container class for all model types
class Models:
    def __init__(self):
        self.llm = llm

# Create a singleton instance
model = Models()
