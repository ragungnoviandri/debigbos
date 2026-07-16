"""Bash/shell execution tool."""

import os
import subprocess
import time
from pathlib import Path

from .registry import ToolDefinition


class BashTool:
    """Tool for executing shell commands."""

    @staticmethod
    def definition(workspace: Path) -> ToolDefinition:
        return ToolDefinition(
            name="bash",
            description="Execute a shell command in the workspace. "
                        "Use for git, npm, pip, docker, and other CLI operations. "
                        "Commands run in the workspace directory by default.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute",
                    },
                    "workdir": {
                        "type": "string",
                        "description": "Working directory (defaults to workspace root)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 120)",
                        "default": 120,
                    },
                },
                "required": ["command"],
            },
            handler=BashTool._run,
            requires_approval=True,
        )

    @staticmethod
    async def _run(command: str, workdir: str | None = None, timeout: int = 120) -> str:
        """Execute the shell command."""
        cwd = workdir or os.getcwd()
        if not os.path.isabs(cwd):
            cwd = os.path.join(os.getcwd(), cwd)

        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=cwd, env=os.environ.copy(),
            )
            output = ""
            if proc.stdout:
                output += proc.stdout
            if proc.stderr:
                output += "\n[stderr]\n" + proc.stderr
            if proc.returncode != 0:
                output += f"\n[exit code: {proc.returncode}]"
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s"
        except Exception as e:
            return f"Error executing command: {e}"
