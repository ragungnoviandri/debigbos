"""Skills system — load on-demand instructions from SKILL.md files.

Skills are Markdown files stored in .debigbos/skills/<name>/SKILL.md.
They're loaded lazily when the agent calls the `skill` tool.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Skill:
    """A loaded skill definition."""
    name: str
    description: str
    content: str
    path: Path
    license_info: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def truncate_for_prompt(self, max_chars: int = 4000) -> str:
        """Return truncated content for prompt injection."""
        if len(self.content) <= max_chars:
            return self.content
        return self.content[:max_chars] + "\n\n... (truncated)"


class SkillManager:
    """Loads and manages skill definitions from filesystem."""

    def __init__(self, workspace: Path, extra_paths: list[str] | None = None,
                 disabled_skills: list[str] | None = None):
        self.workspace = workspace
        self.search_paths: list[Path] = [
            workspace / ".debigbos" / "skills",          # Per-project skills
        ]

        # Global skills (~/.config/deBigBos/skills)
        global_skills = Path.home() / ".config" / "deBigBos" / "skills"
        if global_skills.exists():
            self.search_paths.append(global_skills)

        if extra_paths:
            for p in extra_paths:
                p_expanded = p
                if p.startswith("~"):
                    p_expanded = str(Path.home() / p[2:])
                path = Path(p_expanded)
                if not path.is_absolute():
                    path = workspace / path
                if path.exists() and path not in self.search_paths:
                    self.search_paths.append(path)

        self._skills: dict[str, Skill] = {}
        self._scanned = False
        self.disabled_skills: set[str] = set(disabled_skills or [])

    def scan(self) -> list[Skill]:
        """Scan all skill directories for SKILL.md files."""
        if self._scanned:
            return list(self._skills.values())

        self._skills.clear()
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
            for skill_dir in search_path.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        skill = self._parse_skill(skill_dir.name, skill_file)
                        if skill.name not in self.disabled_skills:
                            self._skills[skill.name] = skill
                    except Exception:
                        continue

        self._scanned = True
        return list(self._skills.values())

    def _parse_skill(self, dir_name: str, file_path: Path) -> Skill:
        """Parse a SKILL.md file with optional frontmatter."""
        raw = file_path.read_text(encoding="utf-8")
        name = dir_name
        description = ""
        license_info = ""
        metadata: dict[str, Any] = {}

        # Parse frontmatter (--- ... ---)
        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', raw, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            content = raw[fm_match.end():]
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip().lower()
                    value = value.strip()
                    if key == "name":
                        name = value
                    elif key == "description":
                        description = value
                    elif key == "license":
                        license_info = value
                    else:
                        metadata[key] = value
        else:
            content = raw
            # Auto-extract first heading as description
            heading_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
            if heading_match:
                description = heading_match.group(1)

        return Skill(
            name=name,
            description=description,
            content=content.strip(),
            path=file_path,
            license_info=license_info,
            metadata=metadata,
        )

    def get(self, name: str) -> Skill | None:
        """Get a skill by name, scanning if needed."""
        if not self._scanned:
            self.scan()
        return self._skills.get(name)

    def list_skills(self) -> list[dict[str, str]]:
        """List available skills as {name, description, enabled, category} pairs."""
        if not self._scanned:
            self.scan()
        # Also return ALL skills (including disabled) for settings UI
        all_skills: dict[str, dict] = {}
        
        # Scan all skills including disabled ones for listing
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
            for skill_dir in search_path.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        skill = self._parse_skill(skill_dir.name, skill_file)
                        all_skills[skill.name] = {
                            "name": skill.name,
                            "description": skill.description,
                            "enabled": skill.name not in self.disabled_skills,
                            "category": self._extract_category(skill),
                        }
                    except Exception:
                        continue
        
        return list(all_skills.values())

    def _extract_category(self, skill: Skill) -> str:
        """Extract category from skill name prefix or first tag."""
        # Try tags first
        tags = skill.metadata.get("hermes", {}).get("tags", []) if isinstance(skill.metadata, dict) else []
        if isinstance(tags, list) and len(tags) > 0:
            cat = str(tags[0])
            if cat:
                return cat.title()
        
        # Fallback: name prefix mapping
        name = skill.name
        prefixes = {
            "react-": "React", "vue-": "Vue",
            "django-": "Django", "flask-": "Flask",
            "github-": "GitHub", "git-": "Git",
            "apple-": "Apple",
            "docker-": "Docker",
            "design-": "Design",
            "test-": "Test", "tdd": "Test",
            "fullstack-": "Full Stack",
            "smartservices-": "Smart Services",
            "opencode": "Developer",
            "hermes-": "Hermes",
            "ai-": "AI", "llm-": "LLM", "ml-": "ML",
        }
        for prefix, cat in prefixes.items():
            if name.startswith(prefix):
                return cat
        return "Uncategorized"

    def enable_skill(self, name: str) -> bool:
        """Enable a skill. Returns True if it was disabled."""
        if name in self.disabled_skills:
            self.disabled_skills.discard(name)
            self._scanned = False  # force re-scan
            return True
        return False

    def disable_skill(self, name: str) -> bool:
        """Disable a skill. Returns True if it was enabled."""
        all_names = {s.name for s in self._all_skills()}
        if name not in self.disabled_skills and name in all_names:
            self.disabled_skills.add(name)
            self._skills.pop(name, None)
            return True
        return False

    def toggle_skill(self, name: str) -> str:
        """Toggle a skill on/off. Returns new status: 'enabled' | 'disabled' | 'unknown'."""
        all_names = {s.name for s in self._all_skills()}
        if name not in all_names:
            return "unknown"
        if name in self.disabled_skills:
            self.disabled_skills.discard(name)
            self._scanned = False
            return "enabled"
        else:
            self.disabled_skills.add(name)
            self._skills.pop(name, None)
            return "disabled"

    def _all_skills(self) -> list[Skill]:
        """Internal: scan all skills without filtering disabled."""
        skills = []
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
            for skill_dir in search_path.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        skills.append(self._parse_skill(skill_dir.name, skill_file))
                    except Exception:
                        continue
        return skills

    def create_skill(self, name: str, description: str, content: str,
                     author: str = "de BigBos", tags: list[str] | None = None) -> Skill | None:
        """Create a new skill and persist it as SKILL.md. Returns the Skill or None on failure."""
        import time

        if not self.search_paths:
            return None

        out_dir = self.search_paths[0] / name
        out_dir.mkdir(parents=True, exist_ok=True)

        # Build frontmatter
        frontmatter_lines = [
            f"name: {name}",
            f"description: \"{description}\"",
            f"version: 1.0.0",
            f"author: {author}",
            "license: MIT",
        ]
        if tags:
            frontmatter_lines.append(f"metadata:")
            frontmatter_lines.append(f"  tags: {tags}")

        fm_block = "\n".join(frontmatter_lines)
        full_content = f"---\n{fm_block}\n---\n\n{content.strip()}\n"

        out_file = out_dir / "SKILL.md"
        out_file.write_text(full_content, encoding="utf-8")

        # Parse & register
        skill = self._parse_skill(name, out_file)
        self._skills[skill.name] = skill
        return skill

    def get_skill_prompt(self) -> str:
        """Build the skills section of the system prompt."""
        skills = self.list_skills()
        if not skills:
            return ""

        lines = ["## Available Skills", ""]
        lines.append("Use the `skill` tool to load a skill's full instructions on demand.")
        lines.append("")
        for s in skills:
            lines.append(f"- **{s['name']}**: {s['description']}")
        return "\n".join(lines)
