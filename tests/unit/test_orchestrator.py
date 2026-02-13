"""
安装编排器的单元测试

测试安装编排器的核心功能：
- 工具安装顺序
- 幂等性（重复执行）
- 容错性（部分失败）
- 安装摘要生成
- 升级流程

**Validates: Requirements 1.1, 1.2, 1.12, 1.13, 5.4, 6.1, 6.2, 6.3**
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from mono_kickstart.orchestrator import (
    InstallOrchestrator,
    INSTALL_ORDER,
)
from mono_kickstart.config import Config, ToolConfig, RegistryConfig, ProjectConfig
from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
from mono_kickstart.installer_base import InstallReport, InstallResult
from mono_kickstart.tool_detector import ToolStatus


@pytest.fixture
def platform_info():
    """创建测试用的平台信息"""
    return PlatformInfo(
        os=OS.LINUX, arch=Arch.X86_64, shell=Shell.BASH, shell_config_file="~/.bashrc"
    )


@pytest.fixture
def config():
    """创建测试用的配置"""
    return Config(
        project=ProjectConfig(name="test-project"),
        tools={
            "nvm": ToolConfig(enabled=True),
            "node": ToolConfig(enabled=True),
            "conda": ToolConfig(enabled=True),
            "bun": ToolConfig(enabled=True),
            "uv": ToolConfig(enabled=True),
        },
        registry=RegistryConfig(),
    )


@pytest.fixture
def orchestrator(config, platform_info):
    """创建测试用的安装编排器"""
    return InstallOrchestrator(config, platform_info, dry_run=False)


class TestOrchestratorInitialization:
    """测试安装编排器初始化"""

    def test_initialization(self, config, platform_info):
        """测试编排器初始化"""
        orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)

        assert orchestrator.config == config
        assert orchestrator.platform_info == platform_info
        assert orchestrator.dry_run is False
        assert orchestrator.tool_detector is not None
        assert orchestrator.mirror_configurator is not None

    def test_initialization_with_dry_run(self, config, platform_info):
        """测试编排器初始化（模拟运行模式）"""
        orchestrator = InstallOrchestrator(config, platform_info, dry_run=True)

        assert orchestrator.dry_run is True


class TestGetInstallOrder:
    """测试工具安装顺序确定"""

    def test_get_install_order_all_enabled(self, orchestrator):
        """测试所有工具启用时的安装顺序"""
        # 启用所有工具
        for tool_name in INSTALL_ORDER:
            orchestrator.config.tools[tool_name] = ToolConfig(enabled=True)

        order = orchestrator.get_install_order()

        # 验证顺序与 INSTALL_ORDER 一致
        assert order == INSTALL_ORDER

    def test_get_install_order_partial_enabled(self, orchestrator):
        """测试部分工具启用时的安装顺序"""
        # 只启用部分工具
        orchestrator.config.tools = {
            "nvm": ToolConfig(enabled=True),
            "node": ToolConfig(enabled=True),
            "bun": ToolConfig(enabled=False),
            "uv": ToolConfig(enabled=True),
        }

        order = orchestrator.get_install_order()

        # 验证只包含启用的工具
        assert "nvm" in order
        assert "node" in order
        assert "uv" in order
        assert "bun" not in order

        # 验证顺序正确
        assert order.index("nvm") < order.index("node")
        assert order.index("node") < order.index("uv")

    def test_get_install_order_none_enabled(self, orchestrator):
        """测试没有工具启用时的安装顺序"""
        # 禁用所有工具
        for tool_name in INSTALL_ORDER:
            orchestrator.config.tools[tool_name] = ToolConfig(enabled=False)

        order = orchestrator.get_install_order()

        # 验证返回空列表
        assert order == []

    def test_get_install_order_respects_dependency_order(self, orchestrator):
        """测试安装顺序遵循依赖关系"""
        # 启用所有工具
        for tool_name in INSTALL_ORDER:
            orchestrator.config.tools[tool_name] = ToolConfig(enabled=True)

        order = orchestrator.get_install_order()

        # 验证依赖关系：NVM 必须在 Node.js 之前
        assert order.index("nvm") < order.index("node")

        # 验证依赖关系：uv 必须在 spec-kit 之前
        assert order.index("uv") < order.index("spec-kit")

        # 验证依赖关系：Node.js 必须在 bmad-method 之前
        assert order.index("node") < order.index("bmad-method")


class TestInstallTool:
    """测试单个工具安装"""

    def test_install_tool_success(self, orchestrator):
        """测试成功安装工具"""
        mock_installer = Mock()
        mock_installer.install.return_value = InstallReport(
            tool_name="nvm", result=InstallResult.SUCCESS, message="安装成功", version="0.40.4"
        )

        with patch.object(orchestrator, "_create_installer", return_value=mock_installer):
            report = orchestrator.install_tool("nvm")

        assert report.result == InstallResult.SUCCESS
        assert report.tool_name == "nvm"
        assert report.version == "0.40.4"
        mock_installer.install.assert_called_once()

    def test_install_tool_already_installed(self, orchestrator):
        """测试工具已安装的情况"""
        mock_installer = Mock()
        mock_installer.install.return_value = InstallReport(
            tool_name="node", result=InstallResult.SKIPPED, message="已安装", version="20.11.0"
        )

        with patch.object(orchestrator, "_create_installer", return_value=mock_installer):
            report = orchestrator.install_tool("node")

        assert report.result == InstallResult.SKIPPED
        assert report.tool_name == "node"

    def test_install_tool_failure(self, orchestrator):
        """测试工具安装失败"""
        mock_installer = Mock()
        mock_installer.install.return_value = InstallReport(
            tool_name="bun", result=InstallResult.FAILED, message="安装失败", error="网络错误"
        )

        with patch.object(orchestrator, "_create_installer", return_value=mock_installer):
            report = orchestrator.install_tool("bun")

        assert report.result == InstallResult.FAILED
        assert report.tool_name == "bun"
        assert report.error == "网络错误"

    def test_install_tool_invalid_name(self, orchestrator):
        """测试无效的工具名称"""
        report = orchestrator.install_tool("invalid-tool")

        assert report.result == InstallResult.FAILED
        assert "无效的工具名称" in report.message
        assert report.error is not None

    def test_install_tool_exception_handling(self, orchestrator):
        """测试安装过程中的异常处理"""
        mock_installer = Mock()
        mock_installer.install.side_effect = Exception("意外错误")

        with patch.object(orchestrator, "_create_installer", return_value=mock_installer):
            report = orchestrator.install_tool("uv")

        assert report.result == InstallResult.FAILED
        assert "异常" in report.message
        assert "意外错误" in report.error

    def test_install_tool_dry_run(self, config, platform_info):
        """测试模拟运行模式"""
        orchestrator = InstallOrchestrator(config, platform_info, dry_run=True)

        report = orchestrator.install_tool("nvm")

        assert report.result == InstallResult.SKIPPED
        assert "模拟运行" in report.message


class TestInstallAllTools:
    """测试批量安装所有工具"""

    def test_install_all_tools_success(self, orchestrator):
        """测试成功安装所有工具"""
        # 设置启用的工具（禁用其他工具）
        orchestrator.config.tools = {
            "nvm": ToolConfig(enabled=True),
            "node": ToolConfig(enabled=True),
            "bun": ToolConfig(enabled=True),
            "conda": ToolConfig(enabled=False),
            "uv": ToolConfig(enabled=False),
            "gh": ToolConfig(enabled=False),
            "claude-code": ToolConfig(enabled=False),
            "copilot-cli": ToolConfig(enabled=False),
            "codex": ToolConfig(enabled=False),
            "opencode": ToolConfig(enabled=False),
            "npx": ToolConfig(enabled=False),
            "uipro": ToolConfig(enabled=False),
            "spec-kit": ToolConfig(enabled=False),
            "bmad-method": ToolConfig(enabled=False),
        }

        # Mock 安装器
        def create_mock_installer(tool_name):
            mock_installer = Mock()
            mock_installer.install.return_value = InstallReport(
                tool_name=tool_name, result=InstallResult.SUCCESS, message=f"{tool_name} 安装成功"
            )
            return mock_installer

        with patch.object(
            orchestrator, "_create_installer", side_effect=lambda name: create_mock_installer(name)
        ):
            reports = orchestrator.install_all_tools()

        # 验证所有工具都被安装
        assert len(reports) == 3
        assert "nvm" in reports
        assert "node" in reports
        assert "bun" in reports

        # 验证所有工具都成功
        for report in reports.values():
            assert report.result == InstallResult.SUCCESS

    def test_install_all_tools_partial_failure(self, orchestrator):
        """测试部分工具安装失败（容错性）"""
        # 设置启用的工具（禁用其他工具）
        orchestrator.config.tools = {
            "nvm": ToolConfig(enabled=True),
            "node": ToolConfig(enabled=True),
            "bun": ToolConfig(enabled=True),
            "conda": ToolConfig(enabled=False),
            "uv": ToolConfig(enabled=False),
            "gh": ToolConfig(enabled=False),
            "claude-code": ToolConfig(enabled=False),
            "copilot-cli": ToolConfig(enabled=False),
            "codex": ToolConfig(enabled=False),
            "opencode": ToolConfig(enabled=False),
            "npx": ToolConfig(enabled=False),
            "uipro": ToolConfig(enabled=False),
            "spec-kit": ToolConfig(enabled=False),
            "bmad-method": ToolConfig(enabled=False),
        }

        # Mock 安装器：第二个工具失败
        def create_mock_installer(tool_name):
            mock_installer = Mock()
            if tool_name == "node":
                mock_installer.install.return_value = InstallReport(
                    tool_name=tool_name,
                    result=InstallResult.FAILED,
                    message=f"{tool_name} 安装失败",
                    error="网络错误",
                )
            else:
                mock_installer.install.return_value = InstallReport(
                    tool_name=tool_name,
                    result=InstallResult.SUCCESS,
                    message=f"{tool_name} 安装成功",
                )
            return mock_installer

        with patch.object(
            orchestrator, "_create_installer", side_effect=lambda name: create_mock_installer(name)
        ):
            reports = orchestrator.install_all_tools()

        # 验证所有工具都被尝试安装
        assert len(reports) == 3

        # 验证失败的工具
        assert reports["node"].result == InstallResult.FAILED

        # 验证其他工具仍然成功
        assert reports["nvm"].result == InstallResult.SUCCESS
        assert reports["bun"].result == InstallResult.SUCCESS

    def test_install_all_tools_respects_order(self, orchestrator):
        """测试安装顺序正确"""
        # 设置启用的工具（禁用其他工具）
        orchestrator.config.tools = {
            "nvm": ToolConfig(enabled=True),
            "node": ToolConfig(enabled=True),
            "bun": ToolConfig(enabled=True),
            "conda": ToolConfig(enabled=False),
            "uv": ToolConfig(enabled=False),
            "gh": ToolConfig(enabled=False),
            "claude-code": ToolConfig(enabled=False),
            "copilot-cli": ToolConfig(enabled=False),
            "codex": ToolConfig(enabled=False),
            "opencode": ToolConfig(enabled=False),
            "npx": ToolConfig(enabled=False),
            "uipro": ToolConfig(enabled=False),
            "spec-kit": ToolConfig(enabled=False),
            "bmad-method": ToolConfig(enabled=False),
        }

        install_sequence = []

        def create_mock_installer(tool_name):
            mock_installer = Mock()

            def record_install():
                install_sequence.append(tool_name)
                return InstallReport(
                    tool_name=tool_name,
                    result=InstallResult.SUCCESS,
                    message=f"{tool_name} 安装成功",
                )

            mock_installer.install.side_effect = record_install
            return mock_installer

        with patch.object(
            orchestrator, "_create_installer", side_effect=lambda name: create_mock_installer(name)
        ):
            orchestrator.install_all_tools()

        # 验证安装顺序
        assert install_sequence == ["nvm", "node", "bun"]

    def test_install_all_tools_empty_list(self, orchestrator):
        """测试没有启用工具时的情况"""
        # 禁用所有工具
        orchestrator.config.tools = {
            "nvm": ToolConfig(enabled=False),
            "node": ToolConfig(enabled=False),
            "conda": ToolConfig(enabled=False),
            "bun": ToolConfig(enabled=False),
            "uv": ToolConfig(enabled=False),
            "gh": ToolConfig(enabled=False),
            "claude-code": ToolConfig(enabled=False),
            "copilot-cli": ToolConfig(enabled=False),
            "codex": ToolConfig(enabled=False),
            "opencode": ToolConfig(enabled=False),
            "npx": ToolConfig(enabled=False),
            "uipro": ToolConfig(enabled=False),
            "spec-kit": ToolConfig(enabled=False),
            "bmad-method": ToolConfig(enabled=False),
        }

        reports = orchestrator.install_all_tools()

        # 验证返回空字典
        assert reports == {}


class TestConfigureMirrors:
    """测试镜像源配置"""

    def test_configure_mirrors_success(self, orchestrator):
        """测试成功配置所有镜像源"""
        with patch.object(
            orchestrator.mirror_configurator,
            "configure_all",
            return_value={"npm": True, "bun": True, "uv": True},
        ):
            results = orchestrator.configure_mirrors()

        assert results["npm"] is True
        assert results["bun"] is True
        assert results["uv"] is True

    def test_configure_mirrors_partial_failure(self, orchestrator):
        """测试部分镜像源配置失败"""
        with patch.object(
            orchestrator.mirror_configurator,
            "configure_all",
            return_value={"npm": True, "bun": False, "uv": True},
        ):
            results = orchestrator.configure_mirrors()

        assert results["npm"] is True
        assert results["bun"] is False
        assert results["uv"] is True

    def test_configure_mirrors_dry_run(self, config, platform_info):
        """测试模拟运行模式下的镜像源配置"""
        orchestrator = InstallOrchestrator(config, platform_info, dry_run=True)

        results = orchestrator.configure_mirrors()

        # 模拟运行应该返回全部成功
        assert results["npm"] is True
        assert results["bun"] is True
        assert results["uv"] is True


class TestCreateProject:
    """测试项目创建"""

    def test_create_project_success(self, orchestrator, tmp_path):
        """测试成功创建项目"""
        project_name = "test-project"

        with patch("mono_kickstart.orchestrator.ProjectCreator") as MockCreator:
            mock_creator = Mock()
            mock_creator.create_project.return_value = (True, None)
            MockCreator.return_value = mock_creator

            success, error = orchestrator.create_project(project_name, force=False)

        assert success is True
        assert error is None

    def test_create_project_failure(self, orchestrator):
        """测试项目创建失败"""
        project_name = "test-project"

        with patch("mono_kickstart.orchestrator.ProjectCreator") as MockCreator:
            mock_creator = Mock()
            mock_creator.create_project.return_value = (False, "目录已存在")
            MockCreator.return_value = mock_creator

            success, error = orchestrator.create_project(project_name, force=False)

        assert success is False
        assert error == "目录已存在"

    def test_create_project_with_force(self, orchestrator):
        """测试强制创建项目"""
        project_name = "test-project"

        with patch("mono_kickstart.orchestrator.ProjectCreator") as MockCreator:
            mock_creator = Mock()
            mock_creator.create_project.return_value = (True, None)
            MockCreator.return_value = mock_creator

            success, error = orchestrator.create_project(project_name, force=True)

            # 验证 force 参数被传递
            mock_creator.create_project.assert_called_once_with(force=True)

        assert success is True

    def test_create_project_uses_config_name(self, orchestrator):
        """测试使用配置中的项目名称"""
        orchestrator.config.project.name = "config-project"

        with patch("mono_kickstart.orchestrator.ProjectCreator") as MockCreator:
            mock_creator = Mock()
            mock_creator.create_project.return_value = (True, None)
            MockCreator.return_value = mock_creator

            orchestrator.create_project(project_name=None, force=False)

            # 验证使用了配置中的名称
            MockCreator.assert_called_once()
            call_args = MockCreator.call_args[0]
            assert call_args[0] == "config-project"

    def test_create_project_uses_current_dir_name(self, orchestrator):
        """测试使用当前目录名称"""
        orchestrator.config.project.name = None

        with patch("mono_kickstart.orchestrator.ProjectCreator") as MockCreator:
            mock_creator = Mock()
            mock_creator.create_project.return_value = (True, None)
            MockCreator.return_value = mock_creator

            with patch("pathlib.Path.cwd") as mock_cwd:
                mock_cwd.return_value = Path("/home/user/my-project")

                orchestrator.create_project(project_name=None, force=False)

                # 验证使用了当前目录名称
                MockCreator.assert_called_once()
                call_args = MockCreator.call_args[0]
                assert call_args[0] == "my-project"

    def test_create_project_dry_run(self, config, platform_info):
        """测试模拟运行模式下的项目创建"""
        orchestrator = InstallOrchestrator(config, platform_info, dry_run=True)

        success, error = orchestrator.create_project("test-project", force=False)

        # 模拟运行应该返回成功
        assert success is True
        assert error is None


class TestRunInit:
    """测试完整初始化流程"""

    def test_run_init_success(self, orchestrator):
        """测试成功执行完整初始化流程"""
        # 设置启用的工具
        orchestrator.config.tools = {
            "node": ToolConfig(enabled=True),
            "bun": ToolConfig(enabled=True),
            "uv": ToolConfig(enabled=True),
        }

        # Mock 工具安装
        def create_mock_installer(tool_name):
            mock_installer = Mock()
            mock_installer.install.return_value = InstallReport(
                tool_name=tool_name, result=InstallResult.SUCCESS, message=f"{tool_name} 安装成功"
            )
            return mock_installer

        # Mock 镜像源配置
        with (
            patch.object(
                orchestrator,
                "_create_installer",
                side_effect=lambda name: create_mock_installer(name),
            ),
            patch.object(
                orchestrator.mirror_configurator, "configure_npm_mirror", return_value=True
            ),
            patch.object(
                orchestrator.mirror_configurator, "configure_bun_mirror", return_value=True
            ),
            patch.object(
                orchestrator.mirror_configurator, "configure_uv_mirror", return_value=True
            ),
            patch.object(orchestrator, "create_project", return_value=(True, None)),
        ):
            reports = orchestrator.run_init(project_name="test-project", force=False)

        # 验证工具安装报告
        assert "node" in reports
        assert "bun" in reports
        assert "uv" in reports

        # 验证镜像源配置报告
        assert "npm-mirror" in reports
        assert "bun-mirror" in reports
        assert "uv-mirror" in reports

        # 验证项目创建报告
        assert "project" in reports
        assert reports["project"].result == InstallResult.SUCCESS

    def test_run_init_only_configures_mirrors_for_successful_tools(self, orchestrator):
        """测试只为成功安装的工具配置镜像源"""
        # 设置启用的工具
        orchestrator.config.tools = {
            "node": ToolConfig(enabled=True),
            "bun": ToolConfig(enabled=True),
        }

        # Mock 工具安装：node 成功，bun 失败
        def create_mock_installer(tool_name):
            mock_installer = Mock()
            if tool_name == "node":
                mock_installer.install.return_value = InstallReport(
                    tool_name=tool_name,
                    result=InstallResult.SUCCESS,
                    message=f"{tool_name} 安装成功",
                )
            else:
                mock_installer.install.return_value = InstallReport(
                    tool_name=tool_name,
                    result=InstallResult.FAILED,
                    message=f"{tool_name} 安装失败",
                )
            return mock_installer

        with (
            patch.object(
                orchestrator,
                "_create_installer",
                side_effect=lambda name: create_mock_installer(name),
            ),
            patch.object(
                orchestrator.mirror_configurator, "configure_npm_mirror", return_value=True
            ) as mock_npm,
            patch.object(
                orchestrator.mirror_configurator, "configure_bun_mirror", return_value=True
            ) as mock_bun,
            patch.object(orchestrator, "create_project", return_value=(True, None)),
        ):
            reports = orchestrator.run_init(project_name="test-project", force=False)

        # 验证只配置了 npm 镜像源
        mock_npm.assert_called_once()
        mock_bun.assert_not_called()

        # 验证报告中有 npm-mirror 但没有 bun-mirror
        assert "npm-mirror" in reports
        assert "bun-mirror" not in reports

    def test_run_init_project_creation_failure_not_fatal(self, orchestrator):
        """测试项目创建失败不影响整体流程"""
        orchestrator.config.tools = {
            "node": ToolConfig(enabled=True),
        }

        def create_mock_installer(tool_name):
            mock_installer = Mock()
            mock_installer.install.return_value = InstallReport(
                tool_name=tool_name, result=InstallResult.SUCCESS, message=f"{tool_name} 安装成功"
            )
            return mock_installer

        with (
            patch.object(
                orchestrator,
                "_create_installer",
                side_effect=lambda name: create_mock_installer(name),
            ),
            patch.object(
                orchestrator.mirror_configurator, "configure_npm_mirror", return_value=True
            ),
            patch.object(orchestrator, "create_project", return_value=(False, "目录已存在")),
        ):
            reports = orchestrator.run_init(project_name="test-project", force=False)

        # 验证工具安装成功
        assert reports["node"].result == InstallResult.SUCCESS

        # 验证项目创建失败被记录
        assert reports["project"].result == InstallResult.FAILED
        assert reports["project"].error == "目录已存在"


class TestUpgradeTool:
    """测试单个工具升级"""

    def test_upgrade_tool_success(self, orchestrator):
        """测试成功升级工具"""
        mock_installer = Mock()
        mock_installer.upgrade.return_value = InstallReport(
            tool_name="node", result=InstallResult.SUCCESS, message="升级成功", version="21.0.0"
        )

        with patch.object(orchestrator, "_create_installer", return_value=mock_installer):
            report = orchestrator.upgrade_tool("node")

        assert report.result == InstallResult.SUCCESS
        assert report.tool_name == "node"
        assert report.version == "21.0.0"
        mock_installer.upgrade.assert_called_once()

    def test_upgrade_tool_failure(self, orchestrator):
        """测试工具升级失败"""
        mock_installer = Mock()
        mock_installer.upgrade.return_value = InstallReport(
            tool_name="bun", result=InstallResult.FAILED, message="升级失败", error="网络错误"
        )

        with patch.object(orchestrator, "_create_installer", return_value=mock_installer):
            report = orchestrator.upgrade_tool("bun")

        assert report.result == InstallResult.FAILED
        assert report.error == "网络错误"

    def test_upgrade_tool_invalid_name(self, orchestrator):
        """测试升级无效的工具名称"""
        report = orchestrator.upgrade_tool("invalid-tool")

        assert report.result == InstallResult.FAILED
        assert "无效的工具名称" in report.message

    def test_upgrade_tool_exception_handling(self, orchestrator):
        """测试升级过程中的异常处理"""
        mock_installer = Mock()
        mock_installer.upgrade.side_effect = Exception("意外错误")

        with patch.object(orchestrator, "_create_installer", return_value=mock_installer):
            report = orchestrator.upgrade_tool("uv")

        assert report.result == InstallResult.FAILED
        assert "异常" in report.message
        assert "意外错误" in report.error

    def test_upgrade_tool_dry_run(self, config, platform_info):
        """测试模拟运行模式下的升级"""
        orchestrator = InstallOrchestrator(config, platform_info, dry_run=True)

        report = orchestrator.upgrade_tool("node")

        assert report.result == InstallResult.SKIPPED
        assert "模拟运行" in report.message


class TestRunUpgrade:
    """测试升级流程"""

    def test_run_upgrade_single_tool(self, orchestrator):
        """测试升级单个工具"""
        mock_installer = Mock()
        mock_installer.upgrade.return_value = InstallReport(
            tool_name="node", result=InstallResult.SUCCESS, message="升级成功"
        )

        with patch.object(orchestrator, "_create_installer", return_value=mock_installer):
            reports = orchestrator.run_upgrade(tool_name="node")

        # 验证只升级了指定的工具
        assert len(reports) == 1
        assert "node" in reports
        assert reports["node"].result == InstallResult.SUCCESS

    def test_run_upgrade_all_tools(self, orchestrator):
        """测试升级所有已安装的工具"""
        # Mock 工具检测
        mock_tool_status = {
            "nvm": ToolStatus(name="nvm", installed=True, version="0.40.4"),
            "node": ToolStatus(name="node", installed=True, version="20.11.0"),
            "bun": ToolStatus(name="bun", installed=False),
            "uv": ToolStatus(name="uv", installed=True, version="0.1.0"),
        }

        # Mock 升级
        def create_mock_installer(tool_name):
            mock_installer = Mock()
            mock_installer.upgrade.return_value = InstallReport(
                tool_name=tool_name, result=InstallResult.SUCCESS, message=f"{tool_name} 升级成功"
            )
            return mock_installer

        with (
            patch.object(
                orchestrator.tool_detector, "detect_all_tools", return_value=mock_tool_status
            ),
            patch.object(
                orchestrator,
                "_create_installer",
                side_effect=lambda name: create_mock_installer(name),
            ),
        ):
            reports = orchestrator.run_upgrade(tool_name=None)

        # 验证只升级了已安装的工具
        assert len(reports) == 3
        assert "nvm" in reports
        assert "node" in reports
        assert "uv" in reports
        assert "bun" not in reports  # 未安装的工具不应该被升级

    def test_run_upgrade_partial_failure(self, orchestrator):
        """测试部分工具升级失败（容错性）"""
        # Mock 工具检测
        mock_tool_status = {
            "nvm": ToolStatus(name="nvm", installed=True, version="0.40.4"),
            "node": ToolStatus(name="node", installed=True, version="20.11.0"),
            "bun": ToolStatus(name="bun", installed=True, version="1.0.0"),
        }

        # Mock 升级：node 失败，其他成功
        def create_mock_installer(tool_name):
            mock_installer = Mock()
            if tool_name == "node":
                mock_installer.upgrade.return_value = InstallReport(
                    tool_name=tool_name,
                    result=InstallResult.FAILED,
                    message=f"{tool_name} 升级失败",
                    error="网络错误",
                )
            else:
                mock_installer.upgrade.return_value = InstallReport(
                    tool_name=tool_name,
                    result=InstallResult.SUCCESS,
                    message=f"{tool_name} 升级成功",
                )
            return mock_installer

        with (
            patch.object(
                orchestrator.tool_detector, "detect_all_tools", return_value=mock_tool_status
            ),
            patch.object(
                orchestrator,
                "_create_installer",
                side_effect=lambda name: create_mock_installer(name),
            ),
        ):
            reports = orchestrator.run_upgrade(tool_name=None)

        # 验证所有工具都被尝试升级
        assert len(reports) == 3

        # 验证失败的工具
        assert reports["node"].result == InstallResult.FAILED

        # 验证其他工具仍然成功
        assert reports["nvm"].result == InstallResult.SUCCESS
        assert reports["bun"].result == InstallResult.SUCCESS


class TestPrintSummary:
    """测试安装摘要打印"""

    def test_print_summary_all_success(self, orchestrator, capsys):
        """测试所有工具成功的摘要"""
        reports = {
            "nvm": InstallReport(
                tool_name="nvm", result=InstallResult.SUCCESS, message="安装成功", version="0.40.4"
            ),
            "node": InstallReport(
                tool_name="node",
                result=InstallResult.SUCCESS,
                message="安装成功",
                version="20.11.0",
            ),
        }

        orchestrator.print_summary(reports)

        captured = capsys.readouterr()
        output = captured.out

        # 验证摘要包含成功信息
        assert "安装摘要" in output
        assert "✓ 成功 (2)" in output
        assert "nvm" in output
        assert "node" in output
        assert "0.40.4" in output
        assert "20.11.0" in output

    def test_print_summary_with_skipped(self, orchestrator, capsys):
        """测试包含跳过工具的摘要"""
        reports = {
            "nvm": InstallReport(tool_name="nvm", result=InstallResult.SUCCESS, message="安装成功"),
            "node": InstallReport(
                tool_name="node", result=InstallResult.SKIPPED, message="已安装", version="20.11.0"
            ),
        }

        orchestrator.print_summary(reports)

        captured = capsys.readouterr()
        output = captured.out

        # 验证摘要包含跳过信息
        assert "○ 跳过 (1)" in output
        assert "node" in output
        assert "已安装" in output

    def test_print_summary_with_failures(self, orchestrator, capsys):
        """测试包含失败工具的摘要"""
        reports = {
            "nvm": InstallReport(tool_name="nvm", result=InstallResult.SUCCESS, message="安装成功"),
            "node": InstallReport(
                tool_name="node", result=InstallResult.FAILED, message="安装失败", error="网络错误"
            ),
        }

        orchestrator.print_summary(reports)

        captured = capsys.readouterr()
        output = captured.out

        # 验证摘要包含失败信息
        assert "✗ 失败 (1)" in output
        assert "node" in output
        assert "安装失败" in output
        assert "网络错误" in output

    def test_print_summary_mixed_results(self, orchestrator, capsys):
        """测试混合结果的摘要"""
        reports = {
            "nvm": InstallReport(tool_name="nvm", result=InstallResult.SUCCESS, message="安装成功"),
            "node": InstallReport(tool_name="node", result=InstallResult.SKIPPED, message="已安装"),
            "bun": InstallReport(
                tool_name="bun", result=InstallResult.FAILED, message="安装失败", error="权限错误"
            ),
        }

        orchestrator.print_summary(reports)

        captured = capsys.readouterr()
        output = captured.out

        # 验证摘要包含所有类型的信息
        assert "✓ 成功 (1)" in output
        assert "○ 跳过 (1)" in output
        assert "✗ 失败 (1)" in output
        assert "总计: 3 个任务" in output

    def test_print_summary_empty_reports(self, orchestrator, capsys):
        """测试空报告的摘要"""
        reports = {}

        orchestrator.print_summary(reports)

        captured = capsys.readouterr()
        output = captured.out

        # 验证摘要显示总计为 0
        assert "总计: 0 个任务" in output


class TestIdempotency:
    """测试幂等性"""

    def test_repeated_install_produces_same_result(self, orchestrator):
        """测试重复安装产生相同结果"""
        # 设置启用的工具
        orchestrator.config.tools = {
            "nvm": ToolConfig(enabled=True),
        }

        # Mock 安装器：第一次安装成功，第二次跳过
        call_count = [0]

        def create_mock_installer(tool_name):
            mock_installer = Mock()

            def mock_install():
                call_count[0] += 1
                if call_count[0] == 1:
                    return InstallReport(
                        tool_name=tool_name,
                        result=InstallResult.SUCCESS,
                        message=f"{tool_name} 安装成功",
                    )
                else:
                    return InstallReport(
                        tool_name=tool_name,
                        result=InstallResult.SKIPPED,
                        message=f"{tool_name} 已安装",
                    )

            mock_installer.install.side_effect = mock_install
            return mock_installer

        with patch.object(
            orchestrator, "_create_installer", side_effect=lambda name: create_mock_installer(name)
        ):
            # 第一次安装
            reports1 = orchestrator.install_all_tools()

            # 第二次安装
            reports2 = orchestrator.install_all_tools()

        # 验证第一次安装成功
        assert reports1["nvm"].result == InstallResult.SUCCESS

        # 验证第二次安装跳过（幂等性）
        assert reports2["nvm"].result == InstallResult.SKIPPED


class TestCreateInstaller:
    """测试安装器创建"""

    def test_create_installer_valid_tools(self, orchestrator):
        """测试创建有效工具的安装器"""
        valid_tools = [
            "nvm",
            "node",
            "conda",
            "bun",
            "uv",
            "claude-code",
            "copilot-cli",
            "codex",
            "opencode",
            "spec-kit",
            "bmad-method",
        ]

        for tool_name in valid_tools:
            installer = orchestrator._create_installer(tool_name)
            assert installer is not None

    def test_create_installer_invalid_tool(self, orchestrator):
        """测试创建无效工具的安装器"""
        installer = orchestrator._create_installer("invalid-tool")
        assert installer is None

    def test_create_installer_uses_config(self, orchestrator):
        """测试安装器使用配置"""
        orchestrator.config.tools["nvm"] = ToolConfig(enabled=True, version="0.40.4")

        installer = orchestrator._create_installer("nvm")

        assert installer is not None
        assert installer.config.version == "0.40.4"

    def test_create_installer_uses_platform_info(self, orchestrator):
        """测试安装器使用平台信息"""
        installer = orchestrator._create_installer("nvm")

        assert installer is not None
        assert installer.platform_info == orchestrator.platform_info


class TestErrorHandling:
    """测试错误处理"""

    def test_install_continues_after_error(self, orchestrator):
        """测试安装过程在错误后继续"""
        orchestrator.config.tools = {
            "nvm": ToolConfig(enabled=True),
            "node": ToolConfig(enabled=True),
            "bun": ToolConfig(enabled=True),
            "conda": ToolConfig(enabled=False),
            "uv": ToolConfig(enabled=False),
            "gh": ToolConfig(enabled=False),
            "claude-code": ToolConfig(enabled=False),
            "copilot-cli": ToolConfig(enabled=False),
            "codex": ToolConfig(enabled=False),
            "opencode": ToolConfig(enabled=False),
            "npx": ToolConfig(enabled=False),
            "uipro": ToolConfig(enabled=False),
            "spec-kit": ToolConfig(enabled=False),
            "bmad-method": ToolConfig(enabled=False),
        }

        # Mock 安装器：第二个工具抛出异常
        def create_mock_installer(tool_name):
            mock_installer = Mock()
            if tool_name == "node":
                mock_installer.install.side_effect = Exception("意外错误")
            else:
                mock_installer.install.return_value = InstallReport(
                    tool_name=tool_name,
                    result=InstallResult.SUCCESS,
                    message=f"{tool_name} 安装成功",
                )
            return mock_installer

        with patch.object(
            orchestrator, "_create_installer", side_effect=lambda name: create_mock_installer(name)
        ):
            reports = orchestrator.install_all_tools()

        # 验证所有工具都被尝试
        assert len(reports) == 3

        # 验证异常被捕获并记录
        assert reports["node"].result == InstallResult.FAILED
        assert "异常" in reports["node"].message

        # 验证其他工具仍然成功
        assert reports["nvm"].result == InstallResult.SUCCESS
        assert reports["bun"].result == InstallResult.SUCCESS

    def test_error_message_includes_tool_name(self, orchestrator):
        """测试错误信息包含工具名称"""
        report = orchestrator.install_tool("invalid-tool")

        assert report.result == InstallResult.FAILED
        assert "invalid-tool" in report.message or "invalid-tool" in str(report.error)

    def test_error_message_includes_error_details(self, orchestrator):
        """测试错误信息包含错误详情"""
        mock_installer = Mock()
        mock_installer.install.side_effect = Exception("详细错误信息")

        with patch.object(orchestrator, "_create_installer", return_value=mock_installer):
            report = orchestrator.install_tool("nvm")

        assert report.result == InstallResult.FAILED
        assert "详细错误信息" in report.error


class TestInstallOrderConstant:
    """测试安装顺序常量"""

    def test_install_order_is_defined(self):
        """测试安装顺序常量已定义"""
        assert INSTALL_ORDER is not None
        assert isinstance(INSTALL_ORDER, list)
        assert len(INSTALL_ORDER) > 0

    def test_install_order_contains_expected_tools(self):
        """测试安装顺序包含预期的工具"""
        expected_tools = [
            "nvm",
            "node",
            "conda",
            "bun",
            "uv",
            "claude-code",
            "copilot-cli",
            "codex",
            "opencode",
            "spec-kit",
            "bmad-method",
        ]

        for tool in expected_tools:
            assert tool in INSTALL_ORDER

    def test_install_order_respects_dependencies(self):
        """测试安装顺序遵循依赖关系"""
        # NVM 必须在 Node.js 之前
        assert INSTALL_ORDER.index("nvm") < INSTALL_ORDER.index("node")

        # uv 必须在 spec-kit 之前
        assert INSTALL_ORDER.index("uv") < INSTALL_ORDER.index("spec-kit")

        # Node.js 必须在 bmad-method 之前
        assert INSTALL_ORDER.index("node") < INSTALL_ORDER.index("bmad-method")

        # Node.js 必须在 copilot-cli 之前（copilot-cli 依赖 Node.js 22+）
        assert INSTALL_ORDER.index("node") < INSTALL_ORDER.index("copilot-cli")


class TestCopilotCLIOrchestratorIntegration:
    """测试 Copilot CLI 编排器集成

    **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
    """

    def test_install_order_contains_copilot_cli(self):
        """测试 INSTALL_ORDER 中包含 copilot-cli

        **Validates: Requirements 7.1**
        """
        assert "copilot-cli" in INSTALL_ORDER

    def test_copilot_cli_after_node(self):
        """测试 copilot-cli 在 node 之后

        Copilot CLI 依赖 Node.js 22+，因此必须在 node 之后安装。

        **Validates: Requirements 7.2**
        """
        node_index = INSTALL_ORDER.index("node")
        copilot_index = INSTALL_ORDER.index("copilot-cli")

        assert copilot_index > node_index, "copilot-cli 必须在 node 之后安装（依赖 Node.js 22+）"

    def test_create_installer_creates_copilot_cli_installer(self, orchestrator):
        """测试 _create_installer() 能正确创建 CopilotCLIInstaller 实例

        **Validates: Requirements 7.3**
        """
        from mono_kickstart.installers.copilot_installer import CopilotCLIInstaller

        installer = orchestrator._create_installer("copilot-cli")

        assert installer is not None
        assert isinstance(installer, CopilotCLIInstaller)

    def test_create_installer_passes_config_to_copilot_cli_installer(self, orchestrator):
        """测试 _create_installer() 将配置传递给 CopilotCLIInstaller

        **Validates: Requirements 7.3**
        """
        # 设置 copilot-cli 配置
        orchestrator.config.tools["copilot-cli"] = ToolConfig(enabled=True, version="1.0.0")

        installer = orchestrator._create_installer("copilot-cli")

        assert installer is not None
        assert installer.config.enabled is True
        assert installer.config.version == "1.0.0"

    def test_create_installer_passes_platform_info_to_copilot_cli_installer(self, orchestrator):
        """测试 _create_installer() 将平台信息传递给 CopilotCLIInstaller

        **Validates: Requirements 7.3**
        """
        installer = orchestrator._create_installer("copilot-cli")

        assert installer is not None
        assert installer.platform_info == orchestrator.platform_info

    def test_install_all_tools_includes_copilot_cli(self, orchestrator):
        """测试 install_all_tools() 包含 copilot-cli

        **Validates: Requirements 7.4**
        """
        # 启用 copilot-cli
        orchestrator.config.tools["copilot-cli"] = ToolConfig(enabled=True)

        # Mock 所有安装器
        with patch.object(orchestrator, "_create_installer") as mock_create:
            mock_installer = Mock()
            mock_installer.install.return_value = InstallReport(
                tool_name="copilot-cli", result=InstallResult.SUCCESS, message="安装成功"
            )
            mock_create.return_value = mock_installer

            reports = orchestrator.install_all_tools()

        # 验证 copilot-cli 被安装
        assert "copilot-cli" in reports

    def test_install_all_tools_respects_copilot_cli_order(self, orchestrator):
        """测试 install_all_tools() 按正确顺序安装 copilot-cli

        验证 copilot-cli 在 node 之后安装。

        **Validates: Requirements 7.2, 7.4**
        """
        # 启用 node 和 copilot-cli
        orchestrator.config.tools = {
            "node": ToolConfig(enabled=True),
            "copilot-cli": ToolConfig(enabled=True),
        }

        install_sequence = []

        def track_install(tool_name):
            """追踪安装顺序"""

            def mock_install():
                install_sequence.append(tool_name)
                return InstallReport(
                    tool_name=tool_name, result=InstallResult.SUCCESS, message="安装成功"
                )

            return mock_install

        # Mock _create_installer 以追踪安装顺序
        original_create = orchestrator._create_installer

        def mock_create_installer(tool_name):
            installer = original_create(tool_name)
            if installer:
                installer.install = track_install(tool_name)
            return installer

        with patch.object(orchestrator, "_create_installer", side_effect=mock_create_installer):
            orchestrator.install_all_tools()

        # 验证安装顺序
        assert "node" in install_sequence
        assert "copilot-cli" in install_sequence
        assert install_sequence.index("node") < install_sequence.index("copilot-cli"), (
            "node 必须在 copilot-cli 之前安装"
        )
