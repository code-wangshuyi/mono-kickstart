"""BMad Method 安装器模块

该模块实现 BMad Method 的安装、升级和验证逻辑。
"""

import shutil
from pathlib import Path
from typing import Optional, Literal

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import PlatformInfo


class BMadInstaller(ToolInstaller):
    """BMad Method 安装器
    
    负责安装、升级和验证 BMad Method。
    BMad Method 通过 npx 或 bunx 交互式安装到项目中。
    
    Attributes:
        platform_info: 平台信息
        config: 工具配置
        install_method: 安装方式（'bunx' 或 'npx'）
    """
    
    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化 BMad Method 安装器
        
        Args:
            platform_info: 平台信息
            config: 工具配置
        """
        super().__init__(platform_info, config)
        
        # 确定安装方式
        self.install_method = self._determine_install_method()
    
    def _determine_install_method(self) -> Literal['bunx', 'npx']:
        """确定安装方式
        
        如果配置中指定了 install_via，则使用指定的方式。
        否则，如果 Bun 已安装则使用 bunx，否则使用 npx。
        
        Returns:
            Literal['bunx', 'npx']: 安装方式
        """
        # 如果配置中指定了安装方式，则使用指定的方式
        if self.config.install_via:
            return self.config.install_via.lower()
        
        # 检查 Bun 是否已安装
        if shutil.which("bun"):
            return 'bunx'
        
        # 默认使用 npx
        return 'npx'
    
    def verify(self) -> bool:
        """验证 BMad Method 是否已正确安装
        
        检查 bmad 命令是否可用，并尝试执行 bmad --version 命令。
        
        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        # 检查 bmad 命令是否在 PATH 中
        if not shutil.which("bmad"):
            return False
        
        # 尝试执行 bmad --version 命令
        returncode, stdout, stderr = self.run_command(
            "bmad --version",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        return returncode == 0
    
    def _get_installed_version(self) -> Optional[str]:
        """获取已安装的 BMad Method 版本
        
        Returns:
            Optional[str]: 版本号，如果无法获取则返回 None
        """
        if not shutil.which("bmad"):
            return None
        
        returncode, stdout, stderr = self.run_command(
            "bmad --version",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        if returncode == 0:
            return stdout.strip()
        
        return None
    
    def install(self) -> InstallReport:
        """安装 BMad Method
        
        执行以下步骤：
        1. 检查 BMad Method 是否已安装
        2. 确定安装方式（bunx 优先，否则 npx）
        3. 使用 npx/bunx 交互式安装
        4. 验证安装
        
        Returns:
            InstallReport: 安装报告
        """
        # 检查是否已安装
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="bmad-method",
                result=InstallResult.SKIPPED,
                message="BMad Method 已安装，跳过安装",
                version=version
            )
        
        try:
            # 根据安装方式执行相应的安装命令
            if self.install_method == 'bunx':
                # 检查 Bun 是否可用
                if not shutil.which("bun"):
                    return InstallReport(
                        tool_name="bmad-method",
                        result=InstallResult.FAILED,
                        message="Bun 未安装，无法使用 bunx 安装 BMad Method",
                        error="请先安装 Bun 或使用 npx 安装"
                    )
                
                install_cmd = "bunx bmad-method init"
            else:  # npx
                # 检查 npx 是否可用
                if not shutil.which("npx"):
                    return InstallReport(
                        tool_name="bmad-method",
                        result=InstallResult.FAILED,
                        message="npx 未安装，无法安装 BMad Method",
                        error="请先安装 Node.js 和 npm"
                    )
                
                install_cmd = "npx bmad-method init"
            
            # 执行交互式安装命令
            # 注意：这是一个交互式命令，需要用户输入
            returncode, stdout, stderr = self.run_command(
                install_cmd,
                shell=True,
                timeout=300,
                max_retries=1  # 交互式命令不重试
            )
            
            if returncode != 0:
                return InstallReport(
                    tool_name="bmad-method",
                    result=InstallResult.FAILED,
                    message=f"使用 {self.install_method} 安装 BMad Method 失败",
                    error=stderr or "安装命令返回非零退出码"
                )
            
            # 验证安装
            if not self.verify():
                return InstallReport(
                    tool_name="bmad-method",
                    result=InstallResult.FAILED,
                    message="BMad Method 安装验证失败",
                    error="安装命令执行成功，但无法验证 BMad Method 是否正确安装"
                )
            
            # 获取安装的版本
            version = self._get_installed_version()
            
            return InstallReport(
                tool_name="bmad-method",
                result=InstallResult.SUCCESS,
                message=f"BMad Method 安装成功（使用 {self.install_method}）",
                version=version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="bmad-method",
                result=InstallResult.FAILED,
                message="BMad Method 安装过程中发生异常",
                error=str(e)
            )
    
    def upgrade(self) -> InstallReport:
        """升级 BMad Method
        
        BMad Method 的升级通过重新运行交互式安装命令实现。
        
        Returns:
            InstallReport: 升级报告
        """
        # 检查是否已安装
        if not self.verify():
            return InstallReport(
                tool_name="bmad-method",
                result=InstallResult.FAILED,
                message="BMad Method 未安装，无法升级",
                error="请先安装 BMad Method"
            )
        
        try:
            # 记录升级前的版本
            old_version = self._get_installed_version()
            
            # 根据安装方式执行相应的升级命令
            if self.install_method == 'bunx':
                # 检查 Bun 是否可用
                if not shutil.which("bun"):
                    return InstallReport(
                        tool_name="bmad-method",
                        result=InstallResult.FAILED,
                        message="Bun 未安装，无法使用 bunx 升级 BMad Method",
                        error="请先安装 Bun 或使用 npx 升级"
                    )
                
                upgrade_cmd = "bunx bmad-method@latest init"
            else:  # npx
                # 检查 npx 是否可用
                if not shutil.which("npx"):
                    return InstallReport(
                        tool_name="bmad-method",
                        result=InstallResult.FAILED,
                        message="npx 未安装，无法升级 BMad Method",
                        error="请先安装 Node.js 和 npm"
                    )
                
                upgrade_cmd = "npx bmad-method@latest init"
            
            # 执行升级命令（交互式）
            returncode, stdout, stderr = self.run_command(
                upgrade_cmd,
                shell=True,
                timeout=300,
                max_retries=1  # 交互式命令不重试
            )
            
            if returncode != 0:
                return InstallReport(
                    tool_name="bmad-method",
                    result=InstallResult.FAILED,
                    message=f"使用 {self.install_method} 升级 BMad Method 失败",
                    error=stderr or "升级命令返回非零退出码"
                )
            
            # 验证升级
            if not self.verify():
                return InstallReport(
                    tool_name="bmad-method",
                    result=InstallResult.FAILED,
                    message="BMad Method 升级验证失败",
                    error="升级命令执行成功，但无法验证 BMad Method 是否正确安装"
                )
            
            # 获取升级后的版本
            new_version = self._get_installed_version()
            
            return InstallReport(
                tool_name="bmad-method",
                result=InstallResult.SUCCESS,
                message=f"BMad Method 升级成功 ({old_version} -> {new_version})",
                version=new_version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="bmad-method",
                result=InstallResult.FAILED,
                message="BMad Method 升级过程中发生异常",
                error=str(e)
            )
