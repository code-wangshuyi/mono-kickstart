"""
工具检测器模块

检测开发工具是否已安装及其版本信息。
"""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class ToolStatus:
    """工具状态
    
    Attributes:
        name: 工具名称
        installed: 是否已安装
        version: 版本号（如果已安装）
        path: 可执行文件路径（如果已安装）
    """
    name: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None


class ToolDetector:
    """工具检测器
    
    检测各种开发工具的安装状态和版本信息。
    """
    
    def is_command_available(self, command: str) -> bool:
        """检查命令是否在 PATH 中可用
        
        Args:
            command: 命令名称
            
        Returns:
            bool: 如果命令可用返回 True，否则返回 False
        """
        return shutil.which(command) is not None
    
    def get_command_version(
        self,
        command: str,
        version_arg: str = "--version"
    ) -> Optional[str]:
        """获取命令的版本号
        
        Args:
            command: 命令名称
            version_arg: 获取版本的参数（默认为 --version）
            
        Returns:
            Optional[str]: 版本号字符串，如果无法获取则返回 None
        """
        try:
            result = subprocess.run(
                [command, version_arg],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 尝试从 stdout 或 stderr 中提取版本号
            output = result.stdout + result.stderr
            
            # 常见的版本号模式
            # 匹配 v1.2.3, 1.2.3, version 1.2.3 等格式
            version_patterns = [
                r'v?(\d+\.\d+\.\d+(?:\.\d+)?)',  # 1.2.3 或 v1.2.3
                r'version\s+v?(\d+\.\d+\.\d+)',   # version 1.2.3
                r'(\d+\.\d+\.\d+)',                # 简单的 1.2.3
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # 如果没有匹配到标准版本号，返回第一行（去除空白）
            first_line = output.strip().split('\n')[0] if output.strip() else None
            return first_line
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return None
    
    def detect_nvm(self) -> ToolStatus:
        """检测 NVM
        
        NVM 是一个 shell 函数，不是独立的可执行文件，需要特殊处理。
        
        Returns:
            ToolStatus: NVM 的状态信息
        """
        # NVM 通常安装在 ~/.nvm 目录
        nvm_dir = Path.home() / ".nvm"
        nvm_sh = nvm_dir / "nvm.sh"
        
        if nvm_sh.exists():
            # 尝试通过 source nvm.sh 并执行 nvm --version 获取版本
            try:
                # 使用 bash -c 来 source nvm.sh 并获取版本
                result = subprocess.run(
                    ["bash", "-c", f"source {nvm_sh} && nvm --version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    version = result.stdout.strip()
                    return ToolStatus(
                        name="nvm",
                        installed=True,
                        version=version,
                        path=str(nvm_sh)
                    )
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
            
            # 如果无法获取版本，但文件存在，仍然认为已安装
            return ToolStatus(
                name="nvm",
                installed=True,
                version=None,
                path=str(nvm_sh)
            )
        
        return ToolStatus(name="nvm", installed=False)
    
    def detect_node(self) -> ToolStatus:
        """检测 Node.js
        
        Returns:
            ToolStatus: Node.js 的状态信息
        """
        if not self.is_command_available("node"):
            return ToolStatus(name="node", installed=False)
        
        version = self.get_command_version("node", "--version")
        path = shutil.which("node")
        
        return ToolStatus(
            name="node",
            installed=True,
            version=version,
            path=path
        )
    
    def detect_conda(self) -> ToolStatus:
        """检测 Conda
        
        Returns:
            ToolStatus: Conda 的状态信息
        """
        if not self.is_command_available("conda"):
            return ToolStatus(name="conda", installed=False)
        
        version = self.get_command_version("conda", "--version")
        path = shutil.which("conda")
        
        return ToolStatus(
            name="conda",
            installed=True,
            version=version,
            path=path
        )
    
    def detect_bun(self) -> ToolStatus:
        """检测 Bun
        
        Returns:
            ToolStatus: Bun 的状态信息
        """
        if not self.is_command_available("bun"):
            return ToolStatus(name="bun", installed=False)
        
        version = self.get_command_version("bun", "--version")
        path = shutil.which("bun")
        
        return ToolStatus(
            name="bun",
            installed=True,
            version=version,
            path=path
        )
    
    def detect_uv(self) -> ToolStatus:
        """检测 uv
        
        Returns:
            ToolStatus: uv 的状态信息
        """
        if not self.is_command_available("uv"):
            return ToolStatus(name="uv", installed=False)
        
        version = self.get_command_version("uv", "--version")
        path = shutil.which("uv")
        
        return ToolStatus(
            name="uv",
            installed=True,
            version=version,
            path=path
        )
    
    def detect_claude_code(self) -> ToolStatus:
        """检测 Claude Code CLI
        
        Returns:
            ToolStatus: Claude Code CLI 的状态信息
        """
        if not self.is_command_available("claude"):
            return ToolStatus(name="claude-code", installed=False)
        
        version = self.get_command_version("claude", "--version")
        path = shutil.which("claude")
        
        return ToolStatus(
            name="claude-code",
            installed=True,
            version=version,
            path=path
        )
    
    def detect_codex(self) -> ToolStatus:
        """检测 Codex CLI
        
        Returns:
            ToolStatus: Codex CLI 的状态信息
        """
        if not self.is_command_available("codex"):
            return ToolStatus(name="codex", installed=False)
        
        version = self.get_command_version("codex", "--version")
        path = shutil.which("codex")
        
        return ToolStatus(
            name="codex",
            installed=True,
            version=version,
            path=path
        )
    
    def detect_npx(self) -> ToolStatus:
        """检测 npx

        Returns:
            ToolStatus: npx 的状态信息
        """
        if not self.is_command_available("npx"):
            return ToolStatus(name="npx", installed=False)

        version = self.get_command_version("npx", "--version")
        path = shutil.which("npx")

        return ToolStatus(
            name="npx",
            installed=True,
            version=version,
            path=path
        )

    def detect_spec_kit(self) -> ToolStatus:
        """检测 Spec Kit
        
        Spec Kit 通过 uv tool install 安装，命令名为 specify。
        
        Returns:
            ToolStatus: Spec Kit 的状态信息
        """
        if not self.is_command_available("specify"):
            return ToolStatus(name="spec-kit", installed=False)
        
        version = self.get_command_version("specify", "version")
        path = shutil.which("specify")
        
        return ToolStatus(
            name="spec-kit",
            installed=True,
            version=version,
            path=path
        )
    
    def detect_uipro(self) -> ToolStatus:
        """检测 UIPro CLI

        UIPro CLI 通过 npm/bun 全局安装，命令名为 uipro。

        Returns:
            ToolStatus: UIPro CLI 的状态信息
        """
        if not self.is_command_available("uipro"):
            return ToolStatus(name="uipro", installed=False)

        version = self.get_command_version("uipro", "versions")
        path = shutil.which("uipro")

        return ToolStatus(
            name="uipro",
            installed=True,
            version=version,
            path=path
        )

    def detect_bmad(self) -> ToolStatus:
        """检测 BMad Method
        
        BMad Method 通过 npx/bunx 安装，命令名为 bmad。
        
        Returns:
            ToolStatus: BMad Method 的状态信息
        """
        if not self.is_command_available("bmad"):
            return ToolStatus(name="bmad-method", installed=False)
        
        version = self.get_command_version("bmad", "--version")
        path = shutil.which("bmad")
        
        return ToolStatus(
            name="bmad-method",
            installed=True,
            version=version,
            path=path
        )
    
    def detect_pip(self) -> ToolStatus:
        """检测 pip

        检查 pip3 或 pip 是否可用。

        Returns:
            ToolStatus: pip 的状态信息
        """
        # 优先检查 pip3
        cmd = None
        if self.is_command_available("pip3"):
            cmd = "pip3"
        elif self.is_command_available("pip"):
            cmd = "pip"

        if cmd is None:
            return ToolStatus(name="pip", installed=False)

        version = self.get_command_version(cmd, "--version")
        path = shutil.which(cmd)

        return ToolStatus(
            name="pip",
            installed=True,
            version=version,
            path=path
        )

    def detect_mirror_tools(self) -> Dict[str, ToolStatus]:
        """检测支持镜像配置的工具

        Returns:
            Dict[str, ToolStatus]: 工具名称到状态的映射
        """
        return {
            "npm": self.detect_node(),  # npm 随 node 一起安装
            "bun": self.detect_bun(),
            "pip": self.detect_pip(),
            "uv": self.detect_uv(),
            "conda": self.detect_conda(),
        }

    def detect_all_tools(self) -> Dict[str, ToolStatus]:
        """检测所有工具
        
        Returns:
            Dict[str, ToolStatus]: 工具名称到状态的映射
        """
        tools = {
            "nvm": self.detect_nvm(),
            "node": self.detect_node(),
            "conda": self.detect_conda(),
            "bun": self.detect_bun(),
            "uv": self.detect_uv(),
            "claude-code": self.detect_claude_code(),
            "codex": self.detect_codex(),
            "npx": self.detect_npx(),
            "uipro": self.detect_uipro(),
            "spec-kit": self.detect_spec_kit(),
            "bmad-method": self.detect_bmad(),
        }
        
        return tools
