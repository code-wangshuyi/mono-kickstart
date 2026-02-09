"""单元测试：BMad Method 安装器

该模块测试 BMad Method 安装器的各种场景。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.mono_kickstart.config import ToolConfig
from src.mono_kickstart.installer_base import InstallResult
from src.mono_kickstart.installers.bmad_installer import BMadInstaller
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
    """创建 BMad Method 安装器实例"""
    return BMadInstaller(platform_info, tool_config)


class TestBMadInstallerDetermineInstallMethod:
    """测试 BMad Method 安装器的安装方式确定功能"""
    
    def test_determine_install_method_with_config(self, platform_info):
        """测试配置中指定安装方式时使用配置的方式"""
        config = ToolConfig(enabled=True, install_via="npx")
        installer = BMadInstaller(platform_info, config)
        assert installer.install_method == "npx"
    
    def test_determine_install_method_with_bun_available(self, platform_info, tool_config):
        """测试 Bun 可用时优先使用 bunx"""
        with patch('shutil.which', side_effect=lambda cmd: "/usr/local/bin/bun" if cmd == "bun" else None):
            installer = BMadInstaller(platform_info, tool_config)
            assert installer.install_method == "bunx"
    
    def test_determine_install_method_without_bun(self, platform_info, tool_config):
        """测试 Bun 不可用时使用 npx"""
        with patch('shutil.which', return_value=None):
            installer = BMadInstaller(platform_info, tool_config)
            assert installer.install_method == "npx"


class TestBMadInstallerVerify:
    """测试 BMad Method 安装器的验证功能"""
    
    def test_verify_when_bmad_installed(self, installer):
        """测试 BMad Method 已安装时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/bmad"), \
             patch.object(installer, 'run_command', return_value=(0, "bmad 1.0.0", "")):
            assert installer.verify() is True
    
    def test_verify_when_bmad_not_in_path(self, installer):
        """测试 BMad Method 不在 PATH 中时的验证"""
        with patch('shutil.which', return_value=None):
            assert installer.verify() is False
    
    def test_verify_when_bmad_command_fails(self, installer):
        """测试 BMad Method 命令执行失败时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/bmad"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            assert installer.verify() is False


class TestBMadInstallerGetVersion:
    """测试 BMad Method 安装器的版本获取功能"""
    
    def test_get_version_success(self, installer):
        """测试成功获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/bmad"), \
             patch.object(installer, 'run_command', return_value=(0, "1.2.3", "")):
            version = installer._get_installed_version()
            assert version == "1.2.3"
    
    def test_get_version_when_not_installed(self, installer):
        """测试 BMad Method 未安装时获取版本"""
        with patch('shutil.which', return_value=None):
            version = installer._get_installed_version()
            assert version is None
    
    def test_get_version_when_command_fails(self, installer):
        """测试命令失败时获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/bmad"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            version = installer._get_installed_version()
            assert version is None


class TestBMadInstallerInstall:
    """测试 BMad Method 安装器的安装功能"""
    
    def test_install_when_already_installed(self, installer):
        """测试 BMad Method 已安装时跳过安装"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"):
            report = installer.install()
            
            assert report.result == InstallResult.SKIPPED
            assert report.tool_name == "bmad-method"
            assert report.version == "1.0.0"
            assert "已安装" in report.message
    
    def test_install_with_bunx_when_bun_not_available(self, platform_info):
        """测试使用 bunx 但 Bun 未安装时失败"""
        config = ToolConfig(enabled=True, install_via="bunx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value=None):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "Bun 未安装" in report.message
    
    def test_install_with_npx_when_npx_not_available(self, platform_info):
        """测试使用 npx 但 npx 未安装时失败"""
        config = ToolConfig(enabled=True, install_via="npx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value=None):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "npx 未安装" in report.message
    
    def test_install_success_with_bunx(self, platform_info):
        """测试使用 bunx 成功安装 BMad Method"""
        config = ToolConfig(enabled=True, install_via="bunx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/bun"), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")), \
             patch.object(installer, '_get_installed_version', return_value="1.2.3"):
            report = installer.install()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "bmad-method"
            assert report.version == "1.2.3"
            assert "成功" in report.message
            assert "bunx" in report.message
    
    def test_install_success_with_npx(self, platform_info):
        """测试使用 npx 成功安装 BMad Method"""
        config = ToolConfig(enabled=True, install_via="npx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")), \
             patch.object(installer, '_get_installed_version', return_value="1.2.3"):
            report = installer.install()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "bmad-method"
            assert report.version == "1.2.3"
            assert "成功" in report.message
            assert "npx" in report.message
    
    def test_install_command_fails(self, installer):
        """测试安装命令执行失败"""
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, 'run_command', return_value=(1, "", "install failed")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "失败" in report.message
            assert report.error is not None
    
    def test_install_verification_fails(self, installer):
        """测试安装后验证失败"""
        with patch.object(installer, 'verify', side_effect=[False, False]), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "验证失败" in report.message
    
    def test_install_exception(self, installer):
        """测试安装过程中发生异常"""
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, 'run_command', side_effect=Exception("test error")):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "异常" in report.message
            assert "test error" in report.error


class TestBMadInstallerUpgrade:
    """测试 BMad Method 安装器的升级功能"""
    
    def test_upgrade_when_not_installed(self, installer):
        """测试 BMad Method 未安装时无法升级"""
        with patch.object(installer, 'verify', return_value=False):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "未安装" in report.message
    
    def test_upgrade_with_bunx_when_bun_not_available(self, platform_info):
        """测试使用 bunx 升级但 Bun 未安装时失败"""
        config = ToolConfig(enabled=True, install_via="bunx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value=None):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "Bun 未安装" in report.message
    
    def test_upgrade_with_npx_when_npx_not_available(self, platform_info):
        """测试使用 npx 升级但 npx 未安装时失败"""
        config = ToolConfig(enabled=True, install_via="npx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value=None):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "npx 未安装" in report.message
    
    def test_upgrade_success_with_bunx(self, platform_info):
        """测试使用 bunx 成功升级 BMad Method"""
        config = ToolConfig(enabled=True, install_via="bunx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/bun"), \
             patch.object(installer, '_get_installed_version', side_effect=["1.0.0", "1.2.3"]), \
             patch.object(installer, 'run_command', return_value=(0, "upgraded", "")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "bmad-method"
            assert report.version == "1.2.3"
            assert "1.0.0" in report.message
            assert "1.2.3" in report.message
    
    def test_upgrade_success_with_npx(self, platform_info):
        """测试使用 npx 成功升级 BMad Method"""
        config = ToolConfig(enabled=True, install_via="npx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, '_get_installed_version', side_effect=["1.0.0", "1.2.3"]), \
             patch.object(installer, 'run_command', return_value=(0, "upgraded", "")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "bmad-method"
            assert report.version == "1.2.3"
            assert "1.0.0" in report.message
            assert "1.2.3" in report.message
    
    def test_upgrade_command_fails(self, installer):
        """测试升级命令执行失败"""
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"), \
             patch.object(installer, 'run_command', return_value=(1, "", "upgrade failed")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "失败" in report.message
    
    def test_upgrade_verification_fails(self, installer):
        """测试升级后验证失败"""
        with patch.object(installer, 'verify', side_effect=[True, False]), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"), \
             patch.object(installer, 'run_command', return_value=(0, "upgraded", "")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "验证失败" in report.message
    
    def test_upgrade_exception(self, installer):
        """测试升级过程中发生异常"""
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, '_get_installed_version', side_effect=Exception("test error")):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "bmad-method"
            assert "异常" in report.message
            assert "test error" in report.error


class TestBMadInstallerCommands:
    """测试 BMad Method 安装器使用正确的命令"""
    
    def test_install_uses_bunx_command(self, platform_info):
        """测试安装时使用正确的 bunx 命令"""
        config = ToolConfig(enabled=True, install_via="bunx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/bun"), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"):
            
            # Mock run_command to capture the command
            commands_run = []
            def capture_command(cmd, **kwargs):
                commands_run.append(cmd)
                return (0, "installed", "")
            
            with patch.object(installer, 'run_command', side_effect=capture_command):
                report = installer.install()
            
            # Verify the command is correct
            assert len(commands_run) == 1
            assert "bunx bmad-method init" in commands_run[0]
    
    def test_install_uses_npx_command(self, platform_info):
        """测试安装时使用正确的 npx 命令"""
        config = ToolConfig(enabled=True, install_via="npx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"):
            
            # Mock run_command to capture the command
            commands_run = []
            def capture_command(cmd, **kwargs):
                commands_run.append(cmd)
                return (0, "installed", "")
            
            with patch.object(installer, 'run_command', side_effect=capture_command):
                report = installer.install()
            
            # Verify the command is correct
            assert len(commands_run) == 1
            assert "npx bmad-method init" in commands_run[0]
    
    def test_upgrade_uses_bunx_latest_command(self, platform_info):
        """测试升级时使用正确的 bunx @latest 命令"""
        config = ToolConfig(enabled=True, install_via="bunx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/bun"), \
             patch.object(installer, '_get_installed_version', side_effect=["1.0.0", "1.2.3"]):
            
            # Mock run_command to capture the command
            commands_run = []
            def capture_command(cmd, **kwargs):
                commands_run.append(cmd)
                return (0, "upgraded", "")
            
            with patch.object(installer, 'run_command', side_effect=capture_command):
                report = installer.upgrade()
            
            # Verify the command includes @latest
            assert len(commands_run) == 1
            assert "bunx bmad-method@latest init" in commands_run[0]
    
    def test_upgrade_uses_npx_latest_command(self, platform_info):
        """测试升级时使用正确的 npx @latest 命令"""
        config = ToolConfig(enabled=True, install_via="npx")
        installer = BMadInstaller(platform_info, config)
        
        with patch.object(installer, 'verify', return_value=True), \
             patch('shutil.which', return_value="/usr/local/bin/npx"), \
             patch.object(installer, '_get_installed_version', side_effect=["1.0.0", "1.2.3"]):
            
            # Mock run_command to capture the command
            commands_run = []
            def capture_command(cmd, **kwargs):
                commands_run.append(cmd)
                return (0, "upgraded", "")
            
            with patch.object(installer, 'run_command', side_effect=capture_command):
                report = installer.upgrade()
            
            # Verify the command includes @latest
            assert len(commands_run) == 1
            assert "npx bmad-method@latest init" in commands_run[0]
