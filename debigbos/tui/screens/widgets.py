"""Widget components for de BigBos TUI.

Classes moved here from home.py for modularity:
- VersionLabel (clickable version badge)
- ChatInput (multi-line prompt)
- StatusBar (3-column status)
- SidebarWidget (session info sidebar)
- ToolLogWidget (tool execution log)
- ShortcutsWidget (keyboard reference)
- ResponseArea (rich response output)
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, RichLog, Static, TextArea


# ── Helpers ─────────────────────────────────────────────

_MARKUP_TAG = re.compile(r"\[/?[^\]]*\]")


def strip_markup(text: str) -> str:
    """Strip Rich markup tags to get plain text length."""
    return _MARKUP_TAG.sub("", text)


# ── Messages ────────────────────────────────────────────

class UpdateAvailable(Message):
    """Posted when user clicks version label while update is available."""

    def __init__(self, new_version: str = "", changelog: str = "") -> None:
        super().__init__()
        self.new_version = new_version
        self.changelog = changelog


# ── Version Label ───────────────────────────────────────

class VersionLabel(Button):
    """Clickable version display — shows update dialog on click."""

    version: reactive[str] = reactive("")
    update_available: reactive[bool] = reactive(False)
    _latest_version: str = ""
    _changelog: str = ""

    def __init__(self, id: str | None = "sidebar-version", **kwargs):
        super().__init__(id=id, **kwargs)
        self.can_focus = True

    def on_button_pressed(self) -> None:
        """Always show version/update dialog on press."""
        if self.update_available:
            self.post_message(UpdateAvailable(self._latest_version, self._changelog))
        else:
            self.post_message(UpdateAvailable("", ""))  # Show "checking" or "up-to-date"

    def render(self) -> str:
        if self.update_available:
            dot = "[bold blue]●[/bold blue]"
        else:
            dot = "[bold green]●[/bold green]"
        return f" {dot} [dim]de BigBos {self.version}[/dim]"


# ── Chat Input ──────────────────────────────────────────

class ChatInput(TextArea):
    """Multi-line chat input. Enter=send, Ctrl+J=newline, ↑↓=history, max 3 rows."""

    BINDINGS = [
        ("ctrl+j", "insert_newline", "New Line"),
        ("ctrl+a", "select_all", "Select All"),
    ]

    def on_mount(self) -> None:
        self.styles.max_height = 6
        self._history_index: int = -1
        self._saved_input: str = ""

    def clear(self):
        """Clear text and undo history to prevent out-of-bounds undo crashes."""
        self._history_index = -1
        self._saved_input = ""
        result = super().clear()
        self.history.clear()
        return result

    def _get_user_messages(self) -> list[str]:
        """Collect user messages from the active session, newest first."""
        screen = self.screen
        if not hasattr(screen, 'agent') or not screen.agent:
            return []
        session = screen.agent.sessions.active if screen.agent.sessions else None
        if not session:
            return []
        seen = set()
        result = []
        for msg in reversed(session.messages):
            if msg.role == "user" and msg.content.strip():
                stripped = msg.content.strip()
                if stripped not in seen:
                    seen.add(stripped)
                    result.append(stripped)
        return result

    def _on_key(self, event) -> None:
        if event.key == "up":
            history = self._get_user_messages()
            if history:
                cursor_row = self.cursor_location[0]
                if self._history_index == -1 and cursor_row > 0:
                    super()._on_key(event)
                    return
                if self._history_index == -1:
                    self._saved_input = self.text
                    self._history_index = 0
                elif self._history_index < len(history) - 1:
                    self._history_index += 1
                if self._history_index < len(history):
                    self.load_text(history[self._history_index])
                    self.move_cursor(self.document.end)
                event.stop()
                event.prevent_default()
            else:
                super()._on_key(event)

        elif event.key == "down":
            if self._history_index > 0:
                self._history_index -= 1
                history = self._get_user_messages()
                self.load_text(history[self._history_index])
                self.move_cursor(self.document.end)
                event.stop()
                event.prevent_default()
            elif self._history_index == 0:
                self._history_index = -1
                self.load_text(self._saved_input)
                self._saved_input = ""
                event.stop()
                event.prevent_default()
            else:
                super()._on_key(event)

        elif event.key == "enter":
            event.stop()
            event.prevent_default()
            text = self.text.strip()
            if text:
                self.clear()
                self.focus()
                screen = self.screen
                if hasattr(screen, '_handle_chat_input'):
                    asyncio.create_task(screen._handle_chat_input(text))
        else:
            if self._history_index != -1:
                self._history_index = -1
                self._saved_input = ""
            super()._on_key(event)

    def action_insert_newline(self) -> None:
        """Insert newline at cursor."""
        self.insert("\n")


# ── Status Bar ──────────────────────────────────────────

class StatusBar(Static):
    """Bottom status bar — 3-column: [indicator] dir | provider/model | stats."""

    model: reactive[str] = reactive("")
    provider: reactive[str] = reactive("")
    context_tokens: reactive[int] = reactive(0)
    context_limit: reactive[int] = reactive(0)
    total_cost: reactive[float] = reactive(0.0)
    mode: reactive[str] = reactive("build")
    elapsed: reactive[float] = reactive(0)
    thinking: reactive[bool] = reactive(False)
    done_flash: reactive[bool] = reactive(False)
    api_info: reactive[str] = reactive("")
    api_error: reactive[str] = reactive("")
    git_info: reactive[str] = reactive("")
    workspace: reactive[str] = reactive("")

    _spinner_frame: int = 0
    _think_start: float = 0.0
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def watch_thinking(self, thinking: bool) -> None:
        if thinking:
            self._think_start = time.time()
            self.done_flash = False
        elif self._think_start > 0:
            self.done_flash = True
            self._spinner_frame = 0
            self.elapsed = time.time() - self._think_start
            self.set_timer(3.0, lambda: self._clear_done())

    def _clear_done(self) -> None:
        self.done_flash = False
        self.refresh(layout=False)

    def on_mount(self) -> None:
        self.set_interval(0.1, self._tick)

    def _tick(self) -> None:
        if self.thinking:
            self._spinner_frame = (self._spinner_frame + 1) % len(self.SPINNER_FRAMES)
            if self._think_start > 0:
                self.elapsed = time.time() - self._think_start
            self.refresh(layout=False)

    def render(self) -> str:
        # ── Left: [spinner/checkmark] workspace ──
        if self.thinking:
            frame = self.SPINNER_FRAMES[self._spinner_frame]
            indicator = f"[yellow]{frame}[/yellow] thinking"
        elif self.done_flash:
            indicator = "[green]✓ Done[/green]"
        elif self.api_error:
            indicator = f"[red]✗ {self.api_error[:20]}[/red]"
        else:
            indicator = "[dim]✓ Ready[/dim]"

        ws = self.workspace or self.git_info or "~"
        left = f"{indicator}  [dim]{ws}[/dim]"

        # ── Center: provider/model ──
        center = ""
        if self.provider:
            center = f"[primary]{self.provider}[/primary]/[secondary]{self.model}[/secondary]"

        # ── Right: elapsed | ctx tokens (%) | cost ──
        right_parts = []
        if self.thinking or self.done_flash:
            right_parts.append(f"[dim]{self.elapsed:.0f}s[/dim]")

        if self.context_tokens > 0:
            limit = self.context_limit or 128000
            pct = min(100, int(self.context_tokens / limit * 100))
            pct_color = "[red]" if pct > 80 else "[yellow]" if pct > 50 else ""
            pct_end = "[/red]" if pct > 80 else "[/yellow]" if pct > 50 else ""
            right_parts.append(f"[dim]ctx {self.context_tokens:,}/{limit:,} {pct_color}({pct}%){pct_end}[/dim]")

        if self.total_cost > 0:
            right_parts.append(f"[green]${self.total_cost:.2f} spent[/green]")

        right = "  ".join(right_parts) if right_parts else ""

        # ── 3-column layout using container width ──
        width = max(80, self.size.width)
        third = width // 3

        left_plain = strip_markup(left)
        center_plain = strip_markup(center)
        right_plain = strip_markup(right)

        left_pad = max(0, third - len(left_plain))
        center_pad = max(0, third - len(center_plain))
        center_left = center_pad // 2
        center_right = center_pad - center_left
        right_pad = max(0, third - len(right_plain))

        return f"{left}{' ' * left_pad}{' ' * center_left}{center}{' ' * center_right}{' ' * right_pad}{right}"


# ── Sidebar Widget ──────────────────────────────────────

class SidebarWidget(Static):
    """Session info sidebar."""

    session_id: reactive[str] = reactive("")
    session_title: reactive[str] = reactive("Untitled")
    model: reactive[str] = reactive("")
    provider: reactive[str] = reactive("")
    context_tokens: reactive[int] = reactive(0)
    context_limit: reactive[int] = reactive(0)
    total_cost: reactive[float] = reactive(0.0)
    skill_count: reactive[int] = reactive(0)
    auto_approve: reactive[bool] = reactive(False)
    mode: reactive[str] = reactive("build")
    thinking: reactive[bool] = reactive(False)
    error_msg: reactive[str] = reactive("")
    git_branch: reactive[str] = reactive("")
    git_status: reactive[str] = reactive("")
    git_remote: reactive[str] = reactive("")

    def render(self) -> str:
        lines = []
        lines.append(f"[bold #fab283] de BigBos[/bold #fab283]")
        lines.append(f" [dim]#{self.session_id or '---'}[/dim]")
        lines.append("")
        if self.error_msg:
            lines.append(f" [red]{self.error_msg[:60]}[/red]")
            lines.append("")
        if self.thinking:
            lines.append(" [yellow]⠋ thinking...[/yellow]")
            lines.append("")
        if self.session_id:
            title = self.session_title or "Untitled"
            lines.append(f" [bold]{title[:35]}[/bold]")
            lines.append("")
        else:
            lines.append(" [dim]No active session[/dim]")
            lines.append("")

        color = "#5c9cf5" if self.mode == "build" else "#fab283"
        lines.append(f" [bold {color}]{self.mode.upper()}[/bold {color}]")
        lines.append("")

        limit = self.context_limit or 128000
        pct = min(100, int(self.context_tokens / limit * 100)) if self.context_tokens > 0 else 0
        pct_color = "[red]" if pct > 80 else "[yellow]" if pct > 50 else ""
        pct_end = "[/red]" if pct > 80 else "[/yellow]" if pct > 50 else ""
        bar = self._make_bar(pct)
        lines.append(" Context")
        lines.append(f"  [dim]{self.context_tokens:,}[/dim]/[bold]{limit:,}[/bold] tokens")
        lines.append(f"  {pct_color}{bar} {pct}% used{pct_end}")
        if self.total_cost > 0:
            lines.append(f"  ${self.total_cost:,.4f} spent")
        else:
            lines.append(f"  [dim]$0 spent[/dim]")
        lines.append("")

        if self.skill_count:
            lines.append(f" Skills: {self.skill_count}")
        if self.auto_approve:
            lines.append(" Auto: [yellow]ON[/yellow]")
        if self.git_branch:
            lines.append("")
            lines.append(f"[bold #5c9cf5] Git[/bold #5c9cf5]")
            lines.append(f" [green]{self.git_branch}[/green] {self.git_status}")
        return "\n".join(lines)

    @staticmethod
    def _make_bar(pct: int, width: int = 10) -> str:
        filled = int(width * pct / 100)
        return "[" + "|" * filled + "." * (width - filled) + "]"


# ── Tool Log Widget ─────────────────────────────────────

class ToolLogWidget(Static):
    """Shows recent tool executions."""

    tool_entries: reactive[list[dict[str, Any]]] = reactive([])

    def render(self) -> str:
        if not self.tool_entries:
            return ""

        lines = [" Tools"]
        lines.append(" ─────")
        for t in self.tool_entries[-5:]:
            icon = "..." if t.get("status") == "running" else "OK"
            args_str = json.dumps(t.get("args", {}))[:60]
            lines.append(f" {icon} {t['name']}({args_str})")
        return "\n".join(lines)


# ── Response Area ───────────────────────────────────────

class ResponseArea(RichLog):
    """Rich text area for model responses — selectable + copyable, never steals focus."""

    def on_mount(self) -> None:
        self.can_focus = False
        self.highlight = True

    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to system clipboard. Returns True on success."""
        import subprocess
        import sys
        if not text:
            return False
        try:
            if sys.platform == "win32":
                subprocess.run("clip", input=text[:10000].encode("utf-8", errors="replace"), check=False)
            elif sys.platform == "darwin":
                subprocess.run("pbcopy", input=text.encode("utf-8", errors="replace"), check=False)
            else:
                subprocess.run(["xclip", "-selection", "clipboard"],
                               input=text.encode("utf-8", errors="replace"), check=False)
            return True
        except Exception:
            return False
