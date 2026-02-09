"""
Unit tests for CLI module
"""

import pytest
from typer.testing import CliRunner
from mono_kickstart.cli import app
from mono_kickstart import __version__


runner = CliRunner()


def test_version_command():
    """Test --version command displays correct version"""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_command():
    """Test --help command displays help information"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Monorepo 项目模板脚手架 CLI 工具" in result.stdout
    assert "init" in result.stdout
    assert "upgrade" in result.stdout


def test_init_help():
    """Test init --help command"""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "初始化 Monorepo 项目和开发环境" in result.stdout
    assert "--config" in result.stdout
    assert "--save-config" in result.stdout
    assert "--interactive" in result.stdout
    assert "--force" in result.stdout
    assert "--dry-run" in result.stdout


def test_upgrade_help():
    """Test upgrade --help command"""
    result = runner.invoke(app, ["upgrade", "--help"])
    assert result.exit_code == 0
    assert "升级已安装的开发工具" in result.stdout
    assert "--all" in result.stdout
    assert "--dry-run" in result.stdout


def test_init_command_placeholder():
    """Test init command runs (placeholder implementation)"""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Mono-Kickstart" in result.stdout


def test_upgrade_command_placeholder():
    """Test upgrade command runs (placeholder implementation)"""
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0
    assert "Mono-Kickstart" in result.stdout


def test_init_with_config_option():
    """Test init command accepts --config option"""
    result = runner.invoke(app, ["init", "--config", "test.yaml"])
    assert result.exit_code == 0


def test_init_with_save_config_option():
    """Test init command accepts --save-config option"""
    result = runner.invoke(app, ["init", "--save-config"])
    assert result.exit_code == 0


def test_init_with_interactive_option():
    """Test init command accepts --interactive option"""
    result = runner.invoke(app, ["init", "--interactive"])
    assert result.exit_code == 0


def test_init_with_force_option():
    """Test init command accepts --force option"""
    result = runner.invoke(app, ["init", "--force"])
    assert result.exit_code == 0


def test_init_with_dry_run_option():
    """Test init command accepts --dry-run option"""
    result = runner.invoke(app, ["init", "--dry-run"])
    assert result.exit_code == 0


def test_upgrade_with_tool_argument():
    """Test upgrade command accepts tool name argument"""
    result = runner.invoke(app, ["upgrade", "node"])
    assert result.exit_code == 0


def test_upgrade_with_all_option():
    """Test upgrade command accepts --all option"""
    result = runner.invoke(app, ["upgrade", "--all"])
    assert result.exit_code == 0


def test_upgrade_with_dry_run_option():
    """Test upgrade command accepts --dry-run option"""
    result = runner.invoke(app, ["upgrade", "--dry-run"])
    assert result.exit_code == 0
