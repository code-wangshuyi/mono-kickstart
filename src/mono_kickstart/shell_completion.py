"""
Shell 补全脚本生成模块

为 Bash、Zsh 和 Fish 生成 Tab 补全脚本。
"""

import os
from pathlib import Path
from typing import Tuple


# Bash 补全脚本
BASH_COMPLETION_SCRIPT = '''# Bash completion for mk and mono-kickstart
_mk_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # 主命令
    local commands="init upgrade install setup-shell"
    
    # 工具列表
    local tools="nvm node conda bun uv claude-code codex spec-kit bmad-method"
    
    # 如果是第一个参数，补全子命令
    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi
    
    # 根据子命令补全
    case "${COMP_WORDS[1]}" in
        init)
            local init_opts="--config --save-config --interactive --force --dry-run --help"
            COMPREPLY=( $(compgen -W "${init_opts}" -- ${cur}) )
            ;;
        upgrade|install)
            if [[ ${cur} == -* ]]; then
                local opts="--all --dry-run --help"
                COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            else
                COMPREPLY=( $(compgen -W "${tools}" -- ${cur}) )
            fi
            ;;
        setup-shell)
            local opts="--help"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
    esac
}

complete -F _mk_completion mk
complete -F _mk_completion mono-kickstart
'''


# Zsh 补全脚本
ZSH_COMPLETION_SCRIPT = '''#compdef mk mono-kickstart

_mk() {
    local -a commands tools
    commands=(
        'init:初始化 Monorepo 项目和开发环境'
        'upgrade:升级已安装的开发工具'
        'install:安装开发工具'
        'setup-shell:配置 shell（PATH 和 Tab 补全）'
    )
    
    tools=(
        'nvm:Node 版本管理器'
        'node:Node.js 运行时'
        'conda:Python 环境管理器'
        'bun:JavaScript 运行时和包管理器'
        'uv:Python 包管理器'
        'claude-code:Claude Code CLI'
        'codex:OpenAI Codex CLI'
        'spec-kit:Spec 驱动开发工具'
        'bmad-method:BMAD 敏捷开发框架'
    )
    
    _arguments -C \
        '1: :->command' \
        '*:: :->args'
    
    case $state in
        command)
            _describe 'command' commands
            ;;
        args)
            case $words[1] in
                init)
                    _arguments \
                        '--config[配置文件路径]:file:_files' \
                        '--save-config[保存配置到 .kickstartrc]' \
                        '--interactive[交互式配置]' \
                        '--force[强制覆盖已有配置]' \
                        '--dry-run[模拟运行，不实际安装]' \
                        '--help[显示帮助信息]'
                    ;;
                upgrade|install)
                    _arguments \
                        '1: :_describe "tool" tools' \
                        '--all[所有工具]' \
                        '--dry-run[模拟运行]' \
                        '--help[显示帮助信息]'
                    ;;
                setup-shell)
                    _arguments \
                        '--help[显示帮助信息]'
                    ;;
            esac
            ;;
    esac
}

_mk "$@"
'''


# Fish 补全脚本
FISH_COMPLETION_SCRIPT = '''# Fish completion for mk and mono-kickstart

# 子命令
complete -c mk -f -n "__fish_use_subcommand" -a "init" -d "初始化 Monorepo 项目和开发环境"
complete -c mk -f -n "__fish_use_subcommand" -a "upgrade" -d "升级已安装的开发工具"
complete -c mk -f -n "__fish_use_subcommand" -a "install" -d "安装开发工具"
complete -c mk -f -n "__fish_use_subcommand" -a "setup-shell" -d "配置 shell（PATH 和 Tab 补全）"

# init 命令选项
complete -c mk -f -n "__fish_seen_subcommand_from init" -l config -d "配置文件路径"
complete -c mk -f -n "__fish_seen_subcommand_from init" -l save-config -d "保存配置到 .kickstartrc"
complete -c mk -f -n "__fish_seen_subcommand_from init" -l interactive -d "交互式配置"
complete -c mk -f -n "__fish_seen_subcommand_from init" -l force -d "强制覆盖已有配置"
complete -c mk -f -n "__fish_seen_subcommand_from init" -l dry-run -d "模拟运行，不实际安装"

# upgrade 和 install 命令的工具名称
set -l tools nvm node conda bun uv claude-code codex spec-kit bmad-method
complete -c mk -f -n "__fish_seen_subcommand_from upgrade install" -a "$tools"

# upgrade 和 install 命令选项
complete -c mk -f -n "__fish_seen_subcommand_from upgrade install" -l all -d "所有工具"
complete -c mk -f -n "__fish_seen_subcommand_from upgrade install" -l dry-run -d "模拟运行"

# mono-kickstart 别名（与 mk 相同的补全）
complete -c mono-kickstart -w mk
'''


def detect_shell() -> Tuple[str, Path, Path]:
    """检测当前 Shell 类型
    
    Returns:
        (shell_name, rc_file, comp_dir) 元组
        - shell_name: Shell 名称（bash/zsh/fish）
        - rc_file: Shell 配置文件路径
        - comp_dir: 补全脚本目录
    """
    shell = os.environ.get("SHELL", "")
    home = Path.home()
    
    if "zsh" in shell:
        return (
            "zsh",
            home / ".zshrc",
            home / ".zsh_completions"
        )
    elif "fish" in shell:
        return (
            "fish",
            home / ".config" / "fish" / "config.fish",
            home / ".config" / "fish" / "completions"
        )
    else:  # 默认 bash
        return (
            "bash",
            home / ".bashrc",
            home / ".bash_completions"
        )


def get_completion_script(shell_name: str) -> str:
    """获取指定 Shell 的补全脚本
    
    Args:
        shell_name: Shell 名称（bash/zsh/fish）
        
    Returns:
        补全脚本内容
    """
    if shell_name == "zsh":
        return ZSH_COMPLETION_SCRIPT
    elif shell_name == "fish":
        return FISH_COMPLETION_SCRIPT
    else:
        return BASH_COMPLETION_SCRIPT


def setup_shell_completion() -> None:
    """配置 Shell 补全和 PATH
    
    自动检测当前 Shell，安装补全脚本并配置 PATH。
    """
    shell_name, rc_file, comp_dir = detect_shell()
    
    # 1. 配置 PATH
    path_line = 'export PATH="$HOME/.local/bin:$PATH"'
    rc_content = rc_file.read_text() if rc_file.exists() else ""
    
    if ".local/bin" not in rc_content:
        rc_file.parent.mkdir(parents=True, exist_ok=True)
        with open(rc_file, "a") as f:
            f.write(f"\n{path_line}\n")
        print(f"✓ 已将 PATH 配置写入 {rc_file}")
    else:
        print(f"✓ PATH 配置已存在于 {rc_file}")
    
    # 2. 安装补全脚本
    comp_dir.mkdir(parents=True, exist_ok=True)
    
    if shell_name == "zsh":
        comp_file = comp_dir / "_mk"
        source_line = f'fpath=({comp_dir} $fpath) && autoload -Uz compinit && compinit'
    elif shell_name == "fish":
        comp_file = comp_dir / "mk.fish"
        source_line = None  # Fish 自动加载 completions 目录
    else:  # bash
        comp_file = comp_dir / "mk.sh"
        source_line = f"source '{comp_file}'"
    
    comp_script = get_completion_script(shell_name)
    comp_file.write_text(comp_script)
    print(f"✓ 已安装补全脚本到 {comp_file}")
    
    # 3. 确保 rc 文件加载补全（Fish 除外）
    if source_line:
        rc_content = rc_file.read_text()
        if str(comp_file) not in rc_content and "mk_completion" not in rc_content:
            with open(rc_file, "a") as f:
                f.write(f"\n{source_line}\n")
            print(f"✓ 已将补全加载配置写入 {rc_file}")
        else:
            print(f"✓ 补全加载配置已存在于 {rc_file}")
    
    print(f"\n请运行以下命令使配置生效：")
    print(f"  source {rc_file}")
