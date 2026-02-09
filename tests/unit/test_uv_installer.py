"""单元测试：uv 安装器

该模块测试 uv 安装器的各种场景。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.mono_kickstart.config import ToolConfig
from src.mono_kickstart.installer_base import InstallResult
from src.mono_kickstart.installers.uv_installer import UVInstaller
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
    """创建 uv 安装器实例"""
    return UVInstaller(platform_info, tool_config)


class TestUVInstallerVerify:
    """测试 uv 安装器的验证功能"""
    
    def test_verify_when_uv_installed(self, installer):
        """测试 uv 已安装时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, 'run_command', return_value=(0, "uv 0.1.0", "")):
            assert installer.verify() is True
    
    def test_verify_when_uv_not_in_path(self, installer):
        """测试 uv 不在 PATH 中时的验证"""
        with patch('shutil.which', return_value=None):
            assert installer.verify() is False
    
    def test_verify_when_uv_command_fails(self, installer):
        """测试 uv 命令执行失败时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            assert installer.verify() is False


class TestUVInstallerGetVersion:
    """测试 uv 安装器的版本获取功能"""
    
    def test_get_version_success(self, installer):
        """测试成功获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, 'run_command', return_value=(0, "uv 0.1.5", "")):
            version = installer._get_installed_version()
            assert version == "0.1.5"
    
    def test_get_version_when_not_installed(self, installer):
        """测试 uv 未安装时获取版本"""
        with patch('shutil.which', return_value=None):
            version = installer._get_installed_version()
            assert version is None
    
    def test_get_version_when_command_fails(self, installer):
        """测试命令失败时获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            version = installer._get_installed_version()
            assert version is None
    
    def test_get_version_with_invalid_output(self, installer):
        """测试版本输出格式不正确时"""
        with patch('shutil.which', return_value="/usr/local/bin/uv"), \
             patch.object(installer, 'run_command', return_value=(0, "invalid", "")):
            version = installer._get_installed_version()
            assert version is None


class TestUVInstallerInstall:
    """测试 uv 安装器的安装功能"""
    
    def test_install_when_already_installed(self, installer):
        """测试 uv 已安装时跳过安装"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', return_value="0.1.0"):
            report = installer.install()
            
            assert report.result == InstallResult.SKIPPED
            assert report.tool_name == "uv"
            assert report.version == "0.1.0"
            assert "已安装" in report.message
    
    def test_install_success(self, installer):
        """测试成功安装 uv"""
        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")), \
             patch.object(installer, '_get_installed_version', return_value="0.1.5"):
            report = installer.install()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "uv"
            assert report.version == "0.1.5"
            assert "成功" in report.message
    
    def test_install_script_fails(self, installer):
        """测试安装脚本执行失败"""
        with patch.object(installer, 'verify', return_value=False), \
             patch.object(installer, 'run_command', return_value=(1, "", "install failed")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uv"
            assert "失败" in report.message
            assert report.error is not None
    
    def test_install_verification_fails(self, installer):
        """测试安装后验证失败"""
        with patch.object(installer, 'verify', side_effect=[False, False]), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uv"
            assert "验证失败" in report.message
    
    def test_install_exception(self, installer):
        """测试安装过程中发生异常"""
        with patch.object(installer, 'verify', return_value=False), \
             patch.object(installer, 'run_command', side_effect=Exception("test error")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uv"
            assert "异常" in report.message
            assert "test error" in report.error


class TestUVInstallerUpgrade:
    """测试 uv 安装器的升级功能"""
    
    def test_upgrade_when_not_installed(self, installer):
        """测试 uv 未安装时无法升级"""
        with patch.object(installer, 'verify', return_value=False):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uv"
            assert "未安装" in report.message
    
    def test_upgrade_success(self, installer):
        """测试成功升级 uv"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', side_effect=["0.1.0", "0.1.5"]), \
             patch.object(installer, 'run_command', return_value=(0, "upgraded", "")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "uv"
            assert report.version == "0.1.5"
            assert "0.1.0" in report.message
            assert "0.1.5" in report.message
    
    def test_upgrade_command_fails(self, installer):
        """测试升级命令执行失败"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', return_value="0.1.0"), \
             patch.object(installer, 'run_command', return_value=(1, "", "upgrade failed")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uv"
            assert "失败" in report.message
    
    def test_upgrade_verification_fails(self, installer):
        """测试升级后验证失败"""
        with patch.object(installer, 'verify', side_effect=[True, False]), \
             patch.object(installer, '_get_installed_version', return_value="0.1.0"), \
             patch.object(installer, 'run_command', return_value=(0, "upgraded", "")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uv"
            assert "验证失败" in report.message
    
    def test_upgrade_exception(self, installer):
        """测试升级过程中发生异常"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', side_effect=Exception("test error")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uv"
            assert "异常" in report.message
            assert "test error" in report.error


class TestUVInstallerInstallScriptUrl:
    """测试 uv 安装器的安装脚本 URL"""
    
    def test_install_script_url(self, installer):
        """测试安装脚本 URL 正确"""
        assert installer.install_script_url == "https://astral.sh/uv/install.sh"
