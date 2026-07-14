"""Web fetch tool."""

from pathlib import Path

from .registry import ToolDefinition


class WebFetchTool:
    """Tool for fetching web content."""

    @staticmethod
    def definition(workspace: Path) -> ToolDefinition:
        async def _fetch(url: str, format: str = "markdown", timeout: int = 30) -> str:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers={
                        "User-Agent": "TheBigBos/1.0",
                    })
                    response.raise_for_status()
                    text = response.text[:50000]

                    if format == "markdown":
                        try:
                            from markdown_it import MarkdownIt
                            md = MarkdownIt()
                            text = md.render(text)
                        except ImportError:
                            pass

                    return text
            except Exception as e:
                return f"Error fetching {url}: {e}"

        return ToolDefinition(
            name="webfetch",
            description="Fetch content from a URL. Returns text, markdown, or HTML.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch content from",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["text", "markdown", "html"],
                        "description": "Format to return (default: markdown)",
                        "default": "markdown",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 30)",
                        "default": 30,
                    },
                },
                "required": ["url"],
            },
            handler=_fetch,
            read_only=True,
        )
