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
