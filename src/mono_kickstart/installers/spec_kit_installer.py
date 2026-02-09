"""Spec Kit 安装器模块

该模块实现 Spec Kit 的安装、升级和验证逻辑。
"""

import re
import shutil
from pathlib import Path
from typing import Optional

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import PlatformInfo


class SpecKitInstaller(ToolInstaller):
    """Spec Kit 安装器
    
    负责安装、升级和验证 Spec Kit。
    Spec Kit 通过 uv tool install 从 GitHub 仓库安装。
    
    Attributes:
        platform_info: 平台信息
        config: 工具配置
        github_repo: GitHub 仓库地址
    """
    
    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化 Spec Kit 安装器
        
        Args:
            platform_info: 平台信息
            config: 工具配置
        """
        super().__init__(platform_info, config)
        
        # Spec Kit GitHub 仓库地址
        self.github_repo = "git+https://github.com/github/spec-kit.git"
    
    def verify(self) -> bool:
        """验证 Spec Kit 是否已正确安装

        检查 specify 命令是否可用，并尝试执行 specify version 命令。

        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        # 检查 specify 命令是否在 PATH 中
        if not shutil.which("specify"):
            return False

        # 尝试执行 specify version 命令
        returncode, stdout, stderr = self.run_command(
            "specify version",
            shell=True,
            timeout=10,
            max_retries=1
        )

        return returncode == 0
    
    def _get_installed_version(self) -> Optional[str]:
        """获取已安装的 Spec Kit 版本

        从 specify version 输出中提取 CLI Version。

        Returns:
            Optional[str]: 版本号，如果无法获取则返回 None
        """
        if not shutil.which("specify"):
            return None

        returncode, stdout, stderr = self.run_command(
            "specify version",
            shell=True,
            timeout=10,
            max_retries=1
        )

        if returncode == 0:
            # specify version 输出富文本表格，提取 "CLI Version    0.0.22"
            match = re.search(r"CLI Version\s+(\S+)", stdout)
            if match:
                return match.group(1)

        return None
    
    def install(self) -> InstallReport:
        """安装 Spec Kit
        
        执行以下步骤：
        1. 检查 Spec Kit 是否已安装
        2. 检查 uv 是否可用
        3. 使用 uv tool install 从 GitHub 安装
        4. 验证安装
        
        Returns:
            InstallReport: 安装报告
        """
        # 检查是否已安装
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="spec-kit",
                result=InstallResult.SKIPPED,
                message="Spec Kit 已安装，跳过安装",
                version=version
            )
        
        try:
            # 检查 uv 是否可用
            if not shutil.which("uv"):
                return InstallReport(
                    tool_name="spec-kit",
                    result=InstallResult.FAILED,
                    message="uv 未安装，无法安装 Spec Kit",
                    error="请先安装 uv"
                )
            
            # 使用 uv tool install 从 GitHub 安装
            install_cmd = f"uv tool install specify-cli --from {self.github_repo}"
            returncode, stdout, stderr = self.run_command(
                install_cmd,
                shell=True,
                timeout=300,
                max_retries=2
            )
            
            if returncode != 0:
                return InstallReport(
                    tool_name="spec-kit",
                    result=InstallResult.FAILED,
                    message="使用 uv tool install 安装 Spec Kit 失败",
                    error=stderr or "安装命令返回非零退出码"
                )
            
            # 验证安装
            if not self.verify():
                return InstallReport(
                    tool_name="spec-kit",
                    result=InstallResult.FAILED,
                    message="Spec Kit 安装验证失败",
                    error="安装命令执行成功，但无法验证 Spec Kit 是否正确安装"
                )
            
            # 获取安装的版本
            version = self._get_installed_version()
            
            return InstallReport(
                tool_name="spec-kit",
                result=InstallResult.SUCCESS,
                message="Spec Kit 安装成功",
                version=version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="spec-kit",
                result=InstallResult.FAILED,
                message="Spec Kit 安装过程中发生异常",
                error=str(e)
            )
    
    def upgrade(self) -> InstallReport:
        """升级 Spec Kit
        
        Spec Kit 的升级通过执行 `uv tool install specify-cli --force --from <github_repo>` 命令实现。
        
        Returns:
            InstallReport: 升级报告
        """
        # 检查是否已安装
        if not self.verify():
            return InstallReport(
                tool_name="spec-kit",
                result=InstallResult.FAILED,
                message="Spec Kit 未安装，无法升级",
                error="请先安装 Spec Kit"
            )
        
        try:
            # 检查 uv 是否可用
            if not shutil.which("uv"):
                return InstallReport(
                    tool_name="spec-kit",
                    result=InstallResult.FAILED,
                    message="uv 未安装，无法升级 Spec Kit",
                    error="请先安装 uv"
                )
            
            # 记录升级前的版本
            old_version = self._get_installed_version()
            
            # 执行升级命令（使用 --force 强制重新安装）
            upgrade_cmd = f"uv tool install specify-cli --force --from {self.github_repo}"
            returncode, stdout, stderr = self.run_command(
                upgrade_cmd,
                shell=True,
                timeout=300,
                max_retries=2
            )
            
            if returncode != 0:
                return InstallReport(
                    tool_name="spec-kit",
                    result=InstallResult.FAILED,
                    message="执行 Spec Kit 升级命令失败",
                    error=stderr or "升级命令返回非零退出码"
                )
            
            # 验证升级
            if not self.verify():
                return InstallReport(
                    tool_name="spec-kit",
                    result=InstallResult.FAILED,
                    message="Spec Kit 升级验证失败",
                    error="升级命令执行成功，但无法验证 Spec Kit 是否正确安装"
                )
            
            # 获取升级后的版本
            new_version = self._get_installed_version()
            
            return InstallReport(
                tool_name="spec-kit",
                result=InstallResult.SUCCESS,
                message=f"Spec Kit 升级成功 ({old_version} -> {new_version})",
                version=new_version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="spec-kit",
                result=InstallResult.FAILED,
                message="Spec Kit 升级过程中发生异常",
                error=str(e)
            )
