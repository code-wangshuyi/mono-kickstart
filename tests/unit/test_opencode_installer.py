import pytest
from unittest.mock import patch

from mono_kickstart.config import ToolConfig
from mono_kickstart.installer_base import InstallResult
from mono_kickstart.installers.opencode_installer import OpenCodeInstaller
from mono_kickstart.platform_detector import Arch, OS, PlatformInfo, Shell


@pytest.fixture
def platform_info():
    return PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file="/home/test/.bashrc",
    )


def test_determine_install_method_bun(platform_info):
    with patch("shutil.which", return_value="/usr/local/bin/bun"):
        installer = OpenCodeInstaller(platform_info, ToolConfig(enabled=True))
    assert installer.install_method == "bun"


def test_determine_install_method_npm(platform_info):
    with patch("shutil.which", return_value=None):
        installer = OpenCodeInstaller(platform_info, ToolConfig(enabled=True))
    assert installer.install_method == "npm"


def test_verify_success(platform_info):
    with patch("shutil.which", return_value="/usr/local/bin/opencode"):
        installer = OpenCodeInstaller(platform_info, ToolConfig(enabled=True))
    with (
        patch("shutil.which", return_value="/usr/local/bin/opencode"),
        patch.object(installer, "run_command", return_value=(0, "1.1.0", "")),
    ):
        assert installer.verify() is True


def test_install_npm_success(platform_info):
    installer = OpenCodeInstaller(platform_info, ToolConfig(enabled=True, install_via="npm"))

    with (
        patch(
            "shutil.which", side_effect=lambda cmd: "/usr/local/bin/npm" if cmd == "npm" else None
        ),
        patch.object(installer, "verify", side_effect=[False, True]),
        patch.object(installer, "run_command", return_value=(0, "ok", "")),
        patch.object(installer, "_get_installed_version", return_value="1.1.0"),
    ):
        report = installer.install()

    assert report.result == InstallResult.SUCCESS
    assert report.tool_name == "opencode"


def test_install_npm_missing(platform_info):
    installer = OpenCodeInstaller(platform_info, ToolConfig(enabled=True, install_via="npm"))
    with (
        patch("shutil.which", return_value=None),
        patch.object(installer, "verify", return_value=False),
    ):
        report = installer.install()
    assert report.result == InstallResult.FAILED


def test_upgrade_not_installed(platform_info):
    installer = OpenCodeInstaller(platform_info, ToolConfig(enabled=True))
    with patch.object(installer, "verify", return_value=False):
        report = installer.upgrade()
    assert report.result == InstallResult.FAILED


def test_upgrade_bun_uses_add_latest(platform_info):
    installer = OpenCodeInstaller(platform_info, ToolConfig(enabled=True, install_via="bun"))

    with (
        patch(
            "shutil.which", side_effect=lambda cmd: "/usr/local/bin/bun" if cmd == "bun" else None
        ),
        patch.object(installer, "verify", side_effect=[True, True]),
        patch.object(installer, "_get_installed_version", side_effect=["1.0.0", "1.1.0"]),
        patch.object(installer, "run_command", return_value=(0, "ok", "")) as mock_run,
    ):
        report = installer.upgrade()

    assert report.result == InstallResult.SUCCESS
    mock_run.assert_called_once_with(
        "bun add -g opencode-ai@latest",
        shell=True,
        timeout=300,
        max_retries=2,
    )
