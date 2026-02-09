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
    add_completion=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


AVAILABLE_TOOLS = [
    ("nvm", "Node 版本管理器"),
    ("node", "Node.js 运行时"),
    ("conda", "Python 环境管理器"),
    ("bun", "JavaScript 运行时和包管理器"),
    ("uv", "Python 包管理器"),
    ("claude-code", "Claude Code CLI"),
    ("codex", "OpenAI Codex CLI"),
    ("spec-kit", "Spec 驱动开发工具"),
    ("bmad-method", "BMAD 敏捷开发框架"),
]


def complete_tool_name(incomplete: str) -> list[tuple[str, str]]:
    """返回匹配的工具名称和描述，用于 Tab 补全。"""
    return [(name, desc) for name, desc in AVAILABLE_TOOLS if name.startswith(incomplete)]


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
    tool: Optional[str] = typer.Argument(
        None, help="要升级的工具名称", autocompletion=complete_tool_name
    ),
    all: bool = typer.Option(False, "--all", help="升级所有工具"),
    dry_run: bool = typer.Option(False, "--dry-run", help="模拟运行，不实际升级"),
) -> None:
    """升级已安装的开发工具"""
    typer.echo("🔄 Mono-Kickstart - 升级开发工具")
    typer.echo("此功能将在后续任务中实现")


@app.command(cls=ChineseCommand)
def install(
    tool: Optional[str] = typer.Argument(
        None, help="要安装的工具名称", autocompletion=complete_tool_name
    ),
    all_tools: bool = typer.Option(False, "--all", help="安装所有工具"),
    dry_run: bool = typer.Option(False, "--dry-run", help="模拟运行，不实际安装"),
) -> None:
    """安装开发工具"""
    typer.echo("📦 Mono-Kickstart - 安装开发工具")
    typer.echo("此功能将在后续任务中实现")


BASH_COMPLETION_SCRIPT = r'''_mk_completion() {
    local cmd_args="${COMP_WORDS[*]:0:$COMP_CWORD+1}"
    local IFS=$'\n'
    local output
    output=$( env _TYPER_COMPLETE_ARGS="$cmd_args" _MK_COMPLETE=complete_zsh $1 2>/dev/null )

    local has_pairs
    has_pairs=$(echo "$output" | grep -c '".*":".*"' || true)
    if [ "$has_pairs" -eq 0 ] && [ "$COMP_CWORD" -gt 1 ]; then
        output=$( env _TYPER_COMPLETE_ARGS="${cmd_args}--" _MK_COMPLETE=complete_zsh $1 2>/dev/null )
    fi

    local completions=() pairs=() max_len=0
    while IFS= read -r line; do
        if [[ "$line" =~ \"([^\"]+)\":\"([^\"]+)\" ]]; then
            completions+=("${BASH_REMATCH[1]}")
            pairs+=("${BASH_REMATCH[1]}|${BASH_REMATCH[2]}")
            (( ${#BASH_REMATCH[1]} > max_len )) && max_len=${#BASH_REMATCH[1]}
        fi
    done <<< "$output"

    if [ ${#completions[@]} -eq 1 ]; then
        COMPREPLY=("${completions[0]}")
    elif [ ${#completions[@]} -gt 1 ]; then
        printf '\n'
        for p in "${pairs[@]}"; do
            local val="${p%%|*}" desc="${p#*|}"
            printf '  %-'"${max_len}"'s  -- %s\n' "$val" "$desc"
        done
        printf '%s%s' "${PS1@P}" "${COMP_LINE}"
        COMPREPLY=("${completions[@]}")
    fi
    return 0
}
complete -o default -o nosort -F _mk_completion mk
complete -o default -o nosort -F _mk_completion mono-kickstart
'''

ZSH_COMPLETION_SCRIPT = r'''#compdef mk mono-kickstart
_mk_completion() {
  eval $(env _TYPER_COMPLETE_ARGS="${words[1,$CURRENT]}" _MK_COMPLETE=complete_zsh mk)
}
compdef _mk_completion mk
compdef _mk_completion mono-kickstart
'''


@app.command(name="setup-shell", cls=ChineseCommand)
def setup_shell() -> None:
    """配置 shell（PATH 和 Tab 补全）"""
    shell = os.environ.get("SHELL", "")
    is_zsh = "zsh" in shell

    if is_zsh:
        rc_file = Path.home() / ".zshrc"
        comp_dir = Path.home() / ".zsh_completions"
        comp_file = comp_dir / "_mk"
        comp_script = ZSH_COMPLETION_SCRIPT
        source_line = f'fpath=({comp_dir} $fpath) && autoload -Uz compinit && compinit'
    else:
        rc_file = Path.home() / ".bashrc"
        comp_dir = Path.home() / ".bash_completions"
        comp_file = comp_dir / "mk.sh"
        comp_script = BASH_COMPLETION_SCRIPT
        source_line = f"source '{comp_file}'"

    # 1. 配置 PATH
    path_line = 'export PATH="$HOME/.local/bin:$PATH"'
    rc_content = rc_file.read_text() if rc_file.exists() else ""

    if ".local/bin" not in rc_content:
        with open(rc_file, "a") as f:
            f.write(f"\n{path_line}\n")
        typer.echo(f"已将 PATH 配置写入 {rc_file}")

    # 2. 安装补全脚本
    comp_dir.mkdir(parents=True, exist_ok=True)
    comp_file.write_text(comp_script)
    typer.echo(f"已安装补全脚本到 {comp_file}")

    # 3. 确保 rc 文件加载补全
    rc_content = rc_file.read_text()
    if str(comp_file) not in rc_content and "mk_completion" not in rc_content:
        with open(rc_file, "a") as f:
            f.write(f"\n{source_line}\n")
        typer.echo(f"已将补全加载配置写入 {rc_file}")

    typer.echo(f"\n请运行以下命令使配置生效：source {rc_file}")


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
