"""错误处理模块单元测试"""

import pytest
from unittest.mock import MagicMock

from mono_kickstart.errors import (
    ExitCode,
    MonoKickstartError,
    PlatformNotSupportedError,
    PythonVersionError,
    ConfigError,
    ToolInstallError,
    NetworkError,
    PermissionError,
    DependencyError,
    format_error_message,
    handle_error
)


class TestExitCode:
    """退出码测试"""
    
    def test_exit_code_values(self):
        """测试退出码值"""
        assert ExitCode.SUCCESS.value == 0
        assert ExitCode.GENERAL_ERROR.value == 1
        assert ExitCode.CONFIG_ERROR.value == 2
        assert ExitCode.ALL_TASKS_FAILED.value == 3
        assert ExitCode.PERMISSION_ERROR.value == 4
        assert ExitCode.DEPENDENCY_ERROR.value == 5
        assert ExitCode.USER_INTERRUPT.value == 130


class TestMonoKickstartError:
    """基础异常类测试"""
    
    def test_init_with_message_only(self):
        """测试仅使用消息初始化"""
        error = MonoKickstartError("Test error")
        
        assert error.message == "Test error"
        assert error.exit_code == ExitCode.GENERAL_ERROR
        assert error.recovery_suggestions == []
    
    def test_init_with_all_parameters(self):
        """测试使用所有参数初始化"""
        suggestions = ["Suggestion 1", "Suggestion 2"]
        error = MonoKickstartError(
            message="Test error",
            exit_code=ExitCode.CONFIG_ERROR,
            recovery_suggestions=suggestions
        )
        
        assert error.message == "Test error"
        assert error.exit_code == ExitCode.CONFIG_ERROR
        assert error.recovery_suggestions == suggestions
    
    def test_str_representation(self):
        """测试字符串表示"""
        error = MonoKickstartError("Test error")
        
        assert str(error) == "Test error"


class TestPlatformNotSupportedError:
    """平台不支持错误测试"""
    
    def test_init(self):
        """测试初始化"""
        error = PlatformNotSupportedError(os="windows", arch="x86_64")
        
        assert "windows" in error.message
        assert "x86_64" in error.message
        assert error.os == "windows"
        assert error.arch == "x86_64"
        assert error.exit_code == ExitCode.GENERAL_ERROR
    
    def test_recovery_suggestions(self):
        """测试恢复建议"""
        error = PlatformNotSupportedError(os="windows", arch="x86_64")
        
        assert len(error.recovery_suggestions) > 0
        assert any("macOS" in s for s in error.recovery_suggestions)
        assert any("Linux" in s for s in error.recovery_suggestions)


class TestPythonVersionError:
    """Python 版本错误测试"""
    
    def test_init_with_default_required_version(self):
        """测试使用默认要求版本初始化"""
        error = PythonVersionError(current_version="3.9.0")
        
        assert "3.9.0" in error.message
        assert "3.11" in error.message
        assert error.current_version == "3.9.0"
        assert error.required_version == "3.11"
    
    def test_init_with_custom_required_version(self):
        """测试使用自定义要求版本初始化"""
        error = PythonVersionError(
            current_version="3.9.0",
            required_version="3.12"
        )
        
        assert "3.9.0" in error.message
        assert "3.12" in error.message
        assert error.required_version == "3.12"
    
    def test_recovery_suggestions(self):
        """测试恢复建议"""
        error = PythonVersionError(current_version="3.9.0")
        
        assert len(error.recovery_suggestions) > 0
        assert any("pyenv" in s for s in error.recovery_suggestions)
        assert any("Conda" in s for s in error.recovery_suggestions)


class TestConfigError:
    """配置错误测试"""
    
    def test_init_without_config_file(self):
        """测试不指定配置文件初始化"""
        error = ConfigError(message="Invalid format")
        
        assert "Invalid format" in error.message
        assert error.config_file is None
        assert error.exit_code == ExitCode.CONFIG_ERROR
    
    def test_init_with_config_file(self):
        """测试指定配置文件初始化"""
        error = ConfigError(
            message="Invalid format",
            config_file=".kickstartrc"
        )
        
        assert "Invalid format" in error.message
        assert ".kickstartrc" in error.message
        assert error.config_file == ".kickstartrc"
    
    def test_recovery_suggestions(self):
        """测试恢复建议"""
        error = ConfigError(message="Invalid format")
        
        assert len(error.recovery_suggestions) > 0
        assert any("YAML" in s for s in error.recovery_suggestions)


class TestToolInstallError:
    """工具安装错误测试"""
    
    def test_init_without_manual_guide(self):
        """测试不提供手动安装指引初始化"""
        error = ToolInstallError(
            tool_name="nvm",
            reason="Network timeout"
        )
        
        assert "nvm" in error.message
        assert "Network timeout" in error.message
        assert error.tool_name == "nvm"
        assert error.reason == "Network timeout"
    
    def test_init_with_manual_guide(self):
        """测试提供手动安装指引初始化"""
        error = ToolInstallError(
            tool_name="nvm",
            reason="Network timeout",
            manual_install_guide="https://github.com/nvm-sh/nvm#install"
        )
        
        assert len(error.recovery_suggestions) > 0
        assert any("https://github.com/nvm-sh/nvm#install" in s 
                  for s in error.recovery_suggestions)
    
    def test_recovery_suggestions(self):
        """测试恢复建议"""
        error = ToolInstallError(tool_name="nvm", reason="Network timeout")
        
        assert len(error.recovery_suggestions) > 0
        assert any("网络" in s for s in error.recovery_suggestions)


class TestNetworkError:
    """网络错误测试"""
    
    def test_init(self):
        """测试初始化"""
        error = NetworkError(
            url="https://example.com/file.tar.gz",
            reason="Connection timeout"
        )
        
        assert "https://example.com/file.tar.gz" in error.message
        assert "Connection timeout" in error.message
        assert error.url == "https://example.com/file.tar.gz"
        assert error.reason == "Connection timeout"
    
    def test_recovery_suggestions(self):
        """测试恢复建议"""
        error = NetworkError(url="https://example.com", reason="Timeout")
        
        assert len(error.recovery_suggestions) > 0
        assert any("网络" in s for s in error.recovery_suggestions)
        assert any("镜像" in s for s in error.recovery_suggestions)


class TestPermissionError:
    """权限错误测试"""
    
    def test_init(self):
        """测试初始化"""
        error = PermissionError(
            path="/usr/local/bin/tool",
            operation="写入"
        )
        
        assert "/usr/local/bin/tool" in error.message
        assert "写入" in error.message
        assert error.path == "/usr/local/bin/tool"
        assert error.operation == "写入"
        assert error.exit_code == ExitCode.PERMISSION_ERROR
    
    def test_recovery_suggestions(self):
        """测试恢复建议"""
        error = PermissionError(path="/usr/local/bin", operation="写入")
        
        assert len(error.recovery_suggestions) > 0
        assert any("权限" in s for s in error.recovery_suggestions)


class TestDependencyError:
    """依赖错误测试"""
    
    def test_init_without_install_command(self):
        """测试不提供安装命令初始化"""
        error = DependencyError(
            dependency="git",
            required_by="nvm"
        )
        
        assert "git" in error.message
        assert "nvm" in error.message
        assert error.dependency == "git"
        assert error.required_by == "nvm"
        assert error.exit_code == ExitCode.DEPENDENCY_ERROR
    
    def test_init_with_install_command(self):
        """测试提供安装命令初始化"""
        error = DependencyError(
            dependency="git",
            required_by="nvm",
            install_command="apt-get install git"
        )
        
        assert len(error.recovery_suggestions) > 0
        assert any("apt-get install git" in s for s in error.recovery_suggestions)
    
    def test_recovery_suggestions(self):
        """测试恢复建议"""
        error = DependencyError(dependency="git", required_by="nvm")
        
        assert len(error.recovery_suggestions) > 0


class TestFormatErrorMessage:
    """格式化错误消息测试"""
    
    def test_format_error_with_suggestions(self):
        """测试格式化带建议的错误"""
        error = MonoKickstartError(
            message="Test error",
            recovery_suggestions=["Suggestion 1", "Suggestion 2"]
        )
        
        formatted = format_error_message(error)
        
        assert "Test error" in formatted
        assert "恢复建议" in formatted
        assert "Suggestion 1" in formatted
        assert "Suggestion 2" in formatted
    
    def test_format_error_without_suggestions(self):
        """测试格式化无建议的错误"""
        error = MonoKickstartError(message="Test error")
        
        formatted = format_error_message(error)
        
        assert "Test error" in formatted
        assert "恢复建议" not in formatted


class TestHandleError:
    """错误处理测试"""
    
    def test_handle_mono_kickstart_error(self):
        """测试处理自定义错误"""
        logger = MagicMock()
        error = MonoKickstartError(
            message="Test error",
            exit_code=ExitCode.CONFIG_ERROR
        )
        
        exit_code = handle_error(error, logger)
        
        assert exit_code == ExitCode.CONFIG_ERROR.value
        logger.error.assert_called_once()
    
    def test_handle_keyboard_interrupt(self):
        """测试处理用户中断"""
        logger = MagicMock()
        error = KeyboardInterrupt()
        
        exit_code = handle_error(error, logger)
        
        assert exit_code == ExitCode.USER_INTERRUPT.value
        logger.error.assert_called_once()
        assert "中断" in logger.error.call_args[0][0]
    
    def test_handle_unknown_error(self):
        """测试处理未知错误"""
        logger = MagicMock()
        error = ValueError("Unknown error")
        
        exit_code = handle_error(error, logger)
        
        assert exit_code == ExitCode.GENERAL_ERROR.value
        logger.error.assert_called()
        logger.debug.assert_called_once()
    
    def test_handle_error_calls_logger_methods(self):
        """测试错误处理调用日志方法"""
        logger = MagicMock()
        error = MonoKickstartError(
            message="Test error",
            recovery_suggestions=["Suggestion"]
        )
        
        handle_error(error, logger)
        
        # 验证 logger.error 被调用
        logger.error.assert_called_once()
        
        # 验证错误消息包含建议
        error_message = logger.error.call_args[0][0]
        assert "Test error" in error_message
        assert "Suggestion" in error_message
