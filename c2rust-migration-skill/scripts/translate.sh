#!/usr/bin/env bash
# translate.sh — Phase 1：位级兼容 Rust 替代（C→Rust 翻译阶段）
#
# 执行 c2rust-migration-skill 的第一阶段工作流：
#   Step 1: 扫描 C 头文件，生成 Spec v1（as-is）
#   Step 2: 生成迁移分析报告（风险信号 + 差分测试分级建议）
#
# 使用方法：
#   bash translate.sh HEADERS=<头文件目录或.h文件>
#   bash translate.sh HEADERS=<路径> SPEC_OUT=<spec输出路径> REPORT_OUT=<报告输出路径>
#
# 环境变量（均可通过命令行 KEY=VALUE 传入）：
#   HEADERS        — 头文件目录或单个 .h 文件（必须）
#   SPEC_OUT       — Spec v1 YAML 输出路径（默认：spec-v1.yml）
#   REPORT_OUT     — 迁移分析报告输出路径（默认：report.md）
#   TEST_COVERAGE  — 现有 C 测试覆盖率估算 0.0~1.0（默认：0.5）
#   PYTHON         — Python 解释器（默认：python3）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
SPEC_OUT="${SPEC_OUT:-spec-v1.yml}"
REPORT_OUT="${REPORT_OUT:-report.md}"
TEST_COVERAGE="${TEST_COVERAGE:-0.5}"

# 解析 KEY=VALUE 参数
for arg in "$@"; do
    case "$arg" in
        HEADERS=*)  HEADERS="${arg#HEADERS=}" ;;
        SPEC_OUT=*) SPEC_OUT="${arg#SPEC_OUT=}" ;;
        REPORT_OUT=*) REPORT_OUT="${arg#REPORT_OUT=}" ;;
        TEST_COVERAGE=*) TEST_COVERAGE="${arg#TEST_COVERAGE=}" ;;
        PYTHON=*)   PYTHON="${arg#PYTHON=}" ;;
    esac
done

if [ -z "${HEADERS:-}" ]; then
    echo "错误：请指定头文件目录或 .h 文件" >&2
    echo "用法：bash translate.sh HEADERS=/path/to/include" >&2
    exit 1
fi

echo "=== c2rust-migration-skill translate (Phase 1) ==="
echo "头文件路径：$HEADERS"
echo "Spec v1 输出：$SPEC_OUT"
echo "报告输出：$REPORT_OUT"
echo ""

# Step 1：扫描头文件，生成 Spec v1
echo "--- Step 1：扫描 C 头文件 → Spec v1 ---"
"$PYTHON" "$SCRIPT_DIR/scan_headers.py" \
    "$HEADERS" \
    --recursive \
    --output "$SPEC_OUT"
echo "Spec v1 已写入：$SPEC_OUT"
echo ""

# Step 2：生成迁移分析报告
echo "--- Step 2：生成迁移分析报告 ---"
"$PYTHON" "$SCRIPT_DIR/generate_report.py" \
    "$SPEC_OUT" \
    --output "$REPORT_OUT" \
    --test-coverage "$TEST_COVERAGE"
echo "报告已写入：$REPORT_OUT"
echo ""

echo "=== Phase 1 前置工作完成 ==="
echo ""
echo "后续人工确认步骤（详见报告与 README.md）："
echo "  ⚠ 确认点 1：审查风险信号，填写处置策略"
echo "  ⚠ 确认点 2：完成 ABI/FFI 冻结清单（templates/abi-freeze-checklist.md）"
echo "  ⚠ 确认点 3：确认差分测试分级（templates/compatibility-validation-plan.md）"
echo "  ⚠ 确认点 4：完成 Rust FFI 层实现后，执行 Phase 1 验收（templates/phase1-acceptance-criteria.md）"
