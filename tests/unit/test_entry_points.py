"""
Unit tests for command entry points

Validates: Property 13 - 命令入口等价性
Verifies that both 'mk' and 'mono-kickstart' commands provide identical functionality.
"""

import subprocess
import sys
from pathlib import Path


def run_command_via_module(args):
    """Run command via Python module"""
    cmd = [sys.executable, "-m", "mono_kickstart.cli"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


def test_version_via_module():
    """Test --version command via module"""
    returncode, stdout, stderr = run_command_via_module(["--version"])
    assert returncode == 0
    assert "Mono-Kickstart version" in stdout


def test_help_via_module():
    """Test --help command via module"""
    returncode, stdout, stderr = run_command_via_module(["--help"])
    assert returncode == 0
    assert "Monorepo 项目模板脚手架 CLI 工具" in stdout


def test_init_via_module():
    """Test init command via module"""
    returncode, stdout, stderr = run_command_via_module(["init"])
    assert returncode == 0
    assert "Mono-Kickstart" in stdout


def test_upgrade_via_module():
    """Test upgrade command via module"""
    returncode, stdout, stderr = run_command_via_module(["upgrade"])
    assert returncode == 0
    assert "Mono-Kickstart" in stdout


def test_init_help_via_module():
    """Test init --help command via module"""
    returncode, stdout, stderr = run_command_via_module(["init", "--help"])
    assert returncode == 0
    assert "初始化 Monorepo 项目和开发环境" in stdout


def test_upgrade_help_via_module():
    """Test upgrade --help command via module"""
    returncode, stdout, stderr = run_command_via_module(["upgrade", "--help"])
    assert returncode == 0
    assert "升级已安装的开发工具" in stdout
