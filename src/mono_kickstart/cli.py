"""
CLI 入口模块

定义命令行接口和子命令（使用 argparse 标准库）。
"""

import argparse
import logging
import os
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
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
