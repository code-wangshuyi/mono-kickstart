"""配置管理模块

该模块定义了配置数据模型和配置管理器，用于加载、合并、验证和保存配置。
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml


@dataclass
class ToolConfig:
    """单个工具的配置
    
    Attributes:
        enabled: 是否启用该工具
        version: 指定的版本号（None 表示使用默认版本）
        install_via: 安装方式（如 bun/npm/brew）
        extra_options: 额外的配置选项
    """
    enabled: bool = True
    version: Optional[str] = None
    install_via: Optional[str] = None
    extra_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegistryConfig:
    """镜像源配置
    
    Attributes:
        npm: npm 镜像源地址
        bun: Bun 镜像源地址
        pypi: PyPI 镜像源地址
        python_install: Python 安装包下载代理地址
    """
    npm: str = "https://registry.npmmirror.com/"
    bun: str = "https://registry.npmmirror.com/"
    pypi: str = "https://mirrors.sustech.edu.cn/pypi/web/simple"
    python_install: str = "https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"


@dataclass
class ProjectConfig:
    """项目配置
    
    Attributes:
        name: 项目名称
    """
    name: Optional[str] = None


@dataclass
class Config:
    """完整配置
    
    Attributes:
        project: 项目配置
        tools: 工具配置字典，键为工具名称
        registry: 镜像源配置
    """
    project: ProjectConfig = field(default_factory=ProjectConfig)
    tools: Dict[str, ToolConfig] = field(default_factory=dict)
    registry: RegistryConfig = field(default_factory=RegistryConfig)

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典
        
        Returns:
            配置的字典表示
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """从字典创建配置对象
        
        Args:
            data: 配置字典
            
        Returns:
            Config 对象
        """
        # 处理 project 字段
        project_data = data.get("project", {})
        project = ProjectConfig(**project_data) if project_data else ProjectConfig()
        
        # 处理 tools 字段
        tools_data = data.get("tools", {})
        tools = {}
        for tool_name, tool_config in tools_data.items():
            if isinstance(tool_config, dict):
                tools[tool_name] = ToolConfig(**tool_config)
            else:
                tools[tool_name] = tool_config
        
        # 处理 registry 字段
        registry_data = data.get("registry", {})
        registry = RegistryConfig(**registry_data) if registry_data else RegistryConfig()
        
        return cls(project=project, tools=tools, registry=registry)


class ConfigManager:
    """配置管理器
    
    负责加载、合并、验证和保存配置。
    """
    
    def __init__(self):
        """初始化配置管理器"""
        self.config = Config()
    
    def load_from_file(self, path: Path) -> Config:
        """从 YAML 文件加载配置
        
        Args:
            path: 配置文件路径
            
        Returns:
            加载的配置对象
            
        Raises:
            FileNotFoundError: 文件不存在
            yaml.YAMLError: YAML 格式错误
        """
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            data = {}
        
        return Config.from_dict(data)
    
    def load_from_defaults(self) -> Config:
        """加载默认配置
        
        Returns:
            默认配置对象
        """
        return Config()
    
    def merge_configs(self, *configs: Config) -> Config:
        """合并多个配置，后面的覆盖前面的
        
        Args:
            *configs: 要合并的配置对象列表
            
        Returns:
            合并后的配置对象
        """
        if not configs:
            return Config()
        
        # 从第一个配置开始
        result = Config()
        
        for config in configs:
            # 合并 project 配置
            if config.project.name is not None:
                result.project.name = config.project.name
            
            # 合并 tools 配置
            for tool_name, tool_config in config.tools.items():
                result.tools[tool_name] = tool_config
            
            # 合并 registry 配置（逐字段）
            if config.registry.npm != RegistryConfig().npm:
                result.registry.npm = config.registry.npm
            if config.registry.bun != RegistryConfig().bun:
                result.registry.bun = config.registry.bun
            if config.registry.pypi != RegistryConfig().pypi:
                result.registry.pypi = config.registry.pypi
            if config.registry.python_install != RegistryConfig().python_install:
                result.registry.python_install = config.registry.python_install
        
        return result
    
    def load_with_priority(
        self,
        cli_config: Optional[Path] = None,
        project_config: Path = Path(".kickstartrc"),
        user_config: Path = Path.home() / ".kickstartrc"
    ) -> Config:
        """按优先级加载配置: CLI > 项目 > 用户 > 默认
        
        Args:
            cli_config: CLI 指定的配置文件路径
            project_config: 项目配置文件路径
            user_config: 用户配置文件路径
            
        Returns:
            合并后的配置对象
        """
        configs = []
        
        # 1. 默认配置（最低优先级）
        configs.append(self.load_from_defaults())
        
        # 2. 用户配置
        if user_config.exists():
            try:
                configs.append(self.load_from_file(user_config))
            except Exception:
                # 用户配置加载失败，跳过
                pass
        
        # 3. 项目配置
        if project_config.exists():
            try:
                configs.append(self.load_from_file(project_config))
            except Exception:
                # 项目配置加载失败，跳过
                pass
        
        # 4. CLI 配置（最高优先级）
        if cli_config is not None and cli_config.exists():
            configs.append(self.load_from_file(cli_config))
        
        return self.merge_configs(*configs)
    
    def save_to_file(self, config: Config, path: Path) -> None:
        """保存配置到 YAML 文件
        
        Args:
            config: 要保存的配置对象
            path: 目标文件路径
        """
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为字典
        data = config.to_dict()
        
        # 写入文件
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def validate(self, config: Config) -> List[str]:
        """验证配置，返回错误列表
        
        Args:
            config: 要验证的配置对象
            
        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []
        
        # 验证工具名称是否有效
        valid_tools = {
            "nvm", "node", "conda", "bun", "uv",
            "claude-code", "codex", "spec-kit", "bmad-method"
        }
        
        for tool_name in config.tools.keys():
            if tool_name not in valid_tools:
                errors.append(f"无效的工具名称: {tool_name}")
        
        # 验证 install_via 字段
        valid_install_methods = {"bun", "npm", "brew", None}
        for tool_name, tool_config in config.tools.items():
            if tool_config.install_via not in valid_install_methods:
                errors.append(
                    f"工具 {tool_name} 的 install_via 值无效: {tool_config.install_via}"
                )
        
        # 验证镜像源 URL 格式（简单检查）
        registry = config.registry
        for field_name in ["npm", "bun", "pypi", "python_install"]:
            url = getattr(registry, field_name)
            if not url or not isinstance(url, str):
                errors.append(f"镜像源 {field_name} 的 URL 无效")
        
        return errors
