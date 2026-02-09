"""单元测试：Spec Kit 安装器

该模块测试 Spec Kit 安装器的各种场景。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.mono_kickstart.config import ToolConfig
from src.mono_kickstart.installer_base import InstallResult
from src.mono_kickstart.installers.spec_kit_installer import SpecKitInstaller
from src.mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell


@pytest.fixture
def platform_info():
    """创建测试用的平台信息"""
    return PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file="/home/test/.bashrc"
    )


@pytest.fixture
def tool_config():
    """创建测试用的工具配置"""
    return ToolConfig(enabled=True)


@pytest.fixture
def installer(platform_info, tool_config):
    """创建 Spec Kit 安装器实例"""
    return SpecKitInstaller(platform_info, tool_config)


class TestSpecKitInstallerVerify:
    """测试 Spec Kit 安装器的验证功能"""
    
    def test_verify_when_spec_kit_installed(self, installer):
        """测试 Spec Kit 已安装时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/specify-cli"), \
             patch.object(installer, 'run_command', return_value=(0, "specify-cli 1.0.0", "")):
            assert installer.verify() is True
    
    def test_verify_when_spec_kit_not_in_path(self, installer):
        """测试 Spec Kit 不在 PATH 中时的验证"""
        with patch('shutil.which', return_value=None):
            assert installer.verify() is False
    
    def test_verify_when_spec_kit_command_fails(self, installer):
        """测试 Spec Kit 命令执行失败时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/specify-cli"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            assert installer.verify() is False


class TestSpecKitInstallerGetVersion:
    """测试 Spec Kit 安装器的版本获取功能"""
    
    def test_get_version_success(self, installer):
        """测试成功获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/specify-cli"), \
             patch.object(installer, 'run_command', return_value=(0, "1.2.3", "")):
            version = installer._get_installed_version()
            assert version == "1.2.3"
    
    def test_get_version_when_not_installed(self, installer):
        """测试 Spec Kit 未安装时获取版本"""
        with patch('shutil.which', return_value=None):
            version = installer._get_installed_version()
            assert version is None
    
    def test_get_version_when_command_fails(self, installer):
        """测试命令失败时获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/specify-cli"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            version = installer._get_installed_version()
            assert version is None


class TestSpecKitInstallerInstall:
    """测试 Spec Kit 安装器的安装功能"""
    
    def test_install_when_already_installed(self, installer):
        """测试 Spec Kit 已安装时跳过安装"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"):
            report = installer.install()
            
            assert report.result == InstallResult.SKIPPED
            assert report.tool_name == "spec-kit"
            assert report.version == "1.0.0"
            assert "已安装" in report.message
    
    def test_install_when_uv_not_available(self, installer):
        """测试 uv 未安装时无法安装 Spec Kit"""
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value=None):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "spec-kit"
            assert "uv 未安装" in report.message
    
    def test_install_success(self, installer):
        """测试成功安装 Spec Kit"""
        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")), \
             patch.object(installer, '_get_installed_version', return_value="1.2.3"):
            report = installer.install()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "spec-kit"
            assert report.version == "1.2.3"
            assert "成功" in report.message
    
    def test_install_command_fails(self, installer):
        """测试安装命令执行失败"""
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, 'run_command', return_value=(1, "", "install failed")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "spec-kit"
            assert "失败" in report.message
            assert report.error is not None
    
    def test_install_verification_fails(self, installer):
        """测试安装后验证失败"""
        with patch.object(installer, 'verify', side_effect=[False, False]), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "spec-kit"
            assert "验证失败" in report.message
    
    def test_install_exception(self, installer):
        """测试安装过程中发生异常"""
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, 'run_command', side_effect=Exception("test error")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "spec-kit"
            assert "异常" in report.message
            assert "test error" in report.error


class TestSpecKitInstallerUpgrade:
    """测试 Spec Kit 安装器的升级功能"""
    
    def test_upgrade_when_not_installed(self, installer):
        """测试 Spec Kit 未安装时无法升级"""
        with patch.object(installer, 'verify', return_value=False):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "spec-kit"
            assert "未安装" in report.message
    
    def test_upgrade_when_uv_not_available(self, installer):
        """测试 uv 未安装时无法升级 Spec Kit"""
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value=None):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "spec-kit"
            assert "uv 未安装" in report.message
    
    def test_upgrade_success(self, installer):
        """测试成功升级 Spec Kit"""
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, '_get_installed_version', side_effect=["1.0.0", "1.2.3"]), \
             patch.object(installer, 'run_command', return_value=(0, "upgraded", "")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "spec-kit"
            assert report.version == "1.2.3"
            assert "1.0.0" in report.message
            assert "1.2.3" in report.message
    
    def test_upgrade_command_fails(self, installer):
        """测试升级命令执行失败"""
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"), \
             patch.object(installer, 'run_command', return_value=(1, "", "upgrade failed")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "spec-kit"
            assert "失败" in report.message
    
    def test_upgrade_verification_fails(self, installer):
        """测试升级后验证失败"""
        with patch.object(installer, 'verify', side_effect=[True, False]), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"), \
             patch.object(installer, 'run_command', return_value=(0, "upgraded", "")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "spec-kit"
            assert "验证失败" in report.message
    
    def test_upgrade_exception(self, installer):
        """测试升级过程中发生异常"""
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, '_get_installed_version', side_effect=Exception("test error")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "spec-kit"
            assert "异常" in report.message
            assert "test error" in report.error


class TestSpecKitInstallerGitHubRepo:
    """测试 Spec Kit 安装器的 GitHub 仓库地址"""
    
    def test_github_repo_url(self, installer):
        """测试 GitHub 仓库地址正确"""
        assert installer.github_repo == "git+https://github.com/github/spec-kit.git"
    
    def test_install_uses_correct_command(self, installer):
        """测试安装命令使用正确的 GitHub 仓库地址"""
        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0") as mock_version:
            
            # Mock run_command to capture the command
            commands_run = []
            def capture_command(cmd, **kwargs):
                commands_run.append(cmd)
                return (0, "installed", "")
            
            with patch.object(installer, 'run_command', side_effect=capture_command):
                report = installer.install()
            
            # Verify the command includes the correct GitHub repo
            assert len(commands_run) == 1
            assert "uv tool install specify-cli --from git+https://github.com/github/spec-kit.git" in commands_run[0]
    
    def test_upgrade_uses_correct_command(self, installer):
        """测试升级命令使用正确的 GitHub 仓库地址和 --force 参数"""
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, '_get_installed_version', side_effect=["1.0.0", "1.2.3"]):
            
            # Mock run_command to capture the command
            commands_run = []
            def capture_command(cmd, **kwargs):
                commands_run.append(cmd)
                return (0, "upgraded", "")
            
            with patch.object(installer, 'run_command', side_effect=capture_command):
                report = installer.upgrade()
            
            # Verify the command includes --force and the correct GitHub repo
            assert len(commands_run) == 1
            assert "uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git" in commands_run[0]
