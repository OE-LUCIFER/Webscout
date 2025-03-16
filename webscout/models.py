import importlib
import pkgutil
from typing import Dict, List, Any, Union
from webscout.AIbase import Provider, TTSProvider

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

class _TTSModels:
    """
    A class for managing TTS provider voices in the webscout package.
    """
    
    def list(self) -> Dict[str, List[str]]:
        """
        Gets all available voices from each TTS provider that has an all_voices attribute.
        
        Returns:
            Dictionary mapping TTS provider names to their available voices
        """
        return self._get_tts_voices()
    
    def get(self, provider_name: str) -> Union[List[str], Dict[str, str]]:
        """
        Gets all available voices for a specific TTS provider.
        
        Args:
            provider_name: The name of the TTS provider
            
        Returns:
            List or Dictionary of available voices for the provider
        """
        all_voices = self._get_tts_voices()
        return all_voices.get(provider_name, [])
    
    def summary(self) -> Dict[str, Any]:
        """
        Returns a summary of available TTS providers and voices.
        
        Returns:
            Dictionary with provider and voice counts
        """
        provider_voices = self._get_tts_voices()
        total_providers = len(provider_voices)
        
        # Count voices, handling both list and dict formats
        total_voices = 0
        provider_voice_counts = {}
        
        for provider, voices in provider_voices.items():
            if isinstance(voices, dict):
                count = len(voices)
            elif isinstance(voices, (list, tuple, set)):
                count = len(voices)
            else:
                count = 1
                
            total_voices += count
            provider_voice_counts[provider] = count
        
        return {
            "providers": total_providers,
            "voices": total_voices,
            "provider_voice_counts": provider_voice_counts
        }
    
    def _get_tts_voices(self) -> Dict[str, Union[List[str], Dict[str, str]]]:
        """
        Internal method to get all available voices from each TTS provider.
        
        Returns:
            Dictionary mapping TTS provider names to their available voices
        """
        provider_voices = {}
        
        try:
            # Import the TTS package specifically
            tts_package = importlib.import_module("webscout.Provider.TTS")
            
            # Iterate through TTS modules
            for _, module_name, _ in pkgutil.iter_modules(tts_package.__path__):
                try:
                    module = importlib.import_module(f"webscout.Provider.TTS.{module_name}")
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, TTSProvider) and attr != TTSProvider:
                            # TTS providers typically use 'all_voices' instead of 'AVAILABLE_MODELS'
                            if hasattr(attr, 'all_voices'):
                                voices = attr.all_voices
                                provider_voices[attr_name] = voices
                except Exception as e:
                    pass
        except Exception as e:
            pass
        
        return provider_voices

# Create singleton instances
llm = _LLMModels()
tts = _TTSModels()

# Container class for all model types
class Models:
    def __init__(self):
        self.llm = llm
        self.tts = tts

# Create a singleton instance
model = Models()
