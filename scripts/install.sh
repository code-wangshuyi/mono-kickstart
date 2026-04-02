#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# 检查 conda 是否可用
if ! command -v conda &>/dev/null; then
    echo "❌ 未找到 conda 命令，请先安装 Miniconda/Anaconda"
    exit 1
fi

CONDA_BASE=$(conda info --base)
ENV_NAME="mk"
ENV_PATH="$CONDA_BASE/envs/$ENV_NAME"

# 检查 mk 环境是否存在
if conda env list | grep -qE "^mk\s"; then
    echo "✓ conda 环境 '$ENV_NAME' 已存在，跳过创建"
else
    echo "📦 创建 conda 环境 '$ENV_NAME' (python=3.11)..."
    conda create -n "$ENV_NAME" python=3.11 --yes
    echo "✓ conda 环境 '$ENV_NAME' 创建完成"
fi

# 使用环境内的 pip 安装项目（editable mode）
PIP="$ENV_PATH/bin/pip"
if [ ! -x "$PIP" ]; then
    echo "❌ 未找到 $PIP，conda 环境可能未正确创建"
    exit 1
fi

echo "📥 安装 mono-kickstart (editable mode) 到环境 '$ENV_NAME'..."
"$PIP" install -e .

# 定位 mk 可执行文件
MK_ABS_PATH="$ENV_PATH/bin/mk"
if [ ! -x "$MK_ABS_PATH" ]; then
    echo "❌ 安装后未找到 $MK_ABS_PATH，请检查安装是否成功"
    exit 1
fi
echo "✓ 找到 mk: $MK_ABS_PATH"

# 创建软链接到 /usr/local/bin/mk
LINK_PATH="/usr/local/bin/mk"

if [ -L "$LINK_PATH" ]; then
    echo "⚠️  $LINK_PATH 已存在（软链接），将更新..."
    sudo ln -sf "$MK_ABS_PATH" "$LINK_PATH"
elif [ -e "$LINK_PATH" ]; then
    echo "⚠️  $LINK_PATH 已存在（非软链接），跳过创建"
    echo "💡 如需覆盖，请手动执行: sudo ln -sf $MK_ABS_PATH $LINK_PATH"
    exit 0
else
    sudo ln -s "$MK_ABS_PATH" "$LINK_PATH"
fi

echo "✓ 已创建软链接: $LINK_PATH -> $MK_ABS_PATH"
echo "✨ 安装完成！可以直接使用 mk 命令。"
