"""GitHub Copilot CLI 安装器的综合属性测试 - Task 8

本模块包含 Task 8 的三个属性测试：
- Property 2: 安装验证一致性
- Property 3: 版本信息完整性
- Property 6: 错误处理完整性
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

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


class TestVerificationConsistency:
    """测试属性 2: 安装验证一致性
    
    **Validates: Requirements 4.2, 4.3**
    
    对于任何系统状态，verify() 方法应该在 copilot 命令可用且 
    copilot --version 成功时返回 True，否则返回 False。
    """

    @given(
        copilot_available=st.booleans(),
        version_cmd_success=st.booleans()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_consistency_with_command_availability(
        self, copilot_available, version_cmd_success
    ):
        """验证 verify() 方法的一致性
        
        对于任何命令可用性和版本命令执行结果的组合，
        verify() 应该返回一致的结果。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock shutil.which
        copilot_path = "/usr/local/bin/copilot" if copilot_available else None
        
        with patch('shutil.which', return_value=copilot_path):
            if copilot_available:
                # Mock run_command
                returncode = 0 if version_cmd_success else 1
                with patch.object(
                    installer,
                    'run_command',
                    return_value=(returncode, "1.0.0", "")
                ):
                    result = installer.verify()
                    
                    # 验证一致性：命令可用且版本命令成功时返回 True
                    expected = copilot_available and version_cmd_success
                    assert result == expected, \
                        f"verify() 应该返回 {expected}（copilot_available={copilot_available}, version_cmd_success={version_cmd_success}），实际返回: {result}"
            else:
                # 命令不可用时应该直接返回 False
                result = installer.verify()
                assert result is False, \
                    "当 copilot 命令不可用时，verify() 应该返回 False"

    @given(version_output=st.text(min_size=1, max_size=50))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_returns_true_when_version_command_succeeds(
        self, version_output
    ):
        """验证当版本命令成功时 verify() 返回 True
        
        对于任何版本输出，只要命令返回码为 0，verify() 应该返回 True。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, version_output, "")
            ):
                result = installer.verify()
                assert result is True, \
                    f"当 copilot --version 成功时，verify() 应该返回 True（版本输出: {version_output}）"

    @given(returncode=st.integers(min_value=1, max_value=255))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_verify_returns_false_when_version_command_fails(
        self, returncode
    ):
        """验证当版本命令失败时 verify() 返回 False
        
        对于任何非零返回码，verify() 应该返回 False。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command',
                return_value=(returncode, "", "error")
            ):
                result = installer.verify()
                assert result is False, \
                    f"当 copilot --version 返回非零退出码 {returncode} 时，verify() 应该返回 False"


class TestVersionInfoCompleteness:
    """测试属性 3: 版本信息完整性
    
    **Validates: Requirements 5.2, 5.4**
    
    对于任何成功的安装或升级操作，返回的 InstallReport 应该包含有效的版本信息字段。
    """

    @given(
        version=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('Nd', 'Ll'), whitelist_characters='.-')
        ),
        node_major_version=st.integers(min_value=22, max_value=30)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_successful_install_includes_version(
        self, version, node_major_version
    ):
        """验证成功的安装包含版本信息
        
        对于任何成功的安装操作，InstallReport 应该包含非空的 version 字段。
        """
        # 跳过无效的版本字符串
        if not version.strip() or version.strip() in ["", ".", "-"]:
            return
        
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        node_version = f"v{node_major_version}.0.0"
        
        # Mock 未安装状态
        with patch('shutil.which') as mock_which:
            call_count = [0]
            
            def which_side_effect(cmd):
                if cmd == "copilot":
                    # 第一次调用（verify 检查）返回 None（未安装）
                    # 后续调用返回路径（已安装）
                    if call_count[0] == 0:
                        call_count[0] += 1
                        return None
                    else:
                        return "/usr/local/bin/copilot"
                elif cmd == "node":
                    return "/usr/local/bin/node"
                return None
            
            mock_which.side_effect = which_side_effect

            with patch.object(
                installer,
                'run_command'
            ) as mock_run_command:
                def run_command_side_effect(cmd, **kwargs):
                    if "node --version" in cmd:
                        return (0, node_version, "")
                    elif "npm install" in cmd:
                        return (0, "installed", "")
                    elif "copilot --version" in cmd:
                        return (0, version, "")
                    return (0, "", "")
                
                mock_run_command.side_effect = run_command_side_effect
                
                report = installer.install()
                
                # 验证安装成功
                assert report.result == InstallResult.SUCCESS, \
                    f"安装应该成功，实际返回: {report.result}"
                
                # 验证包含版本信息
                assert report.version is not None, \
                    "成功的安装报告应该包含版本信息"
                assert report.version == version.strip(), \
                    f"版本信息应该是 {version.strip()}，实际是 {report.version}"

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
    def test_successful_upgrade_includes_version(
        self, old_version, new_version
    ):
        """验证成功的升级包含版本信息
        
        对于任何成功的升级操作，InstallReport 应该包含非空的 version 字段。
        """
        # 跳过无效的版本字符串
        if not old_version.strip() or not new_version.strip():
            return
        if old_version.strip() in ["", ".", "-"] or new_version.strip() in ["", ".", "-"]:
            return
        
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            version_calls = [old_version, new_version]
            call_count = [0]
            
            def mock_run_command(cmd, **kwargs):
                if "copilot --version" in cmd:
                    idx = min(call_count[0], len(version_calls) - 1)
                    result = (0, version_calls[idx], "")
                    call_count[0] += 1
                    return result
                elif "npm update" in cmd:
                    return (0, "upgraded", "")
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
                
                # 验证包含版本信息
                assert report.version is not None, \
                    "成功的升级报告应该包含版本信息"
                assert report.version == new_version.strip(), \
                    f"版本信息应该是新版本 {new_version.strip()}，实际是 {report.version}"

    @given(version=st.text(min_size=1, max_size=50))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_skipped_install_includes_version(self, version):
        """验证跳过的安装包含版本信息
        
        当工具已安装时，SKIPPED 报告也应该包含当前版本信息。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command',
                return_value=(0, version, "")
            ):
                report = installer.install()
                
                # 验证返回 SKIPPED
                assert report.result == InstallResult.SKIPPED, \
                    f"已安装时应该返回 SKIPPED，实际返回: {report.result}"
                
                # 验证包含版本信息
                assert report.version is not None, \
                    "SKIPPED 报告应该包含版本信息"
                assert report.version == version.strip(), \
                    f"版本信息应该是 {version.strip()}，实际是 {report.version}"


class TestErrorHandlingCompleteness:
    """测试属性 6: 错误处理完整性
    
    **Validates: Requirements 9.1, 9.2**
    
    对于任何失败的安装或升级操作（命令失败或异常），系统应该返回 
    InstallResult.FAILED 状态，并在 error 字段中包含错误详情。
    """

    @given(
        node_major_version=st.integers(min_value=0, max_value=21),
        error_message=st.text(min_size=1, max_size=100)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_install_failure_includes_error_details(
        self, node_major_version, error_message
    ):
        """验证安装失败时包含错误详情
        
        对于任何导致安装失败的情况，报告应该包含 FAILED 状态和错误信息。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        node_version = f"v{node_major_version}.0.0"
        
        # Mock 未安装状态
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                if cmd == "copilot":
                    return None  # 未安装
                elif cmd == "node":
                    return "/usr/local/bin/node"
                return None
            
            mock_which.side_effect = which_side_effect
            
            with patch.object(
                installer,
                'run_command',
                return_value=(0, node_version, "")
            ):
                report = installer.install()
                
                # 验证返回失败
                assert report.result == InstallResult.FAILED, \
                    f"Node.js 版本过低时应该返回 FAILED，实际返回: {report.result}"
                
                # 验证包含错误信息
                assert report.error is not None, \
                    "失败的安装报告应该包含错误信息"
                assert len(report.error) > 0, \
                    "错误信息不应该为空"

    @given(
        returncode=st.integers(min_value=1, max_value=255),
        stderr_message=st.text(min_size=1, max_size=100)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_install_command_failure_includes_error(
        self, returncode, stderr_message
    ):
        """验证安装命令失败时包含错误信息
        
        对于任何非零返回码，报告应该包含 FAILED 状态和 stderr 信息。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock 未安装状态
        with patch('shutil.which') as mock_which:
            call_count = [0]
            
            def which_side_effect(cmd):
                if cmd == "copilot":
                    return None  # 未安装
                elif cmd == "node":
                    return "/usr/local/bin/node"
                return None
            
            mock_which.side_effect = which_side_effect
            
            with patch.object(
                installer,
                'run_command'
            ) as mock_run_command:
                def run_command_side_effect(cmd, **kwargs):
                    if "node --version" in cmd:
                        return (0, "v22.0.0", "")
                    elif "npm install" in cmd:
                        # 安装命令失败
                        return (returncode, "", stderr_message)
                    return (0, "", "")
                
                mock_run_command.side_effect = run_command_side_effect
                
                report = installer.install()
                
                # 验证返回失败
                assert report.result == InstallResult.FAILED, \
                    f"安装命令失败时应该返回 FAILED，实际返回: {report.result}"
                
                # 验证包含错误信息
                assert report.error is not None, \
                    "失败的安装报告应该包含错误信息"
                # 错误信息应该包含 stderr 或说明失败
                assert stderr_message in report.error or "失败" in report.message, \
                    f"错误信息应该包含 stderr 或失败说明，实际错误: {report.error}, 消息: {report.message}"

    @given(
        returncode=st.integers(min_value=1, max_value=255),
        stderr_message=st.text(min_size=1, max_size=100)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_upgrade_command_failure_includes_error(
        self, returncode, stderr_message
    ):
        """验证升级命令失败时包含错误信息
        
        对于任何非零返回码，报告应该包含 FAILED 状态和 stderr 信息。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock 已安装状态
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command'
            ) as mock_run_command:
                def run_command_side_effect(cmd, **kwargs):
                    if "copilot --version" in cmd:
                        return (0, "1.0.0", "")
                    elif "npm update" in cmd:
                        # 升级命令失败
                        return (returncode, "", stderr_message)
                    return (0, "", "")
                
                mock_run_command.side_effect = run_command_side_effect
                
                report = installer.upgrade()
                
                # 验证返回失败
                assert report.result == InstallResult.FAILED, \
                    f"升级命令失败时应该返回 FAILED，实际返回: {report.result}"
                
                # 验证包含错误信息
                assert report.error is not None, \
                    "失败的升级报告应该包含错误信息"
                # 错误信息应该包含 stderr 或说明失败
                assert stderr_message in report.error or "失败" in report.message, \
                    f"错误信息应该包含 stderr 或失败说明，实际错误: {report.error}, 消息: {report.message}"

    @given(exception_message=st.text(min_size=1, max_size=100))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_install_exception_includes_error(self, exception_message):
        """验证安装过程中的异常被捕获并包含在错误信息中
        
        对于任何异常，报告应该包含 FAILED 状态和异常信息。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock 未安装状态
        with patch('shutil.which') as mock_which:
            def which_side_effect(cmd):
                if cmd == "copilot":
                    return None  # 未安装
                elif cmd == "node":
                    # 抛出异常
                    raise Exception(exception_message)
                return None
            
            mock_which.side_effect = which_side_effect
            
            report = installer.install()
            
            # 验证返回失败
            assert report.result == InstallResult.FAILED, \
                f"发生异常时应该返回 FAILED，实际返回: {report.result}"
            
            # 验证包含错误信息
            assert report.error is not None, \
                "异常情况下的报告应该包含错误信息"
            # 错误信息应该包含异常消息
            assert exception_message in report.error, \
                f"错误信息应该包含异常消息 '{exception_message}'，实际错误: {report.error}"

    @given(exception_message=st.text(min_size=1, max_size=100))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_upgrade_exception_includes_error(self, exception_message):
        """验证升级过程中的异常被捕获并包含在错误信息中
        
        对于任何异常，报告应该包含 FAILED 状态和异常信息。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock 已安装状态，但在升级时抛出异常
        with patch('shutil.which', return_value="/usr/local/bin/copilot"):
            with patch.object(
                installer,
                'run_command'
            ) as mock_run_command:
                def run_command_side_effect(cmd, **kwargs):
                    if "copilot --version" in cmd:
                        return (0, "1.0.0", "")
                    elif "npm update" in cmd:
                        # 抛出异常
                        raise Exception(exception_message)
                    return (0, "", "")
                
                mock_run_command.side_effect = run_command_side_effect
                
                report = installer.upgrade()
                
                # 验证返回失败
                assert report.result == InstallResult.FAILED, \
                    f"发生异常时应该返回 FAILED，实际返回: {report.result}"
                
                # 验证包含错误信息
                assert report.error is not None, \
                    "异常情况下的报告应该包含错误信息"
                # 错误信息应该包含异常消息
                assert exception_message in report.error, \
                    f"错误信息应该包含异常消息 '{exception_message}'，实际错误: {report.error}"

    def test_upgrade_not_installed_includes_error(self):
        """验证未安装时升级失败并包含错误信息
        
        当工具未安装时，upgrade() 应该返回 FAILED 状态和错误信息。
        """
        platform_info_macos = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info_macos, tool_config)
        
        # Mock 未安装状态
        with patch('shutil.which', return_value=None):
            report = installer.upgrade()
            
            # 验证返回失败
            assert report.result == InstallResult.FAILED, \
                f"未安装时升级应该返回 FAILED，实际返回: {report.result}"
            
            # 验证包含错误信息
            assert report.error is not None, \
                "未安装时升级应该包含错误信息"
            assert len(report.error) > 0, \
                "错误信息不应该为空"
            # 错误信息应该说明需要先安装
            assert "未安装" in report.error or "先安装" in report.error, \
                f"错误信息应该说明需要先安装，实际错误: {report.error}"
    
    @given(
        platform_os=st.sampled_from(["Windows", "FreeBSD", "Unknown"])
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_unsupported_platform_includes_error(self, platform_os):
        """验证不支持的平台返回错误信息
        
        对于任何不支持的平台，install() 和 upgrade() 应该返回 FAILED 状态和错误信息。
        """
        # 创建不支持的平台信息
        # 注意：由于 OS 是枚举类型，我们需要使用 mock 来模拟不支持的平台
        platform_info = create_platform_info_macos()
        tool_config = create_tool_config()
        installer = CopilotCLIInstaller(platform_info, tool_config)
        
        # Mock platform_info.os 为不支持的值
        # 由于 OS 是枚举，我们使用 UNSUPPORTED 来模拟不支持的平台
        from mono_kickstart.platform_detector import OS
        
        with patch.object(platform_info, 'os', OS.UNSUPPORTED):
            # 测试 install()
            install_report = installer.install()
            
            # 验证返回失败
            assert install_report.result == InstallResult.FAILED, \
                f"不支持的平台应该返回 FAILED，实际返回: {install_report.result}"
            
            # 验证包含错误信息
            assert install_report.error is not None, \
                "不支持的平台应该包含错误信息"
            assert "支持" in install_report.error or "macOS" in install_report.error or "Linux" in install_report.error, \
                f"错误信息应该说明平台限制，实际错误: {install_report.error}"
            
            # 测试 upgrade()
            upgrade_report = installer.upgrade()
            
            # 验证返回失败
            assert upgrade_report.result == InstallResult.FAILED, \
                f"不支持的平台应该返回 FAILED，实际返回: {upgrade_report.result}"
            
            # 验证包含错误信息
            assert upgrade_report.error is not None, \
                "不支持的平台应该包含错误信息"
            assert "支持" in upgrade_report.error or "macOS" in upgrade_report.error or "Linux" in upgrade_report.error, \
                f"错误信息应该说明平台限制，实际错误: {upgrade_report.error}"
