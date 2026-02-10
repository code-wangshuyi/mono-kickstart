"""单元测试：UIPro CLI 安装器

该模块测试 UIPro CLI 安装器的各种场景。
"""

from unittest.mock import patch

import pytest

from src.mono_kickstart.config import ToolConfig
from src.mono_kickstart.installer_base import InstallResult
from src.mono_kickstart.installers.uipro_installer import UiproInstaller
from src.mono_kickstart.platform_detector import OS, Arch, PlatformInfo, Shell


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
    """创建 UIPro CLI 安装器实例"""
    with patch('shutil.which', return_value=None):
        return UiproInstaller(platform_info, tool_config)


class TestUiproInstallerDetermineMethod:
    """测试 UIPro CLI 安装器的安装方式判定"""

    def test_default_to_npm_when_bun_not_available(self, platform_info):
        """测试 Bun 不可用时默认使用 npm"""
        config = ToolConfig(enabled=True)
        with patch('shutil.which', return_value=None):
            inst = UiproInstaller(platform_info, config)
            assert inst.install_method == 'npm'

    def test_prefer_bun_when_available(self, platform_info):
        """测试 Bun 可用时优先使用 Bun"""
        config = ToolConfig(enabled=True)
        with patch('shutil.which', return_value="/usr/local/bin/bun"):
            inst = UiproInstaller(platform_info, config)
            assert inst.install_method == 'bun'

    def test_use_config_install_via(self, platform_info):
        """测试配置指定安装方式"""
        config = ToolConfig(enabled=True, install_via="npm")
        with patch('shutil.which', return_value="/usr/local/bin/bun"):
            inst = UiproInstaller(platform_info, config)
            assert inst.install_method == 'npm'


class TestUiproInstallerVerify:
    """测试 UIPro CLI 安装器的验证功能"""

    def test_verify_when_uipro_installed(self, installer):
        """测试 UIPro CLI 已安装时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/uipro"), \
             patch.object(installer, 'run_command', return_value=(0, "1.0.0", "")):
            assert installer.verify() is True

    def test_verify_when_uipro_not_in_path(self, installer):
        """测试 UIPro CLI 不在 PATH 中时的验证"""
        with patch('shutil.which', return_value=None):
            assert installer.verify() is False

    def test_verify_when_uipro_command_fails(self, installer):
        """测试 UIPro CLI 命令执行失败时的验证"""
        with patch('shutil.which', return_value="/usr/local/bin/uipro"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            assert installer.verify() is False


class TestUiproInstallerGetVersion:
    """测试 UIPro CLI 安装器的版本获取功能"""

    def test_get_version_success(self, installer):
        """测试成功获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/uipro"), \
             patch.object(installer, 'run_command', return_value=(0, "1.2.3\nother info", "")):
            version = installer._get_installed_version()
            assert version == "1.2.3"

    def test_get_version_single_line(self, installer):
        """测试单行版本输出"""
        with patch('shutil.which', return_value="/usr/local/bin/uipro"), \
             patch.object(installer, 'run_command', return_value=(0, "2.0.0", "")):
            version = installer._get_installed_version()
            assert version == "2.0.0"

    def test_get_version_when_not_installed(self, installer):
        """测试 UIPro CLI 未安装时获取版本"""
        with patch('shutil.which', return_value=None):
            version = installer._get_installed_version()
            assert version is None

    def test_get_version_when_command_fails(self, installer):
        """测试命令失败时获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/uipro"), \
             patch.object(installer, 'run_command', return_value=(1, "", "error")):
            version = installer._get_installed_version()
            assert version is None

    def test_get_version_when_empty_output(self, installer):
        """测试空输出时获取版本"""
        with patch('shutil.which', return_value="/usr/local/bin/uipro"), \
             patch.object(installer, 'run_command', return_value=(0, "", "")):
            version = installer._get_installed_version()
            assert version is None


class TestUiproInstallerInstall:
    """测试 UIPro CLI 安装器的安装功能"""

    def test_install_when_already_installed(self, installer):
        """测试 UIPro CLI 已安装时跳过安装"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"):
            report = installer.install()

            assert report.result == InstallResult.SKIPPED
            assert report.tool_name == "uipro"
            assert report.version == "1.0.0"
            assert "已安装" in report.message

    def test_install_via_npm_when_npm_not_available(self, installer):
        """测试 npm 未安装时无法安装"""
        installer.install_method = 'npm'
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value=None):
            report = installer.install()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uipro"
            assert "npm 未安装" in report.message

    def test_install_via_bun_when_bun_not_available(self, installer):
        """测试 Bun 未安装时无法使用 Bun 安装"""
        installer.install_method = 'bun'
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value=None):
            report = installer.install()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uipro"
            assert "Bun 未安装" in report.message

    def test_install_success_via_npm(self, installer):
        """测试通过 npm 成功安装"""
        installer.install_method = 'npm'
        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/npm"), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")), \
             patch.object(installer, '_get_installed_version', return_value="1.2.3"):
            report = installer.install()

            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "uipro"
            assert report.version == "1.2.3"
            assert "成功" in report.message

    def test_install_success_via_bun(self, installer):
        """测试通过 Bun 成功安装"""
        installer.install_method = 'bun'
        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/bun"), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")), \
             patch.object(installer, '_get_installed_version', return_value="1.2.3"):
            report = installer.install()

            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "uipro"
            assert report.version == "1.2.3"

    def test_install_command_fails(self, installer):
        """测试安装命令执行失败"""
        installer.install_method = 'npm'
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value="/usr/local/bin/npm"), \
             patch.object(installer, 'run_command', return_value=(1, "", "install failed")):
            report = installer.install()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uipro"
            assert "失败" in report.message
            assert report.error is not None

    def test_install_verification_fails(self, installer):
        """测试安装后验证失败"""
        installer.install_method = 'npm'
        with patch.object(installer, 'verify', side_effect=[False, False]), \
             patch('shutil.which', return_value="/usr/local/bin/npm"), \
             patch.object(installer, 'run_command', return_value=(0, "installed", "")):
            report = installer.install()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uipro"
            assert "验证失败" in report.message

    def test_install_exception(self, installer):
        """测试安装过程中发生异常"""
        installer.install_method = 'npm'
        with patch.object(installer, 'verify', return_value=False), \
             patch('shutil.which', return_value="/usr/local/bin/npm"), \
             patch.object(installer, 'run_command', side_effect=Exception("test error")):
            report = installer.install()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uipro"
            assert "异常" in report.message
            assert "test error" in report.error

    def test_install_uses_correct_npm_command(self, installer):
        """测试安装使用正确的 npm 命令"""
        installer.install_method = 'npm'
        commands_run = []

        def capture_command(cmd, **kwargs):
            commands_run.append(cmd)
            return (0, "installed", "")

        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/npm"), \
             patch.object(installer, 'run_command', side_effect=capture_command), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"):
            installer.install()

        assert len(commands_run) == 1
        assert "npm install -g uipro-cli" in commands_run[0]

    def test_install_uses_correct_bun_command(self, installer):
        """测试安装使用正确的 Bun 命令"""
        installer.install_method = 'bun'
        commands_run = []

        def capture_command(cmd, **kwargs):
            commands_run.append(cmd)
            return (0, "installed", "")

        with patch.object(installer, 'verify', side_effect=[False, True]), \
             patch('shutil.which', return_value="/usr/local/bin/bun"), \
             patch.object(installer, 'run_command', side_effect=capture_command), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"):
            installer.install()

        assert len(commands_run) == 1
        assert "bun install -g uipro-cli" in commands_run[0]


class TestUiproInstallerUpgrade:
    """测试 UIPro CLI 安装器的升级功能"""

    def test_upgrade_when_not_installed(self, installer):
        """测试 UIPro CLI 未安装时无法升级"""
        with patch.object(installer, 'verify', return_value=False):
            report = installer.upgrade()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uipro"
            assert "未安装" in report.message

    def test_upgrade_success(self, installer):
        """测试成功升级 UIPro CLI"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', side_effect=["1.0.0", "1.2.3"]), \
             patch.object(installer, 'run_command', return_value=(0, "updated", "")):
            report = installer.upgrade()

            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "uipro"
            assert report.version == "1.2.3"
            assert "1.0.0" in report.message
            assert "1.2.3" in report.message

    def test_upgrade_uses_uipro_update_command(self, installer):
        """测试升级使用 uipro update 自更新命令"""
        commands_run = []

        def capture_command(cmd, **kwargs):
            commands_run.append(cmd)
            return (0, "updated", "")

        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', side_effect=["1.0.0", "1.2.3"]), \
             patch.object(installer, 'run_command', side_effect=capture_command):
            installer.upgrade()

        assert len(commands_run) == 1
        assert commands_run[0] == "uipro update"

    def test_upgrade_command_fails(self, installer):
        """测试升级命令执行失败"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"), \
             patch.object(installer, 'run_command', return_value=(1, "", "upgrade failed")):
            report = installer.upgrade()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uipro"
            assert "失败" in report.message

    def test_upgrade_verification_fails(self, installer):
        """测试升级后验证失败"""
        with patch.object(installer, 'verify', side_effect=[True, False]), \
             patch.object(installer, '_get_installed_version', return_value="1.0.0"), \
             patch.object(installer, 'run_command', return_value=(0, "updated", "")):
            report = installer.upgrade()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uipro"
            assert "验证失败" in report.message

    def test_upgrade_exception(self, installer):
        """测试升级过程中发生异常"""
        with patch.object(installer, 'verify', return_value=True), \
             patch.object(installer, '_get_installed_version', side_effect=Exception("test error")):
            report = installer.upgrade()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "uipro"
            assert "异常" in report.message
            assert "test error" in report.error
