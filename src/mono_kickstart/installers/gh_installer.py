"""GitHub CLI (gh) 安装器模块

该模块实现 GitHub CLI 的安装、升级和验证逻辑。
gh 通过 Homebrew 进行安装（macOS），或通过系统包管理器安装（Linux）。
"""

import shutil

from ..config import ToolConfig
from ..installer_base import InstallReport, InstallResult, ToolInstaller
from ..platform_detector import OS, PlatformInfo


class GHInstaller(ToolInstaller):
    """GitHub CLI 安装器

    负责安装、升级和验证 GitHub CLI (gh)。
    macOS 上通过 Homebrew 安装，Linux 上优先使用 Homebrew，
    否则使用 apt-get 或 dnf 等系统包管理器。

    Attributes:
        platform_info: 平台信息
        config: 工具配置
    """

    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化 GitHub CLI 安装器

        Args:
            platform_info: 平台信息
            config: 工具配置
        """
        super().__init__(platform_info, config)

    def verify(self) -> bool:
        """验证 gh 是否已正确安装

        检查 gh 命令是否可用，并尝试执行 gh --version 命令。

        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        if not shutil.which("gh"):
            return False

        returncode, stdout, stderr = self.run_command(
            "gh --version", shell=True, timeout=10, max_retries=1
        )

        return returncode == 0

    def _get_installed_version(self) -> str | None:
        """获取已安装的 gh 版本

        Returns:
            str | None: 版本号，如果无法获取则返回 None
        """
        if not shutil.which("gh"):
            return None

        returncode, stdout, stderr = self.run_command(
            "gh --version", shell=True, timeout=10, max_retries=1
        )

        if returncode == 0:
            # gh --version 输出格式: "gh version 2.86.0 (2025-01-15)"
            # 提取版本号
            parts = stdout.strip().split()
            if len(parts) >= 3:
                return parts[2]

        return None

    def _check_brew_available(self) -> bool:
        """检查 Homebrew 是否可用

        Returns:
            bool: 如果 Homebrew 可用返回 True，否则返回 False
        """
        return shutil.which("brew") is not None

    def _detect_linux_package_manager(self) -> str | None:
        """检测 Linux 系统包管理器

        Returns:
            str | None: 包管理器名称（apt-get 或 dnf），如果未检测到则返回 None
        """
        if shutil.which("apt-get"):
            return "apt-get"
        elif shutil.which("dnf"):
            return "dnf"
        return None

    def _install_via_brew(self) -> tuple[bool, str]:
        """通过 Homebrew 安装 gh

        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        returncode, stdout, stderr = self.run_command(
            "brew install gh", shell=True, timeout=600, max_retries=2
        )

        if returncode != 0:
            return False, stderr or "brew install gh 返回非零退出码"

        return True, ""

    def _install_via_apt(self) -> tuple[bool, str]:
        """通过 apt 安装 gh（Debian/Ubuntu）

        设置 GitHub CLI 官方 APT 仓库并安装。

        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        # 安装依赖并添加 GitHub CLI 官方 APT 源
        setup_cmd = (
            "(type -p wget >/dev/null || (sudo apt update && sudo apt install wget -y)) "
            "&& sudo mkdir -p -m 755 /etc/apt/keyrings "
            "&& out=$(mktemp) "
            "&& wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg "
            "&& cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null "
            "&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg "
            '&& echo "deb [arch=$(dpkg --print-architecture) '
            "signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] "
            'https://cli.github.com/packages stable main" '
            "| sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null "
            "&& sudo apt update "
            "&& sudo apt install gh -y"
        )

        returncode, stdout, stderr = self.run_command(
            setup_cmd, shell=True, timeout=600, max_retries=2
        )

        if returncode != 0:
            return False, stderr or "通过 apt 安装 gh 失败"

        return True, ""

    def _install_via_dnf(self) -> tuple[bool, str]:
        """通过 dnf 安装 gh（Fedora/RHEL）

        设置 GitHub CLI 官方 RPM 仓库并安装。

        Returns:
            tuple[bool, str]: (是否成功, 错误信息)
        """
        setup_cmd = (
            "sudo dnf install 'dnf-command(config-manager)' -y "
            "&& sudo dnf config-manager --add-repo "
            "https://cli.github.com/packages/rpm/gh-cli.repo "
            "&& sudo dnf install gh --repo gh-cli -y"
        )

        returncode, stdout, stderr = self.run_command(
            setup_cmd, shell=True, timeout=600, max_retries=2
        )

        if returncode != 0:
            return False, stderr or "通过 dnf 安装 gh 失败"

        return True, ""

    def install(self) -> InstallReport:
        """安装 GitHub CLI

        执行以下步骤：
        1. 检查平台是否支持（仅 macOS 和 Linux）
        2. 检查 gh 是否已安装
        3. macOS: 通过 Homebrew 安装
        4. Linux: 优先 Homebrew，否则使用 apt-get 或 dnf
        5. 验证安装

        Returns:
            InstallReport: 安装报告
        """
        # 检查平台
        if self.platform_info.os not in [OS.MACOS, OS.LINUX]:
            return InstallReport(
                tool_name="gh",
                result=InstallResult.FAILED,
                message="不支持的操作系统",
                error="GitHub CLI 安装器仅支持 macOS 和 Linux",
            )

        # 检查是否已安装
        if self.verify():
            version = self._get_installed_version()
            return InstallReport(
                tool_name="gh",
                result=InstallResult.SKIPPED,
                message="GitHub CLI 已安装，跳过安装",
                version=version,
            )

        try:
            if self.platform_info.os == OS.MACOS:
                # macOS: 使用 Homebrew
                if not self._check_brew_available():
                    return InstallReport(
                        tool_name="gh",
                        result=InstallResult.FAILED,
                        message="Homebrew 未安装",
                        error="macOS 上安装 GitHub CLI 需要 Homebrew，请先安装 Homebrew",
                    )
                install_success, install_error = self._install_via_brew()

            else:
                # Linux: 优先 Homebrew，否则使用系统包管理器
                if self._check_brew_available():
                    install_success, install_error = self._install_via_brew()
                else:
                    pkg_manager = self._detect_linux_package_manager()
                    if pkg_manager == "apt-get":
                        install_success, install_error = self._install_via_apt()
                    elif pkg_manager == "dnf":
                        install_success, install_error = self._install_via_dnf()
                    else:
                        return InstallReport(
                            tool_name="gh",
                            result=InstallResult.FAILED,
                            message="未找到支持的包管理器",
                            error="需要 Homebrew、apt-get 或 dnf 来安装 GitHub CLI",
                        )

            if not install_success:
                return InstallReport(
                    tool_name="gh",
                    result=InstallResult.FAILED,
                    message="安装 GitHub CLI 失败",
                    error=install_error,
                )

            # 验证安装
            if not self.verify():
                return InstallReport(
                    tool_name="gh",
                    result=InstallResult.FAILED,
                    message="GitHub CLI 安装验证失败",
                    error="安装命令执行成功，但无法验证 gh 是否正确安装",
                )

            version = self._get_installed_version()

            return InstallReport(
                tool_name="gh",
                result=InstallResult.SUCCESS,
                message="GitHub CLI 安装成功",
                version=version,
            )

        except Exception as e:
            return InstallReport(
                tool_name="gh",
                result=InstallResult.FAILED,
                message="GitHub CLI 安装过程中发生异常",
                error=str(e),
            )

    def upgrade(self) -> InstallReport:
        """升级 GitHub CLI

        执行以下步骤：
        1. 检查平台是否支持
        2. 检查 gh 是否已安装
        3. 记录当前版本
        4. 执行升级命令
        5. 验证升级

        Returns:
            InstallReport: 升级报告
        """
        # 检查平台
        if self.platform_info.os not in [OS.MACOS, OS.LINUX]:
            return InstallReport(
                tool_name="gh",
                result=InstallResult.FAILED,
                message="不支持的操作系统",
                error="GitHub CLI 安装器仅支持 macOS 和 Linux",
            )

        # 检查是否已安装
        if not self.verify():
            return InstallReport(
                tool_name="gh",
                result=InstallResult.FAILED,
                message="GitHub CLI 未安装，无法升级",
                error="请先安装 GitHub CLI",
            )

        try:
            old_version = self._get_installed_version()

            # 确定升级命令
            if self._check_brew_available():
                upgrade_cmd = "brew upgrade gh"
            else:
                pkg_manager = self._detect_linux_package_manager()
                if pkg_manager == "apt-get":
                    upgrade_cmd = "sudo apt update && sudo apt install --only-upgrade gh -y"
                elif pkg_manager == "dnf":
                    upgrade_cmd = "sudo dnf upgrade gh -y"
                else:
                    return InstallReport(
                        tool_name="gh",
                        result=InstallResult.FAILED,
                        message="未找到支持的包管理器进行升级",
                        error="需要 Homebrew、apt-get 或 dnf 来升级 GitHub CLI",
                    )

            returncode, stdout, stderr = self.run_command(
                upgrade_cmd, shell=True, timeout=600, max_retries=2
            )

            if returncode != 0:
                return InstallReport(
                    tool_name="gh",
                    result=InstallResult.FAILED,
                    message="执行 gh 升级命令失败",
                    error=stderr or "升级命令返回非零退出码",
                )

            # 验证升级
            if not self.verify():
                return InstallReport(
                    tool_name="gh",
                    result=InstallResult.FAILED,
                    message="GitHub CLI 升级验证失败",
                    error="升级命令执行成功，但无法验证 gh 是否正确安装",
                )

            new_version = self._get_installed_version()

            return InstallReport(
                tool_name="gh",
                result=InstallResult.SUCCESS,
                message=f"GitHub CLI 升级成功 ({old_version} -> {new_version})",
                version=new_version,
            )

        except Exception as e:
            return InstallReport(
                tool_name="gh",
                result=InstallResult.FAILED,
                message="GitHub CLI 升级过程中发生异常",
                error=str(e),
            )
