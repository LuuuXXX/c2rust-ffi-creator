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

    # 在 C 目录内执行构建（build_command 推荐为 JSON 数组；字符串格式（可含 && 等 shell 运算符）
    # 将通过 bash -lc 执行以保持兼容性）
    python3 - "${SPEC_JSON}" "${C_DIR}" <<'PYEOF'
import json, sys, subprocess, os

spec_json = sys.argv[1]
c_dir     = sys.argv[2]
with open(spec_json, encoding="utf-8") as f:
    d = json.load(f)
cmd = d["project"]["build_command"]
if isinstance(cmd, list):
    # JSON 数组：直接作为 argv 调用，安全
    shell_cmd = cmd
    use_shell = False
else:
    # 字符串格式：通过 bash -lc 执行，支持 && 等多步命令
    shell_cmd = ["bash", "-lc", cmd]
    use_shell = False
print(f"  C 构建命令：{shell_cmd}")
os.chdir(c_dir)
result = subprocess.run(shell_cmd, shell=use_shell)
sys.exit(result.returncode)
PYEOF

    # 优先从 spec.json output_artifacts 字段获取预期产物路径（将路径作为参数传给 Python）
    ARTIFACTS_JSON=$(python3 -c "
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
arts = d.get('project', {}).get('output_artifacts', [])
print('\n'.join(arts))
" "${SPEC_JSON}" 2>/dev/null || true)

    C_LIB_SO=""
    C_LIB_A=""
    if [[ -n "${ARTIFACTS_JSON}" ]]; then
        SO_FROM_SPEC=()
        A_FROM_SPEC=()
        while IFS= read -r art; do
            [[ -z "${art}" ]] && continue
            art_path="${C_DIR}/${art}"
            if [[ "${art_path}" == *.so || "${art_path}" == *.dylib ]]; then
                SO_FROM_SPEC+=("${art_path}")
            elif [[ "${art_path}" == *.a ]]; then
                A_FROM_SPEC+=("${art_path}")
            fi
        done <<< "${ARTIFACTS_JSON}"
        if [[ ${#SO_FROM_SPEC[@]} -gt 1 ]]; then
            echo "✗ 错误：spec.json output_artifacts 中包含多个动态库，请只保留一个目标产物：" >&2
            printf '    %s\n' "${SO_FROM_SPEC[@]}" >&2
            exit 1
        elif [[ ${#SO_FROM_SPEC[@]} -eq 1 ]]; then
            C_LIB_SO="${SO_FROM_SPEC[0]}"
        fi
        if [[ -z "${C_LIB_SO}" ]]; then
            if [[ ${#A_FROM_SPEC[@]} -gt 1 ]]; then
                echo "✗ 错误：spec.json output_artifacts 中包含多个静态库，请只保留一个目标产物：" >&2
                printf '    %s\n' "${A_FROM_SPEC[@]}" >&2
                exit 1
            elif [[ ${#A_FROM_SPEC[@]} -eq 1 ]]; then
                C_LIB_A="${A_FROM_SPEC[0]}"
            fi
        fi
    fi

    # 回退：在构建目录扫描，如果有多个候选则报错
    if [[ -z "${C_LIB_SO}" && -z "${C_LIB_A}" ]]; then
        mapfile -t SO_CANDIDATES < <(find "${C_DIR}" \( -name "*.so" -o -name "*.dylib" \) 2>/dev/null | grep -v CMakeFiles || true)
        mapfile -t A_CANDIDATES  < <(find "${C_DIR}" -name "*.a" 2>/dev/null | grep -v CMakeFiles || true)
        if [[ ${#SO_CANDIDATES[@]} -eq 1 ]]; then
            C_LIB_SO="${SO_CANDIDATES[0]}"
        elif [[ ${#SO_CANDIDATES[@]} -gt 1 ]]; then
            echo "✗ 错误：在 ${C_DIR} 下发现多个动态库产物，请在 spec.json 的 output_artifacts 字段明确指定：" >&2
            printf '    %s\n' "${SO_CANDIDATES[@]}" >&2
            exit 1
        fi
        if [[ -z "${C_LIB_SO}" ]]; then
            if [[ ${#A_CANDIDATES[@]} -eq 1 ]]; then
                C_LIB_A="${A_CANDIDATES[0]}"
            elif [[ ${#A_CANDIDATES[@]} -gt 1 ]]; then
                echo "✗ 错误：在 ${C_DIR} 下发现多个静态库产物，请在 spec.json 的 output_artifacts 字段明确指定：" >&2
                printf '    %s\n' "${A_CANDIDATES[@]}" >&2
                exit 1
            fi
        fi
    fi

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

# 从 ffi/Cargo.toml 动态读取 [lib] name，回退到 c2rust_ffi
FFI_CARGO="${PROJECT_ROOT}/ffi/Cargo.toml"
if [[ -f "${FFI_CARGO}" ]]; then
    RUST_LIB_NAME=$(python3 -c "
import sys, re
txt = open(sys.argv[1], encoding='utf-8').read()
m = re.search(r'\[lib\].*?^name\s*=\s*[\"\']([\w-]+)[\"\']', txt, re.DOTALL | re.MULTILINE)
print(m.group(1).replace('-', '_') if m else 'c2rust_ffi')
" "${FFI_CARGO}" 2>/dev/null || echo "c2rust_ffi")
else
    RUST_LIB_NAME="c2rust_ffi"
fi

RUST_LIB_SO=$(find "${RUST_TARGET}" -maxdepth 1 \( -name "lib${RUST_LIB_NAME}.so" -o -name "lib${RUST_LIB_NAME}.dylib" \) 2>/dev/null | head -1 || true)
RUST_LIB_A=$(find "${RUST_TARGET}" -maxdepth 1 -name "lib${RUST_LIB_NAME}.a" 2>/dev/null | head -1 || true)

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
    echo "✗ 错误：在 ${RUST_TARGET} 中未找到 lib${RUST_LIB_NAME}.so 或 lib${RUST_LIB_NAME}.a"
    echo "  （lib 名称读取自 ffi/Cargo.toml [lib] name；若已修改库名，请确保构建后产物存在）"
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
    echo "  对于 '< symbol_name'（C 有但 Rust 产物中缺失）："
    echo "    1. 检查 ffi/build.rs 是否已将对应 C 源文件（或静态库）编译并链接进来"
    echo "    2. 检查 spec.json output_artifacts 字段是否指向正确的构建产物路径"
    echo "    3. 确认 C 源文件中的函数已在头文件中声明，并被 hicc-build 正确编译"
    echo ""
    echo "  对于 '> symbol_name'（Rust 产物多出的符号）："
    echo "    1. 若是预期新增的导出，先更新 C 项目后重新提取基准："
    echo "       rm ${EXPECTED_FILE} && bash scripts/verify_symbols.sh ${PROJECT_ROOT}"
    echo "    2. 若是意外导出，检查 ffi/build.rs 是否链接了非预期的 C 目标文件"
    echo "════════════════════════════════════════"
    exit 1
fi
