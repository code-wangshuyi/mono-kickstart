"""Node.js 安装器单元测试

测试 Node.js 安装器的各种场景，包括安装、升级、验证等。
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from mono_kickstart.config import ToolConfig
from mono_kickstart.installer_base import InstallResult
from mono_kickstart.installers.node_installer import NodeInstaller
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
    return ToolConfig(enabled=True)


@pytest.fixture
def node_installer(platform_info, tool_config):
    """创建 Node.js 安装器实例"""
    return NodeInstaller(platform_info, tool_config)


class TestNodeInstaller:
    """Node.js 安装器测试类"""
    
    def test_init_with_default_version(self, platform_info):
        """测试使用默认版本初始化"""
        config = ToolConfig(enabled=True)
        installer = NodeInstaller(platform_info, config)
        
        assert installer.node_version == "lts/*"
    
    def test_init_with_custom_version(self, platform_info):
        """测试使用自定义版本初始化"""
        config = ToolConfig(enabled=True, version="18.0.0")
        installer = NodeInstaller(platform_info, config)
        
        assert installer.node_version == "18.0.0"
    
    def test_check_nvm_installed_not_exists(self, node_installer):
        """测试检查 NVM 未安装（文件不存在）"""
        with patch('pathlib.Path.exists', return_value=False):
            assert node_installer._check_nvm_installed() is False
    
    def test_check_nvm_installed_exists_and_working(self, node_installer):
        """测试检查 NVM 已安装且可用"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                node_installer,
                'run_command',
                return_value=(0, "0.40.4", "")
            ):
                assert node_installer._check_nvm_installed() is True
    
    def test_check_nvm_installed_exists_but_not_working(self, node_installer):
        """测试检查 NVM 已安装但无法执行"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                node_installer,
                'run_command',
                return_value=(1, "", "command not found")
            ):
                assert node_installer._check_nvm_installed() is False
    
    def test_verify_node_not_installed(self, node_installer):
        """测试验证 Node.js 未安装"""
        with patch('pathlib.Path.exists', return_value=False):
            assert node_installer.verify() is False
    
    def test_verify_node_installed_success(self, node_installer):
        """测试验证 Node.js 已安装且可用"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                node_installer,
                'run_command',
                return_value=(0, "v18.20.0", "")
            ):
                assert node_installer.verify() is True
    
    def test_verify_node_installed_but_not_working(self, node_installer):
        """测试验证 Node.js 已安装但无法执行"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                node_installer,
                'run_command',
                return_value=(1, "", "command not found")
            ):
                assert node_installer.verify() is False
    
    def test_get_installed_version_success(self, node_installer):
        """测试获取已安装版本成功"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                node_installer,
                'run_command',
                return_value=(0, "v18.20.0\n", "")
            ):
                version = node_installer._get_installed_version()
                assert version == "v18.20.0"
    
    def test_get_installed_version_not_installed(self, node_installer):
        """测试获取版本时 Node.js 未安装"""
        with patch('pathlib.Path.exists', return_value=False):
            version = node_installer._get_installed_version()
            assert version is None
    
    def test_get_installed_version_command_failed(self, node_installer):
        """测试获取版本时命令执行失败"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(
                node_installer,
                'run_command',
                return_value=(1, "", "error")
            ):
                version = node_installer._get_installed_version()
                assert version is None
    
    def test_install_node_via_nvm_success(self, node_installer):
        """测试通过 NVM 安装 Node.js 成功"""
        with patch.object(
            node_installer,
            'run_command',
            return_value=(0, "Downloading and installing node v18.20.0...", "")
        ):
            success, error = node_installer._install_node_via_nvm()
            assert success is True
            assert error == ""
    
    def test_install_node_via_nvm_failed(self, node_installer):
        """测试通过 NVM 安装 Node.js 失败"""
        with patch.object(
            node_installer,
            'run_command',
            return_value=(1, "", "Installation failed")
        ):
            success, error = node_installer._install_node_via_nvm()
            assert success is False
            assert "Installation failed" in error
    
    def test_set_default_version_lts(self, node_installer):
        """测试设置默认版本为 LTS"""
        node_installer.node_version = "lts/*"
        
        with patch.object(
            node_installer,
            'run_command',
            return_value=(0, "default -> lts/* (-> v18.20.0)", "")
        ):
            success, error = node_installer._set_default_version()
            assert success is True
            assert error == ""
    
    def test_set_default_version_specific(self, node_installer):
        """测试设置默认版本为特定版本"""
        node_installer.node_version = "18.0.0"
        
        with patch.object(
            node_installer,
            'run_command',
            return_value=(0, "default -> 18.0.0", "")
        ):
            success, error = node_installer._set_default_version()
            assert success is True
            assert error == ""
    
    def test_set_default_version_failed(self, node_installer):
        """测试设置默认版本失败"""
        with patch.object(
            node_installer,
            'run_command',
            return_value=(1, "", "Failed to set default")
        ):
            success, error = node_installer._set_default_version()
            assert success is False
            assert "Failed to set default" in error
    
    def test_install_nvm_not_installed(self, node_installer):
        """测试安装时 NVM 未安装"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=False):
            report = node_installer.install()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "node"
            assert "NVM 未安装" in report.message
            assert "请先安装 NVM" in report.error
    
    def test_install_already_installed(self, node_installer):
        """测试安装时 Node.js 已安装"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(node_installer, 'verify', return_value=True):
                with patch.object(
                    node_installer,
                    '_get_installed_version',
                    return_value="v18.20.0"
                ):
                    report = node_installer.install()
                    
                    assert report.result == InstallResult.SKIPPED
                    assert report.tool_name == "node"
                    assert report.version == "v18.20.0"
                    assert "已安装" in report.message
    
    def test_install_node_installation_failed(self, node_installer):
        """测试安装时 Node.js 安装失败"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(node_installer, 'verify', return_value=False):
                with patch.object(
                    node_installer,
                    '_install_node_via_nvm',
                    return_value=(False, "Installation error")
                ):
                    report = node_installer.install()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "node"
                    assert "安装 Node.js 失败" in report.message
                    assert "Installation error" in report.error
    
    def test_install_set_default_failed(self, node_installer):
        """测试安装时设置默认版本失败"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(node_installer, 'verify', return_value=False):
                with patch.object(
                    node_installer,
                    '_install_node_via_nvm',
                    return_value=(True, "")
                ):
                    with patch.object(
                        node_installer,
                        '_set_default_version',
                        return_value=(False, "Failed to set default")
                    ):
                        report = node_installer.install()
                        
                        assert report.result == InstallResult.FAILED
                        assert report.tool_name == "node"
                        assert "默认版本失败" in report.message
                        assert "Failed to set default" in report.error
    
    def test_install_verification_failed(self, node_installer):
        """测试安装后验证失败"""
        verify_calls = [False, False]  # 第一次检查是否已安装，第二次验证安装结果
        
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(
                node_installer,
                'verify',
                side_effect=verify_calls
            ):
                with patch.object(
                    node_installer,
                    '_install_node_via_nvm',
                    return_value=(True, "")
                ):
                    with patch.object(
                        node_installer,
                        '_set_default_version',
                        return_value=(True, "")
                    ):
                        report = node_installer.install()
                        
                        assert report.result == InstallResult.FAILED
                        assert report.tool_name == "node"
                        assert "验证失败" in report.message
    
    def test_install_success(self, node_installer):
        """测试成功安装 Node.js"""
        verify_calls = [False, True]  # 第一次未安装，第二次验证成功
        
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(
                node_installer,
                'verify',
                side_effect=verify_calls
            ):
                with patch.object(
                    node_installer,
                    '_install_node_via_nvm',
                    return_value=(True, "")
                ):
                    with patch.object(
                        node_installer,
                        '_set_default_version',
                        return_value=(True, "")
                    ):
                        with patch.object(
                            node_installer,
                            '_get_installed_version',
                            return_value="v18.20.0"
                        ):
                            report = node_installer.install()
                            
                            assert report.result == InstallResult.SUCCESS
                            assert report.tool_name == "node"
                            assert report.version == "v18.20.0"
                            assert "成功" in report.message
    
    def test_install_exception_handling(self, node_installer):
        """测试安装过程中异常处理"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(node_installer, 'verify', return_value=False):
                with patch.object(
                    node_installer,
                    '_install_node_via_nvm',
                    side_effect=Exception("Unexpected error")
                ):
                    report = node_installer.install()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "node"
                    assert "异常" in report.message
                    assert "Unexpected error" in report.error
    
    def test_upgrade_nvm_not_installed(self, node_installer):
        """测试升级时 NVM 未安装"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=False):
            report = node_installer.upgrade()
            
            assert report.result == InstallResult.FAILED
            assert report.tool_name == "node"
            assert "NVM 未安装" in report.message
    
    def test_upgrade_node_not_installed(self, node_installer):
        """测试升级时 Node.js 未安装"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(node_installer, 'verify', return_value=False):
                report = node_installer.upgrade()
                
                assert report.result == InstallResult.FAILED
                assert report.tool_name == "node"
                assert "未安装" in report.message
    
    def test_upgrade_installation_failed(self, node_installer):
        """测试升级时安装失败"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(node_installer, 'verify', return_value=True):
                with patch.object(
                    node_installer,
                    '_get_installed_version',
                    return_value="v16.0.0"
                ):
                    with patch.object(
                        node_installer,
                        '_install_node_via_nvm',
                        return_value=(False, "Upgrade failed")
                    ):
                        report = node_installer.upgrade()
                        
                        assert report.result == InstallResult.FAILED
                        assert report.tool_name == "node"
                        assert "升级 Node.js 失败" in report.message
                        assert "Upgrade failed" in report.error
    
    def test_upgrade_set_default_failed(self, node_installer):
        """测试升级时设置默认版本失败"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(node_installer, 'verify', return_value=True):
                with patch.object(
                    node_installer,
                    '_get_installed_version',
                    return_value="v16.0.0"
                ):
                    with patch.object(
                        node_installer,
                        '_install_node_via_nvm',
                        return_value=(True, "")
                    ):
                        with patch.object(
                            node_installer,
                            '_set_default_version',
                            return_value=(False, "Failed to set default")
                        ):
                            report = node_installer.upgrade()
                            
                            assert report.result == InstallResult.FAILED
                            assert report.tool_name == "node"
                            assert "默认版本失败" in report.message
    
    def test_upgrade_verification_failed(self, node_installer):
        """测试升级后验证失败"""
        verify_calls = [True, False]  # 第一次已安装，第二次验证失败
        
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(
                node_installer,
                'verify',
                side_effect=verify_calls
            ):
                with patch.object(
                    node_installer,
                    '_get_installed_version',
                    return_value="v16.0.0"
                ):
                    with patch.object(
                        node_installer,
                        '_install_node_via_nvm',
                        return_value=(True, "")
                    ):
                        with patch.object(
                            node_installer,
                            '_set_default_version',
                            return_value=(True, "")
                        ):
                            report = node_installer.upgrade()
                            
                            assert report.result == InstallResult.FAILED
                            assert report.tool_name == "node"
                            assert "验证失败" in report.message
    
    def test_upgrade_success(self, node_installer):
        """测试成功升级 Node.js"""
        verify_calls = [True, True]  # 第一次已安装，第二次验证成功
        version_calls = ["v16.0.0", "v18.20.0"]  # 升级前后的版本
        
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(
                node_installer,
                'verify',
                side_effect=verify_calls
            ):
                with patch.object(
                    node_installer,
                    '_get_installed_version',
                    side_effect=version_calls
                ):
                    with patch.object(
                        node_installer,
                        '_install_node_via_nvm',
                        return_value=(True, "")
                    ):
                        with patch.object(
                            node_installer,
                            '_set_default_version',
                            return_value=(True, "")
                        ):
                            report = node_installer.upgrade()
                            
                            assert report.result == InstallResult.SUCCESS
                            assert report.tool_name == "node"
                            assert report.version == "v18.20.0"
                            assert "v16.0.0" in report.message
                            assert "v18.20.0" in report.message
                            assert "成功" in report.message
    
    def test_upgrade_exception_handling(self, node_installer):
        """测试升级过程中异常处理"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(node_installer, 'verify', return_value=True):
                with patch.object(
                    node_installer,
                    '_get_installed_version',
                    side_effect=Exception("Unexpected error")
                ):
                    report = node_installer.upgrade()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "node"
                    assert "异常" in report.message
                    assert "Unexpected error" in report.error
    
    def test_install_with_lts_version(self, platform_info):
        """测试使用 LTS 版本安装"""
        config = ToolConfig(enabled=True, version="lts/*")
        installer = NodeInstaller(platform_info, config)
        
        verify_calls = [False, True]
        
        with patch.object(installer, '_check_nvm_installed', return_value=True):
            with patch.object(installer, 'verify', side_effect=verify_calls):
                with patch.object(
                    installer,
                    '_install_node_via_nvm',
                    return_value=(True, "")
                ) as mock_install:
                    with patch.object(
                        installer,
                        '_set_default_version',
                        return_value=(True, "")
                    ):
                        with patch.object(
                            installer,
                            '_get_installed_version',
                            return_value="v18.20.0"
                        ):
                            report = installer.install()
                            
                            assert report.result == InstallResult.SUCCESS
                            # 验证使用了 lts/* 版本
                            assert installer.node_version == "lts/*"
    
    def test_install_with_specific_version(self, platform_info):
        """测试使用特定版本安装"""
        config = ToolConfig(enabled=True, version="16.20.0")
        installer = NodeInstaller(platform_info, config)
        
        verify_calls = [False, True]
        
        with patch.object(installer, '_check_nvm_installed', return_value=True):
            with patch.object(installer, 'verify', side_effect=verify_calls):
                with patch.object(
                    installer,
                    '_install_node_via_nvm',
                    return_value=(True, "")
                ):
                    with patch.object(
                        installer,
                        '_set_default_version',
                        return_value=(True, "")
                    ):
                        with patch.object(
                            installer,
                            '_get_installed_version',
                            return_value="v16.20.0"
                        ):
                            report = installer.install()
                            
                            assert report.result == InstallResult.SUCCESS
                            # 验证使用了指定版本
                            assert installer.node_version == "16.20.0"
    
    def test_install_timeout_handling(self, node_installer):
        """测试安装超时处理"""
        with patch.object(node_installer, '_check_nvm_installed', return_value=True):
            with patch.object(node_installer, 'verify', return_value=False):
                with patch.object(
                    node_installer,
                    'run_command',
                    side_effect=Exception("Timeout")
                ):
                    report = node_installer.install()
                    
                    assert report.result == InstallResult.FAILED
                    assert report.tool_name == "node"
                    assert "异常" in report.message
