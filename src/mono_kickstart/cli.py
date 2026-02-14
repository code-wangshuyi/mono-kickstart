"""
CLI 入口模块

定义命令行接口和子命令（使用 argparse 标准库）。
"""

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from mono_kickstart import __version__


# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# 可用工具列表（用于补全）
AVAILABLE_TOOLS = [
    "nvm",
    "node",
    "conda",
    "bun",
    "uv",
    "gh",
    "claude-code",
    "codex",
    "opencode",
    "npx",
    "uipro",
    "spec-kit",
    "bmad-method",
]

# 可下载的工具列表（仅支持有独立安装包的工具）
DOWNLOADABLE_TOOLS = [
    "conda",
]

# MCP 服务器配置注册表
MCP_SERVERS = ["chrome", "context7"]

# --allow 可选值
ALLOW_CHOICES = ["all"]

# --allow all 对应的完整权限列表
ALLOW_ALL_PERMISSIONS = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "Task",
    "NotebookEdit",
    "TodoWrite",
    "AskUserQuestion",
    "ListDir",
    "MultiEdit",
]

# --mode 可选值
MODE_CHOICES = ["plan"]

# --on 可选值
ON_CHOICES = ["team"]

# --off 可选值
OFF_CHOICES = ["suggestion", "team"]

# --skills 可选值
SKILL_CHOICES = ["uipro"]

PLUGIN_CHOICES = ["omc"]
OPENCODE_PLUGIN_CHOICES = ["omo"]

# Skill 配置注册表
SKILL_CONFIGS = {
    "uipro": {
        "name": "ui-ux-pro-max",
        "display_name": "UIPro",
        "cli_command": "uipro",
        "init_command": "uipro init --ai claude",
        "install_hint": "npm install -g uipro-cli",
        "skill_dir": ".claude/skills/ui-ux-pro-max",
    },
}

MCP_SERVER_CONFIGS = {
    "chrome": {
        "name": "chrome-devtools",
        "display_name": "Chrome DevTools",
        "config": {"command": "npx", "args": ["chrome-devtools-mcp@latest"]},
        "claude_mcp_add_cmd": "claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest",
    },
    "context7": {
        "name": "context7",
        "display_name": "Context7",
        "config": {"command": "npx", "args": ["-y", "@upstash/context7-mcp@latest"]},
        "claude_mcp_add_cmd": "claude mcp add context7 -- npx -y @upstash/context7-mcp@latest",
    },
}


GITHUB_RELEASE_SOURCES = {
    "nvm": "nvm-sh/nvm",
    "conda": "conda/conda",
    "bun": "oven-sh/bun",
    "uv": "astral-sh/uv",
    "gh": "cli/cli",
    "spec-kit": "github/spec-kit",
}


NPM_PACKAGE_SOURCES = {
    "claude-code": "@anthropic-ai/claude-code",
    "codex": "@openai/codex",
    "opencode": "opencode-ai",
    "npx": "npm",
    "uipro": "uipro-cli",
    "bmad-method": "bmad-method",
}


class ChineseHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """中文化的帮助信息格式器"""

    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = "用法: "
        return super()._format_usage(usage, actions, groups, prefix)


def create_parser() -> argparse.ArgumentParser:
    """创建主解析器和子命令解析器

    Returns:
        配置好的 ArgumentParser 对象
    """
    # 主解析器
    parser = argparse.ArgumentParser(
        prog="mk",
        description="Mono-Kickstart - Monorepo 项目模板脚手架 CLI 工具\n\n"
        "通过一条命令快速初始化标准化的 Monorepo 工程，\n"
        "自动完成开发环境搭建与工具链安装。",
        formatter_class=ChineseHelpFormatter,
        add_help=True,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Mono-Kickstart version {__version__}",
        help="显示版本号",
    )

    # 子命令解析器
    subparsers = parser.add_subparsers(title="可用命令", dest="command", help="子命令帮助信息")

    # init 子命令
    init_parser = subparsers.add_parser(
        "init",
        help="初始化 Monorepo 项目和开发环境",
        description="初始化 Monorepo 项目和开发环境",
        formatter_class=ChineseHelpFormatter,
    )
    init_parser.add_argument("--config", type=str, metavar="PATH", help="配置文件路径")
    init_parser.add_argument("--save-config", action="store_true", help="保存配置到 .kickstartrc")
    init_parser.add_argument("--interactive", action="store_true", help="交互式配置")
    init_parser.add_argument("--force", action="store_true", help="强制覆盖已有配置")
    init_parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际安装")

    # upgrade 子命令
    upgrade_parser = subparsers.add_parser(
        "upgrade",
        help="升级已安装的开发工具",
        description="升级已安装的开发工具",
        formatter_class=ChineseHelpFormatter,
    )
    upgrade_parser.add_argument(
        "tool",
        nargs="?",
        choices=AVAILABLE_TOOLS,
        metavar="TOOL",
        help=f"要升级的工具名称 (可选值: {', '.join(AVAILABLE_TOOLS)})",
    )
    upgrade_parser.add_argument("--all", action="store_true", help="升级所有工具")
    upgrade_parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际升级")

    # install 子命令
    install_parser = subparsers.add_parser(
        "install",
        help="安装开发工具",
        description="安装开发工具",
        formatter_class=ChineseHelpFormatter,
    )
    install_parser.add_argument(
        "tool",
        nargs="?",
        choices=AVAILABLE_TOOLS,
        metavar="TOOL",
        help=f"要安装的工具名称 (可选值: {', '.join(AVAILABLE_TOOLS)})",
    )
    install_parser.add_argument("--all", action="store_true", help="安装所有工具")
    install_parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际安装")

    # set-default 子命令
    set_default_parser = subparsers.add_parser(
        "set-default",
        help="设置工具的默认版本（如通过 nvm 设置 Node.js 默认版本）",
        description="设置工具的默认版本（如通过 nvm 设置 Node.js 默认版本）",
        formatter_class=ChineseHelpFormatter,
    )
    set_default_parser.add_argument(
        "tool", choices=["node"], metavar="TOOL", help="要设置默认版本的工具名称 (可选值: node)"
    )
    set_default_parser.add_argument(
        "version",
        nargs="?",
        default=None,
        metavar="VERSION",
        help="要设置的版本号（如 20.2.0），不指定则使用默认版本 20.2.0",
    )

    # setup-shell 子命令
    setup_shell_parser = subparsers.add_parser(
        "setup-shell",
        help="配置 shell（PATH 和 Tab 补全）",
        description="配置 shell（PATH 和 Tab 补全）",
        formatter_class=ChineseHelpFormatter,
    )

    # status 子命令
    status_parser = subparsers.add_parser(
        "status",
        help="查看已安装工具的状态和版本",
        description="查看已安装工具的状态和版本",
        formatter_class=ChineseHelpFormatter,
    )

    show_parser = subparsers.add_parser(
        "show",
        help="展示工具信息",
        description="展示工具信息",
        formatter_class=ChineseHelpFormatter,
    )
    show_subparsers = show_parser.add_subparsers(
        title="展示操作", dest="show_action", help="show 子命令帮助信息"
    )
    show_subparsers.add_parser(
        "info",
        help="检查所有工具最新版本并生成相关命令",
        description="检查所有工具最新版本并生成相关命令",
        formatter_class=ChineseHelpFormatter,
    )

    # download 子命令
    download_parser = subparsers.add_parser(
        "download",
        help="下载工具安装包到本地（不安装）",
        description="下载工具安装包到本地磁盘（不执行安装）\n\n"
        "适用于离线安装、气隔环境预下载、团队共享安装包等场景。",
        formatter_class=ChineseHelpFormatter,
    )
    download_parser.add_argument(
        "tool",
        choices=DOWNLOADABLE_TOOLS,
        metavar="TOOL",
        help=f"要下载的工具名称 (可选值: {', '.join(DOWNLOADABLE_TOOLS)})",
    )
    download_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
        metavar="DIR",
        help="下载文件保存目录 (默认: 当前目录)",
    )
    download_parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际下载")

    # config 子命令
    config_parser = subparsers.add_parser(
        "config",
        help="管理配置（镜像源等）",
        description="管理配置（镜像源等）",
        formatter_class=ChineseHelpFormatter,
    )

    config_subparsers = config_parser.add_subparsers(
        title="配置操作", dest="config_action", help="配置子命令帮助信息"
    )

    # config mirror 子命令
    mirror_parser = config_subparsers.add_parser(
        "mirror",
        help="配置镜像源",
        description="配置开发工具的镜像源（npm、bun、pip、uv、conda）",
        formatter_class=ChineseHelpFormatter,
    )

    mirror_subparsers = mirror_parser.add_subparsers(
        title="镜像操作", dest="mirror_action", help="镜像操作子命令"
    )

    # config mirror show
    mirror_subparsers.add_parser(
        "show",
        help="显示当前镜像源配置",
        formatter_class=ChineseHelpFormatter,
    )

    # config mirror reset
    mirror_reset_parser = mirror_subparsers.add_parser(
        "reset",
        help="重置镜像源为上游默认值",
        formatter_class=ChineseHelpFormatter,
    )
    mirror_reset_parser.add_argument(
        "--tool",
        choices=["npm", "bun", "pip", "uv", "conda"],
        metavar="TOOL",
        help="仅重置指定工具的镜像源（可选值: npm, bun, pip, uv, conda）",
    )

    # config mirror set
    mirror_set_parser = mirror_subparsers.add_parser(
        "set",
        help="设置镜像源（支持预设: china/default，或指定工具和 URL）",
        formatter_class=ChineseHelpFormatter,
    )
    mirror_set_parser.add_argument(
        "tool",
        choices=["npm", "bun", "pip", "uv", "conda", "china", "default"],
        metavar="TOOL",
        help="工具名称 (npm, bun, pip, uv, conda) 或预设名 (china: 国内镜像, default: 上游默认)",
    )
    mirror_set_parser.add_argument(
        "url", nargs="?", default=None, metavar="URL", help="镜像源 URL（使用预设时无需指定）"
    )

    # dd 子命令 (driven development)
    dd_parser = subparsers.add_parser(
        "dd",
        help="配置驱动开发工具（Spec-Kit、BMad Method）",
        description="为当前项目配置驱动开发工具\n\n"
        "支持 Spec-Kit（规格驱动开发）和 BMad Method（AI 敏捷开发框架）。\n"
        "至少需要指定一个工具标志（--spec-kit 或 --bmad-method）。",
        formatter_class=ChineseHelpFormatter,
        epilog="示例:\n"
        "  mk dd --spec-kit                使用 Claude 初始化 Spec-Kit（默认）\n"
        "  mk dd --spec-kit --codex        使用 Codex 初始化 Spec-Kit\n"
        "  mk dd --bmad-method             安装 BMad Method\n"
        "  mk dd --spec-kit --bmad-method  同时初始化两个工具\n"
        "  mk dd --spec-kit --force        强制重新初始化 Spec-Kit",
    )
    dd_parser.add_argument(
        "-s", "--spec-kit", action="store_true", help="初始化 Spec-Kit 规格驱动开发工具"
    )
    dd_parser.add_argument(
        "-b", "--bmad-method", action="store_true", help="安装 BMad Method 敏捷开发框架"
    )
    dd_ai_group = dd_parser.add_mutually_exclusive_group()
    dd_ai_group.add_argument(
        "-c", "--claude", action="store_true", help="使用 Claude 作为 AI 后端（默认）"
    )
    dd_ai_group.add_argument("-x", "--codex", action="store_true", help="使用 Codex 作为 AI 后端")
    dd_parser.add_argument(
        "-f", "--force", action="store_true", help="强制重新初始化（覆盖已有配置）"
    )
    dd_parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际执行")

    # claude 子命令
    claude_parser = subparsers.add_parser(
        "claude",
        help="配置 Claude Code 项目设置（MCP 服务器等）",
        description="为当前项目配置 Claude Code 设置\n\n"
        "支持配置 MCP (Model Context Protocol) 服务器、权限、功能开关、技能包和插件，\n"
        "将配置写入当前目录的 .claude/ 目录。",
        formatter_class=ChineseHelpFormatter,
        epilog="示例:\n"
        "  mk claude --mcp chrome               添加 Chrome DevTools MCP 服务器\n"
        "  mk claude --allow all                允许所有命令\n"
        "  mk claude --mode plan                默认以 plan 模式运行\n"
        "  mk claude --allow all --mode plan    同时配置权限和模式\n"
        "  mk claude --allow all --mcp chrome   同时配置权限和 MCP\n"
        "  mk claude --on team                  启用实验性团队功能\n"
        "  mk claude --off team                 禁用实验性团队功能\n"
        "  mk claude --off suggestion             关闭提示建议功能\n"
        "  mk claude --skills uipro              安装 UIPro 设计技能包\n"
        "  mk claude --plugin omc               安装并配置 Oh My Claude Code\n"
        "  mk claude --allow all --dry-run      模拟运行，查看将写入的配置",
    )
    claude_parser.add_argument(
        "--mcp",
        type=str,
        choices=MCP_SERVERS,
        metavar="SERVER",
        help=f"添加 MCP 服务器配置 (可选值: {', '.join(MCP_SERVERS)})",
    )
    claude_parser.add_argument(
        "--allow",
        type=str,
        choices=ALLOW_CHOICES,
        metavar="SCOPE",
        help=f"配置权限允许所有命令 (可选值: {', '.join(ALLOW_CHOICES)})",
    )
    claude_parser.add_argument(
        "--mode",
        type=str,
        choices=MODE_CHOICES,
        metavar="MODE",
        help=f"设置权限模式 (可选值: {', '.join(MODE_CHOICES)})",
    )
    claude_parser.add_argument(
        "--on",
        type=str,
        choices=ON_CHOICES,
        metavar="FEATURE",
        help=f"启用指定功能 (可选值: {', '.join(ON_CHOICES)})",
    )
    claude_parser.add_argument(
        "--off",
        type=str,
        choices=OFF_CHOICES,
        metavar="FEATURE",
        help=f"关闭指定功能 (可选值: {', '.join(OFF_CHOICES)})",
    )
    claude_parser.add_argument(
        "--skills",
        type=str,
        choices=SKILL_CHOICES,
        metavar="SKILL",
        help=f"安装 Claude Code 技能包 (可选值: {', '.join(SKILL_CHOICES)})",
    )
    claude_parser.add_argument(
        "--plugin",
        type=str,
        choices=PLUGIN_CHOICES,
        metavar="PLUGIN",
        help=f"安装 Claude Code 插件 (可选值: {', '.join(PLUGIN_CHOICES)})",
    )
    claude_parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际写入配置")

    opencode_parser = subparsers.add_parser(
        "opencode",
        help="配置 OpenCode 扩展能力",
        description="配置 OpenCode 扩展能力\n\n支持安装插件并写入当前项目配置。",
        formatter_class=ChineseHelpFormatter,
        epilog="示例:\n"
        "  mk opencode --plugin omo            安装并配置 Oh My OpenCode\n"
        "  mk opencode --plugin omo --dry-run  模拟运行，查看将执行的操作",
    )
    opencode_parser.add_argument(
        "--plugin",
        type=str,
        choices=OPENCODE_PLUGIN_CHOICES,
        metavar="PLUGIN",
        help=f"安装 OpenCode 插件 (可选值: {', '.join(OPENCODE_PLUGIN_CHOICES)})",
    )
    opencode_parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际执行")

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    """执行 init 命令

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    from mono_kickstart.platform_detector import PlatformDetector
    from mono_kickstart.config import ConfigManager
    from mono_kickstart.orchestrator import InstallOrchestrator

    logger.info("🚀 Mono-Kickstart - 初始化 Monorepo 项目")
    logger.info("")

    try:
        # 1. 检测平台
        logger.info("📋 检测平台信息...")
        detector = PlatformDetector()

        if not detector.is_supported():
            platform_info = detector.detect_all()
            logger.error(
                f"❌ 错误: 不支持的平台 ({platform_info.os.value}/{platform_info.arch.value})"
            )
            logger.error("支持的平台:")
            logger.error("  - macOS ARM64")
            logger.error("  - macOS x86_64")
            logger.error("  - Linux x86_64")
            return 1

        platform_info = detector.detect_all()
        logger.info(f"✓ 平台: {platform_info.os.value}/{platform_info.arch.value}")
        logger.info(f"✓ Shell: {platform_info.shell.value}")
        logger.info("")

        # 2. 加载配置
        config_manager = ConfigManager()

        # 如果使用交互式模式
        if args.interactive:
            from mono_kickstart.interactive import InteractiveConfigurator

            # 加载默认配置作为交互式配置的基础
            try:
                default_config = config_manager.load_with_priority(
                    cli_config=Path(args.config) if args.config else None,
                    project_config=Path(".kickstartrc"),
                    user_config=Path.home() / ".kickstartrc",
                )
            except Exception:
                # 如果加载失败，使用空配置
                default_config = config_manager.load_from_defaults()

            # 运行交互式配置向导
            configurator = InteractiveConfigurator(default_config)
            config = configurator.run_wizard()

            # 显示配置摘要并确认
            if not configurator.confirm_config(config):
                logger.info("❌ 用户取消操作")
                return 0

            logger.info("")
        else:
            # 非交互式模式：按优先级加载配置
            logger.info("📋 加载配置...")

            try:
                cli_config_path = Path(args.config) if args.config else None
                config = config_manager.load_with_priority(
                    cli_config=cli_config_path,
                    project_config=Path(".kickstartrc"),
                    user_config=Path.home() / ".kickstartrc",
                )

                # 验证配置
                errors = config_manager.validate(config)
                if errors:
                    logger.error("❌ 配置验证失败:")
                    for error in errors:
                        logger.error(f"  - {error}")
                    return 2

                logger.info("✓ 配置加载成功")
                logger.info("")

            except FileNotFoundError as e:
                logger.error(f"❌ 配置文件不存在: {e}")
                return 2
            except Exception as e:
                logger.error(f"❌ 配置加载失败: {e}")
                logger.debug("详细错误信息:", exc_info=True)
                return 2

        # 3. 保存配置（如果需要）
        if args.save_config:
            try:
                config_path = Path(".kickstartrc")
                config_manager.save_to_file(config, config_path)
                logger.info(f"✓ 配置已保存到 {config_path}")
                logger.info("")
            except Exception as e:
                logger.warning(f"⚠️  警告: 配置保存失败: {e}")
                logger.info("")

        # 4. 创建安装编排器
        orchestrator = InstallOrchestrator(
            config=config, platform_info=platform_info, dry_run=args.dry_run
        )

        # 5. 执行初始化流程
        if args.dry_run:
            logger.info("🔍 [模拟运行模式]")
            logger.info("")

        logger.info("🚀 开始初始化...")
        logger.info("")

        # 执行完整初始化流程
        reports = orchestrator.run_init(project_name=config.project.name, force=args.force)

        # 打印摘要
        orchestrator.print_summary(reports)

        # 检查是否有失败的任务
        from mono_kickstart.installer_base import InstallResult

        failed_count = sum(1 for r in reports.values() if r.result == InstallResult.FAILED)

        if failed_count == len(reports):
            # 所有任务都失败
            logger.error("❌ 所有任务都失败了")
            return 3
        elif failed_count > 0:
            # 部分任务失败
            logger.warning(f"⚠️  {failed_count} 个任务失败，但其他任务已成功完成")
            return 0
        else:
            # 全部成功
            logger.info("✨ 初始化完成！")
            return 0

    except KeyboardInterrupt:
        logger.error("\n❌ 用户中断操作")
        return 130
    except Exception as e:
        logger.error(f"❌ 初始化过程中发生错误: {e}")
        logger.debug("详细错误信息:", exc_info=True)
        return 1


def cmd_upgrade(args: argparse.Namespace) -> int:
    """执行 upgrade 命令

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    from mono_kickstart.platform_detector import PlatformDetector
    from mono_kickstart.config import ConfigManager
    from mono_kickstart.orchestrator import InstallOrchestrator
    from mono_kickstart.tool_detector import ToolDetector

    logger.info("🔄 Mono-Kickstart - 升级开发工具")
    logger.info("")

    try:
        # 1. 检测平台
        detector = PlatformDetector()
        if not detector.is_supported():
            platform_info = detector.detect_all()
            logger.error(
                f"❌ 错误: 不支持的平台 ({platform_info.os.value}/{platform_info.arch.value})"
            )
            return 1

        platform_info = detector.detect_all()

        # 2. 加载配置
        config_manager = ConfigManager()
        try:
            config = config_manager.load_with_priority(
                cli_config=None,
                project_config=Path(".kickstartrc"),
                user_config=Path.home() / ".kickstartrc",
            )
        except Exception as e:
            logger.warning(f"⚠️  警告: 配置加载失败，使用默认配置: {e}")
            config = config_manager.load_from_defaults()

        # 3. 创建安装编排器
        orchestrator = InstallOrchestrator(
            config=config, platform_info=platform_info, dry_run=args.dry_run
        )

        # 4. 确定要升级的工具
        if args.dry_run:
            logger.info("🔍 [模拟运行模式]")
            logger.info("")

        # 如果指定了 --all 或没有指定工具名称，升级所有已安装的工具
        tool_name = None
        if not args.all and args.tool:
            tool_name = args.tool
            logger.info(f"🔄 升级工具: {tool_name}")
        else:
            logger.info("🔄 升级所有已安装的工具")
            # 检测已安装的工具
            tool_detector = ToolDetector()
            all_tools = tool_detector.detect_all_tools()
            installed_tools = [name for name, status in all_tools.items() if status.installed]

            if not installed_tools:
                logger.warning("⚠️  没有检测到已安装的工具")
                return 0

            logger.info(f"检测到 {len(installed_tools)} 个已安装的工具:")
            for tool in installed_tools:
                logger.info(f"  - {tool}")

        logger.info("")

        # 5. 执行升级流程
        reports = orchestrator.run_upgrade(tool_name=tool_name)

        # 打印摘要
        orchestrator.print_summary(reports)

        # 检查是否有失败的任务
        from mono_kickstart.installer_base import InstallResult

        failed_count = sum(1 for r in reports.values() if r.result == InstallResult.FAILED)

        if failed_count == len(reports) and len(reports) > 0:
            # 所有任务都失败
            logger.error("❌ 所有任务都失败了")
            return 3
        elif failed_count > 0:
            # 部分任务失败
            logger.warning(f"⚠️  {failed_count} 个任务失败，但其他任务已成功完成")
            return 0
        else:
            # 全部成功
            logger.info("✨ 升级完成！")
            return 0

    except KeyboardInterrupt:
        logger.error("\n❌ 用户中断操作")
        return 130
    except Exception as e:
        logger.error(f"❌ 升级过程中发生错误: {e}")
        logger.debug("详细错误信息:", exc_info=True)
        return 1


def cmd_install(args: argparse.Namespace) -> int:
    """执行 install 命令

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    from mono_kickstart.platform_detector import PlatformDetector
    from mono_kickstart.config import ConfigManager
    from mono_kickstart.orchestrator import InstallOrchestrator

    logger.info("📦 Mono-Kickstart - 安装开发工具")
    logger.info("")

    try:
        # 1. 检测平台
        detector = PlatformDetector()
        if not detector.is_supported():
            platform_info = detector.detect_all()
            logger.error(
                f"❌ 错误: 不支持的平台 ({platform_info.os.value}/{platform_info.arch.value})"
            )
            return 1

        platform_info = detector.detect_all()

        # 2. 加载配置
        config_manager = ConfigManager()
        try:
            config = config_manager.load_with_priority(
                cli_config=None,
                project_config=Path(".kickstartrc"),
                user_config=Path.home() / ".kickstartrc",
            )
        except Exception as e:
            logger.warning(f"⚠️  警告: 配置加载失败，使用默认配置: {e}")
            config = config_manager.load_from_defaults()

        # 3. 创建安装编排器
        orchestrator = InstallOrchestrator(
            config=config, platform_info=platform_info, dry_run=args.dry_run
        )

        # 4. 确定要安装的工具
        if args.dry_run:
            logger.info("🔍 [模拟运行模式]")
            logger.info("")

        if not args.all and not args.tool:
            logger.error("❌ 错误: 请指定要安装的工具名称或使用 --all 安装所有工具")
            return 1

        # 5. 执行安装流程
        if args.all:
            # 安装所有工具
            logger.info("📦 安装所有工具")
            logger.info("")
            reports = orchestrator.install_all_tools()
        else:
            # 安装单个工具
            tool_name = args.tool
            logger.info(f"📦 安装工具: {tool_name}")
            logger.info("")
            report = orchestrator.install_tool(tool_name)
            reports = {tool_name: report}

        # 打印摘要
        orchestrator.print_summary(reports)

        # 检查是否有失败的任务
        from mono_kickstart.installer_base import InstallResult

        failed_count = sum(1 for r in reports.values() if r.result == InstallResult.FAILED)

        if failed_count == len(reports) and len(reports) > 0:
            # 所有任务都失败
            logger.error("❌ 所有任务都失败了")
            return 3
        elif failed_count > 0:
            # 部分任务失败
            logger.warning(f"⚠️  {failed_count} 个任务失败，但其他任务已成功完成")
            return 0
        else:
            # 全部成功
            logger.info("✨ 安装完成！")
            return 0

    except KeyboardInterrupt:
        logger.error("\n❌ 用户中断操作")
        return 130
    except Exception as e:
        logger.error(f"❌ 安装过程中发生错误: {e}")
        logger.debug("详细错误信息:", exc_info=True)
        return 1


def cmd_set_default(args: argparse.Namespace) -> int:
    """执行 set-default 命令

    通过 nvm 设置 Node.js 的默认版本。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    from pathlib import Path as _Path

    if args.tool != "node":
        logger.error(f"❌ 错误: 不支持设置 {args.tool} 的默认版本")
        return 1

    version = args.version or "20.2.0"

    logger.info(f"🔧 设置 Node.js 默认版本为 {version}")
    logger.info("")

    try:
        nvm_sh = _Path.home() / ".nvm" / "nvm.sh"

        if not nvm_sh.exists():
            logger.error("❌ 错误: NVM 未安装，无法设置 Node.js 默认版本")
            logger.error("请先运行 mk install nvm 安装 NVM")
            return 1

        # 1. 检查目标版本是否已安装，未安装则先安装
        check_cmd = f"bash -c 'source {nvm_sh} && nvm ls {version}'"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True, timeout=10)

        if result.returncode != 0 or "N/A" in result.stdout:
            logger.info(f"📦 Node.js {version} 未安装，正在通过 nvm 安装...")
            install_cmd = f"bash -c 'source {nvm_sh} && nvm install {version}'"
            result = subprocess.run(
                install_cmd, shell=True, capture_output=True, text=True, timeout=600
            )
            if result.returncode != 0:
                logger.error(f"❌ 安装 Node.js {version} 失败")
                logger.error(result.stderr or "安装命令返回非零退出码")
                return 1
            logger.info(f"✓ Node.js {version} 安装成功")

        # 2. 设置默认版本
        alias_cmd = f"bash -c 'source {nvm_sh} && nvm alias default {version}'"
        result = subprocess.run(alias_cmd, shell=True, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            logger.error(f"❌ 设置默认版本失败")
            logger.error(result.stderr or "命令返回非零退出码")
            return 1

        # 3. 验证
        verify_cmd = f"bash -c 'source {nvm_sh} && nvm current'"
        result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True, timeout=10)

        current = result.stdout.strip() if result.returncode == 0 else "未知"
        logger.info(f"✓ 已将 Node.js 默认版本设置为 {version}")
        logger.info(f"  当前版本: {current}")
        logger.info("")
        logger.info("💡 提示: 请重新打开终端或运行 'source ~/.nvm/nvm.sh' 使更改生效")
        return 0

    except subprocess.TimeoutExpired:
        logger.error("❌ 命令执行超时")
        return 1
    except KeyboardInterrupt:
        logger.error("\n❌ 用户中断操作")
        return 130
    except Exception as e:
        logger.error(f"❌ 设置默认版本过程中发生错误: {e}")
        return 1


def cmd_setup_shell(args: argparse.Namespace) -> int:
    """执行 setup-shell 命令

    配置 shell 环境（PATH 和 Tab 补全）

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    from mono_kickstart.shell_completion import setup_shell_completion

    try:
        setup_shell_completion()
        return 0
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """执行 status 命令

    查看已安装工具的状态和版本。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    from mono_kickstart.tool_detector import ToolDetector

    DISPLAY_NAMES = {
        "nvm": "NVM",
        "node": "Node.js",
        "conda": "Conda",
        "bun": "Bun",
        "uv": "uv",
        "claude-code": "Claude Code",
        "codex": "Codex",
        "opencode": "OpenCode",
        "npx": "npx",
        "spec-kit": "Spec Kit",
        "bmad-method": "BMad Method",
    }

    detector = ToolDetector()
    tools = detector.detect_all_tools()

    logger.info("工具状态:")
    for name, status in tools.items():
        display = DISPLAY_NAMES.get(name, name)
        if status.installed:
            version = status.version or "已安装"
            path = status.path or ""
            logger.info(f"✓ {display:<12} {version:<10} {path}")
        else:
            logger.info(f"✗ {display:<12} 未安装")

    return 0


def _run_quick_command(command: str, timeout: int = 20) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except Exception as e:
        return 1, "", str(e)


def _fetch_latest_from_github(tool_name: str) -> str | None:
    repo = GITHUB_RELEASE_SOURCES.get(tool_name)
    if not repo:
        return None

    code, stdout, _ = _run_quick_command(
        f"curl -fsSL https://api.github.com/repos/{repo}/releases/latest",
        timeout=20,
    )
    if code != 0:
        return None

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None

    tag = payload.get("tag_name")
    if not isinstance(tag, str):
        return None
    return tag.lstrip("v")


def _fetch_latest_node_lts() -> str | None:
    code, stdout, _ = _run_quick_command(
        "curl -fsSL https://nodejs.org/dist/index.json", timeout=20
    )
    if code != 0:
        return None

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, list):
        return None

    for item in payload:
        if isinstance(item, dict) and item.get("lts"):
            version = item.get("version")
            if isinstance(version, str):
                return version.lstrip("v")
    return None


def _fetch_latest_from_npm(tool_name: str) -> str | None:
    package_name = NPM_PACKAGE_SOURCES.get(tool_name)
    if not package_name or not shutil.which("npm"):
        return None

    code, stdout, _ = _run_quick_command(f"npm view {package_name} version", timeout=20)
    if code != 0:
        return None

    version = stdout.strip()
    return version or None


def _get_latest_version(tool_name: str) -> str | None:
    if tool_name == "node":
        return _fetch_latest_node_lts()

    if tool_name in GITHUB_RELEASE_SOURCES:
        return _fetch_latest_from_github(tool_name)

    if tool_name in NPM_PACKAGE_SOURCES:
        return _fetch_latest_from_npm(tool_name)

    return None


def _parse_semver(version: str | None) -> tuple[int, int, int] | None:
    if not version:
        return None

    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        return None

    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def cmd_show(args: argparse.Namespace) -> int:
    show_action = getattr(args, "show_action", None)

    if show_action is None:
        parser = create_parser()
        parser.parse_args(["show", "--help"])
        return 0

    if show_action == "info":
        return cmd_show_info(args)

    return 0


def cmd_show_info(args: argparse.Namespace) -> int:
    from mono_kickstart.tool_detector import ToolDetector

    logger.info("🔍 Mono-Kickstart - show info")
    logger.info("")

    detector = ToolDetector()
    detected_tools = detector.detect_all_tools()

    related_commands = []

    logger.info("工具版本信息:")
    for tool_name in AVAILABLE_TOOLS:
        status = detected_tools.get(tool_name)
        current_version = status.version if status and status.installed else "未安装"
        latest_version = _get_latest_version(tool_name)
        latest_display = latest_version or "未知"

        recommendation = "无"
        if not status or not status.installed:
            recommendation = f"mk install {tool_name}"
            related_commands.append(recommendation)
        else:
            current_semver = _parse_semver(status.version)
            latest_semver = _parse_semver(latest_version)
            if current_semver and latest_semver and current_semver < latest_semver:
                recommendation = f"mk upgrade {tool_name}"
                related_commands.append(recommendation)

        logger.info(
            f"- {tool_name:<12} 当前: {current_version:<16} 最新: {latest_display:<12} 建议: {recommendation}"
        )

    logger.info("")
    logger.info("相关命令:")
    if related_commands:
        for cmd in related_commands:
            logger.info(f"  {cmd}")
    else:
        logger.info("  无（已是最新或无需操作）")

    return 0


def cmd_download(args: argparse.Namespace) -> int:
    """执行 download 命令

    下载工具安装包到本地磁盘，不执行安装。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    from mono_kickstart.platform_detector import PlatformDetector

    logger.info("📥 Mono-Kickstart - 下载工具安装包")
    logger.info("")

    try:
        # 1. 检测平台
        logger.info("📋 检测平台信息...")
        detector = PlatformDetector()

        if not detector.is_supported():
            platform_info = detector.detect_all()
            logger.error(
                f"❌ 错误: 不支持的平台 ({platform_info.os.value}/{platform_info.arch.value})"
            )
            logger.error("支持的平台:")
            logger.error("  - macOS ARM64")
            logger.error("  - macOS x86_64")
            logger.error("  - Linux x86_64")
            return 1

        platform_info = detector.detect_all()
        logger.info(f"✓ 平台: {platform_info.os.value}/{platform_info.arch.value}")
        logger.info("")

        # 2. 验证输出目录
        output_dir = Path(args.output).resolve()
        if output_dir.exists() and not output_dir.is_dir():
            logger.error(f"❌ 错误: 输出路径不是目录: {output_dir}")
            logger.error("提示: --output 参数应指定一个目录路径")
            return 1

        # 3. 根据工具类型分发到具体下载函数
        if args.tool == "conda":
            return _download_conda(platform_info, output_dir, args.dry_run)
        else:
            logger.error(f"❌ 错误: 不支持下载的工具: {args.tool}")
            return 1

    except KeyboardInterrupt:
        logger.error("\n❌ 用户中断操作")
        return 130
    except Exception as e:
        logger.error(f"❌ 下载过程中发生错误: {e}")
        logger.debug("详细错误信息:", exc_info=True)
        return 1


def _download_conda(platform_info, output_dir: Path, dry_run: bool) -> int:
    """下载 Conda 安装包

    Args:
        platform_info: 平台信息
        output_dir: 输出目录
        dry_run: 是否模拟运行

    Returns:
        退出码
    """
    from mono_kickstart.platform_detector import OS, Arch
    from mono_kickstart.config import ConfigManager, RegistryConfig

    # 加载配置（获取镜像源）
    config_manager = ConfigManager()
    try:
        config = config_manager.load_with_priority(
            cli_config=None,
            project_config=Path(".kickstartrc"),
            user_config=Path.home() / ".kickstartrc",
        )
        base_url = config.registry.conda
    except Exception:
        base_url = RegistryConfig().conda

    # 确定安装包文件名
    if platform_info.os == OS.LINUX and platform_info.arch == Arch.X86_64:
        installer_name = "Miniconda3-latest-Linux-x86_64.sh"
    elif platform_info.os == OS.MACOS and platform_info.arch == Arch.ARM64:
        installer_name = "Miniconda3-latest-MacOSX-arm64.sh"
    elif platform_info.os == OS.MACOS and platform_info.arch == Arch.X86_64:
        installer_name = "Miniconda3-latest-MacOSX-x86_64.sh"
    else:
        logger.error(f"❌ 错误: 不支持的平台 ({platform_info.os.value}/{platform_info.arch.value})")
        return 1

    download_url = f"{base_url}/miniconda/{installer_name}"
    dest_file = output_dir / installer_name

    # Dry-run 模式
    if dry_run:
        logger.info("🔍 [模拟运行模式]")
        logger.info("")
        logger.info("📥 将下载以下文件:")
        logger.info(f"  文件名: {installer_name}")
        logger.info(f"  来源: {download_url}")
        logger.info(f"  保存到: {dest_file}")
        return 0

    # 实际下载
    logger.info(f"📥 正在下载 {installer_name} ...")
    logger.info(f"  来源: {download_url}")
    logger.info("")

    # 确保目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 使用 curl 下载（与 CondaInstaller._download_installer 保持一致）
    result = subprocess.run(
        f"curl -fsSL -o {dest_file} {download_url}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0 or not dest_file.exists() or dest_file.stat().st_size == 0:
        logger.error("❌ 下载失败: 无法连接到镜像服务器")
        logger.error(
            "提示: 请检查网络连接后重试，或使用 'mk config mirror set conda <URL>' 更换镜像源"
        )
        # 清理可能的部分下载文件
        if dest_file.exists():
            try:
                dest_file.unlink()
            except OSError:
                pass
        return 1

    # 计算文件大小和 SHA256
    file_size = dest_file.stat().st_size
    sha256_hash = hashlib.sha256()
    with open(dest_file, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    checksum = sha256_hash.hexdigest()

    logger.info("✓ 下载完成")
    logger.info(f"  文件: {dest_file}")
    logger.info(f"  大小: {_format_file_size(file_size)}")
    logger.info(f"  SHA256: {checksum}")
    logger.info("")
    logger.info(f"💡 提示: 使用 'bash {dest_file} -b -f' 进行安装")

    return 0


def _format_file_size(size_bytes: int) -> str:
    """格式化文件大小为人类可读格式

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def cmd_config(args: argparse.Namespace) -> int:
    """执行 config 命令

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    config_action = getattr(args, "config_action", None)

    if config_action is None:
        # mk config 没有子命令，显示帮助
        parser = create_parser()
        parser.parse_args(["config", "--help"])
        return 0

    if config_action == "mirror":
        return _cmd_config_mirror(args)

    return 0


def _cmd_config_mirror(args: argparse.Namespace) -> int:
    """处理 mk config mirror [action]

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    from mono_kickstart.config import ConfigManager
    from mono_kickstart.mirror_config import MirrorConfigurator
    from mono_kickstart.tool_detector import ToolDetector

    mirror_action = getattr(args, "mirror_action", None)

    # 加载配置
    config_manager = ConfigManager()
    try:
        config = config_manager.load_with_priority(
            cli_config=None,
            project_config=Path(".kickstartrc"),
            user_config=Path.home() / ".kickstartrc",
        )
    except Exception:
        config = config_manager.load_from_defaults()

    configurator = MirrorConfigurator(config.registry)
    detector = ToolDetector()

    try:
        if mirror_action is None:
            # mk config mirror -- 配置所有已安装工具的镜像源
            return _config_mirror_all(configurator, detector)
        elif mirror_action == "show":
            return _config_mirror_show(configurator, detector)
        elif mirror_action == "reset":
            tool = getattr(args, "tool", None)
            return _config_mirror_reset(configurator, tool)
        elif mirror_action == "set":
            return _config_mirror_set(configurator, args.tool, getattr(args, "url", None))
    except KeyboardInterrupt:
        logger.error("\n❌ 用户中断操作")
        return 130
    except Exception as e:
        logger.error(f"❌ 配置过程中发生错误: {e}")
        return 1

    return 0


def _config_mirror_all(configurator, detector) -> int:
    """为所有已安装的工具配置镜像源"""
    logger.info("🔧 配置镜像源...")
    logger.info("")

    mirror_tools = detector.detect_mirror_tools()
    configured_count = 0

    tool_config_map = {
        "npm": ("npm", configurator.configure_npm_mirror),
        "bun": ("Bun", configurator.configure_bun_mirror),
        "pip": ("pip", configurator.configure_pip_mirror),
        "uv": ("uv", configurator.configure_uv_mirror),
        "conda": ("Conda", configurator.configure_conda_mirror),
    }

    for tool_key, (display_name, config_func) in tool_config_map.items():
        status = mirror_tools.get(tool_key)
        if status and status.installed:
            result = config_func()
            if result:
                logger.info(f"  ✓ {display_name} 镜像源配置成功")
                configured_count += 1
            else:
                logger.warning(f"  ✗ {display_name} 镜像源配置失败")
        else:
            logger.info(f"  ○ {display_name} 未安装，跳过")

    logger.info("")
    logger.info(f"✨ 共配置 {configured_count} 个工具的镜像源")
    return 0


def _config_mirror_show(configurator, detector) -> int:
    """显示当前镜像源配置"""
    logger.info("📋 当前镜像源配置:")
    logger.info("")

    status = configurator.show_mirror_status()
    mirror_tools = detector.detect_mirror_tools()

    for tool_name, info in status.items():
        tool_status = mirror_tools.get(tool_name)
        installed_marker = "✓" if (tool_status and tool_status.installed) else "✗"
        configured = info.get("configured", "未配置")
        default = info.get("default", "未知")

        logger.info(f"  {installed_marker} {tool_name}:")
        logger.info(f"      当前: {configured}")
        logger.info(f"      默认: {default}")

    return 0


def _config_mirror_reset(configurator, tool: Optional[str]) -> int:
    """重置镜像源为上游默认值"""
    reset_map = {
        "npm": ("npm", configurator.reset_npm_mirror),
        "bun": ("Bun", configurator.reset_bun_mirror),
        "pip": ("pip", configurator.reset_pip_mirror),
        "uv": ("uv", configurator.reset_uv_mirror),
        "conda": ("Conda", configurator.reset_conda_mirror),
    }

    if tool:
        display_name, reset_func = reset_map[tool]
        result = reset_func()
        if result:
            logger.info(f"✓ {display_name} 镜像源已重置为默认值")
        else:
            logger.error(f"✗ {display_name} 镜像源重置失败")
            return 1
    else:
        logger.info("🔧 重置所有镜像源为默认值...")
        logger.info("")
        for key, (display_name, reset_func) in reset_map.items():
            result = reset_func()
            if result:
                logger.info(f"  ✓ {display_name} 已重置")
            else:
                logger.warning(f"  ✗ {display_name} 重置失败")
        logger.info("")
        logger.info("✨ 镜像源重置完成")

    return 0


MIRROR_PRESETS = {
    "china": {
        "npm": "https://registry.npmmirror.com/",
        "bun": "https://registry.npmmirror.com/",
        "pip": "https://mirrors.sustech.edu.cn/pypi/web/simple",
        "uv": "https://mirrors.sustech.edu.cn/pypi/web/simple",
        "conda": "https://mirrors.sustech.edu.cn/anaconda",
    },
    "default": {
        "npm": "https://registry.npmjs.org/",
        "bun": "https://registry.npmjs.org/",
        "pip": "https://pypi.org/simple",
        "uv": "https://pypi.org/simple",
        "conda": "https://repo.anaconda.com",
    },
}


def _config_mirror_set(configurator, tool: str, url: Optional[str]) -> int:
    """设置镜像源

    支持两种模式：
    - 预设模式: mk config mirror set china / mk config mirror set default
    - 单工具模式: mk config mirror set <tool> <url>
    """
    # 预设模式
    if tool in MIRROR_PRESETS:
        if url is not None:
            logger.warning(f"⚠️  使用预设 '{tool}' 时无需指定 URL，忽略参数: {url}")
        return _apply_mirror_preset(configurator, tool)

    # 单工具模式 — 必须提供 URL
    if url is None:
        logger.error(f"❌ 设置 {tool} 镜像源时必须提供 URL")
        logger.error(f"用法: mk config mirror set {tool} <URL>")
        logger.error(f"提示: 使用 'mk config mirror set china' 可一键设置国内镜像")
        return 1

    # URL 基本验证
    if not url.startswith("http://") and not url.startswith("https://"):
        logger.error(f"❌ 无效的 URL: {url}")
        logger.error("URL 必须以 http:// 或 https:// 开头")
        return 1

    # 更新内存中的配置并调用对应方法
    if tool == "npm":
        configurator.registry_config.npm = url
        result = configurator.configure_npm_mirror()
    elif tool == "bun":
        configurator.registry_config.bun = url
        result = configurator.configure_bun_mirror()
    elif tool == "pip":
        configurator.registry_config.pypi = url
        result = configurator.configure_pip_mirror()
    elif tool == "uv":
        configurator.registry_config.pypi = url
        result = configurator.configure_uv_mirror()
    elif tool == "conda":
        configurator.registry_config.conda = url
        result = configurator.configure_conda_mirror()
    else:
        logger.error(f"❌ 不支持的工具: {tool}")
        return 1

    if result:
        logger.info(f"✓ {tool} 镜像源已设置为: {url}")
    else:
        logger.error(f"✗ {tool} 镜像源设置失败")
        return 1

    return 0


def _apply_mirror_preset(configurator, preset_name: str) -> int:
    """应用镜像源预设"""
    preset = MIRROR_PRESETS[preset_name]
    preset_label = "国内镜像" if preset_name == "china" else "上游默认"
    logger.info(f"🔧 应用{preset_label}预设...")
    logger.info("")

    tool_config_map = {
        "npm": ("npm", "npm", configurator.configure_npm_mirror),
        "bun": ("bun", "bun", configurator.configure_bun_mirror),
        "pip": ("pypi", "pip", configurator.configure_pip_mirror),
        "uv": ("pypi", "uv", configurator.configure_uv_mirror),
        "conda": ("conda", "conda", configurator.configure_conda_mirror),
    }

    failed = []
    for tool_name, url in preset.items():
        config_attr, display, configure_func = tool_config_map[tool_name]
        setattr(configurator.registry_config, config_attr, url)
        result = configure_func()
        if result:
            logger.info(f"  ✓ {display} → {url}")
        else:
            logger.warning(f"  ✗ {display} 设置失败")
            failed.append(display)

    logger.info("")
    if failed:
        logger.warning(f"⚠️  部分工具设置失败: {', '.join(failed)}")
        return 1
    logger.info(f"✨ {preset_label}预设已应用完成")
    return 0


def _dd_spec_kit(ai_backend: str, force: bool, dry_run: bool) -> tuple:
    """Spec-Kit 初始化处理

    Args:
        ai_backend: AI 后端名称 (claude/codex)
        force: 是否强制重新初始化
        dry_run: 是否模拟运行

    Returns:
        (success: bool, message: str) 元组
    """
    logger.info("📋 [Spec-Kit] 检查环境...")

    # 检查 specify 命令是否可用
    if not shutil.which("specify"):
        logger.error("❌ 错误: Spec-Kit (specify) 未安装")
        logger.info("💡 提示: 请先运行 'mk install spec-kit' 安装 Spec-Kit")
        return (False, "specify 未安装")

    # 执行 specify check
    result = subprocess.run(
        "specify check",
        shell=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        logger.error("❌ 错误: Spec-Kit 环境检查失败")
        if result.stderr:
            logger.error(f"  {result.stderr.strip()}")
        logger.info("💡 提示: 请检查 AI 编程代理是否已安装（如 Claude Code 或 Codex）")
        return (False, "环境检查失败")

    logger.info("✓ Spec-Kit 环境检查通过")
    logger.info("")

    # 构造 specify init 命令
    init_cmd = f"specify init . --ai {ai_backend}"
    if force:
        init_cmd += " --force"

    logger.info(f"🚀 [Spec-Kit] 初始化项目（AI 后端: {ai_backend}）...")

    if dry_run:
        logger.info(f"  [模拟运行] 将执行: {init_cmd}")
        return (True, f"[模拟运行] 将使用 {ai_backend} 后端初始化")

    # 执行 specify init
    result = subprocess.run(
        init_cmd,
        shell=True,
        timeout=300,
    )
    if result.returncode != 0:
        logger.error("❌ 错误: Spec-Kit 初始化失败")
        return (False, "初始化失败")

    logger.info("✓ Spec-Kit 初始化成功")
    return (True, f"使用 {ai_backend} 后端初始化成功")


def _dd_bmad_method(dry_run: bool) -> tuple:
    """BMad Method 安装处理

    Args:
        dry_run: 是否模拟运行

    Returns:
        (success: bool, message: str) 元组
    """
    logger.info("📋 [BMad Method] 检查环境...")

    # 确定安装方式：优先 bunx，否则 npx
    if shutil.which("bun"):
        method = "bunx"
    elif shutil.which("npx"):
        method = "npx"
    else:
        logger.error("❌ 错误: 未找到 npx 或 bunx，无法安装 BMad Method")
        logger.info("💡 提示: 请先运行 'mk install bun' 或 'mk install node' 安装")
        return (False, "npx/bunx 未安装")

    logger.info(f"✓ 将使用 {method} 安装 BMad Method")
    logger.info("")

    install_cmd = f"{method} bmad-method install"

    logger.info("🚀 [BMad Method] 安装到当前项目...")

    if dry_run:
        logger.info(f"  [模拟运行] 将执行: {install_cmd}")
        return (True, f"[模拟运行] 将使用 {method} 安装")

    # 执行交互式安装（继承 stdin/stdout）
    result = subprocess.run(
        install_cmd,
        shell=True,
        timeout=600,
    )
    if result.returncode != 0:
        logger.error("❌ 错误: BMad Method 安装失败")
        return (False, "安装失败")

    logger.info("✓ BMad Method 安装成功")
    return (True, f"使用 {method} 安装成功")


def cmd_dd(args: argparse.Namespace) -> int:
    """执行 dd (driven development) 命令

    为当前项目配置驱动开发工具（Spec-Kit、BMad Method）。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    # 验证: 至少需要一个工具标志
    if not args.spec_kit and not args.bmad_method:
        logger.error("❌ 错误: 请至少指定一个工具标志（--spec-kit 或 --bmad-method）")
        logger.info("💡 提示: 使用 mk dd --help 查看可用选项")
        return 1

    # 验证: --claude/--codex 需要 --spec-kit
    if (args.claude or args.codex) and not args.spec_kit:
        logger.error("❌ 错误: --claude/--codex 需要与 --spec-kit 一起使用")
        logger.info("💡 提示: 使用 mk dd --spec-kit --claude 初始化 Spec-Kit")
        return 1

    # 确定 AI 后端
    ai_backend = "codex" if args.codex else "claude"

    logger.info("🔧 Mono-Kickstart - 配置驱动开发工具")
    logger.info("")

    if args.dry_run:
        logger.info("🔍 [模拟运行模式]")
        logger.info("")

    results = {}

    try:
        # Spec-Kit 初始化
        if args.spec_kit:
            success, msg = _dd_spec_kit(ai_backend, args.force, args.dry_run)
            results["Spec-Kit"] = (success, msg)
            logger.info("")

        # BMad Method 安装
        if args.bmad_method:
            success, msg = _dd_bmad_method(args.dry_run)
            results["BMad Method"] = (success, msg)
            logger.info("")

        # 打印摘要
        logger.info("=" * 60)
        for tool_name, (success, msg) in results.items():
            symbol = "✓" if success else "✗"
            logger.info(f"{symbol} {tool_name}: {msg}")
        logger.info("=" * 60)

        # 判断退出码
        failed = [k for k, (s, _) in results.items() if not s]
        if len(failed) == len(results):
            logger.error("❌ 所有工具配置都失败了")
            return 1
        elif failed:
            logger.warning(f"⚠️  部分工具配置失败: {', '.join(failed)}")
            return 0

        if args.dry_run:
            logger.info("✨ 模拟运行完成，未实际执行任何操作。")
        else:
            logger.info("✨ 驱动开发工具配置完成！")
        return 0

    except KeyboardInterrupt:
        logger.error("\n❌ 用户中断操作")
        return 130
    except subprocess.TimeoutExpired:
        logger.error("❌ 错误: 命令执行超时")
        return 1
    except Exception as e:
        logger.error(f"❌ 配置过程中发生错误: {e}")
        return 1


def cmd_claude(args: argparse.Namespace) -> int:
    """执行 claude 命令

    为当前项目配置 Claude Code 设置（MCP 服务器等）。

    Args:
        args: 解析后的命令行参数

    Returns:
        退出码（0 表示成功）
    """
    # 验证: 至少需要一个操作
    if (
        not args.mcp
        and not args.allow
        and not args.mode
        and not args.on
        and not args.off
        and not args.skills
        and not args.plugin
    ):
        logger.error(
            "❌ 错误: 请指定要配置的内容"
            "（如 --mcp chrome、--allow all、--mode plan、--on team、--off suggestion/team、"
            "--skills uipro 或 --plugin omc）"
        )
        logger.info("💡 提示: 使用 mk claude --help 查看可用选项")
        return 1

    logger.info("🔧 Mono-Kickstart - 配置 Claude Code 项目设置")
    logger.info("")

    if args.dry_run:
        logger.info("🔍 [模拟运行模式]")
        logger.info("")

    try:
        if args.mcp:
            result = _claude_add_mcp(args.mcp, args.dry_run)
            if result != 0:
                return result

        if args.allow:
            result = _claude_set_allow(args.dry_run)
            if result != 0:
                return result

        if args.mode:
            result = _claude_set_mode(args.mode, args.dry_run)
            if result != 0:
                return result

        if args.on:
            result = _claude_set_on(args.on, args.dry_run)
            if result != 0:
                return result

        if args.off:
            result = _claude_set_off(args.off, args.dry_run)
            if result != 0:
                return result

        if args.skills:
            result = _claude_add_skill(args.skills, args.dry_run)
            if result != 0:
                return result

        if args.plugin:
            result = _claude_add_plugin(args.plugin, args.dry_run)
            if result != 0:
                return result

    except KeyboardInterrupt:
        logger.error("\n❌ 用户中断操作")
        return 130
    except Exception as e:
        logger.error(f"❌ 配置过程中发生错误: {e}")
        return 1

    return 0


def _claude_add_mcp(server_key: str, dry_run: bool) -> int:
    """添加 MCP 服务器配置到当前项目

    将 MCP 服务器配置写入 .claude/settings.local.json。

    Args:
        server_key: MCP 服务器标识（如 chrome）
        dry_run: 是否模拟运行

    Returns:
        退出码（0 表示成功）
    """
    server_info = MCP_SERVER_CONFIGS[server_key]
    server_name = server_info["name"]
    display_name = server_info["display_name"]
    mcp_config = server_info["config"]

    logger.info(f"📋 [MCP] 添加 {display_name} 服务器...")

    # 目标文件
    claude_dir = Path(".claude")
    settings_file = claude_dir / "settings.local.json"

    # 读取现有配置
    existing_config = {}
    if settings_file.exists():
        try:
            existing_config = json.loads(settings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"⚠️  读取现有配置失败，将创建新配置: {e}")

    # 合并 MCP 配置（已存在则覆盖）
    if "mcpServers" not in existing_config:
        existing_config["mcpServers"] = {}
    existing_config["mcpServers"][server_name] = mcp_config

    if dry_run:
        logger.info(f"  [模拟运行] 将写入 {settings_file}:")
        logger.info(f"  {json.dumps({'mcpServers': {server_name: mcp_config}}, indent=2)}")
        logger.info("")
        logger.info("============================================================")
        logger.info(f"○ {display_name}: [模拟运行] 将添加 MCP 服务器配置")
        logger.info("============================================================")
        logger.info("✨ 模拟运行完成，未实际写入任何配置。")
        return 0

    # 创建 .claude 目录
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 写入配置
    settings_file.write_text(
        json.dumps(existing_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    logger.info(f"✓ {display_name} MCP 服务器配置已写入 {settings_file}")

    # 尝试运行 claude mcp add 命令
    claude_mcp_cmd = server_info["claude_mcp_add_cmd"]
    if shutil.which("claude"):
        logger.info("")
        logger.info(f"📋 [MCP] 执行 claude mcp add 注册命令...")
        result = subprocess.run(
            claude_mcp_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info(f"✓ 已通过 claude CLI 注册 {display_name} MCP 服务器")
        else:
            logger.warning(f"⚠️  claude mcp add 执行失败（配置文件已写入，可忽略）")
    else:
        logger.info(f"💡 提示: 也可手动执行 '{claude_mcp_cmd}' 注册 MCP 服务器")

    logger.info("")
    logger.info("============================================================")
    logger.info(f"✓ {display_name}: MCP 服务器配置完成")
    logger.info("============================================================")
    logger.info("✨ Claude Code 项目设置配置完成！")
    return 0


def _claude_set_allow(dry_run: bool) -> int:
    """配置权限允许所有命令

    将 permissions.allow 设置为完整工具列表，写入 .claude/settings.local.json。

    Args:
        dry_run: 是否模拟运行

    Returns:
        退出码（0 表示成功）
    """
    logger.info("📋 [权限] 配置允许所有命令...")

    # 目标文件
    claude_dir = Path(".claude")
    settings_file = claude_dir / "settings.local.json"

    # 读取现有配置
    existing_config = {}
    if settings_file.exists():
        try:
            existing_config = json.loads(settings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"⚠️  读取现有配置失败，将创建新配置: {e}")

    # 合并权限配置（覆盖 permissions.allow）
    if "permissions" not in existing_config:
        existing_config["permissions"] = {}
    existing_config["permissions"]["allow"] = ALLOW_ALL_PERMISSIONS

    if dry_run:
        logger.info(f"  [模拟运行] 将写入 {settings_file}:")
        logger.info(f"  {json.dumps({'permissions': {'allow': ALLOW_ALL_PERMISSIONS}}, indent=2)}")
        logger.info("")
        logger.info("============================================================")
        logger.info("○ [模拟运行] 权限: 将配置允许所有命令")
        logger.info("============================================================")
        logger.info("✨ 模拟运行完成，未实际写入任何配置。")
        return 0

    # 创建 .claude 目录
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 写入配置
    settings_file.write_text(
        json.dumps(existing_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    logger.info(f"✓ 权限配置已写入 {settings_file}")
    logger.info(f"  permissions.allow = {json.dumps(ALLOW_ALL_PERMISSIONS)}")
    logger.info("")
    logger.info("============================================================")
    logger.info("✓ 权限: 已配置允许所有命令")
    logger.info("============================================================")
    logger.info("✨ Claude Code 权限配置完成！")
    return 0


def _claude_set_mode(mode: str, dry_run: bool) -> int:
    """配置权限模式

    设置 permissionMode，写入 .claude/settings.local.json。

    Args:
        mode: 权限模式（如 plan）
        dry_run: 是否模拟运行

    Returns:
        退出码（0 表示成功）
    """
    logger.info(f"📋 [模式] 配置 {mode} 模式...")

    # 目标文件
    claude_dir = Path(".claude")
    settings_file = claude_dir / "settings.local.json"

    # 读取现有配置
    existing_config = {}
    if settings_file.exists():
        try:
            existing_config = json.loads(settings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"⚠️  读取现有配置失败，将创建新配置: {e}")

    existing_config["permissionMode"] = mode

    if dry_run:
        logger.info(f"  [模拟运行] 将写入 {settings_file}:")
        logger.info(f"  {json.dumps({'permissionMode': mode}, indent=2)}")
        logger.info("")
        logger.info("============================================================")
        logger.info(f"○ [模拟运行] 模式: 将配置 permissionMode = {mode}")
        logger.info("============================================================")
        logger.info("✨ 模拟运行完成，未实际写入任何配置。")
        return 0

    # 创建 .claude 目录
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 写入配置
    settings_file.write_text(
        json.dumps(existing_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    logger.info(f"✓ 模式配置已写入 {settings_file}")
    logger.info(f'  permissionMode = "{mode}"')
    logger.info("")
    logger.info("============================================================")
    logger.info(f"✓ 模式: 已配置 permissionMode = {mode}")
    logger.info("============================================================")
    logger.info("✨ Claude Code 模式配置完成！")
    return 0


def _claude_set_off(feature: str, dry_run: bool) -> int:
    """关闭指定功能

    根据 feature 类型，设置配置项为 false 或移除环境变量，写入 .claude/settings.local.json。

    Args:
        feature: 功能标识（如 suggestion、team）
        dry_run: 是否模拟运行

    Returns:
        退出码（0 表示成功）
    """
    # 功能映射
    feature_map = {
        "suggestion": {
            "type": "boolean",
            "key": "promptSuggestionEnabled",
            "display_name": "提示建议",
        },
        "team": {
            "type": "env_var",
            "key": "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS",
            "display_name": "实验性团队",
            "extra_settings": ["teammateMode"],
        },
    }

    info = feature_map[feature]
    feature_type = info["type"]
    config_key = info["key"]
    display_name = info["display_name"]

    logger.info(f"📋 [功能] 关闭{display_name}...")

    # 目标文件
    claude_dir = Path(".claude")
    settings_file = claude_dir / "settings.local.json"

    # 读取现有配置
    existing_config = {}
    if settings_file.exists():
        try:
            existing_config = json.loads(settings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"⚠️  读取现有配置失败，将创建新配置: {e}")

    if feature_type == "boolean":
        existing_config[config_key] = False
    elif feature_type == "env_var":
        if "env" in existing_config and config_key in existing_config["env"]:
            del existing_config["env"][config_key]
            if not existing_config["env"]:
                del existing_config["env"]
        # 移除额外的顶层配置项
        extra_keys = info.get("extra_settings", [])
        for k in extra_keys:
            existing_config.pop(k, None)

    if dry_run:
        logger.info(f"  [模拟运行] 将写入 {settings_file}:")
        if feature_type == "boolean":
            logger.info(f"  {json.dumps({config_key: False}, indent=2)}")
        elif feature_type == "env_var":
            logger.info(f"  移除环境变量: {config_key}")
            for k in info.get("extra_settings", []):
                logger.info(f"  移除配置项: {k}")
        logger.info("")
        logger.info("============================================================")
        if feature_type == "boolean":
            logger.info(f"○ [模拟运行] 功能: 将关闭{display_name} ({config_key} = false)")
        elif feature_type == "env_var":
            logger.info(f"○ [模拟运行] 功能: 将关闭{display_name} (移除环境变量 {config_key})")
        logger.info("============================================================")
        logger.info("✨ 模拟运行完成，未实际写入任何配置。")
        return 0

    # 创建 .claude 目录
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 写入配置
    settings_file.write_text(
        json.dumps(existing_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    logger.info(f"✓ 功能配置已写入 {settings_file}")
    if feature_type == "boolean":
        logger.info(f"  {config_key} = false")
    elif feature_type == "env_var":
        logger.info(f"  已移除环境变量: {config_key}")
        for k in info.get("extra_settings", []):
            logger.info(f"  已移除配置项: {k}")
    logger.info("")
    logger.info("============================================================")
    if feature_type == "boolean":
        logger.info(f"✓ 功能: 已关闭{display_name} ({config_key} = false)")
    elif feature_type == "env_var":
        logger.info(f"✓ 功能: 已关闭{display_name} (已移除环境变量 {config_key})")
    logger.info("============================================================")
    logger.info("✨ Claude Code 功能配置完成！")
    return 0


def _claude_set_on(feature: str, dry_run: bool) -> int:
    """启用指定功能

    根据 feature 设置对应的环境变量，写入 .claude/settings.local.json。

    Args:
        feature: 功能标识（如 team）
        dry_run: 是否模拟运行

    Returns:
        退出码（0 表示成功）
    """
    # 功能映射
    feature_map = {
        "team": {
            "key": "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS",
            "value": "1",
            "display_name": "实验性团队",
            "extra_settings": {"teammateMode": "auto"},
        },
    }

    info = feature_map[feature]
    config_key = info["key"]
    config_value = info["value"]
    display_name = info["display_name"]

    logger.info(f"📋 [功能] 启用{display_name}...")

    # 目标文件
    claude_dir = Path(".claude")
    settings_file = claude_dir / "settings.local.json"

    # 读取现有配置
    existing_config = {}
    if settings_file.exists():
        try:
            existing_config = json.loads(settings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"⚠️  读取现有配置失败，将创建新配置: {e}")

    # 确保 env 对象存在并设置环境变量
    if "env" not in existing_config:
        existing_config["env"] = {}
    existing_config["env"][config_key] = config_value

    # 设置额外的顶层配置项
    extra_settings = info.get("extra_settings", {})
    for k, v in extra_settings.items():
        existing_config[k] = v

    if dry_run:
        logger.info(f"  [模拟运行] 将写入 {settings_file}:")
        preview = {"env": {config_key: config_value}, **extra_settings}
        logger.info(f"  {json.dumps(preview, indent=2)}")
        logger.info("")
        logger.info("============================================================")
        logger.info(
            f"○ [模拟运行] 功能: 将启用{display_name} "
            f"(设置环境变量 {config_key} = {config_value})"
        )
        for k, v in extra_settings.items():
            logger.info(f"○ [模拟运行] 功能: 将设置 {k} = {v}")
        logger.info("============================================================")
        logger.info("✨ 模拟运行完成，未实际写入任何配置。")
        return 0

    # 创建 .claude 目录
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 写入配置
    settings_file.write_text(
        json.dumps(existing_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    logger.info(f"✓ 功能配置已写入 {settings_file}")
    logger.info(f"  已设置环境变量: {config_key} = {config_value}")
    for k, v in extra_settings.items():
        logger.info(f"  已设置: {k} = {v}")
    logger.info("")
    logger.info("============================================================")
    logger.info(f"✓ 功能: 已启用{display_name} (环境变量 {config_key} = {config_value})")
    for k, v in extra_settings.items():
        logger.info(f"✓ 功能: 已设置 {k} = {v}")
    logger.info("============================================================")
    logger.info("✨ Claude Code 功能配置完成！")
    return 0


def _claude_add_skill(skill_key: str, dry_run: bool) -> int:
    """安装 Claude Code 技能包

    通过调用相应的 CLI 工具初始化技能包到当前项目。

    Args:
        skill_key: 技能包标识（如 uipro）
        dry_run: 是否模拟运行

    Returns:
        退出码（0 表示成功）
    """
    skill_info = SKILL_CONFIGS[skill_key]
    display_name = skill_info["display_name"]
    cli_command = skill_info["cli_command"]
    init_command = skill_info["init_command"]
    install_hint = skill_info["install_hint"]
    skill_dir = skill_info["skill_dir"]

    logger.info(f"📋 [技能] 安装 {display_name} 技能包...")

    # 检查 CLI 工具是否已安装
    if not shutil.which(cli_command):
        logger.error(f"❌ {display_name} CLI 未安装")
        logger.info(f"💡 提示: 请先运行 '{install_hint}' 安装 {display_name} CLI")
        logger.info("   或使用 'mk install uipro' 安装")
        return 1

    # 检查技能包是否已存在
    skill_path = Path(skill_dir)
    if skill_path.exists():
        logger.info(f"⚠️  {display_name} 技能包已存在于 {skill_dir}，将重新初始化")

    if dry_run:
        logger.info(f"  [模拟运行] 将执行: {init_command}")
        logger.info(f"  [模拟运行] 将创建技能包目录: {skill_dir}")
        logger.info("")
        logger.info("============================================================")
        logger.info(f"○ {display_name}: [模拟运行] 将安装技能包")
        logger.info("============================================================")
        logger.info("✨ 模拟运行完成，未实际执行任何操作。")
        return 0

    # 执行初始化命令
    try:
        result = subprocess.run(
            init_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            logger.error(f"❌ {display_name} 技能包安装失败")
            if result.stderr:
                logger.error(f"  错误信息: {result.stderr.strip()}")
            return 1

    except subprocess.TimeoutExpired:
        logger.error(f"❌ {display_name} 技能包安装超时")
        return 1
    except OSError as e:
        logger.error(f"❌ 执行 {init_command} 失败: {e}")
        return 1

    # 验证安装结果
    if skill_path.exists():
        logger.info(f"✓ {display_name} 技能包已安装到 {skill_dir}")
    else:
        logger.warning(f"⚠️  命令执行成功，但未找到预期的技能包目录 {skill_dir}")

    logger.info("")
    logger.info("============================================================")
    logger.info(f"✓ {display_name}: 技能包安装完成")
    logger.info("============================================================")
    logger.info("✨ Claude Code 技能包配置完成！")
    return 0


def _claude_add_plugin(plugin_key: str, dry_run: bool) -> int:
    if plugin_key != "omc":
        logger.error(f"❌ 不支持的插件: {plugin_key}")
        return 1

    logger.info("📋 [插件] 安装 Oh My Claude Code (OMC)...")

    if not shutil.which("claude"):
        logger.error("❌ 未检测到 claude 命令")
        logger.info("💡 提示: 请先运行 'mk install claude-code' 安装 Claude Code CLI")
        return 1

    marketplace_cmd = (
        "claude /plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode"
    )
    install_cmd = "claude /plugin install oh-my-claudecode"
    config_url = (
        "https://raw.githubusercontent.com/Yeachan-Heo/oh-my-claudecode/main/docs/CLAUDE.md"
    )
    claude_md_file = Path(".claude") / "CLAUDE.md"
    download_cmd = f"curl -fsSL {config_url} -o {claude_md_file}"

    if dry_run:
        logger.info(f"  [模拟运行] 将执行: {marketplace_cmd}")
        logger.info(f"  [模拟运行] 将执行: {install_cmd}")
        logger.info(f"  [模拟运行] 将执行: {download_cmd}")
        logger.info(f"  [模拟运行] 将写入: {claude_md_file}")
        logger.info("")
        logger.info("============================================================")
        logger.info("○ OMC: [模拟运行] 将安装并配置插件")
        logger.info("============================================================")
        logger.info("✨ 模拟运行完成，未实际执行任何操作。")
        return 0

    result = subprocess.run(marketplace_cmd, shell=True, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error("❌ 添加 OMC 插件源失败")
        if result.stderr:
            logger.error(f"  错误信息: {result.stderr.strip()}")
        return 1

    result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error("❌ 安装 OMC 插件失败")
        if result.stderr:
            logger.error(f"  错误信息: {result.stderr.strip()}")
        return 1

    claude_md_file.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(download_cmd, shell=True, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error("❌ 下载 OMC 项目配置模板失败")
        if result.stderr:
            logger.error(f"  错误信息: {result.stderr.strip()}")
        return 1

    logger.info(f"✓ OMC 配置已写入 {claude_md_file}")
    logger.info("")
    logger.info("============================================================")
    logger.info("✓ OMC: 插件安装与项目配置完成")
    logger.info("============================================================")
    logger.info("✨ Claude Code 插件配置完成！")
    return 0


def cmd_opencode(args: argparse.Namespace) -> int:
    if not args.plugin:
        logger.error("❌ 错误: 请指定要安装的插件（如 --plugin omo）")
        logger.info("💡 提示: 使用 mk opencode --help 查看可用选项")
        return 1

    if args.plugin == "omo":
        return _opencode_install_omo(args.dry_run)

    return 0


def _opencode_install_omo(dry_run: bool) -> int:
    logger.info("🔧 Mono-Kickstart - 配置 Oh My OpenCode")
    logger.info("")

    if not shutil.which("opencode"):
        logger.error("❌ 错误: 未检测到 opencode 命令")
        logger.info("💡 提示: 请先运行 'mk install opencode' 安装 OpenCode CLI")
        return 1

    installer_cmd = None
    if shutil.which("bunx"):
        installer_cmd = (
            "bunx oh-my-opencode install --no-tui --claude=no --openai=no --gemini=no "
            "--copilot=no --opencode-zen=no --zai-coding-plan=no"
        )
    elif shutil.which("npx"):
        installer_cmd = (
            "npx oh-my-opencode install --no-tui --claude=no --openai=no --gemini=no "
            "--copilot=no --opencode-zen=no --zai-coding-plan=no"
        )

    if installer_cmd is None:
        logger.error("❌ 错误: 未找到 bunx 或 npx，无法安装 oh-my-opencode")
        logger.info("💡 提示: 请先安装 Bun 或 Node.js")
        return 1

    opencode_config_file = Path.home() / ".config" / "opencode" / "opencode.json"
    omo_config_file = Path(".opencode") / "oh-my-opencode.json"
    schema_url = (
        "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/master/"
        "assets/oh-my-opencode.schema.json"
    )

    opencode_config = {}
    if opencode_config_file.exists():
        try:
            opencode_config = json.loads(opencode_config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            opencode_config = {}

    plugins = opencode_config.get("plugin")
    if not isinstance(plugins, list):
        plugins = []
    if "oh-my-opencode" not in plugins:
        plugins.append("oh-my-opencode")
    opencode_config["plugin"] = plugins

    omo_config = {}
    if omo_config_file.exists():
        try:
            omo_config = json.loads(omo_config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            omo_config = {}
    omo_config.setdefault("$schema", schema_url)

    if dry_run:
        logger.info("🔍 [模拟运行模式]")
        logger.info("")
        logger.info(f"  [模拟运行] 将执行: {installer_cmd}")
        logger.info(f"  [模拟运行] 将写入: {opencode_config_file}")
        logger.info(f"  [模拟运行] 将写入: {omo_config_file}")
        logger.info("")
        logger.info("✨ 模拟运行完成，未实际执行任何操作。")
        return 0

    logger.info(f"📦 执行安装命令: {installer_cmd}")
    install_result = subprocess.run(installer_cmd, shell=True)
    if install_result.returncode != 0:
        logger.error("❌ oh-my-opencode 安装命令执行失败")
        return 1

    opencode_config_file.parent.mkdir(parents=True, exist_ok=True)
    opencode_config_file.write_text(
        json.dumps(opencode_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    omo_config_file.parent.mkdir(parents=True, exist_ok=True)
    omo_config_file.write_text(
        json.dumps(omo_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    logger.info(f"✓ 已更新 {opencode_config_file}")
    logger.info(f"✓ 已更新 {omo_config_file}")
    logger.info("✨ Oh My OpenCode 配置完成！")
    return 0


def main() -> int:
    """主入口函数

    Returns:
        退出码（0 表示成功，非 0 表示失败）
    """
    parser = create_parser()
    args = parser.parse_args()

    # 如果没有指定子命令，显示帮助信息
    if not args.command:
        parser.print_help()
        return 0

    # 根据子命令调用相应的处理函数
    if args.command == "init":
        return cmd_init(args)
    elif args.command == "upgrade":
        return cmd_upgrade(args)
    elif args.command == "install":
        return cmd_install(args)
    elif args.command == "set-default":
        return cmd_set_default(args)
    elif args.command == "setup-shell":
        return cmd_setup_shell(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "show":
        return cmd_show(args)
    elif args.command == "download":
        return cmd_download(args)
    elif args.command == "config":
        return cmd_config(args)
    elif args.command == "dd":
        return cmd_dd(args)
    elif args.command == "claude":
        return cmd_claude(args)
    elif args.command == "opencode":
        return cmd_opencode(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
