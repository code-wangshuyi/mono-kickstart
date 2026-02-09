"""Node.js 安装器模块

该模块实现 Node.js 的安装、升级和验证逻辑。
Node.js 通过 NVM 进行安装和管理。
"""

from pathlib import Path
from typing import Optional

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import PlatformInfo


class NodeInstaller(ToolInstaller):
    """Node.js 安装器
    
    负责安装、升级和验证 Node.js。
    Node.js 通过 NVM 安装 LTS 版本，并设置为默认版本。
    
    Attributes:
        platform_info: 平台信息
        config: 工具配置
        node_version: Node.js 版本（默认 'lts/*' 表示最新 LTS 版本）
    """
    
    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化 Node.js 安装器
        
        Args:
            platform_info: 平台信息
            config: 工具配置
        """
        super().__init__(platform_info, config)
        
        # 从配置中获取版本，如果未指定则使用 LTS
        self.node_version = config.version or "lts/*"
    
    def _check_nvm_installed(self) -> bool:
        """检查 NVM 是否已安装
        
        Returns:
            bool: 如果 NVM 已安装返回 True，否则返回 False
        """
        nvm_dir = Path.home() / ".nvm"
        nvm_sh = nvm_dir / "nvm.sh"
        
        if not nvm_sh.exists():
            return False
        
        # 尝试执行 nvm --version 命令
        returncode, stdout, stderr = self.run_command(
            f"bash -c 'source {nvm_sh} && nvm --version'",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        return returncode == 0
    
    def verify(self) -> bool:
        """验证 Node.js 是否已正确安装
        
        检查 node 命令是否可用，并尝试执行 node --version 命令。
        
        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        nvm_sh = Path.home() / ".nvm" / "nvm.sh"
        
        if not nvm_sh.exists():
            return False
        
        # 尝试执行 node --version 命令
        returncode, stdout, stderr = self.run_command(
            f"bash -c 'source {nvm_sh} && node --version'",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        return returncode == 0
    
    def _get_installed_version(self) -> Optional[str]:
        """获取已安装的 Node.js 版本
        
        Returns:
            Optional[str]: 版本号，如果无法获取则返回 None
        """
        nvm_sh = Path.home() / ".nvm" / "nvm.sh"
        
        if not nvm_sh.exists():
            return None
        
        returncode, stdout, stderr = self.run_command(
            f"bash -c 'source {nvm_sh} && node --version'",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        if returncode == 0:
            return stdout.strip()
        
        return None
    
    def _install_node_via_nvm(self) -> tuple[bool, str]:
        """通过 NVM 安装 Node.js
        
        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        nvm_sh = Path.home() / ".nvm" / "nvm.sh"
        
        # 安装 Node.js
        install_cmd = f"bash -c 'source {nvm_sh} && nvm install {self.node_version}'"
        returncode, stdout, stderr = self.run_command(
            install_cmd,
            shell=True,
            timeout=600,  # Node.js 安装可能需要较长时间
            max_retries=2
        )
        
        if returncode != 0:
            return False, stderr or "安装命令返回非零退出码"
        
        return True, ""
    
    def _set_default_version(self) -> tuple[bool, str]:
        """设置 Node.js 默认版本
        
        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        nvm_sh = Path.home() / ".nvm" / "nvm.sh"
        
        # 设置默认版本
        # 如果安装的是 lts/*，则将默认版本设置为 lts/*
        # 否则设置为指定的版本
        if self.node_version == "lts/*":
            default_version = "lts/*"
        else:
            default_version = self.node_version
        
        alias_cmd = f"bash -c 'source {nvm_sh} && nvm alias default {default_version}'"
        returncode, stdout, stderr = self.run_command(
            alias_cmd,
            shell=True,
            timeout=30,
            max_retries=1
        )
        
        if returncode != 0:
            return False, stderr or "设置默认版本命令返回非零退出码"
        
        return True, ""
    
    def install(self) -> InstallReport:
        """安装 Node.js
        
        执行以下步骤：
        1. 检查 NVM 是否已安装（Node.js 依赖 NVM）
        2. 检查 Node.js 是否已安装
        3. 通过 NVM 安装 Node.js LTS 版本
        4. 设置为默认版本
        5. 验证安装
        
        Returns:
            InstallReport: 安装报告
        """
        # 检查 NVM 是否已安装
        if not self._check_nvm_installed():
            return InstallReport(
                tool_name="node",
                result=InstallResult.FAILED,
                message="NVM 未安装，无法安装 Node.js",
                error="请先安装 NVM"
            )
        
        # 检查是否已安装
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="node",
                result=InstallResult.SKIPPED,
                message="Node.js 已安装，跳过安装",
                version=version
            )
        
        try:
            # 通过 NVM 安装 Node.js
            install_success, install_error = self._install_node_via_nvm()
            
            if not install_success:
                return InstallReport(
                    tool_name="node",
                    result=InstallResult.FAILED,
                    message="通过 NVM 安装 Node.js 失败",
                    error=install_error
                )
            
            # 设置默认版本
            default_success, default_error = self._set_default_version()
            
            if not default_success:
                return InstallReport(
                    tool_name="node",
                    result=InstallResult.FAILED,
                    message="设置 Node.js 默认版本失败",
                    error=default_error
                )
            
            # 验证安装
            if not self.verify():
                return InstallReport(
                    tool_name="node",
                    result=InstallResult.FAILED,
                    message="Node.js 安装验证失败",
                    error="安装命令执行成功，但无法验证 Node.js 是否正确安装"
                )
            
            # 获取安装的版本
            version = self._get_installed_version()
            
            return InstallReport(
                tool_name="node",
                result=InstallResult.SUCCESS,
                message="Node.js 安装成功",
                version=version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="node",
                result=InstallResult.FAILED,
                message="Node.js 安装过程中发生异常",
                error=str(e)
            )
    
    def upgrade(self) -> InstallReport:
        """升级 Node.js
        
        执行以下步骤：
        1. 检查 NVM 是否已安装
        2. 检查 Node.js 是否已安装
        3. 通过 NVM 安装最新的 LTS 版本
        4. 设置为默认版本
        5. 验证升级
        
        Returns:
            InstallReport: 升级报告
        """
        # 检查 NVM 是否已安装
        if not self._check_nvm_installed():
            return InstallReport(
                tool_name="node",
                result=InstallResult.FAILED,
                message="NVM 未安装，无法升级 Node.js",
                error="请先安装 NVM"
            )
        
        # 检查是否已安装
        if not self.verify():
            return InstallReport(
                tool_name="node",
                result=InstallResult.FAILED,
                message="Node.js 未安装，无法升级",
                error="请先安装 Node.js"
            )
        
        try:
            # 记录升级前的版本
            old_version = self._get_installed_version()
            
            # 通过 NVM 安装最新的 LTS 版本（会自动下载新版本）
            install_success, install_error = self._install_node_via_nvm()
            
            if not install_success:
                return InstallReport(
                    tool_name="node",
                    result=InstallResult.FAILED,
                    message="通过 NVM 升级 Node.js 失败",
                    error=install_error
                )
            
            # 设置默认版本
            default_success, default_error = self._set_default_version()
            
            if not default_success:
                return InstallReport(
                    tool_name="node",
                    result=InstallResult.FAILED,
                    message="设置 Node.js 默认版本失败",
                    error=default_error
                )
            
            # 验证升级
            if not self.verify():
                return InstallReport(
                    tool_name="node",
                    result=InstallResult.FAILED,
                    message="Node.js 升级验证失败",
                    error="升级命令执行成功，但无法验证 Node.js 是否正确安装"
                )
            
            # 获取升级后的版本
            new_version = self._get_installed_version()
            
            return InstallReport(
                tool_name="node",
                result=InstallResult.SUCCESS,
                message=f"Node.js 升级成功 ({old_version} -> {new_version})",
                version=new_version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="node",
                result=InstallResult.FAILED,
                message="Node.js 升级过程中发生异常",
                error=str(e)
            )
