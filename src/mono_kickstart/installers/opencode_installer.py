import shutil
from typing import Literal, Optional

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import PlatformInfo


class OpenCodeInstaller(ToolInstaller):
    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        super().__init__(platform_info, config)
        self.install_method = self._determine_install_method()

    def _determine_install_method(self) -> Literal["bun", "npm"]:
        if self.config.install_via:
            method = self.config.install_via.lower()
            if method == "bun":
                return "bun"
            if method == "npm":
                return "npm"

        if shutil.which("bun"):
            return "bun"

        return "npm"

    def verify(self) -> bool:
        if not shutil.which("opencode"):
            return False

        returncode, _, _ = self.run_command(
            "opencode --version",
            shell=True,
            timeout=10,
            max_retries=1,
        )
        return returncode == 0

    def _get_installed_version(self) -> Optional[str]:
        if not shutil.which("opencode"):
            return None

        returncode, stdout, _ = self.run_command(
            "opencode --version",
            shell=True,
            timeout=10,
            max_retries=1,
        )
        if returncode == 0:
            return stdout.strip()
        return None

    def install(self) -> InstallReport:
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="opencode",
                result=InstallResult.SKIPPED,
                message="OpenCode CLI 已安装，跳过安装",
                version=version,
            )

        try:
            if self.install_method == "bun":
                if not shutil.which("bun"):
                    return InstallReport(
                        tool_name="opencode",
                        result=InstallResult.FAILED,
                        message="Bun 未安装，无法使用 Bun 安装 OpenCode CLI",
                        error="请先安装 Bun 或使用 npm 安装",
                    )
                install_cmd = "bun add -g opencode-ai"
            else:
                if not shutil.which("npm"):
                    return InstallReport(
                        tool_name="opencode",
                        result=InstallResult.FAILED,
                        message="npm 未安装，无法安装 OpenCode CLI",
                        error="请先安装 Node.js 和 npm",
                    )
                install_cmd = "npm i -g opencode-ai"

            returncode, _, stderr = self.run_command(
                install_cmd,
                shell=True,
                timeout=300,
                max_retries=2,
            )
            if returncode != 0:
                return InstallReport(
                    tool_name="opencode",
                    result=InstallResult.FAILED,
                    message=f"使用 {self.install_method} 安装 OpenCode CLI 失败",
                    error=stderr or "安装命令返回非零退出码",
                )

            if not self.verify():
                return InstallReport(
                    tool_name="opencode",
                    result=InstallResult.FAILED,
                    message="OpenCode CLI 安装验证失败",
                    error="安装命令执行成功，但无法验证 OpenCode CLI 是否正确安装",
                )

            version = self._get_installed_version()
            return InstallReport(
                tool_name="opencode",
                result=InstallResult.SUCCESS,
                message=f"OpenCode CLI 安装成功（使用 {self.install_method}）",
                version=version,
            )
        except Exception as e:
            return InstallReport(
                tool_name="opencode",
                result=InstallResult.FAILED,
                message="OpenCode CLI 安装过程中发生异常",
                error=str(e),
            )

    def upgrade(self) -> InstallReport:
        if not self.verify():
            return InstallReport(
                tool_name="opencode",
                result=InstallResult.FAILED,
                message="OpenCode CLI 未安装，无法升级",
                error="请先安装 OpenCode CLI",
            )

        try:
            old_version = self._get_installed_version()

            if self.install_method == "bun":
                if not shutil.which("bun"):
                    return InstallReport(
                        tool_name="opencode",
                        result=InstallResult.FAILED,
                        message="Bun 未安装，无法使用 Bun 升级 OpenCode CLI",
                        error="请先安装 Bun 或使用 npm 升级",
                    )
                upgrade_cmd = "bun add -g opencode-ai@latest"
            else:
                if not shutil.which("npm"):
                    return InstallReport(
                        tool_name="opencode",
                        result=InstallResult.FAILED,
                        message="npm 未安装，无法升级 OpenCode CLI",
                        error="请先安装 Node.js 和 npm",
                    )
                upgrade_cmd = "npm update -g opencode-ai"

            returncode, _, stderr = self.run_command(
                upgrade_cmd,
                shell=True,
                timeout=300,
                max_retries=2,
            )
            if returncode != 0:
                return InstallReport(
                    tool_name="opencode",
                    result=InstallResult.FAILED,
                    message=f"使用 {self.install_method} 升级 OpenCode CLI 失败",
                    error=stderr or "升级命令返回非零退出码",
                )

            if not self.verify():
                return InstallReport(
                    tool_name="opencode",
                    result=InstallResult.FAILED,
                    message="OpenCode CLI 升级验证失败",
                    error="升级命令执行成功，但无法验证 OpenCode CLI 是否正确安装",
                )

            new_version = self._get_installed_version()
            return InstallReport(
                tool_name="opencode",
                result=InstallResult.SUCCESS,
                message=f"OpenCode CLI 升级成功 ({old_version} -> {new_version})",
                version=new_version,
            )
        except Exception as e:
            return InstallReport(
                tool_name="opencode",
                result=InstallResult.FAILED,
                message="OpenCode CLI 升级过程中发生异常",
                error=str(e),
            )
