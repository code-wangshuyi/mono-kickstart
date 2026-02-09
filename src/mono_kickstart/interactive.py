"""交互式配置模块

提供交互式问答界面，帮助用户配置项目和工具选项。
"""

from typing import List, Dict, Optional
from pathlib import Path
import questionary
from questionary import Style

from .config import Config, ProjectConfig, ToolConfig, RegistryConfig


# 自定义样式
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
])


# 可用工具列表
AVAILABLE_TOOLS = [
    {"name": "NVM", "value": "nvm", "checked": True},
    {"name": "Node.js", "value": "node", "checked": True},
    {"name": "Conda", "value": "conda", "checked": True},
    {"name": "Bun", "value": "bun", "checked": True},
    {"name": "uv", "value": "uv", "checked": True},
    {"name": "Claude Code CLI", "value": "claude-code", "checked": True},
    {"name": "Codex CLI", "value": "codex", "checked": True},
    {"name": "Spec Kit", "value": "spec-kit", "checked": True},
    {"name": "BMad Method", "value": "bmad-method", "checked": True},
]


class InteractiveConfigurator:
    """交互式配置器"""
    
    def __init__(self, default_config: Optional[Config] = None):
        """初始化交互式配置器
        
        Args:
            default_config: 默认配置，用于提供默认值
        """
        self.default_config = default_config or Config()
    
    def ask_project_name(self) -> str:
        """询问项目名称
        
        Returns:
            项目名称
        """
        default_name = self.default_config.project.name or Path.cwd().name
        
        return questionary.text(
            "项目名称:",
            default=default_name,
            style=custom_style
        ).ask()
    
    def ask_tools_to_install(self) -> List[str]:
        """询问要安装的工具
        
        Returns:
            选中的工具名称列表
        """
        # 根据默认配置设置选中状态
        choices = []
        for tool in AVAILABLE_TOOLS:
            tool_config = self.default_config.tools.get(tool["value"])
            checked = tool_config.enabled if tool_config else tool["checked"]
            choices.append({
                "name": tool["name"],
                "value": tool["value"],
                "checked": checked
            })
        
        selected = questionary.checkbox(
            "选择要安装的工具:",
            choices=choices,
            style=custom_style
        ).ask()
        
        return selected or []
    
    def ask_node_version(self) -> str:
        """询问 Node.js 版本
        
        Returns:
            Node.js 版本选项
        """
        node_config = self.default_config.tools.get("node")
        default_version = node_config.version if node_config and node_config.version else "lts"
        
        # 确定默认选项的索引
        choices = ["LTS (推荐)", "Latest (最新)", "指定版本"]
        if default_version == "lts":
            default = choices[0]
        elif default_version == "latest":
            default = choices[1]
        else:
            default = choices[2]
        
        version_choice = questionary.select(
            "Node.js 版本:",
            choices=choices,
            default=default,
            style=custom_style
        ).ask()
        
        if version_choice == "指定版本":
            custom_version = questionary.text(
                "请输入 Node.js 版本号 (例如: 18.17.0):",
                default=default_version if default_version not in ["lts", "latest"] else "",
                style=custom_style
            ).ask()
            return custom_version
        elif version_choice == "Latest (最新)":
            return "latest"
        else:
            return "lts"
    
    def ask_python_version(self) -> str:
        """询问 Python 版本
        
        Returns:
            Python 版本选项
        """
        conda_config = self.default_config.tools.get("conda")
        default_version = conda_config.version if conda_config and conda_config.version else "3.11"
        
        version = questionary.text(
            "Python 版本 (用于 Conda):",
            default=default_version,
            style=custom_style
        ).ask()
        
        return version
    
    def ask_use_china_mirrors(self) -> bool:
        """询问是否使用中国镜像源
        
        Returns:
            是否使用中国镜像源
        """
        # 检查默认配置是否使用中国镜像
        default_npm = self.default_config.registry.npm
        use_mirrors = "npmmirror.com" in default_npm or "taobao.org" in default_npm
        
        return questionary.confirm(
            "是否配置中国大陆镜像源 (加速下载)?",
            default=use_mirrors,
            style=custom_style
        ).ask()
    
    def run_wizard(self) -> Config:
        """运行完整配置向导
        
        Returns:
            配置对象
        """
        print("\n🚀 欢迎使用 Mono-Kickstart 交互式配置向导!\n")
        
        # 询问项目名称
        project_name = self.ask_project_name()
        
        # 询问工具选择
        selected_tools = self.ask_tools_to_install()
        
        # 询问 Node.js 版本 (如果选择了 Node.js)
        node_version = "lts"
        if "node" in selected_tools:
            node_version = self.ask_node_version()
        
        # 询问 Python 版本 (如果选择了 Conda)
        python_version = "3.11"
        if "conda" in selected_tools:
            python_version = self.ask_python_version()
        
        # 询问是否使用中国镜像
        use_china_mirrors = self.ask_use_china_mirrors()
        
        # 构建配置对象
        config = Config()
        config.project = ProjectConfig(name=project_name)
        
        # 配置工具
        for tool in AVAILABLE_TOOLS:
            tool_name = tool["value"]
            enabled = tool_name in selected_tools
            
            tool_config = ToolConfig(enabled=enabled)
            
            # 设置特定工具的版本
            if tool_name == "node" and enabled:
                tool_config.version = node_version
            elif tool_name == "conda" and enabled:
                tool_config.version = python_version
            
            config.tools[tool_name] = tool_config
        
        # 配置镜像源
        if use_china_mirrors:
            config.registry = RegistryConfig(
                npm="https://registry.npmmirror.com/",
                bun="https://registry.npmmirror.com/",
                pypi="https://mirrors.sustech.edu.cn/pypi/web/simple",
                python_install="https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"
            )
        else:
            config.registry = RegistryConfig(
                npm="https://registry.npmjs.org/",
                bun="https://registry.npmjs.org/",
                pypi="https://pypi.org/simple",
                python_install="https://github.com/astral-sh/python-build-standalone/releases/download"
            )
        
        return config
    
    def confirm_config(self, config: Config) -> bool:
        """显示配置摘要并确认
        
        Args:
            config: 配置对象
            
        Returns:
            用户是否确认
        """
        print("\n" + "=" * 60)
        print("📋 配置摘要")
        print("=" * 60)
        
        # 项目信息
        print(f"\n项目名称: {config.project.name}")
        
        # 启用的工具
        enabled_tools = [name for name, tool_config in config.tools.items() if tool_config.enabled]
        print(f"\n启用的工具 ({len(enabled_tools)}):")
        for tool_name in enabled_tools:
            tool_config = config.tools[tool_name]
            version_info = f" (版本: {tool_config.version})" if tool_config.version else ""
            print(f"  ✓ {tool_name}{version_info}")
        
        # 镜像源配置
        print(f"\n镜像源配置:")
        print(f"  npm: {config.registry.npm}")
        print(f"  PyPI: {config.registry.pypi}")
        
        print("\n" + "=" * 60 + "\n")
        
        return questionary.confirm(
            "确认以上配置并继续?",
            default=True,
            style=custom_style
        ).ask()
