# TheBigBos

AI-powered CLI assistant with persistent memory, soul, skills, and multi-model support. Built with Python + Textual TUI — inspired by OpenCode and Hermes.

```
   _____ _         ____  _       ____
  |_   _| |__     | __ )(_) __ _| __ )  ___  ___
    | | | '_ \    |  _ \| |/ _` |  _ \ / _ \/ __|
    | | | | | |   | |_) | | (_| | |_) | (_) \__ \
    |_| |_| |_|   |____/|_|\__, |____/ \___/|___/
                            |___/
```

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Model** | OpenAI, Anthropic, OpenCode Go, OpenRouter, Groq, Ollama — 6+ providers |
| **Persistent Memory** | 3-layer: short-term (context), medium-term (SQLite summaries), long-term (embeddings) |
| **Soul/Personality** | Configurable persona, tone, greeting, constraints |
| **Skills System** | Markdown-based SKILL.md lazy-loading |
| **Subagents** | Built-in explore, planner, reviewer agents with isolated context |
| **Session Management** | Persistent sessions, auto-import from OpenCode & Hermes |
| **Textual TUI** | Rich terminal UI with sidebar, status bar, session picker |
| **Tools** | bash, read, write, edit, glob, grep, webfetch, todowrite + custom tools |
| **Context Compaction** | Auto-summarize when approaching token limit |
| **Reasoning Support** | DeepSeek V4, o1/o3, Claude extended thinking |
| **Cross-Platform** | Windows, Linux, macOS |

## Installation

### One-Liner (Recommended)

```bash
# Windows
powershell -c "irm https://raw.githubusercontent.com/ragungnoviandri/thebigbos/main/install.ps1 | iex"

# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/ragungnoviandri/thebigbos/main/install.sh | bash
```

The installer handles everything: clone repo, setup Python venv, install dependencies, add to PATH.

### For Developers (Editable)

```bash
git clone https://github.com/ragungnoviandri/thebigbos
cd thebigbos
pip install -e .
thebigbos setup
```

Editable mode — code changes take effect immediately. No need to reinstall.

### Quick Start

```bash
# 1. Interactive setup — pick model + API key
thebigbos setup

# 2. Start chatting (TUI mode)
thebigbos

# 3. Or headless
thebigbos run "bikin hello world"
```

## Commands

### CLI Commands

| Command | Description |
|---------|-------------|
| `thebigbos` | Start interactive TUI |
| `thebigbos chat` | Start TUI (explicit) |
| `thebigbos run "query"` | Headless single query |
| `thebigbos setup` | Interactive model + API key setup |
| `thebigbos configure` | View or change config |
| `thebigbos init` | Initialize `.bigbos/` in project |
| `thebigbos install` | Install global config |
| `thebigbos import hermes` | Import sessions from Hermes |
| `thebigbos import opencode` | Import sessions from OpenCode |
| `thebigbos import all --dry-run` | Preview import |
| `thebigbos sessions list` | List all sessions |
| `thebigbos sessions rename <id> <title>` | Rename a session |
| `thebigbos version` | Show version + git info |
| `thebigbos update` | Check for and install updates |
| `thebigbos update --check` | Check for updates only |
| `thebigbos uninstall` | Remove TheBigBos (keeps config) |

### TUI Commands

| Key / Command | Description |
|---------------|-------------|
| `Ctrl+S` `/sessions` | Session picker (arrows, Enter, D=delete, R=rename) |
| `Ctrl+M` `/models` | List available models |
| `/model <id>` | Switch active model |
| `/agent <name> <task>` | Spawn subagent |
| `/remember key:value` | Store persistent fact |
| `/recall <query>` | Search memories |
| `/rename <title>` | Rename current session |
| `/clear` | Clear screen |
| `/help` | Show help |
| `Ctrl+Q` `/exit` | Quit |

## Configuration

Config files are merged from multiple locations (highest to lowest priority):

1. `.bigbos/config.json` — Per-project overrides
2. `thebigbos.json` — Project config
3. `~/.config/thebigbos/config.json` — Global config

### Example `thebigbos.json`

```json
{
  "active_provider": "opencode-go",
  "active_model": "deepseek-v4-pro",
  "providers": {
    "opencode-go": {
      "api_key": "${OPENCODE_GO_API_KEY}",
      "base_url": "https://opencode.ai/zen/go/v1"
    }
  },
  "soul": {
    "name": "TheBigBos",
    "persona": "A sharp, witty AI assistant. Direct and concise.",
    "tone": "casual but professional",
    "greeting": "Yo! TheBigBos here. What are we building today?"
  },
  "memory": {
    "compaction_threshold": 0.8,
    "vector_search_k": 5
  }
}
```

## Supported Providers

| Provider | Models | Setup |
|----------|--------|-------|
| **OpenCode Go** | deepseek-v4-pro, qwen3.5, kimi-k2, glm5, minimax-m3 | `OPENCODE_GO_API_KEY` ($10/mo) |
| **OpenAI** | gpt-4o, o3-mini, o1 | `OPENAI_API_KEY` |
| **Anthropic** | claude-sonnet-4, claude-opus | `ANTHROPIC_API_KEY` |
| **OpenRouter** | All models via router | `OPENROUTER_API_KEY` |
| **Groq** | llama-3.1, mixtral, gemma | `GROQ_API_KEY` |
| **Ollama** | llama3.1, qwen2.5, deepseek-r1 | Local, free |

## Skills

Create a `SKILL.md` file in `.bigbos/skills/<name>/`:

```markdown
---
name: my-skill
description: Custom skill for specific tasks
---

# My Skill

When asked about X, follow these steps:
1. Check for Y
2. Verify Z
3. Return findings
```

Load on-demand via `/skills` or `skill` tool in chat.

## Subagents

Built-in subagents:

| Agent | Description | Tools |
|-------|-------------|-------|
| `explore` | Codebase explorer | read, glob, grep, webfetch |
| `planner` | Task planning | read, glob, grep, todowrite |
| `reviewer` | Code review | read, glob, grep |

Usage:
```bash
# From TUI
/agent reviewer review semua file Python

# Or configure your own in thebigbos.json
```

## Directory Layout

```
~/.config/thebigbos/              # Global user config (persists across updates)
├── config.json                   # Model, provider, API keys, soul
├── skills/                       # User SKILL.md files
├── agents/                       # Custom subagent definitions
└── tools/                        # Custom tool JSON

~/.local/share/thebigbos/         # App installation
├── repo/                         # Git repository (pulled from GitHub)
│   └── thebigbos/                # Source code
├── venv/                         # Python virtual environment
├── bin/                          # Wrapper scripts
│   ├── thebigbos                 # Shell wrapper
│   └── thebigbos.bat             # Windows wrapper
└── versions/                     # Version history for rollback

<project>/.bigbos/                # Per-project data
├── memory.db                     # Session history (SQLite)
└── config.json                   # Project-level overrides
```

## Project Structure

```
TheBigBos/
├── thebigbos/                  # Main package
│   ├── main.py                 # CLI entry point
│   ├── config/manager.py       # Config loader
│   ├── models/                 # Multi-model providers
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── opencode_provider.py
│   │   └── ollama_provider.py
│   ├── core/                   # Brain & memory
│   │   ├── agent.py            # Main agent loop
│   │   ├── soul.py             # Personality engine
│   │   ├── memory.py           # SQLite persistent memory
│   │   ├── skills.py           # SKILL.md loader
│   │   └── session.py          # Session management
│   ├── tools/                  # Built-in tools
│   │   ├── bash_tool.py
│   │   ├── file_tools.py       # read, write, edit, glob, grep
│   │   ├── web_tool.py
│   │   └── todo_tool.py
│   └── tui/                    # Textual terminal UI
│       ├── app.py              # BigBosApp
│       ├── screens/home.py     # Chat screen + sidebar + status bar
│       ├── screens/welcome.py  # Welcome/splash screen
│       ├── dialogs.py          # Modal dialogs
│       ├── theme.py            # Theme management
│       ├── plugin.py           # Plugin system
│       └── keymap.py           # Keybinding registry
├── .bigbos/                    # User config (auto-created)
│   ├── skills/
│   ├── agents/
│   └── tools/
├── install.py                  # Installer
├── thebigbos.json              # Default config
└── pyproject.toml
```

## Architecture

```
User Input
    │
    ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Textual     │───▶│  BigBosAgent │───▶│  Provider    │
│  TUI         │    │              │    │  (OpenAI,    │
│  - Chat      │    │  - System    │    │   Anthropic, │
│  - Sidebar   │    │    Prompt    │    │   OpenCode,  │
│  - StatusBar │    │  - Memory    │    │   Ollama)    │
│  - Tool Log  │    │  - Skills    │    └──────┬───────┘
└──────────────┘    │  - Tools     │           │
                    │  - Session   │    ┌──────▼───────┐
                    │  - Subagents │    │  Model API   │
                    └──────┬───────┘    │  Response    │
                           │            └──────────────┘
                    ┌──────▼───────┐
                    │  Memory DB   │
                    │  (SQLite)    │
                    │  - Sessions  │
                    │  - Messages  │
                    │  - Facts     │
                    │  - Embeddings│
                    └──────────────┘
```

## Requirements

- Python 3.10+
- API key for at least one provider (or Ollama for local)
- Optional: `sentence-transformers` for long-term memory embeddings

## License

MIT — [github.com/ragungnoviandri/thebigbos](https://github.com/ragungnoviandri/thebigbos)
