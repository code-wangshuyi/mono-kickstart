#!/usr/bin/env bash
#
# setenv.sh — 一键配置 mono-kickstart 开发环境（uv 路线）
#
# 幂等设计：可重复执行，每步先检测再动作，已就绪的环节会跳过。
# 与 install.sh 的分工：install.sh 走 conda 路线做终端用户安装，
#                       本脚本走 uv 路线搭开发环境。
#
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_ROOT="$(pwd)"
VENV_DIR="$REPO_ROOT/.venv"
LINK_PATH="/usr/local/bin/mk"
UV_INSTALL_URL="https://astral.sh/uv/install.sh"

# ---- 可调参数（由命令行开关覆盖）----
PYTHON_VERSION="3.11"
DO_LINK=1
WITH_RUFF=0
DO_CHECK=0
DO_TEST=0
FORCE_RECREATE=0

UV=""
UV_IN_PATH=0   # uv 是否本就在用户 PATH 中（在改动 PATH 之前记录）

usage() {
    cat <<'EOF'
用法: bash scripts/setenv.sh [选项]

一键配置 mono-kickstart 开发环境：安装 uv、创建 Python 虚拟环境、
按 uv.lock 同步依赖（含 dev），并把 mk 命令软链到 /usr/local/bin。

选项:
  --python <版本>   指定虚拟环境的 Python 版本（默认: 3.11）
  --no-link         跳过创建 /usr/local/bin/mk 全局软链
  --with-ruff       额外安装 ruff（uv tool install），补齐 lint/format 能力
  --check           结尾执行冒烟自检（Python 版本、mk 可用性、dev 依赖）
  --test            结尾执行单元测试（uv run pytest tests/unit/）
  --force           无条件删除并重建 .venv
  -h, --help        显示本帮助

示例:
  bash scripts/setenv.sh                    # 标准一键配置
  bash scripts/setenv.sh --check            # 配置并自检
  bash scripts/setenv.sh --force --check    # 强制重建后自检
  bash scripts/setenv.sh --with-ruff --test # 装上 ruff 并跑单元测试

退出码: 0=成功  1=一般错误  2=用法错误
EOF
}

# ---- 参数解析 ----
while [ $# -gt 0 ]; do
    case "$1" in
        --python)
            if [ $# -lt 2 ]; then
                echo "❌ --python 需要一个版本号参数" >&2
                exit 2
            fi
            PYTHON_VERSION="$2"
            shift 2
            ;;
        --python=*)
            PYTHON_VERSION="${1#*=}"
            shift
            ;;
        --no-link)   DO_LINK=0;        shift ;;
        --with-ruff) WITH_RUFF=1;      shift ;;
        --check)     DO_CHECK=1;       shift ;;
        --test)      DO_TEST=1;        shift ;;
        --force)     FORCE_RECREATE=1; shift ;;
        -h|--help)   usage; exit 0 ;;
        *)
            echo "❌ 未知选项: $1" >&2
            echo "💡 运行 'bash scripts/setenv.sh --help' 查看用法" >&2
            exit 2
            ;;
    esac
done

# ---------------------------------------------------------------------------
# 1. 确保 uv 可用
# ---------------------------------------------------------------------------
find_uv() {
    if command -v uv &>/dev/null; then
        command -v uv
        return 0
    fi
    # uv 官方安装脚本新版落在 ~/.local/bin，旧版落在 ~/.cargo/bin，两处都探
    for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
        if [ -x "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

ensure_uv() {
    if UV="$(find_uv)"; then
        echo "✓ uv 已安装: $UV ($("$UV" --version))"
    else
        echo "📥 未找到 uv，正在安装..."
        if ! command -v curl &>/dev/null; then
            echo "❌ 未找到 curl，无法自动安装 uv" >&2
            echo "💡 请先安装 curl，或手动安装 uv: $UV_INSTALL_URL" >&2
            exit 1
        fi
        curl -LsSf "$UV_INSTALL_URL" | sh
        if ! UV="$(find_uv)"; then
            echo "❌ uv 安装后仍未找到可执行文件" >&2
            echo "💡 请检查安装输出，或手动将 uv 所在目录加入 PATH" >&2
            exit 1
        fi
        echo "✓ uv 安装完成: $UV ($("$UV" --version))"
    fi

    # 记录改 PATH 之前的状态，供结尾提示是否需要持久化 PATH
    if command -v uv &>/dev/null; then
        UV_IN_PATH=1
    fi

    # 把 uv 所在目录加进 PATH，保证 uv 自身及其子进程都能互相找到
    UV_BIN_DIR="$(dirname "$UV")"
    case ":$PATH:" in
        *":$UV_BIN_DIR:"*) ;;
        *) export PATH="$UV_BIN_DIR:$PATH" ;;
    esac
}

# ---------------------------------------------------------------------------
# 2. 确保虚拟环境健康
# ---------------------------------------------------------------------------
venv_is_healthy() {
    # 关键：用「能否真正执行」判活，而非判断目录/文件是否存在。
    # 若 uv 托管的 Python 被删除，.venv/bin/python 会成为悬空软链——
    # 目录仍在、看着正常，但任何命令都跑不起来。
    [ -x "$VENV_DIR/bin/python" ] && "$VENV_DIR/bin/python" -c 'pass' &>/dev/null
}

ensure_venv() {
    if [ "$FORCE_RECREATE" -eq 1 ] && [ -d "$VENV_DIR" ]; then
        echo "🔄 --force 已指定，删除现有虚拟环境..."
        rm -rf "$VENV_DIR"
    elif [ -d "$VENV_DIR" ]; then
        if venv_is_healthy; then
            local current
            current="$("$VENV_DIR/bin/python" --version 2>&1)"
            echo "✓ 虚拟环境健康，跳过创建 ($current)"
            return 0
        fi
        echo "⚠️  检测到虚拟环境已损坏（解释器无法执行），将重建..."
        rm -rf "$VENV_DIR"
    fi

    echo "📦 创建虚拟环境 (Python $PYTHON_VERSION)..."
    # 不用 uv python pin：那会在仓库根写出 .python-version，显式传 --python 足够
    "$UV" venv --python "$PYTHON_VERSION"
    echo "✓ 虚拟环境创建完成: $VENV_DIR"
}

# ---------------------------------------------------------------------------
# 3. 同步依赖（含 dev）
# ---------------------------------------------------------------------------
sync_deps() {
    echo "📥 同步依赖（含 dev）..."
    "$UV" sync --extra dev
    echo "✓ 依赖同步完成"
}

# ---------------------------------------------------------------------------
# 4. 创建全局 mk 软链
# ---------------------------------------------------------------------------
# 按权限选择写入方式：root 直接写，非 root 尝试 sudo，都不行则给提示。
run_privileged() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo &>/dev/null; then
        sudo "$@"
    else
        return 1
    fi
}

link_mk() {
    local mk_path="$VENV_DIR/bin/mk"

    if [ ! -x "$mk_path" ]; then
        echo "⚠️  未找到 $mk_path，跳过软链创建"
        return 0
    fi

    if [ -L "$LINK_PATH" ]; then
        local current
        current="$(readlink "$LINK_PATH")"
        if [ "$current" = "$mk_path" ]; then
            echo "✓ 全局软链已正确指向本项目，跳过"
            return 0
        fi
        echo "⚠️  $LINK_PATH 当前指向 $current，将更新..."
    elif [ -e "$LINK_PATH" ]; then
        # 普通文件不覆盖，保守处理（与 install.sh 一致）
        echo "⚠️  $LINK_PATH 已存在且非软链接，跳过"
        echo "💡 如需覆盖，请手动执行: ln -sf $mk_path $LINK_PATH"
        return 0
    fi

    if run_privileged ln -sf "$mk_path" "$LINK_PATH"; then
        echo "✓ 已创建全局软链: $LINK_PATH -> $mk_path"
    else
        # 拿不到权限不算失败，环境本身已经可用
        echo "⚠️  无权限写入 $LINK_PATH（既非 root，也无 sudo），跳过"
        echo "💡 如需全局 mk 命令，请手动执行: ln -sf $mk_path $LINK_PATH"
    fi
}

# ---------------------------------------------------------------------------
# 5. 可选：安装 ruff
# ---------------------------------------------------------------------------
install_ruff() {
    # ruff 不在 pyproject 的 dev extra 中（CI 亦单独安装），
    # 用 uv tool 装成独立工具，避免污染 uv.lock
    echo "📥 安装 ruff..."
    "$UV" tool install ruff
    echo "✓ ruff 安装完成"
}

# ---------------------------------------------------------------------------
# 6. 可选：冒烟自检
# ---------------------------------------------------------------------------
smoke_check() {
    echo ""
    echo "🔍 冒烟自检..."

    local py_version
    py_version="$("$UV" run python --version 2>&1)"
    case "$py_version" in
        *"$PYTHON_VERSION"*) echo "  ✓ Python 版本: $py_version" ;;
        *)
            echo "  ✗ Python 版本不符: 期望 $PYTHON_VERSION，实际 $py_version" >&2
            return 1
            ;;
    esac

    if "$UV" run mk --version &>/dev/null; then
        echo "  ✓ mk CLI: $("$UV" run mk --version 2>&1)"
    else
        echo "  ✗ mk CLI 无法执行" >&2
        return 1
    fi

    if "$UV" run python -c "import pytest, hypothesis, responses, coverage" &>/dev/null; then
        echo "  ✓ dev 依赖可用 (pytest / hypothesis / responses / coverage)"
    else
        echo "  ✗ dev 依赖缺失" >&2
        return 1
    fi

    echo "✓ 冒烟自检通过"
}

# ---------------------------------------------------------------------------
# 7. 可选：单元测试
# ---------------------------------------------------------------------------
run_tests() {
    echo ""
    echo "🧪 运行单元测试..."
    # 必须带 --no-cov：pyproject 的 addopts 默认强开覆盖率报告
    "$UV" run pytest tests/unit/ -q --no-cov
}

# ---------------------------------------------------------------------------
# 8. 结尾摘要
# ---------------------------------------------------------------------------
print_summary() {
    echo ""
    echo "✨ 环境配置完成！"
    echo ""
    echo "  虚拟环境:  $VENV_DIR"
    echo "  Python:    $("$VENV_DIR/bin/python" --version 2>&1)"
    if [ -x "$VENV_DIR/bin/mk" ]; then
        echo "  mk:        $VENV_DIR/bin/mk"
    fi
    if [ -L "$LINK_PATH" ]; then
        echo "  全局命令:  $LINK_PATH"
    fi
    echo ""
    echo "常用命令:"
    echo "  uv run mk status              # 查看工具状态"
    echo "  uv run pytest tests/unit/     # 运行单元测试"
    echo ""

    # uv 若不在用户原有 PATH 中，提示持久化
    local uv_bin_dir
    uv_bin_dir="$(dirname "$UV")"
    if [ "$UV_IN_PATH" -eq 0 ]; then
        echo "💡 uv 位于 $uv_bin_dir，该目录不在 PATH 中。"
        echo "   如需直接使用 uv 命令，请加入 shell 配置文件："
        echo "     export PATH=\"$uv_bin_dir:\$PATH\""
        echo ""
    fi
}

# ---------------------------------------------------------------------------
main() {
    echo "🚀 配置 mono-kickstart 开发环境"
    echo "   仓库路径: $REPO_ROOT"
    echo ""

    ensure_uv
    ensure_venv
    sync_deps

    if [ "$DO_LINK" -eq 1 ]; then
        link_mk
    else
        echo "⏭️  已指定 --no-link，跳过全局软链"
    fi

    if [ "$WITH_RUFF" -eq 1 ]; then
        install_ruff
    fi

    if [ "$DO_CHECK" -eq 1 ]; then
        smoke_check
    fi

    if [ "$DO_TEST" -eq 1 ]; then
        run_tests
    fi

    print_summary
}

main
