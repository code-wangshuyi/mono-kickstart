"""完整升级流程集成测试"""

import pytest
from unittest.mock import patch, MagicMock

from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell
from mono_kickstart.config import Config, ConfigManager, ToolConfig
from mono_kickstart.orchestrator import InstallOrchestrator
from mono_kickstart.installer_base import InstallResult, InstallReport
from mono_kickstart.tool_detector import ToolStatus


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
    
    # 启用所有工具
    for tool_name in ["nvm", "node", "conda", "bun", "uv", "claude-code", "codex", "spec-kit", "bmad-method"]:
        config.tools[tool_name] = ToolConfig(enabled=True)
    
    return config


class TestUpgradeFlowIntegration:
    """升级流程集成测试"""
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    def test_upgrade_all_tools(
        self,
        mock_tool_detector_class,
        mock_platform_info,
        test_config
    ):
        """测试升级所有工具"""
        # Mock 工具检测器 - 所有工具都已安装
        mock_detector = MagicMock()
        mock_detector.detect_nvm.return_value = ToolStatus(name="nvm", installed=True, version="0.39.0")
        mock_detector.detect_node.return_value = ToolStatus(name="node", installed=True, version="18.17.0")
        mock_detector.detect_bun.return_value = ToolStatus(name="bun", installed=True, version="1.0.0")
        mock_detector.detect_uv.return_value = ToolStatus(name="uv", installed=True, version="0.1.0")
        mock_tool_detector_class.return_value = mock_detector
        
        with patch('mono_kickstart.orchestrator.NVMInstaller') as mock_nvm, \
             patch('mono_kickstart.orchestrator.NodeInstaller') as mock_node, \
             patch('mono_kickstart.orchestrator.BunInstaller') as mock_bun, \
             patch('mono_kickstart.orchestrator.UVInstaller') as mock_uv:
            
            # 配置升级器返回成功
            for mock_installer in [mock_nvm, mock_node, mock_bun, mock_uv]:
                mock_instance = MagicMock()
                mock_instance.upgrade.return_value = InstallReport(
                    tool_name="test",
                    result=InstallResult.SUCCESS,
                    message="升级成功",
                    version="latest"
                )
                mock_installer.return_value = mock_instance
            
            # 创建编排器
            orchestrator = InstallOrchestrator(
                config=test_config,
                platform_info=mock_platform_info,
                dry_run=False
            )
            
            # 执行升级（所有工具）
            reports = orchestrator.run_upgrade(tool_name=None)
            
            # 验证所有已安装的工具都被升级
            assert "nvm" in reports
            assert "node" in reports
            assert "bun" in reports
            assert "uv" in reports
            
            # 验证所有工具都成功升级
            for tool_name, report in reports.items():
                assert report.result == InstallResult.SUCCESS
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    def test_upgrade_single_tool(
        self,
        mock_tool_detector_class,
        mock_platform_info,
        test_config
    ):
        """测试升级单个工具"""
        # Mock 工具检测器
        mock_detector = MagicMock()
        mock_detector.detect_node.return_value = ToolStatus(name="node", installed=True, version="18.17.0")
        mock_tool_detector_class.return_value = mock_detector
        
        with patch('mono_kickstart.orchestrator.NodeInstaller') as mock_node:
            # 配置 Node.js 升级器
            mock_node_instance = MagicMock()
            mock_node_instance.upgrade.return_value = InstallReport(
                tool_name="node",
                result=InstallResult.SUCCESS,
                message="升级成功",
                version="20.0.0"
            )
            mock_node.return_value = mock_node_instance
            
            # 创建编排器
            orchestrator = InstallOrchestrator(
                config=test_config,
                platform_info=mock_platform_info,
                dry_run=False
            )
            
            # 执行升级（仅 Node.js）
            reports = orchestrator.run_upgrade(tool_name="node")
            
            # 验证只有 Node.js 被升级
            assert len(reports) == 1
            assert "node" in reports
            assert reports["node"].result == InstallResult.SUCCESS
            assert reports["node"].version == "20.0.0"
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    def test_upgrade_tool_not_installed(
        self,
        mock_tool_detector_class,
        mock_platform_info,
        test_config
    ):
        """测试升级未安装的工具"""
        # Mock 工具检测器 - 工具未安装
        mock_detector = MagicMock()
        mock_detector.detect_bun.return_value = ToolStatus(name="bun", installed=False)
        mock_tool_detector_class.return_value = mock_detector
        
        # 创建编排器
        orchestrator = InstallOrchestrator(
            config=test_config,
            platform_info=mock_platform_info,
            dry_run=False
        )
        
        # 执行升级（Bun 未安装）
        reports = orchestrator.run_upgrade(tool_name="bun")
        
        # 验证未安装的工具被跳过
        assert "bun" in reports
        assert reports["bun"].result == InstallResult.SKIPPED
        assert "未安装" in reports["bun"].message or "not installed" in reports["bun"].message.lower()
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    def test_upgrade_with_failures(
        self,
        mock_tool_detector_class,
        mock_platform_info,
        test_config
    ):
        """测试升级流程（部分工具升级失败）"""
        # Mock 工具检测器
        mock_detector = MagicMock()
        mock_detector.detect_nvm.return_value = ToolStatus(name="nvm", installed=True, version="0.39.0")
        mock_detector.detect_node.return_value = ToolStatus(name="node", installed=True, version="18.17.0")
        mock_detector.detect_bun.return_value = ToolStatus(name="bun", installed=True, version="1.0.0")
        mock_tool_detector_class.return_value = mock_detector
        
        with patch('mono_kickstart.orchestrator.NVMInstaller') as mock_nvm, \
             patch('mono_kickstart.orchestrator.NodeInstaller') as mock_node, \
             patch('mono_kickstart.orchestrator.BunInstaller') as mock_bun:
            
            # NVM 升级成功
            mock_nvm_instance = MagicMock()
            mock_nvm_instance.upgrade.return_value = InstallReport(
                tool_name="nvm",
                result=InstallResult.SUCCESS,
                message="升级成功"
            )
            mock_nvm.return_value = mock_nvm_instance
            
            # Node.js 升级失败
            mock_node_instance = MagicMock()
            mock_node_instance.upgrade.return_value = InstallReport(
                tool_name="node",
                result=InstallResult.FAILED,
                message="升级失败",
                error="Network timeout"
            )
            mock_node.return_value = mock_node_instance
            
            # Bun 升级成功
            mock_bun_instance = MagicMock()
            mock_bun_instance.upgrade.return_value = InstallReport(
                tool_name="bun",
                result=InstallResult.SUCCESS,
                message="升级成功"
            )
            mock_bun.return_value = mock_bun_instance
            
            # 创建编排器
            orchestrator = InstallOrchestrator(
                config=test_config,
                platform_info=mock_platform_info,
                dry_run=False
            )
            
            # 执行升级
            reports = orchestrator.run_upgrade(tool_name=None)
            
            # 验证结果
            assert reports["nvm"].result == InstallResult.SUCCESS
            assert reports["node"].result == InstallResult.FAILED
            assert reports["bun"].result == InstallResult.SUCCESS
            
            # 验证失败的工具有错误信息
            assert reports["node"].error is not None
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    def test_upgrade_dry_run(
        self,
        mock_tool_detector_class,
        mock_platform_info,
        test_config
    ):
        """测试升级流程（模拟运行模式）"""
        # Mock 工具检测器
        mock_detector = MagicMock()
        mock_detector.detect_nvm.return_value = ToolStatus(name="nvm", installed=True, version="0.39.0")
        mock_detector.detect_node.return_value = ToolStatus(name="node", installed=True, version="18.17.0")
        mock_tool_detector_class.return_value = mock_detector
        
        # 创建编排器（dry_run=True）
        orchestrator = InstallOrchestrator(
            config=test_config,
            platform_info=mock_platform_info,
            dry_run=True
        )
        
        # 执行升级
        reports = orchestrator.run_upgrade(tool_name=None)
        
        # 验证在 dry_run 模式下，返回报告但不执行实际升级
        assert len(reports) > 0
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    def test_upgrade_respects_config(
        self,
        mock_tool_detector_class,
        mock_platform_info
    ):
        """测试升级流程尊重配置（禁用的工具不升级）"""
        # 创建配置 - 部分工具禁用
        config = Config()
        config.tools["nvm"] = ToolConfig(enabled=True)
        config.tools["node"] = ToolConfig(enabled=False)  # 禁用
        config.tools["bun"] = ToolConfig(enabled=True)
        
        # Mock 工具检测器
        mock_detector = MagicMock()
        mock_detector.detect_nvm.return_value = ToolStatus(name="nvm", installed=True)
        mock_detector.detect_node.return_value = ToolStatus(name="node", installed=True)
        mock_detector.detect_bun.return_value = ToolStatus(name="bun", installed=True)
        mock_tool_detector_class.return_value = mock_detector
        
        with patch('mono_kickstart.orchestrator.NVMInstaller') as mock_nvm, \
             patch('mono_kickstart.orchestrator.BunInstaller') as mock_bun:
            
            # 配置升级器
            for mock_installer in [mock_nvm, mock_bun]:
                mock_instance = MagicMock()
                mock_instance.upgrade.return_value = InstallReport(
                    tool_name="test",
                    result=InstallResult.SUCCESS,
                    message="升级成功"
                )
                mock_installer.return_value = mock_instance
            
            # 创建编排器
            orchestrator = InstallOrchestrator(
                config=config,
                platform_info=mock_platform_info,
                dry_run=False
            )
            
            # 执行升级
            reports = orchestrator.run_upgrade(tool_name=None)
            
            # 验证启用的工具被升级
            assert "nvm" in reports
            assert "bun" in reports
            
            # 验证禁用的工具不在报告中（或被跳过）
            if "node" in reports:
                assert reports["node"].result == InstallResult.SKIPPED
    
    @patch('mono_kickstart.orchestrator.ToolDetector')
    def test_upgrade_nonexistent_tool(
        self,
        mock_tool_detector_class,
        mock_platform_info,
        test_config
    ):
        """测试升级不存在的工具"""
        # Mock 工具检测器
        mock_detector = MagicMock()
        mock_tool_detector_class.return_value = mock_detector
        
        # 创建编排器
        orchestrator = InstallOrchestrator(
            config=test_config,
            platform_info=mock_platform_info,
            dry_run=False
        )
        
        # 执行升级（不存在的工具）
        reports = orchestrator.run_upgrade(tool_name="nonexistent-tool")
        
        # 验证返回错误或跳过
        assert "nonexistent-tool" in reports
        assert reports["nonexistent-tool"].result in [InstallResult.FAILED, InstallResult.SKIPPED]
