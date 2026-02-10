"""配置管理器的单元测试"""

import pytest
from pathlib import Path
import yaml

from mono_kickstart.config import (
    ToolConfig,
    RegistryConfig,
    ProjectConfig,
    Config,
    ConfigManager,
)


class TestToolConfig:
    """测试 ToolConfig 数据类"""
    
    def test_default_values(self):
        """测试默认值"""
        config = ToolConfig()
        assert config.enabled is True
        assert config.version is None
        assert config.install_via is None
        assert config.extra_options == {}
    
    def test_custom_values(self):
        """测试自定义值"""
        config = ToolConfig(
            enabled=False,
            version="1.0.0",
            install_via="npm",
            extra_options={"key": "value"}
        )
        assert config.enabled is False
        assert config.version == "1.0.0"
        assert config.install_via == "npm"
        assert config.extra_options == {"key": "value"}


class TestRegistryConfig:
    """测试 RegistryConfig 数据类"""
    
    def test_default_values(self):
        """测试默认值"""
        config = RegistryConfig()
        assert config.npm == "https://registry.npmmirror.com/"
        assert config.bun == "https://registry.npmmirror.com/"
        assert config.pypi == "https://mirrors.sustech.edu.cn/pypi/web/simple"
        assert "ghfast.top" in config.python_install
    
    def test_custom_values(self):
        """测试自定义值"""
        config = RegistryConfig(
            npm="https://custom-npm.com/",
            bun="https://custom-bun.com/",
            pypi="https://custom-pypi.com/",
            python_install="https://custom-python.com/"
        )
        assert config.npm == "https://custom-npm.com/"
        assert config.bun == "https://custom-bun.com/"
        assert config.pypi == "https://custom-pypi.com/"
        assert config.python_install == "https://custom-python.com/"

    def test_default_conda_value(self):
        """测试 conda 默认值"""
        config = RegistryConfig()
        assert config.conda == "https://mirrors.sustech.edu.cn/anaconda"

    def test_custom_conda_value(self):
        """测试自定义 conda 值"""
        config = RegistryConfig(conda="https://custom-conda.com/")
        assert config.conda == "https://custom-conda.com/"


class TestProjectConfig:
    """测试 ProjectConfig 数据类"""
    
    def test_default_values(self):
        """测试默认值"""
        config = ProjectConfig()
        assert config.name is None
    
    def test_custom_values(self):
        """测试自定义值"""
        config = ProjectConfig(name="my-project")
        assert config.name == "my-project"


class TestConfig:
    """测试 Config 数据类"""
    
    def test_default_values(self):
        """测试默认值"""
        config = Config()
        assert isinstance(config.project, ProjectConfig)
        assert config.tools == {}
        assert isinstance(config.registry, RegistryConfig)
    
    def test_custom_values(self):
        """测试自定义值"""
        project = ProjectConfig(name="test-project")
        tools = {"nvm": ToolConfig(enabled=True)}
        registry = RegistryConfig(npm="https://custom.com/")
        
        config = Config(project=project, tools=tools, registry=registry)
        assert config.project.name == "test-project"
        assert "nvm" in config.tools
        assert config.registry.npm == "https://custom.com/"
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = Config(
            project=ProjectConfig(name="test"),
            tools={"nvm": ToolConfig(enabled=False)},
            registry=RegistryConfig()
        )
        
        data = config.to_dict()
        assert isinstance(data, dict)
        assert data["project"]["name"] == "test"
        assert data["tools"]["nvm"]["enabled"] is False
        assert "npm" in data["registry"]
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "project": {"name": "test-project"},
            "tools": {
                "nvm": {"enabled": False, "version": "0.40.4"}
            },
            "registry": {
                "npm": "https://custom.com/"
            }
        }
        
        config = Config.from_dict(data)
        assert config.project.name == "test-project"
        assert config.tools["nvm"].enabled is False
        assert config.tools["nvm"].version == "0.40.4"
        assert config.registry.npm == "https://custom.com/"
    
    def test_from_dict_empty(self):
        """测试从空字典创建"""
        config = Config.from_dict({})
        assert config.project.name is None
        assert config.tools == {}
        assert isinstance(config.registry, RegistryConfig)
    
    def test_from_dict_partial(self):
        """测试从部分字典创建"""
        data = {
            "project": {"name": "test"}
        }
        
        config = Config.from_dict(data)
        assert config.project.name == "test"
        assert config.tools == {}
        assert isinstance(config.registry, RegistryConfig)


class TestConfigManager:
    """测试 ConfigManager 类"""
    
    def test_init(self):
        """测试初始化"""
        manager = ConfigManager()
        assert isinstance(manager.config, Config)
    
    def test_load_from_defaults(self):
        """测试加载默认配置"""
        manager = ConfigManager()
        config = manager.load_from_defaults()
        
        assert isinstance(config, Config)
        assert config.project.name is None
        assert config.tools == {}
        assert isinstance(config.registry, RegistryConfig)
    
    def test_load_from_file_not_exists(self):
        """测试加载不存在的文件"""
        manager = ConfigManager()
        
        with pytest.raises(FileNotFoundError):
            manager.load_from_file(Path("/nonexistent/config.yaml"))
    
    def test_load_from_file_valid(self, tmp_path):
        """测试加载有效的配置文件"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "project": {"name": "test-project"},
            "tools": {
                "nvm": {"enabled": True, "version": "0.40.4"}
            },
            "registry": {
                "npm": "https://custom.com/"
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.safe_dump(config_data, f)
        
        manager = ConfigManager()
        config = manager.load_from_file(config_file)
        
        assert config.project.name == "test-project"
        assert config.tools["nvm"].enabled is True
        assert config.tools["nvm"].version == "0.40.4"
        assert config.registry.npm == "https://custom.com/"
    
    def test_load_from_file_empty(self, tmp_path):
        """测试加载空配置文件"""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        
        manager = ConfigManager()
        config = manager.load_from_file(config_file)
        
        assert isinstance(config, Config)
        assert config.project.name is None
    
    def test_load_from_file_invalid_yaml(self, tmp_path):
        """测试加载无效的 YAML 文件"""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        manager = ConfigManager()
        
        with pytest.raises(yaml.YAMLError):
            manager.load_from_file(config_file)
    
    def test_save_to_file(self, tmp_path):
        """测试保存配置到文件"""
        config = Config(
            project=ProjectConfig(name="test-project"),
            tools={"nvm": ToolConfig(enabled=False)},
            registry=RegistryConfig(npm="https://custom.com/")
        )
        
        config_file = tmp_path / "config.yaml"
        manager = ConfigManager()
        manager.save_to_file(config, config_file)
        
        assert config_file.exists()
        
        # 验证保存的内容
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["project"]["name"] == "test-project"
        assert data["tools"]["nvm"]["enabled"] is False
        assert data["registry"]["npm"] == "https://custom.com/"
    
    def test_save_to_file_creates_directory(self, tmp_path):
        """测试保存时自动创建目录"""
        config = Config()
        config_file = tmp_path / "subdir" / "config.yaml"
        
        manager = ConfigManager()
        manager.save_to_file(config, config_file)
        
        assert config_file.exists()
        assert config_file.parent.exists()
    
    def test_merge_configs_empty(self):
        """测试合并空配置列表"""
        manager = ConfigManager()
        result = manager.merge_configs()
        
        assert isinstance(result, Config)
        assert result.project.name is None
        assert result.tools == {}
    
    def test_merge_configs_single(self):
        """测试合并单个配置"""
        config = Config(project=ProjectConfig(name="test"))
        
        manager = ConfigManager()
        result = manager.merge_configs(config)
        
        assert result.project.name == "test"
    
    def test_merge_configs_multiple(self):
        """测试合并多个配置"""
        config1 = Config(
            project=ProjectConfig(name="project1"),
            tools={"nvm": ToolConfig(enabled=True)},
            registry=RegistryConfig(npm="https://npm1.com/")
        )
        
        config2 = Config(
            project=ProjectConfig(name="project2"),
            tools={"node": ToolConfig(enabled=False)},
            registry=RegistryConfig(bun="https://bun2.com/")
        )
        
        manager = ConfigManager()
        result = manager.merge_configs(config1, config2)
        
        # 后面的配置覆盖前面的
        assert result.project.name == "project2"
        # 工具配置合并
        assert "nvm" in result.tools
        assert "node" in result.tools
        # 镜像源配置合并
        assert result.registry.npm == "https://npm1.com/"
        assert result.registry.bun == "https://bun2.com/"
    
    def test_merge_configs_partial_override(self):
        """测试部分字段覆盖"""
        config1 = Config(
            project=ProjectConfig(name="project1"),
            tools={"nvm": ToolConfig(enabled=True, version="1.0")},
        )
        
        config2 = Config(
            tools={"nvm": ToolConfig(enabled=False)},
        )
        
        manager = ConfigManager()
        result = manager.merge_configs(config1, config2)
        
        # project.name 保持不变
        assert result.project.name == "project1"
        # nvm 配置被完全覆盖
        assert result.tools["nvm"].enabled is False
    
    def test_load_with_priority_default_only(self, tmp_path):
        """测试仅使用默认配置"""
        manager = ConfigManager()
        config = manager.load_with_priority(
            cli_config=None,
            project_config=tmp_path / ".kickstartrc",
            user_config=tmp_path / "user" / ".kickstartrc"
        )
        
        assert isinstance(config, Config)
        assert config.project.name is None
    
    def test_load_with_priority_all_sources(self, tmp_path):
        """测试从所有源加载配置"""
        # 创建用户配置
        user_config = tmp_path / "user.yaml"
        user_config.write_text(yaml.safe_dump({
            "project": {"name": "user-project"},
            "tools": {"nvm": {"enabled": True}}
        }))
        
        # 创建项目配置
        project_config = tmp_path / "project.yaml"
        project_config.write_text(yaml.safe_dump({
            "project": {"name": "project-project"},
            "tools": {"node": {"enabled": False}}
        }))
        
        # 创建 CLI 配置
        cli_config = tmp_path / "cli.yaml"
        cli_config.write_text(yaml.safe_dump({
            "project": {"name": "cli-project"}
        }))
        
        manager = ConfigManager()
        config = manager.load_with_priority(
            cli_config=cli_config,
            project_config=project_config,
            user_config=user_config
        )
        
        # CLI 配置优先级最高
        assert config.project.name == "cli-project"
        # 工具配置合并
        assert "nvm" in config.tools
        assert "node" in config.tools
    
    def test_load_with_priority_skip_invalid(self, tmp_path):
        """测试跳过无效的配置文件"""
        # 创建无效的用户配置
        user_config = tmp_path / "user.yaml"
        user_config.write_text("invalid: yaml: [")
        
        # 创建有效的项目配置
        project_config = tmp_path / "project.yaml"
        project_config.write_text(yaml.safe_dump({
            "project": {"name": "project-name"}
        }))
        
        manager = ConfigManager()
        config = manager.load_with_priority(
            cli_config=None,
            project_config=project_config,
            user_config=user_config
        )
        
        # 应该使用项目配置
        assert config.project.name == "project-name"
    
    def test_validate_valid_config(self):
        """测试验证有效配置"""
        config = Config(
            tools={
                "nvm": ToolConfig(enabled=True),
                "node": ToolConfig(enabled=False, install_via="npm")
            }
        )
        
        manager = ConfigManager()
        errors = manager.validate(config)
        
        assert errors == []
    
    def test_validate_invalid_tool_name(self):
        """测试验证无效的工具名称"""
        config = Config(
            tools={
                "invalid-tool": ToolConfig(enabled=True)
            }
        )
        
        manager = ConfigManager()
        errors = manager.validate(config)
        
        assert len(errors) > 0
        assert "invalid-tool" in errors[0]
    
    def test_validate_copilot_cli_tool_name(self):
        """测试验证 copilot-cli 工具名称"""
        config = Config(
            tools={
                "copilot-cli": ToolConfig(enabled=True)
            }
        )
        
        manager = ConfigManager()
        errors = manager.validate(config)
        
        assert errors == []
    
    def test_copilot_cli_default_config(self):
        """测试 copilot-cli 配置默认值的正确性
        
        验证当配置文件中未指定 copilot-cli 配置时，系统使用默认配置（enabled=True）
        Requirements: 6.1, 6.4
        """
        # 创建一个空配置（未指定 copilot-cli）
        config = Config()
        
        # 验证默认情况下 tools 字典为空
        assert "copilot-cli" not in config.tools
        
        # 当工具未在配置中指定时，应该使用 ToolConfig 的默认值
        default_tool_config = ToolConfig()
        assert default_tool_config.enabled is True
        assert default_tool_config.version is None
        assert default_tool_config.install_via is None
        assert default_tool_config.extra_options == {}
    
    def test_copilot_cli_custom_config(self):
        """测试 copilot-cli 自定义配置
        
        验证可以通过配置文件设置 copilot-cli 的各项配置
        Requirements: 6.2, 6.3
        """
        config = Config(
            tools={
                "copilot-cli": ToolConfig(
                    enabled=False,
                    version="1.0.0",
                    install_via="npm",
                    extra_options={"custom": "value"}
                )
            }
        )
        
        # 验证自定义配置正确设置
        assert config.tools["copilot-cli"].enabled is False
        assert config.tools["copilot-cli"].version == "1.0.0"
        assert config.tools["copilot-cli"].install_via == "npm"
        assert config.tools["copilot-cli"].extra_options == {"custom": "value"}
        
        # 验证配置通过验证
        manager = ConfigManager()
        errors = manager.validate(config)
        assert errors == []
    
    def test_validate_invalid_install_via(self):
        """测试验证无效的 install_via"""
        config = Config(
            tools={
                "nvm": ToolConfig(enabled=True, install_via="invalid-method")
            }
        )
        
        manager = ConfigManager()
        errors = manager.validate(config)
        
        assert len(errors) > 0
        assert "install_via" in errors[0]
    
    def test_validate_invalid_registry_url(self):
        """测试验证无效的镜像源 URL"""
        config = Config(
            registry=RegistryConfig(npm="")
        )

        manager = ConfigManager()
        errors = manager.validate(config)

        assert len(errors) > 0
        assert "npm" in errors[0]

    def test_merge_configs_conda_override(self):
        """测试 conda 字段合并覆盖"""
        config1 = Config(
            registry=RegistryConfig(conda="https://conda1.com/")
        )

        config2 = Config(
            registry=RegistryConfig(conda="https://conda2.com/")
        )

        manager = ConfigManager()
        result = manager.merge_configs(config1, config2)

        # 后面的配置覆盖前面的
        assert result.registry.conda == "https://conda2.com/"

    def test_validate_conda_url(self):
        """测试验证 conda URL"""
        config = Config(
            registry=RegistryConfig(conda="")
        )

        manager = ConfigManager()
        errors = manager.validate(config)

        assert len(errors) > 0
        assert "conda" in errors[0]
    
    def test_roundtrip_consistency(self, tmp_path):
        """测试配置保存和加载的往返一致性"""
        original_config = Config(
            project=ProjectConfig(name="test-project"),
            tools={
                "nvm": ToolConfig(enabled=True, version="0.40.4"),
                "node": ToolConfig(enabled=False, install_via="npm")
            },
            registry=RegistryConfig(
                npm="https://custom-npm.com/",
                bun="https://custom-bun.com/"
            )
        )
        
        config_file = tmp_path / "config.yaml"
        manager = ConfigManager()
        
        # 保存配置
        manager.save_to_file(original_config, config_file)
        
        # 加载配置
        loaded_config = manager.load_from_file(config_file)
        
        # 验证一致性
        assert loaded_config.project.name == original_config.project.name
        assert loaded_config.tools.keys() == original_config.tools.keys()
        for tool_name in original_config.tools:
            assert loaded_config.tools[tool_name].enabled == original_config.tools[tool_name].enabled
            assert loaded_config.tools[tool_name].version == original_config.tools[tool_name].version
            assert loaded_config.tools[tool_name].install_via == original_config.tools[tool_name].install_via
        assert loaded_config.registry.npm == original_config.registry.npm
        assert loaded_config.registry.bun == original_config.registry.bun
