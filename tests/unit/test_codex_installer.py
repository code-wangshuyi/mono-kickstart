"""单元测试：Codex CLI 安装器

该模块测试 Codex CLI 安装器的各种场景，包括安装方式选择逻辑。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.mono_kickstart.config import ToolConfig
from src.mono_kickstart.installer_base import InstallResult
from src.mono_kickstart.installers.codex_installer import CodexInstaller
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
    """创建 Codex CLI 安装器实例"""
    with patch('shutil.which', return_value=None):
        return CodexInstaller(platform_info, tool_config)


class TestCodexInstallerDetermineInstallMethod:
    """测试 Codex CLI 安装器的安装方式选择逻辑"""
    
    def test_determine_method_when_bun_installed(self, platform_info):
        """测试 Bun 已安装时选择 Bun"""
        config = ToolConfig(enabled=True)
        with patch('shutil.which', return_value="/usr/local/bin/bun"):
            installer = CodexInstaller(platform_info, config)
            assert installer.install_method == 'bun'
    
    def test_determine_method_when_bun_not_installed(self, platform_info):
        """测试 Bun 未安装时选择 npm"""
        config = ToolConfig(enabled=True)
        with patch('shutil.which', return_value=None):
            installer = CodexInstaller(platform_info, config)
            assert installer.install_method == 'npm'
    
    def test_determine_method_with_config_override_bun(self, platform_info):
        """测试配置指定使用 Bun"""
        config = ToolConfig(enabled=True, install_via='bun')
        with patch('shutil.which', return_value=None):
            installer = CodexInstaller(platform_info, config)
            assert installer.install_method == 'bun'
    
    def test_determine_method_with_config_override_npm(self, platform_info):
        """测试配置指定使用 npm"""
        config = ToolConfig(enabled=True, install_via='npm')
        with patch('shutil.which', return_value="/usr/local/bin/bun"):
            installer = CodexInstaller(platform_info, config)
            assert installer.install_method == 'npm'
    
    def test_determine_method_with_config_case_insensitive(self, platform_info):
        """测试配置大小写不敏感"""
        config = ToolConfig(enabled=True, install_via='BUN')
        with patch('shutil.which', return_value=None):
            installer = CodexInstaller(platform_info, config)
            assert installer.install_method == 'bun'


class TestCodexInstallerVerify:
    """测试 Codex CLI 安装器的验证功能"""
    
    def test_verify_when_codex_installed(self, installer):
        """测试 Codex CLI 已安装时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/codex"), \
             patch.object(installer, 'run_command', return_value=(0, "1.0.0", "")):
            assert installer.verify() is True
    
    def test_verify_when_codex_not_in_path(self, installer):
        """测试 Codex CLI 不在 PATH 中时的验证"""
        with patch('shutil.which', return_value=None):
            assert installer.verify() is False
    
    def test_verify_when_codex_command_fails(self, installer):
        """测试 Codex CLI 命令执行失败时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/codex"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            assert installer.verify() is False


class TestCodexInstallerGetVersion:
    """测试 Codex CLI 安装器的版本获取功能"""
    
    def test_get_version_success(self, installer):
        """测试成功获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/codex"), \
             patch.object(installer, 'run_command', return_value=(0, "2.1.0", "")):
            version = installer._get_installed_version()
            assert version == "2.1.0"
    
    def test_get_version_when_not_installed(self, installer):
        """测试 Codex CLI 未安装时获取版本"""
        with patch('shutil.which', return_value=None):
            version = installer._get_installed_version()
            assert version is None
    
    def test_get_version_when_command_fails(self, installer):
        """测试命令失败时获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/codex"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            version = installer._get_installed_version()
            assert version is None


class TestCodexInstallerInstall:
    """测试 Codex CLI 安装器的安装功能"""
    
    def test_install_when_already_installed(self, installer):
        """测试 Codex CLI 已安装时跳过安装"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', return_value="2.0.0"):
            report = installer.install()
            
            assert report.result == InstallResult.SKIPPED
            assert report.tool_name == "codex"
            assert report.version == "2.0.0"
            assert "已安装" in report.message
    
    def test_install_with_bun_success(self, platform_info):
        """测试使用 Bun 成功安装 Codex CLI"""
        config = ToolConfig(enabled=True, install_via='bun')
        
        with patch('shutil.which') as mock_which, \
             patch.object(CodexInstaller, 'verify', side_effect=[False, True]), \
             patch.object(CodexInstaller, 'run_command', return_value=(0, "installed", "")), \
             patch.object(CodexInstaller, '_get_installed_version', return_value="2.1.0"):
            
            def which_side_effect(cmd):
                if cmd == "bun":
                    return "/usr/local/bin/bun"
                elif cmd == "codex":
                    return None
                return None
            
            mock_which.side_effect = which_side_effect
            
            installer = CodexInstaller(platform_info, config)
            report = installer.install()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "codex"
            assert report.version == "2.1.0"
            assert "bun" in report.message.lower()
    
    def test_install_with_npm_success(self, platform_info):
        """测试使用 npm 成功安装 Codex CLI"""
        config = ToolConfig(enabled=True, install_via='npm')
        
        with patch('shutil.which') as mock_which, \
             patch.object(CodexInstaller, 'verify', side_effect=[False, True]), \
             patch.object(CodexInstaller, 'run_command', return_value=(0, "installed", "")), \
             patch.object(CodexInstaller, '_get_installed_version', return_value="2.1.0"):
            
            def which_side_effect(cmd):
                if cmd == "npm":
                    return "/usr/local/bin/npm"
                elif cmd == "codex":
                    return None
                return None
            
            mock_which.side_effect = which_side_effect
            
            installer = CodexInstaller(platform_info, config)
            report = installer.install()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "codex"
            assert report.version == "2.1.0"
            assert "npm" in report.message.lower()
    
    def test_install_with_bun_but_bun_not_available(self, platform_info):
        """测试配置使用 Bun 但 Bun 未安装"""
        config = ToolConfig(enabled=True, install_via='bun')
        
        with patch('shutil.which', return_value=None), \
             patch.object(CodexInstaller, 'verify', return_value=False):
            
            installer = CodexInstaller(platform_info, config)
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "codex"
            assert "Bun 未安装" in report.message
    
    def test_install_with_npm_but_npm_not_available(self, platform_info):
        """测试配置使用 npm 但 npm 未安装"""
        config = ToolConfig(enabled=True, install_via='npm')
        
        with patch('shutil.which', return_value=None), \
             patch.object(CodexInstaller, 'verify', return_value=False):
            
            installer = CodexInstaller(platform_info, config)
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "codex"
            assert "npm 未安装" in report.message
    
    def test_install_command_fails(self, installer):
        """测试安装命令执行失败"""
        with patch('shutil.which') as mock_which, \
             patch.object(installer, 'verify', return_value=False), \
             patch.object(installer, 'run_command', return_value=(1, "", "install failed")):
            
            mock_which.return_value = "/usr/local/bin/npm"
            
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "codex"
            assert "失败" in report.message
    
    def test_install_verification_fails(self, installer):
        """测试安装后验证失败"""
        with patch('shutil.which', return_value="/usr/local/bin/npm"), \
             patch.object(installer, 'verify', side_effect=[False, False]), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")):
            
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "codex"
            assert "验证失败" in report.message
    
    def test_install_exception(self, installer):
        """测试安装过程中发生异常"""
        with patch('shutil.which', return_value="/usr/local/bin/npm"), \
             patch.object(installer, 'verify', return_value=False), \
             patch.object(installer, 'run_command', side_effect=Exception("test error")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "codex"
            assert "异常" in report.message
            assert "test error" in report.error


class TestCodexInstallerUpgrade:
    """测试 Codex CLI 安装器的升级功能"""
    
    def test_upgrade_when_not_installed(self, installer):
        """测试 Codex CLI 未安装时无法升级"""
        with patch.object(installer, 'verify', return_value=False):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "codex"
            assert "未安装" in report.message
    
    def test_upgrade_with_bun_success(self, platform_info):
        """测试使用 Bun 成功升级 Codex CLI"""
        config = ToolConfig(enabled=True, install_via='bun')
        
        with patch('shutil.which') as mock_which, \
             patch.object(CodexInstaller, 'verify', return_value=True), \
             patch.object(CodexInstaller, '_get_installed_version', side_effect=["2.0.0", "2.1.0"]), \
             patch.object(CodexInstaller, 'run_command', return_value=(0, "upgraded", "")):
            
            def which_side_effect(cmd):
                if cmd == "bun":
                    return "/usr/local/bin/bun"
                elif cmd == "codex":
                    return "/usr/local/bin/codex"
                return None
            
            mock_which.side_effect = which_side_effect
            
            installer = CodexInstaller(platform_info, config)
            report = installer.upgrade()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "codex"
            assert report.version == "2.1.0"
            assert "2.0.0" in report.message
            assert "2.1.0" in report.message
    
    def test_upgrade_with_npm_success(self, platform_info):
        """测试使用 npm 成功升级 Codex CLI"""
        config = ToolConfig(enabled=True, install_via='npm')
        
        with patch('shutil.which') as mock_which, \
             patch.object(CodexInstaller, 'verify', return_value=True), \
             patch.object(CodexInstaller, '_get_installed_version', side_effect=["2.0.0", "2.1.0"]), \
             patch.object(CodexInstaller, 'run_command', return_value=(0, "upgraded", "")):
            
            def which_side_effect(cmd):
                if cmd == "npm":
                    return "/usr/local/bin/npm"
                elif cmd == "codex":
                    return "/usr/local/bin/codex"
                return None
            
            mock_which.side_effect = which_side_effect
            
            installer = CodexInstaller(platform_info, config)
            report = installer.upgrade()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "codex"
            assert report.version == "2.1.0"
    
    def test_upgrade_command_fails(self, installer):
        """测试升级命令执行失败"""
        with patch('shutil.which', return_value="/usr/local/bin/npm"), \
             patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', return_value="2.0.0"), \
             patch.object(installer, 'run_command', return_value=(1, "", "upgrade failed")):
            
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "codex"
            assert "失败" in report.message
    
    def test_upgrade_verification_fails(self, installer):
        """测试升级后验证失败"""
        with patch('shutil.which', return_value="/usr/local/bin/npm"), \
             patch.object(installer, 'verify', side_effect=[True, False]), \
             patch.object(installer, '_get_installed_version', return_value="2.0.0"), \
             patch.object(installer, 'run_command', return_value=(0, "upgraded", "")):
            
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "codex"
            assert "验证失败" in report.message
    
    def test_upgrade_exception(self, installer):
        """测试升级过程中发生异常"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', side_effect=Exception("test error")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "codex"
            assert "异常" in report.message
            assert "test error" in report.error
