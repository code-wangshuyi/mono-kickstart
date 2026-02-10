"""GitHub Copilot CLI 安装器模块

该模块实现 GitHub Copilot CLI 的安装、升级和验证逻辑。
Copilot CLI 通过 npm 进行安装，需要 Node.js 22 或更高版本。
"""

import shutil
from typing import Optional

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import PlatformInfo


class CopilotCLIInstaller(ToolInstaller):
    """GitHub Copilot CLI 安装器
    
    负责安装、升级和验证 GitHub Copilot CLI。
    Copilot CLI 通过 npm 安装，需要 Node.js 22 或更高版本。
    仅支持 macOS 和 Linux 平台。
    
    Attributes:
        platform_info: 平台信息
        config: 工具配置
        min_node_version: 最低 Node.js 主版本号（22）
    """
    
    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化 GitHub Copilot CLI 安装器
        
        Args:
            platform_info: 平台信息
            config: 工具配置
        """
        super().__init__(platform_info, config)
        self.min_node_version = 22
    
    def verify(self) -> bool:
        """验证 Copilot CLI 是否已正确安装
        
        检查 copilot 命令是否可用，并尝试执行 copilot --version 命令。
        
        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        # 检查 copilot 命令是否在 PATH 中
        if not shutil.which("copilot"):
            return False
        
        # 尝试执行 copilot --version 命令
        returncode, stdout, stderr = self.run_command(
            "copilot --version",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        return returncode == 0
    
    def _get_installed_version(self) -> Optional[str]:
        """获取已安装的 Copilot CLI 版本
        
        Returns:
            Optional[str]: 版本号，如果无法获取则返回 None
        """
        if not shutil.which("copilot"):
            return None
        
        returncode, stdout, stderr = self.run_command(
            "copilot --version",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        if returncode == 0:
            return stdout.strip()
        
        return None
    
    def _check_node_version(self) -> tuple[bool, Optional[str]]:
        """检查 Node.js 版本是否满足要求
        
        Returns:
            tuple[bool, Optional[str]]: (是否满足要求, 错误信息)
        """
        # 检查 node 命令是否可用
        if not shutil.which("node"):
            return False, "Node.js 未安装，请先安装 Node.js"
        
        # 执行 node --version 获取版本号
        returncode, stdout, stderr = self.run_command(
            "node --version",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        if returncode != 0:
            return False, "无法获取 Node.js 版本信息"
        
        # 解析版本号（格式: v22.1.0）
        version_str = stdout.strip()
        if not version_str.startswith('v'):
            return False, f"无法解析 Node.js 版本号: {version_str}"
        
        try:
            # 移除 'v' 前缀并分割版本号
            version_parts = version_str[1:].split('.')
            major_version = int(version_parts[0])
            
            # 比较主版本号
            if major_version < self.min_node_version:
                return False, f"Node.js 版本过低（当前: {version_str}，需要: >= v{self.min_node_version}.0.0）"
            
            return True, None
            
        except (ValueError, IndexError):
            return False, f"无法解析 Node.js 版本号: {version_str}"
    
    def _install_via_npm(self) -> tuple[bool, str]:
        """通过 npm 安装 Copilot CLI
        
        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        install_cmd = "npm install -g @github/copilot"
        returncode, stdout, stderr = self.run_command(
            install_cmd,
            shell=True,
            timeout=300,
            max_retries=3
        )
        
        if returncode != 0:
            return False, stderr or "安装命令返回非零退出码"
        
        return True, ""
    
    def install(self) -> InstallReport:
        """安装 GitHub Copilot CLI
        
        执行以下步骤：
        1. 检查平台是否支持（仅 macOS 和 Linux）
        2. 检查 Copilot CLI 是否已安装
        3. 检查 Node.js 版本是否满足要求
        4. 通过 npm 安装 Copilot CLI
        5. 验证安装
        
        Returns:
            InstallReport: 安装报告
        """
        # 检查平台是否为不支持的操作系统（Windows）
        from ..platform_detector import OS
        if self.platform_info.os not in [OS.MACOS, OS.LINUX]:
            return InstallReport(
                tool_name="copilot-cli",
                result=InstallResult.FAILED,
                message="不支持的操作系统",
                error="GitHub Copilot CLI 安装器仅支持 macOS 和 Linux"
            )
        
        # 检查是否已安装
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="copilot-cli",
                result=InstallResult.SKIPPED,
                message="GitHub Copilot CLI 已安装，跳过安装",
                version=version
            )
        
        try:
            # 检查 Node.js 版本
            node_ok, node_error = self._check_node_version()
            if not node_ok:
                return InstallReport(
                    tool_name="copilot-cli",
                    result=InstallResult.FAILED,
                    message="Node.js 版本不满足要求",
                    error=node_error
                )
            
            # 通过 npm 安装
            install_success, install_error = self._install_via_npm()
            
            if not install_success:
                return InstallReport(
                    tool_name="copilot-cli",
                    result=InstallResult.FAILED,
                    message="通过 npm 安装 GitHub Copilot CLI 失败",
                    error=install_error
                )
            
            # 验证安装
            if not self.verify():
                return InstallReport(
                    tool_name="copilot-cli",
                    result=InstallResult.FAILED,
                    message="GitHub Copilot CLI 安装验证失败",
                    error="安装命令执行成功，但无法验证 Copilot CLI 是否正确安装"
                )
            
            # 获取安装的版本
            version = self._get_installed_version()
            
            return InstallReport(
                tool_name="copilot-cli",
                result=InstallResult.SUCCESS,
                message="GitHub Copilot CLI 安装成功",
                version=version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="copilot-cli",
                result=InstallResult.FAILED,
                message="GitHub Copilot CLI 安装过程中发生异常",
                error=str(e)
            )
    
    def upgrade(self) -> InstallReport:
        """升级 GitHub Copilot CLI
        
        执行以下步骤：
        1. 检查平台是否支持（仅 macOS 和 Linux）
        2. 检查 Copilot CLI 是否已安装
        3. 记录当前版本
        4. 使用 npm 执行升级命令
        5. 验证升级
        6. 返回升级报告（包含版本变化）
        
        Returns:
            InstallReport: 升级报告
        """
        # 检查平台是否为不支持的操作系统（Windows）
        from ..platform_detector import OS
        if self.platform_info.os not in [OS.MACOS, OS.LINUX]:
            return InstallReport(
                tool_name="copilot-cli",
                result=InstallResult.FAILED,
                message="不支持的操作系统",
                error="GitHub Copilot CLI 安装器仅支持 macOS 和 Linux"
            )
        
        # 检查是否已安装
        if not self.verify():
            return InstallReport(
                tool_name="copilot-cli",
                result=InstallResult.FAILED,
                message="GitHub Copilot CLI 未安装，无法升级",
                error="请先安装 GitHub Copilot CLI"
            )
        
        try:
            # 记录升级前的版本
            old_version = self._get_installed_version()
            
            # 使用 npm 升级
            upgrade_cmd = "npm update -g @github/copilot"
            returncode, stdout, stderr = self.run_command(
                upgrade_cmd,
                shell=True,
                timeout=300,
                max_retries=3
            )
            
            if returncode != 0:
                return InstallReport(
                    tool_name="copilot-cli",
                    result=InstallResult.FAILED,
                    message="通过 npm 升级 GitHub Copilot CLI 失败",
                    error=stderr or "升级命令返回非零退出码"
                )
            
            # 验证升级
            if not self.verify():
                return InstallReport(
                    tool_name="copilot-cli",
                    result=InstallResult.FAILED,
                    message="GitHub Copilot CLI 升级验证失败",
                    error="升级命令执行成功，但无法验证 Copilot CLI 是否正确安装"
                )
            
            # 获取升级后的版本
            new_version = self._get_installed_version()
            
            return InstallReport(
                tool_name="copilot-cli",
                result=InstallResult.SUCCESS,
                message=f"GitHub Copilot CLI 升级成功 ({old_version} -> {new_version})",
                version=new_version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="copilot-cli",
                result=InstallResult.FAILED,
                message="GitHub Copilot CLI 升级过程中发生异常",
                error=str(e)
            )
