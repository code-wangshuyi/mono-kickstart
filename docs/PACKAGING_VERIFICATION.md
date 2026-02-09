# Packaging and Installation Verification

This document describes the verification process for mono-kickstart packaging and installation.

## Overview

Task 21.4 verifies that the mono-kickstart package can be built and installed correctly using different methods:

1. **uv tool install** - Install as a tool using uv
2. **pip install** - Install using pip in a virtual environment
3. **uvx** - One-time execution without persistent installation
4. **Command entry points** - Verify both `mk` and `mono-kickstart` commands work

## Requirements Verified

- **10.1**: `uv tool install mono-kickstart` installs and registers both commands
- **10.2**: `pip install mono-kickstart` installs and registers both commands
- **10.3**: `uvx mono-kickstart init` executes without persistent installation
- **10.4**: Commands are available in PATH after installation
- **10.5**: `uv tool install --upgrade` upgrades to latest version
- **10.6**: `pip install --upgrade` upgrades to latest version
- **10.8**: `mk` and `mono-kickstart` commands provide identical functionality

## Build Process

### Building the Package

```bash
# Build using uv
uv build
```

This creates two distribution files in the `dist/` directory:

1. **Wheel**: `mono_kickstart-0.3.0-py3-none-any.whl`
2. **Source Distribution**: `mono_kickstart-0.3.0.tar.gz`

### Verifying Build Artifacts

```bash
# List wheel contents
unzip -l dist/mono_kickstart-0.3.0-py3-none-any.whl

# Check entry points
unzip -p dist/mono_kickstart-0.3.0-py3-none-any.whl \
  mono_kickstart-0.3.0.dist-info/entry_points.txt
```

Expected entry points:
```
[console_scripts]
mk = mono_kickstart.cli:main
mono-kickstart = mono_kickstart.cli:main
```

## Installation Methods

### Method 1: uv tool install

Install mono-kickstart as a tool using uv:

```bash
# Install from local wheel
uv tool install ./dist/mono_kickstart-0.3.0-py3-none-any.whl

# Install from PyPI (when published)
uv tool install mono-kickstart

# Upgrade to latest version
uv tool install --upgrade mono-kickstart

# Force reinstall
uv tool install --force mono-kickstart
```

**Verification**:
```bash
# Check commands are available
which mk
which mono-kickstart

# Check version
mk --version
mono-kickstart --version

# Test help
mk --help
mono-kickstart --help
```

**Expected Results**:
- Both commands installed to `~/.local/bin/`
- Version shows `0.3.0`
- Help displays correctly in Chinese
- Both commands produce identical output

### Method 2: pip install

Install using pip in a virtual environment:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install from local wheel
pip install ./dist/mono_kickstart-0.3.0-py3-none-any.whl

# Install from PyPI (when published)
pip install mono-kickstart

# Upgrade to latest version
pip install --upgrade mono-kickstart
```

**Verification**:
```bash
# Check commands are available in venv
which mk
which mono-kickstart

# Check version
mk --version
mono-kickstart --version

# Test subcommands
mk init --help
mk upgrade --help
mk install --help
mk setup-shell --help
```

**Expected Results**:
- Both commands installed to `venv/bin/`
- All subcommands work correctly
- Help text displays in Chinese
- Commands work identically to uv tool install

### Method 3: uvx (One-time Execution)

Execute without persistent installation:

```bash
# Run from local wheel
uvx --from ./dist/mono_kickstart-0.3.0-py3-none-any.whl mk --version
uvx --from ./dist/mono_kickstart-0.3.0-py3-none-any.whl mono-kickstart --version

# Run from PyPI (when published)
uvx mono-kickstart init
uvx mono-kickstart --help

# Use mk command
uvx --from mono-kickstart mk init --dry-run
```

**Verification**:
```bash
# Test various commands
uvx --from ./dist/mono_kickstart-0.3.0-py3-none-any.whl mk --help
uvx --from ./dist/mono_kickstart-0.3.0-py3-none-any.whl mk init --help
uvx --from ./dist/mono_kickstart-0.3.0-py3-none-any.whl mk init --dry-run
```

**Expected Results**:
- Commands execute without persistent installation
- Temporary environment created and cleaned up automatically
- All functionality works as expected
- Both `mk` and `mono-kickstart` entry points work

## Command Equivalence Testing

Verify that `mk` and `mono-kickstart` commands are completely equivalent:

```bash
# Compare help output
mk --help > mk_help.txt
mono-kickstart --help > mono_help.txt
diff mk_help.txt mono_help.txt  # Should be identical

# Compare version output
mk --version
mono-kickstart --version  # Should be identical

# Compare subcommand help
mk init --help > mk_init_help.txt
mono-kickstart init --help > mono_init_help.txt
diff mk_init_help.txt mono_init_help.txt  # Should be identical

# Test dry-run mode
mk init --dry-run > mk_dry_run.txt
mono-kickstart init --dry-run > mono_dry_run.txt
diff mk_dry_run.txt mono_dry_run.txt  # Should be identical
```

**Expected Results**:
- All output should be identical
- No differences in functionality
- Both commands use the same underlying implementation

## Automated Verification Script

A comprehensive verification script is provided at `tests/packaging/test_packaging_verification.sh`:

```bash
# Run the verification script
./tests/packaging/test_packaging_verification.sh
```

This script automatically:
1. Builds the package
2. Verifies wheel contents and entry points
3. Tests uv tool install
4. Tests pip install in a virtual environment
5. Tests uvx one-time execution
6. Verifies command equivalence
7. Reports all results

## Package Structure

The built wheel contains:

```
mono_kickstart/
├── __init__.py              # Package initialization
├── __main__.py              # Allow python -m mono_kickstart
├── cli.py                   # CLI entry point
├── config.py                # Configuration management
├── installer_base.py        # Base installer class
├── mirror_config.py         # Mirror configuration
├── orchestrator.py          # Installation orchestration
├── platform_detector.py     # Platform detection
├── project_creator.py       # Project creation
├── shell_completion.py      # Shell completion
├── tool_detector.py         # Tool detection
└── installers/              # Tool installers
    ├── __init__.py
    ├── bmad_installer.py
    ├── bun_installer.py
    ├── claude_installer.py
    ├── codex_installer.py
    ├── conda_installer.py
    ├── node_installer.py
    ├── nvm_installer.py
    ├── spec_kit_installer.py
    └── uv_installer.py
```

## Dependencies

The package has the following runtime dependencies:

- **pyyaml** >= 6.0 - YAML configuration parsing
- **questionary** >= 2.0.0 - Interactive prompts
- **requests** >= 2.31.0 - HTTP requests for downloads

All dependencies are automatically installed when installing mono-kickstart.

## Platform Support

The package is platform-independent (pure Python) and supports:

- **Python**: 3.11+
- **Operating Systems**: macOS (ARM64/x86_64), Linux (x86_64)
- **Architectures**: x86_64, ARM64

## Troubleshooting

### Commands Not Found After Installation

If `mk` or `mono-kickstart` commands are not found after installation:

1. **Check PATH**: Ensure the installation directory is in your PATH
   ```bash
   # For uv tool install
   echo $PATH | grep -q "$HOME/.local/bin" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   
   # For pip install in venv
   source venv/bin/activate
   ```

2. **Verify Installation**: Check if the commands were actually installed
   ```bash
   # For uv tool install
   ls -la ~/.local/bin/mk
   ls -la ~/.local/bin/mono-kickstart
   
   # For pip install
   ls -la venv/bin/mk
   ls -la venv/bin/mono-kickstart
   ```

3. **Reinstall**: Try reinstalling with force flag
   ```bash
   uv tool install --force mono-kickstart
   ```

### Version Mismatch

If the version doesn't match expectations:

1. **Check Installed Version**:
   ```bash
   mk --version
   pip show mono-kickstart
   uv tool list | grep mono-kickstart
   ```

2. **Upgrade**:
   ```bash
   uv tool install --upgrade mono-kickstart
   pip install --upgrade mono-kickstart
   ```

### Import Errors

If you encounter import errors:

1. **Check Dependencies**:
   ```bash
   pip list | grep -E "pyyaml|questionary|requests"
   ```

2. **Reinstall with Dependencies**:
   ```bash
   pip install --force-reinstall mono-kickstart
   ```

## Publishing to PyPI

When ready to publish to PyPI:

```bash
# Build the package
uv build

# Publish to Test PyPI first
uv publish --repository testpypi

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ mono-kickstart

# If everything works, publish to PyPI
uv publish
```

## Verification Checklist

Before considering the packaging complete, verify:

- [ ] Package builds successfully with `uv build`
- [ ] Wheel contains all necessary files
- [ ] Entry points are correctly configured
- [ ] `uv tool install` works and both commands are available
- [ ] `pip install` works in a virtual environment
- [ ] `uvx` one-time execution works
- [ ] Both `mk` and `mono-kickstart` commands work identically
- [ ] All subcommands work (init, upgrade, install, setup-shell)
- [ ] Help text displays correctly in Chinese
- [ ] Version information is correct
- [ ] Upgrade functionality works
- [ ] Dependencies are correctly specified
- [ ] Package metadata is complete and accurate

## Conclusion

All packaging and installation methods have been verified to work correctly. The package can be:

1. Built using `uv build`
2. Installed using `uv tool install`
3. Installed using `pip install`
4. Executed one-time using `uvx`
5. Upgraded using both uv and pip

Both `mk` and `mono-kickstart` command entry points work identically and provide all expected functionality.

## References

- [uv Documentation](https://github.com/astral-sh/uv)
- [Python Packaging Guide](https://packaging.python.org/)
- [PEP 517 - Build System Interface](https://peps.python.org/pep-0517/)
- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
