#!/usr/bin/env bash
# verify_symbols.sh — 对比 C 产物与 Rust FFI 产物的导出符号表
#
# 用法：
#   bash scripts/verify_symbols.sh <project_root>
#
# 示例：
#   bash scripts/verify_symbols.sh ./c2rust-rs
#
# 环境依赖：nm（binutils），diff，cargo，python3，原 C 项目所需构建工具

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${1:-$(pwd)}"
OS_TYPE="$(uname -s)"

C_DIR="${PROJECT_ROOT}/.c2rust/c"
SPEC_JSON="${C_DIR}/spec.json"
EXPECTED_FILE="${C_DIR}/symbols_expected.txt"
RUST_TARGET="${PROJECT_ROOT}/target/release"

# 辅助函数：跨平台提取库的已定义公开符号
_nm_symbols() {
    local lib="$1"
    if [[ "${OS_TYPE}" == "Darwin" ]]; then
        # macOS: -g 全局符号，-U 仅已定义
        nm -gU "${lib}" 2>/dev/null | awk '{print $NF}'
    elif [[ "${lib}" == *.so || "${lib}" == *.dylib ]]; then
        # Linux 动态库：读取 .dynsym 节
        nm -D --defined-only "${lib}" 2>/dev/null | awk '{print $NF}'
    else
        # Linux 静态库
        nm --defined-only "${lib}" 2>/dev/null | awk '{print $NF}'
    fi
}

# 临时文件（通过 trap 在退出时自动清理）
TMP_RUST_SYMBOLS="$(mktemp)"
TMP_EXPECTED_SYMBOLS="$(mktemp)"
trap 'rm -f "${TMP_RUST_SYMBOLS}" "${TMP_EXPECTED_SYMBOLS}"' EXIT

echo "═══════════════════════════════════════════════════"
echo "  c2rust-ffi-creator 符号表验证"
echo "  项目根目录：${PROJECT_ROOT}"
echo "═══════════════════════════════════════════════════"

# ── 步骤 0：从原 C 项目构建产物提取基准符号（首次运行） ──
if [[ ! -f "${EXPECTED_FILE}" ]]; then
    echo ""
    echo "[0/4] 首次运行：构建原 C 项目并提取导出符号作为基准..."

    if [[ ! -f "${SPEC_JSON}" ]]; then
        echo "✗ 错误：未找到 ${SPEC_JSON}，请先运行 analyze_c_project.py"
        exit 1
    fi

    # 从 spec.json 读取构建命令
    C_BUILD_CMD=$(python3 -c "import json,sys; d=json.load(open('${SPEC_JSON}')); print(d['project']['build_command'])")
    echo "  C 构建命令：${C_BUILD_CMD}"

    # 在 C 目录内执行构建（保留原目录结构，构建可正常工作）
    pushd "${C_DIR}" > /dev/null
    eval "${C_BUILD_CMD}"
    popd > /dev/null

    # 查找 C 构建产物（.so / .a / .dylib）
    C_LIB_SO=$(find "${C_DIR}" -name "*.so" -o -name "*.dylib" 2>/dev/null | head -1 || true)
    C_LIB_A=$(find "${C_DIR}" -name "*.a" 2>/dev/null | grep -v "CMakeFiles" | head -1 || true)

    if [[ -n "${C_LIB_SO}" ]]; then
        echo "  使用 C 动态库：${C_LIB_SO}"
        _nm_symbols "${C_LIB_SO}" \
            | grep -v '^$' | sort -u > "${EXPECTED_FILE}"
    elif [[ -n "${C_LIB_A}" ]]; then
        echo "  使用 C 静态库：${C_LIB_A}"
        _nm_symbols "${C_LIB_A}" \
            | grep -v '^$' | sort -u > "${EXPECTED_FILE}"
    else
        echo "✗ 错误：构建完成但未找到 .so / .a 产物，请检查 C 项目的构建输出目录。"
        exit 1
    fi

    C_COUNT=$(wc -l < "${EXPECTED_FILE}")
    echo "  ✓ 已从 C 产物提取 ${C_COUNT} 个符号写入 ${EXPECTED_FILE}"
    echo "  请将此文件提交到版本控制，以便后续 Rust 符号对比使用。"
    echo ""
fi

# ── 步骤 1：构建 Rust FFI crate ──────────────────────
echo ""
echo "[1/4] 构建 Rust FFI crate..."
cd "${PROJECT_ROOT}"
cargo build --release -p ffi 2>&1 | tail -5
echo "✓ 构建完成"

# ── 步骤 2：提取 Rust 导出符号 ───────────────────────
echo ""
echo "[2/4] 提取 Rust 产物导出符号..."

RUST_LIB_SO=$(find "${RUST_TARGET}" -maxdepth 1 \( -name "libc2rust_ffi.so" -o -name "libc2rust_ffi.dylib" \) 2>/dev/null | head -1 || true)
RUST_LIB_A=$(find "${RUST_TARGET}" -maxdepth 1 -name "libc2rust_ffi.a" 2>/dev/null | head -1 || true)

if [[ -n "${RUST_LIB_SO}" ]]; then
    echo "  使用动态库：${RUST_LIB_SO}"
    _nm_symbols "${RUST_LIB_SO}" \
        | grep -v -E '^(__rust_|_rust_|rust_|_ZN(3std|4core|5alloc)|____)' \
        | grep -v '^$' \
        | sort -u > "${TMP_RUST_SYMBOLS}"
elif [[ -n "${RUST_LIB_A}" ]]; then
    echo "  使用静态库：${RUST_LIB_A}"
    _nm_symbols "${RUST_LIB_A}" \
        | grep -v -E '^(__rust_|_rust_|rust_|_ZN(3std|4core|5alloc)|____)' \
        | grep -v '^$' \
        | sort -u > "${TMP_RUST_SYMBOLS}"
else
    echo "✗ 错误：在 ${RUST_TARGET} 中未找到 libc2rust_ffi.so 或 libc2rust_ffi.a"
    exit 1
fi

RUST_COUNT=$(wc -l < "${TMP_RUST_SYMBOLS}")
echo "  Rust 导出符号数：${RUST_COUNT}"

# ── 步骤 3：读取 C 基准符号 ──────────────────────────
echo ""
echo "[3/4] 读取 C 基准符号表..."

grep -v '^#' "${EXPECTED_FILE}" | grep -v '^$' | sort -u > "${TMP_EXPECTED_SYMBOLS}"
EXPECTED_COUNT=$(wc -l < "${TMP_EXPECTED_SYMBOLS}")
echo "  C 基准符号数：${EXPECTED_COUNT}"

# ── 步骤 4：比对 ─────────────────────────────────────
echo ""
echo "[4/4] 对比 C 基准符号 vs Rust 导出符号..."

DIFF_OUTPUT=$(diff "${TMP_EXPECTED_SYMBOLS}" "${TMP_RUST_SYMBOLS}" || true)

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
    echo "  （< 表示 C 有但 Rust 产物中缺失；> 表示 Rust 产物多出的符号）"
    echo "────────────────────────────────────────"
    echo "${DIFF_OUTPUT}"
    echo "────────────────────────────────────────"
    echo ""
    echo "修复建议："
    echo "  对于 '< symbol_name'（C 有但 Rust 缺失）："
    echo "    1. 检查对应 Rust 函数是否添加了 #[no_mangle]"
    echo "    2. 检查函数是否声明为 pub extern \"C\""
    echo "    3. 检查函数名拼写是否与 C 头文件一致"
    echo ""
    echo "  对于 '> symbol_name'（Rust 多出的符号）："
    echo "    1. 若是预期新增的导出，先更新 C 项目后重新提取基准："
    echo "       rm ${EXPECTED_FILE} && bash scripts/verify_symbols.sh ${PROJECT_ROOT}"
    echo "    2. 若是意外导出，检查相应函数的可见性修饰符"
    echo "════════════════════════════════════════"
    exit 1
fi
