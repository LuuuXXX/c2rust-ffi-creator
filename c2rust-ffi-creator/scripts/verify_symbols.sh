#!/usr/bin/env bash
# verify_symbols.sh — 对比 C 产物与 Rust FFI 产物的导出符号表
#
# 用法：
#   bash scripts/verify_symbols.sh <project_root>
#
# 示例：
#   bash scripts/verify_symbols.sh ./c2rust-rs
#
# 环境依赖：nm（binutils），diff，cargo

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${1:-$(pwd)}"

C_DIR="${PROJECT_ROOT}/.c2rust/c"
EXPECTED_FILE="${C_DIR}/symbols_expected.txt"
RUST_TARGET="${PROJECT_ROOT}/target/release"

echo "═══════════════════════════════════════════════════"
echo "  c2rust-ffi-creator 符号表验证"
echo "  项目根目录：${PROJECT_ROOT}"
echo "═══════════════════════════════════════════════════"

# ── 步骤 1：构建 Rust FFI crate ──────────────────────
echo ""
echo "[1/4] 构建 Rust FFI crate..."
cd "${PROJECT_ROOT}"
cargo build --release -p ffi 2>&1 | tail -5
echo "✓ 构建完成"

# ── 步骤 2：提取 Rust 导出符号 ───────────────────────
echo ""
echo "[2/4] 提取 Rust 产物导出符号..."

RUST_LIB_SO=$(find "${RUST_TARGET}" -maxdepth 1 -name "libc2rust_ffi.so" -o -name "libc2rust_ffi.dylib" 2>/dev/null | head -1 || true)
RUST_LIB_A=$(find "${RUST_TARGET}" -maxdepth 1 -name "libc2rust_ffi.a" 2>/dev/null | head -1 || true)

if [[ -n "${RUST_LIB_SO}" ]]; then
    echo "  使用动态库：${RUST_LIB_SO}"
    nm -D --defined-only "${RUST_LIB_SO}" 2>/dev/null \
        | awk '{print $NF}' \
        | grep -v -E '^(__rust_|_rust_|rust_|_ZN(3std|4core|5alloc)|____)' \
        | grep -v '^$' \
        | sort -u > /tmp/rust_symbols.txt
elif [[ -n "${RUST_LIB_A}" ]]; then
    echo "  使用静态库：${RUST_LIB_A}"
    nm --defined-only "${RUST_LIB_A}" 2>/dev/null \
        | awk '{print $NF}' \
        | grep -v -E '^(__rust_|_rust_|rust_|_ZN(3std|4core|5alloc)|____)' \
        | grep -v '^$' \
        | sort -u > /tmp/rust_symbols.txt
else
    echo "✗ 错误：在 ${RUST_TARGET} 中未找到 libc2rust_ffi.so 或 libc2rust_ffi.a"
    exit 1
fi

RUST_COUNT=$(wc -l < /tmp/rust_symbols.txt)
echo "  Rust 导出符号数：${RUST_COUNT}"

# ── 步骤 3：获取预期符号表 ───────────────────────────
echo ""
echo "[3/4] 读取预期符号表..."

if [[ ! -f "${EXPECTED_FILE}" ]]; then
    echo "  ⚠ 未找到 symbols_expected.txt，将以当前 Rust 符号表作为基准并写入。"
    cp /tmp/rust_symbols.txt "${EXPECTED_FILE}"
    echo "  已写入：${EXPECTED_FILE}"
    echo ""
    echo "════════════════════════════════════════"
    echo "  ✓ 基准符号表已创建，请提交到版本控制。"
    echo "════════════════════════════════════════"
    exit 0
fi

# 过滤掉注释行
grep -v '^#' "${EXPECTED_FILE}" | grep -v '^$' | sort -u > /tmp/expected_symbols.txt
EXPECTED_COUNT=$(wc -l < /tmp/expected_symbols.txt)
echo "  预期符号数：${EXPECTED_COUNT}"

# ── 步骤 4：比对 ─────────────────────────────────────
echo ""
echo "[4/4] 对比符号表..."

DIFF_OUTPUT=$(diff /tmp/expected_symbols.txt /tmp/rust_symbols.txt || true)

if [[ -z "${DIFF_OUTPUT}" ]]; then
    echo ""
    echo "════════════════════════════════════════"
    echo "  ✓ 符号表验证通过！共 ${EXPECTED_COUNT} 个符号完全匹配。"
    echo "════════════════════════════════════════"
    exit 0
else
    echo ""
    echo "════════════════════════════════════════"
    echo "  ✗ 符号表验证失败！差异如下："
    echo "  （< 表示预期有但 Rust 产物中缺失；> 表示 Rust 产物多出的符号）"
    echo "────────────────────────────────────────"
    echo "${DIFF_OUTPUT}"
    echo "────────────────────────────────────────"
    echo ""
    echo "修复建议："
    echo "  对于 '< symbol_name'（缺失符号）："
    echo "    1. 检查对应 Rust 函数是否添加了 #[no_mangle]"
    echo "    2. 检查函数是否声明为 pub extern \"C\""
    echo "    3. 检查函数名拼写是否与 C 头文件一致"
    echo ""
    echo "  对于 '> symbol_name'（多余符号）："
    echo "    1. 若是预期新增的导出，运行以下命令更新基准："
    echo "       cp /tmp/rust_symbols.txt ${EXPECTED_FILE}"
    echo "    2. 若是意外导出，检查相应函数的可见性修饰符"
    echo "════════════════════════════════════════"
    exit 1
fi
