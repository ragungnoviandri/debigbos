"""Welcome/splash screen — OpenCode-style centered layout."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Static


class WelcomeScreen(Screen[Any]):
    """Welcome screen shown on startup — OpenCode-style centered layout."""

    def __init__(
        self,
        agent: Any = None,
        workspace: Path | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._agent = agent
        self._workspace = workspace
        self._sessions: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Label("")
            yield Label("")
            banner = r"""[bold #fab283]
                 _  __   ____  _       ____
              __|_|/_/  | __ )(_) __ _| __ )  ___  ___
             / _  |     |  _ \| |/ _` |  _ \ / _ \/ __|
            | |_| |     | |_) | | (_| | |_) | (_) \__ \   _   _   _
             \__|_|     |____/|_|\__, |____/ \___/|___/  |_| |_| |_|
                                 |___/

[/bold #fab283]"""
            yield Label(banner)
            yield Label("")
            yield Label("")

            if self._agent:
                p = self._agent.config.active_provider
                m = self._agent.config.active_model
                yield Label(f"  [dim]d' BigBos...[/dim]")
                yield Label(f"  [bold #fab283]{self._agent.config.mode.upper()}[/bold #fab283]  [secondary]{p}[/secondary]/[primary]{m}[/primary]  [dim]{self._workspace}[/dim]")
                yield Label("")

            yield Label("  [dim]Type /help for commands  •  Ctrl+Q to quit  •  Enter to start[/dim]")
            yield Label("")

            if self._agent:
                sessions = self._agent.memory.list_sessions(limit=5)
                if sessions:
                    yield Label("  [bold]Recent Sessions:[/bold]")
                    for s in sessions[:5]:
                        title = (s.get("title") or "Untitled")[:50]
                        src = f" [{s.get('source', '')}]" if s.get("source") else ""
                        yield Label(f"    • [cyan]{title}[/cyan]{src}")

        yield Footer()

    def on_mount(self) -> None:
        if self._agent:
            self._agent._ensure_sessions_imported()
            self._sessions = self._agent.memory.list_sessions(limit=30)

        try:
            from ...core.updater import Updater
            u = Updater()
            new_ver = u.check()
            if new_ver:
                self.app.notify(
                    f"Update v{new_ver} available! Run 'thebigbos update'",
                    title="TheBigBos",
                    timeout=10
                )
        except Exception:
            pass

    def on_key(self, event) -> None:
        if hasattr(event, 'key') and event.key not in ("ctrl+q",):
            self._go_home()

    def _go_home(self) -> None:
        from .home import HomeScreen
        home = HomeScreen(agent=self._agent, workspace=self._workspace)
        self.app.push_screen(home)

    def on_click(self, event) -> None:
        if hasattr(event, 'button') and event.button == 1:
            self._go_home() 