#!/usr/bin/env bash
# extract_symbols.sh - 提取库文件的导出符号表
# 用法: extract_symbols.sh <库文件路径>
# 示例: extract_symbols.sh .c2rust/c/_build/libcalc.so

set -euo pipefail

usage() {
    echo "用法: $0 <库文件路径>"
    echo ""
    echo "提取动态库或静态库的导出符号表，输出到 stdout。"
    echo ""
    echo "示例:"
    echo "  $0 .c2rust/c/_build/libcalc.so > .c2rust/c/symbols_c.txt"
    echo "  $0 target/release/libc2rust_rs.so > symbols_rust.txt"
    exit 1
}

[[ $# -lt 1 ]] && usage

LIB_FILE="$1"

if [[ ! -f "$LIB_FILE" ]]; then
    echo "错误: 库文件不存在: $LIB_FILE" >&2
    exit 1
fi

# 检测平台和文件类型
case "$(uname -s)" in
    Linux)
        if file "$LIB_FILE" | grep -q "shared object"; then
            # 动态库：提取全局导出函数符号
            nm -gD --defined-only "$LIB_FILE" 2>/dev/null \
                | grep " T \| W " \
                | awk '{print $3}' \
                | sort
        else
            # 静态库
            nm -g --defined-only "$LIB_FILE" 2>/dev/null \
                | grep " T \| W " \
                | awk '{print $3}' \
                | sort
        fi
        ;;
    Darwin)
        if file "$LIB_FILE" | grep -q "dynamically linked\|Mach-O"; then
            nm -gU "$LIB_FILE" 2>/dev/null \
                | grep " T \| W " \
                | awk '{print $3}' \
                | sed 's/^_//' \
                | sort
        else
            nm -g "$LIB_FILE" 2>/dev/null \
                | grep " T \| W " \
                | awk '{print $3}' \
                | sed 's/^_//' \
                | sort
        fi
        ;;
    *)
        # 通用回退：使用 nm
        nm -g "$LIB_FILE" 2>/dev/null \
            | grep " T \| W " \
            | awk '{print $3}' \
            | sort
        ;;
esac
