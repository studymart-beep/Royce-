from ai.providers.base import BaseProvider
from ai.providers.gemini import GeminiProvider
from ai.providers.groq import GroqProvider
from ai.providers.cerebras import CerebrasProvider

PROVIDER_REGISTRY = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "cerebras": CerebrasProvider,
}


def build_provider_instances() -> dict:
    """Return name -> provider instance (stateless)."""
    return {name: cls() for name, cls in PROVIDER_REGISTRY.items()}
