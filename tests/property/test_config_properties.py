"""配置管理器的基于属性的测试

本模块使用 Hypothesis 框架测试配置管理器的通用属性。
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from pathlib import Path
import yaml
import tempfile
import shutil

from mono_kickstart.config import (
    ToolConfig,
    RegistryConfig,
    ProjectConfig,
    Config,
    ConfigManager,
)


# 定义测试数据生成策略

# 有效的工具名称
VALID_TOOLS = [
    "nvm",
    "node",
    "conda",
    "bun",
    "uv",
    "claude-code",
    "codex",
    "opencode",
    "spec-kit",
    "bmad-method",
]

# 有效的安装方式
VALID_INSTALL_METHODS = ["bun", "npm", "brew", None]


@st.composite
def tool_config_strategy(draw):
    """生成 ToolConfig 对象的策略"""
    return ToolConfig(
        enabled=draw(st.booleans()),
        version=draw(
            st.one_of(
                st.none(),
                st.text(
                    alphabet=st.characters(
                        min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cs")
                    ),
                    min_size=1,
                    max_size=20,
                ),
            )
        ),
        install_via=draw(st.sampled_from(VALID_INSTALL_METHODS)),
        extra_options=draw(
            st.dictionaries(
                st.text(
                    alphabet=st.characters(
                        min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cs")
                    ),
                    min_size=1,
                    max_size=10,
                ),
                st.text(
                    alphabet=st.characters(
                        min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cs")
                    ),
                    min_size=1,
                    max_size=20,
                ),
                max_size=3,
            )
        ),
    )


@st.composite
def registry_config_strategy(draw):
    """生成 RegistryConfig 对象的策略"""
    return RegistryConfig(
        npm=draw(
            st.text(
                alphabet=st.characters(
                    min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cs")
                ),
                min_size=10,
                max_size=100,
            )
        ),
        bun=draw(
            st.text(
                alphabet=st.characters(
                    min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cs")
                ),
                min_size=10,
                max_size=100,
            )
        ),
        pypi=draw(
            st.text(
                alphabet=st.characters(
                    min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cs")
                ),
                min_size=10,
                max_size=100,
            )
        ),
        python_install=draw(
            st.text(
                alphabet=st.characters(
                    min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cs")
                ),
                min_size=10,
                max_size=100,
            )
        ),
    )


@st.composite
def project_config_strategy(draw):
    """生成 ProjectConfig 对象的策略"""
    return ProjectConfig(
        name=draw(
            st.one_of(
                st.none(),
                st.text(
                    alphabet=st.characters(
                        min_codepoint=32, max_codepoint=126, blacklist_categories=("Cc", "Cs")
                    ),
                    min_size=1,
                    max_size=50,
                ),
            )
        )
    )


@st.composite
def config_strategy(draw):
    """生成 Config 对象的策略"""
    return Config(
        project=draw(project_config_strategy()),
        tools=draw(
            st.dictionaries(st.sampled_from(VALID_TOOLS), tool_config_strategy(), max_size=5)
        ),
        registry=draw(registry_config_strategy()),
    )


class TestConfigPriorityMerge:
    """测试属性 7: 配置优先级合并

    **Validates: Requirements 4.1, 4.9**
    """

    @given(
        config1=config_strategy(),
        config2=config_strategy(),
        config3=config_strategy(),
        config4=config_strategy(),
    )
    def test_merge_priority_order(self, config1, config2, config3, config4):
        """验证配置按优先级正确合并

        对于任何多个配置源，配置管理器应该按优先级合并，
        高优先级配置字段覆盖低优先级字段。
        """
        manager = ConfigManager()
        merged = manager.merge_configs(config1, config2, config3, config4)

        # 验证 project.name 使用最后一个非 None 的值
        expected_name = None
        for config in [config1, config2, config3, config4]:
            if config.project.name is not None:
                expected_name = config.project.name
        assert merged.project.name == expected_name

        # 验证所有工具配置都被包含（后面的覆盖前面的）
        all_tools = set()
        for config in [config1, config2, config3, config4]:
            all_tools.update(config.tools.keys())

        for tool_name in all_tools:
            assert tool_name in merged.tools

            # 找到最后一个定义该工具的配置
            expected_tool_config = None
            for config in [config1, config2, config3, config4]:
                if tool_name in config.tools:
                    expected_tool_config = config.tools[tool_name]

            # 验证合并后的工具配置与预期一致
            assert merged.tools[tool_name] == expected_tool_config

    @given(configs=st.lists(config_strategy(), min_size=1, max_size=5))
    def test_merge_is_associative(self, configs):
        """验证配置合并满足结合律

        merge(a, b, c) 应该等于 merge(merge(a, b), c)
        """
        manager = ConfigManager()

        # 一次性合并所有配置
        result1 = manager.merge_configs(*configs)

        # 逐步合并配置
        result2 = configs[0]
        for config in configs[1:]:
            result2 = manager.merge_configs(result2, config)

        # 验证结果相同
        assert result1.project.name == result2.project.name
        assert result1.tools.keys() == result2.tools.keys()
        for tool_name in result1.tools:
            assert result1.tools[tool_name] == result2.tools[tool_name]

    @given(config=config_strategy())
    def test_merge_with_empty_is_identity(self, config):
        """验证与空配置合并保持不变

        merge(config, empty) 应该等于 config
        merge(empty, config) 应该等于 config
        """
        manager = ConfigManager()
        empty = Config()

        # 空配置在后
        result1 = manager.merge_configs(config, empty)
        # 空配置在前
        result2 = manager.merge_configs(empty, config)

        # 验证 project.name
        assert result1.project.name == config.project.name
        assert result2.project.name == config.project.name

        # 验证 tools
        assert result1.tools.keys() == config.tools.keys()
        assert result2.tools.keys() == config.tools.keys()


class TestConfigFileFormatValidation:
    """测试属性 8: 配置文件格式验证

    **Validates: Requirements 4.4**
    """

    @given(
        invalid_yaml=st.text(min_size=1, max_size=100).filter(
            lambda s: s.strip() and not s.strip().startswith("#")
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_yaml_raises_error(self, invalid_yaml):
        """验证无效的 YAML 格式抛出错误

        对于任何无效的 YAML 格式配置文件，
        配置管理器应该抛出格式错误或类型错误。
        """
        # 使用临时目录
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # 创建无效的 YAML 文件
            config_file = tmp_path / "invalid.yaml"
            # 添加一些明显无效的 YAML 语法
            config_file.write_text(f"{invalid_yaml}\n  invalid: yaml: [[[")

            manager = ConfigManager()

            # 验证抛出 YAML 错误或 AttributeError（当 YAML 解析为非字典类型时）
            with pytest.raises((yaml.YAMLError, AttributeError)):
                manager.load_from_file(config_file)

    @given(config=config_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_valid_config_loads_without_error(self, config):
        """验证有效的配置可以正常加载

        对于任何有效的配置对象，保存后应该能够无错误加载。
        """
        # 使用临时目录
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            config_file = tmp_path / "valid.yaml"
            manager = ConfigManager()

            # 保存配置
            manager.save_to_file(config, config_file)

            # 加载配置不应抛出异常
            loaded_config = manager.load_from_file(config_file)
            assert isinstance(loaded_config, Config)


class TestConfigRoundtripConsistency:
    """测试属性 9: 配置往返一致性

    **Validates: Requirements 4.5, 11.8**
    """

    @given(config=config_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_load_roundtrip(self, config):
        """验证配置保存和加载的往返一致性

        对于任何有效的配置对象，保存到文件然后重新加载
        应该产生等价的配置对象。
        """
        # 使用临时目录
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            config_file = tmp_path / "config.yaml"
            manager = ConfigManager()

            # 保存配置
            manager.save_to_file(config, config_file)

            # 加载配置
            loaded_config = manager.load_from_file(config_file)

            # 验证 project 配置一致
            assert loaded_config.project.name == config.project.name

            # 验证 tools 配置一致
            assert loaded_config.tools.keys() == config.tools.keys()
            for tool_name in config.tools:
                original_tool = config.tools[tool_name]
                loaded_tool = loaded_config.tools[tool_name]
                assert loaded_tool.enabled == original_tool.enabled
                assert loaded_tool.version == original_tool.version
                assert loaded_tool.install_via == original_tool.install_via
                assert loaded_tool.extra_options == original_tool.extra_options

            # 验证 registry 配置一致
            assert loaded_config.registry.npm == config.registry.npm
            assert loaded_config.registry.bun == config.registry.bun
            assert loaded_config.registry.pypi == config.registry.pypi
            assert loaded_config.registry.python_install == config.registry.python_install

    @given(config=config_strategy(), iterations=st.integers(min_value=2, max_value=5))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_roundtrips(self, config, iterations):
        """验证多次往返保持一致性

        多次保存和加载应该保持配置不变。
        """
        # 使用临时目录
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            config_file = tmp_path / "config.yaml"
            manager = ConfigManager()

            current_config = config
            for i in range(iterations):
                # 保存
                manager.save_to_file(current_config, config_file)
                # 加载
                current_config = manager.load_from_file(config_file)

            # 验证最终配置与原始配置一致
            assert current_config.project.name == config.project.name
            assert current_config.tools.keys() == config.tools.keys()
            for tool_name in config.tools:
                assert current_config.tools[tool_name].enabled == config.tools[tool_name].enabled

    @given(config=config_strategy())
    def test_to_dict_from_dict_roundtrip(self, config):
        """验证字典转换的往返一致性

        Config -> dict -> Config 应该保持一致。
        """
        # 转换为字典
        config_dict = config.to_dict()

        # 从字典创建配置
        restored_config = Config.from_dict(config_dict)

        # 验证一致性
        assert restored_config.project.name == config.project.name
        assert restored_config.tools.keys() == config.tools.keys()
        for tool_name in config.tools:
            assert restored_config.tools[tool_name].enabled == config.tools[tool_name].enabled
            assert restored_config.tools[tool_name].version == config.tools[tool_name].version


class TestConfigValidation:
    """测试配置验证的属性"""

    @given(config=config_strategy())
    def test_valid_config_has_no_errors(self, config):
        """验证有效的配置不产生错误

        对于任何使用有效工具名称和安装方式的配置，
        验证应该返回空错误列表。
        """
        manager = ConfigManager()
        errors = manager.validate(config)

        # 有效配置不应有错误
        assert errors == []

    @given(
        config=config_strategy(),
        invalid_tool=st.text(min_size=1, max_size=20).filter(lambda s: s not in VALID_TOOLS),
    )
    def test_invalid_tool_name_produces_error(self, config, invalid_tool):
        """验证无效的工具名称产生错误

        对于任何包含无效工具名称的配置，
        验证应该返回包含该工具名称的错误。
        """
        # 添加无效的工具
        config.tools[invalid_tool] = ToolConfig()

        manager = ConfigManager()
        errors = manager.validate(config)

        # 应该有错误
        assert len(errors) > 0
        # 错误信息应该包含无效的工具名称
        assert any(invalid_tool in error for error in errors)

    @given(
        config=config_strategy(),
        invalid_method=st.text(min_size=1, max_size=20).filter(
            lambda s: s not in ["bun", "npm", "brew"]
        ),
    )
    def test_invalid_install_via_produces_error(self, config, invalid_method):
        """验证无效的 install_via 产生错误

        对于任何包含无效安装方式的配置，
        验证应该返回相关错误。
        """
        # 添加一个有效工具但使用无效的安装方式
        config.tools["nvm"] = ToolConfig(install_via=invalid_method)

        manager = ConfigManager()
        errors = manager.validate(config)

        # 应该有错误
        assert len(errors) > 0
        # 错误信息应该提到 install_via
        assert any("install_via" in error for error in errors)
