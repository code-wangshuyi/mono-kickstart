"""GitHub Copilot CLI 安装器的基于属性的测试

本模块使用 Hypothesis 框架测试 Copilot CLI 安装器的通用属性。
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from mono_kickstart.config import ToolConfig
from mono_kickstart.installer_base import InstallResult
from mono_kickstart.installers.copilot_installer import CopilotCLIInstaller
from mono_kickstart.platform_detector import Arch, OS, PlatformInfo, Shell


def create_platform_info_macos():
    """创建测试用的 macOS 平台信息"""
    return PlatformInfo(
        os=OS.MACOS,
        arch=Arch.ARM64,
        shell=Shell.ZSH,
        shell_config_file=str(Path.home() / ".zshrc")
    )


def create_tool_config():
    """创建测试用的工具配置"""
    return ToolConfig(enabled=True)


class TestNodeVersionValidation:
    """测试属性 1: Node.js 版本依赖验证
    
    **Validates: Requirements 3.2, 3.3**
    
    对于任何 Node.js 版本号，系统应该正确判断版本是否满足最低要求（>= 22），
    并在不满足时返回包含版本要求的失败报告。
    """
    
    @given(major_version=st.integers(min_value=0, max_value=50))
    def test_node_version_validation_logic(self, major_version):
        """验证 Node.js 版本判断逻辑的正确性
        
        对于任意主版本号，验证系统是否正确判断版本是否满足要求。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        version_string = f"v{major_version}.0.0"
        
        with patch('shutil.which', return_value="/usr/local/bin/node"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, version_string, "")
            ):
                ok, error = installer._check_node_version()
                
                # 验证判断逻辑正确
                if major_version >= 22:
                    assert ok is True, f"版本 {version_string} 应该满足要求"
                    assert error is None, f"版本 {version_string} 不应该有错误信息"
                else:
                    assert ok is False, f"版本 {version_string} 不应该满足要求"
                    assert error is not None, f"版本 {version_string} 应该有错误信息"
    
    @given(major_version=st.integers(min_value=0, max_value=21))
    def test_node_version_too_low_error_message(self, major_version):
        """验证版本过低时错误信息的完整性
        
        对于任何低于最低要求的版本，错误信息应该包含当前版本和最低要求版本。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        version_string = f"v{major_version}.0.0"
        
        with patch('shutil.which', return_value="/usr/local/bin/node"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, version_string, "")
            ):
                ok, error = installer._check_node_version()
                
                # 验证返回失败
                assert ok is False
                assert error is not None
                
                # 验证错误信息包含必要信息
                assert "版本过低" in error or "过低" in error, "错误信息应该说明版本过低"
                assert version_string in error, "错误信息应该包含当前版本"
                assert "22" in error, "错误信息应该包含最低版本要求"
    
    @given(
        major_version=st.integers(min_value=22, max_value=50),
        minor_version=st.integers(min_value=0, max_value=20),
        patch_version=st.integers(min_value=0, max_value=20)
    )
    def test_node_version_with_minor_and_patch(
        self, major_version, minor_version, patch_version
    ):
        """验证版本判断只关注主版本号
        
        对于任何满足主版本号要求的版本，无论次版本号和补丁版本号如何，都应该通过验证。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        version_string = f"v{major_version}.{minor_version}.{patch_version}"
        
        with patch('shutil.which', return_value="/usr/local/bin/node"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, version_string, "")
            ):
                ok, error = installer._check_node_version()
                
                # 主版本号 >= 22 应该通过
                assert ok is True
                assert error is None
    
    @given(
        version_prefix=st.sampled_from(["", "v", "V", "version "]),
        major_version=st.integers(min_value=22, max_value=30)
    )
    def test_node_version_format_variations(
        self, version_prefix, major_version
    ):
        """验证版本号格式解析的健壮性
        
        对于不同的版本号格式前缀，系统应该能够正确解析（或合理拒绝）。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        version_string = f"{version_prefix}{major_version}.0.0"
        
        with patch('shutil.which', return_value="/usr/local/bin/node"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, version_string, "")
            ):
                ok, error = installer._check_node_version()
                
                # 只有 'v' 前缀应该被正确解析
                if version_prefix == "v":
                    assert ok is True
                    assert error is None
                else:
                    # 其他格式应该返回解析错误
                    assert ok is False
                    assert error is not None
                    assert "解析" in error or "格式" in error
    
    @given(major_version=st.integers(min_value=0, max_value=50))
    def test_node_not_installed_error_message(self, major_version):
        """验证 Node.js 未安装时的错误信息
        
        无论请求检查什么版本，如果 Node.js 未安装，都应该返回明确的错误信息。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        with patch('shutil.which', return_value=None):
            ok, error = installer._check_node_version()
            
            # 验证返回失败
            assert ok is False
            assert error is not None
            
            # 验证错误信息说明 Node.js 未安装
            assert "未安装" in error or "not installed" in error.lower()
            assert "Node" in error or "node" in error


class TestSkipInstalledToolLogic:
    """测试属性 7: 已安装工具跳过逻辑
    
    **Validates: Requirements 10.2, 10.3**
    
    对于任何已安装的 Copilot CLI，调用 install() 方法应该返回 
    InstallResult.SKIPPED 状态，并在报告中包含当前版本信息。
    """
    
    @given(installed_version=st.text(min_size=1, max_size=50))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_skip_when_already_installed(self, installed_version):
        """验证已安装时跳过安装逻辑
        
        对于任意已安装版本，验证 install() 方法返回 SKIPPED 状态。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock copilot 命令已安装
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, installed_version, "")
            ):
                report = installer.install()
                
                # 验证返回 SKIPPED 状态
                assert report.result == InstallResult.SKIPPED, \
                    f"已安装时应该返回 SKIPPED，实际返回: {report.result}"
                
                # 验证报告包含版本信息
                assert report.version is not None, \
                    "SKIPPED 报告应该包含版本信息"
                # 版本信息应该是 strip() 后的结果（实现会调用 strip()）
                assert report.version == installed_version.strip(), \
                    f"报告中的版本应该是 {installed_version.strip()}，实际是 {report.version}"
                
                # 验证消息说明跳过安装
                assert "跳过" in report.message or "已安装" in report.message, \
                    "消息应该说明跳过安装"
    
    @given(
        installed_version=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Nd', 'Ll'), whitelist_characters='.-')
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_skip_with_version_format_variations(self, installed_version):
        """验证不同版本格式下的跳过逻辑
        
        对于不同格式的版本号（如 1.0.0, v1.0.0, 1.0.0-beta），
        都应该正确返回 SKIPPED 状态并包含版本信息。
        """
        # 跳过空字符串或只有特殊字符的版本
        if not installed_version or installed_version.strip() in ["", ".", "-"]:
            return
        
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock copilot 命令已安装
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, installed_version, "")
            ):
                report = installer.install()
                
                # 验证返回 SKIPPED 状态
                assert report.result == InstallResult.SKIPPED
                
                # 验证报告包含版本信息（strip() 后的结果）
                assert report.version is not None
                assert report.version == installed_version.strip()
    
    @given(
        installed_version=st.text(min_size=1, max_size=50),
        node_major_version=st.integers(min_value=22, max_value=30)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_skip_without_checking_node_version(
        self, installed_version, node_major_version
    ):
        """验证已安装时不检查 Node.js 版本
        
        当 Copilot CLI 已安装时，应该直接返回 SKIPPED，
        而不需要检查 Node.js 版本（因为已经安装说明依赖已满足）。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock copilot 命令已安装
        with patch('shutil.which') as mock_which:
            # 设置 copilot 可用，但 node 不可用
            def which_side_effect(cmd):
                if cmd == "copilot":
                    return "/usr/local/bin/copilot"
                elif cmd == "node":
                    return None  # Node.js 不可用
                return None
            
            mock_which.side_effect = which_side_effect
            
            with patch.object(
                installer,
                'run_command',
                return_value=(0, installed_version, "")
            ):
                report = installer.install()
                
                # 即使 Node.js 不可用，已安装的工具也应该返回 SKIPPED
                assert report.result == InstallResult.SKIPPED
                # 版本信息应该是 strip() 后的结果
                assert report.version == installed_version.strip()
    
    @given(installed_version=st.text(min_size=1, max_size=50))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_skip_result_never_has_error(self, installed_version):
        """验证 SKIPPED 状态不应该包含错误信息
        
        对于任何已安装的版本，返回 SKIPPED 状态时，
        error 字段应该为 None（因为这不是错误情况）。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock copilot 命令已安装
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, installed_version, "")
            ):
                report = installer.install()
                
                # 验证 SKIPPED 状态
                assert report.result == InstallResult.SKIPPED
                
                # 验证没有错误信息
                assert report.error is None, \
                    "SKIPPED 状态不应该包含错误信息"
    
    @given(
        installed_version=st.text(min_size=1, max_size=50),
        verify_call_count=st.integers(min_value=1, max_value=1)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_called_before_skip(
        self, installed_version, verify_call_count
    ):
        """验证跳过前调用了 verify() 方法
        
        install() 方法应该首先调用 verify() 检查是否已安装，
        然后才决定是否跳过安装。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        verify_called = []
        
        # Mock verify 方法来追踪调用
        original_verify = installer.verify
        
        def mock_verify():
            verify_called.append(True)
            return original_verify()
        
        # Mock copilot 命令已安装
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, installed_version, "")
            ):
                with patch.object(installer, 'verify', side_effect=mock_verify):
                    report = installer.install()
                    
                    # 验证 verify 被调用
                    assert len(verify_called) >= verify_call_count, \
                        "install() 应该调用 verify() 检查是否已安装"
                    
                    # 验证返回 SKIPPED
                    assert report.result == InstallResult.SKIPPED


class TestConfigDrivenBehavior:
    """测试属性 4: 配置驱动行为
    
    **Validates: Requirements 6.2, 6.4**
    
    对于任何配置对象，当 copilot-cli.enabled 设置为 False 时，系统应该跳过安装；
    当未指定配置时，应使用默认值（enabled=True）。
    """
    
    @given(enabled=st.booleans())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_enabled_flag_controls_installation(self, enabled):
        """验证 enabled 标志控制安装行为
        
        对于任何 enabled 值（True 或 False），验证配置是否正确控制安装行为。
        注意：这个测试验证配置对象的创建，实际的跳过逻辑由编排器处理。
        """
        # 创建配置对象
        tool_config = ToolConfig(enabled=enabled)
        
        # 验证配置对象的 enabled 字段正确设置
        assert tool_config.enabled == enabled, \
            f"配置的 enabled 字段应该是 {enabled}，实际是 {tool_config.enabled}"
        
        # 验证安装器可以正常创建（无论 enabled 值如何）
        platform_info_macos = create_platform_info_macos()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # 验证安装器的配置正确
        assert installer.config.enabled == enabled, \
            f"安装器的配置 enabled 字段应该是 {enabled}，实际是 {installer.config.enabled}"
    
    def test_default_config_enabled_is_true(self):
        """验证默认配置的 enabled 为 True
        
        当未指定配置时，应使用默认值 enabled=True。
        """
        # 创建默认配置对象（不传递任何参数）
        tool_config = ToolConfig()
        
        # 验证默认值为 True
        assert tool_config.enabled is True, \
            f"默认配置的 enabled 应该是 True，实际是 {tool_config.enabled}"
        
        # 验证安装器使用默认配置
        platform_info_macos = create_platform_info_macos()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        assert installer.config.enabled is True, \
            "使用默认配置的安装器 enabled 应该是 True"
    
    @given(
        enabled=st.booleans(),
        version=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
        install_via=st.one_of(st.none(), st.sampled_from(["npm", "brew"]))
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_config_fields_preserved(self, enabled, version, install_via):
        """验证配置字段正确保存
        
        对于任何配置值组合，验证配置对象正确保存所有字段。
        """
        # 创建配置对象
        tool_config = ToolConfig(
            enabled=enabled,
            version=version,
            install_via=install_via
        )
        
        # 验证所有字段正确保存
        assert tool_config.enabled == enabled
        assert tool_config.version == version
        assert tool_config.install_via == install_via
        
        # 验证安装器可以访问配置
        platform_info_macos = create_platform_info_macos()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        assert installer.config.enabled == enabled
        assert installer.config.version == version
        assert installer.config.install_via == install_via
    
    @given(enabled=st.booleans())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_config_enabled_does_not_affect_verify(self, enabled):
        """验证 enabled 配置不影响 verify() 方法
        
        verify() 方法应该检查实际安装状态，不受 enabled 配置影响。
        """
        tool_config = ToolConfig(enabled=enabled)
        platform_info_macos = create_platform_info_macos()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock copilot 命令已安装
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, "1.0.0", "")
            ):
                # 无论 enabled 值如何，verify() 都应该返回 True
                result = installer.verify()
                assert result is True, \
                    f"当 copilot 已安装时，verify() 应该返回 True（enabled={enabled}）"
        
        # Mock copilot 命令未安装
        with patch('shutil.which', return_value=None):
            # 无论 enabled 值如何，verify() 都应该返回 False
            result = installer.verify()
            assert result is False, \
                f"当 copilot 未安装时，verify() 应该返回 False（enabled={enabled}）"
    
    @given(
        enabled=st.booleans(),
        extra_options=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(), st.integers(), st.booleans()),
            max_size=5
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_extra_options_preserved(self, enabled, extra_options):
        """验证 extra_options 字段正确保存
        
        对于任何 extra_options 值，验证配置对象正确保存。
        """
        # 创建配置对象
        tool_config = ToolConfig(
            enabled=enabled,
            extra_options=extra_options
        )
        
        # 验证 extra_options 正确保存
        assert tool_config.extra_options == extra_options
        
        # 验证安装器可以访问 extra_options
        platform_info_macos = create_platform_info_macos()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        assert installer.config.extra_options == extra_options


class TestUpgradeVersionTracking:
    """测试属性 5: 升级报告版本追踪
    
    **Validates: Requirements 8.3**
    
    对于任何成功的升级操作，返回的 InstallReport 应该在 message 字段中
    包含升级前后的版本信息。
    """
    
    @given(
        old_version=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Nd', 'Ll'), whitelist_characters='.-')
        ),
        new_version=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Nd', 'Ll'), whitelist_characters='.-')
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_upgrade_report_contains_version_change(
        self, old_version, new_version
    ):
        """验证升级报告包含版本变化信息
        
        对于任何成功的升级操作，报告的 message 字段应该包含
        升级前后的版本信息（格式: old_version -> new_version）。
        """
        # 跳过无效的版本字符串
        if not old_version.strip() or not new_version.strip():
            return
        if old_version.strip() in ["", ".", "-"] or new_version.strip() in ["", ".", "-"]:
            return
        
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        old_version_stripped = old_version.strip()
        new_version_stripped = new_version.strip()
        
        # Mock copilot 命令已安装
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            # 使用列表追踪调用次数，确保正确返回版本
            call_count = [0]
            
            def mock_run_command(cmd, **kwargs):
                if "copilot --version" in cmd:
                    # verify() 调用一次，_get_installed_version() 调用两次
                    # 第一次: verify() 检查是否已安装
                    # 第二次: _get_installed_version() 获取旧版本
                    # 第三次: _get_installed_version() 获取新版本
                    if call_count[0] == 0:
                        # verify() 调用
                        call_count[0] += 1
                        return (0, old_version, "")
                    elif call_count[0] == 1:
                        # 获取旧版本
                        call_count[0] += 1
                        return (0, old_version, "")
                    else:
                        # 获取新版本
                        return (0, new_version, "")
                elif "npm update" in cmd:
                    # 升级命令成功
                    return (0, "upgraded", "")
                else:
                    return (0, "", "")
            
            with patch.object(
                installer,
                'run_command',
                side_effect=mock_run_command
            ):
                report = installer.upgrade()
                
                # 验证升级成功
                assert report.result == InstallResult.SUCCESS, \
                    f"升级应该成功，实际返回: {report.result}"
                
                # 验证 message 包含版本变化信息
                assert report.message is not None, \
                    "升级报告应该包含消息"
                
                # 验证消息包含旧版本和新版本
                assert old_version_stripped in report.message, \
                    f"消息应该包含旧版本 {old_version_stripped}，实际消息: {report.message}"
                assert new_version_stripped in report.message, \
                    f"消息应该包含新版本 {new_version_stripped}，实际消息: {report.message}"
                
                # 验证消息包含版本变化指示符（->）
                assert "->" in report.message, \
                    f"消息应该包含版本变化指示符 '->'，实际消息: {report.message}"
                
                # 只有当版本不同时才验证顺序
                if old_version_stripped != new_version_stripped:
                    # 验证版本顺序正确（旧版本在前，新版本在后）
                    # 使用更精确的匹配：查找 "old -> new" 模式
                    expected_pattern = f"{old_version_stripped} -> {new_version_stripped}"
                    assert expected_pattern in report.message, \
                        f"消息应该包含版本变化模式 '{expected_pattern}'，实际消息: {report.message}"
    
    @given(
        version=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Nd', 'Ll'), whitelist_characters='.-')
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_upgrade_report_version_field_contains_new_version(self, version):
        """验证升级报告的 version 字段包含新版本
        
        对于任何成功的升级操作，报告的 version 字段应该包含升级后的新版本。
        """
        # 跳过无效的版本字符串
        if not version.strip() or version.strip() in ["", ".", "-"]:
            return
        
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        old_version = "1.0.0"  # 固定旧版本
        new_version = version
        
        # Mock copilot 命令已安装
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            # 第一次调用返回旧版本，第二次调用返回新版本
            version_calls = [old_version, new_version]
            call_count = [0]
            
            def mock_run_command(cmd, **kwargs):
                if "copilot --version" in cmd:
                    # 返回版本信息
                    idx = min(call_count[0], len(version_calls) - 1)
                    result = (0, version_calls[idx], "")
                    call_count[0] += 1
                    return result
                elif "npm update" in cmd:
                    # 升级命令成功
                    return (0, "upgraded", "")
                else:
                    return (0, "", "")
            
            with patch.object(
                installer,
                'run_command',
                side_effect=mock_run_command
            ):
                report = installer.upgrade()
                
                # 验证升级成功
                assert report.result == InstallResult.SUCCESS
                
                # 验证 version 字段包含新版本
                assert report.version is not None, \
                    "升级报告应该包含版本信息"
                assert report.version == new_version.strip(), \
                    f"version 字段应该是新版本 {new_version.strip()}，实际是 {report.version}"
    
    @given(
        old_version=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Nd', 'Ll'), whitelist_characters='.-')
        ),
        new_version=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Nd', 'Ll'), whitelist_characters='.-')
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_upgrade_success_never_has_error(
        self, old_version, new_version
    ):
        """验证成功的升级不应该包含错误信息
        
        对于任何成功的升级操作，报告的 error 字段应该为 None。
        """
        # 跳过无效的版本字符串
        if not old_version.strip() or not new_version.strip():
            return
        if old_version.strip() in ["", ".", "-"] or new_version.strip() in ["", ".", "-"]:
            return
        
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock copilot 命令已安装
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            # 第一次调用返回旧版本，第二次调用返回新版本
            version_calls = [old_version, new_version]
            call_count = [0]
            
            def mock_run_command(cmd, **kwargs):
                if "copilot --version" in cmd:
                    # 返回版本信息
                    idx = min(call_count[0], len(version_calls) - 1)
                    result = (0, version_calls[idx], "")
                    call_count[0] += 1
                    return result
                elif "npm update" in cmd:
                    # 升级命令成功
                    return (0, "upgraded", "")
                else:
                    return (0, "", "")
            
            with patch.object(
                installer,
                'run_command',
                side_effect=mock_run_command
            ):
                report = installer.upgrade()
                
                # 验证升级成功
                assert report.result == InstallResult.SUCCESS
                
                # 验证没有错误信息
                assert report.error is None, \
                    f"成功的升级不应该包含错误信息，实际 error: {report.error}"
    
    @given(
        old_version=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Nd', 'Ll'), whitelist_characters='.-')
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_upgrade_not_installed_fails_with_error(self, old_version):
        """验证未安装时升级失败并包含错误信息
        
        当 Copilot CLI 未安装时，upgrade() 应该返回 FAILED 状态，
        并在 error 字段中说明需要先安装。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock copilot 命令未安装
        with patch('shutil.which', return_value=None):
            report = installer.upgrade()
            
            # 验证返回失败
            assert report.result == InstallResult.FAILED, \
                f"未安装时升级应该失败，实际返回: {report.result}"
            
            # 验证包含错误信息
            assert report.error is not None, \
                "未安装时升级应该包含错误信息"
            
            # 验证错误信息说明需要先安装
            assert "未安装" in report.error or "先安装" in report.error, \
                f"错误信息应该说明需要先安装，实际错误: {report.error}"
    
    @given(
        old_version=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Nd', 'Ll'), whitelist_characters='.-')
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_upgrade_command_failure_includes_error(self, old_version):
        """验证升级命令失败时包含错误信息
        
        当 npm update 命令失败时，应该返回 FAILED 状态，
        并在 error 字段中包含错误详情。
        """
        # 跳过无效的版本字符串
        if not old_version.strip() or old_version.strip() in ["", ".", "-"]:
            return
        
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        error_message = "npm update failed: network error"
        
        # Mock copilot 命令已安装
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            def mock_run_command(cmd, **kwargs):
                if "copilot --version" in cmd:
                    # 返回旧版本
                    return (0, old_version, "")
                elif "npm update" in cmd:
                    # 升级命令失败
                    return (1, "", error_message)
                else:
                    return (0, "", "")
            
            with patch.object(
                installer,
                'run_command',
                side_effect=mock_run_command
            ):
                report = installer.upgrade()
                
                # 验证返回失败
                assert report.result == InstallResult.FAILED, \
                    f"升级命令失败应该返回 FAILED，实际返回: {report.result}"
                
                # 验证包含错误信息
                assert report.error is not None, \
                    "升级命令失败应该包含错误信息"
                
                # 验证错误信息包含失败详情
                assert error_message in report.error or "失败" in report.message, \
                    f"错误信息应该包含失败详情，实际错误: {report.error}, 消息: {report.message}"
