"""Conda 安装器单元测试

测试 Conda 安装器的各种场景，包括安装、升级、验证、平台特定逻辑等。
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from mono_kickstart.config import ToolConfig
from mono_kickstart.installer_base import InstallResult
from mono_kickstart.installers.conda_installer import CondaInstaller
from mono_kickstart.platform_detector import Arch, OS, PlatformInfo, Shell


@pytest.fixture
def platform_info_macos_arm64():
    """创建 macOS ARM64 平台信息"""
    return PlatformInfo(
        os=OS.MACOS,
        arch=Arch.ARM64,
        shell=Shell.ZSH,
        shell_config_file=str(Path.home() / ".zshrc")
    )


@pytest.fixture
def platform_info_macos_x86():
    """创建 macOS x86_64 平台信息"""
    return PlatformInfo(
        os=OS.MACOS,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(Path.home() / ".bashrc")
    )


@pytest.fixture
def platform_info_linux_x86():
    """创建 Linux x86_64 平台信息"""
    return PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file=str(Path.home() / ".bashrc")
    )


@pytest.fixture
def platform_info_unsupported():
    """创建不支持的平台信息"""
    return PlatformInfo(
        os=OS.LINUX,
        arch=Arch.ARM64,  # Linux ARM64 不支持
        shell=Shell.BASH,
        shell_config_file=str(Path.home() / ".bashrc")
    )


@pytest.fixture
def tool_config():
    """创建测试用的工具配置"""
    return ToolConfig(enabled=True)


class TestCondaInstaller:
    """Conda 安装器测试类"""
    
    def test_init(self, platform_info_macos_arm64, tool_config):
        """测试初始化"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        assert installer.platform_info == platform_info_macos_arm64
        assert installer.config == tool_config
        assert installer.install_dir == Path.home() / "miniconda3"
    
    def test_get_install_url_macos_arm64(self, platform_info_macos_arm64, tool_config):
        """测试 macOS ARM64 平台的安装包 URL"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        url = installer.get_install_url()
        
        assert "Miniconda3-latest-MacOSX-arm64.sh" in url
        assert url.startswith("https://mirrors.sustech.edu.cn/anaconda/miniconda")
    
    def test_get_install_url_macos_x86(self, platform_info_macos_x86, tool_config):
        """测试 macOS x86_64 平台的安装包 URL"""
        installer = CondaInstaller(platform_info_macos_x86, tool_config)
        url = installer.get_install_url()
        
        assert "Miniconda3-latest-MacOSX-x86_64.sh" in url
        assert url.startswith("https://mirrors.sustech.edu.cn/anaconda/miniconda")
    
    def test_get_install_url_linux_x86(self, platform_info_linux_x86, tool_config):
        """测试 Linux x86_64 平台的安装包 URL"""
        installer = CondaInstaller(platform_info_linux_x86, tool_config)
        url = installer.get_install_url()
        
        assert "Miniconda3-latest-Linux-x86_64.sh" in url
        assert url.startswith("https://mirrors.sustech.edu.cn/anaconda/miniconda")
    
    def test_get_install_url_unsupported_platform(self, platform_info_unsupported, tool_config):
        """测试不支持的平台抛出异常"""
        installer = CondaInstaller(platform_info_unsupported, tool_config)
        
        with pytest.raises(ValueError) as exc_info:
            installer.get_install_url()
        
        assert "不支持的平台" in str(exc_info.value)
    
    def test_verify_not_installed_dir_not_exists(self, platform_info_macos_arm64, tool_config):
        """测试验证 Conda 未安装（目录不存在）"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch('pathlib.Path.exists', return_value=False):
            assert installer.verify() is False
    
    def test_verify_not_installed_conda_bin_not_exists(self, platform_info_macos_arm64, tool_config):
        """测试验证 Conda 未安装（conda 可执行文件不存在）"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        # 模拟安装目录存在但 conda 可执行文件不存在
        def mock_exists(self):
            if "miniconda3" in str(self) and "bin/conda" not in str(self):
                return True
            return False
        
        with patch('pathlib.Path.exists', mock_exists):
            assert installer.verify() is False
    
    def test_verify_installed_success(self, platform_info_macos_arm64, tool_config):
        """测试验证 Conda 已安装且可用"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, "conda 23.1.0", "")
            ):
                assert installer.verify() is True
    
    def test_verify_installed_but_not_working(self, platform_info_macos_arm64, tool_config):
        """测试验证 Conda 已安装但无法执行"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                installer,
                'run_command',
                return_value=(1, "", "command not found")
            ):
                assert installer.verify() is False
    
    def test_get_installed_version_success(self, platform_info_macos_arm64, tool_config):
        """测试获取已安装版本成功"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, "conda 23.1.0\n", "")
            ):
                version = installer._get_installed_version()
                assert version == "23.1.0"
    
    def test_get_installed_version_not_installed(self, platform_info_macos_arm64, tool_config):
        """测试获取版本时 Conda 未安装"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch('pathlib.Path.exists', return_value=False):
            version = installer._get_installed_version()
            assert version is None
    
    def test_get_installed_version_command_failed(self, platform_info_macos_arm64, tool_config):
        """测试获取版本时命令执行失败"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                installer,
                'run_command',
                return_value=(1, "", "error")
            ):
                version = installer._get_installed_version()
                assert version is None
    
    def test_get_installed_version_unexpected_format(self, platform_info_macos_arm64, tool_config):
        """测试获取版本时输出格式不符合预期"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, "singleword", "")
            ):
                version = installer._get_installed_version()
                # 当输出只有一个单词时，无法提取版本号
                assert version is None
    
    def test_install_already_installed(self, platform_info_macos_arm64, tool_config):
        """测试安装时 Conda 已安装"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=True):
            with patch.object(
                installer,
                '_get_installed_version',
                return_value="23.1.0"
            ):
                report = installer.install()
                
                assert report.result == InstallResult.SKIPPED
                assert report.tool_name == "conda"
                assert report.version == "23.1.0"
                assert "已安装" in report.message
    
    def test_install_unsupported_platform(self, platform_info_unsupported, tool_config):
        """测试在不支持的平台上安装"""
        installer = CondaInstaller(platform_info_unsupported, tool_config)
        
        with patch.object(installer, 'verify', return_value=False):
            report = installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "conda"
            assert "不支持的平台" in report.message
            assert report.error is not None
    
    def test_install_download_failed(self, platform_info_macos_arm64, tool_config):
        """测试安装时下载脚本失败"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=False):
            with patch.object(installer, '_download_installer', return_value=False):
                report = installer.install()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "conda"
                assert "下载" in report.message
                assert report.error is not None
    
    def test_install_script_execution_failed(self, platform_info_macos_arm64, tool_config):
        """测试安装时脚本执行失败"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=False):
            with patch.object(installer, '_download_installer', return_value=True):
                with patch.object(
                    installer,
                    'run_command',
                    return_value=(1, "", "installation error")
                ):
                    with patch('pathlib.Path.unlink'):
                        report = installer.install()
                        
                        assert report.result == InstallResult.FAILED
                        assert report.tool_name == "conda"
                        assert "执行" in report.message or "脚本" in report.message
                        assert report.error is not None
    
    def test_install_verification_failed(self, platform_info_macos_arm64, tool_config):
        """测试安装后验证失败"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        verify_calls = [False, False]  # 第一次检查是否已安装，第二次验证安装结果
        
        with patch.object(
            installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(installer, '_download_installer', return_value=True):
                with patch.object(
                    installer,
                    'run_command',
                    return_value=(0, "installed", "")
                ):
                    with patch('pathlib.Path.unlink'):
                        report = installer.install()
                        
                        assert report.result == InstallResult.FAILED
                        assert report.tool_name == "conda"
                        assert "验证" in report.message
    
    def test_install_success(self, platform_info_macos_arm64, tool_config):
        """测试成功安装 Conda"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        verify_calls = [False, True]  # 第一次未安装，第二次验证成功
        
        with patch.object(
            installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(installer, '_download_installer', return_value=True):
                with patch.object(
                    installer,
                    'run_command',
                    return_value=(0, "installed", "")
                ):
                    with patch.object(
                        installer,
                        '_get_installed_version',
                        return_value="23.1.0"
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = installer.install()
                            
                            assert report.result == InstallResult.SUCCESS
                            assert report.tool_name == "conda"
                            assert report.version == "23.1.0"
                            assert "成功" in report.message
    
    def test_install_uses_correct_command_flags(self, platform_info_macos_arm64, tool_config):
        """测试安装时使用正确的命令参数"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        verify_calls = [False, True]
        
        with patch.object(installer, 'verify', side_effect=verify_calls):
            with patch.object(installer, '_download_installer', return_value=True):
                with patch.object(installer, 'run_command') as mock_run:
                    mock_run.return_value = (0, "installed", "")
                    
                    with patch.object(
                        installer,
                        '_get_installed_version',
                        return_value="23.1.0"
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = installer.install()
                            
                            # 验证调用了 run_command 且包含正确的参数
                            assert mock_run.called
                            call_args = mock_run.call_args[0][0]
                            assert "-b" in call_args  # 批量模式
                            assert "-f" in call_args  # 强制安装
                            assert report.result == InstallResult.SUCCESS

    def test_install_exception_handling(self, platform_info_macos_arm64, tool_config):
        """测试安装过程中异常处理"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=False):
            with patch.object(
                installer,
                '_download_installer',
                side_effect=Exception("Unexpected error")
            ):
                report = installer.install()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "conda"
                assert "异常" in report.message
                assert "Unexpected error" in report.error
    
    def test_install_cleans_up_temp_file_on_success(self, platform_info_macos_arm64, tool_config):
        """测试安装成功后清理临时文件"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        verify_calls = [False, True]
        
        with patch.object(installer, 'verify', side_effect=verify_calls):
            with patch.object(installer, '_download_installer', return_value=True):
                with patch.object(
                    installer,
                    'run_command',
                    return_value=(0, "installed", "")
                ):
                    with patch.object(
                        installer,
                        '_get_installed_version',
                        return_value="23.1.0"
                    ):
                        with patch('pathlib.Path.unlink') as mock_unlink:
                            report = installer.install()
                            
                            # 验证临时文件被删除
                            assert mock_unlink.called
                            assert report.result == InstallResult.SUCCESS
    
    def test_install_cleans_up_temp_file_on_failure(self, platform_info_macos_arm64, tool_config):
        """测试安装失败后清理临时文件"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=False):
            with patch.object(installer, '_download_installer', return_value=True):
                with patch.object(
                    installer,
                    'run_command',
                    return_value=(1, "", "error")
                ):
                    with patch('pathlib.Path.unlink') as mock_unlink:
                        report = installer.install()
                        
                        # 验证临时文件被删除
                        assert mock_unlink.called
                        assert report.result == InstallResult.FAILED
    
    def test_upgrade_not_installed(self, platform_info_macos_arm64, tool_config):
        """测试升级时 Conda 未安装"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=False):
            report = installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "conda"
            assert "未安装" in report.message
    
    def test_upgrade_unsupported_platform(self, platform_info_unsupported, tool_config):
        """测试在不支持的平台上升级"""
        installer = CondaInstaller(platform_info_unsupported, tool_config)
        
        with patch.object(installer, 'verify', return_value=True):
            with patch.object(
                installer,
                '_get_installed_version',
                return_value="22.0.0"
            ):
                report = installer.upgrade()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "conda"
                assert "不支持的平台" in report.message
    
    def test_upgrade_download_failed(self, platform_info_macos_arm64, tool_config):
        """测试升级时下载脚本失败"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=True):
            with patch.object(
                installer,
                '_get_installed_version',
                return_value="22.0.0"
            ):
                with patch.object(installer, '_download_installer', return_value=False):
                    report = installer.upgrade()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "conda"
                    assert "下载" in report.message
    
    def test_upgrade_script_execution_failed(self, platform_info_macos_arm64, tool_config):
        """测试升级时脚本执行失败"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=True):
            with patch.object(
                installer,
                '_get_installed_version',
                return_value="22.0.0"
            ):
                with patch.object(installer, '_download_installer', return_value=True):
                    with patch.object(
                        installer,
                        'run_command',
                        return_value=(1, "", "upgrade error")
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = installer.upgrade()
                            
                            assert report.result == InstallResult.FAILED
                            assert report.tool_name == "conda"
                            assert "升级" in report.message or "脚本" in report.message
    
    def test_upgrade_verification_failed(self, platform_info_macos_arm64, tool_config):
        """测试升级后验证失败"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        verify_calls = [True, False]  # 第一次已安装，第二次验证失败
        
        with patch.object(
            installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(
                installer,
                '_get_installed_version',
                return_value="22.0.0"
            ):
                with patch.object(installer, '_download_installer', return_value=True):
                    with patch.object(
                        installer,
                        'run_command',
                        return_value=(0, "upgraded", "")
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = installer.upgrade()
                            
                            assert report.result == InstallResult.FAILED
                            assert report.tool_name == "conda"
                            assert "验证" in report.message
    
    def test_upgrade_success(self, platform_info_macos_arm64, tool_config):
        """测试成功升级 Conda"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        verify_calls = [True, True]  # 第一次已安装，第二次验证成功
        version_calls = ["22.0.0", "23.1.0"]  # 升级前后的版本
        
        with patch.object(
            installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(
                installer,
                '_get_installed_version',
                side_effect=version_calls
            ):
                with patch.object(installer, '_download_installer', return_value=True):
                    with patch.object(
                        installer,
                        'run_command',
                        return_value=(0, "upgraded", "")
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = installer.upgrade()
                            
                            assert report.result == InstallResult.SUCCESS
                            assert report.tool_name == "conda"
                            assert report.version == "23.1.0"
                            assert "22.0.0" in report.message
                            assert "23.1.0" in report.message
                            assert "成功" in report.message
    
    def test_upgrade_uses_correct_command_flags(self, platform_info_macos_arm64, tool_config):
        """测试升级时使用正确的命令参数（包含 -u 参数）"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        verify_calls = [True, True]
        version_calls = ["22.0.0", "23.1.0"]
        
        with patch.object(installer, 'verify', side_effect=verify_calls):
            with patch.object(
                installer,
                '_get_installed_version',
                side_effect=version_calls
            ):
                with patch.object(installer, '_download_installer', return_value=True):
                    with patch.object(installer, 'run_command') as mock_run:
                        mock_run.return_value = (0, "upgraded", "")
                        
                        with patch('pathlib.Path.unlink'):
                            report = installer.upgrade()
                            
                            # 验证调用了 run_command 且包含正确的参数
                            assert mock_run.called
                            call_args = mock_run.call_args[0][0]
                            assert "-b" in call_args  # 批量模式
                            assert "-f" in call_args  # 强制安装
                            assert report.result == InstallResult.SUCCESS
    
    def test_upgrade_exception_handling(self, platform_info_macos_arm64, tool_config):
        """测试升级过程中异常处理"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=True):
            with patch.object(
                installer,
                '_get_installed_version',
                side_effect=Exception("Unexpected error")
            ):
                report = installer.upgrade()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "conda"
                assert "异常" in report.message
                assert "Unexpected error" in report.error
    
    def test_upgrade_cleans_up_temp_file_on_success(self, platform_info_macos_arm64, tool_config):
        """测试升级成功后清理临时文件"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        verify_calls = [True, True]
        version_calls = ["22.0.0", "23.1.0"]
        
        with patch.object(installer, 'verify', side_effect=verify_calls):
            with patch.object(
                installer,
                '_get_installed_version',
                side_effect=version_calls
            ):
                with patch.object(installer, '_download_installer', return_value=True):
                    with patch.object(
                        installer,
                        'run_command',
                        return_value=(0, "upgraded", "")
                    ):
                        with patch('pathlib.Path.unlink') as mock_unlink:
                            report = installer.upgrade()
                            
                            # 验证临时文件被删除
                            assert mock_unlink.called
                            assert report.result == InstallResult.SUCCESS
    
    def test_upgrade_cleans_up_temp_file_on_failure(self, platform_info_macos_arm64, tool_config):
        """测试升级失败后清理临时文件"""
        installer = CondaInstaller(platform_info_macos_arm64, tool_config)
        
        with patch.object(installer, 'verify', return_value=True):
            with patch.object(
                installer,
                '_get_installed_version',
                return_value="22.0.0"
            ):
                with patch.object(installer, '_download_installer', return_value=True):
                    with patch.object(
                        installer,
                        'run_command',
                        return_value=(1, "", "error")
                    ):
                        with patch('pathlib.Path.unlink') as mock_unlink:
                            report = installer.upgrade()
                            
                            # 验证临时文件被删除
                            assert mock_unlink.called
                            assert report.result == InstallResult.FAILED
