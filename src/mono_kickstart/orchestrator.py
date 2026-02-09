"""安装编排器模块

该模块负责编排整个安装流程，包括：
- 确定工具安装顺序（基于依赖关系）
- 执行单个工具的安装逻辑（检测、跳过或安装）
- 执行批量工具安装（按顺序，容错）
- 调用镜像源配置
- 调用项目创建
- 生成和打印安装摘要
- 执行升级流程（全部或单个工具）
"""

from pathlib import Path
from typing import Dict, List, Optional

from .config import Config, ToolConfig
from .installer_base import InstallReport, InstallResult, ToolInstaller
from .installers.bmad_installer import BMadInstaller
from .installers.bun_installer import BunInstaller
from .installers.claude_installer import ClaudeCodeInstaller
from .installers.codex_installer import CodexInstaller
from .installers.conda_installer import CondaInstaller
from .installers.node_installer import NodeInstaller
from .installers.nvm_installer import NVMInstaller
from .installers.spec_kit_installer import SpecKitInstaller
from .installers.uv_installer import UVInstaller
from .mirror_config import MirrorConfigurator
from .platform_detector import PlatformInfo
from .project_creator import ProjectCreator
from .tool_detector import ToolDetector


# 工具安装顺序（基于依赖关系）
INSTALL_ORDER = [
    "nvm",           # 1. 首先安装 NVM
    "node",          # 2. 通过 NVM 安装 Node.js
    "conda",         # 3. 安装 Conda（独立）
    "bun",           # 4. 安装 Bun（需要 Node.js 作为备选）
    "uv",            # 5. 安装 uv
    "claude-code",   # 6. 安装 Claude Code CLI
    "codex",         # 7. 安装 Codex CLI（可能依赖 Bun）
    "spec-kit",      # 8. 安装 Spec Kit（依赖 uv）
    "bmad-method",   # 9. 安装 BMad Method（依赖 Node.js/Bun）
]


class InstallOrchestrator:
    """安装编排器
    
    负责编排整个安装和升级流程。
    
    Attributes:
        config: 配置对象
        platform_info: 平台信息
        dry_run: 是否为模拟运行
        tool_detector: 工具检测器
        mirror_configurator: 镜像源配置器
    """
    
    def __init__(
        self,
        config: Config,
        platform_info: PlatformInfo,
        dry_run: bool = False
    ):
        """初始化安装编排器
        
        Args:
            config: 配置对象
            platform_info: 平台信息
            dry_run: 是否为模拟运行（默认 False）
        """
        self.config = config
        self.platform_info = platform_info
        self.dry_run = dry_run
        self.tool_detector = ToolDetector()
        self.mirror_configurator = MirrorConfigurator(config.registry)
    
    def get_install_order(self) -> List[str]:
        """获取工具安装顺序
        
        根据配置中启用的工具，返回按依赖关系排序的工具列表。
        
        Returns:
            List[str]: 工具名称列表，按安装顺序排列
        """
        # 获取所有启用的工具
        enabled_tools = []
        for tool_name in INSTALL_ORDER:
            tool_config = self.config.tools.get(tool_name, ToolConfig())
            if tool_config.enabled:
                enabled_tools.append(tool_name)
        
        return enabled_tools
    
    def _create_installer(self, tool_name: str) -> Optional[ToolInstaller]:
        """创建工具安装器实例
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[ToolInstaller]: 安装器实例，如果工具名称无效则返回 None
        """
        tool_config = self.config.tools.get(tool_name, ToolConfig())
        
        installer_map = {
            "nvm": NVMInstaller,
            "node": NodeInstaller,
            "conda": CondaInstaller,
            "bun": BunInstaller,
            "uv": UVInstaller,
            "claude-code": ClaudeCodeInstaller,
            "codex": CodexInstaller,
            "spec-kit": SpecKitInstaller,
            "bmad-method": BMadInstaller,
        }
        
        installer_class = installer_map.get(tool_name)
        if installer_class is None:
            return None
        
        return installer_class(self.platform_info, tool_config)
    
    def install_tool(self, tool_name: str) -> InstallReport:
        """安装单个工具
        
        执行以下步骤：
        1. 检测工具是否已安装
        2. 如果已安装，跳过安装
        3. 如果未安装，创建安装器并执行安装
        
        Args:
            tool_name: 工具名称
            
        Returns:
            InstallReport: 安装报告
        """
        # 如果是模拟运行，返回模拟报告
        if self.dry_run:
            return InstallReport(
                tool_name=tool_name,
                result=InstallResult.SKIPPED,
                message=f"[模拟运行] 将安装 {tool_name}"
            )
        
        # 创建安装器
        installer = self._create_installer(tool_name)
        if installer is None:
            return InstallReport(
                tool_name=tool_name,
                result=InstallResult.FAILED,
                message=f"无效的工具名称: {tool_name}",
                error="工具名称不在支持列表中"
            )
        
        # 执行安装
        try:
            return installer.install()
        except Exception as e:
            return InstallReport(
                tool_name=tool_name,
                result=InstallResult.FAILED,
                message=f"{tool_name} 安装过程中发生异常",
                error=str(e)
            )
    
    def install_all_tools(self) -> Dict[str, InstallReport]:
        """按顺序安装所有工具
        
        按照依赖关系顺序安装所有启用的工具。
        即使某个工具安装失败，也会继续安装其余工具（容错性）。
        
        Returns:
            Dict[str, InstallReport]: 工具名称到安装报告的映射
        """
        install_order = self.get_install_order()
        reports = {}
        
        for tool_name in install_order:
            report = self.install_tool(tool_name)
            reports[tool_name] = report
        
        return reports
    
    def configure_mirrors(self) -> Dict[str, bool]:
        """配置镜像源
        
        配置 npm、Bun 和 uv 的镜像源。
        
        Returns:
            Dict[str, bool]: 工具名称到配置结果的映射
        """
        if self.dry_run:
            return {
                "npm": True,
                "bun": True,
                "uv": True,
            }
        
        return self.mirror_configurator.configure_all()
    
    def create_project(self, project_name: Optional[str] = None, force: bool = False) -> tuple[bool, Optional[str]]:
        """创建项目结构
        
        Args:
            project_name: 项目名称（如果为 None，使用配置中的名称或当前目录名）
            force: 是否强制覆盖已存在的目录
            
        Returns:
            tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        if self.dry_run:
            return True, None
        
        # 确定项目名称
        if project_name is None:
            project_name = self.config.project.name
        
        if project_name is None:
            project_name = Path.cwd().name
        
        # 创建项目
        project_path = Path.cwd() / project_name
        creator = ProjectCreator(project_name, project_path)
        
        return creator.create_project(force=force)
    
    def run_init(self, project_name: Optional[str] = None, force: bool = False) -> Dict[str, InstallReport]:
        """执行完整初始化流程
        
        执行以下步骤：
        1. 安装所有工具
        2. 配置镜像源
        3. 创建项目结构
        
        Args:
            project_name: 项目名称
            force: 是否强制覆盖已存在的目录
            
        Returns:
            Dict[str, InstallReport]: 所有工具的安装报告
        """
        # 1. 安装所有工具
        tool_reports = self.install_all_tools()
        
        # 2. 配置镜像源（在相关工具安装成功后）
        # 检查 npm/node 是否安装成功
        if "node" in tool_reports and tool_reports["node"].result == InstallResult.SUCCESS:
            npm_result = self.mirror_configurator.configure_npm_mirror()
            tool_reports["npm-mirror"] = InstallReport(
                tool_name="npm-mirror",
                result=InstallResult.SUCCESS if npm_result else InstallResult.FAILED,
                message="npm 镜像源配置成功" if npm_result else "npm 镜像源配置失败"
            )
        
        # 检查 bun 是否安装成功
        if "bun" in tool_reports and tool_reports["bun"].result == InstallResult.SUCCESS:
            bun_result = self.mirror_configurator.configure_bun_mirror()
            tool_reports["bun-mirror"] = InstallReport(
                tool_name="bun-mirror",
                result=InstallResult.SUCCESS if bun_result else InstallResult.FAILED,
                message="Bun 镜像源配置成功" if bun_result else "Bun 镜像源配置失败"
            )
        
        # 检查 uv 是否安装成功
        if "uv" in tool_reports and tool_reports["uv"].result == InstallResult.SUCCESS:
            uv_result = self.mirror_configurator.configure_uv_mirror()
            tool_reports["uv-mirror"] = InstallReport(
                tool_name="uv-mirror",
                result=InstallResult.SUCCESS if uv_result else InstallResult.FAILED,
                message="uv 镜像源配置成功" if uv_result else "uv 镜像源配置失败"
            )
        
        # 3. 创建项目结构
        if not self.dry_run:
            project_success, project_error = self.create_project(project_name, force)
            tool_reports["project"] = InstallReport(
                tool_name="project",
                result=InstallResult.SUCCESS if project_success else InstallResult.FAILED,
                message="项目创建成功" if project_success else "项目创建失败",
                error=project_error
            )
        
        return tool_reports
    
    def upgrade_tool(self, tool_name: str) -> InstallReport:
        """升级单个工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            InstallReport: 升级报告
        """
        # 如果是模拟运行，返回模拟报告
        if self.dry_run:
            return InstallReport(
                tool_name=tool_name,
                result=InstallResult.SKIPPED,
                message=f"[模拟运行] 将升级 {tool_name}"
            )
        
        # 创建安装器
        installer = self._create_installer(tool_name)
        if installer is None:
            return InstallReport(
                tool_name=tool_name,
                result=InstallResult.FAILED,
                message=f"无效的工具名称: {tool_name}",
                error="工具名称不在支持列表中"
            )
        
        # 执行升级
        try:
            return installer.upgrade()
        except Exception as e:
            return InstallReport(
                tool_name=tool_name,
                result=InstallResult.FAILED,
                message=f"{tool_name} 升级过程中发生异常",
                error=str(e)
            )
    
    def run_upgrade(self, tool_name: Optional[str] = None) -> Dict[str, InstallReport]:
        """执行升级流程
        
        Args:
            tool_name: 要升级的工具名称（如果为 None，升级所有工具）
            
        Returns:
            Dict[str, InstallReport]: 工具名称到升级报告的映射
        """
        reports = {}
        
        if tool_name is not None:
            # 升级单个工具
            report = self.upgrade_tool(tool_name)
            reports[tool_name] = report
        else:
            # 升级所有已安装的工具
            all_tools = self.tool_detector.detect_all_tools()
            
            for tool_name, tool_status in all_tools.items():
                if tool_status.installed:
                    report = self.upgrade_tool(tool_name)
                    reports[tool_name] = report
        
        return reports
    
    def print_summary(self, reports: Dict[str, InstallReport]) -> None:
        """打印安装摘要
        
        显示成功、跳过和失败的工具列表。
        
        Args:
            reports: 工具名称到安装报告的映射
        """
        # 分类统计
        success_tools = []
        skipped_tools = []
        failed_tools = []
        
        for tool_name, report in reports.items():
            if report.result == InstallResult.SUCCESS:
                success_tools.append((tool_name, report))
            elif report.result == InstallResult.SKIPPED:
                skipped_tools.append((tool_name, report))
            elif report.result == InstallResult.FAILED:
                failed_tools.append((tool_name, report))
        
        # 打印摘要
        print("\n" + "=" * 60)
        print("安装摘要")
        print("=" * 60)
        
        # 成功的工具
        if success_tools:
            print(f"\n✓ 成功 ({len(success_tools)}):")
            for tool_name, report in success_tools:
                version_info = f" (v{report.version})" if report.version else ""
                print(f"  - {tool_name}{version_info}: {report.message}")
        
        # 跳过的工具
        if skipped_tools:
            print(f"\n○ 跳过 ({len(skipped_tools)}):")
            for tool_name, report in skipped_tools:
                version_info = f" (v{report.version})" if report.version else ""
                print(f"  - {tool_name}{version_info}: {report.message}")
        
        # 失败的工具
        if failed_tools:
            print(f"\n✗ 失败 ({len(failed_tools)}):")
            for tool_name, report in failed_tools:
                print(f"  - {tool_name}: {report.message}")
                if report.error:
                    print(f"    错误: {report.error}")
        
        print("\n" + "=" * 60)
        
        # 总结
        total = len(reports)
        print(f"总计: {total} 个任务")
        print(f"  成功: {len(success_tools)}")
        print(f"  跳过: {len(skipped_tools)}")
        print(f"  失败: {len(failed_tools)}")
        print("=" * 60 + "\n")
