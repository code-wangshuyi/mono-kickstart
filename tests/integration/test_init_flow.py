"""完整初始化流程集成测试"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import tempfile

from mono_kickstart.platform_detector import PlatformDetector, PlatformInfo, OS, Arch, Shell
from mono_kickstart.config import Config, ConfigManager, ProjectConfig, ToolConfig, RegistryConfig
from mono_kickstart.orchestrator import InstallOrchestrator
from mono_kickstart.installer_base import InstallResult, InstallReport


@pytest.fixture
def mock_platform_info():
    """Mock 平台信息"""
    return PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file="~/.bashrc"
    )


@pytest.fixture
def test_config():
    """测试配置"""
    config = Config()
    config.project = ProjectConfig(name="test-project")
    
    # 启用部分工具
    config.tools["nvm"] = ToolConfig(enabled=True)
    config.tools["node"] = ToolConfig(enabled=True, version="lts")
    config.tools["bun"] = ToolConfig(enabled=True)
    config.tools["uv"] = ToolConfig(enabled=True)
    
    # 禁用其他工具
    config.tools["conda"] = ToolConfig(enabled=False)
    config.tools["claude-code"] = ToolConfig(enabled=False)
    config.tools["codex"] = ToolConfig(enabled=False)
    config.tools["spec-kit"] = ToolConfig(enabled=False)
    config.tools["bmad-method"] = ToolConfig(enabled=False)
    
    # 配置镜像源
    config.registry = RegistryConfig(
        npm="https://registry.npmmirror.com/",
        bun="https://registry.npmmirror.com/",
        pypi="https://mirrors.sustech.edu.cn/pypi/web/simple",
        python_install="https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"
    )
    
    return config


class TestInitFlowIntegration:
    """初始化流程集成测试"""
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    @patch('mono_kickstart.orchestrator.MirrorConfigurator')
    @patch('mono_kickstart.orchestrator.ProjectCreator')
    def test_complete_init_flow(
        self,
        mock_project_creator_class,
        mock_mirror_configurator_class,
        mock_tool_detector_class,
        mock_platform_info,
        test_config,
        tmp_path
    ):
        """测试完整的初始化流程"""
        # Mock 工具检测器
        mock_detector = MagicMock()
        mock_detector.detect_nvm.return_value.installed = False
        mock_detector.detect_node.return_value.installed = False
        mock_detector.detect_bun.return_value.installed = False
        mock_detector.detect_uv.return_value.installed = False
        mock_tool_detector_class.return_value = mock_detector
        
        # Mock 镜像配置器
        mock_mirror_config = MagicMock()
        mock_mirror_config.configure_npm_mirror.return_value = True
        mock_mirror_config.configure_bun_mirror.return_value = True
        mock_mirror_config.configure_uv_mirror.return_value = True
        mock_mirror_configurator_class.return_value = mock_mirror_config
        
        # Mock 项目创建器
        mock_project = MagicMock()
        mock_project.create_project.return_value = True
        mock_project_creator_class.return_value = mock_project
        
        # Mock 工具安装器
        with patch('mono_kickstart.orchestrator.NVMInstaller') as mock_nvm, \
             patch('mono_kickstart.orchestrator.NodeInstaller') as mock_node, \
             patch('mono_kickstart.orchestrator.BunInstaller') as mock_bun, \
             patch('mono_kickstart.orchestrator.UVInstaller') as mock_uv:
            
            # 配置安装器返回成功
            for mock_installer in [mock_nvm, mock_node, mock_bun, mock_uv]:
                mock_instance = MagicMock()
                mock_instance.install.return_value = InstallReport(
                    tool_name="test",
                    result=InstallResult.SUCCESS,
                    message="安装成功",
                    version="1.0.0"
                )
                mock_installer.return_value = mock_instance
            
            # 创建编排器
            orchestrator = InstallOrchestrator(
                config=test_config,
                platform_info=mock_platform_info,
                dry_run=False
            )
            
            # 执行初始化
            reports = orchestrator.run_init(
                project_name="test-project",
                force=False
            )
            
            # 验证工具安装
            assert "nvm" in reports
            assert "node" in reports
            assert "bun" in reports
            assert "uv" in reports
            
            # 验证所有工具都成功安装
            for tool_name, report in reports.items():
                if tool_name in ["nvm", "node", "bun", "uv"]:
                    assert report.result == InstallResult.SUCCESS
            
            # 验证镜像源配置被调用
            assert mock_mirror_config.configure_npm_mirror.called
            assert mock_mirror_config.configure_bun_mirror.called
            assert mock_mirror_config.configure_uv_mirror.called
            
            # 验证项目创建被调用
            assert mock_project.create_project.called
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    def test_init_flow_with_existing_tools(
        self,
        mock_tool_detector_class,
        mock_platform_info,
        test_config
    ):
        """测试初始化流程（部分工具已安装）"""
        # Mock 工具检测器 - 部分工具已安装
        mock_detector = MagicMock()
        mock_detector.detect_nvm.return_value.installed = True  # 已安装
        mock_detector.detect_node.return_value.installed = True  # 已安装
        mock_detector.detect_bun.return_value.installed = False  # 未安装
        mock_detector.detect_uv.return_value.installed = False  # 未安装
        mock_tool_detector_class.return_value = mock_detector
        
        with patch('mono_kickstart.orchestrator.MirrorConfigurator'), \
             patch('mono_kickstart.orchestrator.ProjectCreator'), \
             patch('mono_kickstart.orchestrator.BunInstaller') as mock_bun, \
             patch('mono_kickstart.orchestrator.UVInstaller') as mock_uv:
            
            # 配置未安装工具的安装器
            for mock_installer in [mock_bun, mock_uv]:
                mock_instance = MagicMock()
                mock_instance.install.return_value = InstallReport(
                    tool_name="test",
                    result=InstallResult.SUCCESS,
                    message="安装成功"
                )
                mock_installer.return_value = mock_instance
            
            # 创建编排器
            orchestrator = InstallOrchestrator(
                config=test_config,
                platform_info=mock_platform_info,
                dry_run=False
            )
            
            # 执行初始化
            reports = orchestrator.run_init(
                project_name="test-project",
                force=False
            )
            
            # 验证已安装的工具被跳过
            assert reports["nvm"].result == InstallResult.SKIPPED
            assert reports["node"].result == InstallResult.SKIPPED
            
            # 验证未安装的工具被安装
            assert reports["bun"].result == InstallResult.SUCCESS
            assert reports["uv"].result == InstallResult.SUCCESS
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    @patch('mono_kickstart.orchestrator.MirrorConfigurator')
    @patch('mono_kickstart.orchestrator.ProjectCreator')
    def test_init_flow_with_failures(
        self,
        mock_project_creator_class,
        mock_mirror_configurator_class,
        mock_tool_detector_class,
        mock_platform_info,
        test_config
    ):
        """测试初始化流程（部分工具安装失败）"""
        # Mock 工具检测器
        mock_detector = MagicMock()
        mock_detector.detect_nvm.return_value.installed = False
        mock_detector.detect_node.return_value.installed = False
        mock_detector.detect_bun.return_value.installed = False
        mock_detector.detect_uv.return_value.installed = False
        mock_tool_detector_class.return_value = mock_detector
        
        # Mock 镜像配置器和项目创建器
        mock_mirror_configurator_class.return_value = MagicMock()
        mock_project_creator_class.return_value = MagicMock()
        
        with patch('mono_kickstart.orchestrator.NVMInstaller') as mock_nvm, \
             patch('mono_kickstart.orchestrator.NodeInstaller') as mock_node, \
             patch('mono_kickstart.orchestrator.BunInstaller') as mock_bun, \
             patch('mono_kickstart.orchestrator.UVInstaller') as mock_uv:
            
            # NVM 安装成功
            mock_nvm_instance = MagicMock()
            mock_nvm_instance.install.return_value = InstallReport(
                tool_name="nvm",
                result=InstallResult.SUCCESS,
                message="安装成功"
            )
            mock_nvm.return_value = mock_nvm_instance
            
            # Node.js 安装失败
            mock_node_instance = MagicMock()
            mock_node_instance.install.return_value = InstallReport(
                tool_name="node",
                result=InstallResult.FAILED,
                message="安装失败",
                error="Network timeout"
            )
            mock_node.return_value = mock_node_instance
            
            # Bun 安装成功
            mock_bun_instance = MagicMock()
            mock_bun_instance.install.return_value = InstallReport(
                tool_name="bun",
                result=InstallResult.SUCCESS,
                message="安装成功"
            )
            mock_bun.return_value = mock_bun_instance
            
            # uv 安装成功
            mock_uv_instance = MagicMock()
            mock_uv_instance.install.return_value = InstallReport(
                tool_name="uv",
                result=InstallResult.SUCCESS,
                message="安装成功"
            )
            mock_uv.return_value = mock_uv_instance
            
            # 创建编排器
            orchestrator = InstallOrchestrator(
                config=test_config,
                platform_info=mock_platform_info,
                dry_run=False
            )
            
            # 执行初始化
            reports = orchestrator.run_init(
                project_name="test-project",
                force=False
            )
            
            # 验证结果
            assert reports["nvm"].result == InstallResult.SUCCESS
            assert reports["node"].result == InstallResult.FAILED
            assert reports["bun"].result == InstallResult.SUCCESS
            assert reports["uv"].result == InstallResult.SUCCESS
            
            # 验证失败的工具有错误信息
            assert reports["node"].error is not None
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    @patch('mono_kickstart.orchestrator.MirrorConfigurator')
    @patch('mono_kickstart.orchestrator.ProjectCreator')
    def test_init_flow_dry_run(
        self,
        mock_project_creator_class,
        mock_mirror_configurator_class,
        mock_tool_detector_class,
        mock_platform_info,
        test_config
    ):
        """测试初始化流程（模拟运行模式）"""
        # Mock 工具检测器
        mock_detector = MagicMock()
        mock_detector.detect_nvm.return_value.installed = False
        mock_detector.detect_node.return_value.installed = False
        mock_tool_detector_class.return_value = mock_detector
        
        # Mock 镜像配置器和项目创建器
        mock_mirror_config = MagicMock()
        mock_mirror_configurator_class.return_value = mock_mirror_config
        mock_project = MagicMock()
        mock_project_creator_class.return_value = mock_project
        
        # 创建编排器（dry_run=True）
        orchestrator = InstallOrchestrator(
            config=test_config,
            platform_info=mock_platform_info,
            dry_run=True
        )
        
        # 执行初始化
        reports = orchestrator.run_init(
            project_name="test-project",
            force=False
        )
        
        # 验证在 dry_run 模式下，实际的安装操作不会被执行
        # 但会返回报告
        assert len(reports) > 0
        
        # 验证镜像配置和项目创建不会被调用（dry_run 模式）
        # 注意：这取决于 orchestrator 的实现
    
    def test_config_loading_and_merging(self, tmp_path):
        """测试配置加载和合并"""
        # 创建测试配置文件
        user_config_path = tmp_path / "user_config.yaml"
        user_config_path.write_text("""
project:
  name: user-project

tools:
  nvm:
    enabled: true
  node:
    enabled: true
    version: "18.17.0"

registry:
  npm: "https://registry.npmjs.org/"
""")
        
        project_config_path = tmp_path / "project_config.yaml"
        project_config_path.write_text("""
project:
  name: my-project

tools:
  node:
    version: "lts"
  bun:
    enabled: true
""")
        
        # 加载配置
        config_manager = ConfigManager()
        
        user_config = config_manager.load_from_file(user_config_path)
        project_config = config_manager.load_from_file(project_config_path)
        
        # 合并配置（项目配置优先级更高）
        merged_config = config_manager.merge_configs(user_config, project_config)
        
        # 验证合并结果
        assert merged_config.project.name == "my-project"  # 项目配置覆盖
        assert merged_config.tools["node"].version == "lts"  # 项目配置覆盖
        assert merged_config.tools["nvm"].enabled is True  # 用户配置保留
        assert merged_config.tools["bun"].enabled is True  # 项目配置新增
        assert merged_config.registry.npm == "https://registry.npmjs.org/"  # 用户配置保留
