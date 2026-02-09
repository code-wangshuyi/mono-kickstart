"""属性测试：Codex CLI 安装方式选择

**Validates: Requirements 1.9**

该模块测试 Codex CLI 安装器的条件安装方式选择逻辑。
"""

import pytest
from hypothesis import given, strategies as st
from unittest.mock import Mock, patch

from src.mono_kickstart.config import ToolConfig
from src.mono_kickstart.installers.codex_installer import CodexInstaller
from src.mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell


# 策略：生成平台信息
@st.composite
def platform_info_strategy(draw):
    """生成平台信息策略"""
    os = draw(st.sampled_from([OS.MACOS, OS.LINUX]))
    arch = draw(st.sampled_from([Arch.ARM64, Arch.X86_64]))
    shell = draw(st.sampled_from([Shell.BASH, Shell.ZSH, Shell.FISH]))
    shell_config_file = f"/home/user/.{shell.value}rc"
    
    return PlatformInfo(
        os=os,
        arch=arch,
        shell=shell,
        shell_config_file=shell_config_file
    )


# 策略：生成工具配置
@st.composite
def tool_config_strategy(draw):
    """生成工具配置策略"""
    enabled = draw(st.booleans())
    version = draw(st.one_of(st.none(), st.text(min_size=1, max_size=20)))
    install_via = draw(st.one_of(st.none(), st.sampled_from(['bun', 'npm', 'Bun', 'NPM'])))
    
    return ToolConfig(
        enabled=enabled,
        version=version,
        install_via=install_via
    )


# Feature: mono-kickstart, Property 4: 条件安装方式选择
@given(
    platform_info=platform_info_strategy(),
    config=tool_config_strategy(),
    bun_installed=st.booleans()
)
def test_codex_install_method_selection(platform_info, config, bun_installed):
    """
    属性 4: 条件安装方式选择
    
    对于任何工具安装状态，当安装 Codex CLI 时，如果 Bun 已安装则应使用 bun install -g，
    否则应使用 npm install -g。
    
    **Validates: Requirements 1.9**
    """
    with patch('shutil.which') as mock_which:
        # 模拟 Bun 的安装状态
        def which_side_effect(cmd):
            if cmd == "bun":
                return "/usr/local/bin/bun" if bun_installed else None
            return None
        
        mock_which.side_effect = which_side_effect
        
        # 创建安装器
        installer = CodexInstaller(platform_info, config)
        
        # 验证安装方式选择逻辑
        if config.install_via:
            # 如果配置中指定了安装方式，应使用指定的方式
            expected_method = config.install_via.lower()
            assert installer.install_method == expected_method, \
                f"配置指定了 install_via={config.install_via}，应使用 {expected_method}"
        else:
            # 如果配置中未指定，应根据 Bun 是否安装来选择
            if bun_installed:
                assert installer.install_method == 'bun', \
                    "Bun 已安装，应使用 bun 作为安装方式"
            else:
                assert installer.install_method == 'npm', \
                    "Bun 未安装，应使用 npm 作为安装方式"


# Feature: mono-kickstart, Property 4: 条件安装方式选择（安装命令验证）
@given(
    platform_info=platform_info_strategy(),
    bun_installed=st.booleans()
)
def test_codex_install_command_matches_method(platform_info, bun_installed):
    """
    属性 4: 条件安装方式选择（安装命令验证）
    
    验证实际执行的安装命令与选择的安装方式一致。
    
    **Validates: Requirements 1.9**
    """
    with patch('shutil.which') as mock_which, \
         patch.object(CodexInstaller, 'run_command') as mock_run_command, \
         patch.object(CodexInstaller, 'verify') as mock_verify:
        
        # 模拟 Bun 的安装状态
        def which_side_effect(cmd):
            if cmd == "bun":
                return "/usr/local/bin/bun" if bun_installed else None
            elif cmd == "npm":
                return "/usr/local/bin/npm"
            elif cmd == "codex":
                return None  # 未安装
            return None
        
        mock_which.side_effect = which_side_effect
        
        # 模拟命令执行成功
        mock_run_command.return_value = (0, "success", "")
        
        # 模拟验证：第一次返回 False（未安装），第二次返回 True（安装成功）
        mock_verify.side_effect = [False, True]
        
        # 创建安装器（不指定 install_via）
        config = ToolConfig(enabled=True)
        installer = CodexInstaller(platform_info, config)
        
        # 执行安装
        result = installer.install()
        
        # 验证安装命令
        if bun_installed:
            # 应该调用 bun install -g
            assert mock_run_command.called
            call_args = mock_run_command.call_args[0][0]
            assert "bun install -g @openai/codex" in call_args, \
                f"Bun 已安装，应使用 'bun install -g' 命令，实际命令: {call_args}"
        else:
            # 应该调用 npm install -g
            assert mock_run_command.called
            call_args = mock_run_command.call_args[0][0]
            assert "npm i -g @openai/codex" in call_args, \
                f"Bun 未安装，应使用 'npm install -g' 命令，实际命令: {call_args}"


# Feature: mono-kickstart, Property 4: 条件安装方式选择（升级命令验证）
@given(
    platform_info=platform_info_strategy(),
    bun_installed=st.booleans()
)
def test_codex_upgrade_command_matches_method(platform_info, bun_installed):
    """
    属性 4: 条件安装方式选择（升级命令验证）
    
    验证实际执行的升级命令与选择的安装方式一致。
    
    **Validates: Requirements 1.9**
    """
    with patch('shutil.which') as mock_which, \
         patch.object(CodexInstaller, 'run_command') as mock_run_command, \
         patch.object(CodexInstaller, 'verify') as mock_verify, \
         patch.object(CodexInstaller, '_get_installed_version') as mock_get_version:
        
        # 模拟 Bun 的安装状态
        def which_side_effect(cmd):
            if cmd == "bun":
                return "/usr/local/bin/bun" if bun_installed else None
            elif cmd == "npm":
                return "/usr/local/bin/npm"
            elif cmd == "codex":
                return "/usr/local/bin/codex"  # 已安装
            return None
        
        mock_which.side_effect = which_side_effect
        
        # 模拟命令执行成功
        mock_run_command.return_value = (0, "success", "")
        
        # 模拟验证成功
        mock_verify.return_value = True
        
        # 模拟版本获取
        mock_get_version.return_value = "1.0.0"
        
        # 创建安装器（不指定 install_via）
        config = ToolConfig(enabled=True)
        installer = CodexInstaller(platform_info, config)
        
        # 执行升级
        result = installer.upgrade()
        
        # 验证升级命令
        if bun_installed:
            # 应该调用 bun update -g
            assert mock_run_command.called
            call_args = mock_run_command.call_args[0][0]
            assert "bun update -g @openai/codex" in call_args, \
                f"Bun 已安装，应使用 'bun update -g' 命令，实际命令: {call_args}"
        else:
            # 应该调用 npm update -g
            assert mock_run_command.called
            call_args = mock_run_command.call_args[0][0]
            assert "npm update -g @openai/codex" in call_args, \
                f"Bun 未安装，应使用 'npm update -g' 命令，实际命令: {call_args}"
