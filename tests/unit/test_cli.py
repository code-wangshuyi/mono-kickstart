"""
Unit tests for CLI module
"""

import sys
from io import StringIO
from unittest.mock import patch

import pytest

from mono_kickstart import __version__
from mono_kickstart.cli import create_parser, main


def test_version_command():
    """Test --version command displays correct version"""
    with patch('sys.argv', ['mk', '--version']):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            assert __version__ in fake_out.getvalue()


def test_help_command():
    """Test --help command displays help information"""
    with patch('sys.argv', ['mk', '--help']):
        with patch('sys.stdout', new=StringIO()) as fake_out:
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
    with patch('sys.argv', ['mk', 'init', '--help']):
        with patch('sys.stdout', new=StringIO()) as fake_out:
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
    with patch('sys.argv', ['mk', 'upgrade', '--help']):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as exc_info:
                parser = create_parser()
                parser.parse_args()
            assert exc_info.value.code == 0
            output = fake_out.getvalue()
            assert "升级已安装的开发工具" in output
            assert "--all" in output
            assert "--dry-run" in output


# ============================================================================
# Complete Flow Tests
# ============================================================================


def test_init_complete_flow_success_mocked(tmp_path, monkeypatch):
    """Test init command complete flow with successful installation (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.return_value = {
                'nvm': InstallReport('nvm', InstallResult.SUCCESS, 'Installed successfully', '0.40.4'),
                'node': InstallReport('node', InstallResult.SUCCESS, 'Installed successfully', '20.0.0'),
            }
            mock_orch.print_summary.return_value = None
            
            with patch('sys.argv', ['mk', 'init', '--dry-run']):
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
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.return_value = {
                'nvm': InstallReport('nvm', InstallResult.SUCCESS, 'Installed successfully', '0.40.4'),
                'node': InstallReport('node', InstallResult.FAILED, 'Installation failed', error='Network error'),
            }
            mock_orch.print_summary.return_value = None
            
            with patch('sys.argv', ['mk', 'init', '--dry-run']):
                exit_code = main()
                assert exit_code == 0  # Partial failure should return 0


def test_init_complete_flow_all_failures_mocked(tmp_path, monkeypatch):
    """Test init command when all installations fail (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.return_value = {
                'nvm': InstallReport('nvm', InstallResult.FAILED, 'Installation failed', error='Network error'),
                'node': InstallReport('node', InstallResult.FAILED, 'Installation failed', error='Network error'),
            }
            mock_orch.print_summary.return_value = None
            
            with patch('sys.argv', ['mk', 'init', '--dry-run']):
                exit_code = main()
                assert exit_code == 3  # All failures should return 3


def test_upgrade_complete_flow_success_mocked(tmp_path, monkeypatch):
    """Test upgrade command complete flow with successful upgrades (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.tool_detector import ToolStatus
    from mono_kickstart.installer_base import InstallReport, InstallResult
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.tool_detector.ToolDetector') as mock_tool_detector_class:
            mock_tool_detector = mock_tool_detector_class.return_value
            mock_tool_detector.detect_all_tools.return_value = {
                'nvm': ToolStatus('nvm', True, '0.40.3', '/usr/local/bin/nvm'),
                'node': ToolStatus('node', True, '18.0.0', '/usr/local/bin/node'),
            }
            
            with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
                mock_orch = mock_orch_class.return_value
                mock_orch.run_upgrade.return_value = {
                    'nvm': InstallReport('nvm', InstallResult.SUCCESS, 'Upgraded successfully', '0.40.4'),
                    'node': InstallReport('node', InstallResult.SUCCESS, 'Upgraded successfully', '20.0.0'),
                }
                mock_orch.print_summary.return_value = None
                
                with patch('sys.argv', ['mk', 'upgrade', '--all', '--dry-run']):
                    exit_code = main()
                    assert exit_code == 0
                    assert mock_orch.run_upgrade.called


def test_upgrade_single_tool_mocked(tmp_path, monkeypatch):
    """Test upgrade command for a single tool (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_upgrade.return_value = {
                'node': InstallReport('node', InstallResult.SUCCESS, 'Upgraded successfully', '20.0.0'),
            }
            mock_orch.print_summary.return_value = None
            
            with patch('sys.argv', ['mk', 'upgrade', 'node', '--dry-run']):
                exit_code = main()
                assert exit_code == 0


def test_install_complete_flow_success_mocked(tmp_path, monkeypatch):
    """Test install command complete flow with successful installation (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.install_tool.return_value = InstallReport(
                'bun', InstallResult.SUCCESS, 'Installed successfully', '1.0.0'
            )
            mock_orch.print_summary.return_value = None
            
            with patch('sys.argv', ['mk', 'install', 'bun', '--dry-run']):
                exit_code = main()
                assert exit_code == 0
                assert mock_orch.install_tool.called


def test_install_all_tools_mocked(tmp_path, monkeypatch):
    """Test install command with --all flag (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.installer_base import InstallReport, InstallResult
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.install_all_tools.return_value = {
                'nvm': InstallReport('nvm', InstallResult.SUCCESS, 'Installed successfully', '0.40.4'),
                'node': InstallReport('node', InstallResult.SUCCESS, 'Installed successfully', '20.0.0'),
            }
            mock_orch.print_summary.return_value = None
            
            with patch('sys.argv', ['mk', 'install', '--all', '--dry-run']):
                exit_code = main()
                assert exit_code == 0
                assert mock_orch.install_all_tools.called


def test_install_without_tool_or_all_flag_mocked(tmp_path, monkeypatch):
    """Test install command fails when neither tool nor --all is specified (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('sys.argv', ['mk', 'install', '--dry-run']):
            exit_code = main()
            assert exit_code == 1


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_init_unsupported_platform_mocked():
    """Test init command fails on unsupported platform (mocked)"""
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    
    mock_platform = PlatformInfo(
        os=OS.UNSUPPORTED,
        arch=Arch.UNSUPPORTED,
        shell=Shell.BASH,
        shell_config_file=""
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = False
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('sys.argv', ['mk', 'init']):
            exit_code = main()
            assert exit_code == 1


def test_upgrade_unsupported_platform_mocked():
    """Test upgrade command fails on unsupported platform (mocked)"""
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    
    mock_platform = PlatformInfo(
        os=OS.UNSUPPORTED,
        arch=Arch.UNSUPPORTED,
        shell=Shell.BASH,
        shell_config_file=""
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = False
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('sys.argv', ['mk', 'upgrade', '--all']):
            exit_code = main()
            assert exit_code == 1


def test_install_unsupported_platform_mocked():
    """Test install command fails on unsupported platform (mocked)"""
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    
    mock_platform = PlatformInfo(
        os=OS.UNSUPPORTED,
        arch=Arch.UNSUPPORTED,
        shell=Shell.BASH,
        shell_config_file=""
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = False
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('sys.argv', ['mk', 'install', '--all']):
            exit_code = main()
            assert exit_code == 1


def test_init_config_file_not_found_mocked(tmp_path, monkeypatch):
    """Test init command handles missing config file gracefully (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.config.ConfigManager') as mock_config_class:
            mock_config = mock_config_class.return_value
            mock_config.load_with_priority.side_effect = FileNotFoundError("Config file not found")
            
            with patch('sys.argv', ['mk', 'init', '--config', 'nonexistent.yaml']):
                exit_code = main()
                assert exit_code == 2


def test_init_config_validation_error_mocked(tmp_path, monkeypatch):
    """Test init command handles config validation errors (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.config import Config
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.config.ConfigManager') as mock_config_class:
            mock_config = mock_config_class.return_value
            mock_config.load_with_priority.return_value = Config()
            mock_config.validate.return_value = ["Invalid tool name: invalid-tool"]
            
            with patch('sys.argv', ['mk', 'init']):
                exit_code = main()
                assert exit_code == 2


def test_init_keyboard_interrupt_mocked(tmp_path, monkeypatch):
    """Test init command handles keyboard interrupt gracefully (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.side_effect = KeyboardInterrupt()
            
            with patch('sys.argv', ['mk', 'init', '--dry-run']):
                exit_code = main()
                assert exit_code == 130


def test_upgrade_keyboard_interrupt_mocked(tmp_path, monkeypatch):
    """Test upgrade command handles keyboard interrupt gracefully (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_upgrade.side_effect = KeyboardInterrupt()
            
            with patch('sys.argv', ['mk', 'upgrade', '--all', '--dry-run']):
                exit_code = main()
                assert exit_code == 130


def test_install_keyboard_interrupt_mocked(tmp_path, monkeypatch):
    """Test install command handles keyboard interrupt gracefully (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.install_all_tools.side_effect = KeyboardInterrupt()
            
            with patch('sys.argv', ['mk', 'install', '--all', '--dry-run']):
                exit_code = main()
                assert exit_code == 130


def test_init_unexpected_exception_mocked(tmp_path, monkeypatch):
    """Test init command handles unexpected exceptions (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run_init.side_effect = RuntimeError("Unexpected error")
            
            with patch('sys.argv', ['mk', 'init', '--dry-run']):
                exit_code = main()
                assert exit_code == 1


def test_upgrade_no_installed_tools_mocked(tmp_path, monkeypatch):
    """Test upgrade command when no tools are installed (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.tool_detector import ToolStatus
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.tool_detector.ToolDetector') as mock_tool_detector_class:
            mock_tool_detector = mock_tool_detector_class.return_value
            mock_tool_detector.detect_all_tools.return_value = {
                'nvm': ToolStatus('nvm', False, None, None),
                'node': ToolStatus('node', False, None, None),
            }
            
            with patch('sys.argv', ['mk', 'upgrade', '--all', '--dry-run']):
                exit_code = main()
                assert exit_code == 0


def test_init_with_save_config_mocked(tmp_path, monkeypatch):
    """Test init command saves config when --save-config is used (mocked)"""
    monkeypatch.chdir(tmp_path)
    
    from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
    from mono_kickstart.config import Config
    from mono_kickstart.installer_base import InstallReport, InstallResult
    
    mock_platform = PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(tmp_path / ".bashrc")
    )
    
    with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector_class:
        mock_detector = mock_detector_class.return_value
        mock_detector.is_supported.return_value = True
        mock_detector.detect_all.return_value = mock_platform
        
        with patch('mono_kickstart.config.ConfigManager') as mock_config_class:
            mock_config = mock_config_class.return_value
            mock_config.load_with_priority.return_value = Config()
            mock_config.validate.return_value = []
            
            with patch('mono_kickstart.orchestrator.InstallOrchestrator') as mock_orch_class:
                mock_orch = mock_orch_class.return_value
                mock_orch.run_init.return_value = {
                    'nvm': InstallReport('nvm', InstallResult.SUCCESS, 'Installed successfully', '0.40.4'),
                }
                mock_orch.print_summary.return_value = None
                
                with patch('sys.argv', ['mk', 'init', '--save-config', '--dry-run']):
                    exit_code = main()
                    
                    assert exit_code == 0
                    # Verify save_to_file was called
                    assert mock_config.save_to_file.called
