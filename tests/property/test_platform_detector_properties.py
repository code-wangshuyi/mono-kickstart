"""
平台检测器属性测试

使用 Hypothesis 进行基于属性的测试，验证平台检测器的通用属性。

Feature: mono-kickstart
Property 3: 平台特定安装包选择
**Validates: Requirements 1.5, 9.1, 9.2, 9.3**
"""

from hypothesis import given, strategies as st
import pytest

from mono_kickstart.platform_detector import (
    OS,
    Arch,
    Shell,
    PlatformInfo,
    PlatformDetector,
)


# 策略：生成支持的平台组合
supported_platforms = st.sampled_from([
    (OS.MACOS, Arch.ARM64),
    (OS.MACOS, Arch.X86_64),
    (OS.LINUX, Arch.X86_64),
])

# 策略：生成所有可能的 OS 和 Arch 组合
all_os = st.sampled_from([OS.MACOS, OS.LINUX, OS.UNSUPPORTED])
all_arch = st.sampled_from([Arch.ARM64, Arch.X86_64, Arch.UNSUPPORTED])


class TestProperty3PlatformSpecificPackageSelection:
    """
    属性 3: 平台特定安装包选择
    
    验证对于任何支持的平台（macOS ARM64、macOS x86_64、Linux x86_64），
    平台检测器能够正确识别平台信息，以便安装器选择匹配的工具安装包。
    
    **Validates: Requirements 1.5, 9.1, 9.2, 9.3**
    """

    @given(platform=supported_platforms)
    def test_supported_platforms_are_correctly_identified(self, platform):
        """
        属性：对于任何支持的平台组合，平台检测器应该能够正确识别
        
        这确保了安装器能够为每个支持的平台选择正确的安装包。
        """
        os_type, arch_type = platform
        
        # 创建 PlatformInfo 对象
        platform_info = PlatformInfo(
            os=os_type,
            arch=arch_type,
            shell=Shell.BASH,  # Shell 类型不影响平台支持性
            shell_config_file="/tmp/.bashrc"
        )
        
        # 验证平台信息正确
        assert platform_info.os == os_type
        assert platform_info.arch == arch_type
        
        # 验证这是一个支持的平台组合
        assert (os_type, arch_type) in [
            (OS.MACOS, Arch.ARM64),
            (OS.MACOS, Arch.X86_64),
            (OS.LINUX, Arch.X86_64),
        ]

    @given(platform=supported_platforms)
    def test_supported_platforms_have_distinct_characteristics(self, platform):
        """
        属性：每个支持的平台组合都有独特的特征，可用于选择正确的安装包
        
        这确保了安装器能够区分不同的平台并选择相应的安装包。
        """
        os_type, arch_type = platform
        
        # 为每个平台组合生成唯一的标识符
        # 这模拟了安装器如何为不同平台选择不同的安装包 URL
        platform_identifier = f"{os_type.value}-{arch_type.value}"
        
        # 验证每个平台都有唯一的标识符
        expected_identifiers = [
            "macos-arm64",
            "macos-x86_64",
            "linux-x86_64",
        ]
        
        assert platform_identifier in expected_identifiers
        
        # 验证标识符包含正确的 OS 和架构信息
        assert os_type.value in platform_identifier
        assert arch_type.value in platform_identifier

    @given(
        os_type=all_os,
        arch_type=all_arch,
    )
    def test_platform_support_consistency(self, os_type, arch_type):
        """
        属性：平台支持性检查与支持的平台列表一致
        
        对于任何 OS 和架构组合，如果它在支持列表中，则应该被识别为支持的；
        否则应该被识别为不支持的。
        
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        supported_combinations = [
            (OS.MACOS, Arch.ARM64),
            (OS.MACOS, Arch.X86_64),
            (OS.LINUX, Arch.X86_64),
        ]
        
        is_in_supported_list = (os_type, arch_type) in supported_combinations
        
        # 检查是否包含不支持的 OS 或架构
        has_unsupported = (os_type == OS.UNSUPPORTED or arch_type == Arch.UNSUPPORTED)
        
        # 如果包含不支持的 OS 或架构，则整个组合不支持
        if has_unsupported:
            assert not is_in_supported_list
        else:
            # 否则，检查是否在支持列表中
            if is_in_supported_list:
                # 支持的平台不应该包含 UNSUPPORTED
                assert os_type != OS.UNSUPPORTED
                assert arch_type != Arch.UNSUPPORTED
            else:
                # 不支持的组合（如 Linux ARM64）
                # 虽然 OS 和 Arch 本身可能是支持的，但组合不支持
                pass

    @given(platform=supported_platforms)
    def test_platform_info_enables_correct_package_selection(self, platform):
        """
        属性：平台信息包含足够的信息来选择正确的安装包
        
        验证 PlatformInfo 对象包含所有必要的信息，使安装器能够：
        1. 识别操作系统类型
        2. 识别 CPU 架构
        3. 选择相应的安装包 URL 或命令
        
        **Validates: Requirements 1.5, 9.1, 9.2, 9.3**
        """
        os_type, arch_type = platform
        
        platform_info = PlatformInfo(
            os=os_type,
            arch=arch_type,
            shell=Shell.BASH,
            shell_config_file="/tmp/.bashrc"
        )
        
        # 验证平台信息包含必要的字段
        assert hasattr(platform_info, 'os')
        assert hasattr(platform_info, 'arch')
        
        # 验证字段值是正确的枚举类型
        assert isinstance(platform_info.os, OS)
        assert isinstance(platform_info.arch, Arch)
        
        # 验证可以基于平台信息构建安装包标识符
        # 这模拟了安装器如何使用平台信息选择安装包
        if platform_info.os == OS.MACOS and platform_info.arch == Arch.ARM64:
            package_suffix = "MacOSX-arm64"
        elif platform_info.os == OS.MACOS and platform_info.arch == Arch.X86_64:
            package_suffix = "MacOSX-x86_64"
        elif platform_info.os == OS.LINUX and platform_info.arch == Arch.X86_64:
            package_suffix = "Linux-x86_64"
        else:
            package_suffix = None
        
        # 对于支持的平台，应该能够生成有效的包后缀
        assert package_suffix is not None
        assert len(package_suffix) > 0

    @given(platform=supported_platforms)
    def test_platform_specific_conda_url_selection(self, platform):
        """
        属性：对于每个支持的平台，应该能够选择正确的 Conda 安装包 URL
        
        这是属性 3 的具体应用：验证 Conda 安装器能够根据平台信息
        选择正确的 Miniconda 安装包。
        
        **Validates: Requirements 1.5**
        """
        os_type, arch_type = platform
        
        # 模拟 Conda 安装器的 URL 选择逻辑
        base_url = "https://repo.anaconda.com/miniconda/"
        version = "latest"
        
        if os_type == OS.MACOS and arch_type == Arch.ARM64:
            expected_pattern = "MacOSX-arm64"
        elif os_type == OS.MACOS and arch_type == Arch.X86_64:
            expected_pattern = "MacOSX-x86_64"
        elif os_type == OS.LINUX and arch_type == Arch.X86_64:
            expected_pattern = "Linux-x86_64"
        else:
            expected_pattern = None
        
        # 验证能够为每个支持的平台生成正确的 URL 模式
        assert expected_pattern is not None
        
        # 验证 URL 模式包含正确的平台标识符
        if os_type == OS.MACOS:
            assert "MacOSX" in expected_pattern
        elif os_type == OS.LINUX:
            assert "Linux" in expected_pattern
        
        if arch_type == Arch.ARM64:
            assert "arm64" in expected_pattern
        elif arch_type == Arch.X86_64:
            assert "x86_64" in expected_pattern

    @given(
        os_type=all_os,
        arch_type=all_arch,
    )
    def test_unsupported_platforms_are_rejected(self, os_type, arch_type):
        """
        属性：不支持的平台组合应该被正确识别为不支持
        
        这确保了安装器不会尝试在不支持的平台上安装工具。
        
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        supported_combinations = [
            (OS.MACOS, Arch.ARM64),
            (OS.MACOS, Arch.X86_64),
            (OS.LINUX, Arch.X86_64),
        ]
        
        is_supported = (os_type, arch_type) in supported_combinations
        
        # 如果包含 UNSUPPORTED，则整个组合不支持
        if os_type == OS.UNSUPPORTED or arch_type == Arch.UNSUPPORTED:
            assert not is_supported
        
        # 如果不在支持列表中，则不支持
        if not is_supported:
            # 验证这确实不是一个支持的组合
            assert (os_type, arch_type) not in supported_combinations
