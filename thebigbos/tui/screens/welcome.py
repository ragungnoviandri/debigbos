"""Welcome / splash screen — Hermes-style startup with banner, config, and tools overview."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Static


class WelcomeScreen(Screen[Any]):
    """Welcome screen shown on startup with banner, config, tools, and skills."""

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
        yield Header(show_clock=True, name="TheBigBos")
        with VerticalScroll():
            # Banner
            banner = r"""[bold cyan]
   _____ _         ____  _       ____
  |_   _| |__     | __ )(_) __ _| __ )  ___  ___
    | | | '_ \    |  _ \| |/ _` |  _ \ / _ \/ __|
    | | | | | |   | |_) | | (_| | |_) | (_) \__ \
    |_| |_| |_|   |____/|_|\__, |____/ \___/|___/
                            |___/
[/bold cyan]"""
            yield Label(banner)

            # Welcome line
            if self._agent:
                m = self._agent.config.active_model
                p = self._agent.config.active_provider
                yield Label(f"  [dim]AI Assistant with Soul, Memory & Skills  |  {p}/{m}[/dim]\n")

            # Config info + sessions
            if self._agent:
                provider = self._agent.config.active_provider
                model = self._agent.config.active_model
                soul = self._agent.soul.name
                skills = len(self._agent.skills.list_skills())
                providers = ", ".join(self._agent.providers.list_providers() or [provider])
                ws = str(self._workspace or ".")
                yield Label(f"  Model: {provider}/{model}  |  Soul: {soul}  |  Skills: {skills}  |  Workspace: {ws}\n")

                # Tools
                tools = self._agent.tools.get_tool_names()
                yield Label(f"  [bold]Tools:[/bold] {', '.join(tools[:10])}{' +' if len(tools) > 10 else ''}\n")

                # Skills list
                skill_list = self._agent.skills.list_skills()
                if skill_list:
                    skill_names = ", ".join(s["name"] for s in skill_list[:8])
                    yield Label(f"  [bold]Skills:[/bold] {skill_names}{' +' if len(skill_list) > 8 else ''}\n")

                # Sessions preview
                sessions = self._agent.memory.list_sessions(limit=5)
                if sessions:
                    yield Label("  [bold]Recent Sessions:[/bold]")
                    for s in sessions[:5]:
                        title = (s.get("title") or "Untitled")[:40]
                        src = f" [{s.get('source', '')}]" if s.get("source") else ""
                        yield Label(f"    - {title}{src}")
                yield Label("")

            yield Label("  [bold]Press any key to start — session created on first message[/bold]")
            yield Label("  /help for commands  |  Ctrl+Q to quit")

        yield Footer()

    def on_mount(self) -> None:
        """Check for updates and import sessions."""
        if self._agent:
            self._agent._ensure_sessions_imported()
            self._sessions = self._agent.memory.list_sessions(limit=30)

        # Check for updates in background
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
        """Any key advances to home."""
        if hasattr(event, 'key') and event.key not in ("ctrl+q",):
            self._go_home()

    def _go_home(self) -> None:
        """Transition to HomeScreen."""
        from .home import HomeScreen
        home = HomeScreen(agent=self._agent, workspace=self._workspace)
        self.app.push_screen(home)
