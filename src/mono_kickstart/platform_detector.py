"""
平台检测器模块

检测操作系统、架构和 Shell 类型，提供平台信息用于工具安装。
"""

import os
import platform
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class OS(Enum):
    """操作系统类型"""
    MACOS = "macos"
    LINUX = "linux"
    UNSUPPORTED = "unsupported"


class Arch(Enum):
    """CPU 架构类型"""
    ARM64 = "arm64"
    X86_64 = "x86_64"
    UNSUPPORTED = "unsupported"


class Shell(Enum):
    """Shell 类型"""
    BASH = "bash"
    ZSH = "zsh"
    FISH = "fish"
    UNKNOWN = "unknown"


@dataclass
class PlatformInfo:
    """平台信息"""
    os: OS
    arch: Arch
    shell: Shell
    shell_config_file: str


class PlatformDetector:
    """平台检测器"""

    def detect_os(self) -> OS:
        """
        检测操作系统
        
        Returns:
            OS: 操作系统类型（macOS、Linux 或不支持）
        """
        system = platform.system().lower()
        
        if system == "darwin":
            return OS.MACOS
        elif system == "linux":
            return OS.LINUX
        else:
            return OS.UNSUPPORTED

    def detect_arch(self) -> Arch:
        """
        检测 CPU 架构
        
        Returns:
            Arch: CPU 架构类型（ARM64、x86_64 或不支持）
        """
        machine = platform.machine().lower()
        
        # ARM64 的各种表示方式
        if machine in ("arm64", "aarch64"):
            return Arch.ARM64
        # x86_64 的各种表示方式
        elif machine in ("x86_64", "amd64"):
            return Arch.X86_64
        else:
            return Arch.UNSUPPORTED

    def detect_shell(self) -> Shell:
        """
        检测当前 Shell 类型
        
        通过检查 SHELL 环境变量来确定当前使用的 Shell。
        
        Returns:
            Shell: Shell 类型（Bash、Zsh、Fish 或未知）
        """
        shell_path = os.environ.get("SHELL", "")
        shell_name = Path(shell_path).name.lower()
        
        if shell_name == "bash":
            return Shell.BASH
        elif shell_name == "zsh":
            return Shell.ZSH
        elif shell_name == "fish":
            return Shell.FISH
        else:
            return Shell.UNKNOWN

    def get_shell_config_file(self, shell: Shell) -> str:
        """
        获取 Shell 配置文件路径
        
        Args:
            shell: Shell 类型
            
        Returns:
            str: Shell 配置文件的完整路径
        """
        home = Path.home()
        
        if shell == Shell.BASH:
            # 优先使用 .bashrc，如果不存在则使用 .bash_profile
            bashrc = home / ".bashrc"
            bash_profile = home / ".bash_profile"
            if bashrc.exists():
                return str(bashrc)
            else:
                return str(bash_profile)
        elif shell == Shell.ZSH:
            return str(home / ".zshrc")
        elif shell == Shell.FISH:
            return str(home / ".config" / "fish" / "config.fish")
        else:
            # 对于未知 Shell，返回 .profile 作为后备
            return str(home / ".profile")

    def detect_all(self) -> PlatformInfo:
        """
        检测所有平台信息
        
        Returns:
            PlatformInfo: 包含操作系统、架构、Shell 类型和配置文件路径的完整平台信息
        """
        detected_os = self.detect_os()
        detected_arch = self.detect_arch()
        detected_shell = self.detect_shell()
        shell_config = self.get_shell_config_file(detected_shell)
        
        return PlatformInfo(
            os=detected_os,
            arch=detected_arch,
            shell=detected_shell,
            shell_config_file=shell_config,
        )

    def is_supported(self) -> bool:
        """
        检查当前平台是否支持
        
        支持的平台组合：
        - macOS ARM64
        - macOS x86_64
        - Linux x86_64
        
        Returns:
            bool: 如果平台支持返回 True，否则返回 False
        """
        detected_os = self.detect_os()
        detected_arch = self.detect_arch()
        
        # 检查是否为不支持的操作系统或架构
        if detected_os == OS.UNSUPPORTED or detected_arch == Arch.UNSUPPORTED:
            return False
        
        # 支持的平台组合
        supported_combinations = [
            (OS.MACOS, Arch.ARM64),
            (OS.MACOS, Arch.X86_64),
            (OS.LINUX, Arch.X86_64),
        ]
        
        return (detected_os, detected_arch) in supported_combinations
