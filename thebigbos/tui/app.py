"""TheBigBos TUI Application — main Textual App.

Architecture (OpenCode-inspired):
  - Plugin system with lifecycle hooks
  - Route-based screen navigation
  - Slot system for widget injection
  - Keymap layers for keybindings
  - Theme management with JSON tokens
  - Dialog components (Alert, Confirm, Prompt, Select)

Usage:
    from thebigbos.tui.app import BigBosApp, run_app
    await run_app("/path/to/workspace")
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from .plugin import PluginManager, TuiPlugin, TuiPluginApi
from .routes import RouteRegistry
from .slots import SlotRegistry
from .keymap import KeymapRegistry
from .theme import ThemeManager
from .screens.home import HomeScreen
from .screens.welcome import WelcomeScreen


class BigBosApp(App[Any]):
    """Main TheBigBos Textual application."""

    CSS = """
    Screen {
        background: #0d0d0d;
    }

    #main-area {
        width: 3fr;
        height: 100%;
        border-right: solid #00d4ff;
    }

    #sidebar {
        width: 1fr;
        height: 100%;
        padding: 1;
        background: #1a1a2e;
    }

    #sidebar-info {
        height: auto;
        color: #e0e0e0;
    }

    #response-area {
        height: 5fr;
        padding: 1 2;
        background: #0d0d0d;
        color: #e0e0e0;
        border: none;
    }

    #tool-log {
        height: auto;
        max-height: 6;
        padding: 1 2;
        background: #12122a;
        border-top: solid #00d4ff;
        color: #888899;
    }

    #tool-log.hidden {
        display: none;
    }

    #prompt-area {
        height: auto;
        padding: 1 2;
        background: #1a1a2e;
        border-top: solid #00d4ff;
    }

    #prompt-input {
        width: 1fr;
        height: auto;
        min-height: 3;
        max-height: 12;
        border: solid #333355;
        background: #0d0d0d;
        color: #e0e0e0;
        padding: 0 1;
    }

    #send-btn {
        min-width: 10;
        height: 3;
    }

    /* Sidebar widget */
    SidebarWidget {
        padding: 1;
    }

    #sidebar-session-label {
        padding: 0 1;
        margin-top: 1;
    }

    #session-select {
        margin: 0 1;
        width: 100%;
    }

    /* Dialog styling */
    DialogAlert > Center,
    DialogConfirm > Center,
    DialogPrompt > Center,
    DialogSelect > Center {
        background: #1a1a2e;
        border: thick #00d4ff;
        padding: 1 2;
    }

    /* Scrollbar */
    Scrollbar {
        scrollbar-color: #333355;
        scrollbar-color-hover: #444466;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "command_palette", "Palette"),
    ]

    def __init__(
        self,
        workspace: Path | None = None,
        agent: Any = None,
        driver_class: Any = None,
        css_path: Any = None,
        watch_css: bool = False,
    ) -> None:
        super().__init__(driver_class=driver_class, css_path=css_path, watch_css=watch_css)
        self.workspace = workspace or Path.cwd()
        self.agent = agent

        # Plugin system
        self.plugin_manager = PluginManager()

        # Theme tokens (not to be confused with Textual's theme reactive)
        self._theme_tokens = ThemeManager.current()

    def compose(self) -> ComposeResult:
        """Build the app shell."""
        yield Header(show_clock=True, name="TheBigBos", icon="🦾")
        yield Footer()

    async def on_mount(self) -> None:
        """Called when app is mounted. Init agent, show welcome, then home."""
        # Create and initialize agent
        if not self.agent:
            from ..core.agent import BigBosAgent
            self.agent = BigBosAgent(self.workspace)
            await self.agent.initialize()

        # Show welcome screen first
        welcome = WelcomeScreen(agent=self.agent, workspace=self.workspace)
        self.push_screen(welcome)

    async def _load_plugins(self) -> None:
        """Load plugins from config."""
        # Look for tui.json plugins config
        config_path = self.workspace / "thebigbos.json"
        if config_path.exists():
            import json
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                plugins_config = config.get("tui", {}).get("plugins", [])
                for plugin_cfg in plugins_config:
                    # For now, plugins are loaded via config
                    pass
            except Exception:
                pass

    def action_command_palette(self) -> None:
        """Show command palette."""
        self.notify("Command palette — coming soon!", title="Palette")


async def run_app(
    workspace: str | Path = ".",
    agent: Any = None,
) -> None:
    """Run the TheBigBos TUI application.

    Args:
        workspace: Path to project workspace
        agent: BigBosAgent instance (or None for headless)
    """
    ws = Path(workspace).resolve()

    app = BigBosApp(workspace=ws, agent=agent)

    # Apply theme early
    ThemeManager._apply_theme(app)

    await app.run_async()


# Legacy compatibility wrapper
class BigBosTUI:
    """Legacy wrapper for the Textual-based TUI. Maintains the old interface."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()
        self.agent = None
        self.show_raw = False

    async def run(self) -> None:
        """Start the TUI."""
        await run_app(str(self.workspace), self.agent)
