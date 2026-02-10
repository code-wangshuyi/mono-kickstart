"""镜像源配置模块

该模块负责配置各工具的镜像源，包括 npm、Bun、uv、pip 和 conda。
"""

import configparser
import subprocess
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse
import tomllib
import yaml

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
    
    def configure_pip_mirror(self) -> bool:
        """配置 pip 镜像源

        创建或更新 ~/.pip/pip.conf 配置文件。

        Returns:
            配置是否成功
        """
        try:
            pip_dir = Path.home() / ".pip"
            pip_conf_path = pip_dir / "pip.conf"

            # 解析 trusted-host
            parsed = urlparse(self.registry_config.pypi)
            trusted_host = parsed.hostname or ""

            # 使用 configparser 保留已有配置
            config = configparser.ConfigParser()
            if pip_conf_path.exists():
                config.read(str(pip_conf_path))

            if not config.has_section("global"):
                config.add_section("global")

            config.set("global", "index-url", self.registry_config.pypi)
            config.set("global", "trusted-host", trusted_host)

            # 写入配置文件
            pip_dir.mkdir(parents=True, exist_ok=True)
            with open(pip_conf_path, 'w', encoding='utf-8') as f:
                config.write(f)

            return True
        except Exception:
            return False

    def configure_conda_mirror(self) -> bool:
        """配置 Conda 镜像源

        创建或更新 ~/.condarc 配置文件。

        Returns:
            配置是否成功
        """
        try:
            condarc_path = Path.home() / ".condarc"
            base_url = self.registry_config.conda.rstrip('/')

            # 读取现有配置
            existing_config = {}
            if condarc_path.exists():
                with open(condarc_path, 'r', encoding='utf-8') as f:
                    existing_config = yaml.safe_load(f) or {}

            # 更新镜像相关字段，保留其他设置
            existing_config["channels"] = ["defaults"]
            existing_config["show_channel_urls"] = True
            existing_config["default_channels"] = [
                f"{base_url}/pkgs/main",
                f"{base_url}/pkgs/r",
                f"{base_url}/pkgs/msys2",
            ]
            existing_config["custom_channels"] = {
                "conda-forge": f"{base_url}/cloud",
                "pytorch": f"{base_url}/cloud",
            }

            # 写入配置文件
            with open(condarc_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(existing_config, f, default_flow_style=False, allow_unicode=True)

            return True
        except Exception:
            return False

    def verify_pip_mirror(self) -> bool:
        """验证 pip 镜像源配置

        检查 ~/.pip/pip.conf 文件是否存在且包含正确的 index-url。

        Returns:
            验证是否成功
        """
        try:
            pip_conf_path = Path.home() / ".pip" / "pip.conf"

            if not pip_conf_path.exists():
                return False

            config = configparser.ConfigParser()
            config.read(str(pip_conf_path))

            index_url = config.get("global", "index-url", fallback=None)
            if index_url:
                return index_url.rstrip('/') == self.registry_config.pypi.rstrip('/')

            return False
        except Exception:
            return False

    def verify_conda_mirror(self) -> bool:
        """验证 Conda 镜像源配置

        检查 ~/.condarc 文件是否存在且包含正确的镜像源配置。

        Returns:
            验证是否成功
        """
        try:
            condarc_path = Path.home() / ".condarc"

            if not condarc_path.exists():
                return False

            with open(condarc_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config or "default_channels" not in config:
                return False

            base_url = self.registry_config.conda.rstrip('/')
            expected_channel = f"{base_url}/pkgs/main"

            return expected_channel in config["default_channels"]
        except Exception:
            return False

    def reset_npm_mirror(self) -> bool:
        """重置 npm 镜像源为默认值

        Returns:
            重置是否成功
        """
        try:
            result = subprocess.run(
                ["npm", "config", "delete", "registry"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return True  # 命令不存在视为已重置

    def reset_bun_mirror(self) -> bool:
        """重置 Bun 镜像源

        删除 ~/.bunfig.toml 中的 registry 设置。

        Returns:
            重置是否成功
        """
        try:
            bunfig_path = Path.home() / ".bunfig.toml"

            if not bunfig_path.exists():
                return True  # 文件不存在视为已重置

            with open(bunfig_path, 'rb') as f:
                config = tomllib.load(f)

            # 删除 install.registry
            if "install" in config and "registry" in config["install"]:
                config["install"].pop("registry")
                # 如果 install 段为空，也删除
                if not config["install"]:
                    config.pop("install")

            if not config:
                # 配置为空，删除文件
                bunfig_path.unlink()
            else:
                # 重写配置文件
                config_lines = []
                for section, values in config.items():
                    config_lines.append(f"[{section}]")
                    if isinstance(values, dict):
                        for key, value in values.items():
                            if isinstance(value, str):
                                config_lines.append(f'{key} = "{value}"')
                            elif isinstance(value, bool):
                                config_lines.append(f'{key} = {str(value).lower()}')
                            else:
                                config_lines.append(f'{key} = {value}')
                    config_lines.append("")

                with open(bunfig_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(config_lines))

            return True
        except Exception:
            return False

    def reset_uv_mirror(self) -> bool:
        """重置 uv 镜像源

        删除 ~/.config/uv/uv.toml 配置文件。

        Returns:
            重置是否成功
        """
        try:
            uv_config_path = Path.home() / ".config" / "uv" / "uv.toml"

            if uv_config_path.exists():
                uv_config_path.unlink()

            return True
        except Exception:
            return False

    def reset_pip_mirror(self) -> bool:
        """重置 pip 镜像源

        删除 ~/.pip/pip.conf 配置文件。

        Returns:
            重置是否成功
        """
        try:
            pip_conf_path = Path.home() / ".pip" / "pip.conf"

            if pip_conf_path.exists():
                pip_conf_path.unlink()

            return True
        except Exception:
            return False

    def reset_conda_mirror(self) -> bool:
        """重置 Conda 镜像源

        重写 ~/.condarc 为默认配置。

        Returns:
            重置是否成功
        """
        try:
            condarc_path = Path.home() / ".condarc"

            if not condarc_path.exists():
                return True  # 文件不存在视为已重置

            # 读取现有配置，保留非镜像设置
            with open(condarc_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}

            # 删除镜像相关字段
            config.pop("default_channels", None)
            config.pop("custom_channels", None)
            config["channels"] = ["defaults"]

            with open(condarc_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)

            return True
        except Exception:
            return False

    def show_mirror_status(self) -> Dict[str, Dict[str, str]]:
        """读取各工具当前镜像配置

        Returns:
            字典，键为工具名称，值为 {"configured": url, "default": upstream_url}
        """
        status = {}

        # npm
        npm_configured = "未配置"
        try:
            result = subprocess.run(
                ["npm", "get", "registry"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                npm_configured = result.stdout.strip()
        except Exception:
            npm_configured = "无法检测（npm 不可用）"
        status["npm"] = {"configured": npm_configured, "default": "https://registry.npmjs.org/"}

        # bun
        bun_configured = "未配置"
        try:
            bunfig_path = Path.home() / ".bunfig.toml"
            if bunfig_path.exists():
                with open(bunfig_path, 'rb') as f:
                    config = tomllib.load(f)
                registry = config.get("install", {}).get("registry")
                if registry:
                    bun_configured = registry
        except Exception:
            bun_configured = "无法检测"
        status["bun"] = {"configured": bun_configured, "default": "https://registry.npmjs.org/"}

        # pip
        pip_configured = "未配置"
        try:
            pip_conf_path = Path.home() / ".pip" / "pip.conf"
            if pip_conf_path.exists():
                config = configparser.ConfigParser()
                config.read(str(pip_conf_path))
                index_url = config.get("global", "index-url", fallback=None)
                if index_url:
                    pip_configured = index_url
        except Exception:
            pip_configured = "无法检测"
        status["pip"] = {"configured": pip_configured, "default": "https://pypi.org/simple"}

        # uv
        uv_configured = "未配置"
        try:
            uv_config_path = Path.home() / ".config" / "uv" / "uv.toml"
            if uv_config_path.exists():
                content = uv_config_path.read_text()
                # 提取 url = "..." 行
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith('url = "'):
                        uv_configured = line.split('"')[1]
                        break
        except Exception:
            uv_configured = "无法检测"
        status["uv"] = {"configured": uv_configured, "default": "https://pypi.org/simple"}

        # conda
        conda_configured = "未配置"
        try:
            condarc_path = Path.home() / ".condarc"
            if condarc_path.exists():
                with open(condarc_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                if config and "default_channels" in config:
                    channels = config["default_channels"]
                    if channels:
                        conda_configured = channels[0]
        except Exception:
            conda_configured = "无法检测"
        status["conda"] = {"configured": conda_configured, "default": "https://repo.anaconda.com/pkgs/main"}

        return status

    def configure_all(self) -> Dict[str, bool]:
        """配置所有镜像源

        依次配置 npm、Bun、uv、pip 和 conda 的镜像源。

        Returns:
            字典，键为工具名称，值为配置是否成功
        """
        results = {}

        results["npm"] = self.configure_npm_mirror()
        results["bun"] = self.configure_bun_mirror()
        results["uv"] = self.configure_uv_mirror()
        results["pip"] = self.configure_pip_mirror()
        results["conda"] = self.configure_conda_mirror()

        return results
