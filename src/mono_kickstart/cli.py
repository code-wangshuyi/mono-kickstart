"""
CLI 入口模块

定义命令行接口和子命令。
"""

import os
from pathlib import Path
from typing import Optional

import click
import typer
import typer.core
import typer.rich_utils as ru

# 中文化帮助面板标题
ru.OPTIONS_PANEL_TITLE = "选项"
ru.COMMANDS_PANEL_TITLE = "命令"
ru.ARGUMENTS_PANEL_TITLE = "参数"
ru.DEFAULT_STRING = "[默认值: {}]"
ru.REQUIRED_LONG_STRING = "[必填]"


def _chinese_help_option(self, ctx):
    """返回中文帮助选项。"""
    help_options = self.get_help_option_names(ctx)
    if not help_options or not self.add_help_option:
        return None

    def show_help(ctx, param, value):
        if value and not ctx.resilient_parsing:
            click.echo(ctx.get_help(), color=ctx.color)
            ctx.exit()

    return click.Option(
        help_options,
        is_flag=True,
        is_eager=True,
        expose_value=False,
        callback=show_help,
        help="显示帮助信息并退出。",
    )


class ChineseGroup(typer.core.TyperGroup):
    get_help_option = _chinese_help_option


class ChineseCommand(typer.core.TyperCommand):
    get_help_option = _chinese_help_option


app = typer.Typer(
    name="mono-kickstart",
    help="Monorepo 项目模板脚手架 CLI 工具",
    cls=ChineseGroup,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command(cls=ChineseCommand)
def init(
    config: Optional[str] = typer.Option(None, "--config", help="配置文件路径"),
    save_config: bool = typer.Option(False, "--save-config", help="保存配置到 .kickstartrc"),
    interactive: bool = typer.Option(False, "--interactive", help="交互式配置"),
    force: bool = typer.Option(False, "--force", help="强制覆盖已有配置"),
    dry_run: bool = typer.Option(False, "--dry-run", help="模拟运行，不实际安装"),
) -> None:
    """初始化 Monorepo 项目和开发环境"""
    typer.echo("🚀 Mono-Kickstart - 初始化 Monorepo 项目")
    typer.echo("此功能将在后续任务中实现")


@app.command(cls=ChineseCommand)
def upgrade(
    tool: Optional[str] = typer.Argument(None, help="要升级的工具名称"),
    all: bool = typer.Option(False, "--all", help="升级所有工具"),
    dry_run: bool = typer.Option(False, "--dry-run", help="模拟运行，不实际升级"),
) -> None:
    """升级已安装的开发工具"""
    typer.echo("🔄 Mono-Kickstart - 升级开发工具")
    typer.echo("此功能将在后续任务中实现")


@app.command(name="setup-shell", cls=ChineseCommand)
def setup_shell() -> None:
    """将 ~/.local/bin 添加到 shell PATH 配置"""
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        rc_file = Path.home() / ".zshrc"
    else:
        rc_file = Path.home() / ".bashrc"

    path_line = 'export PATH="$HOME/.local/bin:$PATH"'

    if rc_file.exists():
        content = rc_file.read_text()
        if ".local/bin" in content:
            typer.echo(f"{rc_file} 中已包含 .local/bin 配置，无需重复添加。")
            return

    with open(rc_file, "a") as f:
        f.write(f"\n{path_line}\n")

    typer.echo(f"已将 PATH 配置写入 {rc_file}")
    typer.echo(f"请运行以下命令使配置生效：source {rc_file}")


def version_callback(value: bool):
    """显示版本信息"""
    if value:
        from mono_kickstart import __version__
        typer.echo(f"Mono-Kickstart version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="显示版本号",
    ),
):
    """
    Mono-Kickstart - Monorepo 项目模板脚手架 CLI 工具

    通过一条命令快速初始化标准化的 Monorepo 工程，自动完成开发环境搭建与工具链安装。
    """
    pass


if __name__ == "__main__":
    app()
