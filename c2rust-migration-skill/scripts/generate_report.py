#!/usr/bin/env python3
"""
generate_report.py — 迁移分析报告生成器

用途：
    读取 scan_headers.py 生成的 spec-v1.yml，
    分析风险信号和接口特征，输出：
      1. 北向接口清单（摘要）
      2. 风险信号清单（需人工确认的 TODO 项）
      3. 差分测试分级建议（Tier 0 / 1 / 2）
      4. Phase 1 实施建议（优先接口顺序）

使用示例：
    python generate_report.py spec-v1.yml
    python generate_report.py spec-v1.yml --output report.md
    python generate_report.py spec-v1.yml --test-coverage 0.65

输出：
    Markdown 格式的迁移分析报告
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────────────────────────
# YAML loader (stdlib only)
# ──────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> Any:
    """
    Load a YAML file.
    Prefers PyYAML if available; otherwise falls back to a minimal
    line-by-line loader that handles the output of scan_headers.py.
    """
    try:
        import yaml  # type: ignore[import]
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except ImportError:
        pass

    # Minimal fallback: only sufficient to read the structure produced
    # by scan_headers.py (scalars + nested dicts/lists with 2-space indent).
    lines = path.read_text(encoding="utf-8").splitlines()
    return _minimal_yaml_parse(lines)


def _minimal_yaml_parse(lines: list[str]) -> Any:
    """
    Very limited YAML parser.  Handles:
      - key: scalar
      - key:
          nested: ...
      - - list items
    Only suitable for reading scan_headers.py output.
    """
    # Strip comments and blank lines for index building
    idx = 0

    def parse_value(line_rest: str, indent: int) -> tuple[Any, int]:
        nonlocal idx
        line_rest = line_rest.strip()
        if line_rest in ("", "null", "~"):
            return None, idx
        if line_rest == "[]":
            return [], idx
        if line_rest == "{}":
            return {}, idx
        if line_rest in ("true", "True", "yes"):
            return True, idx
        if line_rest in ("false", "False", "no"):
            return False, idx
        try:
            return int(line_rest), idx
        except ValueError:
            pass
        try:
            return float(line_rest), idx
        except ValueError:
            pass
        # Block scalar (|)
        if line_rest.startswith("|"):
            result_lines = []
            child_indent: int | None = None
            while idx < len(lines):
                line = lines[idx]
                stripped = line.lstrip()
                if not stripped:
                    result_lines.append("")
                    idx += 1
                    continue
                cur_indent = len(line) - len(stripped)
                if child_indent is None:
                    child_indent = cur_indent
                if cur_indent < child_indent:
                    break
                result_lines.append(line[child_indent:])
                idx += 1
            return "\n".join(result_lines), idx
        # Quoted string
        if (line_rest.startswith('"') and line_rest.endswith('"')) or \
           (line_rest.startswith("'") and line_rest.endswith("'")):
            return line_rest[1:-1], idx
        return line_rest, idx

    def parse_block(base_indent: int) -> Any:
        nonlocal idx
        result: dict | list | None = None

        while idx < len(lines):
            raw = lines[idx]
            if not raw.strip() or raw.strip().startswith("#"):
                idx += 1
                continue
            cur_indent = len(raw) - len(raw.lstrip())
            if cur_indent < base_indent:
                break

            stripped = raw.lstrip()

            # List item
            if stripped.startswith("- ") or stripped == "-":
                if result is None:
                    result = []
                if not isinstance(result, list):
                    break
                rest = stripped[2:].strip() if stripped.startswith("- ") else ""
                idx += 1
                if rest:
                    if ": " in rest:
                        # Inline dict start
                        item = {}
                        k, v = rest.split(": ", 1)
                        v = v.strip()
                        if v:
                            val, _ = parse_value(v, cur_indent + 2)
                            item[k] = val
                        else:
                            item[k] = parse_block(cur_indent + 2)
                        # Continue reading more keys at same level
                        while idx < len(lines):
                            nraw = lines[idx]
                            if not nraw.strip() or nraw.strip().startswith("#"):
                                idx += 1
                                continue
                            n_indent = len(nraw) - len(nraw.lstrip())
                            if n_indent <= cur_indent:
                                break
                            nstripped = nraw.lstrip()
                            if nstripped.startswith("- "):
                                break
                            if ": " in nstripped:
                                nk, nv = nstripped.split(": ", 1)
                                nv = nv.strip()
                                idx += 1
                                if nv:
                                    val2, _ = parse_value(nv, n_indent)
                                    item[nk] = val2
                                else:
                                    item[nk] = parse_block(n_indent + 2)
                            else:
                                idx += 1
                        result.append(item)
                    else:
                        val, _ = parse_value(rest, cur_indent + 2)
                        result.append(val)
                else:
                    item = parse_block(cur_indent + 2)
                    result.append(item if item is not None else {})
                continue

            # Dict entry
            if ": " in stripped or stripped.endswith(":"):
                if result is None:
                    result = {}
                if not isinstance(result, dict):
                    break
                if ": " in stripped:
                    k, v = stripped.split(": ", 1)
                    v = v.strip()
                else:
                    k = stripped.rstrip(":")
                    v = ""
                idx += 1
                if v:
                    val, _ = parse_value(v, cur_indent + 2)
                    result[k] = val
                else:
                    result[k] = parse_block(cur_indent + 2)
                continue

            idx += 1

        return result

    idx = 0
    return parse_block(0)


# ──────────────────────────────────────────────────────────────────
# Tier heuristics
# ──────────────────────────────────────────────────────────────────

TIER_DESCRIPTIONS = {
    0: "Tier 0 — 仅复用现有 C 测试（无额外差分测试）",
    1: "Tier 1 — Golden File 对比测试",
    2: "Tier 2 — 模糊测试 + 差分对比",
}


def _compute_tier(func: dict[str, Any], test_coverage: float) -> tuple[int, list[str]]:
    """
    Compute suggested diff-test tier for a function.
    Returns (tier, reasons).
    """
    risk_signals = func.get("risk_signals") or []
    risk_types = {r.get("type", "") for r in risk_signals}

    reasons: list[str] = []
    score = 0

    # Coverage-based baseline
    if test_coverage < 0.40:
        score += 2
        reasons.append(f"测试覆盖率较低（{test_coverage:.0%} < 40%）")
    elif test_coverage < 0.70:
        score += 1
        reasons.append(f"测试覆盖率中等（{test_coverage:.0%} < 70%）")
    else:
        reasons.append(f"测试覆盖率充足（{test_coverage:.0%} ≥ 70%）")

    # Risk signal scoring
    if "CALLBACK" in risk_types:
        score += 2
        reasons.append("检测到回调函数指针（调用时序复杂）")
    if "GLOBAL_STATE" in risk_types:
        score += 2
        reasons.append("检测到全局状态（init/deinit）")
    if "VARARGS" in risk_types:
        score += 2
        reasons.append("检测到可变参数（...）")
    if "OUT_BUF" in risk_types:
        score += 1
        reasons.append("检测到 out buffer 参数（输出需逐字节验证）")
    if "OPAQUE" in risk_types:
        score += 1
        reasons.append("检测到 void* 不透明指针（生命周期不明）")
    if "PLATFORM_TYPE" in risk_types:
        score += 1
        reasons.append("检测到平台相关类型（跨平台行为需验证）")

    # Complex parameter list
    params = func.get("params") or []
    if len(params) > 6:
        score += 1
        reasons.append(f"参数数量较多（{len(params)} 个）")

    if score == 0:
        tier = 0
    elif score <= 2:
        tier = 1
    else:
        tier = 2
    return tier, reasons


# ──────────────────────────────────────────────────────────────────
# Priority ordering heuristic
# ──────────────────────────────────────────────────────────────────

def _priority_score(func: dict[str, Any]) -> int:
    """
    Lower score = higher priority for Phase 1 implementation.
    Prefer simple, low-risk functions first.
    """
    risk_signals = func.get("risk_signals") or []
    risk_types = {r.get("type", "") for r in risk_signals}
    params = func.get("params") or []

    penalty = 0
    penalty += len(risk_signals) * 2
    penalty += len(params)
    if "CALLBACK" in risk_types:
        penalty += 5
    if "GLOBAL_STATE" in risk_types:
        penalty += 4
    if "VARARGS" in risk_types:
        penalty += 6
    return penalty


# ──────────────────────────────────────────────────────────────────
# Report builder
# ──────────────────────────────────────────────────────────────────

def _build_report(
    spec: dict[str, Any],
    test_coverage: float,
    source_path: Path,
) -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = spec.get("metadata") or {}
    project = meta.get("project") or "未知项目"
    functions: list[dict[str, Any]] = spec.get("functions") or []
    types: list[dict[str, Any]] = spec.get("types") or []

    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────────
    lines += [
        f"# C→Rust 迁移分析报告：{project}",
        "",
        f"> **生成时间**：{now}  ",
        f"> **输入文件**：`{source_path}`  ",
        f"> **测试覆盖率输入**：{test_coverage:.0%}（用户提供的估算值）  ",
        "> **注意**：本报告由工具自动生成，所有建议须经人工确认后方可执行。",
        "",
    ]

    # ── Summary ───────────────────────────────────────────────────
    total_risks = sum(len(f.get("risk_signals") or []) for f in functions)
    tier_counts = {0: 0, 1: 0, 2: 0}
    for f in functions:
        tier, _ = _compute_tier(f, test_coverage)
        tier_counts[tier] += 1

    lines += [
        "## 摘要",
        "",
        f"| 指标 | 数量 |",
        f"|---|---|",
        f"| 北向函数 | {len(functions)} |",
        f"| 类型定义（struct/enum/typedef）| {len(types)} |",
        f"| 风险信号（需人工确认） | {total_risks} |",
        f"| 建议 Tier 0 接口数 | {tier_counts[0]} |",
        f"| 建议 Tier 1 接口数 | {tier_counts[1]} |",
        f"| 建议 Tier 2 接口数 | {tier_counts[2]} |",
        "",
    ]

    # ── Interface list ─────────────────────────────────────────────
    lines += [
        "## 北向接口清单",
        "",
        "| 函数名 | 参数数 | 风险信号 | 建议 Tier | 建议优先级 |",
        "|---|---|---|---|---|",
    ]

    sorted_funcs = sorted(functions, key=_priority_score)
    for rank, func in enumerate(sorted_funcs, 1):
        name = func.get("name") or "unknown"
        params = func.get("params") or []
        risks = func.get("risk_signals") or []
        risk_str = ", ".join({r.get("type", "") for r in risks}) if risks else "无"
        tier, _ = _compute_tier(func, test_coverage)
        lines.append(f"| `{name}` | {len(params)} | {risk_str} | Tier {tier} | #{rank} |")

    lines += ["", "---", ""]

    # ── Risk signal details ────────────────────────────────────────
    lines += [
        "## ⚠ 风险信号清单（需人工确认）",
        "",
        "> 每个风险信号代表一个潜在的迁移难点，需要在 Phase 1 实施前明确处置策略。",
        "",
    ]

    todo_counter = 0
    for func in functions:
        risks = func.get("risk_signals") or []
        if not risks:
            continue
        func_name = func.get("name") or "unknown"
        lines += [f"### `{func_name}`", ""]
        for risk in risks:
            todo_counter += 1
            rtype = risk.get("type") or "UNKNOWN"
            detail = risk.get("detail") or ""
            lines += [
                f"**[ TODO-{todo_counter:03d} ]** `[RISK: {rtype}]` {detail}",
                "",
                "需确认以下问题（根据 rtype 不同）：",
            ]
            if rtype == "CALLBACK":
                lines += [
                    "- [ ] 回调在哪个线程调用？",
                    "- [ ] 是否允许重入？",
                    "- [ ] 回调函数指针的生命周期由谁持有？",
                    "- [ ] `user_data` 如何传递与释放？",
                ]
            elif rtype == "OUT_BUF":
                lines += [
                    "- [ ] 谁负责分配 out buffer？",
                    "- [ ] buffer 最大长度单位（字节 / 元素数）？",
                    "- [ ] 失败时是否写入 buffer？",
                ]
            elif rtype == "GLOBAL_STATE":
                lines += [
                    "- [ ] 是否为单例（多次调用行为）？",
                    "- [ ] init/deinit 的线程安全性？",
                    "- [ ] Rust 侧是否需要 `std::sync::Once` 保护？",
                ]
            elif rtype == "OPAQUE":
                lines += [
                    "- [ ] `void*` 指向的实际类型是什么？",
                    "- [ ] 生命周期由谁管理？",
                    "- [ ] Rust 侧如何映射（`*mut c_void` vs newtype handle）？",
                ]
            elif rtype == "VARARGS":
                lines += [
                    "- [ ] Rust 侧是否需要提供镜像实现？",
                    "- [ ] 若不需要，是否可以包装为固定签名版本？",
                ]
            elif rtype == "PLATFORM_TYPE":
                lines += [
                    "- [ ] 目标平台是否包含 32 位环境？",
                    "- [ ] 类型宽度策略：`usize`/`isize` 还是固定宽度（`u64`/`i64`）？",
                ]

            decision = risk.get("decision") or "TODO"
            lines += [
                "",
                f"**处置决策**：{decision}",
                "",
            ]

    if todo_counter == 0:
        lines += ["*未检测到风险信号。*", ""]

    lines += ["---", ""]

    # ── Tier recommendations ───────────────────────────────────────
    lines += [
        "## 差分测试分级建议",
        "",
        "> ⚠ **人工确认点 3**：下表的「选定 Tier」栏由负责人填写并签字后，填入 `templates/compatibility-validation-plan.md`。",
        "",
        "| 函数名 | 建议 Tier | 建议理由摘要 | 选定 Tier（人工填写） |",
        "|---|---|---|---|",
    ]

    for func in functions:
        name = func.get("name") or "unknown"
        tier, reasons = _compute_tier(func, test_coverage)
        reason_summary = reasons[0] if reasons else "无风险信号"
        lines.append(
            f"| `{name}` | **Tier {tier}** | {reason_summary} | TODO |"
        )

    lines += ["", "---", ""]

    # ── Phase 1 implementation priority ───────────────────────────
    lines += [
        "## Phase 1 实施顺序建议",
        "",
        "> 按风险从低到高排序；建议优先实现低风险接口，建立信心后再攻关高风险接口。",
        "",
    ]

    for rank, func in enumerate(sorted_funcs, 1):
        name = func.get("name") or "unknown"
        tier, reasons = _compute_tier(func, test_coverage)
        risks = func.get("risk_signals") or []
        risk_summary = "无风险信号" if not risks else f"{len(risks)} 个风险信号"
        lines += [
            f"### #{rank}. `{name}`（Tier {tier}）",
            "",
            f"**风险摘要**：{risk_summary}",
        ]
        if reasons:
            lines.append("")
            for r in reasons[:3]:
                lines.append(f"- {r}")
        lines.append("")

    # ── Type inventory ─────────────────────────────────────────────
    if types:
        lines += [
            "## 类型定义清单",
            "",
            "| 类型名 | Kind | 需 `#[repr(C)]` |",
            "|---|---|---|",
        ]
        for t in types:
            name = t.get("name") or "unknown"
            kind = t.get("kind") or "unknown"
            needs_repr = "✓" if kind in ("struct", "union") else "—"
            lines.append(f"| `{name}` | {kind} | {needs_repr} |")
        lines += ["", "---", ""]

    # ── Next steps ─────────────────────────────────────────────────
    lines += [
        "## 建议的后续步骤",
        "",
        "1. **[ ⚠ 人工确认点 1 ]** 审查上方风险信号清单，为每个 TODO 填写处置决策。",
        "2. 基于确认结果，补全 `spec-v1.yml` 中各函数的行为契约字段。",
        "3. **[ ⚠ 人工确认点 2 ]** 完成 `templates/abi-freeze-checklist.md` 并签字冻结。",
        "4. **[ ⚠ 人工确认点 3 ]** 确认上方差分测试分级表，填入 `templates/compatibility-validation-plan.md`。",
        "5. 按 `README.md` Step 5 开始 Rust FFI 层实现（参考 `r2rust-ffi-creator/SKILL.md`）。",
        "6. 实现完成后，执行 `templates/phase1-acceptance-criteria.md` 验收检查。",
        "",
    ]

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="生成 C→Rust 迁移分析报告（差分测试分级 + 风险信号 + 优先级）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "spec_file",
        help="scan_headers.py 生成的 spec-v1.yml 文件路径",
    )
    parser.add_argument(
        "--output", "-o",
        default="report.md",
        help="输出 Markdown 报告路径（默认：report.md）",
    )
    parser.add_argument(
        "--test-coverage",
        type=float,
        default=0.5,
        metavar="RATIO",
        help="现有 C 测试覆盖率估算（0.0~1.0，默认：0.5）。影响差分测试分级建议。",
    )
    args = parser.parse_args()

    spec_path = Path(args.spec_file)
    if not spec_path.exists():
        print(f"错误：{spec_path} 不存在", file=sys.stderr)
        return 1

    coverage = max(0.0, min(1.0, args.test_coverage))

    print(f"加载 {spec_path}...", file=sys.stderr)
    spec = _load_yaml(spec_path)

    if not isinstance(spec, dict):
        print(f"错误：{spec_path} 不是有效的 YAML 字典", file=sys.stderr)
        return 1

    functions = spec.get("functions") or []
    print(
        f"分析 {len(functions)} 个函数（测试覆盖率估算：{coverage:.0%}）...",
        file=sys.stderr,
    )

    report = _build_report(spec, coverage, spec_path)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"报告已写入：{output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
