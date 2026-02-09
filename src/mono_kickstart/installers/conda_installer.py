"""Conda 安装器模块

该模块实现 Conda (Miniconda) 的安装、升级和验证逻辑。
"""

import tempfile
from pathlib import Path
from typing import Optional

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import PlatformInfo, OS, Arch


class CondaInstaller(ToolInstaller):
    """Conda 安装器
    
    负责安装、升级和验证 Conda (Miniconda)。
    Conda 通过下载并执行平台特定的 Miniconda 安装脚本进行安装。
    
    Attributes:
        platform_info: 平台信息
        config: 工具配置
        install_dir: Conda 安装目录（默认 ~/miniconda3）
    """
    
    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化 Conda 安装器
        
        Args:
            platform_info: 平台信息
            config: 工具配置
        """
        super().__init__(platform_info, config)
        
        # Conda 安装目录
        self.install_dir = Path.home() / "miniconda3"
    
    def get_install_url(self) -> str:
        """根据平台选择正确的 Miniconda 安装包 URL
        
        根据操作系统和架构选择对应的安装包：
        - Linux x86_64: Miniconda3-latest-Linux-x86_64.sh
        - macOS ARM64: Miniconda3-latest-MacOSX-arm64.sh
        - macOS x86_64: Miniconda3-latest-MacOSX-x86_64.sh
        
        Returns:
            str: 安装包 URL
            
        Raises:
            ValueError: 如果平台不支持
        """
        base_url = "https://mirrors.sustech.edu.cn/anaconda/miniconda"
        
        # 根据平台选择安装包
        if self.platform_info.os == OS.LINUX and self.platform_info.arch == Arch.X86_64:
            installer_name = "Miniconda3-latest-Linux-x86_64.sh"
        elif self.platform_info.os == OS.MACOS and self.platform_info.arch == Arch.ARM64:
            installer_name = "Miniconda3-latest-MacOSX-arm64.sh"
        elif self.platform_info.os == OS.MACOS and self.platform_info.arch == Arch.X86_64:
            installer_name = "Miniconda3-latest-MacOSX-x86_64.sh"
        else:
            raise ValueError(
                f"不支持的平台: {self.platform_info.os.value} {self.platform_info.arch.value}"
            )
        
        return f"{base_url}/{installer_name}"
    
    def verify(self) -> bool:
        """验证 Conda 是否已正确安装
        
        检查 conda 命令是否可用，并尝试执行 conda --version 命令。
        
        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        # 检查安装目录是否存在
        if not self.install_dir.exists():
            return False
        
        # 检查 conda 可执行文件是否存在
        conda_bin = self.install_dir / "bin" / "conda"
        if not conda_bin.exists():
            return False
        
        # 尝试执行 conda --version 命令
        returncode, stdout, stderr = self.run_command(
            f"{conda_bin} --version",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        return returncode == 0
    
    def _get_installed_version(self) -> Optional[str]:
        """获取已安装的 Conda 版本
        
        Returns:
            Optional[str]: 版本号，如果无法获取则返回 None
        """
        conda_bin = self.install_dir / "bin" / "conda"
        
        if not conda_bin.exists():
            return None
        
        returncode, stdout, stderr = self.run_command(
            f"{conda_bin} --version",
            shell=True,
            timeout=10,
            max_retries=1
        )
        
        if returncode == 0:
            # conda --version 输出格式: "conda 23.1.0"
            # 提取版本号
            parts = stdout.strip().split()
            if len(parts) >= 2:
                return parts[1]
        
        return None
    
    def _download_installer(self, url: str, dest: str) -> bool:
        """使用 curl 下载安装脚本

        使用外部 curl 进程下载，避免 Python urllib 在 conda 环境下
        因 SSL 库冲突导致 segfault。

        Args:
            url: 下载 URL
            dest: 目标文件路径

        Returns:
            bool: 下载成功返回 True，否则返回 False
        """
        returncode, stdout, stderr = self.run_command(
            f"curl -fsSL -o {dest} {url}",
            shell=True,
            timeout=300,
            max_retries=3
        )
        return returncode == 0 and Path(dest).exists() and Path(dest).stat().st_size > 0

    def install(self) -> InstallReport:
        """安装 Conda
        
        执行以下步骤：
        1. 检查 Conda 是否已安装
        2. 根据平台选择正确的安装包 URL
        3. 下载 Miniconda 安装脚本
        4. 执行安装脚本（批量模式，不修改 shell 配置）
        5. 验证安装
        
        Returns:
            InstallReport: 安装报告
        """
        # 检查是否已安装
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="conda",
                result=InstallResult.SKIPPED,
                message="Conda 已安装，跳过安装",
                version=version
            )
        
        try:
            # 获取安装包 URL
            try:
                install_url = self.get_install_url()
            except ValueError as e:
                return InstallReport(
                    tool_name="conda",
                    result=InstallResult.FAILED,
                    message="不支持的平台",
                    error=str(e)
                )
            
            # 下载安装脚本到临时文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                delete=False
            ) as temp_file:
                temp_script_path = temp_file.name
            
            # 下载安装脚本（使用 curl 避免 Python SSL 库冲突）
            download_success = self._download_installer(install_url, temp_script_path)

            if not download_success:
                return InstallReport(
                    tool_name="conda",
                    result=InstallResult.FAILED,
                    message="下载 Miniconda 安装脚本失败",
                    error="无法从 Anaconda 仓库下载安装脚本"
                )
            
            # 执行安装脚本
            # -b: 批量模式（不需要用户交互）
            # -f: 强制安装（即使目录已存在也不报错）
            install_cmd = f"bash {temp_script_path} -b -f"
            returncode, stdout, stderr = self.run_command(
                install_cmd,
                shell=True,
                timeout=600,  # 安装可能需要较长时间
                max_retries=1
            )
            
            # 清理临时文件
            try:
                Path(temp_script_path).unlink()
            except OSError:
                pass
            
            if returncode != 0:
                return InstallReport(
                    tool_name="conda",
                    result=InstallResult.FAILED,
                    message="执行 Conda 安装脚本失败",
                    error=stderr or "安装脚本返回非零退出码"
                )
            
            # 验证安装
            if not self.verify():
                return InstallReport(
                    tool_name="conda",
                    result=InstallResult.FAILED,
                    message="Conda 安装验证失败",
                    error="安装脚本执行成功，但无法验证 Conda 是否正确安装"
                )
            
            # 获取安装的版本
            version = self._get_installed_version()
            
            return InstallReport(
                tool_name="conda",
                result=InstallResult.SUCCESS,
                message="Conda 安装成功",
                version=version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="conda",
                result=InstallResult.FAILED,
                message="Conda 安装过程中发生异常",
                error=str(e)
            )
    
    def upgrade(self) -> InstallReport:
        """升级 Conda
        
        Conda 的升级通过重新下载最新安装包并使用覆盖安装模式实现。
        使用 -b（批量模式）、-u（更新模式）、-p（指定路径）参数。
        
        Returns:
            InstallReport: 升级报告
        """
        # 检查是否已安装
        if not self.verify():
            return InstallReport(
                tool_name="conda",
                result=InstallResult.FAILED,
                message="Conda 未安装，无法升级",
                error="请先安装 Conda"
            )
        
        try:
            # 记录升级前的版本
            old_version = self._get_installed_version()
            
            # 获取安装包 URL
            try:
                install_url = self.get_install_url()
            except ValueError as e:
                return InstallReport(
                    tool_name="conda",
                    result=InstallResult.FAILED,
                    message="不支持的平台",
                    error=str(e)
                )
            
            # 下载安装脚本到临时文件
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                delete=False
            ) as temp_file:
                temp_script_path = temp_file.name
            
            # 下载安装脚本（使用 curl 避免 Python SSL 库冲突）
            download_success = self._download_installer(install_url, temp_script_path)

            if not download_success:
                return InstallReport(
                    tool_name="conda",
                    result=InstallResult.FAILED,
                    message="下载 Miniconda 安装脚本失败",
                    error="无法从 Anaconda 仓库下载安装脚本"
                )
            
            # 执行升级（覆盖安装）
            # -b: 批量模式（不需要用户交互）
            # -f: 强制安装（覆盖已有安装）
            upgrade_cmd = f"bash {temp_script_path} -b -f"
            returncode, stdout, stderr = self.run_command(
                upgrade_cmd,
                shell=True,
                timeout=600,
                max_retries=1
            )
            
            # 清理临时文件
            try:
                Path(temp_script_path).unlink()
            except OSError:
                pass
            
            if returncode != 0:
                return InstallReport(
                    tool_name="conda",
                    result=InstallResult.FAILED,
                    message="执行 Conda 升级脚本失败",
                    error=stderr or "升级脚本返回非零退出码"
                )
            
            # 验证升级
            if not self.verify():
                return InstallReport(
                    tool_name="conda",
                    result=InstallResult.FAILED,
                    message="Conda 升级验证失败",
                    error="升级脚本执行成功，但无法验证 Conda 是否正确安装"
                )
            
            # 获取升级后的版本
            new_version = self._get_installed_version()
            
            return InstallReport(
                tool_name="conda",
                result=InstallResult.SUCCESS,
                message=f"Conda 升级成功 ({old_version} -> {new_version})",
                version=new_version
            )
            
        except Exception as e:
            return InstallReport(
                tool_name="conda",
                result=InstallResult.FAILED,
                message="Conda 升级过程中发生异常",
                error=str(e)
            )
