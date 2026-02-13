"""
Unit tests for CLI module
"""

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from mono_kickstart import __version__
from mono_kickstart.cli import create_parser, main


def test_version_command():
    """Test --version command displays correct version"""
    with patch("sys.argv", ["mk", "--version"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            assert __version__ in fake_out.getvalue()


def test_help_command():
    """Test --help command displays help information"""
    with patch("sys.argv", ["mk", "--help"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "Monorepo 项目模板脚手架 CLI 工具" in output
            assert "init" in output
            assert "upgrade" in output


def test_init_help():
    """Test init --help command"""
    with patch("sys.argv", ["mk", "init", "--help"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "初始化 Monorepo 项目和开发环境" in output
            assert "--config" in output
            assert "--save-config" in output
            assert "--interactive" in output
            assert "--force" in output
            assert "--dry-run" in output


def test_upgrade_help():
    """Test upgrade --help command"""
    with patch("sys.argv", ["mk", "upgrade", "--help"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "升级已安装的开发工具" in output
            assert "--all" in output
            assert "--dry-run" in output


def test_opencode_help():
    with patch("sys.argv", ["mk", "opencode", "--help"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "配置 OpenCode 扩展能力" in output
            assert "--plugin" in output
            assert "omo" in output


def test_show_help():
    with patch("sys.argv", ["mk", "show", "--help"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "展示工具信息" in output
            assert "info" in output


def test_show_info_help():
    with patch("sys.argv", ["mk", "show", "info", "--help"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "检查所有工具最新版本并生成相关命令" in output


def test_show_info_generates_related_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    fake_detected = {
        "nvm": type("S", (), {"installed": False, "version": None, "path": None})(),
        "node": type("S", (), {"installed": True, "version": "20.0.0", "path": "/usr/bin/node"})(),
    }

    with patch("mono_kickstart.tool_detector.ToolDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.detect_all_tools.return_value = fake_detected

        with patch("mono_kickstart.cli._get_latest_version") as mock_latest:
            mock_latest.side_effect = lambda tool: {
                "nvm": "0.40.4",
                "node": "22.1.0",
            }.get(tool)
            with patch("mono_kickstart.cli.logger.info") as mock_info:
                with patch("sys.argv", ["mk", "show", "info"]):
                    exit_code = main()

    assert exit_code == 0
    merged = "\n".join(str(call.args[0]) for call in mock_info.call_args_list if call.args)
    assert "mk install nvm" in merged
    assert "mk upgrade node" in merged


def test_opencode_omo_dry_run_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("mono_kickstart.cli.shutil.which") as mock_which:
        mock_which.side_effect = lambda cmd: {
            "opencode": "/usr/local/bin/opencode",
            "bunx": "/usr/local/bin/bunx",
        }.get(cmd)
        with patch("mono_kickstart.cli.subprocess.run") as mock_run:
            with patch("sys.argv", ["mk", "opencode", "--plugin", "omo", "--dry-run"]):
                exit_code = main()
    assert exit_code == 0
    mock_run.assert_not_called()


def test_opencode_omo_requires_opencode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("mono_kickstart.cli.shutil.which", return_value=None):
        with patch("sys.argv", ["mk", "opencode", "--plugin", "omo"]):
            exit_code = main()
    assert exit_code == 1


def test_opencode_requires_plugin_option(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("sys.argv", ["mk", "opencode"]):
        exit_code = main()
    assert exit_code == 1


def test_opencode_omo_writes_config_files(tmp_path, monkeypatch):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    fake_home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(fake_home))

    with patch("mono_kickstart.cli.shutil.which") as mock_which:
        mock_which.side_effect = lambda cmd: {
            "opencode": "/usr/local/bin/opencode",
            "bunx": "/usr/local/bin/bunx",
        }.get(cmd)
        with patch("mono_kickstart.cli.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            with patch("sys.argv", ["mk", "opencode", "--plugin", "omo"]):
                exit_code = main()

    assert exit_code == 0

    opencode_json = fake_home / ".config" / "opencode" / "opencode.json"
    assert opencode_json.exists()
    opencode_config = json.loads(opencode_json.read_text(encoding="utf-8"))
    assert "plugin" in opencode_config
    assert "oh-my-opencode" in opencode_config["plugin"]

    omo_json = project_dir / ".opencode" / "oh-my-opencode.json"
    assert omo_json.exists()
    omo_config = json.loads(omo_json.read_text(encoding="utf-8"))
    assert "$schema" in omo_config


# ============================================================================
# Complete Flow Tests
# ============================================================================


def test_init_complete_flow_success_mocked(tmp_path, monkeypatch):
    """Test init command complete flow with successful installation (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.return_value = {
                "nvm": InstallReport(
                    "nvm", InstallResult.SUCCESS, "Installed successfully", "0.40.4"
                ),
                "node": InstallReport(
                    "node", InstallResult.SUCCESS, "Installed successfully", "20.0.0"
                ),
            }
            mock_orch.print_summary.return_value = None

            with patch("sys.argv", ["mk", "init", "--dry-run"]):
                exit_code = main()

                assert exit_code == 0
                assert mock_orch.run_init.called
                assert mock_orch.print_summary.called


def test_init_complete_flow_partial_failure_mocked(tmp_path, monkeypatch):
    """Test init command with partial failures (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.return_value = {
                "nvm": InstallReport(
                    "nvm", InstallResult.SUCCESS, "Installed successfully", "0.40.4"
                ),
                "node": InstallReport(
                    "node", InstallResult.FAILED, "Installation failed", error="Network error"
                ),
            }
            mock_orch.print_summary.return_value = None

            with patch("sys.argv", ["mk", "init", "--dry-run"]):
                exit_code = main()
                assert exit_code == 0  # Partial failure should return 0


def test_init_complete_flow_all_failures_mocked(tmp_path, monkeypatch):
    """Test init command when all installations fail (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.return_value = {
                "nvm": InstallReport(
                    "nvm", InstallResult.FAILED, "Installation failed", error="Network error"
                ),
                "node": InstallReport(
                    "node", InstallResult.FAILED, "Installation failed", error="Network error"
                ),
            }
            mock_orch.print_summary.return_value = None

            with patch("sys.argv", ["mk", "init", "--dry-run"]):
                exit_code = main()
                assert exit_code == 3  # All failures should return 3


def test_upgrade_complete_flow_success_mocked(tmp_path, monkeypatch):
    """Test upgrade command complete flow with successful upgrades (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.tool_detector import ToolStatus
    from mono_kickstart.installer_base import InstallReport, InstallResult

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.tool_detector.ToolDetector") as mock_tool_detector_class:
            mock_tool_detector = mock_tool_detector_class.return_value
            mock_tool_detector.detect_all_tools.return_value = {
                "nvm": ToolStatus("nvm", True, "0.40.3", "/usr/local/bin/nvm"),
                "node": ToolStatus("node", True, "18.0.0", "/usr/local/bin/node"),
            }

            with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
                mock_orch = mock_orch_class.return_value
                mock_orch.run_upgrade.return_value = {
                    "nvm": InstallReport(
                        "nvm", InstallResult.SUCCESS, "Upgraded successfully", "0.40.4"
                    ),
                    "node": InstallReport(
                        "node", InstallResult.SUCCESS, "Upgraded successfully", "20.0.0"
                    ),
                }
                mock_orch.print_summary.return_value = None

                with patch("sys.argv", ["mk", "upgrade", "--all", "--dry-run"]):
                    exit_code = main()
                    assert exit_code == 0
                    assert mock_orch.run_upgrade.called


def test_upgrade_single_tool_mocked(tmp_path, monkeypatch):
    """Test upgrade command for a single tool (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_upgrade.return_value = {
                "node": InstallReport(
                    "node", InstallResult.SUCCESS, "Upgraded successfully", "20.0.0"
                ),
            }
            mock_orch.print_summary.return_value = None

            with patch("sys.argv", ["mk", "upgrade", "node", "--dry-run"]):
                exit_code = main()
                assert exit_code == 0


def test_install_complete_flow_success_mocked(tmp_path, monkeypatch):
    """Test install command complete flow with successful installation (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.install_tool.return_value = InstallReport(
                "bun", InstallResult.SUCCESS, "Installed successfully", "1.0.0"
            )
            mock_orch.print_summary.return_value = None

            with patch("sys.argv", ["mk", "install", "bun", "--dry-run"]):
                exit_code = main()
                assert exit_code == 0
                assert mock_orch.install_tool.called


def test_install_all_tools_mocked(tmp_path, monkeypatch):
    """Test install command with --all flag (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.install_all_tools.return_value = {
                "nvm": InstallReport(
                    "nvm", InstallResult.SUCCESS, "Installed successfully", "0.40.4"
                ),
                "node": InstallReport(
                    "node", InstallResult.SUCCESS, "Installed successfully", "20.0.0"
                ),
            }
            mock_orch.print_summary.return_value = None

            with patch("sys.argv", ["mk", "install", "--all", "--dry-run"]):
                exit_code = main()
                assert exit_code == 0
                assert mock_orch.install_all_tools.called


def test_install_without_tool_or_all_flag_mocked(tmp_path, monkeypatch):
    """Test install command fails when neither tool nor --all is specified (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("sys.argv", ["mk", "install", "--dry-run"]):
            exit_code = main()
            assert exit_code == 1


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_init_unsupported_platform_mocked():
    """Test init command fails on unsupported platform (mocked)"""
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.UNSUPPORTED, arch=Arch.UNSUPPORTED, shell=Shell.BASH, shell_config_file=""
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = False
        mock_detector.detect_all.return_value = mock_platform

        with patch("sys.argv", ["mk", "init"]):
            exit_code = main()
            assert exit_code == 1


def test_upgrade_unsupported_platform_mocked():
    """Test upgrade command fails on unsupported platform (mocked)"""
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.UNSUPPORTED, arch=Arch.UNSUPPORTED, shell=Shell.BASH, shell_config_file=""
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = False
        mock_detector.detect_all.return_value = mock_platform

        with patch("sys.argv", ["mk", "upgrade", "--all"]):
            exit_code = main()
            assert exit_code == 1


def test_install_unsupported_platform_mocked():
    """Test install command fails on unsupported platform (mocked)"""
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.UNSUPPORTED, arch=Arch.UNSUPPORTED, shell=Shell.BASH, shell_config_file=""
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = False
        mock_detector.detect_all.return_value = mock_platform

        with patch("sys.argv", ["mk", "install", "--all"]):
            exit_code = main()
            assert exit_code == 1


def test_init_config_file_not_found_mocked(tmp_path, monkeypatch):
    """Test init command handles missing config file gracefully (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.config.ConfigManager") as mock_config_class:
            mock_config = mock_config_class.return_value
            mock_config.load_with_priority.side_effect = FileNotFoundError("Config file not found")

            with patch("sys.argv", ["mk", "init", "--config", "nonexistent.yaml"]):
                exit_code = main()
                assert exit_code == 2


def test_init_config_validation_error_mocked(tmp_path, monkeypatch):
    """Test init command handles config validation errors (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.config import Config

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.config.ConfigManager") as mock_config_class:
            mock_config = mock_config_class.return_value
            mock_config.load_with_priority.return_value = Config()
            mock_config.validate.return_value = ["Invalid tool name: invalid-tool"]

            with patch("sys.argv", ["mk", "init"]):
                exit_code = main()
                assert exit_code == 2


def test_init_keyboard_interrupt_mocked(tmp_path, monkeypatch):
    """Test init command handles keyboard interrupt gracefully (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.side_effect = KeyboardInterrupt()

            with patch("sys.argv", ["mk", "init", "--dry-run"]):
                exit_code = main()
                assert exit_code == 130


def test_upgrade_keyboard_interrupt_mocked(tmp_path, monkeypatch):
    """Test upgrade command handles keyboard interrupt gracefully (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_upgrade.side_effect = KeyboardInterrupt()

            with patch("sys.argv", ["mk", "upgrade", "--all", "--dry-run"]):
                exit_code = main()
                assert exit_code == 130


def test_install_keyboard_interrupt_mocked(tmp_path, monkeypatch):
    """Test install command handles keyboard interrupt gracefully (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.install_all_tools.side_effect = KeyboardInterrupt()

            with patch("sys.argv", ["mk", "install", "--all", "--dry-run"]):
                exit_code = main()
                assert exit_code == 130


def test_init_unexpected_exception_mocked(tmp_path, monkeypatch):
    """Test init command handles unexpected exceptions (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.side_effect = RuntimeError("Unexpected error")

            with patch("sys.argv", ["mk", "init", "--dry-run"]):
                exit_code = main()
                assert exit_code == 1


def test_upgrade_no_installed_tools_mocked(tmp_path, monkeypatch):
    """Test upgrade command when no tools are installed (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.tool_detector import ToolStatus

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.tool_detector.ToolDetector") as mock_tool_detector_class:
            mock_tool_detector = mock_tool_detector_class.return_value
            mock_tool_detector.detect_all_tools.return_value = {
                "nvm": ToolStatus("nvm", False, None, None),
                "node": ToolStatus("node", False, None, None),
            }

            with patch("sys.argv", ["mk", "upgrade", "--all", "--dry-run"]):
                exit_code = main()
                assert exit_code == 0


def test_init_with_save_config_mocked(tmp_path, monkeypatch):
    """Test init command saves config when --save-config is used (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.config import Config
    from mono_kickstart.installer_base import InstallReport, InstallResult

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.config.ConfigManager") as mock_config_class:
            mock_config = mock_config_class.return_value
            mock_config.load_with_priority.return_value = Config()
            mock_config.validate.return_value = []

            with patch("mono_kickstart.orchestrator.InstallOrchestrator") as mock_orch_class:
                mock_orch = mock_orch_class.return_value
                mock_orch.run_init.return_value = {
                    "nvm": InstallReport(
                        "nvm", InstallResult.SUCCESS, "Installed successfully", "0.40.4"
                    ),
                }
                mock_orch.print_summary.return_value = None

                with patch("sys.argv", ["mk", "init", "--save-config", "--dry-run"]):
                    exit_code = main()

                    assert exit_code == 0
                    # Verify save_to_file was called
                    assert mock_config.save_to_file.called


# ============================================================================
# Config Command Tests
# ============================================================================


def test_config_help():
    """Test config --help command displays help information"""
    with patch("sys.argv", ["mk", "config", "--help"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "mirror" in output
            assert "管理配置" in output


def test_config_mirror_help():
    """Test config mirror --help command"""
    with patch("sys.argv", ["mk", "config", "mirror", "--help"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "show" in output
            assert "reset" in output
            assert "set" in output


def test_config_mirror_show_mocked(tmp_path, monkeypatch):
    """Test config mirror show command (mocked)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.tool_detector import ToolStatus

    with patch("mono_kickstart.mirror_config.MirrorConfigurator") as mock_config_class:
        mock_configurator = mock_config_class.return_value
        mock_configurator.show_mirror_status.return_value = {
            "npm": {"configured": True, "default": "https://registry.npmjs.org/"},
            "bun": {"configured": False, "default": "https://registry.npmjs.org/"},
            "pip": {"configured": True, "default": "https://pypi.org/simple"},
            "uv": {"configured": False, "default": "https://pypi.org/simple"},
            "conda": {"configured": False, "default": "https://repo.anaconda.com/pkgs/main/"},
        }

        with patch("mono_kickstart.tool_detector.ToolDetector") as mock_detector_class:
            mock_detector = mock_detector_class.return_value
            mock_detector.detect_mirror_tools.return_value = {
                "npm": ToolStatus("node", True, "20.11.0", "/usr/bin/node"),
                "bun": ToolStatus("bun", False),
                "pip": ToolStatus("pip", True, "23.0.1", "/usr/bin/pip3"),
                "uv": ToolStatus("uv", False),
                "conda": ToolStatus("conda", False),
            }

            with patch("sys.argv", ["mk", "config", "mirror", "show"]):
                exit_code = main()

                assert exit_code == 0
                assert mock_configurator.show_mirror_status.called


def test_config_mirror_reset_all_mocked(tmp_path, monkeypatch):
    """Test config mirror reset command without --tool argument (resets all)"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.tool_detector import ToolStatus

    with patch("mono_kickstart.mirror_config.MirrorConfigurator") as mock_config_class:
        mock_configurator = mock_config_class.return_value
        mock_configurator.reset_npm_mirror.return_value = True
        mock_configurator.reset_bun_mirror.return_value = True
        mock_configurator.reset_uv_mirror.return_value = True
        mock_configurator.reset_pip_mirror.return_value = True
        mock_configurator.reset_conda_mirror.return_value = True

        with patch("mono_kickstart.tool_detector.ToolDetector") as mock_detector_class:
            mock_detector = mock_detector_class.return_value
            mock_detector.detect_mirror_tools.return_value = {
                "npm": ToolStatus("node", True, "20.11.0", "/usr/bin/node"),
                "bun": ToolStatus("bun", True, "1.0.25", "/usr/bin/bun"),
                "pip": ToolStatus("pip", True, "23.0.1", "/usr/bin/pip3"),
                "uv": ToolStatus("uv", True, "0.1.5", "/usr/local/bin/uv"),
                "conda": ToolStatus("conda", True, "23.5.0", "/opt/conda/bin/conda"),
            }

            with patch("sys.argv", ["mk", "config", "mirror", "reset"]):
                exit_code = main()

                assert exit_code == 0
                assert mock_configurator.reset_npm_mirror.called
                assert mock_configurator.reset_bun_mirror.called
                assert mock_configurator.reset_uv_mirror.called
                assert mock_configurator.reset_pip_mirror.called
                assert mock_configurator.reset_conda_mirror.called


def test_config_mirror_set_mocked(tmp_path, monkeypatch):
    """Test config mirror set command (mocked)"""
    monkeypatch.chdir(tmp_path)

    with patch("mono_kickstart.mirror_config.MirrorConfigurator") as mock_config_class:
        mock_configurator = mock_config_class.return_value
        mock_configurator.configure_npm_mirror.return_value = True

        with patch(
            "sys.argv", ["mk", "config", "mirror", "set", "npm", "https://custom-registry.com/"]
        ):
            exit_code = main()

            assert exit_code == 0
            assert mock_configurator.configure_npm_mirror.called


def test_config_mirror_set_china_preset(tmp_path, monkeypatch):
    """Test config mirror set china applies all China mirror presets"""
    monkeypatch.chdir(tmp_path)

    with patch("mono_kickstart.mirror_config.MirrorConfigurator") as mock_config_class:
        mock_configurator = mock_config_class.return_value
        mock_configurator.configure_npm_mirror.return_value = True
        mock_configurator.configure_bun_mirror.return_value = True
        mock_configurator.configure_pip_mirror.return_value = True
        mock_configurator.configure_uv_mirror.return_value = True
        mock_configurator.configure_conda_mirror.return_value = True

        with patch("sys.argv", ["mk", "config", "mirror", "set", "china"]):
            exit_code = main()

            assert exit_code == 0
            assert mock_configurator.configure_npm_mirror.called
            assert mock_configurator.configure_bun_mirror.called
            assert mock_configurator.configure_pip_mirror.called
            assert mock_configurator.configure_uv_mirror.called
            assert mock_configurator.configure_conda_mirror.called


def test_config_mirror_set_default_preset(tmp_path, monkeypatch):
    """Test config mirror set default applies all upstream defaults"""
    monkeypatch.chdir(tmp_path)

    with patch("mono_kickstart.mirror_config.MirrorConfigurator") as mock_config_class:
        mock_configurator = mock_config_class.return_value
        mock_configurator.configure_npm_mirror.return_value = True
        mock_configurator.configure_bun_mirror.return_value = True
        mock_configurator.configure_pip_mirror.return_value = True
        mock_configurator.configure_uv_mirror.return_value = True
        mock_configurator.configure_conda_mirror.return_value = True

        with patch("sys.argv", ["mk", "config", "mirror", "set", "default"]):
            exit_code = main()

            assert exit_code == 0
            assert mock_configurator.configure_npm_mirror.called
            assert mock_configurator.configure_bun_mirror.called
            assert mock_configurator.configure_pip_mirror.called
            assert mock_configurator.configure_uv_mirror.called
            assert mock_configurator.configure_conda_mirror.called


def test_config_mirror_set_tool_without_url(tmp_path, monkeypatch):
    """Test config mirror set <tool> without URL fails"""
    monkeypatch.chdir(tmp_path)

    with patch("mono_kickstart.mirror_config.MirrorConfigurator") as mock_config_class:
        mock_configurator = mock_config_class.return_value

        with patch("sys.argv", ["mk", "config", "mirror", "set", "npm"]):
            exit_code = main()

            assert exit_code == 1
            assert not mock_configurator.configure_npm_mirror.called


def test_config_mirror_set_china_preset_urls(tmp_path, monkeypatch):
    """Test config mirror set china sets correct China URLs"""
    monkeypatch.chdir(tmp_path)
    from mono_kickstart.config import RegistryConfig

    with patch("mono_kickstart.mirror_config.MirrorConfigurator") as mock_config_class:
        mock_configurator = mock_config_class.return_value
        mock_configurator.registry_config = RegistryConfig()
        mock_configurator.configure_npm_mirror.return_value = True
        mock_configurator.configure_bun_mirror.return_value = True
        mock_configurator.configure_pip_mirror.return_value = True
        mock_configurator.configure_uv_mirror.return_value = True
        mock_configurator.configure_conda_mirror.return_value = True

        with patch("sys.argv", ["mk", "config", "mirror", "set", "china"]):
            exit_code = main()

            assert exit_code == 0
            assert mock_configurator.registry_config.npm == "https://registry.npmmirror.com/"
            assert mock_configurator.registry_config.bun == "https://registry.npmmirror.com/"
            assert (
                mock_configurator.registry_config.pypi
                == "https://mirrors.sustech.edu.cn/pypi/web/simple"
            )
            assert (
                mock_configurator.registry_config.conda == "https://mirrors.sustech.edu.cn/anaconda"
            )


# ============================================================================
# Download Command Tests
# ============================================================================


def test_download_help():
    """Test download --help command displays help information"""
    with patch("sys.argv", ["mk", "download", "--help"]):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "下载工具安装包到本地磁盘" in output
            assert "--output" in output
            assert "--dry-run" in output
            assert "conda" in output


def test_download_conda_dry_run_mocked(tmp_path, monkeypatch):
    """Test download conda --dry-run shows download info without downloading"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.MACOS, arch=Arch.ARM64, shell=Shell.ZSH, shell_config_file=str(tmp_path / ".zshrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("sys.argv", ["mk", "download", "conda", "--dry-run"]):
            exit_code = main()
            assert exit_code == 0


def test_download_conda_success_mocked(tmp_path, monkeypatch):
    """Test download conda downloads file successfully"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        # Create a fake downloaded file before subprocess.run is called
        fake_file = tmp_path / "Miniconda3-latest-Linux-x86_64.sh"
        fake_file.write_text("fake installer content")

        with patch("mono_kickstart.cli.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0

            with patch("sys.argv", ["mk", "download", "conda", "-o", str(tmp_path)]):
                exit_code = main()
                assert exit_code == 0


def test_download_conda_network_error_mocked(tmp_path, monkeypatch):
    """Test download conda handles network error"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.cli.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 1

            with patch("sys.argv", ["mk", "download", "conda"]):
                exit_code = main()
                assert exit_code == 1


def test_download_unsupported_platform_mocked():
    """Test download command fails on unsupported platform"""
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.UNSUPPORTED, arch=Arch.UNSUPPORTED, shell=Shell.BASH, shell_config_file=""
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = False
        mock_detector.detect_all.return_value = mock_platform

        with patch("sys.argv", ["mk", "download", "conda"]):
            exit_code = main()
            assert exit_code == 1


def test_download_output_is_file_not_dir(tmp_path, monkeypatch):
    """Test download command fails when output path is a file"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    # Create a file at the output path
    file_path = tmp_path / "not_a_dir"
    file_path.write_text("I am a file")

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("sys.argv", ["mk", "download", "conda", "-o", str(file_path)]):
            exit_code = main()
            assert exit_code == 1


def test_download_keyboard_interrupt_mocked(tmp_path, monkeypatch):
    """Test download command handles keyboard interrupt gracefully"""
    monkeypatch.chdir(tmp_path)

    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell

    mock_platform = PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file=str(tmp_path / ".bashrc")
    )

    with patch("mono_kickstart.platform_detector.PlatformDetector") as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform

        with patch("mono_kickstart.cli.subprocess.run", side_effect=KeyboardInterrupt()):
            with patch("sys.argv", ["mk", "download", "conda"]):
                exit_code = main()
                assert exit_code == 130


def test_format_file_size():
    """Test _format_file_size utility function"""
    from mono_kickstart.cli import _format_file_size

    assert _format_file_size(0) == "0 B"
    assert _format_file_size(512) == "512 B"
    assert _format_file_size(1023) == "1023 B"
    assert _format_file_size(1024) == "1.0 KB"
    assert _format_file_size(1536) == "1.5 KB"
    assert _format_file_size(1048576) == "1.0 MB"
    assert _format_file_size(103456789) == "98.7 MB"
    assert _format_file_size(1073741824) == "1.0 GB"
