"""UIPro CLI 安装器模块

该模块实现 UIPro CLI 的安装、升级和验证逻辑。
"""

import shutil
from typing import Literal

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import PlatformInfo


class UiproInstaller(ToolInstaller):
    """UIPro CLI 安装器

    负责安装、升级和验证 UIPro CLI。
    UIPro CLI 优先使用 Bun 安装（如果 Bun 已安装），否则使用 npm 安装。
    升级通过 uipro update 自更新命令实现。

    Attributes:
        platform_info: 平台信息
        config: 工具配置
        install_method: 安装方式（'bun' 或 'npm'）
    """

    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化 UIPro CLI 安装器

        Args:
            platform_info: 平台信息
            config: 工具配置
        """
        super().__init__(platform_info, config)

        # 确定安装方式
        self.install_method = self._determine_install_method()

    def _determine_install_method(self) -> Literal['bun', 'npm']:
        """确定安装方式

        如果配置中指定了 install_via，则使用指定的方式。
        否则，如果 Bun 已安装则使用 Bun，否则使用 npm。

        Returns:
            Literal['bun', 'npm']: 安装方式
        """
        # 如果配置中指定了安装方式，则使用指定的方式
        if self.config.install_via:
            return self.config.install_via.lower()

        # 检查 Bun 是否已安装
        if shutil.which("bun"):
            return 'bun'

        # 默认使用 npm
        return 'npm'

    def verify(self) -> bool:
        """验证 UIPro CLI 是否已正确安装

        检查 uipro 命令是否可用，并尝试执行 uipro versions 命令。

        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        # 检查 uipro 命令是否在 PATH 中
        if not shutil.which("uipro"):
            return False

        # 尝试执行 uipro versions 命令
        returncode, stdout, stderr = self.run_command(
            "uipro versions",
            shell=True,
            timeout=10,
            max_retries=1
        )

        return returncode == 0

    def _get_installed_version(self) -> str | None:
        """获取已安装的 UIPro CLI 版本

        从 uipro versions 输出中提取当前版本。

        Returns:
            Optional[str]: 版本号，如果无法获取则返回 None
        """
        if not shutil.which("uipro"):
            return None

        returncode, stdout, stderr = self.run_command(
            "uipro versions",
            shell=True,
            timeout=10,
            max_retries=1
        )

        if returncode == 0 and stdout.strip():
            # 返回输出的第一行作为版本信息
            return stdout.strip().splitlines()[0].strip()

        return None

    def install(self) -> InstallReport:
        """安装 UIPro CLI

        执行以下步骤：
        1. 检查 UIPro CLI 是否已安装
        2. 确定安装方式（Bun 优先，否则 npm）
        3. 执行相应的安装命令
        4. 验证安装

        Returns:
            InstallReport: 安装报告
        """
        # 检查是否已安装
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="uipro",
                result=InstallResult.SKIPPED,
                message="UIPro CLI 已安装，跳过安装",
                version=version
            )

        try:
            # 根据安装方式执行相应的安装命令
            if self.install_method == 'bun':
                # 检查 Bun 是否可用
                if not shutil.which("bun"):
                    return InstallReport(
                        tool_name="uipro",
                        result=InstallResult.FAILED,
                        message="Bun 未安装，无法使用 Bun 安装 UIPro CLI",
                        error="请先安装 Bun 或使用 npm 安装"
                    )

                install_cmd = "bun install -g uipro-cli"
            else:  # npm
                # 检查 npm 是否可用
                if not shutil.which("npm"):
                    return InstallReport(
                        tool_name="uipro",
                        result=InstallResult.FAILED,
                        message="npm 未安装，无法安装 UIPro CLI",
                        error="请先安装 Node.js 和 npm"
                    )

                install_cmd = "npm install -g uipro-cli"

            # 执行安装命令
            returncode, stdout, stderr = self.run_command(
                install_cmd,
                shell=True,
                timeout=300,
                max_retries=2
            )

            if returncode != 0:
                return InstallReport(
                    tool_name="uipro",
                    result=InstallResult.FAILED,
                    message=f"使用 {self.install_method} 安装 UIPro CLI 失败",
                    error=stderr or "安装命令返回非零退出码"
                )

            # 验证安装
            if not self.verify():
                return InstallReport(
                    tool_name="uipro",
                    result=InstallResult.FAILED,
                    message="UIPro CLI 安装验证失败",
                    error="安装命令执行成功，但无法验证 UIPro CLI 是否正确安装"
                )

            # 获取安装的版本
            version = self._get_installed_version()

            return InstallReport(
                tool_name="uipro",
                result=InstallResult.SUCCESS,
                message=f"UIPro CLI 安装成功（使用 {self.install_method}）",
                version=version
            )

        except Exception as e:
            return InstallReport(
                tool_name="uipro",
                result=InstallResult.FAILED,
                message="UIPro CLI 安装过程中发生异常",
                error=str(e)
            )

    def upgrade(self) -> InstallReport:
        """升级 UIPro CLI

        UIPro CLI 的升级通过执行 `uipro update` 自更新命令实现。

        Returns:
            InstallReport: 升级报告
        """
        # 检查是否已安装
        if not self.verify():
            return InstallReport(
                tool_name="uipro",
                result=InstallResult.FAILED,
                message="UIPro CLI 未安装，无法升级",
                error="请先安装 UIPro CLI"
            )

        try:
            # 记录升级前的版本
            old_version = self._get_installed_version()

            # 执行自更新命令
            upgrade_cmd = "uipro update"
            returncode, stdout, stderr = self.run_command(
                upgrade_cmd,
                shell=True,
                timeout=300,
                max_retries=2
            )

            if returncode != 0:
                return InstallReport(
                    tool_name="uipro",
                    result=InstallResult.FAILED,
                    message="执行 UIPro CLI 升级命令失败",
                    error=stderr or "升级命令返回非零退出码"
                )

            # 验证升级
            if not self.verify():
                return InstallReport(
                    tool_name="uipro",
                    result=InstallResult.FAILED,
                    message="UIPro CLI 升级验证失败",
                    error="升级命令执行成功，但无法验证 UIPro CLI 是否正确安装"
                )

            # 获取升级后的版本
            new_version = self._get_installed_version()

            return InstallReport(
                tool_name="uipro",
                result=InstallResult.SUCCESS,
                message=f"UIPro CLI 升级成功 ({old_version} -> {new_version})",
                version=new_version
            )

        except Exception as e:
            return InstallReport(
                tool_name="uipro",
                result=InstallResult.FAILED,
                message="UIPro CLI 升级过程中发生异常",
                error=str(e)
            )
