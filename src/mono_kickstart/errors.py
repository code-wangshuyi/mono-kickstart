"""错误处理模块

定义自定义异常类和错误恢复建议。
"""

from typing import Optional, List
from enum import Enum


class ExitCode(Enum):
    """退出码枚举"""
    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    ALL_TASKS_FAILED = 3
    PERMISSION_ERROR = 4
    DEPENDENCY_ERROR = 5
    USER_INTERRUPT = 130


class MonoKickstartError(Exception):
    """Mono-Kickstart 基础异常类"""
    
    def __init__(
        self,
        message: str,
        exit_code: ExitCode = ExitCode.GENERAL_ERROR,
        recovery_suggestions: Optional[List[str]] = None
    ):
        """初始化异常
        
        Args:
            message: 错误消息
            exit_code: 退出码
            recovery_suggestions: 恢复建议列表
        """
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.recovery_suggestions = recovery_suggestions or []


class PlatformNotSupportedError(MonoKickstartError):
    """平台不支持错误"""
    
    def __init__(self, os: str, arch: str):
        """初始化平台不支持错误
        
        Args:
            os: 操作系统
            arch: 架构
        """
        message = f"不支持的平台: {os}/{arch}"
        recovery_suggestions = [
            "支持的平台:",
            "  - macOS ARM64",
            "  - macOS x86_64",
            "  - Linux x86_64",
            "请在支持的平台上运行此工具。"
        ]
        super().__init__(
            message=message,
            exit_code=ExitCode.GENERAL_ERROR,
            recovery_suggestions=recovery_suggestions
        )
        self.os = os
        self.arch = arch


class PythonVersionError(MonoKickstartError):
    """Python 版本不满足错误"""
    
    def __init__(self, current_version: str, required_version: str = "3.11"):
        """初始化 Python 版本错误
        
        Args:
            current_version: 当前 Python 版本
            required_version: 要求的 Python 版本
        """
        message = f"Python 版本不满足要求: 当前 {current_version}, 需要 {required_version}+"
        recovery_suggestions = [
            f"请升级 Python 到 {required_version} 或更高版本。",
            "推荐使用以下方式安装 Python:",
            "  - 使用 pyenv: pyenv install 3.11",
            "  - 使用 Conda: conda install python=3.11",
            "  - 从官网下载: https://www.python.org/downloads/"
        ]
        super().__init__(
            message=message,
            exit_code=ExitCode.GENERAL_ERROR,
            recovery_suggestions=recovery_suggestions
        )
        self.current_version = current_version
        self.required_version = required_version


class ConfigError(MonoKickstartError):
    """配置错误"""
    
    def __init__(self, message: str, config_file: Optional[str] = None):
        """初始化配置错误
        
        Args:
            message: 错误消息
            config_file: 配置文件路径
        """
        full_message = f"配置错误: {message}"
        if config_file:
            full_message += f" (文件: {config_file})"
        
        recovery_suggestions = [
            "请检查配置文件格式是否正确。",
            "配置文件应为有效的 YAML 格式。",
            "参考文档: https://github.com/mono-kickstart/mono-kickstart#configuration"
        ]
        
        super().__init__(
            message=full_message,
            exit_code=ExitCode.CONFIG_ERROR,
            recovery_suggestions=recovery_suggestions
        )
        self.config_file = config_file


class ToolInstallError(MonoKickstartError):
    """工具安装错误"""
    
    def __init__(
        self,
        tool_name: str,
        reason: str,
        manual_install_guide: Optional[str] = None
    ):
        """初始化工具安装错误
        
        Args:
            tool_name: 工具名称
            reason: 失败原因
            manual_install_guide: 手动安装指引
        """
        message = f"工具 '{tool_name}' 安装失败: {reason}"
        
        recovery_suggestions = []
        if manual_install_guide:
            recovery_suggestions.append(f"手动安装指引: {manual_install_guide}")
        
        recovery_suggestions.extend([
            "您可以尝试:",
            "  1. 检查网络连接",
            "  2. 重新运行安装命令",
            "  3. 手动安装该工具",
            "  4. 跳过该工具继续安装其他工具"
        ])
        
        super().__init__(
            message=message,
            exit_code=ExitCode.GENERAL_ERROR,
            recovery_suggestions=recovery_suggestions
        )
        self.tool_name = tool_name
        self.reason = reason


class NetworkError(MonoKickstartError):
    """网络错误"""
    
    def __init__(self, url: str, reason: str):
        """初始化网络错误
        
        Args:
            url: 请求的 URL
            reason: 失败原因
        """
        message = f"网络请求失败: {url} - {reason}"
        recovery_suggestions = [
            "请检查网络连接。",
            "如果在中国大陆，建议使用 --interactive 模式配置镜像源。",
            "您也可以稍后重试。"
        ]
        
        super().__init__(
            message=message,
            exit_code=ExitCode.GENERAL_ERROR,
            recovery_suggestions=recovery_suggestions
        )
        self.url = url
        self.reason = reason


class PermissionError(MonoKickstartError):
    """权限错误"""
    
    def __init__(self, path: str, operation: str):
        """初始化权限错误
        
        Args:
            path: 文件或目录路径
            operation: 操作类型（读、写、执行等）
        """
        message = f"权限不足: 无法{operation} {path}"
        recovery_suggestions = [
            "请检查文件或目录的权限。",
            "您可能需要使用 sudo 运行命令（不推荐）。",
            "或者更改文件/目录的所有者或权限。"
        ]
        
        super().__init__(
            message=message,
            exit_code=ExitCode.PERMISSION_ERROR,
            recovery_suggestions=recovery_suggestions
        )
        self.path = path
        self.operation = operation


class DependencyError(MonoKickstartError):
    """依赖缺失错误"""
    
    def __init__(self, dependency: str, required_by: str, install_command: Optional[str] = None):
        """初始化依赖错误
        
        Args:
            dependency: 缺失的依赖
            required_by: 需要该依赖的工具
            install_command: 安装命令
        """
        message = f"缺少依赖: {dependency} (被 {required_by} 需要)"
        
        recovery_suggestions = []
        if install_command:
            recovery_suggestions.append(f"安装命令: {install_command}")
        
        recovery_suggestions.extend([
            f"请先安装 {dependency}，然后重新运行。",
            "或者跳过 {required_by} 的安装。"
        ])
        
        super().__init__(
            message=message,
            exit_code=ExitCode.DEPENDENCY_ERROR,
            recovery_suggestions=recovery_suggestions
        )
        self.dependency = dependency
        self.required_by = required_by


def format_error_message(error: MonoKickstartError) -> str:
    """格式化错误消息
    
    Args:
        error: 错误对象
        
    Returns:
        格式化后的错误消息
    """
    lines = [
        f"❌ 错误: {error.message}",
        ""
    ]
    
    if error.recovery_suggestions:
        lines.append("💡 恢复建议:")
        for suggestion in error.recovery_suggestions:
            lines.append(f"   {suggestion}")
        lines.append("")
    
    return "\n".join(lines)


def handle_error(error: Exception, logger) -> int:
    """统一错误处理
    
    Args:
        error: 异常对象
        logger: 日志记录器
        
    Returns:
        退出码
    """
    if isinstance(error, MonoKickstartError):
        # 自定义错误
        logger.error(format_error_message(error))
        return error.exit_code.value
    elif isinstance(error, KeyboardInterrupt):
        # 用户中断
        logger.error("\n❌ 用户中断操作")
        return ExitCode.USER_INTERRUPT.value
    else:
        # 未知错误
        logger.error(f"❌ 发生未知错误: {error}")
        logger.debug("详细错误信息:", exc_info=True)
        return ExitCode.GENERAL_ERROR.value
