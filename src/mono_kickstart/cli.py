"""
CLI 入口模块

定义命令行接口和子命令。
"""

import typer
from typing import Optional

app = typer.Typer(
    name="mono-kickstart",
    help="Monorepo 项目模板脚手架 CLI 工具",
    add_completion=True,
)


@app.command()
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


@app.command()
def upgrade(
    tool: Optional[str] = typer.Argument(None, help="要升级的工具名称"),
    all: bool = typer.Option(False, "--all", help="升级所有工具"),
    dry_run: bool = typer.Option(False, "--dry-run", help="模拟运行，不实际升级"),
) -> None:
    """升级已安装的开发工具"""
    typer.echo("🔄 Mono-Kickstart - 升级开发工具")
    typer.echo("此功能将在后续任务中实现")


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
