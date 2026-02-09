"""NVM 安装器模块

该模块实现 NVM (Node Version Manager) 的安装、升级和验证逻辑。
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import PlatformInfo, Shell


class NVMInstaller(ToolInstaller):
    """NVM 安装器
    
    负责安装、升级和验证 NVM (Node Version Manager)。
    NVM 通过下载并执行官方安装脚本进行安装，并将环境变量写入 Shell 配置文件。
    
    Attributes:
        platform_info: 平台信息
        config: 工具配置
        nvm_version: NVM 版本（默认 v0.40.4）
        install_script_url: 安装脚本 URL
    """
    
    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化 NVM 安装器
        
        Args:
            platform_info: 平台信息
            config: 工具配置
        """
        super().__init__(platform_info, config)
        
        # 从配置中获取版本，如果未指定则使用默认版本
        self.nvm_version = config.version or "v0.40.4"
        
        # 构建安装脚本 URL
        self.install_script_url = (
            f"https://raw.githubusercontent.com/nvm-sh/nvm/{self.nvm_version}/install.sh"
        )
    
    def verify(self) -> bool:
        """验证 NVM 是否已正确安装
        
        检查 ~/.nvm/nvm.sh 文件是否存在，并尝试执行 nvm --version 命令。
        
        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        nvm_dir = Path.home() / ".nvm"
        nvm_sh = nvm_dir / "nvm.sh"
        
        # 检查 nvm.sh 文件是否存在
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
    
    def _get_installed_version(self) -> Optional[str]:
        """获取已安装的 NVM 版本
        
        Returns:
            Optional[str]: 版本号，如果无法获取则返回 None
        """
        nvm_sh = Path.home() / ".nvm" / "nvm.sh"
        
        if not nvm_sh.exists():
            return None
        
        returncode, stdout, stderr = self.run_command(
            f"bash -c 'source {nvm_sh} && nvm --version'",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        if returncode == 0:
            return stdout.strip()
        
        return None
    
    def _write_env_to_shell_config(self) -> bool:
        """将 NVM 环境变量写入 Shell 配置文件
        
        根据当前 Shell 类型，将 NVM 的环境变量配置写入相应的配置文件。
        如果配置已存在，则不重复写入。
        
        Returns:
            bool: 如果写入成功返回 True，否则返回 False
        """
        shell_config_file = Path(self.platform_info.shell_config_file)
        
        # NVM 环境变量配置
        nvm_config_lines = [
            '# NVM configuration',
            'export NVM_DIR="$HOME/.nvm"',
            '[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"  # This loads nvm',
            '[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion',
        ]
        
        try:
            # 读取现有配置文件内容
            if shell_config_file.exists():
                with open(shell_config_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            else:
                existing_content = ""
            
            # 检查是否已经包含 NVM 配置
            if 'NVM_DIR' in existing_content and 'nvm.sh' in existing_content:
                # 配置已存在，无需重复写入
                return True
            
            # 追加 NVM 配置到文件末尾
            with open(shell_config_file, 'a', encoding='utf-8') as f:
                # 确保文件末尾有换行符
                if existing_content and not existing_content.endswith('\n'):
                    f.write('\n')
                
                # 写入配置
                f.write('\n')
                for line in nvm_config_lines:
                    f.write(line + '\n')
            
            return True
            
        except (OSError, IOError) as e:
            # 文件操作失败
            return False
    
    def install(self) -> InstallReport:
        """安装 NVM
        
        执行以下步骤：
        1. 检查 NVM 是否已安装
        2. 下载 NVM 安装脚本
        3. 执行安装脚本
        4. 将环境变量写入 Shell 配置文件
        5. 验证安装
        
        Returns:
            InstallReport: 安装报告
        """
        # 检查是否已安装
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="nvm",
                result=InstallResult.SKIPPED,
                message="NVM 已安装，跳过安装",
                version=version
            )
        
        try:
            # 下载安装脚本到临时文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                delete=False
            ) as temp_file:
                temp_script_path = temp_file.name
            
            # 下载安装脚本
            download_success = self.download_file(
                self.install_script_url,
                temp_script_path,
                max_retries=3,
                timeout=60
            )
            
            if not download_success:
                return InstallReport(
                    tool_name="nvm",
                    result=InstallResult.FAILED,
                    message="下载 NVM 安装脚本失败",
                    error="无法从 GitHub 下载安装脚本"
                )
            
            # 执行安装脚本
            returncode, stdout, stderr = self.run_command(
                f"bash {temp_script_path}",
                shell=True,
                timeout=300,
                max_retries=1
            )
            
            # 清理临时文件
            try:
                Path(temp_script_path).unlink()
            except OSError:
                pass
            
            if returncode != 0:
                return InstallReport(
                    tool_name="nvm",
                    result=InstallResult.FAILED,
                    message="执行 NVM 安装脚本失败",
                    error=stderr or "安装脚本返回非零退出码"
                )
            
            # 将环境变量写入 Shell 配置文件
            env_write_success = self._write_env_to_shell_config()
            
            if not env_write_success:
                return InstallReport(
                    tool_name="nvm",
                    result=InstallResult.FAILED,
                    message="写入 Shell 配置文件失败",
                    error="无法将 NVM 环境变量写入 Shell 配置文件"
                )
            
            # 验证安装
            if not self.verify():
                return InstallReport(
                    tool_name="nvm",
                    result=InstallResult.FAILED,
                    message="NVM 安装验证失败",
                    error="安装脚本执行成功，但无法验证 NVM 是否正确安装"
                )
            
            # 获取安装的版本
            version = self._get_installed_version()
            
            return InstallReport(
                tool_name="nvm",
                result=InstallResult.SUCCESS,
                message="NVM 安装成功",
                version=version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="nvm",
                result=InstallResult.FAILED,
                message="NVM 安装过程中发生异常",
                error=str(e)
            )
    
    def upgrade(self) -> InstallReport:
        """升级 NVM
        
        NVM 的升级通过重新执行安装脚本实现。
        安装脚本会自动检测已有安装并进行升级。
        
        Returns:
            InstallReport: 升级报告
        """
        # 检查是否已安装
        if not self.verify():
            return InstallReport(
                tool_name="nvm",
                result=InstallResult.FAILED,
                message="NVM 未安装，无法升级",
                error="请先安装 NVM"
            )
        
        try:
            # 记录升级前的版本
            old_version = self._get_installed_version()
            
            # 下载安装脚本到临时文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                delete=False
            ) as temp_file:
                temp_script_path = temp_file.name
            
            # 下载安装脚本
            download_success = self.download_file(
                self.install_script_url,
                temp_script_path,
                max_retries=3,
                timeout=60
            )
            
            if not download_success:
                return InstallReport(
                    tool_name="nvm",
                    result=InstallResult.FAILED,
                    message="下载 NVM 安装脚本失败",
                    error="无法从 GitHub 下载安装脚本"
                )
            
            # 执行安装脚本（会自动升级）
            returncode, stdout, stderr = self.run_command(
                f"bash {temp_script_path}",
                shell=True,
                timeout=300,
                max_retries=1
            )
            
            # 清理临时文件
            try:
                Path(temp_script_path).unlink()
            except OSError:
                pass
            
            if returncode != 0:
                return InstallReport(
                    tool_name="nvm",
                    result=InstallResult.FAILED,
                    message="执行 NVM 升级脚本失败",
                    error=stderr or "升级脚本返回非零退出码"
                )
            
            # 验证升级
            if not self.verify():
                return InstallReport(
                    tool_name="nvm",
                    result=InstallResult.FAILED,
                    message="NVM 升级验证失败",
                    error="升级脚本执行成功，但无法验证 NVM 是否正确安装"
                )
            
            # 获取升级后的版本
            new_version = self._get_installed_version()
            
            return InstallReport(
                tool_name="nvm",
                result=InstallResult.SUCCESS,
                message=f"NVM 升级成功 ({old_version} -> {new_version})",
                version=new_version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="nvm",
                result=InstallResult.FAILED,
                message="NVM 升级过程中发生异常",
                error=str(e)
            )
