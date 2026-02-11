"""单元测试：GitHub CLI 安装器

该模块测试 GitHub CLI 安装器的各种场景。
"""

from unittest.mock import patch

import pytest

from src.mono_kickstart.config import ToolConfig
from src.mono_kickstart.installer_base import InstallResult
from src.mono_kickstart.installers.gh_installer import GHInstaller
from src.mono_kickstart.platform_detector import OS, Arch, PlatformInfo, Shell


@pytest.fixture
def platform_info():
    """创建测试用的平台信息（macOS）"""
    return PlatformInfo(
        os=OS.MACOS, arch=Arch.ARM64, shell=Shell.ZSH, shell_config_file="/Users/test/.zshrc"
    )


@pytest.fixture
def linux_platform_info():
    """创建测试用的平台信息（Linux）"""
    return PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file="/home/test/.bashrc"
    )


@pytest.fixture
def tool_config():
    """创建测试用的工具配置"""
    return ToolConfig(enabled=True)


@pytest.fixture
def installer(platform_info, tool_config):
    """创建 GitHub CLI 安装器实例（macOS）"""
    return GHInstaller(platform_info, tool_config)


@pytest.fixture
def linux_installer(linux_platform_info, tool_config):
    """创建 GitHub CLI 安装器实例（Linux）"""
    return GHInstaller(linux_platform_info, tool_config)


class TestGHInstallerVerify:
    """测试 GitHub CLI 安装器的验证功能"""

    def test_verify_when_gh_installed(self, installer):
        """测试 gh 已安装时的验证"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/gh"),
            patch.object(
                installer, "run_command", return_value=(0, "gh version 2.86.0 (2025-01-15)", "")
            ),
        ):
            assert installer.verify() is True

    def test_verify_when_gh_not_in_path(self, installer):
        """测试 gh 不在 PATH 中时的验证"""
        with patch("shutil.which", return_value=None):
            assert installer.verify() is False

    def test_verify_when_gh_command_fails(self, installer):
        """测试 gh 命令执行失败时的验证"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/gh"),
            patch.object(installer, "run_command", return_value=(1, "", "error")),
        ):
            assert installer.verify() is False


class TestGHInstallerGetVersion:
    """测试 GitHub CLI 安装器的版本获取功能"""

    def test_get_version_success(self, installer):
        """测试成功获取版本"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/gh"),
            patch.object(
                installer, "run_command", return_value=(0, "gh version 2.86.0 (2025-01-15)", "")
            ),
        ):
            version = installer._get_installed_version()
            assert version == "2.86.0"

    def test_get_version_when_not_installed(self, installer):
        """测试 gh 未安装时获取版本"""
        with patch("shutil.which", return_value=None):
            version = installer._get_installed_version()
            assert version is None

    def test_get_version_when_command_fails(self, installer):
        """测试命令失败时获取版本"""
        with (
            patch("shutil.which", return_value="/usr/local/bin/gh"),
            patch.object(installer, "run_command", return_value=(1, "", "error")),
        ):
            version = installer._get_installed_version()
            assert version is None


class TestGHInstallerInstall:
    """测试 GitHub CLI 安装器的安装功能"""

    def test_install_when_already_installed(self, installer):
        """测试 gh 已安装时跳过安装"""
        with (
            patch.object(installer, "verify", return_value=True),
            patch.object(installer, "_get_installed_version", return_value="2.86.0"),
        ):
            report = installer.install()

            assert report.result == InstallResult.SKIPPED
            assert report.tool_name == "gh"
            assert report.version == "2.86.0"
            assert "已安装" in report.message

    def test_install_success_macos_brew(self, installer):
        """测试 macOS 上通过 Homebrew 成功安装"""
        with (
            patch.object(installer, "verify", side_effect=[False, True]),
            patch.object(installer, "_check_brew_available", return_value=True),
            patch.object(installer, "_install_via_brew", return_value=(True, "")),
            patch.object(installer, "_get_installed_version", return_value="2.86.0"),
        ):
            report = installer.install()

            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "gh"
            assert report.version == "2.86.0"
            assert "成功" in report.message

    def test_install_macos_no_brew(self, installer):
        """测试 macOS 上 Homebrew 不可用时安装失败"""
        with (
            patch.object(installer, "verify", return_value=False),
            patch.object(installer, "_check_brew_available", return_value=False),
        ):
            report = installer.install()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "gh"
            assert "Homebrew" in report.message

    def test_install_brew_fails(self, installer):
        """测试 Homebrew 安装命令失败"""
        with (
            patch.object(installer, "verify", return_value=False),
            patch.object(installer, "_check_brew_available", return_value=True),
            patch.object(
                installer, "_install_via_brew", return_value=(False, "brew install failed")
            ),
        ):
            report = installer.install()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "gh"
            assert "失败" in report.message

    def test_install_verification_fails(self, installer):
        """测试安装后验证失败"""
        with (
            patch.object(installer, "verify", side_effect=[False, False]),
            patch.object(installer, "_check_brew_available", return_value=True),
            patch.object(installer, "_install_via_brew", return_value=(True, "")),
        ):
            report = installer.install()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "gh"
            assert "验证失败" in report.message

    def test_install_exception(self, installer):
        """测试安装过程中发生异常"""
        with (
            patch.object(installer, "verify", return_value=False),
            patch.object(installer, "_check_brew_available", side_effect=Exception("test error")),
        ):
            report = installer.install()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "gh"
            assert "异常" in report.message
            assert "test error" in report.error

    def test_install_unsupported_os(self, tool_config):
        """测试不支持的操作系统"""
        unsupported_platform = PlatformInfo(
            os=OS.UNSUPPORTED,
            arch=Arch.X86_64,
            shell=Shell.BASH,
            shell_config_file="/home/test/.bashrc",
        )
        inst = GHInstaller(unsupported_platform, tool_config)
        report = inst.install()

        assert report.result == InstallResult.FAILED
        assert "不支持" in report.message

    def test_install_linux_with_brew(self, linux_installer):
        """测试 Linux 上使用 Homebrew 安装"""
        with (
            patch.object(linux_installer, "verify", side_effect=[False, True]),
            patch.object(linux_installer, "_check_brew_available", return_value=True),
            patch.object(linux_installer, "_install_via_brew", return_value=(True, "")),
            patch.object(linux_installer, "_get_installed_version", return_value="2.86.0"),
        ):
            report = linux_installer.install()

            assert report.result == InstallResult.SUCCESS
            assert report.version == "2.86.0"

    def test_install_linux_with_apt(self, linux_installer):
        """测试 Linux 上使用 apt 安装"""
        with (
            patch.object(linux_installer, "verify", side_effect=[False, True]),
            patch.object(linux_installer, "_check_brew_available", return_value=False),
            patch.object(linux_installer, "_detect_linux_package_manager", return_value="apt-get"),
            patch.object(linux_installer, "_install_via_apt", return_value=(True, "")),
            patch.object(linux_installer, "_get_installed_version", return_value="2.86.0"),
        ):
            report = linux_installer.install()

            assert report.result == InstallResult.SUCCESS
            assert report.version == "2.86.0"

    def test_install_linux_with_dnf(self, linux_installer):
        """测试 Linux 上使用 dnf 安装"""
        with (
            patch.object(linux_installer, "verify", side_effect=[False, True]),
            patch.object(linux_installer, "_check_brew_available", return_value=False),
            patch.object(linux_installer, "_detect_linux_package_manager", return_value="dnf"),
            patch.object(linux_installer, "_install_via_dnf", return_value=(True, "")),
            patch.object(linux_installer, "_get_installed_version", return_value="2.86.0"),
        ):
            report = linux_installer.install()

            assert report.result == InstallResult.SUCCESS
            assert report.version == "2.86.0"

    def test_install_linux_no_package_manager(self, linux_installer):
        """测试 Linux 上没有支持的包管理器"""
        with (
            patch.object(linux_installer, "verify", return_value=False),
            patch.object(linux_installer, "_check_brew_available", return_value=False),
            patch.object(linux_installer, "_detect_linux_package_manager", return_value=None),
        ):
            report = linux_installer.install()

            assert report.result == InstallResult.FAILED
            assert "包管理器" in report.message


class TestGHInstallerUpgrade:
    """测试 GitHub CLI 安装器的升级功能"""

    def test_upgrade_when_not_installed(self, installer):
        """测试 gh 未安装时无法升级"""
        with patch.object(installer, "verify", return_value=False):
            report = installer.upgrade()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "gh"
            assert "未安装" in report.message

    def test_upgrade_success_via_brew(self, installer):
        """测试通过 Homebrew 成功升级"""
        with (
            patch.object(installer, "verify", return_value=True),
            patch.object(installer, "_get_installed_version", side_effect=["2.85.0", "2.86.0"]),
            patch.object(installer, "_check_brew_available", return_value=True),
            patch.object(installer, "run_command", return_value=(0, "upgraded", "")),
        ):
            report = installer.upgrade()

            assert report.result == InstallResult.SUCCESS
            assert report.tool_name == "gh"
            assert report.version == "2.86.0"
            assert "2.85.0" in report.message
            assert "2.86.0" in report.message

    def test_upgrade_command_fails(self, installer):
        """测试升级命令执行失败"""
        with (
            patch.object(installer, "verify", return_value=True),
            patch.object(installer, "_get_installed_version", return_value="2.85.0"),
            patch.object(installer, "_check_brew_available", return_value=True),
            patch.object(installer, "run_command", return_value=(1, "", "upgrade failed")),
        ):
            report = installer.upgrade()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "gh"
            assert "失败" in report.message

    def test_upgrade_verification_fails(self, installer):
        """测试升级后验证失败"""
        with (
            patch.object(installer, "verify", side_effect=[True, False]),
            patch.object(installer, "_get_installed_version", return_value="2.85.0"),
            patch.object(installer, "_check_brew_available", return_value=True),
            patch.object(installer, "run_command", return_value=(0, "upgraded", "")),
        ):
            report = installer.upgrade()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "gh"
            assert "验证失败" in report.message

    def test_upgrade_exception(self, installer):
        """测试升级过程中发生异常"""
        with (
            patch.object(installer, "verify", return_value=True),
            patch.object(installer, "_get_installed_version", side_effect=Exception("test error")),
        ):
            report = installer.upgrade()

            assert report.result == InstallResult.FAILED
            assert report.tool_name == "gh"
            assert "异常" in report.message
            assert "test error" in report.error

    def test_upgrade_unsupported_os(self, tool_config):
        """测试不支持的操作系统升级"""
        unsupported_platform = PlatformInfo(
            os=OS.UNSUPPORTED,
            arch=Arch.X86_64,
            shell=Shell.BASH,
            shell_config_file="/home/test/.bashrc",
        )
        inst = GHInstaller(unsupported_platform, tool_config)
        report = inst.upgrade()

        assert report.result == InstallResult.FAILED
        assert "不支持" in report.message

    def test_upgrade_linux_no_package_manager(self, linux_installer):
        """测试 Linux 上没有支持的包管理器时升级失败"""
        with (
            patch.object(linux_installer, "verify", return_value=True),
            patch.object(linux_installer, "_get_installed_version", return_value="2.85.0"),
            patch.object(linux_installer, "_check_brew_available", return_value=False),
            patch.object(linux_installer, "_detect_linux_package_manager", return_value=None),
        ):
            report = linux_installer.upgrade()

            assert report.result == InstallResult.FAILED
            assert "包管理器" in report.message


class TestGHInstallerHelpers:
    """测试 GitHub CLI 安装器的辅助方法"""

    def test_check_brew_available_true(self, installer):
        """测试 Homebrew 可用"""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            assert installer._check_brew_available() is True

    def test_check_brew_available_false(self, installer):
        """测试 Homebrew 不可用"""
        with patch("shutil.which", return_value=None):
            assert installer._check_brew_available() is False

    def test_detect_linux_apt(self, linux_installer):
        """测试检测 apt-get"""
        with patch(
            "shutil.which", side_effect=lambda cmd: "/usr/bin/apt-get" if cmd == "apt-get" else None
        ):
            assert linux_installer._detect_linux_package_manager() == "apt-get"

    def test_detect_linux_dnf(self, linux_installer):
        """测试检测 dnf"""
        with patch(
            "shutil.which", side_effect=lambda cmd: "/usr/bin/dnf" if cmd == "dnf" else None
        ):
            assert linux_installer._detect_linux_package_manager() == "dnf"

    def test_detect_linux_no_manager(self, linux_installer):
        """测试没有可用的包管理器"""
        with patch("shutil.which", return_value=None):
            assert linux_installer._detect_linux_package_manager() is None
