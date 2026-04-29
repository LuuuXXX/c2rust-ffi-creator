#!/usr/bin/env bash
# copy_c_sources.sh - 将 C 源码复制到 c2rust-rs/.c2rust/c/ 目录
# 用法: copy_c_sources.sh <原C项目路径> <c2rust-rs路径>
# 示例: copy_c_sources.sh /path/to/my-c-lib ./c2rust-rs

set -euo pipefail

usage() {
    echo "用法: $0 <原C项目路径> <c2rust-rs路径>"
    echo ""
    echo "将原 C 项目的源代码复制到 c2rust-rs/.c2rust/c/ 目录，保持原目录结构。"
    echo ""
    echo "示例:"
    echo "  $0 /path/to/my-c-lib ./c2rust-rs"
    exit 1
}

[[ $# -lt 2 ]] && usage

C_SRC="$(realpath "$1")"
DEST_ROOT="$(realpath "$2")"
DEST_DIR="$DEST_ROOT/.c2rust/c"

if [[ ! -d "$C_SRC" ]]; then
    echo "错误: C 项目路径不存在: $C_SRC"
    exit 1
fi

echo "=== 复制 C 源码 ==="
echo "  源目录: $C_SRC"
echo "  目标目录: $DEST_DIR"
echo ""

mkdir -p "$DEST_DIR"

# 复制所有 .c、.h 文件，保持目录结构
echo "[1/4] 复制 .c 和 .h 文件..."
find "$C_SRC" -type f \( -name "*.c" -o -name "*.h" \) | while read -r file; do
    rel_path="${file#$C_SRC/}"
    dest_file="$DEST_DIR/$rel_path"
    mkdir -p "$(dirname "$dest_file")"
    cp "$file" "$dest_file"
    echo "  复制: $rel_path"
done

# 复制构建文件
echo ""
echo "[2/4] 复制构建文件..."
for build_file in CMakeLists.txt Makefile meson.build configure.ac configure build.sh; do
    if [[ -f "$C_SRC/$build_file" ]]; then
        cp "$C_SRC/$build_file" "$DEST_DIR/$build_file"
        echo "  复制: $build_file"
    fi
done

# 递归查找 CMakeLists.txt
find "$C_SRC" -name "CMakeLists.txt" -not -path "$C_SRC/CMakeLists.txt" | while read -r file; do
    rel_path="${file#$C_SRC/}"
    dest_file="$DEST_DIR/$rel_path"
    mkdir -p "$(dirname "$dest_file")"
    cp "$file" "$dest_file"
    echo "  复制: $rel_path"
done

# 复制测试目录
echo ""
echo "[3/4] 复制测试文件..."
for test_dir in tests test test_suite; do
    if [[ -d "$C_SRC/$test_dir" ]]; then
        cp -r "$C_SRC/$test_dir" "$DEST_DIR/$test_dir"
        echo "  复制目录: $test_dir/"
    fi
done

# 生成复制清单
echo ""
echo "[4/4] 生成复制清单..."
MANIFEST="$DEST_DIR/MANIFEST.txt"
{
    echo "# C 源码复制清单"
    echo "# 生成时间: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "# 原始路径: $C_SRC"
    echo ""
    echo "## 文件列表"
    find "$DEST_DIR" -type f | sort | while read -r f; do
        echo "  ${f#$DEST_DIR/}"
    done
} > "$MANIFEST"

echo ""
echo "=== 复制完成 ==="
echo "  文件已写入: $DEST_DIR"
echo "  清单文件: $MANIFEST"
echo ""
echo "下一步: 运行 analyze_c_project.sh $DEST_DIR 分析 C 项目"
