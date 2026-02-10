"""
CLI 入口模块

定义命令行接口和子命令（使用 argparse 标准库）。
"""

import argparse
import hashlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from mono_kickstart import __version__


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# 可用工具列表（用于补全）
AVAILABLE_TOOLS = [
    "nvm",
    "node",
    "conda",
    "bun",
    "uv",
    "claude-code",
    "codex",
    "npx",
    "spec-kit",
    "bmad-method",
]

# 可下载的工具列表（仅支持有独立安装包的工具）
DOWNLOADABLE_TOOLS = [
    "conda",
]


class ChineseHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """中文化的帮助信息格式器"""
    
    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = '用法: '
        return super()._format_usage(usage, actions, groups, prefix)


def create_parser() -> argparse.ArgumentParser:
    """创建主解析器和子命令解析器
    
    Returns:
        配置好的 ArgumentParser 对象
    """
    # 主解析器
    parser = argparse.ArgumentParser(
        prog='mk',
        description='Mono-Kickstart - Monorepo 项目模板脚手架 CLI 工具\n\n'
                    '通过一条命令快速初始化标准化的 Monorepo 工程，\n'
                    '自动完成开发环境搭建与工具链安装。',
        formatter_class=ChineseHelpFormatter,
        add_help=True,
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'Mono-Kickstart version {__version__}',
        help='显示版本号'
    )
    
    # 子命令解析器
    subparsers = parser.add_subparsers(
        title='可用命令',
        dest='command',
        help='子命令帮助信息'
    )
    
    # init 子命令
    init_parser = subparsers.add_parser(
        'init',
        help='初始化 Monorepo 项目和开发环境',
        description='初始化 Monorepo 项目和开发环境',
        formatter_class=ChineseHelpFormatter,
    )
    init_parser.add_argument(
        '--config',
        type=str,
        metavar='PATH',
        help='配置文件路径'
    )
    init_parser.add_argument(
        '--save-config',
        action='store_true',
        help='保存配置到 .kickstartrc'
    )
    init_parser.add_argument(
        '--interactive',
        action='store_true',
        help='交互式配置'
    )
    init_parser.add_argument(
        '--force',
        action='store_true',
        help='强制覆盖已有配置'
    )
    init_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，不实际安装'
    )
    
    # upgrade 子命令
    upgrade_parser = subparsers.add_parser(
        'upgrade',
        help='升级已安装的开发工具',
        description='升级已安装的开发工具',
        formatter_class=ChineseHelpFormatter,
    )
    upgrade_parser.add_argument(
        'tool',
        nargs='?',
        choices=AVAILABLE_TOOLS,
        metavar='TOOL',
        help=f'要升级的工具名称 (可选值: {", ".join(AVAILABLE_TOOLS)})'
    )
    upgrade_parser.add_argument(
        '--all',
        action='store_true',
        help='升级所有工具'
    )
    upgrade_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，不实际升级'
    )
    
    # install 子命令
    install_parser = subparsers.add_parser(
        'install',
        help='安装开发工具',
        description='安装开发工具',
        formatter_class=ChineseHelpFormatter,
    )
    install_parser.add_argument(
        'tool',
        nargs='?',
        choices=AVAILABLE_TOOLS,
        metavar='TOOL',
        help=f'要安装的工具名称 (可选值: {", ".join(AVAILABLE_TOOLS)})'
    )
    install_parser.add_argument(
        '--all',
        action='store_true',
        help='安装所有工具'
    )
    install_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，不实际安装'
    )
    
    # set-default 子命令
    set_default_parser = subparsers.add_parser(
        'set-default',
        help='设置工具的默认版本（如通过 nvm 设置 Node.js 默认版本）',
        description='设置工具的默认版本（如通过 nvm 设置 Node.js 默认版本）',
        formatter_class=ChineseHelpFormatter,
    )
    set_default_parser.add_argument(
        'tool',
        choices=['node'],
        metavar='TOOL',
        help='要设置默认版本的工具名称 (可选值: node)'
    )
    set_default_parser.add_argument(
        'version',
        nargs='?',
        default=None,
        metavar='VERSION',
        help='要设置的版本号（如 20.2.0），不指定则使用默认版本 20.2.0'
    )

    # setup-shell 子命令
    setup_shell_parser = subparsers.add_parser(
        'setup-shell',
        help='配置 shell（PATH 和 Tab 补全）',
        description='配置 shell（PATH 和 Tab 补全）',
        formatter_class=ChineseHelpFormatter,
    )

    # status 子命令
    status_parser = subparsers.add_parser(
        'status',
        help='查看已安装工具的状态和版本',
        description='查看已安装工具的状态和版本',
        formatter_class=ChineseHelpFormatter,
    )

    # download 子命令
    download_parser = subparsers.add_parser(
        'download',
        help='下载工具安装包到本地（不安装）',
        description='下载工具安装包到本地磁盘（不执行安装）\n\n'
                    '适用于离线安装、气隔环境预下载、团队共享安装包等场景。',
        formatter_class=ChineseHelpFormatter,
    )
    download_parser.add_argument(
        'tool',
        choices=DOWNLOADABLE_TOOLS,
        metavar='TOOL',
        help=f'要下载的工具名称 (可选值: {", ".join(DOWNLOADABLE_TOOLS)})'
    )
    download_parser.add_argument(
        '-o', '--output',
        type=str,
        default='.',
        metavar='DIR',
        help='下载文件保存目录 (默认: 当前目录)'
    )
    download_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='模拟运行，不实际下载'
    )

    # config 子命令
    config_parser = subparsers.add_parser(
        'config',
        help='管理配置（镜像源等）',
        description='管理配置（镜像源等）',
        formatter_class=ChineseHelpFormatter,
    )

    config_subparsers = config_parser.add_subparsers(
        title='配置操作',
        dest='config_action',
        help='配置子命令帮助信息'
    )

    # config mirror 子命令
    mirror_parser = config_subparsers.add_parser(
        'mirror',
        help='配置镜像源',
        description='配置开发工具的镜像源（npm、bun、pip、uv、conda）',
        formatter_class=ChineseHelpFormatter,
    )

    mirror_subparsers = mirror_parser.add_subparsers(
        title='镜像操作',
        dest='mirror_action',
        help='镜像操作子命令'
    )

    # config mirror show
    mirror_subparsers.add_parser(
        'show',
        help='显示当前镜像源配置',
        formatter_class=ChineseHelpFormatter,
    )

    # config mirror reset
    mirror_reset_parser = mirror_subparsers.add_parser(
        'reset',
        help='重置镜像源为上游默认值',
        formatter_class=ChineseHelpFormatter,
    )
    mirror_reset_parser.add_argument(
        '--tool',
        choices=['npm', 'bun', 'pip', 'uv', 'conda'],
        metavar='TOOL',
        help='仅重置指定工具的镜像源（可选值: npm, bun, pip, uv, conda）'
    )

    # config mirror set
    mirror_set_parser = mirror_subparsers.add_parser(
        'set',
        help='设置镜像源（支持预设: china/default，或指定工具和 URL）',
        formatter_class=ChineseHelpFormatter,
    )
    mirror_set_parser.add_argument(
        'tool',
        choices=['npm', 'bun', 'pip', 'uv', 'conda', 'china', 'default'],
        metavar='TOOL',
        help='工具名称 (npm, bun, pip, uv, conda) 或预设名 (china: 国内镜像, default: 上游默认)'
    )
    mirror_set_parser.add_argument(
        'url',
        nargs='?',
        default=None,
        metavar='URL',
        help='镜像源 URL（使用预设时无需指定）'
    )

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
            logger.error(f"❌ 错误: 不支持的平台 ({platform_info.os.value}/{platform_info.arch.value})")
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
                    user_config=Path.home() / ".kickstartrc"
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
                    user_config=Path.home() / ".kickstartrc"
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
            config=config,
            platform_info=platform_info,
            dry_run=args.dry_run
        )
        
        # 5. 执行初始化流程
        if args.dry_run:
            logger.info("🔍 [模拟运行模式]")
            logger.info("")
        
        logger.info("🚀 开始初始化...")
        logger.info("")
        
        # 执行完整初始化流程
        reports = orchestrator.run_init(
            project_name=config.project.name,
            force=args.force
        )
        
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
            logger.error(f"❌ 错误: 不支持的平台 ({platform_info.os.value}/{platform_info.arch.value})")
            return 1
        
        platform_info = detector.detect_all()
        
        # 2. 加载配置
        config_manager = ConfigManager()
        try:
            config = config_manager.load_with_priority(
                cli_config=None,
                project_config=Path(".kickstartrc"),
                user_config=Path.home() / ".kickstartrc"
            )
        except Exception as e:
            logger.warning(f"⚠️  警告: 配置加载失败，使用默认配置: {e}")
            config = config_manager.load_from_defaults()
        
        # 3. 创建安装编排器
        orchestrator = InstallOrchestrator(
            config=config,
            platform_info=platform_info,
            dry_run=args.dry_run
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
            logger.error(f"❌ 错误: 不支持的平台 ({platform_info.os.value}/{platform_info.arch.value})")
            return 1
        
        platform_info = detector.detect_all()
        
        # 2. 加载配置
        config_manager = ConfigManager()
        try:
            config = config_manager.load_with_priority(
                cli_config=None,
                project_config=Path(".kickstartrc"),
                user_config=Path.home() / ".kickstartrc"
            )
        except Exception as e:
            logger.warning(f"⚠️  警告: 配置加载失败，使用默认配置: {e}")
            config = config_manager.load_from_defaults()
        
        # 3. 创建安装编排器
        orchestrator = InstallOrchestrator(
            config=config,
            platform_info=platform_info,
            dry_run=args.dry_run
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

    if args.tool != 'node':
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

        import subprocess

        # 1. 检查目标版本是否已安装，未安装则先安装
        check_cmd = f"bash -c 'source {nvm_sh} && nvm ls {version}'"
        result = subprocess.run(
            check_cmd, shell=True, capture_output=True, text=True, timeout=10
        )

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
        result = subprocess.run(
            alias_cmd, shell=True, capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            logger.error(f"❌ 设置默认版本失败")
            logger.error(result.stderr or "命令返回非零退出码")
            return 1

        # 3. 验证
        verify_cmd = f"bash -c 'source {nvm_sh} && nvm current'"
        result = subprocess.run(
            verify_cmd, shell=True, capture_output=True, text=True, timeout=10
        )

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
            logger.error(f"❌ 错误: 不支持的平台 ({platform_info.os.value}/{platform_info.arch.value})")
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
        if args.tool == 'conda':
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
            user_config=Path.home() / ".kickstartrc"
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
        timeout=300
    )

    if result.returncode != 0 or not dest_file.exists() or dest_file.stat().st_size == 0:
        logger.error("❌ 下载失败: 无法连接到镜像服务器")
        logger.error("提示: 请检查网络连接后重试，或使用 'mk config mirror set conda <URL>' 更换镜像源")
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
    config_action = getattr(args, 'config_action', None)

    if config_action is None:
        # mk config 没有子命令，显示帮助
        parser = create_parser()
        parser.parse_args(['config', '--help'])
        return 0

    if config_action == 'mirror':
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

    mirror_action = getattr(args, 'mirror_action', None)

    # 加载配置
    config_manager = ConfigManager()
    try:
        config = config_manager.load_with_priority(
            cli_config=None,
            project_config=Path(".kickstartrc"),
            user_config=Path.home() / ".kickstartrc"
        )
    except Exception:
        config = config_manager.load_from_defaults()

    configurator = MirrorConfigurator(config.registry)
    detector = ToolDetector()

    try:
        if mirror_action is None:
            # mk config mirror -- 配置所有已安装工具的镜像源
            return _config_mirror_all(configurator, detector)
        elif mirror_action == 'show':
            return _config_mirror_show(configurator, detector)
        elif mirror_action == 'reset':
            tool = getattr(args, 'tool', None)
            return _config_mirror_reset(configurator, tool)
        elif mirror_action == 'set':
            return _config_mirror_set(configurator, args.tool, getattr(args, 'url', None))
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
    if args.command == 'init':
        return cmd_init(args)
    elif args.command == 'upgrade':
        return cmd_upgrade(args)
    elif args.command == 'install':
        return cmd_install(args)
    elif args.command == 'set-default':
        return cmd_set_default(args)
    elif args.command == 'setup-shell':
        return cmd_setup_shell(args)
    elif args.command == 'status':
        return cmd_status(args)
    elif args.command == 'download':
        return cmd_download(args)
    elif args.command == 'config':
        return cmd_config(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
