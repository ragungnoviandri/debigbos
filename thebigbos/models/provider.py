"""Abstract model provider and data types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ToolCall:
    """A tool call from the model."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Result from executing a tool."""
    tool_call_id: str
    name: str
    output: str
    error: str | None = None


@dataclass
class Message:
    """A conversation message."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ModelResponse:
    """Response from a model call."""
    content: str = ""
    reasoning_content: str = ""  # Thinking/reasoning from DeepSeek, o1/o3, Claude
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class ModelOptions:
    """Options for a model call."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    reasoning_effort: str | None = None
    thinking_budget: int | None = None


class ModelProvider(ABC):
    """Abstract base for all model providers."""

    name: str = "base"

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        options: ModelOptions | None = None,
    ) -> ModelResponse:
        """Send messages to the model and get a response."""
        ...

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        options: ModelOptions | None = None,
    ):
        """Stream responses from the model."""
        ...

    def count_tokens(self, messages: list[Message]) -> int:
        """Estimate token count for a list of messages."""
        return sum(len(m.content.split()) * 1.3 for m in messages)

    def get_context_window(self, model: str) -> int:
        """Return the context window size (in tokens) for a given model.
        
        Subclasses can override this with provider-specific values.
        """
        return _MODEL_CONTEXT_WINDOWS.get(model, 128000)

    async def fetch_models(self) -> list[str]:
        """Fetch available models from the provider's API.
        
        Override in subclasses that support model listing via API.
        Default returns empty list — provider uses hardcoded config models.
        """
        return []


# ——— Known model context windows (in tokens) ———
_MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    # OpenAI
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-5": 128000,
    "gpt-5.1": 128000,
    "gpt-5.1-codex": 128000,
    "gpt-5.2": 128000,
    "o3-mini": 200000,
    "o1": 200000,
    "o4-mini": 200000,
    # Anthropic
    "claude-sonnet-4-20250514": 200000,
    "claude-opus-4-20250514": 200000,
    "claude-opus-4.5": 200000,
    "claude-sonnet-4.5": 200000,
    "claude-3-5-sonnet-20241022": 200000,
    "claude-3-opus-20240229": 200000,
    "claude-3-haiku-20240307": 200000,
    # DeepSeek (via OpenCode)
    "deepseek-v4-pro": 1000000,
    "deepseek-v4-flash": 1000000,
    "deepseek-v3": 128000,
    "deepseek-v3.2": 1000000,
    "deepseek-r1": 128000,
    "deepseek-r1-0528": 1000000,
    "deepseek-r1-distill-llama-70b": 128000,
    # Qwen (via OpenCode)
    "qwen-plus": 131072,
    "qwen-max": 131072,
    "qwen3.5-397b": 131072,
    "qwen3.5-plus": 131072,
    "qwen3.6-plus": 131072,
    "qwen3.7-plus": 131072,
    "qwen3.7-max": 131072,
    "qwen2.5": 131072,
    # Kimi (via OpenCode)
    "kimi-k2": 131072,
    "kimi-k2.5": 131072,
    "kimi-k2.6": 131072,
    "kimi-k2.7-code": 131072,
    # GLM (via OpenCode)
    "glm-4": 131072,
    "glm-5": 131072,
    "glm-5.1": 131072,
    "glm-5.2": 131072,
    "glm5": 131072,  # legacy alias
    # MiniMax (via OpenCode)
    "minimax-m1": 1000000,
    "minimax-m2.5": 1000000,
    "minimax-m2.7": 1000000,
    "minimax-m3": 1000000,
    # Mimo (via OpenCode)
    "mimo-v2": 131072,
    "mimo-v2-pro": 131072,
    "mimo-v2-omni": 131072,
    "mimo-v2.5": 131072,
    "mimo-v2.5-pro": 131072,
    # Hy (via OpenCode)
    "hy3-preview": 131072,
    # Mistral
    "mistral-large-3": 131072,
    # Gemini
    "gemini-2.5-pro": 1048576,
    "gemini-2.5-flash": 1048576,
    "gemini-3-pro": 1048576,
    # Groq
    "llama-3.1-70b": 128000,
    "llama-3.3-70b": 128000,
    "mixtral-8x7b": 32000,
    "gemma2-9b": 8192,
    # Ollama local
    "llama3.1": 128000,
    "qwen2.5": 128000,
    "codellama": 16384,
    "phi3": 4096,
}
