"""GitHub Copilot CLI 安装器单元测试

测试 GitHub Copilot CLI 安装器的各种场景，包括安装、升级、验证等。
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from mono_kickstart.config import ToolConfig
from mono_kickstart.installer_base import InstallResult
from mono_kickstart.installers.copilot_installer import CopilotCLIInstaller
from mono_kickstart.platform_detector import Arch, OS, PlatformInfo, Shell


@pytest.fixture
def platform_info_macos():
    """创建测试用的 macOS 平台信息"""
    return PlatformInfo(
        os=OS.MACOS,
        arch=Arch.ARM64,
        shell=Shell.ZSH,
        shell_config_file=str(Path.home() / ".zshrc")
    )


@pytest.fixture
def platform_info_linux():
    """创建测试用的 Linux 平台信息"""
    return PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(Path.home() / ".bashrc")
    )


@pytest.fixture
def platform_info_unsupported():
    """创建测试用的不支持平台信息（Windows）"""
    return PlatformInfo(
        os=OS.UNSUPPORTED,
        arch=Arch.X86_64,
        shell=Shell.UNKNOWN,
        shell_config_file=""
    )


@pytest.fixture
def tool_config():
    """创建测试用的工具配置"""
    return ToolConfig(enabled=True)


@pytest.fixture
def copilot_installer(platform_info_macos, tool_config):
    """创建 Copilot CLI 安装器实例"""
    return CopilotCLIInstaller(platform_info_macos, tool_config)


class TestCopilotCLIInstaller:
    """GitHub Copilot CLI 安装器测试类"""
    
    def test_init_sets_min_node_version(self, platform_info_macos, tool_config):
        """测试初始化时设置最低 Node.js 版本"""
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        assert installer.min_node_version == 22
    
    def test_verify_copilot_not_in_path(self, copilot_installer):
        """测试验证 Copilot CLI 不在 PATH 中"""
        with patch('shutil.which', return_value=None):
            assert copilot_installer.verify() is False
    
    def test_verify_copilot_in_path_but_command_fails(self, copilot_installer):
        """测试验证 Copilot CLI 在 PATH 中但命令执行失败"""
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                copilot_installer,
                'run_command',
                return_value=(1, "", "command failed")
            ):
                assert copilot_installer.verify() is False
    
    def test_verify_copilot_installed_and_working(self, copilot_installer):
        """测试验证 Copilot CLI 已安装且可用"""
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                copilot_installer,
                'run_command',
                return_value=(0, "1.0.0", "")
            ):
                assert copilot_installer.verify() is True
    
    def test_get_installed_version_not_installed(self, copilot_installer):
        """测试获取版本时 Copilot CLI 未安装"""
        with patch('shutil.which', return_value=None):
            version = copilot_installer._get_installed_version()
            assert version is None
    
    def test_get_installed_version_command_failed(self, copilot_installer):
        """测试获取版本时命令执行失败"""
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                copilot_installer,
                'run_command',
                return_value=(1, "", "error")
            ):
                version = copilot_installer._get_installed_version()
                assert version is None
    
    def test_get_installed_version_success(self, copilot_installer):
        """测试成功获取已安装版本"""
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                copilot_installer,
                'run_command',
                return_value=(0, "1.0.0\n", "")
            ):
                version = copilot_installer._get_installed_version()
                assert version == "1.0.0"
    
    def test_check_node_version_node_not_installed(self, copilot_installer):
        """测试检查 Node.js 版本时 Node.js 未安装"""
        with patch('shutil.which', return_value=None):
            ok, error = copilot_installer._check_node_version()
            assert ok is False
            assert "Node.js 未安装" in error
    
    def test_check_node_version_command_failed(self, copilot_installer):
        """测试检查 Node.js 版本时命令执行失败"""
        with patch('shutil.which', return_value="/usr/local/bin/node"):
            with patch.object(
                copilot_installer,
                'run_command',
                return_value=(1, "", "error")
            ):
                ok, error = copilot_installer._check_node_version()
                assert ok is False
                assert "无法获取 Node.js 版本信息" in error
    
    def test_check_node_version_invalid_format(self, copilot_installer):
        """测试检查 Node.js 版本时版本格式无效"""
        with patch('shutil.which', return_value="/usr/local/bin/node"):
            with patch.object(
                copilot_installer,
                'run_command',
                return_value=(0, "invalid", "")
            ):
                ok, error = copilot_installer._check_node_version()
                assert ok is False
                assert "无法解析 Node.js 版本号" in error
    
    def test_check_node_version_too_low(self, copilot_installer):
        """测试检查 Node.js 版本过低"""
        with patch('shutil.which', return_value="/usr/local/bin/node"):
            with patch.object(
                copilot_installer,
                'run_command',
                return_value=(0, "v20.0.0", "")
            ):
                ok, error = copilot_installer._check_node_version()
                assert ok is False
                assert "Node.js 版本过低" in error
                assert "v20.0.0" in error
                assert "v22.0.0" in error
    
    def test_check_node_version_exactly_minimum(self, copilot_installer):
        """测试检查 Node.js 版本刚好满足最低要求"""
        with patch('shutil.which', return_value="/usr/local/bin/node"):
            with patch.object(
                copilot_installer,
                'run_command',
                return_value=(0, "v22.0.0", "")
            ):
                ok, error = copilot_installer._check_node_version()
                assert ok is True
                assert error is None
    
    def test_check_node_version_above_minimum(self, copilot_installer):
        """测试检查 Node.js 版本高于最低要求"""
        with patch('shutil.which', return_value="/usr/local/bin/node"):
            with patch.object(
                copilot_installer,
                'run_command',
                return_value=(0, "v23.1.0", "")
            ):
                ok, error = copilot_installer._check_node_version()
                assert ok is True
                assert error is None
    
    def test_install_via_npm_success(self, copilot_installer):
        """测试通过 npm 安装成功"""
        with patch.object(
            copilot_installer,
            'run_command',
            return_value=(0, "added 1 package", "")
        ):
            success, error = copilot_installer._install_via_npm()
            assert success is True
            assert error == ""
    
    def test_install_via_npm_failed(self, copilot_installer):
        """测试通过 npm 安装失败"""
        with patch.object(
            copilot_installer,
            'run_command',
            return_value=(1, "", "npm ERR! Installation failed")
        ):
            success, error = copilot_installer._install_via_npm()
            assert success is False
            assert "npm ERR!" in error
    
    def test_install_on_unsupported_platform(self, platform_info_unsupported, tool_config):
        """测试在不支持的平台上安装"""
        installer = CopilotCLIInstaller(platform_info_unsupported, tool_config)
        report = installer.install()
        
        assert report.result == InstallResult.FAILED
        assert report.tool_name == "copilot-cli"
        assert "不支持的操作系统" in report.message
        assert "仅支持 macOS 和 Linux" in report.error
    
    def test_install_already_installed(self, copilot_installer):
        """测试安装时 Copilot CLI 已安装"""
        with patch.object(copilot_installer, 'verify', return_value=True):
            with patch.object(
                copilot_installer,
                '_get_installed_version',
                return_value="1.0.0"
            ):
                report = copilot_installer.install()
                
                assert report.result == InstallResult.SKIPPED
                assert report.tool_name == "copilot-cli"
                assert report.version == "1.0.0"
                assert "已安装" in report.message
    
    def test_install_node_version_too_low(self, copilot_installer):
        """测试安装时 Node.js 版本过低"""
        with patch.object(copilot_installer, 'verify', return_value=False):
            with patch.object(
                copilot_installer,
                '_check_node_version',
                return_value=(False, "Node.js 版本过低")
            ):
                report = copilot_installer.install()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "copilot-cli"
                assert "Node.js 版本不满足要求" in report.message
                assert "Node.js 版本过低" in report.error
    
    def test_install_npm_installation_failed(self, copilot_installer):
        """测试安装时 npm 安装失败"""
        with patch.object(copilot_installer, 'verify', return_value=False):
            with patch.object(
                copilot_installer,
                '_check_node_version',
                return_value=(True, None)
            ):
                with patch.object(
                    copilot_installer,
                    '_install_via_npm',
                    return_value=(False, "npm error")
                ):
                    report = copilot_installer.install()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "copilot-cli"
                    assert "npm 安装" in report.message
                    assert "npm error" in report.error
    
    def test_install_verification_failed(self, copilot_installer):
        """测试安装后验证失败"""
        verify_calls = [False, False]  # 第一次检查是否已安装，第二次验证安装结果
        
        with patch.object(
            copilot_installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(
                copilot_installer,
                '_check_node_version',
                return_value=(True, None)
            ):
                with patch.object(
                    copilot_installer,
                    '_install_via_npm',
                    return_value=(True, "")
                ):
                    report = copilot_installer.install()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "copilot-cli"
                    assert "验证失败" in report.message
    
    def test_install_success(self, copilot_installer):
        """测试成功安装 Copilot CLI"""
        verify_calls = [False, True]  # 第一次未安装，第二次验证成功
        
        with patch.object(
            copilot_installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(
                copilot_installer,
                '_check_node_version',
                return_value=(True, None)
            ):
                with patch.object(
                    copilot_installer,
                    '_install_via_npm',
                    return_value=(True, "")
                ):
                    with patch.object(
                        copilot_installer,
                        '_get_installed_version',
                        return_value="1.0.0"
                    ):
                        report = copilot_installer.install()
                        
                        assert report.result == InstallResult.SUCCESS
                        assert report.tool_name == "copilot-cli"
                        assert report.version == "1.0.0"
                        assert "成功" in report.message
    
    def test_install_exception_handling(self, copilot_installer):
        """测试安装过程中异常处理"""
        with patch.object(copilot_installer, 'verify', return_value=False):
            with patch.object(
                copilot_installer,
                '_check_node_version',
                side_effect=Exception("Unexpected error")
            ):
                report = copilot_installer.install()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "copilot-cli"
                assert "异常" in report.message
                assert "Unexpected error" in report.error
    
    def test_upgrade_on_unsupported_platform(self, platform_info_unsupported, tool_config):
        """测试在不支持的平台上升级"""
        installer = CopilotCLIInstaller(platform_info_unsupported, tool_config)
        report = installer.upgrade()
        
        assert report.result == InstallResult.FAILED
        assert report.tool_name == "copilot-cli"
        assert "不支持的操作系统" in report.message
        assert "仅支持 macOS 和 Linux" in report.error
    
    def test_upgrade_not_installed(self, copilot_installer):
        """测试升级时 Copilot CLI 未安装"""
        with patch.object(copilot_installer, 'verify', return_value=False):
            report = copilot_installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "copilot-cli"
            assert "未安装" in report.message
    
    def test_upgrade_command_failed(self, copilot_installer):
        """测试升级时命令执行失败"""
        with patch.object(copilot_installer, 'verify', return_value=True):
            with patch.object(
                copilot_installer,
                '_get_installed_version',
                return_value="1.0.0"
            ):
                with patch.object(
                    copilot_installer,
                    'run_command',
                    return_value=(1, "", "npm ERR! Update failed")
                ):
                    report = copilot_installer.upgrade()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "copilot-cli"
                    assert "升级" in report.message
                    assert "npm ERR!" in report.error
    
    def test_upgrade_verification_failed(self, copilot_installer):
        """测试升级后验证失败"""
        verify_calls = [True, False]  # 第一次已安装，第二次验证失败
        
        with patch.object(
            copilot_installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(
                copilot_installer,
                '_get_installed_version',
                return_value="1.0.0"
            ):
                with patch.object(
                    copilot_installer,
                    'run_command',
                    return_value=(0, "updated 1 package", "")
                ):
                    report = copilot_installer.upgrade()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "copilot-cli"
                    assert "验证失败" in report.message
    
    def test_upgrade_success(self, copilot_installer):
        """测试成功升级 Copilot CLI"""
        verify_calls = [True, True]  # 第一次已安装，第二次验证成功
        version_calls = ["1.0.0", "1.1.0"]  # 升级前后的版本
        
        with patch.object(
            copilot_installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(
                copilot_installer,
                '_get_installed_version',
                side_effect=version_calls
            ):
                with patch.object(
                    copilot_installer,
                    'run_command',
                    return_value=(0, "updated 1 package", "")
                ):
                    report = copilot_installer.upgrade()
                    
                    assert report.result == InstallResult.SUCCESS
                    assert report.tool_name == "copilot-cli"
                    assert report.version == "1.1.0"
                    assert "1.0.0" in report.message
                    assert "1.1.0" in report.message
                    assert "成功" in report.message
    
    def test_upgrade_exception_handling(self, copilot_installer):
        """测试升级过程中异常处理"""
        with patch.object(copilot_installer, 'verify', return_value=True):
            with patch.object(
                copilot_installer,
                '_get_installed_version',
                side_effect=Exception("Unexpected error")
            ):
                report = copilot_installer.upgrade()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "copilot-cli"
                assert "异常" in report.message
                assert "Unexpected error" in report.error
    
    def test_install_on_linux(self, platform_info_linux, tool_config):
        """测试在 Linux 平台上安装"""
        installer = CopilotCLIInstaller(platform_info_linux, tool_config)
        
        verify_calls = [False, True]
        
        with patch.object(installer, 'verify', side_effect=verify_calls):
            with patch.object(
                installer,
                '_check_node_version',
                return_value=(True, None)
            ):
                with patch.object(
                    installer,
                    '_install_via_npm',
                    return_value=(True, "")
                ):
                    with patch.object(
                        installer,
                        '_get_installed_version',
                        return_value="1.0.0"
                    ):
                        report = installer.install()
                        
                        assert report.result == InstallResult.SUCCESS
                        assert report.tool_name == "copilot-cli"
    
    def test_install_on_macos(self, platform_info_macos, tool_config):
        """测试在 macOS 平台上安装"""
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        verify_calls = [False, True]
        
        with patch.object(installer, 'verify', side_effect=verify_calls):
            with patch.object(
                installer,
                '_check_node_version',
                return_value=(True, None)
            ):
                with patch.object(
                    installer,
                    '_install_via_npm',
                    return_value=(True, "")
                ):
                    with patch.object(
                        installer,
                        '_get_installed_version',
                        return_value="1.0.0"
                    ):
                        report = installer.install()
                        
                        assert report.result == InstallResult.SUCCESS
                        assert report.tool_name == "copilot-cli"
