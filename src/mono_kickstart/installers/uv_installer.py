"""uv 安装器模块

该模块实现 uv 的安装、升级和验证逻辑。
"""

import shutil
from pathlib import Path
from typing import Optional

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import PlatformInfo


class UVInstaller(ToolInstaller):
    """uv 安装器
    
    负责安装、升级和验证 uv。
    uv 通过执行官方安装脚本进行安装。
    
    Attributes:
        platform_info: 平台信息
        config: 工具配置
        install_script_url: 安装脚本 URL
    """
    
    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化 uv 安装器
        
        Args:
            platform_info: 平台信息
            config: 工具配置
        """
        super().__init__(platform_info, config)
        
        # uv 官方安装脚本 URL
        self.install_script_url = "https://astral.sh/uv/install.sh"
    
    def verify(self) -> bool:
        """验证 uv 是否已正确安装
        
        检查 uv 命令是否可用，并尝试执行 uv --version 命令。
        
        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        # 检查 uv 命令是否在 PATH 中
        if not shutil.which("uv"):
            return False
        
        # 尝试执行 uv --version 命令
        returncode, stdout, stderr = self.run_command(
            "uv --version",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        return returncode == 0
    
    def _get_installed_version(self) -> Optional[str]:
        """获取已安装的 uv 版本
        
        Returns:
            Optional[str]: 版本号，如果无法获取则返回 None
        """
        if not shutil.which("uv"):
            return None
        
        returncode, stdout, stderr = self.run_command(
            "uv --version",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        if returncode == 0:
            # uv --version 输出格式: "uv 0.1.0"
            # 提取版本号
            parts = stdout.strip().split()
            if len(parts) >= 2:
                return parts[1]
        
        return None
    
    def install(self) -> InstallReport:
        """安装 uv
        
        执行以下步骤：
        1. 检查 uv 是否已安装
        2. 执行官方安装脚本
        3. 验证安装
        
        Returns:
            InstallReport: 安装报告
        """
        # 检查是否已安装
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="uv",
                result=InstallResult.SKIPPED,
                message="uv 已安装，跳过安装",
                version=version
            )
        
        try:
            # 执行官方安装脚本
            # curl -LsSf https://astral.sh/uv/install.sh | sh
            install_cmd = f"curl -LsSf {self.install_script_url} | sh"
            returncode, stdout, stderr = self.run_command(
                install_cmd,
                shell=True,
                timeout=300,
                max_retries=2
            )
            
            if returncode != 0:
                return InstallReport(
                    tool_name="uv",
                    result=InstallResult.FAILED,
                    message="执行 uv 安装脚本失败",
                    error=stderr or "安装脚本返回非零退出码"
                )
            
            # 验证安装
            if not self.verify():
                return InstallReport(
                    tool_name="uv",
                    result=InstallResult.FAILED,
                    message="uv 安装验证失败",
                    error="安装脚本执行成功，但无法验证 uv 是否正确安装"
                )
            
            # 获取安装的版本
            version = self._get_installed_version()
            
            return InstallReport(
                tool_name="uv",
                result=InstallResult.SUCCESS,
                message="uv 安装成功",
                version=version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="uv",
                result=InstallResult.FAILED,
                message="uv 安装过程中发生异常",
                error=str(e)
            )
    
    def upgrade(self) -> InstallReport:
        """升级 uv
        
        uv 的升级通过执行 `uv self update` 命令实现。
        
        Returns:
            InstallReport: 升级报告
        """
        # 检查是否已安装
        if not self.verify():
            return InstallReport(
                tool_name="uv",
                result=InstallResult.FAILED,
                message="uv 未安装，无法升级",
                error="请先安装 uv"
            )
        
        try:
            # 记录升级前的版本
            old_version = self._get_installed_version()
            
            # 执行升级命令
            returncode, stdout, stderr = self.run_command(
                "uv self update",
                shell=True,
                timeout=300,
                max_retries=2
            )
            
            if returncode != 0:
                return InstallReport(
                    tool_name="uv",
                    result=InstallResult.FAILED,
                    message="执行 uv 升级命令失败",
                    error=stderr or "升级命令返回非零退出码"
                )
            
            # 验证升级
            if not self.verify():
                return InstallReport(
                    tool_name="uv",
                    result=InstallResult.FAILED,
                    message="uv 升级验证失败",
                    error="升级命令执行成功，但无法验证 uv 是否正确安装"
                )
            
            # 获取升级后的版本
            new_version = self._get_installed_version()
            
            return InstallReport(
                tool_name="uv",
                result=InstallResult.SUCCESS,
                message=f"uv 升级成功 ({old_version} -> {new_version})",
                version=new_version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="uv",
                result=InstallResult.FAILED,
                message="uv 升级过程中发生异常",
                error=str(e)
            )
