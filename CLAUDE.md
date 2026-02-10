# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mono-kickstart (`mk`) is a Python 3.11+ CLI tool for initializing Monorepo projects with automated development environment setup. It orchestrates installation of tools (NVM, Node.js, Conda, Bun, uv, Claude Code, Codex, npx, Spec Kit, BMad Method), configures package manager mirrors, and generates project scaffolding.

## Common Commands

### Development Setup
```bash
uv sync --extra dev          # Install all dependencies including dev
uv pip install -e .          # Install package in editable mode
```

### Running the CLI
```bash
uv run mk status             # Run via uv
mk status                    # Run directly if installed
```

### Testing
```bash
uv run pytest tests/unit/                        # Run all unit tests
uv run pytest tests/unit/test_cli.py             # Run a specific test file
uv run pytest tests/unit/test_cli.py -k "test_name"  # Run a single test
uv run pytest tests/property/                    # Property-based tests (Hypothesis)
uv run pytest tests/integration/                 # Integration tests
uv run pytest --cov=mono_kickstart               # Run with coverage
```

### Linting & Formatting
```bash
uv run ruff check src/ tests/         # Lint check
uv run ruff check --fix src/ tests/   # Lint with auto-fix
uv run ruff format src/ tests/        # Format code
uv run ruff format --check src/ tests/  # Check formatting
```

### Building
```bash
uv build                     # Build distribution packages
```

## Architecture

### Entry Points
- `mk` and `mono-kickstart` both invoke `mono_kickstart.cli:main`
- CLI uses Python standard library `argparse` (migrated from Typer)

### Source Layout (`src/mono_kickstart/`)

**Core modules:**
- `cli.py` — Command parser, subcommand handlers (`cmd_init`, `cmd_upgrade`, `cmd_install`, etc.), and main dispatcher
- `orchestrator.py` — Controls installation order and sequencing via `INSTALL_ORDER`; creates installers via factory method `_create_installer()`
- `config.py` — Dataclass-based config (`Config`, `ToolConfig`, `RegistryConfig`); YAML loading with priority merging (CLI > project `.kickstartrc` > user `~/.kickstartrc` > defaults)
- `mirror_config.py` — Reads/writes tool-specific config files for package manager mirrors (npm, pip, uv, bun, conda)
- `interactive.py` — Questionary-based interactive wizard for configuration

**Detection & platform:**
- `platform_detector.py` — Detects OS (macOS/Linux), arch (ARM64/x86_64), shell (Bash/Zsh/Fish)
- `tool_detector.py` — Checks installed tools and versions via `shutil.which()` and version command output

**Infrastructure:**
- `installer_base.py` — Abstract `ToolInstaller` base class with `install()`, `upgrade()`, `verify()` interface and `run_command()` with retry logic
- `errors.py` — Custom exception hierarchy rooted at `MonoKickstartError`, each with exit codes and recovery hints
- `logger.py` — Colored console + file logging to `~/.mono-kickstart/logs/`
- `project_creator.py` — Generates monorepo directory structure (apps/, packages/, shared/)
- `shell_completion.py` — Tab completion scripts for Bash/Zsh/Fish

**Installers (`installers/`):**
Each inherits `ToolInstaller` and implements `install()`, `upgrade()`, `verify()`. To add a new tool: create an installer, register in `orchestrator.py` `INSTALL_ORDER` and `_create_installer()`.

### Key Flow: `mk init`
`main()` → `cmd_init()` → `PlatformDetector` → `Config.load_with_priority()` → [optional `InteractiveConfigurator`] → `InstallOrchestrator.run_init()` → iterates `INSTALL_ORDER`, creates each installer, calls `install()` → `MirrorConfigurator` → `ProjectCreator` → summary

## Conventions

- **Language**: All CLI help text and user-facing output is in Chinese (Simplified). Commands and flags are in English.
- **Help formatter**: Custom `ChineseHelpFormatter` in cli.py
- **Icons**: `✓` success, `✗`/`❌` fail, `⚠️` warning, `📦`/`📥` progress, `🔍` dry-run
- **Exit codes**: 0=success, 1=general error, 2=config/usage error, 3=all tasks failed, 130=Ctrl+C
- **`--dry-run`**: Consistent simulation flag across commands
- **Ruff config**: Line length 100, target Python 3.11, rules E/F/I/N/W/UP (in pyproject.toml)
- **Platform support**: macOS ARM64/x86_64, Linux x86_64. No Windows.
