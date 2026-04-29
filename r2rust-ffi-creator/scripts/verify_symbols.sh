#!/usr/bin/env bash
# verify_symbols.sh - 验证 C 与 Rust 版本的导出符号一致性
# 用法: verify_symbols.sh [c2rust-rs 路径]
# 示例: verify_symbols.sh .
#       verify_symbols.sh /path/to/c2rust-rs

set -euo pipefail

usage() {
    echo "用法: $0 [c2rust-rs 路径]"
    echo ""
    echo "对比 C 版本与 Rust 版本的导出符号，验证一致性。"
    echo ""
    echo "前置要求："
    echo "  1. 已运行 build_c.sh 构建 C 版本（产生 .c2rust/c/_build/*.so）"
    echo "  2. 已运行 cargo build --release 构建 Rust 版本（产生 target/release/*.so）"
    echo ""
    echo "退出码："
    echo "  0 - 符号一致"
    echo "  1 - 符号不一致（或构建产物不存在）"
    exit 1
}

PROJECT_DIR="$(realpath "${1:-.}")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 查找 C 版本库文件
find_c_lib() {
    local build_dir="$PROJECT_DIR/.c2rust/c/_build"
    # 查找动态库
    find "$build_dir" -name "*.so" -o -name "*.dylib" 2>/dev/null | head -1 || \
    # 查找静态库
    find "$build_dir" -name "*.a" 2>/dev/null | head -1 || \
    echo ""
}

# 查找 Rust 版本库文件
find_rust_lib() {
    local release_dir="$PROJECT_DIR/target/release"
    # The Rust library is named after the crate: libc2rust_rs.*
    find "$release_dir" -maxdepth 1 \( -name "libc2rust_rs.so" -o -name "libc2rust_rs.dylib" \) 2>/dev/null | head -1 || \
    # Fallback: find any cdylib
    find "$release_dir" -maxdepth 1 \( -name "*.so" -o -name "*.dylib" \) 2>/dev/null | grep -v "build" | head -1 || \
    echo ""
}

echo "=== 符号一致性验证 ==="
echo "  项目目录: $PROJECT_DIR"
echo ""

# 查找库文件
C_LIB="$(find_c_lib)"
RUST_LIB="$(find_rust_lib)"

if [[ -z "$C_LIB" ]]; then
    echo "错误: 未找到 C 版本库文件（.c2rust/c/_build/*.so 或 *.a）"
    echo "请先运行: scripts/build_c.sh .c2rust/c"
    exit 1
fi

if [[ -z "$RUST_LIB" ]]; then
    echo "错误: 未找到 Rust 版本库文件（target/release/*.so 或 *.a）"
    echo "请先运行: cargo build --release"
    exit 1
fi

echo "  C 库文件:    $C_LIB"
echo "  Rust 库文件: $RUST_LIB"
echo ""

# 提取符号
SYMBOLS_C="$PROJECT_DIR/.c2rust/c/symbols_c.txt"
SYMBOLS_RUST="$PROJECT_DIR/.c2rust/symbols_rust.txt"

echo "[1/3] 提取 C 版本符号..."
"$SCRIPT_DIR/extract_symbols.sh" "$C_LIB" > "$SYMBOLS_C"
echo "  符号数: $(wc -l < "$SYMBOLS_C")"
cat "$SYMBOLS_C"

echo ""
echo "[2/3] 提取 Rust 版本符号..."
"$SCRIPT_DIR/extract_symbols.sh" "$RUST_LIB" > "$SYMBOLS_RUST"
echo "  符号数: $(wc -l < "$SYMBOLS_RUST")"
cat "$SYMBOLS_RUST"

echo ""
echo "[3/3] 对比符号..."

# 过滤掉 Rust 运行时特有符号（仅关注公开 API 符号）
# 找出 C 中有但 Rust 中没有的符号
MISSING=$(comm -23 <(sort "$SYMBOLS_C") <(sort "$SYMBOLS_RUST") || true)
# 找出 Rust 中有但 C 中没有的额外符号（不算错误，但会报告）
EXTRA=$(comm -13 <(sort "$SYMBOLS_C") <(sort "$SYMBOLS_RUST") | grep -v "^_" | grep -v "^rust_" | grep -v "^__" || true)

echo ""
if [[ -z "$MISSING" ]]; then
    echo "✓ 所有 C 导出符号均在 Rust 版本中存在"
else
    echo "✗ 以下 C 导出符号在 Rust 版本中缺失："
    echo "$MISSING" | sed 's/^/  - /'
fi

if [[ -n "$EXTRA" ]]; then
    echo ""
    echo "⚠ 以下符号在 Rust 版本中存在但 C 版本中没有（可接受的额外导出）："
    echo "$EXTRA" | sed 's/^/  + /'
fi

echo ""
if [[ -z "$MISSING" ]]; then
    echo "=== 符号一致性验证通过 ✓ ==="
    exit 0
else
    echo "=== 符号一致性验证失败 ✗ ==="
    echo ""
    echo "修复方法："
    echo "  1. 检查缺失函数是否在 src/lib.rs 中添加了 #[no_mangle] pub extern \"C\" fn"
    echo "  2. 检查 Cargo.toml 中 [lib] crate-type 是否包含 cdylib 或 staticlib"
    echo "  3. 参考 references/troubleshooting.md 获取更多诊断信息"
    exit 1
fi
