#!/usr/bin/env python3
"""
scan_headers.py — C 头文件扫描器

用途：
    枚举指定目录中的 C 头文件，提取函数声明、结构体定义和 typedef，
    生成符合 templates/spec-v1-extraction.yml 格式的初始骨架文件。

解析策略：
    1. 若安装了 libclang Python 绑定（pip install libclang），优先使用 AST 解析（精准）。
    2. 否则自动降级为正则表达式解析（best-effort，无法处理复杂宏展开）。
       降级时会在输出文件中添加醒目警告。

使用示例：
    python scan_headers.py /path/to/include --output spec-v1.yml
    python scan_headers.py /path/to/include --output spec-v1.yml --force-regex
    python scan_headers.py /path/to/include --recursive --output spec-v1.yml

输出：
    符合 templates/spec-v1-extraction.yml 骨架的 YAML 文件，
    所有需要人工补全的字段标注 TODO，
    检测到的风险信号自动填入 risk_signals 字段。
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────────────────────────
# Risk signal detection patterns
# ──────────────────────────────────────────────────────────────────

RISK_PATTERNS: list[tuple[str, str, str]] = [
    # (risk_type, description, regex_pattern_for_function_text)
    ("CALLBACK",
     "函数包含函数指针参数（回调）",
     r"\(\s*\*\s*\w+\s*\)"),
    ("OUT_BUF",
     "函数包含 out buffer 参数（指针+长度或双重指针）",
     r"\b\w+\s*\*\s*\*\s*\w+|\b\w+\s*\*\s+\w*out\w*|\b\w+\s*\*\s+\w*buf\w*|\b\w+\s*\*\s+\w*result\w*"),
    ("GLOBAL_STATE",
     "函数名暗示全局初始化或反初始化",
     r"\b(?:init|deinit|initialize|finalize|startup|shutdown)\b|global_"),
    ("OPAQUE",
     "函数使用 void* 不透明指针",
     r"\bvoid\s*\*"),
    ("VARARGS",
     "函数使用可变参数（...）",
     r"\.\.\.\s*\)"),
    ("PLATFORM_TYPE",
     "函数使用平台相关类型（long, size_t, ssize_t, ptrdiff_t）",
     r"\b(?:long|size_t|ssize_t|ptrdiff_t|uintptr_t|intptr_t)\b"),
]


def _detect_risk_signals(text: str) -> list[dict[str, Any]]:
    """Detect risk signals in a function signature or declaration text."""
    signals = []
    for risk_type, description, pattern in RISK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            signals.append({
                "type": risk_type,
                "detail": description,
                "confirmed": False,
                "decision": "TODO: 接受 / 需额外封装 / 延迟到 Phase 2",
            })
    return signals


# ──────────────────────────────────────────────────────────────────
# YAML helpers (no external dependency)
# ──────────────────────────────────────────────────────────────────

def _indent(text: str, level: int) -> str:
    prefix = "  " * level
    return "\n".join(prefix + line if line.strip() else line for line in text.splitlines())


def _yaml_str(value: str, indent: int = 0) -> str:
    """Produce a YAML string scalar, using block style for multi-line values."""
    if "\n" in value:
        lines = ["|\n"] + [("  " * (indent + 1)) + line for line in value.splitlines()]
        return "".join(lines)
    # Escape if needed
    if any(c in value for c in ('"', "'", ":", "#", "{", "}", "[", "]", "&", "*", "!")):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value if value else '""'


def _emit_yaml(data: Any, indent: int = 0, key: str | None = None) -> str:
    """Minimal recursive YAML emitter for our specific data shapes."""
    pad = "  " * indent
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                if isinstance(v, list) and len(v) == 0:
                    lines.append(f"{pad}{k}: []")
                elif isinstance(v, dict) and len(v) == 0:
                    lines.append(f"{pad}{k}: {{}}")
                else:
                    lines.append(f"{pad}{k}:")
                    lines.append(_emit_yaml(v, indent + 1))
            elif isinstance(v, bool):
                lines.append(f"{pad}{k}: {'true' if v else 'false'}")
            elif isinstance(v, (int, float)):
                lines.append(f"{pad}{k}: {v}")
            elif v is None:
                lines.append(f"{pad}{k}: null")
            else:
                sv = str(v)
                if "\n" in sv:
                    lines.append(f"{pad}{k}: |")
                    for sl in sv.splitlines():
                        lines.append(f"{pad}  {sl}")
                else:
                    lines.append(f"{pad}{k}: {_yaml_str(sv)}")
        return "\n".join(lines)
    elif isinstance(data, list):
        if not data:
            return f"{pad}[]"
        lines = []
        for item in data:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    prefix = f"{pad}- " if first else f"{pad}  "
                    first = False
                    if isinstance(v, (dict, list)):
                        lines.append(f"{prefix}{k}:")
                        lines.append(_emit_yaml(v, indent + 2))
                    elif isinstance(v, bool):
                        lines.append(f"{prefix}{k}: {'true' if v else 'false'}")
                    elif isinstance(v, (int, float)):
                        lines.append(f"{prefix}{k}: {v}")
                    elif v is None:
                        lines.append(f"{prefix}{k}: null")
                    else:
                        sv = str(v)
                        if "\n" in sv:
                            lines.append(f"{prefix}{k}: |")
                            for sl in sv.splitlines():
                                lines.append(f"{pad}    {sl}")
                        else:
                            lines.append(f"{prefix}{k}: {_yaml_str(sv)}")
            else:
                lines.append(f"{pad}- {_yaml_str(str(item))}")
        return "\n".join(lines)
    else:
        return f"{pad}{_yaml_str(str(data))}"


# ──────────────────────────────────────────────────────────────────
# Regex-based parser (fallback)
# ──────────────────────────────────────────────────────────────────

# Matches function declarations: type name(params);
# Handles one level of nested parentheses (e.g. callback typedefs like
# void (*on_done)(int, void*)).  Applied to whitespace-normalised single lines.
_FUNC_RE = re.compile(
    r"(?:(?:static|inline|__inline__|extern)\s+)*"
    r"([\w][\w\s\*]*?)\s+"                           # return type (non-greedy)
    r"(\w+)\s*"                                       # function name
    r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*;"          # params with 1-level nested parens
)

# Matches struct definitions: struct Name { ... };
_STRUCT_RE = re.compile(
    r"(?:typedef\s+)?struct\s+(\w*)\s*\{([^}]*)\}\s*(\w+)?\s*;",
    re.DOTALL,
)

# Matches simple typedefs: typedef type alias;
_TYPEDEF_RE = re.compile(
    r"typedef\s+([\w\s\*]+?)\s+(\w+)\s*;",
)

# Matches enum definitions
_ENUM_RE = re.compile(
    r"(?:typedef\s+)?enum\s+(\w*)\s*\{([^}]*)\}\s*(\w+)?\s*;",
    re.DOTALL,
)


def _strip_comments(text: str) -> str:
    """Remove C/C++ comments."""
    # Remove block comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    # Remove line comments
    text = re.sub(r"//[^\n]*", "", text)
    return text


def _parse_params_regex(params_str: str) -> list[dict[str, Any]]:
    """Parse parameter list into structured dicts (best-effort)."""
    params_str = params_str.strip()
    if not params_str or params_str in ("void", ""):
        return []

    params = []
    # Split on commas not inside parentheses
    depth = 0
    current = []
    for ch in params_str:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            params.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        params.append("".join(current).strip())

    result = []
    for p in params:
        p = p.strip()
        if not p or p == "...":
            if p == "...":
                result.append({
                    "name": "...",
                    "c_type": "...",
                    "rust_type": "TODO",
                    "nullable": False,
                    "direction": "in",
                    "ownership": "TODO",
                    "length_field": "",
                    "notes": "可变参数，需人工评估",
                })
            continue
        # Try to split type and name
        tokens = p.rsplit(None, 1)
        if len(tokens) == 2:
            c_type = tokens[0].strip().rstrip("*").strip()
            stars = tokens[0].count("*")
            name = tokens[1].lstrip("*").strip()
            c_type_full = tokens[0].strip()
        else:
            c_type_full = p
            c_type = p
            name = "TODO"
            stars = p.count("*")

        nullable = "*" in c_type_full
        direction = "out" if ("**" in c_type_full or re.search(r"\*\s*\*", c_type_full)) else "in"

        result.append({
            "name": name,
            "c_type": c_type_full,
            "rust_type": "TODO",
            "nullable": nullable,
            "direction": direction,
            "ownership": "TODO",
            "length_field": "",
            "notes": "",
        })
    return result


def _parse_headers_regex(header_files: list[Path]) -> dict[str, Any]:
    """Parse headers using regex fallback. Returns raw extracted data."""
    functions: list[dict[str, Any]] = []
    types: list[dict[str, Any]] = []

    for hfile in header_files:
        try:
            text = hfile.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"  [WARN] Cannot read {hfile}: {e}", file=sys.stderr)
            continue

        clean = _strip_comments(text)

        # Extract structs
        for m in _STRUCT_RE.finditer(clean):
            struct_tag = m.group(1) or ""
            body = m.group(2)
            typedef_name = m.group(3) or struct_tag
            if not typedef_name:
                continue
            fields = []
            for line in body.splitlines():
                line = line.strip().rstrip(";").strip()
                if line:
                    fields.append({
                        "name": "TODO",
                        "c_type": line,
                        "rust_type": "TODO",
                        "size_bytes": "TODO",
                        "offset_bytes": "TODO",
                        "notes": "",
                    })
            types.append({
                "name": typedef_name,
                "kind": "struct",
                "c_definition": m.group(0).strip(),
                "rust_repr": "#[repr(C)]",
                "fields": fields,
                "notes": "",
            })

        # Extract enums
        for m in _ENUM_RE.finditer(clean):
            enum_tag = m.group(1) or ""
            typedef_name = m.group(3) or enum_tag
            if not typedef_name:
                continue
            types.append({
                "name": typedef_name,
                "kind": "enum",
                "c_definition": m.group(0).strip(),
                "rust_repr": "#[repr(i32)]",
                "fields": [],
                "notes": "TODO: 确认底层类型",
            })

        # Extract simple typedefs (not struct/enum)
        for m in _TYPEDEF_RE.finditer(clean):
            orig_type = m.group(1).strip()
            alias = m.group(2).strip()
            if orig_type.startswith("struct") or orig_type.startswith("enum"):
                continue
            types.append({
                "name": alias,
                "kind": "typedef",
                "c_definition": f"typedef {orig_type} {alias};",
                "rust_repr": "",
                "fields": [],
                "notes": "",
            })

        # Extract function declarations.
        # First, join continuation lines (multi-line parameter lists) into
        # single lines by tracking open-paren depth, then normalise spaces.
        joined_lines: list[str] = []
        buf: list[str] = []
        paren_depth = 0
        for raw_line in clean.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                if not buf:
                    continue
            paren_depth += stripped.count("(") - stripped.count(")")
            buf.append(stripped)
            if paren_depth <= 0:
                joined_lines.append(re.sub(r"\s+", " ", " ".join(buf)).strip())
                buf = []
                paren_depth = 0
        if buf:
            joined_lines.append(re.sub(r"\s+", " ", " ".join(buf)).strip())
        normalized = "\n".join(joined_lines)

        for m in _FUNC_RE.finditer(normalized):
            ret_type = m.group(1).strip()
            func_name = m.group(2).strip()
            params_str = m.group(3).strip()

            # Skip obviously non-function patterns
            if func_name in ("if", "while", "for", "switch", "return"):
                continue

            full_sig = f"{ret_type} {func_name}({params_str});"
            params = _parse_params_regex(params_str)
            risks = _detect_risk_signals(full_sig + " " + params_str)

            functions.append({
                "name": func_name,
                "header_file": str(hfile),
                "c_signature": full_sig,
                "params": params,
                "return": {
                    "c_type": ret_type,
                    "rust_type": "TODO",
                    "error_codes": [
                        {"value": 0, "meaning": "成功（假设）"},
                        {"value": -1, "meaning": "TODO: 填写错误码含义"},
                    ],
                    "notes": "",
                },
                "contract": {
                    "preconditions": [],
                    "postconditions": [],
                    "error_behavior": "TODO",
                    "idempotent": False,
                },
                "memory": {
                    "allocator": "TODO",
                    "deallocated_by": "TODO",
                    "notes": "",
                },
                "concurrency": {
                    "thread_safe": False,
                    "reentrant": False,
                    "requires_external_lock": False,
                    "lock_notes": "",
                },
                "callbacks": [],
                "global_state": {
                    "depends_on_init": False,
                    "init_function": "",
                    "modifies_global": False,
                    "notes": "",
                },
                "implementation_analysis": {
                    "source_file": "TODO: 实现此函数的 .c 文件路径（来自 c-project-analysis.md 第6节）",
                    "internal_callees": [
                        {
                            "name": "TODO: 被调用的内部函数名",
                            "source_file": "TODO: 所在 .c 文件",
                            "purpose": "TODO: 作用说明",
                        }
                    ],
                    "global_state_deps": [
                        {
                            "name": "TODO: 全局变量名",
                            "c_type": "TODO: C 类型",
                            "access": "read",
                            "thread_safety_notes": "TODO: 默认按 read 填充；需人工确认实际访问方式是否为 write/read_write，并补充线程安全影响",
                        }
                    ],
                    "logic_summary": ["TODO: 实现逻辑步骤 1", "TODO: 步骤 2"],
                    "conditional_compilation": [],
                    "notes": "",
                },
                "risk_signals": risks,
                "notes": "",
            })

    return {"functions": functions, "types": types}


# ──────────────────────────────────────────────────────────────────
# libclang-based parser (preferred)
# ──────────────────────────────────────────────────────────────────

def _try_import_clang() -> Any:
    """Try to import libclang bindings. Returns module or None."""
    try:
        import clang.cindex as ci  # type: ignore[import]
        return ci
    except ImportError:
        return None


def _clang_type_str(cursor_type: Any) -> str:
    return cursor_type.spelling if cursor_type else "unknown"


def _parse_headers_clang(header_files: list[Path], ci: Any) -> dict[str, Any]:
    """Parse headers using libclang AST (accurate)."""
    functions: list[dict[str, Any]] = []
    types: list[dict[str, Any]] = []

    index = ci.Index.create()

    for hfile in header_files:
        try:
            tu = index.parse(str(hfile), args=["-x", "c", "-std=c11"])
        except Exception as e:
            print(f"  [WARN] libclang failed on {hfile}: {e}", file=sys.stderr)
            continue

        if tu.diagnostics:
            for diag in tu.diagnostics:
                if diag.severity >= ci.Diagnostic.Error:
                    print(f"  [WARN] {hfile}: {diag.spelling}", file=sys.stderr)

        for cursor in tu.cursor.get_children():
            # Only process declarations from this specific file
            if cursor.location.file and Path(cursor.location.file.name) != hfile:
                continue

            if cursor.kind == ci.CursorKind.FUNCTION_DECL:
                func_name = cursor.spelling
                ret_type = _clang_type_str(cursor.result_type)
                params = []
                for arg in cursor.get_arguments():
                    param_type = _clang_type_str(arg.type)
                    param_name = arg.spelling or "unnamed"
                    nullable = "*" in param_type or "[" in param_type
                    direction = "out" if "**" in param_type else "in"
                    params.append({
                        "name": param_name,
                        "c_type": param_type,
                        "rust_type": "TODO",
                        "nullable": nullable,
                        "direction": direction,
                        "ownership": "TODO",
                        "length_field": "",
                        "notes": "",
                    })

                full_sig = cursor.type.spelling
                risks = _detect_risk_signals(full_sig)

                functions.append({
                    "name": func_name,
                    "header_file": str(hfile),
                    "c_signature": full_sig,
                    "params": params,
                    "return": {
                        "c_type": ret_type,
                        "rust_type": "TODO",
                        "error_codes": [
                            {"value": 0, "meaning": "成功（假设）"},
                            {"value": -1, "meaning": "TODO: 填写错误码含义"},
                        ],
                        "notes": "",
                    },
                    "contract": {
                        "preconditions": [],
                        "postconditions": [],
                        "error_behavior": "TODO",
                        "idempotent": False,
                    },
                    "memory": {
                        "allocator": "TODO",
                        "deallocated_by": "TODO",
                        "notes": "",
                    },
                    "concurrency": {
                        "thread_safe": False,
                        "reentrant": False,
                        "requires_external_lock": False,
                        "lock_notes": "",
                    },
                    "callbacks": [],
                    "global_state": {
                        "depends_on_init": False,
                        "init_function": "",
                        "modifies_global": False,
                        "notes": "",
                    },
                    "implementation_analysis": {
                        "source_file": "TODO: 实现此函数的 .c 文件路径（来自 c-project-analysis.md 第6节）",
                        "internal_callees": [
                            {
                                "name": "TODO: 被调用的内部函数名",
                                "source_file": "TODO: 所在 .c 文件",
                                "purpose": "TODO: 作用说明",
                            }
                        ],
                        "global_state_deps": [
                            {
                                "name": "TODO: 全局变量名",
                                "c_type": "TODO: C 类型",
                                "access": "read",
                                "thread_safety_notes": "TODO: 确认实际访问方式（read/write/read_write）及线程安全影响",
                            }
                        ],
                        "logic_summary": ["TODO: 实现逻辑步骤 1", "TODO: 步骤 2"],
                        "conditional_compilation": [],
                        "notes": "",
                    },
                    "risk_signals": risks,
                    "notes": "",
                })

            elif cursor.kind in (ci.CursorKind.STRUCT_DECL, ci.CursorKind.TYPEDEF_DECL):
                type_name = cursor.spelling
                if not type_name:
                    continue
                kind = "struct" if cursor.kind == ci.CursorKind.STRUCT_DECL else "typedef"
                fields = []
                if cursor.kind == ci.CursorKind.STRUCT_DECL:
                    for field in cursor.get_children():
                        if field.kind == ci.CursorKind.FIELD_DECL:
                            field_size = field.type.get_size()
                            fields.append({
                                "name": field.spelling,
                                "c_type": _clang_type_str(field.type),
                                "rust_type": "TODO",
                                "size_bytes": field_size if field_size > 0 else "TODO",
                                "offset_bytes": "TODO",
                                "notes": "",
                            })
                types.append({
                    "name": type_name,
                    "kind": kind,
                    "c_definition": f"/* see header: {hfile} */",
                    "rust_repr": "#[repr(C)]",
                    "fields": fields,
                    "notes": "",
                })

            elif cursor.kind == ci.CursorKind.ENUM_DECL:
                enum_name = cursor.spelling
                if not enum_name:
                    continue
                types.append({
                    "name": enum_name,
                    "kind": "enum",
                    "c_definition": f"/* see header: {hfile} */",
                    "rust_repr": "#[repr(i32)]",
                    "fields": [],
                    "notes": "TODO: 确认底层类型",
                })

    return {"functions": functions, "types": types}


# ──────────────────────────────────────────────────────────────────
# Output builder
# ──────────────────────────────────────────────────────────────────

def _build_output(
    data: dict[str, Any],
    header_files: list[Path],
    used_clang: bool,
) -> str:
    today = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d")

    lines: list[str] = []

    lines.append("# Spec v1 (as-is) — 由 scan_headers.py 自动生成")
    lines.append("#")
    lines.append(f"# 生成时间: {today}")
    if not used_clang:
        lines.append("#")
        lines.append("# ⚠ 警告：libclang 不可用，使用正则解析（降级模式）。")
        lines.append("#   解析结果可能不完整，尤其对于宏展开的类型。")
        lines.append("#   建议安装 libclang：pip install libclang")
    lines.append("#")
    lines.append("# 请人工逐字段补全行为契约，将 TODO 替换为实际信息。")
    lines.append("")

    meta: dict[str, Any] = {
        "metadata": {
            "project": "TODO: 填写 C 项目名称",
            "version": "TODO: 填写被分析的版本号或 commit",
            "extracted_by": "scan_headers.py (自动生成，需人工补全)",
            "extracted_at": today,
            "parser": "libclang" if used_clang else "regex (降级模式)",
            "headers_scanned": [str(h) for h in header_files],
            "notes": "",
        }
    }
    lines.append(_emit_yaml(meta))
    lines.append("")

    if data["types"]:
        lines.append(_emit_yaml({"types": data["types"]}))
    else:
        lines.append("types: []")
    lines.append("")

    if data["functions"]:
        lines.append(_emit_yaml({"functions": data["functions"]}))
    else:
        lines.append("functions: []")
    lines.append("")

    lines.append(_emit_yaml({
        "known_edge_cases": [],
        "sign_off": {
            "reviewed_by": "TODO",
            "reviewed_at": "TODO: YYYY-MM-DD",
            "confirmed": False,
            "comments": "",
        },
    }))

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────

def _collect_headers(root: Path, recursive: bool) -> list[Path]:
    if recursive:
        return sorted(root.rglob("*.h"))
    else:
        return sorted(root.glob("*.h"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="扫描 C 头文件，生成 Spec v1 YAML 骨架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "headers_dir",
        help="包含 .h 文件的目录（或单个 .h 文件）",
    )
    parser.add_argument(
        "--output", "-o",
        default="spec-v1.yml",
        help="输出 YAML 文件路径（默认：spec-v1.yml）",
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        default=False,
        help="递归扫描子目录",
    )
    parser.add_argument(
        "--force-regex",
        action="store_true",
        default=False,
        help="强制使用正则解析（即使 libclang 可用）",
    )
    args = parser.parse_args()

    root = Path(args.headers_dir)
    if root.is_file() and root.suffix == ".h":
        header_files = [root]
    elif root.is_dir():
        header_files = _collect_headers(root, args.recursive)
    else:
        print(f"错误：{root} 不是有效的目录或 .h 文件", file=sys.stderr)
        return 1

    if not header_files:
        print(f"警告：在 {root} 中未找到任何 .h 文件", file=sys.stderr)
        return 1

    print(f"扫描 {len(header_files)} 个头文件...", file=sys.stderr)
    for h in header_files:
        print(f"  {h}", file=sys.stderr)

    ci = None if args.force_regex else _try_import_clang()
    used_clang = ci is not None

    if used_clang:
        print("解析引擎：libclang (精准模式)", file=sys.stderr)
        data = _parse_headers_clang(header_files, ci)
    else:
        if not args.force_regex:
            print("解析引擎：正则（降级模式）— 建议安装 libclang 以获得更精准结果", file=sys.stderr)
        else:
            print("解析引擎：正则（强制）", file=sys.stderr)
        data = _parse_headers_regex(header_files)

    n_funcs = len(data["functions"])
    n_types = len(data["types"])
    total_risks = sum(len(f.get("risk_signals", [])) for f in data["functions"])
    print(
        f"提取结果：{n_funcs} 个函数，{n_types} 个类型，{total_risks} 个风险信号",
        file=sys.stderr,
    )

    output_text = _build_output(data, header_files, used_clang)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"输出已写入：{output_path}", file=sys.stderr)

    if total_risks > 0:
        print(
            f"\n⚠  检测到 {total_risks} 个风险信号，请运行 generate_report.py 生成完整分析报告。",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
