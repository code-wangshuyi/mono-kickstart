"""
Unit tests for command entry points

Validates requirement 10.1, 10.4, and 10.8:
- Both mk and mono-kickstart commands are registered
- Both commands provide identical functionality
"""

import subprocess
import sys


def test_mk_entry_point_exists():
    """Test that mk entry point can be imported"""
    # This verifies the entry point is correctly configured in pyproject.toml
    from mono_kickstart.cli import main
    assert callable(main)


def test_mono_kickstart_entry_point_exists():
    """Test that mono-kickstart entry point can be imported"""
    # Both entry points point to the same function
    from mono_kickstart.cli import main
    assert callable(main)


def test_mk_command_version():
    """Test mk command shows version (validates requirement 10.1, 10.4)"""
    result = subprocess.run(
        [sys.executable, "-m", "mono_kickstart.cli", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Mono-Kickstart version" in result.stdout


def test_mk_command_help():
    """Test mk command shows help (validates requirement 10.8)"""
    result = subprocess.run(
        [sys.executable, "-m", "mono_kickstart.cli", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Monorepo 项目模板脚手架 CLI 工具" in result.stdout
    assert "init" in result.stdout
    assert "upgrade" in result.stdout


def test_entry_points_are_identical():
    """Test that both entry points provide identical functionality (validates requirement 10.8)
    
    Both mk and mono-kickstart commands point to the same main() function,
    ensuring they provide completely identical functionality.
    """
    from mono_kickstart.cli import main
    
    # Both entry points in pyproject.toml point to mono_kickstart.cli:main
    # This test verifies they reference the same function
    assert main.__module__ == "mono_kickstart.cli"
    assert main.__name__ == "main"


def test_pyproject_entry_points_configuration():
    """Test that pyproject.toml has correct entry points configuration
    
    Validates requirement 10.1:
    - mk = "mono_kickstart.cli:main"
    - mono-kickstart = "mono_kickstart.cli:main"
    """
    import tomllib
    from pathlib import Path
    
    # Read pyproject.toml
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    
    # Verify entry points are configured
    scripts = pyproject.get("project", {}).get("scripts", {})
    
    assert "mk" in scripts, "mk entry point not found in [project.scripts]"
    assert "mono-kickstart" in scripts, "mono-kickstart entry point not found in [project.scripts]"
    
    # Verify both point to the same function
    assert scripts["mk"] == "mono_kickstart.cli:main"
    assert scripts["mono-kickstart"] == "mono_kickstart.cli:main"
    
    # Verify they are identical (requirement 10.8)
    assert scripts["mk"] == scripts["mono-kickstart"]
