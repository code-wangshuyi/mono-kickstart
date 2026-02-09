"""CLI 的基于属性的测试

本模块使用 Hypothesis 框架测试 CLI 的通用属性。
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from mono_kickstart.installer_base import InstallResult, InstallReport


# 定义测试数据生成策略

# 可用的子命令
SUBCOMMANDS = ["init", "upgrade", "install", "setup-shell"]

# 可用的工具名称
AVAILABLE_TOOLS = [
    "nvm", "node", "conda", "bun", "uv",
    "claude-code", "codex", "spec-kit", "bmad-method"
]

# init 命令的选项
INIT_OPTIONS = [
    [],
    ["--dry-run"],
    ["--force"],
    ["--save-config"],
    ["--interactive"],
    ["--dry-run", "--force"],
    ["--config", "test.yaml"],
]

# upgrade 命令的选项
UPGRADE_OPTIONS = [
    [],
    ["--dry-run"],
    ["--all"],
    ["--all", "--dry-run"],
]

# install 命令的选项
INSTALL_OPTIONS = [
    [],
    ["--dry-run"],
    ["--all"],
    ["--all", "--dry-run"],
]


@st.composite
def init_command_strategy(draw):
    """生成 init 命令及其参数的策略"""
    options = draw(st.sampled_from(INIT_OPTIONS))
    return ["init"] + options


@st.composite
def upgrade_command_strategy(draw):
    """生成 upgrade 命令及其参数的策略"""
    options = draw(st.sampled_from(UPGRADE_OPTIONS))
    # 可能添加工具名称参数
    if "--all" not in options and draw(st.booleans()):
        tool = draw(st.sampled_from(AVAILABLE_TOOLS))
        return ["upgrade", tool] + options
    return ["upgrade"] + options


@st.composite
def install_command_strategy(draw):
    """生成 install 命令及其参数的策略"""
    options = draw(st.sampled_from(INSTALL_OPTIONS))
    # 可能添加工具名称参数
    if "--all" not in options and draw(st.booleans()):
        tool = draw(st.sampled_from(AVAILABLE_TOOLS))
        return ["install", tool] + options
    return ["install"] + options


@st.composite
def command_strategy(draw):
    """生成任意命令及其参数的策略"""
    subcommand = draw(st.sampled_from(SUBCOMMANDS))
    
    if subcommand == "init":
        return draw(init_command_strategy())
    elif subcommand == "upgrade":
        return draw(upgrade_command_strategy())
    elif subcommand == "install":
        return draw(install_command_strategy())
    elif subcommand == "setup-shell":
        return ["setup-shell"]
    else:
        return [subcommand]


def create_mock_orchestrator():
    """创建一个 mock 的 InstallOrchestrator"""
    mock_orchestrator = MagicMock()
    
    # Mock run_init 返回空的报告字典
    mock_orchestrator.run_init.return_value = {}
    
    # Mock run_upgrade 返回空的报告字典
    mock_orchestrator.run_upgrade.return_value = {}
    
    # Mock install_all_tools 返回空的报告字典
    mock_orchestrator.install_all_tools.return_value = {}
    
    # Mock install_tool 返回成功的报告
    mock_orchestrator.install_tool.return_value = InstallReport(
        tool_name="test",
        result=InstallResult.SUCCESS,
        message="Test success"
    )
    
    # Mock print_summary 不做任何事
    mock_orchestrator.print_summary.return_value = None
    
    return mock_orchestrator


class TestCommandEntryEquivalence:
    """测试属性 13: 命令入口等价性
    
    **Validates: Requirements 7.8, 10.8**
    """
    
    @given(command_args=command_strategy())
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # 禁用超时，因为某些命令可能需要较长时间
    )
    def test_mk_and_mono_kickstart_produce_same_results(self, command_args):
        """验证 mk 和 mono-kickstart 命令产生相同的执行结果
        
        对于任何命令和参数组合，使用 mk 和 mono-kickstart 两个入口
        应该产生完全相同的执行结果（退出码和输出）。
        """
        # 跳过需要交互的命令
        if "--interactive" in command_args:
            assume(False)
        
        # 跳过需要实际文件的命令（避免文件系统副作用）
        if "--config" in command_args:
            assume(False)
        
        # 跳过 setup-shell 命令（它有不同的实现路径）
        if command_args[0] == "setup-shell":
            assume(False)
        
        # 创建 mock orchestrator
        mock_orch = create_mock_orchestrator()
        
        # 测试 mk 入口
        with patch('sys.argv', ['mk'] + command_args):
            with patch('sys.stdout', new=StringIO()) as mk_stdout:
                with patch('sys.stderr', new=StringIO()) as mk_stderr:
                    with patch('mono_kickstart.orchestrator.InstallOrchestrator', return_value=mock_orch):
                        with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector:
                            # Mock 平台检测为支持的平台
                            mock_platform = MagicMock()
                            mock_platform.os.value = "linux"
                            mock_platform.arch.value = "x86_64"
                            mock_platform.shell.value = "bash"
                            mock_detector.return_value.is_supported.return_value = True
                            mock_detector.return_value.detect_all.return_value = mock_platform
                            
                            with patch('mono_kickstart.config.ConfigManager') as mock_config:
                                # Mock 配置管理器
                                mock_config_obj = MagicMock()
                                mock_config_obj.validate.return_value = []
                                mock_config_obj.project.name = "test-project"
                                mock_config.return_value.load_with_priority.return_value = mock_config_obj
                                mock_config.return_value.load_from_defaults.return_value = mock_config_obj
                                
                                with patch('mono_kickstart.tool_detector.ToolDetector') as mock_tool_detector:
                                    # Mock 工具检测器
                                    mock_tool_detector.return_value.detect_all_tools.return_value = {}
                                    
                                    try:
                                        from mono_kickstart.cli import main
                                        mk_exit_code = main()
                                    except SystemExit as e:
                                        mk_exit_code = e.code if e.code is not None else 0
                                    except Exception:
                                        # 如果发生异常，记录为非零退出码
                                        mk_exit_code = 1
                                    
                                    mk_output = mk_stdout.getvalue()
                                    mk_error = mk_stderr.getvalue()
        
        # 测试 mono-kickstart 入口
        with patch('sys.argv', ['mono-kickstart'] + command_args):
            with patch('sys.stdout', new=StringIO()) as mono_stdout:
                with patch('sys.stderr', new=StringIO()) as mono_stderr:
                    with patch('mono_kickstart.orchestrator.InstallOrchestrator', return_value=mock_orch):
                        with patch('mono_kickstart.platform_detector.PlatformDetector') as mock_detector:
                            # Mock 平台检测为支持的平台
                            mock_platform = MagicMock()
                            mock_platform.os.value = "linux"
                            mock_platform.arch.value = "x86_64"
                            mock_platform.shell.value = "bash"
                            mock_detector.return_value.is_supported.return_value = True
                            mock_detector.return_value.detect_all.return_value = mock_platform
                            
                            with patch('mono_kickstart.config.ConfigManager') as mock_config:
                                # Mock 配置管理器
                                mock_config_obj = MagicMock()
                                mock_config_obj.validate.return_value = []
                                mock_config_obj.project.name = "test-project"
                                mock_config.return_value.load_with_priority.return_value = mock_config_obj
                                mock_config.return_value.load_from_defaults.return_value = mock_config_obj
                                
                                with patch('mono_kickstart.tool_detector.ToolDetector') as mock_tool_detector:
                                    # Mock 工具检测器
                                    mock_tool_detector.return_value.detect_all_tools.return_value = {}
                                    
                                    try:
                                        # 重新导入以确保使用相同的代码路径
                                        from mono_kickstart.cli import main
                                        mono_exit_code = main()
                                    except SystemExit as e:
                                        mono_exit_code = e.code if e.code is not None else 0
                                    except Exception:
                                        # 如果发生异常，记录为非零退出码
                                        mono_exit_code = 1
                                    
                                    mono_output = mono_stdout.getvalue()
                                    mono_error = mono_stderr.getvalue()
        
        # 验证退出码相同
        assert mk_exit_code == mono_exit_code, (
            f"Exit codes differ for command {command_args}: "
            f"mk={mk_exit_code}, mono-kickstart={mono_exit_code}"
        )
        
        # 验证标准输出相同（忽略程序名称的差异）
        # 由于输出中可能包含程序名称，我们需要规范化输出
        mk_normalized = mk_output.replace('mk', 'PROG').replace('mono-kickstart', 'PROG')
        mono_normalized = mono_output.replace('mk', 'PROG').replace('mono-kickstart', 'PROG')
        
        assert mk_normalized == mono_normalized, (
            f"Outputs differ for command {command_args}:\n"
            f"mk output:\n{mk_output}\n"
            f"mono-kickstart output:\n{mono_output}"
        )
        
        # 验证标准错误相同（忽略程序名称的差异）
        mk_error_normalized = mk_error.replace('mk', 'PROG').replace('mono-kickstart', 'PROG')
        mono_error_normalized = mono_error.replace('mk', 'PROG').replace('mono-kickstart', 'PROG')
        
        assert mk_error_normalized == mono_error_normalized, (
            f"Error outputs differ for command {command_args}:\n"
            f"mk error:\n{mk_error}\n"
            f"mono-kickstart error:\n{mono_error}"
        )
    
    def test_help_option_equivalence(self):
        """验证 --help 选项在两个入口点中产生相同的帮助信息
        
        这是一个特殊的测试用例，因为 --help 会导致 SystemExit。
        """
        # 测试 mk --help
        with patch('sys.argv', ['mk', '--help']):
            with patch('sys.stdout', new=StringIO()) as mk_stdout:
                with pytest.raises(SystemExit) as mk_exc:
                    from mono_kickstart.cli import main
                    main()
                mk_help = mk_stdout.getvalue()
                mk_exit_code = mk_exc.value.code
        
        # 测试 mono-kickstart --help
        with patch('sys.argv', ['mono-kickstart', '--help']):
            with patch('sys.stdout', new=StringIO()) as mono_stdout:
                with pytest.raises(SystemExit) as mono_exc:
                    from mono_kickstart.cli import main
                    main()
                mono_help = mono_stdout.getvalue()
                mono_exit_code = mono_exc.value.code
        
        # 验证退出码相同
        assert mk_exit_code == mono_exit_code == 0
        
        # 验证帮助信息相同（忽略程序名称）
        mk_normalized = mk_help.replace('mk', 'PROG').replace('mono-kickstart', 'PROG')
        mono_normalized = mono_help.replace('mk', 'PROG').replace('mono-kickstart', 'PROG')
        assert mk_normalized == mono_normalized
    
    def test_version_option_equivalence(self):
        """验证 --version 选项在两个入口点中产生相同的版本信息
        
        这是一个特殊的测试用例，因为 --version 会导致 SystemExit。
        """
        # 测试 mk --version
        with patch('sys.argv', ['mk', '--version']):
            with patch('sys.stdout', new=StringIO()) as mk_stdout:
                with pytest.raises(SystemExit) as mk_exc:
                    from mono_kickstart.cli import main
                    main()
                mk_version = mk_stdout.getvalue()
                mk_exit_code = mk_exc.value.code
        
        # 测试 mono-kickstart --version
        with patch('sys.argv', ['mono-kickstart', '--version']):
            with patch('sys.stdout', new=StringIO()) as mono_stdout:
                with pytest.raises(SystemExit) as mono_exc:
                    from mono_kickstart.cli import main
                    main()
                mono_version = mono_stdout.getvalue()
                mono_exit_code = mono_exc.value.code
        
        # 验证退出码相同
        assert mk_exit_code == mono_exit_code == 0
        
        # 验证版本信息相同
        assert mk_version == mono_version
        
        # 验证版本信息包含版本号
        from mono_kickstart import __version__
        assert __version__ in mk_version
    
    @given(
        subcommand=st.sampled_from(["init", "upgrade", "install"])
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None
    )
    def test_subcommand_help_equivalence(self, subcommand):
        """验证子命令的 --help 选项在两个入口点中产生相同的帮助信息"""
        # 测试 mk <subcommand> --help
        with patch('sys.argv', ['mk', subcommand, '--help']):
            with patch('sys.stdout', new=StringIO()) as mk_stdout:
                with pytest.raises(SystemExit) as mk_exc:
                    from mono_kickstart.cli import main
                    main()
                mk_help = mk_stdout.getvalue()
                mk_exit_code = mk_exc.value.code
        
        # 测试 mono-kickstart <subcommand> --help
        with patch('sys.argv', ['mono-kickstart', subcommand, '--help']):
            with patch('sys.stdout', new=StringIO()) as mono_stdout:
                with pytest.raises(SystemExit) as mono_exc:
                    from mono_kickstart.cli import main
                    main()
                mono_help = mono_stdout.getvalue()
                mono_exit_code = mono_exc.value.code
        
        # 验证退出码相同
        assert mk_exit_code == mono_exit_code == 0
        
        # 验证帮助信息相同（忽略程序名称）
        mk_normalized = mk_help.replace('mk', 'PROG').replace('mono-kickstart', 'PROG')
        mono_normalized = mono_help.replace('mk', 'PROG').replace('mono-kickstart', 'PROG')
        assert mk_normalized == mono_normalized


class TestCommandEntryPointsExist:
    """测试命令入口点的存在性"""
    
    def test_mk_entry_point_exists(self):
        """验证 mk 入口点存在于 pyproject.toml 中"""
        import tomli
        
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomli.load(f)
        
        scripts = pyproject.get("project", {}).get("scripts", {})
        assert "mk" in scripts, "mk entry point not found in pyproject.toml"
        assert scripts["mk"] == "mono_kickstart.cli:main"
    
    def test_mono_kickstart_entry_point_exists(self):
        """验证 mono-kickstart 入口点存在于 pyproject.toml 中"""
        import tomli
        
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomli.load(f)
        
        scripts = pyproject.get("project", {}).get("scripts", {})
        assert "mono-kickstart" in scripts, "mono-kickstart entry point not found in pyproject.toml"
        assert scripts["mono-kickstart"] == "mono_kickstart.cli:main"
    
    def test_both_entry_points_use_same_function(self):
        """验证两个入口点使用相同的函数"""
        import tomli
        
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomli.load(f)
        
        scripts = pyproject.get("project", {}).get("scripts", {})
        mk_entry = scripts.get("mk")
        mono_entry = scripts.get("mono-kickstart")
        
        assert mk_entry == mono_entry, (
            f"Entry points use different functions: mk={mk_entry}, mono-kickstart={mono_entry}"
        )
