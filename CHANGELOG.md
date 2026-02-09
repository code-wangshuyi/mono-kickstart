# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: Migrated CLI framework from Typer to argparse (Python standard library)
  - Removed dependency on `typer` and `rich` packages
  - All CLI functionality remains the same
  - Shell completion now uses custom `setup-shell` command instead of `--install-completion`
- Improved Chinese help messages and formatting

### Added
- **Core Modules**:
  - Platform detection module with OS, architecture, and Shell detection
  - Configuration management module with YAML-based multi-source config merging
  - Tool detection module for checking installed tools and versions
  - Installation orchestrator for managing tool installation workflow
  - Mirror configuration module for China mainland acceleration
  - Project creator module for generating Monorepo structure

- **Tool Installers**:
  - NVM installer with Shell configuration
  - Node.js installer via NVM
  - Conda (Miniconda) installer with platform-specific packages
  - Bun installer with official installation script
  - uv installer with official installation script
  - Claude Code CLI installer with native binary installation
  - Codex CLI installer with Bun/npm fallback
  - Spec Kit installer via uv tool install
  - BMad Method installer via npx/bunx

- **CLI Commands**:
  - `init` command for project initialization and tool installation
  - `upgrade` command for upgrading installed tools
  - `install` command for installing individual tools
  - `setup-shell` command for Shell PATH and Tab completion configuration
  - Support for `--dry-run`, `--force`, `--config`, `--save-config` options

- **Testing**:
  - Comprehensive unit tests for all modules (85%+ coverage)
  - Property-based tests using Hypothesis for correctness verification
  - Test fixtures and mocks for isolated testing

- **Documentation**:
  - Complete requirements and design documents
  - Detailed implementation plan with task breakdown
  - Comprehensive README with usage examples and FAQ

### Fixed
- Shell completion scripts now properly support both `mk` and `mono-kickstart` commands
- Configuration priority merging now correctly handles nested fields
- Platform-specific package selection for Conda installer

## [0.3.0] - 2024-01-XX

### Added
- Platform detection module (OS, architecture, Shell)
- Configuration management module (YAML-based)
- Property-based tests for platform detection and configuration
- Unit tests for all core modules

### Changed
- Updated project structure to follow best practices
- Improved test coverage to 85%

## [0.2.0] - 2024-01-XX

### Added
- Initial CLI structure with Typer
- Basic command scaffolding (init, upgrade, install)

## [0.1.0] - 2024-01-XX

### Added
- Initial project setup
- Project requirements and design documents
- Basic project structure

[Unreleased]: https://github.com/mono-kickstart/mono-kickstart/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/mono-kickstart/mono-kickstart/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/mono-kickstart/mono-kickstart/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mono-kickstart/mono-kickstart/releases/tag/v0.1.0
