"""镜像源配置模块

该模块负责配置各工具的镜像源，包括 npm、Bun 和 uv。
"""

import subprocess
from pathlib import Path
from typing import Dict, Optional
import tomllib

from .config import RegistryConfig


class MirrorConfigurator:
    """镜像源配置器
    
    负责配置 npm、Bun 和 uv 的镜像源，以加速中国大陆地区的下载速度。
    """
    
    def __init__(self, registry_config: RegistryConfig):
        """初始化镜像源配置器
        
        Args:
            registry_config: 镜像源配置对象
        """
        self.registry_config = registry_config
    
    def configure_npm_mirror(self) -> bool:
        """配置 npm 镜像源
        
        使用 npm config set 命令配置 registry。
        
        Returns:
            配置是否成功
        """
        try:
            # 设置 npm registry
            result = subprocess.run(
                ["npm", "config", "set", "registry", self.registry_config.npm],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def configure_bun_mirror(self) -> bool:
        """配置 Bun 镜像源
        
        创建 ~/.bunfig.toml 配置文件并设置 registry。
        
        Returns:
            配置是否成功
        """
        try:
            bunfig_path = Path.home() / ".bunfig.toml"
            
            # 读取现有配置（如果存在）
            existing_config = {}
            if bunfig_path.exists():
                with open(bunfig_path, 'rb') as f:
                    existing_config = tomllib.load(f)
            
            # 构建新配置
            # 保留现有配置，只更新 install.registry
            config_lines = []
            
            # 如果有其他配置，先写入
            for section, values in existing_config.items():
                if section != "install":
                    config_lines.append(f"[{section}]")
                    if isinstance(values, dict):
                        for key, value in values.items():
                            if isinstance(value, str):
                                config_lines.append(f'{key} = "{value}"')
                            elif isinstance(value, bool):
                                # 使用小写的 true/false
                                config_lines.append(f'{key} = {str(value).lower()}')
                            else:
                                config_lines.append(f'{key} = {value}')
                    config_lines.append("")
            
            # 写入 install 配置
            config_lines.append("[install]")
            config_lines.append(f'registry = "{self.registry_config.bun}"')
            
            # 如果 install 中有其他配置，也保留
            if "install" in existing_config:
                for key, value in existing_config["install"].items():
                    if key != "registry":
                        if isinstance(value, str):
                            config_lines.append(f'{key} = "{value}"')
                        elif isinstance(value, bool):
                            # 使用小写的 true/false
                            config_lines.append(f'{key} = {str(value).lower()}')
                        else:
                            config_lines.append(f'{key} = {value}')
            
            config_lines.append("")
            
            # 写入配置文件
            bunfig_path.parent.mkdir(parents=True, exist_ok=True)
            with open(bunfig_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(config_lines))
            
            return True
        except Exception:
            return False
    
    def configure_uv_mirror(self) -> bool:
        """配置 uv PyPI 镜像源和 CPython 下载代理
        
        创建 ~/.config/uv/uv.toml 配置文件，包含：
        1. python-install-mirror 配置（在 [[index]] 之前）
        2. PyPI 镜像源配置
        
        Returns:
            配置是否成功
        """
        try:
            uv_config_dir = Path.home() / ".config" / "uv"
            uv_config_path = uv_config_dir / "uv.toml"
            
            # 创建配置目录
            uv_config_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建配置内容
            # 注意：python-install-mirror 必须在 [[index]] 之前
            config_lines = [
                "# uv 配置文件",
                "# 由 mono-kickstart 自动生成",
                "",
                "# CPython 下载代理",
                f'python-install-mirror = "{self.registry_config.python_install}"',
                "",
                "# PyPI 镜像源",
                "[[index]]",
                f'url = "{self.registry_config.pypi}"',
                ""
            ]
            
            # 写入配置文件
            with open(uv_config_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(config_lines))
            
            return True
        except Exception:
            return False
    
    def verify_npm_mirror(self) -> bool:
        """验证 npm 镜像源配置
        
        通过 npm get registry 命令验证配置是否生效。
        
        Returns:
            验证是否成功
        """
        try:
            result = subprocess.run(
                ["npm", "get", "registry"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # 检查输出是否包含配置的镜像源
                output = result.stdout.strip()
                # 移除末尾的斜杠进行比较
                configured = self.registry_config.npm.rstrip('/')
                actual = output.rstrip('/')
                return configured == actual
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def verify_bun_mirror(self) -> bool:
        """验证 Bun 镜像源配置
        
        检查 ~/.bunfig.toml 文件是否存在且包含正确的配置。
        
        Returns:
            验证是否成功
        """
        try:
            bunfig_path = Path.home() / ".bunfig.toml"
            
            if not bunfig_path.exists():
                return False
            
            # 读取配置文件
            with open(bunfig_path, 'rb') as f:
                config = tomllib.load(f)
            
            # 检查 registry 配置
            registry = config.get("install", {}).get("registry")
            if registry:
                # 移除末尾的斜杠进行比较
                configured = self.registry_config.bun.rstrip('/')
                actual = registry.rstrip('/')
                return configured == actual
            
            return False
        except Exception:
            return False
    
    def verify_uv_mirror(self) -> bool:
        """验证 uv 镜像源配置
        
        检查 ~/.config/uv/uv.toml 文件是否存在且包含正确的配置。
        
        Returns:
            验证是否成功
        """
        try:
            uv_config_path = Path.home() / ".config" / "uv" / "uv.toml"
            
            if not uv_config_path.exists():
                return False
            
            # 读取配置文件内容
            with open(uv_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含 python-install-mirror 配置
            if f'python-install-mirror = "{self.registry_config.python_install}"' not in content:
                return False
            
            # 检查是否包含 PyPI 镜像源配置
            if f'url = "{self.registry_config.pypi}"' not in content:
                return False
            
            # 检查 python-install-mirror 是否在 [[index]] 之前
            python_install_pos = content.find('python-install-mirror')
            index_pos = content.find('[[index]]')
            
            if python_install_pos == -1 or index_pos == -1:
                return False
            
            return python_install_pos < index_pos
        except Exception:
            return False
    
    def configure_all(self) -> Dict[str, bool]:
        """配置所有镜像源
        
        依次配置 npm、Bun 和 uv 的镜像源。
        
        Returns:
            字典，键为工具名称，值为配置是否成功
        """
        results = {}
        
        results["npm"] = self.configure_npm_mirror()
        results["bun"] = self.configure_bun_mirror()
        results["uv"] = self.configure_uv_mirror()
        
        return results
