"""File operation tools — read, write, edit, glob, grep."""

import fnmatch
import os
import re
from pathlib import Path

from .registry import ToolDefinition


class ReadTool:
    """Tool for reading files."""

    @staticmethod
    def definition(workspace: Path) -> ToolDefinition:
        async def _read(filePath: str, offset: int = 0, limit: int = 2000) -> str:
            path = _resolve_path(filePath, workspace)
            if not path.exists():
                return f"File not found: {filePath}"
            if path.is_dir():
                entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name))
                lines = []
                for entry in entries:
                    suffix = "/" if entry.is_dir() else ""
                    lines.append(entry.name + suffix)
                return "\n".join(lines)
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
                start = max(0, offset - 1) if offset > 0 else 0
                end = start + limit
                chunk = lines[start:end]
                numbered = [f"{i+start+1}: {line}" for i, line in enumerate(chunk)]
                return "\n".join(numbered)
            except Exception as e:
                return f"Error reading file: {e}"

        return ToolDefinition(
            name="read",
            description="Read a file or directory. Returns line-numbered content for files, "
                        "or entry list for directories.",
            parameters={
                "type": "object",
                "properties": {
                    "filePath": {
                        "type": "string",
                        "description": "Absolute or workspace-relative path to the file/directory",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Line number to start reading from (1-indexed)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lines to read (default 2000)",
                        "default": 2000,
                    },
                },
                "required": ["filePath"],
            },
            handler=_read,
            read_only=True,
        )


class WriteTool:
    """Tool for writing files."""

    @staticmethod
    def definition(workspace: Path) -> ToolDefinition:
        async def _write(filePath: str, content: str) -> str:
            path = _resolve_path(filePath, workspace)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"Written {len(content)} chars to {filePath}"

        return ToolDefinition(
            name="write",
            description="Write content to a file. Creates parent directories if needed. Overwrites existing files.",
            parameters={
                "type": "object",
                "properties": {
                    "filePath": {
                        "type": "string",
                        "description": "Absolute or workspace-relative path to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                },
                "required": ["filePath", "content"],
            },
            handler=_write,
            requires_approval=True,
        )


class EditTool:
    """Tool for editing files with exact string replacement."""

    @staticmethod
    def definition(workspace: Path) -> ToolDefinition:
        async def _edit(filePath: str, oldString: str, newString: str,
                        replaceAll: bool = False) -> str:
            path = _resolve_path(filePath, workspace)
            if not path.exists():
                return f"File not found: {filePath}"
            content = path.read_text(encoding="utf-8")
            count = content.count(oldString)
            if count == 0:
                return f"oldString not found in file"
            if count > 1 and not replaceAll:
                return f"Found {count} matches for oldString. Use replaceAll=true or provide more context."
            new_content = content.replace(oldString, newString) if replaceAll else content.replace(oldString, newString, 1)
            path.write_text(new_content, encoding="utf-8")
            return f"Replaced {oldString[:50]}... with {newString[:50]}... ({count} occurrence(s))"

        return ToolDefinition(
            name="edit",
            description="Edit a file with exact string replacement. Find oldString and replace with newString. "
                        "Use replaceAll=true to replace all occurrences.",
            parameters={
                "type": "object",
                "properties": {
                    "filePath": {
                        "type": "string",
                        "description": "Absolute or workspace-relative path to edit",
                    },
                    "oldString": {
                        "type": "string",
                        "description": "Exact text to find and replace",
                    },
                    "newString": {
                        "type": "string",
                        "description": "Text to replace with",
                    },
                    "replaceAll": {
                        "type": "boolean",
                        "description": "Replace all occurrences (default false)",
                        "default": False,
                    },
                },
                "required": ["filePath", "oldString", "newString"],
            },
            handler=_edit,
            requires_approval=True,
        )


class GlobTool:
    """Tool for file pattern matching."""

    @staticmethod
    def definition(workspace: Path) -> ToolDefinition:
        async def _glob(pattern: str, path: str = "") -> str:
            search_dir = _resolve_path(path or ".", workspace)
            if not search_dir.exists():
                return f"Directory not found: {path}"
            matches = []
            for root, _, files in os.walk(str(search_dir)):
                rel_root = os.path.relpath(root, str(workspace))
                for name in files:
                    rel_path = os.path.join(rel_root, name).replace("\\", "/")
                    if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(name, pattern):
                        matches.append(rel_path)
            if not matches:
                return f"No files matched pattern '{pattern}'"
            return "\n".join(sorted(matches)[:200])

        return ToolDefinition(
            name="glob",
            description="Find files matching a glob pattern (e.g., '**/*.py', 'src/**/*.ts').",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to match files against",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in (defaults to workspace root)",
                    },
                },
                "required": ["pattern"],
            },
            handler=_glob,
            read_only=True,
        )


class GrepTool:
    """Tool for regex content search."""

    @staticmethod
    def definition(workspace: Path) -> ToolDefinition:
        async def _grep(pattern: str, include: str = "", path: str = "") -> str:
            search_dir = _resolve_path(path or ".", workspace)
            if not search_dir.exists():
                return f"Directory not found: {path}"
            compiled = re.compile(pattern)
            results = []
            for root, _, files in os.walk(str(search_dir)):
                for name in files:
                    if include and not fnmatch.fnmatch(name, include):
                        continue
                    file_path = os.path.join(root, name)
                    try:
                        content = open(file_path, encoding="utf-8", errors="replace").read()
                        for i, line in enumerate(content.split("\n"), 1):
                            if compiled.search(line):
                                rel = os.path.relpath(file_path, str(workspace)).replace("\\", "/")
                                results.append(f"{rel}:{i}: {line[:200]}")
                    except Exception:
                        continue
                    if len(results) >= 200:
                        break
                if len(results) >= 200:
                    break
            if not results:
                return f"No matches for pattern '{pattern}'"
            return "\n".join(results[:200])

        return ToolDefinition(
            name="grep",
            description="Search file contents with regex pattern. Use 'include' to filter file types.",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for in file contents",
                    },
                    "include": {
                        "type": "string",
                        "description": "File pattern to filter (e.g., '*.py', '*.{ts,js}')",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in (defaults to workspace root)",
                    },
                },
                "required": ["pattern"],
            },
            handler=_grep,
            read_only=True,
        )


def _resolve_path(file_path: str, workspace: Path) -> Path:
    """Resolve a path — absolute or relative to workspace."""
    p = Path(file_path)
    if p.is_absolute():
        return p
    return workspace / p
