"""Provider registry — manages all model providers."""

from typing import Any

from ..config.manager import Config, ProviderConfig
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .opencode_provider import OpencodeGoProvider
from .ollama_provider import OllamaProvider
from .provider import Message, ModelOptions, ModelProvider, ModelResponse


class ProviderRegistry:
    """Registry of all available model providers."""

    def __init__(self, config: Config):
        self.config = config
        self._providers: dict[str, ModelProvider] = {}

    async def initialize(self) -> None:
        """Initialize configured providers."""
        for name, provider_cfg in self.config.providers.items():
            provider = self._create_provider(name, provider_cfg)
            if provider:
                self._providers[name] = provider

    def _create_provider(self, name: str, cfg: ProviderConfig) -> ModelProvider | None:
        """Create a provider instance from config."""
        if name == "openai":
            return OpenAIProvider(cfg)
        elif name == "anthropic":
            return AnthropicProvider(cfg)
        elif name == "ollama":
            return OllamaProvider(cfg)
        elif name == "opencode-go":
            return OpencodeGoProvider(cfg)
        elif name in ("openrouter", "groq", "deepseek", "together"):
            return OpenAIProvider(cfg)
        return None

    def get(self, name: str | None = None) -> ModelProvider | None:
        """Get a provider by name, or the active provider."""
        name = name or self.config.active_provider
        return self._providers.get(name)

    @property
    def active(self) -> ModelProvider | None:
        """Get the currently active provider."""
        return self.get(self.config.active_provider)

    @property
    def active_model(self) -> str:
        """Get the currently active model ID."""
        return self.config.active_model

    def list_providers(self) -> list[str]:
        """List all available provider names."""
        return list(self._providers.keys())

    def list_models(self, provider_name: str | None = None) -> list[str]:
        """List models for a provider."""
        provider_name = provider_name or self.config.active_provider
        if cfg := self.config.providers.get(provider_name):
            return cfg.models
        return []

    def build_tool_schemas(self, tool_definitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert internal tool definitions to provider-specific format."""
        schemas = []
        for tool in tool_definitions:
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {"type": "object", "properties": {}, "required": []}),
                },
            })
        return schemas
