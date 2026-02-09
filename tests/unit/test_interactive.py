"""交互式配置器单元测试"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from mono_kickstart.interactive import InteractiveConfigurator, AVAILABLE_TOOLS
from mono_kickstart.config import Config, ProjectConfig, ToolConfig, RegistryConfig


class TestInteractiveConfigurator:
    """交互式配置器测试"""
    
    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        config = Config()
        config.project.name = "test-project"
        
        configurator = InteractiveConfigurator(config)
        
        assert configurator.default_config == config
        assert configurator.default_config.project.name == "test-project"
    
    def test_init_without_default_config(self):
        """测试不提供默认配置初始化"""
        configurator = InteractiveConfigurator()
        
        assert configurator.default_config is not None
        assert isinstance(configurator.default_config, Config)
    
    @patch('mono_kickstart.interactive.questionary.text')
    def test_ask_project_name_with_default(self, mock_text):
        """测试询问项目名称（使用默认值）"""
        config = Config()
        config.project.name = "my-project"
        configurator = InteractiveConfigurator(config)
        
        mock_text.return_value.ask.return_value = "my-project"
        
        result = configurator.ask_project_name()
        
        assert result == "my-project"
        mock_text.assert_called_once()
        # 验证默认值被传递
        call_kwargs = mock_text.call_args[1]
        assert call_kwargs['default'] == "my-project"
    
    @patch('mono_kickstart.interactive.questionary.text')
    @patch('mono_kickstart.interactive.Path.cwd')
    def test_ask_project_name_without_default(self, mock_cwd, mock_text):
        """测试询问项目名称（无默认值，使用当前目录名）"""
        mock_cwd.return_value.name = "current-dir"
        configurator = InteractiveConfigurator()
        
        mock_text.return_value.ask.return_value = "new-project"
        
        result = configurator.ask_project_name()
        
        assert result == "new-project"
        # 验证使用当前目录名作为默认值
        call_kwargs = mock_text.call_args[1]
        assert call_kwargs['default'] == "current-dir"
    
    @patch('mono_kickstart.interactive.questionary.checkbox')
    def test_ask_tools_to_install_all_selected(self, mock_checkbox):
        """测试询问工具选择（全选）"""
        configurator = InteractiveConfigurator()
        
        all_tools = [tool["value"] for tool in AVAILABLE_TOOLS]
        mock_checkbox.return_value.ask.return_value = all_tools
        
        result = configurator.ask_tools_to_install()
        
        assert result == all_tools
        assert len(result) == len(AVAILABLE_TOOLS)
    
    @patch('mono_kickstart.interactive.questionary.checkbox')
    def test_ask_tools_to_install_partial_selected(self, mock_checkbox):
        """测试询问工具选择（部分选择）"""
        configurator = InteractiveConfigurator()
        
        selected_tools = ["nvm", "node", "bun"]
        mock_checkbox.return_value.ask.return_value = selected_tools
        
        result = configurator.ask_tools_to_install()
        
        assert result == selected_tools
        assert len(result) == 3
    
    @patch('mono_kickstart.interactive.questionary.checkbox')
    def test_ask_tools_to_install_none_selected(self, mock_checkbox):
        """测试询问工具选择（未选择）"""
        configurator = InteractiveConfigurator()
        
        mock_checkbox.return_value.ask.return_value = []
        
        result = configurator.ask_tools_to_install()
        
        assert result == []
    
    @patch('mono_kickstart.interactive.questionary.checkbox')
    def test_ask_tools_respects_default_config(self, mock_checkbox):
        """测试工具选择尊重默认配置"""
        config = Config()
        config.tools["nvm"] = ToolConfig(enabled=False)
        config.tools["node"] = ToolConfig(enabled=True)
        
        configurator = InteractiveConfigurator(config)
        mock_checkbox.return_value.ask.return_value = ["node"]
        
        configurator.ask_tools_to_install()
        
        # 验证 checkbox 被调用，并检查选项
        mock_checkbox.assert_called_once()
        call_args = mock_checkbox.call_args[1]
        choices = call_args['choices']
        
        # 查找 nvm 和 node 的选项
        nvm_choice = next((c for c in choices if c["value"] == "nvm"), None)
        node_choice = next((c for c in choices if c["value"] == "node"), None)
        
        assert nvm_choice is not None
        assert node_choice is not None
        assert nvm_choice["checked"] == False
        assert node_choice["checked"] == True
    
    @patch('mono_kickstart.interactive.questionary.select')
    def test_ask_node_version_lts(self, mock_select):
        """测试询问 Node.js 版本（选择 LTS）"""
        configurator = InteractiveConfigurator()
        
        mock_select.return_value.ask.return_value = "LTS (推荐)"
        
        result = configurator.ask_node_version()
        
        assert result == "lts"
    
    @patch('mono_kickstart.interactive.questionary.select')
    def test_ask_node_version_latest(self, mock_select):
        """测试询问 Node.js 版本（选择 Latest）"""
        configurator = InteractiveConfigurator()
        
        mock_select.return_value.ask.return_value = "Latest (最新)"
        
        result = configurator.ask_node_version()
        
        assert result == "latest"
    
    @patch('mono_kickstart.interactive.questionary.text')
    @patch('mono_kickstart.interactive.questionary.select')
    def test_ask_node_version_custom(self, mock_select, mock_text):
        """测试询问 Node.js 版本（指定版本）"""
        configurator = InteractiveConfigurator()
        
        mock_select.return_value.ask.return_value = "指定版本"
        mock_text.return_value.ask.return_value = "18.17.0"
        
        result = configurator.ask_node_version()
        
        assert result == "18.17.0"
        mock_text.assert_called_once()
    
    @patch('mono_kickstart.interactive.questionary.text')
    def test_ask_python_version(self, mock_text):
        """测试询问 Python 版本"""
        configurator = InteractiveConfigurator()
        
        mock_text.return_value.ask.return_value = "3.12"
        
        result = configurator.ask_python_version()
        
        assert result == "3.12"
    
    @patch('mono_kickstart.interactive.questionary.text')
    def test_ask_python_version_with_default(self, mock_text):
        """测试询问 Python 版本（使用默认值）"""
        config = Config()
        config.tools["conda"] = ToolConfig(version="3.10")
        configurator = InteractiveConfigurator(config)
        
        mock_text.return_value.ask.return_value = "3.10"
        
        result = configurator.ask_python_version()
        
        assert result == "3.10"
        # 验证默认值
        call_kwargs = mock_text.call_args[1]
        assert call_kwargs['default'] == "3.10"
    
    @patch('mono_kickstart.interactive.questionary.confirm')
    def test_ask_use_china_mirrors_yes(self, mock_confirm):
        """测试询问是否使用中国镜像（是）"""
        configurator = InteractiveConfigurator()
        
        mock_confirm.return_value.ask.return_value = True
        
        result = configurator.ask_use_china_mirrors()
        
        assert result is True
    
    @patch('mono_kickstart.interactive.questionary.confirm')
    def test_ask_use_china_mirrors_no(self, mock_confirm):
        """测试询问是否使用中国镜像（否）"""
        configurator = InteractiveConfigurator()
        
        mock_confirm.return_value.ask.return_value = False
        
        result = configurator.ask_use_china_mirrors()
        
        assert result is False
    
    @patch('mono_kickstart.interactive.questionary.confirm')
    def test_ask_use_china_mirrors_detects_default(self, mock_confirm):
        """测试询问镜像源时检测默认配置"""
        config = Config()
        config.registry.npm = "https://registry.npmmirror.com/"
        configurator = InteractiveConfigurator(config)
        
        mock_confirm.return_value.ask.return_value = True
        
        configurator.ask_use_china_mirrors()
        
        # 验证默认值为 True（因为配置中使用了中国镜像）
        call_kwargs = mock_confirm.call_args[1]
        assert call_kwargs['default'] is True
    
    @patch('mono_kickstart.interactive.questionary.confirm')
    @patch('mono_kickstart.interactive.questionary.checkbox')
    @patch('mono_kickstart.interactive.questionary.select')
    @patch('mono_kickstart.interactive.questionary.text')
    def test_run_wizard_complete_flow(self, mock_text, mock_select, mock_checkbox, mock_confirm):
        """测试完整的配置向导流程"""
        configurator = InteractiveConfigurator()
        
        # Mock 用户输入
        mock_text.return_value.ask.side_effect = ["my-monorepo", "3.11"]
        mock_checkbox.return_value.ask.return_value = ["nvm", "node", "conda"]
        mock_select.return_value.ask.return_value = "LTS (推荐)"
        mock_confirm.return_value.ask.return_value = True
        
        config = configurator.run_wizard()
        
        # 验证配置
        assert config.project.name == "my-monorepo"
        assert config.tools["nvm"].enabled is True
        assert config.tools["node"].enabled is True
        assert config.tools["node"].version == "lts"
        assert config.tools["conda"].enabled is True
        assert config.tools["conda"].version == "3.11"
        assert config.tools["bun"].enabled is False
        assert "npmmirror.com" in config.registry.npm
    
    @patch('mono_kickstart.interactive.questionary.confirm')
    @patch('mono_kickstart.interactive.questionary.checkbox')
    @patch('mono_kickstart.interactive.questionary.text')
    def test_run_wizard_without_china_mirrors(self, mock_text, mock_checkbox, mock_confirm):
        """测试配置向导（不使用中国镜像）"""
        configurator = InteractiveConfigurator()
        
        # Mock 用户输入
        mock_text.return_value.ask.return_value = "test-project"
        mock_checkbox.return_value.ask.return_value = ["nvm"]
        mock_confirm.return_value.ask.return_value = False
        
        config = configurator.run_wizard()
        
        # 验证镜像源配置
        assert config.registry.npm == "https://registry.npmjs.org/"
        assert config.registry.pypi == "https://pypi.org/simple"
    
    @patch('mono_kickstart.interactive.questionary.confirm')
    def test_confirm_config_accepted(self, mock_confirm, capsys):
        """测试配置确认（接受）"""
        configurator = InteractiveConfigurator()
        
        config = Config()
        config.project.name = "test-project"
        config.tools["nvm"] = ToolConfig(enabled=True)
        config.tools["node"] = ToolConfig(enabled=True, version="lts")
        
        mock_confirm.return_value.ask.return_value = True
        
        result = configurator.confirm_config(config)
        
        assert result is True
        
        # 验证输出包含配置摘要
        captured = capsys.readouterr()
        assert "配置摘要" in captured.out
        assert "test-project" in captured.out
        assert "nvm" in captured.out
        assert "node" in captured.out
    
    @patch('mono_kickstart.interactive.questionary.confirm')
    def test_confirm_config_rejected(self, mock_confirm):
        """测试配置确认（拒绝）"""
        configurator = InteractiveConfigurator()
        
        config = Config()
        config.project.name = "test-project"
        
        mock_confirm.return_value.ask.return_value = False
        
        result = configurator.confirm_config(config)
        
        assert result is False
    
    @patch('mono_kickstart.interactive.questionary.confirm')
    def test_confirm_config_displays_tool_versions(self, mock_confirm, capsys):
        """测试配置确认显示工具版本"""
        configurator = InteractiveConfigurator()
        
        config = Config()
        config.project.name = "test-project"
        config.tools["node"] = ToolConfig(enabled=True, version="18.17.0")
        config.tools["conda"] = ToolConfig(enabled=True, version="3.11")
        
        mock_confirm.return_value.ask.return_value = True
        
        configurator.confirm_config(config)
        
        # 验证输出包含版本信息
        captured = capsys.readouterr()
        assert "18.17.0" in captured.out
        assert "3.11" in captured.out
    
    @patch('mono_kickstart.interactive.questionary.confirm')
    def test_confirm_config_displays_mirror_settings(self, mock_confirm, capsys):
        """测试配置确认显示镜像源设置"""
        configurator = InteractiveConfigurator()
        
        config = Config()
        config.project.name = "test-project"
        config.registry.npm = "https://registry.npmmirror.com/"
        config.registry.pypi = "https://mirrors.sustech.edu.cn/pypi/web/simple"
        
        mock_confirm.return_value.ask.return_value = True
        
        configurator.confirm_config(config)
        
        # 验证输出包含镜像源信息
        captured = capsys.readouterr()
        assert "镜像源配置" in captured.out
        assert "npmmirror.com" in captured.out
        assert "sustech.edu.cn" in captured.out
