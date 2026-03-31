#!/usr/bin/env bash
set -euo pipefail

echo "📦 安装 mono-kickstart (editable mode)..."
pip install -e .

# 查找 mk 命令的绝对路径
MK_PATH=$(which mk 2>/dev/null || true)

if [ -z "$MK_PATH" ]; then
    echo "❌ 安装后未找到 mk 命令，请检查 pip install 是否成功"
    exit 1
fi

MK_ABS_PATH=$(realpath "$MK_PATH")
echo "✓ 找到 mk: $MK_ABS_PATH"

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
