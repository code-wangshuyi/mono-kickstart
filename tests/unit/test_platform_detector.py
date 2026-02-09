"""
平台检测器单元测试

测试平台检测器的各种场景，包括：
- OS 检测（macOS、Linux、不支持）
- 架构检测（ARM64、x86_64、不支持）
- Shell 检测（Bash、Zsh、Fish、未知）
- Shell 配置文件路径获取
- 平台支持性检查
"""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mono_kickstart.platform_detector import (
    OS,
    Arch,
    Shell,
    PlatformInfo,
    PlatformDetector,
)


class TestOSDetection:
    """测试操作系统检测"""

    def test_detect_macos(self):
        """测试 macOS 检测"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="Darwin"):
            assert detector.detect_os() == OS.MACOS

    def test_detect_linux(self):
        """测试 Linux 检测"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="Linux"):
            assert detector.detect_os() == OS.LINUX

    def test_detect_unsupported_os(self):
        """测试不支持的操作系统"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="Windows"):
            assert detector.detect_os() == OS.UNSUPPORTED

    def test_detect_os_case_insensitive(self):
        """测试 OS 检测的大小写不敏感性"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="DARWIN"):
            assert detector.detect_os() == OS.MACOS
        with patch("platform.system", return_value="linux"):
            assert detector.detect_os() == OS.LINUX


class TestArchDetection:
    """测试 CPU 架构检测"""

    def test_detect_arm64(self):
        """测试 ARM64 架构检测"""
        detector = PlatformDetector()
        with patch("platform.machine", return_value="arm64"):
            assert detector.detect_arch() == Arch.ARM64

    def test_detect_aarch64(self):
        """测试 aarch64 架构检测（ARM64 的另一种表示）"""
        detector = PlatformDetector()
        with patch("platform.machine", return_value="aarch64"):
            assert detector.detect_arch() == Arch.ARM64

    def test_detect_x86_64(self):
        """测试 x86_64 架构检测"""
        detector = PlatformDetector()
        with patch("platform.machine", return_value="x86_64"):
            assert detector.detect_arch() == Arch.X86_64

    def test_detect_amd64(self):
        """测试 amd64 架构检测（x86_64 的另一种表示）"""
        detector = PlatformDetector()
        with patch("platform.machine", return_value="amd64"):
            assert detector.detect_arch() == Arch.X86_64

    def test_detect_unsupported_arch(self):
        """测试不支持的架构"""
        detector = PlatformDetector()
        with patch("platform.machine", return_value="i386"):
            assert detector.detect_arch() == Arch.UNSUPPORTED

    def test_detect_arch_case_insensitive(self):
        """测试架构检测的大小写不敏感性"""
        detector = PlatformDetector()
        with patch("platform.machine", return_value="ARM64"):
            assert detector.detect_arch() == Arch.ARM64
        with patch("platform.machine", return_value="X86_64"):
            assert detector.detect_arch() == Arch.X86_64


class TestShellDetection:
    """测试 Shell 类型检测"""

    def test_detect_bash(self):
        """测试 Bash 检测"""
        detector = PlatformDetector()
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            assert detector.detect_shell() == Shell.BASH

    def test_detect_zsh(self):
        """测试 Zsh 检测"""
        detector = PlatformDetector()
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            assert detector.detect_shell() == Shell.ZSH

    def test_detect_fish(self):
        """测试 Fish 检测"""
        detector = PlatformDetector()
        with patch.dict(os.environ, {"SHELL": "/usr/bin/fish"}):
            assert detector.detect_shell() == Shell.FISH

    def test_detect_unknown_shell(self):
        """测试未知 Shell"""
        detector = PlatformDetector()
        with patch.dict(os.environ, {"SHELL": "/bin/ksh"}):
            assert detector.detect_shell() == Shell.UNKNOWN

    def test_detect_shell_no_env_var(self):
        """测试 SHELL 环境变量不存在的情况"""
        detector = PlatformDetector()
        with patch.dict(os.environ, {}, clear=True):
            assert detector.detect_shell() == Shell.UNKNOWN

    def test_detect_shell_case_insensitive(self):
        """测试 Shell 检测的大小写不敏感性"""
        detector = PlatformDetector()
        with patch.dict(os.environ, {"SHELL": "/bin/BASH"}):
            assert detector.detect_shell() == Shell.BASH


class TestShellConfigFile:
    """测试 Shell 配置文件路径获取"""

    def test_bash_config_file_bashrc_exists(self, tmp_path):
        """测试 Bash 配置文件（.bashrc 存在）"""
        detector = PlatformDetector()
        bashrc = tmp_path / ".bashrc"
        bashrc.touch()
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            config_file = detector.get_shell_config_file(Shell.BASH)
            assert config_file == str(bashrc)

    def test_bash_config_file_bashrc_not_exists(self, tmp_path):
        """测试 Bash 配置文件（.bashrc 不存在，使用 .bash_profile）"""
        detector = PlatformDetector()
        bash_profile = tmp_path / ".bash_profile"
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            config_file = detector.get_shell_config_file(Shell.BASH)
            assert config_file == str(bash_profile)

    def test_zsh_config_file(self, tmp_path):
        """测试 Zsh 配置文件"""
        detector = PlatformDetector()
        zshrc = tmp_path / ".zshrc"
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            config_file = detector.get_shell_config_file(Shell.ZSH)
            assert config_file == str(zshrc)

    def test_fish_config_file(self, tmp_path):
        """测试 Fish 配置文件"""
        detector = PlatformDetector()
        fish_config = tmp_path / ".config" / "fish" / "config.fish"
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            config_file = detector.get_shell_config_file(Shell.FISH)
            assert config_file == str(fish_config)

    def test_unknown_shell_config_file(self, tmp_path):
        """测试未知 Shell 的配置文件（使用 .profile 作为后备）"""
        detector = PlatformDetector()
        profile = tmp_path / ".profile"
        
        with patch("pathlib.Path.home", return_value=tmp_path):
            config_file = detector.get_shell_config_file(Shell.UNKNOWN)
            assert config_file == str(profile)


class TestDetectAll:
    """测试完整平台信息检测"""

    def test_detect_all_macos_arm64_zsh(self, tmp_path):
        """测试 macOS ARM64 + Zsh 的完整检测"""
        detector = PlatformDetector()
        zshrc = tmp_path / ".zshrc"
        
        with patch("platform.system", return_value="Darwin"), \
             patch("platform.machine", return_value="arm64"), \
             patch.dict(os.environ, {"SHELL": "/bin/zsh"}), \
             patch("pathlib.Path.home", return_value=tmp_path):
            
            info = detector.detect_all()
            
            assert info.os == OS.MACOS
            assert info.arch == Arch.ARM64
            assert info.shell == Shell.ZSH
            assert info.shell_config_file == str(zshrc)

    def test_detect_all_linux_x86_64_bash(self, tmp_path):
        """测试 Linux x86_64 + Bash 的完整检测"""
        detector = PlatformDetector()
        bashrc = tmp_path / ".bashrc"
        bashrc.touch()
        
        with patch("platform.system", return_value="Linux"), \
             patch("platform.machine", return_value="x86_64"), \
             patch.dict(os.environ, {"SHELL": "/bin/bash"}), \
             patch("pathlib.Path.home", return_value=tmp_path):
            
            info = detector.detect_all()
            
            assert info.os == OS.LINUX
            assert info.arch == Arch.X86_64
            assert info.shell == Shell.BASH
            assert info.shell_config_file == str(bashrc)

    def test_detect_all_unsupported_platform(self, tmp_path):
        """测试不支持的平台的完整检测"""
        detector = PlatformDetector()
        
        with patch("platform.system", return_value="Windows"), \
             patch("platform.machine", return_value="x86_64"), \
             patch.dict(os.environ, {"SHELL": "/bin/bash"}), \
             patch("pathlib.Path.home", return_value=tmp_path):
            
            info = detector.detect_all()
            
            assert info.os == OS.UNSUPPORTED
            assert info.arch == Arch.X86_64
            assert info.shell == Shell.BASH


class TestPlatformSupport:
    """测试平台支持性检查"""

    def test_macos_arm64_supported(self):
        """测试 macOS ARM64 是支持的平台"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="Darwin"), \
             patch("platform.machine", return_value="arm64"):
            assert detector.is_supported() is True

    def test_macos_x86_64_supported(self):
        """测试 macOS x86_64 是支持的平台"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="Darwin"), \
             patch("platform.machine", return_value="x86_64"):
            assert detector.is_supported() is True

    def test_linux_x86_64_supported(self):
        """测试 Linux x86_64 是支持的平台"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="Linux"), \
             patch("platform.machine", return_value="x86_64"):
            assert detector.is_supported() is True

    def test_linux_arm64_not_supported(self):
        """测试 Linux ARM64 不是支持的平台"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="Linux"), \
             patch("platform.machine", return_value="arm64"):
            assert detector.is_supported() is False

    def test_windows_not_supported(self):
        """测试 Windows 不是支持的平台"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="Windows"), \
             patch("platform.machine", return_value="x86_64"):
            assert detector.is_supported() is False

    def test_unsupported_arch_not_supported(self):
        """测试不支持的架构"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="Darwin"), \
             patch("platform.machine", return_value="i386"):
            assert detector.is_supported() is False

    def test_unsupported_os_not_supported(self):
        """测试不支持的操作系统"""
        detector = PlatformDetector()
        with patch("platform.system", return_value="FreeBSD"), \
             patch("platform.machine", return_value="x86_64"):
            assert detector.is_supported() is False


class TestPlatformInfoDataclass:
    """测试 PlatformInfo 数据类"""

    def test_platform_info_creation(self):
        """测试 PlatformInfo 对象创建"""
        info = PlatformInfo(
            os=OS.MACOS,
            arch=Arch.ARM64,
            shell=Shell.ZSH,
            shell_config_file="/Users/test/.zshrc",
        )
        
        assert info.os == OS.MACOS
        assert info.arch == Arch.ARM64
        assert info.shell == Shell.ZSH
        assert info.shell_config_file == "/Users/test/.zshrc"

    def test_platform_info_equality(self):
        """测试 PlatformInfo 对象相等性"""
        info1 = PlatformInfo(
            os=OS.MACOS,
            arch=Arch.ARM64,
            shell=Shell.ZSH,
            shell_config_file="/Users/test/.zshrc",
        )
        info2 = PlatformInfo(
            os=OS.MACOS,
            arch=Arch.ARM64,
            shell=Shell.ZSH,
            shell_config_file="/Users/test/.zshrc",
        )
        
        assert info1 == info2

    def test_platform_info_inequality(self):
        """测试 PlatformInfo 对象不相等性"""
        info1 = PlatformInfo(
            os=OS.MACOS,
            arch=Arch.ARM64,
            shell=Shell.ZSH,
            shell_config_file="/Users/test/.zshrc",
        )
        info2 = PlatformInfo(
            os=OS.LINUX,
            arch=Arch.X86_64,
            shell=Shell.BASH,
            shell_config_file="/home/test/.bashrc",
        )
        
        assert info1 != info2
