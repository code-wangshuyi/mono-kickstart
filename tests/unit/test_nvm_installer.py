"""NVM 安装器单元测试

测试 NVM 安装器的各种场景，包括安装、升级、验证等。
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from mono_kickstart.config import ToolConfig
from mono_kickstart.installer_base import InstallReport, InstallResult
from mono_kickstart.installers.nvm_installer import NVMInstaller
from mono_kickstart.platform_detector import Arch, OS, PlatformInfo, Shell


@pytest.fixture
def platform_info():
    """创建测试用的平台信息"""
    return PlatformInfo(
        os=OS.MACOS,
        arch=Arch.ARM64,
        shell=Shell.ZSH,
        shell_config_file=str(Path.home() / ".zshrc")
    )


@pytest.fixture
def tool_config():
    """创建测试用的工具配置"""
    return ToolConfig(enabled=True, version="v0.40.4")


@pytest.fixture
def nvm_installer(platform_info, tool_config):
    """创建 NVM 安装器实例"""
    return NVMInstaller(platform_info, tool_config)


class TestNVMInstaller:
    """NVM 安装器测试类"""
    
    def test_init_with_default_version(self, platform_info):
        """测试使用默认版本初始化"""
        config = ToolConfig(enabled=True)
        installer = NVMInstaller(platform_info, config)
        
        assert installer.nvm_version == "v0.40.4"
        assert "v0.40.4" in installer.install_script_url
    
    def test_init_with_custom_version(self, platform_info):
        """测试使用自定义版本初始化"""
        config = ToolConfig(enabled=True, version="v0.39.0")
        installer = NVMInstaller(platform_info, config)
        
        assert installer.nvm_version == "v0.39.0"
        assert "v0.39.0" in installer.install_script_url
    
    def test_verify_nvm_not_installed(self, nvm_installer):
        """测试验证 NVM 未安装的情况"""
        with patch('pathlib.Path.exists', return_value=False):
            assert nvm_installer.verify() is False
    
    def test_verify_nvm_installed_success(self, nvm_installer):
        """测试验证 NVM 已安装且可用"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                nvm_installer,
                'run_command',
                return_value=(0, "0.40.4", "")
            ):
                assert nvm_installer.verify() is True
    
    def test_verify_nvm_installed_but_not_working(self, nvm_installer):
        """测试验证 NVM 已安装但无法执行"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                nvm_installer,
                'run_command',
                return_value=(1, "", "command not found")
            ):
                assert nvm_installer.verify() is False
    
    def test_get_installed_version_success(self, nvm_installer):
        """测试获取已安装版本成功"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                nvm_installer,
                'run_command',
                return_value=(0, "0.40.4\n", "")
            ):
                version = nvm_installer._get_installed_version()
                assert version == "0.40.4"
    
    def test_get_installed_version_not_installed(self, nvm_installer):
        """测试获取版本时 NVM 未安装"""
        with patch('pathlib.Path.exists', return_value=False):
            version = nvm_installer._get_installed_version()
            assert version is None
    
    def test_get_installed_version_command_failed(self, nvm_installer):
        """测试获取版本时命令执行失败"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                nvm_installer,
                'run_command',
                return_value=(1, "", "error")
            ):
                version = nvm_installer._get_installed_version()
                assert version is None
    
    def test_write_env_to_shell_config_new_file(self, nvm_installer, tmp_path):
        """测试写入环境变量到新的配置文件"""
        config_file = tmp_path / ".zshrc"
        nvm_installer.platform_info.shell_config_file = str(config_file)
        
        result = nvm_installer._write_env_to_shell_config()
        
        assert result is True
        assert config_file.exists()
        
        content = config_file.read_text()
        assert "NVM_DIR" in content
        assert "nvm.sh" in content
        assert "bash_completion" in content
    
    def test_write_env_to_shell_config_existing_file(self, nvm_installer, tmp_path):
        """测试写入环境变量到已存在的配置文件"""
        config_file = tmp_path / ".zshrc"
        config_file.write_text("# Existing config\nexport PATH=/usr/local/bin:$PATH\n")
        nvm_installer.platform_info.shell_config_file = str(config_file)
        
        result = nvm_installer._write_env_to_shell_config()
        
        assert result is True
        
        content = config_file.read_text()
        assert "# Existing config" in content
        assert "NVM_DIR" in content
        assert "nvm.sh" in content
    
    def test_write_env_to_shell_config_already_configured(self, nvm_installer, tmp_path):
        """测试配置已存在时不重复写入"""
        config_file = tmp_path / ".zshrc"
        existing_content = """# NVM configuration
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
"""
        config_file.write_text(existing_content)
        nvm_installer.platform_info.shell_config_file = str(config_file)
        
        result = nvm_installer._write_env_to_shell_config()
        
        assert result is True
        
        # 验证内容没有重复（原始内容有1个NVM_DIR）
        content = config_file.read_text()
        # 由于原始内容已经包含配置，不应该再添加
        assert content == existing_content
    
    def test_write_env_to_shell_config_permission_error(self, nvm_installer, tmp_path):
        """测试写入配置文件时权限错误"""
        config_file = tmp_path / ".zshrc"
        nvm_installer.platform_info.shell_config_file = str(config_file)
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = nvm_installer._write_env_to_shell_config()
            assert result is False
    
    def test_install_already_installed(self, nvm_installer):
        """测试安装时 NVM 已安装"""
        with patch.object(nvm_installer, 'verify', return_value=True):
            with patch.object(
                nvm_installer,
                '_get_installed_version',
                return_value="0.40.4"
            ):
                report = nvm_installer.install()
                
                assert report.result == InstallResult.SKIPPED
                assert report.tool_name == "nvm"
                assert report.version == "0.40.4"
                assert "已安装" in report.message
    
    def test_install_download_failed(self, nvm_installer):
        """测试安装时下载脚本失败"""
        with patch.object(nvm_installer, 'verify', return_value=False):
            with patch.object(nvm_installer, 'download_file', return_value=False):
                report = nvm_installer.install()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "nvm"
                assert "下载" in report.message
                assert report.error is not None
    
    def test_install_script_execution_failed(self, nvm_installer):
        """测试安装时脚本执行失败"""
        with patch.object(nvm_installer, 'verify', return_value=False):
            with patch.object(nvm_installer, 'download_file', return_value=True):
                with patch.object(
                    nvm_installer,
                    'run_command',
                    return_value=(1, "", "script error")
                ):
                    with patch('pathlib.Path.unlink'):
                        report = nvm_installer.install()
                        
                        assert report.result == InstallResult.FAILED
                        assert report.tool_name == "nvm"
                        assert "执行" in report.message or "脚本" in report.message
    
    def test_install_env_write_failed(self, nvm_installer):
        """测试安装时写入环境变量失败"""
        with patch.object(nvm_installer, 'verify', return_value=False):
            with patch.object(nvm_installer, 'download_file', return_value=True):
                with patch.object(
                    nvm_installer,
                    'run_command',
                    return_value=(0, "installed", "")
                ):
                    with patch.object(
                        nvm_installer,
                        '_write_env_to_shell_config',
                        return_value=False
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = nvm_installer.install()
                            
                            assert report.result == InstallResult.FAILED
                            assert report.tool_name == "nvm"
                            assert "配置文件" in report.message
    
    def test_install_verification_failed(self, nvm_installer):
        """测试安装后验证失败"""
        verify_calls = [False, False]  # 第一次检查是否已安装，第二次验证安装结果
        
        with patch.object(
            nvm_installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(nvm_installer, 'download_file', return_value=True):
                with patch.object(
                    nvm_installer,
                    'run_command',
                    return_value=(0, "installed", "")
                ):
                    with patch.object(
                        nvm_installer,
                        '_write_env_to_shell_config',
                        return_value=True
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = nvm_installer.install()
                            
                            assert report.result == InstallResult.FAILED
                            assert report.tool_name == "nvm"
                            assert "验证" in report.message
    
    def test_install_success(self, nvm_installer):
        """测试成功安装 NVM"""
        verify_calls = [False, True]  # 第一次未安装，第二次验证成功
        
        with patch.object(
            nvm_installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(nvm_installer, 'download_file', return_value=True):
                with patch.object(
                    nvm_installer,
                    'run_command',
                    return_value=(0, "installed", "")
                ):
                    with patch.object(
                        nvm_installer,
                        '_write_env_to_shell_config',
                        return_value=True
                    ):
                        with patch.object(
                            nvm_installer,
                            '_get_installed_version',
                            return_value="0.40.4"
                        ):
                            with patch('pathlib.Path.unlink'):
                                report = nvm_installer.install()
                                
                                assert report.result == InstallResult.SUCCESS
                                assert report.tool_name == "nvm"
                                assert report.version == "0.40.4"
                                assert "成功" in report.message
    
    def test_install_exception_handling(self, nvm_installer):
        """测试安装过程中异常处理"""
        # 让 verify 第一次返回 False（未安装），然后在 download_file 时抛出异常
        with patch.object(nvm_installer, 'verify', return_value=False):
            with patch.object(nvm_installer, 'download_file', side_effect=Exception("Unexpected error")):
                report = nvm_installer.install()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "nvm"
                assert "异常" in report.message
                assert "Unexpected error" in report.error
    
    def test_upgrade_not_installed(self, nvm_installer):
        """测试升级时 NVM 未安装"""
        with patch.object(nvm_installer, 'verify', return_value=False):
            report = nvm_installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "nvm"
            assert "未安装" in report.message
    
    def test_upgrade_download_failed(self, nvm_installer):
        """测试升级时下载脚本失败"""
        with patch.object(nvm_installer, 'verify', return_value=True):
            with patch.object(
                nvm_installer,
                '_get_installed_version',
                return_value="0.39.0"
            ):
                with patch.object(nvm_installer, 'download_file', return_value=False):
                    report = nvm_installer.upgrade()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "nvm"
                    assert "下载" in report.message
    
    def test_upgrade_script_execution_failed(self, nvm_installer):
        """测试升级时脚本执行失败"""
        with patch.object(nvm_installer, 'verify', return_value=True):
            with patch.object(
                nvm_installer,
                '_get_installed_version',
                return_value="0.39.0"
            ):
                with patch.object(nvm_installer, 'download_file', return_value=True):
                    with patch.object(
                        nvm_installer,
                        'run_command',
                        return_value=(1, "", "upgrade error")
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = nvm_installer.upgrade()
                            
                            assert report.result == InstallResult.FAILED
                            assert report.tool_name == "nvm"
                            assert "升级" in report.message or "脚本" in report.message
    
    def test_upgrade_verification_failed(self, nvm_installer):
        """测试升级后验证失败"""
        verify_calls = [True, False]  # 第一次已安装，第二次验证失败
        
        with patch.object(
            nvm_installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(
                nvm_installer,
                '_get_installed_version',
                return_value="0.39.0"
            ):
                with patch.object(nvm_installer, 'download_file', return_value=True):
                    with patch.object(
                        nvm_installer,
                        'run_command',
                        return_value=(0, "upgraded", "")
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = nvm_installer.upgrade()
                            
                            assert report.result == InstallResult.FAILED
                            assert report.tool_name == "nvm"
                            assert "验证" in report.message
    
    def test_upgrade_success(self, nvm_installer):
        """测试成功升级 NVM"""
        verify_calls = [True, True]  # 第一次已安装，第二次验证成功
        version_calls = ["0.39.0", "0.40.4"]  # 升级前后的版本
        
        with patch.object(
            nvm_installer,
            'verify',
            side_effect=verify_calls
        ):
            with patch.object(
                nvm_installer,
                '_get_installed_version',
                side_effect=version_calls
            ):
                with patch.object(nvm_installer, 'download_file', return_value=True):
                    with patch.object(
                        nvm_installer,
                        'run_command',
                        return_value=(0, "upgraded", "")
                    ):
                        with patch('pathlib.Path.unlink'):
                            report = nvm_installer.upgrade()
                            
                            assert report.result == InstallResult.SUCCESS
                            assert report.tool_name == "nvm"
                            assert report.version == "0.40.4"
                            assert "0.39.0" in report.message
                            assert "0.40.4" in report.message
                            assert "成功" in report.message
    
    def test_upgrade_exception_handling(self, nvm_installer):
        """测试升级过程中异常处理"""
        # 让 verify 第一次返回 True（已安装），然后在后续操作时抛出异常
        with patch.object(nvm_installer, 'verify', return_value=True):
            with patch.object(
                nvm_installer,
                '_get_installed_version',
                side_effect=Exception("Unexpected error")
            ):
                report = nvm_installer.upgrade()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "nvm"
                assert "异常" in report.message
                assert "Unexpected error" in report.error
    
    def test_install_cleans_up_temp_file_on_success(self, nvm_installer):
        """测试安装成功后清理临时文件"""
        verify_calls = [False, True]
        
        with patch.object(nvm_installer, 'verify', side_effect=verify_calls):
            with patch.object(nvm_installer, 'download_file', return_value=True):
                with patch.object(
                    nvm_installer,
                    'run_command',
                    return_value=(0, "installed", "")
                ):
                    with patch.object(
                        nvm_installer,
                        '_write_env_to_shell_config',
                        return_value=True
                    ):
                        with patch.object(
                            nvm_installer,
                            '_get_installed_version',
                            return_value="0.40.4"
                        ):
                            with patch('pathlib.Path.unlink') as mock_unlink:
                                report = nvm_installer.install()
                                
                                # 验证临时文件被删除
                                assert mock_unlink.called
                                assert report.result == InstallResult.SUCCESS
    
    def test_install_cleans_up_temp_file_on_failure(self, nvm_installer):
        """测试安装失败后清理临时文件"""
        with patch.object(nvm_installer, 'verify', return_value=False):
            with patch.object(nvm_installer, 'download_file', return_value=True):
                with patch.object(
                    nvm_installer,
                    'run_command',
                    return_value=(1, "", "error")
                ):
                    with patch('pathlib.Path.unlink') as mock_unlink:
                        report = nvm_installer.install()
                        
                        # 验证临时文件被删除
                        assert mock_unlink.called
                        assert report.result == InstallResult.FAILED
