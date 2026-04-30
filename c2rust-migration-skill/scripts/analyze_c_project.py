#!/usr/bin/env python3
"""
analyze_c_project.py — C 项目完整分析器（Step 0）

用途：
    在头文件扫描（Step 1）之前，对整个 C 项目做全面分析：
      1. 构建系统识别（Makefile / CMakeLists.txt / autoconf / meson）
      2. 源文件与头文件清点
      3. 已有测试文件识别与接口覆盖映射
      4. 实现文件内部依赖分析（每个北向函数调用了哪些内部函数、用到了哪些类型）
      5. 全局变量与静态变量清点
      6. 若提供已构建的二进制，提取实际导出符号（nm / objdump）

输出：
    Markdown 格式的 c-project-analysis.md，作为 templates/c-project-analysis.md 的填写结果

使用示例：
    python analyze_c_project.py /path/to/c/project --output c-project-analysis.md
    python analyze_c_project.py /path/to/c/project --binary /path/to/libfoo.so --output c-project-analysis.md
    python analyze_c_project.py /path/to/c/project --headers /path/to/include --output c-project-analysis.md
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────────────────────────
# Build system detection
# ──────────────────────────────────────────────────────────────────

BUILD_SYSTEM_INDICATORS: list[tuple[str, str]] = [
    ("CMakeLists.txt",   "CMake"),
    ("Makefile",         "Make"),
    ("GNUmakefile",      "Make"),
    ("makefile",         "Make"),
    ("configure.ac",     "Autoconf/Automake"),
    ("configure.in",     "Autoconf/Automake"),
    ("meson.build",      "Meson"),
    ("BUILD",            "Bazel"),
    ("BUILD.bazel",      "Bazel"),
    ("SConstruct",       "SCons"),
    ("wscript",          "Waf"),
    ("xmake.lua",        "XMake"),
]


def detect_build_system(root: Path) -> list[dict[str, str]]:
    """Detect build system files in the project root."""
    found = []
    for filename, system in BUILD_SYSTEM_INDICATORS:
        p = root / filename
        if p.exists():
            found.append({"file": filename, "system": system, "path": str(p)})
    return found


def extract_cmake_targets(cmake_file: Path) -> list[str]:
    """Extract library/executable targets from CMakeLists.txt (best-effort)."""
    targets = []
    try:
        text = cmake_file.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(
            r'\badd_library\s*\(\s*(\w+)', text, re.IGNORECASE
        ):
            targets.append(m.group(1) + " (library)")
        for m in re.finditer(
            r'\badd_executable\s*\(\s*(\w+)', text, re.IGNORECASE
        ):
            targets.append(m.group(1) + " (executable)")
    except Exception:
        pass
    return targets


def extract_make_targets(makefile: Path) -> list[str]:
    """Extract top-level targets from a Makefile (best-effort)."""
    targets = []
    try:
        text = makefile.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'^([a-zA-Z0-9_\-]+)\s*:', text, re.MULTILINE):
            name = m.group(1)
            if name not in ("all", "clean", "install", "uninstall",
                             "test", "check", "distclean", "PHONY"):
                targets.append(name)
    except Exception:
        pass
    return targets[:20]  # cap to avoid noise


# ──────────────────────────────────────────────────────────────────
# File enumeration
# ──────────────────────────────────────────────────────────────────

def collect_files(root: Path, extensions: list[str],
                  max_files: int = 500) -> list[Path]:
    """Recursively collect files with given extensions."""
    result = []
    for ext in extensions:
        for p in root.rglob(f"*{ext}"):
            if any(part.startswith(".") for part in p.parts):
                continue  # skip hidden dirs
            result.append(p)
            if len(result) >= max_files:
                return result
    return result


# ──────────────────────────────────────────────────────────────────
# Test file detection
# ──────────────────────────────────────────────────────────────────

TEST_DIR_PATTERNS = re.compile(
    r'(?i)^(test|tests|spec|specs|check|checks|t|unittest|unit_test)$'
)
TEST_FILE_PATTERNS = re.compile(
    r'(?i)(test|spec|check|unittest).*\.(c|cpp|h)$|.*\.(c|cpp|h).*test.*'
)
TEST_FUNC_PATTERN = re.compile(
    r'\b(TEST|TEST_F|TEST_P|test_\w+|check_\w+|suite_add|CU_add|assert\w*)\s*[(\s]',
    re.IGNORECASE,
)


def is_test_file(path: Path) -> bool:
    """Heuristic: decide if a .c file is a test file."""
    # Check directory name
    for part in path.parts:
        if TEST_DIR_PATTERNS.match(part):
            return True
    # Check filename pattern
    if TEST_FILE_PATTERNS.match(path.name):
        return True
    # Check file content for test function names
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        if TEST_FUNC_PATTERN.search(text):
            return True
    except Exception:
        pass
    return False


def extract_tested_functions(test_file: Path,
                              known_functions: list[str]) -> list[str]:
    """Find which known exported functions are referenced in a test file."""
    if not known_functions:
        return []
    try:
        text = test_file.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    referenced = []
    for fn in known_functions:
        if re.search(r'\b' + re.escape(fn) + r'\b', text):
            referenced.append(fn)
    return referenced


def extract_test_function_names(test_file: Path) -> list[str]:
    """Extract test case function names from a test file."""
    names: list[str] = []
    try:
        text = test_file.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return names
    # Common patterns: test_foo(), TEST(suite, case), check_foo()
    for m in re.finditer(
        r'\bvoid\s+(test_\w+|check_\w+)\s*\(', text, re.IGNORECASE
    ):
        names.append(m.group(1))
    for m in re.finditer(
        r'\bTEST(?:_F|_P)?\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)', text
    ):
        names.append(f"{m.group(1)}.{m.group(2)}")
    return names


# ──────────────────────────────────────────────────────────────────
# C source implementation analysis
# ──────────────────────────────────────────────────────────────────

# Matches a C function definition (very approximate, handles most common forms)
C_FUNC_DEF_RE = re.compile(
    r'(?:^|\n)(?:(?:static|inline|extern|__attribute__\s*\([^)]*\))\s+)*'
    r'[\w\s\*]+\s+(\w+)\s*\([^)]*\)\s*\{',
    re.MULTILINE,
)

C_FUNC_CALL_RE = re.compile(r'\b(\w+)\s*\(')

C_GLOBAL_VAR_RE = re.compile(
    r'^(?:static\s+)?(?:const\s+)?'
    r'(?:unsigned\s+|signed\s+|long\s+|short\s+)?'
    r'(?:int|char|float|double|void\s*\*|size_t|uint\w+|int\w+|\w+_t|\w+)\s+'
    r'(\w+)\s*(?:=|;)',
    re.MULTILINE,
)

# C keywords that must not be mistaken for global variable names
_C_KEYWORDS: frozenset[str] = frozenset({
    "return", "if", "else", "for", "while", "do",
    "switch", "case", "break", "continue",
})

# Common libc / runtime function names to exclude from callee maps
_COMMON_LIBC_FUNCS: frozenset[str] = frozenset({
    "if", "while", "for", "switch", "return", "sizeof",
    "typeof", "assert", "printf", "fprintf", "malloc", "free",
    "memset", "memcpy", "strlen", "strcpy", "strcat", "sprintf",
})


def analyze_source_file(src: Path) -> dict[str, Any]:
    """Extract function definitions, calls, and global variables from a .c file."""
    result: dict[str, Any] = {
        "path": str(src),
        "functions_defined": [],
        "global_vars": [],
    }
    try:
        text = src.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return result

    # Function definitions
    for m in C_FUNC_DEF_RE.finditer(text):
        result["functions_defined"].append(m.group(1))

    # Global variables (file-scope, non-local)
    # Only look outside function bodies — approximate by scanning top ~40 lines
    top = "\n".join(text.splitlines()[:80])
    for m in C_GLOBAL_VAR_RE.finditer(top):
        name = m.group(1)
        if name not in _C_KEYWORDS:
            result["global_vars"].append(name)

    return result


def build_callee_map(src: Path,
                     exported_functions: list[str]) -> dict[str, list[str]]:
    """
    For each exported function, find which other functions it directly calls.
    This is a best-effort text analysis; it does not parse macro expansions.
    """
    try:
        text = src.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    # Split text into rough function bodies
    callee_map: dict[str, list[str]] = {}
    # Find all function definition positions
    positions = [
        (m.start(), m.group(1))
        for m in C_FUNC_DEF_RE.finditer(text)
    ]
    if not positions:
        return callee_map

    # For each function body, scan for call expressions
    for i, (start, fname) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        body = text[start:end]
        # Find matching brace end of this function (approximate)
        depth = 0
        func_body_end = len(body)
        for j, ch in enumerate(body):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    func_body_end = j
                    break
        body = body[:func_body_end]
        callees = set()
        for m in C_FUNC_CALL_RE.finditer(body):
            called = m.group(1)
            if called != fname and called not in _COMMON_LIBC_FUNCS:
                callees.add(called)
        callee_map[fname] = sorted(callees)

    return callee_map


def extract_include_deps(src: Path) -> list[str]:
    """Extract #include directives from a source file."""
    includes = []
    try:
        text = src.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'#\s*include\s*[<"]([^>"]+)[>"]', text):
            includes.append(m.group(1))
    except Exception:
        pass
    return includes


# ──────────────────────────────────────────────────────────────────
# Binary symbol extraction
# ──────────────────────────────────────────────────────────────────

def extract_exported_symbols(binary: Path) -> list[str]:
    """Run nm or objdump to list exported symbols from a binary."""
    symbols: list[str] = []

    # Try nm first
    for cmd in [
        ["nm", "-D", "--defined-only", str(binary)],
        ["nm", "--defined-only", str(binary)],
    ]:
        try:
            out = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=10
            ).decode("utf-8", errors="replace")
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[-2].upper() in ("T", "W", "V"):
                    sym = parts[-1]
                    if not sym.startswith("_Z"):  # skip C++ mangled
                        symbols.append(sym)
            if symbols:
                return sorted(set(symbols))
        except (FileNotFoundError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired):
            pass

    # Try objdump as fallback
    try:
        out = subprocess.check_output(
            ["objdump", "-T", str(binary)],
            stderr=subprocess.DEVNULL, timeout=10
        ).decode("utf-8", errors="replace")
        for line in out.splitlines():
            if " g " in line or " G " in line:
                parts = line.split()
                if parts:
                    sym = parts[-1]
                    if not sym.startswith("_Z"):
                        symbols.append(sym)
        return sorted(set(symbols))
    except (FileNotFoundError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired):
        pass

    return []


# ──────────────────────────────────────────────────────────────────
# Header-declared function extraction (lightweight, no libclang needed)
# ──────────────────────────────────────────────────────────────────

HEADER_FUNC_RE = re.compile(
    r'(?:extern\s+)?'
    r'(?:(?:unsigned|signed|const|volatile|static|inline)\s+)*'
    r'[\w\s\*]+\s+'
    r'(\w+)\s*\([^)]*\)\s*;',
    re.MULTILINE,
)


def extract_header_functions(header_files: list[Path]) -> list[str]:
    """Extract function names declared in header files."""
    functions: list[str] = []
    keywords = {"if", "else", "for", "while", "do", "switch", "return",
                 "sizeof", "typedef", "struct", "enum", "union"}
    for hf in header_files:
        try:
            text = hf.read_text(encoding="utf-8", errors="replace")
            for m in HEADER_FUNC_RE.finditer(text):
                name = m.group(1)
                if name not in keywords:
                    functions.append(name)
        except Exception:
            pass
    return sorted(set(functions))


# ──────────────────────────────────────────────────────────────────
# Report generation
# ──────────────────────────────────────────────────────────────────

def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def generate_report(
    root: Path,
    header_dir: Path | None,
    binary: Path | None,
    output: Path,
) -> None:
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    lines.append(f"# C 项目完整分析报告")
    lines.append(f"")
    lines.append(f"> **生成时间**：{now}")
    lines.append(f"> **分析根目录**：`{root}`")
    lines.append(f"> **用途**：本文件是 Phase 1 Step 0（C 项目完整分析）的输出，")
    lines.append(f"> 须由负责人逐节审查、补全 TODO 项并在文末签字后方可推进至 Step 1。")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ── 1. 构建系统 ────────────────────────────────────────────────
    lines.append(f"## 1. 构建系统分析")
    lines.append(f"")
    build_systems = detect_build_system(root)
    if build_systems:
        rows = [[b["system"], b["file"]] for b in build_systems]
        lines.append(_md_table(["构建系统", "文件"], rows))
        lines.append(f"")
        # Try to extract targets
        for b in build_systems:
            p = Path(b["path"])
            if b["system"] == "CMake":
                targets = extract_cmake_targets(p)
                if targets:
                    lines.append(f"**CMake 构建目标**（来自 `{b['file']}`）：")
                    for t in targets:
                        lines.append(f"- `{t}`")
                    lines.append(f"")
            elif b["system"] == "Make":
                targets = extract_make_targets(p)
                if targets:
                    lines.append(f"**Make 目标**（来自 `{b['file']}`，节选）：")
                    for t in targets[:10]:
                        lines.append(f"- `{t}`")
                    lines.append(f"")
    else:
        lines.append(f"> ⚠ 未检测到已知构建系统文件。请手动填写。")
        lines.append(f"")

    lines.append(f"**TODO（人工补全）**：")
    lines.append(f"- 构建命令（生成最终产物）：`TODO`")
    lines.append(f"- 最终产物（库文件名及路径）：`TODO`")
    lines.append(f"- 产物类型：`staticlib (.a)` / `cdylib (.so/.dll)` / 两者均有")
    lines.append(f"- 编译选项（-O2 / ASAN / UBSAN 等）：`TODO`")
    lines.append(f"- 目标平台（x86_64-linux / aarch64-linux / ...）：`TODO`")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ── 2. 文件清单 ────────────────────────────────────────────────
    lines.append(f"## 2. 项目文件清单")
    lines.append(f"")
    src_files = collect_files(root, [".c"])
    header_files = collect_files(header_dir or root, [".h"])
    test_files = [f for f in src_files if is_test_file(f)]
    impl_files = [f for f in src_files if not is_test_file(f)]

    lines.append(f"| 类别 | 数量 |")
    lines.append(f"| --- | --- |")
    lines.append(f"| C 源文件（.c） | {len(src_files)} |")
    lines.append(f"| 头文件（.h） | {len(header_files)} |")
    lines.append(f"| 推断为测试文件 | {len(test_files)} |")
    lines.append(f"| 推断为实现文件 | {len(impl_files)} |")
    lines.append(f"")

    if test_files:
        lines.append(f"**识别到的测试文件**：")
        for tf in sorted(test_files)[:20]:
            lines.append(f"- `{tf.relative_to(root)}`")
        if len(test_files) > 20:
            lines.append(f"- …（共 {len(test_files)} 个，仅展示前 20）")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")

    # ── 3. 北向接口声明（头文件） ────────────────────────────────────
    lines.append(f"## 3. 北向接口声明（来自头文件）")
    lines.append(f"")
    declared_fns = extract_header_functions(header_files)
    if declared_fns:
        lines.append(f"从头文件中检测到 **{len(declared_fns)}** 个函数声明：")
        lines.append(f"")
        rows = [[f"`{fn}`", "TODO（所在头文件）", "TODO（区分北向/内部）"] for fn in declared_fns]
        lines.append(_md_table(
            ["函数名", "所在头文件", "接口类型"],
            rows,
        ))
        lines.append(f"")
        lines.append(f"> **TODO（人工确认）**：在「接口类型」列中，将每个函数标记为"
                     f"「北向（对外）」或「内部（仅内部使用）」，并删除非北向函数行。")
    else:
        lines.append(f"> ⚠ 未从头文件中检测到函数声明。请检查头文件路径或手动填写。")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ── 4. 实际导出符号（二进制） ────────────────────────────────────
    lines.append(f"## 4. 实际导出符号（来自已构建二进制）")
    lines.append(f"")
    if binary and binary.exists():
        symbols = extract_exported_symbols(binary)
        if symbols:
            lines.append(f"从 `{binary}` 提取到 **{len(symbols)}** 个导出符号：")
            lines.append(f"")
            rows = [[f"`{s}`", "TODO（头文件中是否声明）", "TODO（需Rust侧导出）"] for s in symbols]
            lines.append(_md_table(
                ["符号名", "头文件声明", "是否需要Rust侧导出"],
                rows,
            ))
            lines.append(f"")
            # Cross-check with header declarations
            declared_set = set(declared_fns)
            symbol_set = set(symbols)
            extra_in_binary = symbol_set - declared_set
            missing_in_binary = declared_set - symbol_set
            if extra_in_binary:
                lines.append(f"⚠ **仅存在于二进制、未在头文件中声明**（{len(extra_in_binary)} 个）：")
                for s in sorted(extra_in_binary)[:10]:
                    lines.append(f"- `{s}`")
                lines.append(f"")
            if missing_in_binary:
                lines.append(f"⚠ **头文件中声明但未出现在二进制中**（{len(missing_in_binary)} 个）：")
                for s in sorted(missing_in_binary)[:10]:
                    lines.append(f"- `{s}`")
                lines.append(f"")
        else:
            lines.append(f"> ⚠ 无法从 `{binary}` 提取符号（nm/objdump 不可用或二进制格式不支持）。")
            lines.append(f"> 请手动运行：`nm -D {binary} | grep ' T '` 并将结果填入下表。")
    else:
        lines.append(f"> ⚠ 未提供已构建二进制路径（--binary 参数），无法自动提取符号。")
        lines.append(f">")
        lines.append(f"> **TODO（人工必填）**：")
        lines.append(f"> 1. 按以下命令构建项目并运行符号检查：")
        lines.append(f">    ```bash")
        lines.append(f">    # 构建")
        lines.append(f">    TODO: 填写构建命令")
        lines.append(f">    # 查看导出符号")
        lines.append(f">    nm -D <产物路径> | grep ' T '")
        lines.append(f">    # 或")
        lines.append(f">    objdump -T <产物路径> | grep ' g '")
        lines.append(f">    ```")
        lines.append(f"> 2. 将输出符号填入下表：")
        lines.append(f"")
        lines.append(_md_table(
            ["符号名", "头文件声明", "是否需要Rust侧导出"],
            [["TODO", "TODO", "TODO"]],
        ))
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ── 5. 测试覆盖映射 ─────────────────────────────────────────────
    lines.append(f"## 5. 现有测试覆盖映射")
    lines.append(f"")
    if test_files:
        test_coverage: list[list[str]] = []
        for tf in sorted(test_files)[:30]:
            test_funcs = extract_test_function_names(tf)
            covered = extract_tested_functions(tf, declared_fns)
            test_coverage.append([
                f"`{tf.relative_to(root)}`",
                ", ".join(f"`{t}`" for t in test_funcs[:5]) or "—",
                ", ".join(f"`{c}`" for c in covered) or "TODO（人工标注）",
            ])
        lines.append(_md_table(
            ["测试文件", "测试用例（节选）", "覆盖的北向接口"],
            test_coverage,
        ))
        lines.append(f"")
        lines.append(f"**TODO（人工补全）**：")
        lines.append(f"- 「覆盖的北向接口」列请人工核对并补全（自动检测可能遗漏间接覆盖）")
        lines.append(f"- 填写整体测试覆盖率估算：TODO%")
        lines.append(f"- 标记无任何测试覆盖的北向接口（高风险，须在验证计划中特别处理）：TODO")
    else:
        lines.append(f"> ⚠ 未检测到测试文件。")
        lines.append(f"> **TODO（人工必填）**：")
        lines.append(f"> - 测试框架名称（gtest / cmocka / Unity / 自研 / 无）：TODO")
        lines.append(f"> - 如何运行测试（命令）：`TODO`")
        lines.append(f"> - 哪些北向接口有测试覆盖：TODO")
        lines.append(f"> - 估算整体覆盖率：TODO%")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ── 6. 实现依赖分析 ─────────────────────────────────────────────
    lines.append(f"## 6. 北向函数实现依赖分析")
    lines.append(f"")
    lines.append(f"> 本节分析每个北向函数在 C 实现文件中调用了哪些内部函数、")
    lines.append(f"> 依赖了哪些全局变量，以及引入了哪些头文件依赖。")
    lines.append(f"> **转换时必须将这些依赖一并纳入分析范围，不得仅针对接口签名做翻译。**")
    lines.append(f"")

    all_callee_maps: dict[str, list[str]] = {}
    all_global_vars: list[str] = []
    all_includes: list[str] = []
    func_to_file: dict[str, str] = {}

    for sf in impl_files[:50]:  # cap to avoid very large projects
        info = analyze_source_file(sf)
        for fn in info["functions_defined"]:
            func_to_file[fn] = str(sf.relative_to(root))
        all_global_vars.extend(info["global_vars"])
        all_includes.extend(extract_include_deps(sf))
        callee_map = build_callee_map(sf, declared_fns)
        for fn, callees in callee_map.items():
            if fn not in all_callee_maps:
                all_callee_maps[fn] = []
            all_callee_maps[fn].extend(callees)

    if declared_fns:
        lines.append(f"### 6.1 每个北向函数的直接调用依赖")
        lines.append(f"")
        rows = []
        for fn in declared_fns:
            callees = all_callee_maps.get(fn, [])
            src_file = func_to_file.get(fn, "TODO（未在扫描范围内找到实现）")
            callee_str = ", ".join(f"`{c}`" for c in callees[:8]) if callees else "—（无或未检测到）"
            rows.append([f"`{fn}`", f"`{src_file}`", callee_str])
        lines.append(_md_table(
            ["北向函数", "实现文件", "直接调用的内部函数（自动检测，需人工核对）"],
            rows,
        ))
        lines.append(f"")
        lines.append(f"**TODO（人工补全）**：")
        lines.append(f"- 核对自动检测结果，补全遗漏的间接依赖")
        lines.append(f"- 标记跨文件依赖（函数 A 调用了另一文件中的函数 B）")
        lines.append(f"- 标记涉及条件编译（`#ifdef`）的依赖分支")
        lines.append(f"")
    else:
        lines.append(f"> ⚠ 未能建立函数依赖图（未检测到北向函数声明）。请手动填写。")
        lines.append(f"")

    lines.append(f"### 6.2 全局变量与静态变量")
    lines.append(f"")
    unique_globals = sorted(set(all_global_vars))
    if unique_globals:
        lines.append(f"在实现文件中检测到以下文件作用域变量（自动检测，需人工核对）：")
        lines.append(f"")
        rows = [[f"`{g}`", "TODO（C 类型）", "TODO（哪些北向函数依赖此变量）",
                  "TODO（线程安全方案）"] for g in unique_globals[:20]]
        lines.append(_md_table(
            ["变量名", "C 类型", "依赖该变量的北向函数", "线程安全方案"],
            rows,
        ))
    else:
        lines.append(f"> 未检测到明显的全局变量（或位于宏/条件编译中）。")
        lines.append(f"> **TODO**：人工确认是否存在全局状态。")
    lines.append(f"")

    lines.append(f"### 6.3 数据类型清单")
    lines.append(f"")
    lines.append(f"> **TODO（人工必填）**：列出所有跨 FFI 边界传递的数据类型，")
    lines.append(f"> 包括结构体、枚举、typedef、函数指针类型等。")
    lines.append(f"> 对于每个类型，需确认：")
    lines.append(f"> - 完整 C 定义（含字段/成员）")
    lines.append(f"> - 是否跨平台（32/64 位兼容性）")
    lines.append(f"> - 是否含位域（需特殊处理）")
    lines.append(f"> - Rust 侧对应的 `#[repr(C)]` 结构体设计")
    lines.append(f"")
    lines.append(_md_table(
        ["类型名", "Kind", "C 定义摘要", "跨平台问题", "Rust 对应类型"],
        [["TODO", "struct/enum/typedef", "TODO", "TODO", "TODO"]],
    ))
    lines.append(f"")

    lines.append(f"### 6.4 头文件依赖")
    lines.append(f"")
    unique_includes = sorted(set(all_includes))
    if unique_includes:
        lines.append(f"实现文件中引用的头文件（含系统头文件）：")
        lines.append(f"")
        for inc in unique_includes[:30]:
            lines.append(f"- `{inc}`")
        if len(unique_includes) > 30:
            lines.append(f"- …（共 {len(unique_includes)} 个，仅展示前 30）")
    else:
        lines.append(f"> 未检测到 #include 指令。")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ── 7. 风险汇总 ────────────────────────────────────────────────
    lines.append(f"## 7. 风险汇总（Step 0 阶段）")
    lines.append(f"")
    lines.append(f"| 风险项 | 说明 | 影响范围 | 需在 Step 1 前明确 |")
    lines.append(f"| --- | --- | --- | --- |")
    lines.append(f"| TODO | TODO | TODO | ☐ |")
    lines.append(f"")
    lines.append(f"> **TODO（人工填写）**：根据以上各节分析结果，")
    lines.append(f"> 汇总发现的风险（如：无测试的接口、全局状态、平台类型、二进制符号与头文件不一致等）。")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ── 8. 人工确认记录 ─────────────────────────────────────────────
    lines.append(f"## ⚠ 人工确认点 0（Step 0 完成确认）")
    lines.append(f"")
    lines.append(f"> **阻断门**：以下清单未全部打勾并签字之前，**不得推进至 Step 1（头文件扫描）**。")
    lines.append(f"")
    lines.append(f"### 必须完成的核查项")
    lines.append(f"")
    lines.append(f"**构建系统**")
    lines.append(f"- [ ] 构建命令已确认，可成功构建出目标产物")
    lines.append(f"- [ ] 产物形式（staticlib / cdylib）已确认")
    lines.append(f"- [ ] 目标平台矩阵已确认")
    lines.append(f"")
    lines.append(f"**导出符号**")
    lines.append(f"- [ ] 已实际构建二进制并用 `nm`/`objdump` 提取导出符号")
    lines.append(f"- [ ] 导出符号列表已与头文件声明逐一核对，差异已记录并说明")
    lines.append(f"- [ ] 需 Rust 侧导出的符号集合已最终确认（填入第4节表格）")
    lines.append(f"")
    lines.append(f"**测试现状**")
    lines.append(f"- [ ] 已识别所有测试文件和测试框架")
    lines.append(f"- [ ] 测试命令已确认（可成功运行）")
    lines.append(f"- [ ] 每个北向接口的测试覆盖情况已标注（有/无/部分）")
    lines.append(f"- [ ] 无测试覆盖的接口已标记为高风险，将在验证计划中特别处理")
    lines.append(f"")
    lines.append(f"**实现分析**")
    lines.append(f"- [ ] 每个北向函数的实现文件已定位")
    lines.append(f"- [ ] 每个北向函数的直接与间接调用依赖已梳理完毕")
    lines.append(f"- [ ] 所有跨 FFI 边界的数据类型（结构体/枚举/typedef）已清点")
    lines.append(f"- [ ] 全局变量和静态变量已清点，线程安全方案已初步确认")
    lines.append(f"- [ ] 第6节所有 TODO 项已填写完毕")
    lines.append(f"")
    lines.append(f"**本文件完整性**")
    lines.append(f"- [ ] 本文件中所有 TODO 标记已填写或明确标注「不适用」")
    lines.append(f"- [ ] 第7节风险汇总已填写")
    lines.append(f"")
    lines.append(f"### 签字记录")
    lines.append(f"")
    lines.append(f"| 字段 | 值 |")
    lines.append(f"| --- | --- |")
    lines.append(f"| 分析人 | TODO |")
    lines.append(f"| 审查人 | TODO |")
    lines.append(f"| 签字日期 | TODO（YYYY-MM-DD） |")
    lines.append("| 未解决风险项 | TODO（无则填「无」） |")
    lines.append(f"| 确认状态 | ☐ 未完成 / ☐ **已完成，允许推进 Step 1** |")
    lines.append(f"")
    lines.append(f"> **签字意味着**：C 项目的构建方式、实际导出符号、测试覆盖现状、")
    lines.append(f"> 函数实现依赖与数据类型已全面分析，结果已记录于本文件，")
    lines.append(f"> 可作为后续 Spec v1 填写和 ABI 冻结的输入依据。")
    lines.append(f"")

    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"分析报告已写入：{output}")


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="C 项目完整分析器（Step 0）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "project_root",
        help="C 项目根目录",
    )
    parser.add_argument(
        "--headers",
        help="头文件目录（默认与 project_root 相同）",
        default=None,
    )
    parser.add_argument(
        "--binary",
        help="已构建的库二进制文件路径（用于提取导出符号）",
        default=None,
    )
    parser.add_argument(
        "--output",
        help="输出报告路径（默认：c-project-analysis.md）",
        default="c-project-analysis.md",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"错误：项目根目录不存在：{root}", file=sys.stderr)
        sys.exit(1)

    header_dir = Path(args.headers).resolve() if args.headers else None
    if header_dir and not header_dir.exists():
        print(f"错误：头文件目录不存在：{header_dir}", file=sys.stderr)
        sys.exit(1)

    binary = Path(args.binary).resolve() if args.binary else None
    output = Path(args.output)

    generate_report(root, header_dir, binary, output)


if __name__ == "__main__":
    main()
