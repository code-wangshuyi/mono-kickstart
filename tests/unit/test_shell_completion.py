"""
Unit tests for shell completion module
"""

import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from mono_kickstart.shell_completion import (
    detect_shell,
    get_completion_script,
    BASH_COMPLETION_SCRIPT,
    ZSH_COMPLETION_SCRIPT,
    FISH_COMPLETION_SCRIPT,
)


class TestDetectShell:
    """Tests for detect_shell function"""

    def test_detect_bash(self):
        """Test detecting bash shell"""
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            shell_name, rc_file, comp_dir = detect_shell()
            assert shell_name == "bash"
            assert rc_file == Path.home() / ".bashrc"
            assert comp_dir == Path.home() / ".bash_completions"

    def test_detect_zsh(self):
        """Test detecting zsh shell"""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            shell_name, rc_file, comp_dir = detect_shell()
            assert shell_name == "zsh"
            assert rc_file == Path.home() / ".zshrc"
            assert comp_dir == Path.home() / ".zsh_completions"

    def test_detect_fish(self):
        """Test detecting fish shell"""
        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            shell_name, rc_file, comp_dir = detect_shell()
            assert shell_name == "fish"
            assert rc_file == Path.home() / ".config" / "fish" / "config.fish"
            assert comp_dir == Path.home() / ".config" / "fish" / "completions"

    def test_detect_unknown_defaults_to_bash(self):
        """Test unknown shell defaults to bash"""
        with patch.dict(os.environ, {"SHELL": "/bin/unknown"}):
            shell_name, rc_file, comp_dir = detect_shell()
            assert shell_name == "bash"


class TestGetCompletionScript:
    """Tests for get_completion_script function"""

    def test_get_bash_script(self):
        """Test getting bash completion script"""
        script = get_completion_script("bash")
        assert script == BASH_COMPLETION_SCRIPT
        assert "_mk_completion" in script
        assert "complete -F _mk_completion mk" in script

    def test_get_zsh_script(self):
        """Test getting zsh completion script"""
        script = get_completion_script("zsh")
        assert script == ZSH_COMPLETION_SCRIPT
        assert "#compdef mk mono-kickstart" in script
        assert "_mk" in script

    def test_get_fish_script(self):
        """Test getting fish completion script"""
        script = get_completion_script("fish")
        assert script == FISH_COMPLETION_SCRIPT
        assert "complete -c mk" in script
        assert "complete -c mono-kickstart" in script

    def test_get_unknown_defaults_to_bash(self):
        """Test unknown shell defaults to bash script"""
        script = get_completion_script("unknown")
        assert script == BASH_COMPLETION_SCRIPT


class TestCompletionScriptContent:
    """Tests for completion script content"""

    def test_bash_script_has_all_commands(self):
        """Test bash script includes all commands"""
        assert "init" in BASH_COMPLETION_SCRIPT
        assert "upgrade" in BASH_COMPLETION_SCRIPT
        assert "install" in BASH_COMPLETION_SCRIPT
        assert "setup-shell" in BASH_COMPLETION_SCRIPT
        assert "status" in BASH_COMPLETION_SCRIPT
        assert "show" in BASH_COMPLETION_SCRIPT
        assert "opencode" in BASH_COMPLETION_SCRIPT

    def test_bash_script_has_all_tools(self):
        """Test bash script includes all tools"""
        tools = [
            "nvm",
            "node",
            "conda",
            "bun",
            "uv",
            "claude-code",
            "codex",
            "opencode",
            "spec-kit",
            "bmad-method",
        ]
        for tool in tools:
            assert tool in BASH_COMPLETION_SCRIPT

    def test_zsh_script_has_all_commands(self):
        """Test zsh script includes all commands"""
        assert "init" in ZSH_COMPLETION_SCRIPT
        assert "upgrade" in ZSH_COMPLETION_SCRIPT
        assert "install" in ZSH_COMPLETION_SCRIPT
        assert "setup-shell" in ZSH_COMPLETION_SCRIPT
        assert "status" in ZSH_COMPLETION_SCRIPT
        assert "show" in ZSH_COMPLETION_SCRIPT
        assert "opencode" in ZSH_COMPLETION_SCRIPT

    def test_zsh_script_has_all_tools(self):
        """Test zsh script includes all tools"""
        tools = [
            "nvm",
            "node",
            "conda",
            "bun",
            "uv",
            "claude-code",
            "codex",
            "opencode",
            "spec-kit",
            "bmad-method",
        ]
        for tool in tools:
            assert tool in ZSH_COMPLETION_SCRIPT

    def test_fish_script_has_all_commands(self):
        """Test fish script includes all commands"""
        assert "init" in FISH_COMPLETION_SCRIPT
        assert "upgrade" in FISH_COMPLETION_SCRIPT
        assert "install" in FISH_COMPLETION_SCRIPT
        assert "setup-shell" in FISH_COMPLETION_SCRIPT
        assert "status" in FISH_COMPLETION_SCRIPT
        assert "show" in FISH_COMPLETION_SCRIPT
        assert "opencode" in FISH_COMPLETION_SCRIPT

    def test_fish_script_has_all_tools(self):
        """Test fish script includes all tools"""
        tools = [
            "nvm",
            "node",
            "conda",
            "bun",
            "uv",
            "claude-code",
            "codex",
            "opencode",
            "spec-kit",
            "bmad-method",
        ]
        for tool in tools:
            assert tool in FISH_COMPLETION_SCRIPT

    def test_bash_script_claude_has_skills(self):
        """Test bash script includes --skills for claude subcommand"""
        assert "--skills" in BASH_COMPLETION_SCRIPT
        assert "--plugin" in BASH_COMPLETION_SCRIPT
        assert "uipro" in BASH_COMPLETION_SCRIPT
        assert "omc" in BASH_COMPLETION_SCRIPT

    def test_zsh_script_claude_has_skills(self):
        """Test zsh script includes --skills for claude subcommand"""
        assert "--skills" in ZSH_COMPLETION_SCRIPT
        assert "--plugin" in ZSH_COMPLETION_SCRIPT
        assert "uipro" in ZSH_COMPLETION_SCRIPT
        assert "omc" in ZSH_COMPLETION_SCRIPT

    def test_fish_script_claude_has_skills(self):
        """Test fish script includes skills for claude subcommand"""
        assert "skills" in FISH_COMPLETION_SCRIPT
        assert "plugin" in FISH_COMPLETION_SCRIPT
        assert "omc" in FISH_COMPLETION_SCRIPT

    def test_opencode_plugin_completion(self):
        assert "--plugin" in BASH_COMPLETION_SCRIPT
        assert "--plugin" in ZSH_COMPLETION_SCRIPT
        assert "-l plugin" in FISH_COMPLETION_SCRIPT
        assert "omo" in BASH_COMPLETION_SCRIPT

    def test_all_scripts_support_both_commands(self):
        """Test all scripts support both mk and mono-kickstart"""
        assert "mk" in BASH_COMPLETION_SCRIPT
        assert "mono-kickstart" in BASH_COMPLETION_SCRIPT
        assert "mk" in ZSH_COMPLETION_SCRIPT
        assert "mono-kickstart" in ZSH_COMPLETION_SCRIPT
        assert "mk" in FISH_COMPLETION_SCRIPT
        assert "mono-kickstart" in FISH_COMPLETION_SCRIPT
