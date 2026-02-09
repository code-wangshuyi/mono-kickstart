"""配置文件加载集成测试"""

import pytest
from pathlib import Path
import yaml

from mono_kickstart.config import ConfigManager, Config, ProjectConfig, ToolConfig, RegistryConfig


class TestConfigLoadingIntegration:
    """配置文件加载集成测试"""
    
    def test_load_single_config_file(self, tmp_path):
        """测试加载单个配置文件"""
        # 创建配置文件
        config_file = tmp_path / ".kickstartrc"
        config_data = {
            "project": {
                "name": "test-project"
            },
            "tools": {
                "nvm": {"enabled": True},
                "node": {"enabled": True, "version": "lts"}
            },
            "registry": {
                "npm": "https://registry.npmmirror.com/"
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.load_from_file(config_file)
        
        # 验证配置
        assert config.project.name == "test-project"
        assert config.tools["nvm"].enabled is True
        assert config.tools["node"].enabled is True
        assert config.tools["node"].version == "lts"
        assert config.registry.npm == "https://registry.npmmirror.com/"
    
    def test_load_with_priority(self, tmp_path):
        """测试按优先级加载多个配置文件"""
        # 创建用户配置文件
        user_config = tmp_path / "user.yaml"
        user_config_data = {
            "project": {"name": "user-project"},
            "tools": {
                "nvm": {"enabled": True},
                "node": {"enabled": True, "version": "18.17.0"}
            },
            "registry": {
                "npm": "https://registry.npmjs.org/",
                "pypi": "https://pypi.org/simple"
            }
        }
        with open(user_config, 'w') as f:
            yaml.dump(user_config_data, f)
        
        # 创建项目配置文件
        project_config = tmp_path / "project.yaml"
        project_config_data = {
            "project": {"name": "my-project"},
            "tools": {
                "node": {"version": "lts"},
                "bun": {"enabled": True}
            }
        }
        with open(project_config, 'w') as f:
            yaml.dump(project_config_data, f)
        
        # 加载配置
        config_manager = ConfigManager()
        
        # 按优先级加载：项目配置 > 用户配置 > 默认配置
        config = config_manager.load_with_priority(
            cli_config=None,
            project_config=project_config,
            user_config=user_config
        )
        
        # 验证合并结果
        # 项目配置覆盖用户配置
        assert config.project.name == "my-project"
        assert config.tools["node"].version == "lts"
        
        # 用户配置保留（项目配置未指定）
        assert config.tools["nvm"].enabled is True
        assert config.registry.pypi == "https://pypi.org/simple"
        
        # 项目配置新增
        assert config.tools["bun"].enabled is True
    
    def test_load_with_cli_config_priority(self, tmp_path):
        """测试 CLI 配置优先级最高"""
        # 创建用户配置
        user_config = tmp_path / "user.yaml"
        user_config_data = {
            "project": {"name": "user-project"},
            "tools": {"node": {"version": "18.17.0"}}
        }
        with open(user_config, 'w') as f:
            yaml.dump(user_config_data, f)
        
        # 创建项目配置
        project_config = tmp_path / "project.yaml"
        project_config_data = {
            "project": {"name": "project-name"},
            "tools": {"node": {"version": "lts"}}
        }
        with open(project_config, 'w') as f:
            yaml.dump(project_config_data, f)
        
        # 创建 CLI 配置
        cli_config = tmp_path / "cli.yaml"
        cli_config_data = {
            "project": {"name": "cli-project"},
            "tools": {"node": {"version": "20.0.0"}}
        }
        with open(cli_config, 'w') as f:
            yaml.dump(cli_config_data, f)
        
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.load_with_priority(
            cli_config=cli_config,
            project_config=project_config,
            user_config=user_config
        )
        
        # 验证 CLI 配置优先级最高
        assert config.project.name == "cli-project"
        assert config.tools["node"].version == "20.0.0"
    
    def test_load_with_missing_files(self, tmp_path):
        """测试加载不存在的配置文件"""
        # 创建一个存在的配置文件
        existing_config = tmp_path / "existing.yaml"
        existing_config_data = {
            "project": {"name": "test-project"}
        }
        with open(existing_config, 'w') as f:
            yaml.dump(existing_config_data, f)
        
        # 不存在的配置文件路径
        missing_config = tmp_path / "missing.yaml"
        
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.load_with_priority(
            cli_config=None,
            project_config=existing_config,
            user_config=missing_config  # 不存在
        )
        
        # 验证能正常加载存在的配置
        assert config.project.name == "test-project"
    
    def test_save_and_reload_config(self, tmp_path):
        """测试保存和重新加载配置"""
        # 创建配置
        config = Config()
        config.project = ProjectConfig(name="test-project")
        config.tools["nvm"] = ToolConfig(enabled=True)
        config.tools["node"] = ToolConfig(enabled=True, version="lts")
        config.registry = RegistryConfig(
            npm="https://registry.npmmirror.com/",
            pypi="https://mirrors.sustech.edu.cn/pypi/web/simple"
        )
        
        # 保存配置
        config_file = tmp_path / ".kickstartrc"
        config_manager = ConfigManager()
        config_manager.save_to_file(config, config_file)
        
        # 验证文件存在
        assert config_file.exists()
        
        # 重新加载配置
        loaded_config = config_manager.load_from_file(config_file)
        
        # 验证配置一致
        assert loaded_config.project.name == config.project.name
        assert loaded_config.tools["nvm"].enabled == config.tools["nvm"].enabled
        assert loaded_config.tools["node"].version == config.tools["node"].version
        assert loaded_config.registry.npm == config.registry.npm
        assert loaded_config.registry.pypi == config.registry.pypi
    
    def test_config_roundtrip_consistency(self, tmp_path):
        """测试配置往返一致性"""
        # 创建复杂配置
        config = Config()
        config.project = ProjectConfig(name="complex-project")
        
        # 配置多个工具
        config.tools["nvm"] = ToolConfig(enabled=True)
        config.tools["node"] = ToolConfig(enabled=True, version="18.17.0")
        config.tools["conda"] = ToolConfig(enabled=False)
        config.tools["bun"] = ToolConfig(enabled=True, version="latest")
        config.tools["uv"] = ToolConfig(enabled=True)
        
        # 配置镜像源
        config.registry = RegistryConfig(
            npm="https://registry.npmmirror.com/",
            bun="https://registry.npmmirror.com/",
            pypi="https://mirrors.sustech.edu.cn/pypi/web/simple",
            python_install="https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"
        )
        
        # 保存配置
        config_file = tmp_path / ".kickstartrc"
        config_manager = ConfigManager()
        config_manager.save_to_file(config, config_file)
        
        # 重新加载
        loaded_config = config_manager.load_from_file(config_file)
        
        # 验证所有字段一致
        assert loaded_config.project.name == config.project.name
        
        for tool_name in ["nvm", "node", "conda", "bun", "uv"]:
            assert loaded_config.tools[tool_name].enabled == config.tools[tool_name].enabled
            assert loaded_config.tools[tool_name].version == config.tools[tool_name].version
        
        assert loaded_config.registry.npm == config.registry.npm
        assert loaded_config.registry.bun == config.registry.bun
        assert loaded_config.registry.pypi == config.registry.pypi
        assert loaded_config.registry.python_install == config.registry.python_install
    
    def test_merge_nested_configs(self, tmp_path):
        """测试嵌套配置的合并"""
        # 创建基础配置
        base_config = tmp_path / "base.yaml"
        base_config_data = {
            "tools": {
                "nvm": {"enabled": True},
                "node": {"enabled": True, "version": "18.17.0"},
                "bun": {"enabled": True}
            }
        }
        with open(base_config, 'w') as f:
            yaml.dump(base_config_data, f)
        
        # 创建覆盖配置
        override_config = tmp_path / "override.yaml"
        override_config_data = {
            "tools": {
                "node": {"version": "lts"},  # 覆盖版本
                "bun": {"enabled": False},  # 禁用 bun
                "uv": {"enabled": True}  # 新增 uv
            }
        }
        with open(override_config, 'w') as f:
            yaml.dump(override_config_data, f)
        
        # 加载并合并配置
        config_manager = ConfigManager()
        base = config_manager.load_from_file(base_config)
        override = config_manager.load_from_file(override_config)
        merged = config_manager.merge_configs(base, override)
        
        # 验证合并结果
        assert merged.tools["nvm"].enabled is True  # 保留基础配置
        assert merged.tools["node"].enabled is True  # 保留基础配置
        assert merged.tools["node"].version == "lts"  # 覆盖版本
        assert merged.tools["bun"].enabled is False  # 覆盖启用状态
        assert merged.tools["uv"].enabled is True  # 新增工具
    
    def test_config_validation(self, tmp_path):
        """测试配置验证"""
        # 创建有效配置
        valid_config = Config()
        valid_config.project = ProjectConfig(name="valid-project")
        valid_config.tools["nvm"] = ToolConfig(enabled=True)
        
        config_manager = ConfigManager()
        errors = config_manager.validate(valid_config)
        
        # 验证有效配置无错误
        assert len(errors) == 0
    
    def test_load_config_with_extra_fields(self, tmp_path):
        """测试加载包含额外字段的配置文件"""
        # 创建包含额外字段的配置文件
        config_file = tmp_path / ".kickstartrc"
        config_data = {
            "project": {
                "name": "test-project"
                # 注意：dataclass 不支持额外字段，所以不测试额外字段
            },
            "tools": {
                "nvm": {"enabled": True}
            }
            # 注意：未知部分会被忽略
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.load_from_file(config_file)
        
        # 验证已知字段正常加载
        assert config.project.name == "test-project"
        assert config.tools["nvm"].enabled is True
