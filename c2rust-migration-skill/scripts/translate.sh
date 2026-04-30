#!/usr/bin/env bash
# translate.sh — Phase 1：位级兼容 Rust 替代（C→Rust 翻译阶段）
#
# 执行 c2rust-migration-skill 的第一阶段工作流：
#   Step 0: 分析 C 项目构建系统、源文件实现、导出符号、测试结构（须人工确认后才能继续）
#   Step 1: 扫描 C 头文件，生成 Spec v1（as-is）
#   Step 2: 生成迁移分析报告（风险信号 + 差分测试分级建议）
#
# 使用方法：
#   bash translate.sh PROJECT=<C项目根目录> HEADERS=<头文件目录或.h文件>
#   bash translate.sh PROJECT=<路径> HEADERS=<路径> BINARY=<已构建库路径> SPEC_OUT=<spec输出路径> REPORT_OUT=<报告输出路径>
#
# 环境变量（均可通过命令行 KEY=VALUE 传入）：
#   PROJECT        — C 项目根目录（必须，用于 Step 0 完整分析）
#   HEADERS        — 头文件目录或单个 .h 文件（必须，用于 Step 1 扫描）
#   BINARY         — 已构建的 C 库二进制文件路径（可选，用于 Step 0 符号提取）
#   ANALYSIS_OUT   — Step 0 分析报告输出路径（默认：c-project-analysis.md）
#   SPEC_OUT       — Spec v1 YAML 输出路径（默认：spec-v1.yml）
#   REPORT_OUT     — 迁移分析报告输出路径（默认：report.md）
#   TEST_COVERAGE  — 现有 C 测试覆盖率估算 0.0~1.0（默认：0.5，建议从 Step 0 结果中获取）
#   SKIP_STEP0     — 设为 "1" 可跳过 Step 0（仅在已有确认的分析报告时使用）
#   PYTHON         — Python 解释器（默认：python3）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
ANALYSIS_OUT="${ANALYSIS_OUT:-c-project-analysis.md}"
SPEC_OUT="${SPEC_OUT:-spec-v1.yml}"
REPORT_OUT="${REPORT_OUT:-report.md}"
TEST_COVERAGE="${TEST_COVERAGE:-0.5}"
SKIP_STEP0="${SKIP_STEP0:-0}"

# 解析 KEY=VALUE 参数
for arg in "$@"; do
    case "$arg" in
        PROJECT=*)      PROJECT="${arg#PROJECT=}" ;;
        HEADERS=*)      HEADERS="${arg#HEADERS=}" ;;
        BINARY=*)       BINARY="${arg#BINARY=}" ;;
        ANALYSIS_OUT=*) ANALYSIS_OUT="${arg#ANALYSIS_OUT=}" ;;
        SPEC_OUT=*)     SPEC_OUT="${arg#SPEC_OUT=}" ;;
        REPORT_OUT=*)   REPORT_OUT="${arg#REPORT_OUT=}" ;;
        TEST_COVERAGE=*) TEST_COVERAGE="${arg#TEST_COVERAGE=}" ;;
        SKIP_STEP0=*)   SKIP_STEP0="${arg#SKIP_STEP0=}" ;;
        PYTHON=*)       PYTHON="${arg#PYTHON=}" ;;
    esac
done

if [ -z "${HEADERS:-}" ]; then
    echo "错误：请指定头文件目录或 .h 文件（HEADERS=...）" >&2
    echo "用法：bash translate.sh PROJECT=/path/to/project HEADERS=/path/to/include" >&2
    exit 1
fi

if [ "$SKIP_STEP0" != "1" ] && [ -z "${PROJECT:-}" ]; then
    echo "错误：Step 0 分析需要 C 项目根目录（PROJECT=...）" >&2
    echo "用法：bash translate.sh PROJECT=/path/to/project HEADERS=/path/to/include" >&2
    echo "提示：若已完成 Step 0，可加 SKIP_STEP0=1 跳过此校验" >&2
    exit 1
fi

echo "=== c2rust-migration-skill translate (Phase 1) ==="
echo "C 项目根目录：${PROJECT:-（未指定，仅在 SKIP_STEP0=1 时有效）}"
echo "头文件路径：$HEADERS"
echo "Step 0 分析报告：$ANALYSIS_OUT"
echo "Spec v1 输出：$SPEC_OUT"
echo "报告输出：$REPORT_OUT"
echo ""

# ──────────────────────────────────────────────────────────────────
# Step 0：C 项目完整分析（构建系统 + 符号 + 测试 + 实现依赖）
# ──────────────────────────────────────────────────────────────────
if [ "$SKIP_STEP0" = "1" ]; then
    echo "--- Step 0：已跳过（SKIP_STEP0=1） ---"
    echo "⚠  警告：跳过 Step 0 意味着你已有经过签字确认的 c-project-analysis.md。"
    echo "   若尚未完成 Step 0 的人工确认，请先补完后再继续。"
    echo ""
else
    echo "--- Step 0：C 项目完整分析 ---"
    STEP0_ARGS="$PROJECT"
    if [ -n "${BINARY:-}" ]; then
        "$PYTHON" "$SCRIPT_DIR/analyze_c_project.py" \
            "$STEP0_ARGS" \
            --headers "$HEADERS" \
            --binary "$BINARY" \
            --output "$ANALYSIS_OUT"
    else
        "$PYTHON" "$SCRIPT_DIR/analyze_c_project.py" \
            "$STEP0_ARGS" \
            --headers "$HEADERS" \
            --output "$ANALYSIS_OUT"
    fi
    echo "Step 0 分析报告已写入：$ANALYSIS_OUT"
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ⚠  人工确认点 0 —— 阻断门                                  ║"
    echo "║                                                              ║"
    echo "║  在继续之前，请完成以下操作：                                 ║"
    echo "║  1. 打开 $ANALYSIS_OUT"
    echo "║  2. 逐节核查并补全所有 TODO 项，重点确认：                    ║"
    echo "║     a. 已实际构建 C 产物并用 nm/objdump 提取导出符号          ║"
    echo "║     b. 已运行现有测试并记录覆盖情况                           ║"
    echo "║     c. 每个北向函数的实现依赖（调用链/数据类型）已梳理         ║"
    echo "║  3. 在文末「⚠ 人工确认点 0」签字，将状态改为「已完成」        ║"
    echo "║                                                              ║"
    echo "║  签字完成后，重新运行：                                       ║"
    echo "║  bash translate.sh ... SKIP_STEP0=1                          ║"
    echo "║  继续 Step 1 和 Step 2。                                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    exit 0
fi

# ──────────────────────────────────────────────────────────────────
# Step 1：扫描头文件，生成 Spec v1
# ──────────────────────────────────────────────────────────────────
echo "--- Step 1：扫描 C 头文件 → Spec v1 ---"
"$PYTHON" "$SCRIPT_DIR/scan_headers.py" \
    "$HEADERS" \
    --recursive \
    --output "$SPEC_OUT"
echo "Spec v1 已写入：$SPEC_OUT"
echo ""

# ──────────────────────────────────────────────────────────────────
# Step 2：生成迁移分析报告
# ──────────────────────────────────────────────────────────────────
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
echo "  ⚠ 确认点 1a：符号对账——将 nm/objdump 结果与 scan_headers.py 的头文件声明逐行 diff"
echo "  　　           填写 templates/abi-freeze-checklist.md 第 2.1~2.2 节，差异全部清零后签字"
echo "  ⚠ 确认点 1：审查风险信号，填写处置策略（$REPORT_OUT）"
echo "  ⚠ 确认点 2：完成 ABI/FFI 冻结清单（templates/abi-freeze-checklist.md，须与符号对账结果一致）"
echo "  ⚠ 确认点 3：确认差分测试分级（templates/compatibility-validation-plan.md）"
echo "  ⚠ 确认点 4：完成 Rust FFI 层实现后，执行 Phase 1 验收（templates/phase1-acceptance-criteria.md）"
echo ""
echo "注意：以上每个确认点均为阻断门，须签字完成后方可推进至下一步。"
