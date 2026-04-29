#!/usr/bin/env python3
"""
分析 C 项目，生成 spec.json 和 interfaces.md。

用法：
    python scripts/analyze_c_project.py <c_dir>

示例：
    python scripts/analyze_c_project.py ./c2rust-rs/.c2rust/c

输出：
    <c_dir>/spec.json        — 机器可读的项目规格
    <c_dir>/interfaces.md    — 人工可读的接口清单
"""

import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime, timezone


# ──────────────────────────────────────────────
# 解析工具
# ──────────────────────────────────────────────

def find_files(base: Path, exts):
    return sorted(p for ext in exts for p in base.rglob(f"*{ext}"))


def extract_functions_from_header(header: Path):
    """从头文件中提取函数声明（公开 API）。"""
    text = header.read_text(errors="replace")
    # 匹配函数声明：返回类型 + 函数名 + 参数列表 + ;
    pattern = re.compile(
        r'(?:extern\s+)?'
        r'([\w\s\*]+?)\s+'      # 返回类型
        r'(\w+)\s*'             # 函数名
        r'\(([^)]*)\)\s*;',     # 参数列表
        re.MULTILINE
    )
    funcs = []
    for m in pattern.finditer(text):
        ret_type = m.group(1).strip()
        func_name = m.group(2).strip()
        params_raw = m.group(3).strip()

        # 跳过宏、typedef、常见关键字
        if ret_type in ("typedef", "struct", "enum", "union", "#define"):
            continue
        if func_name.startswith("_"):
            continue

        params = _parse_params(params_raw)
        funcs.append({
            "function": func_name,
            "signature": f"{ret_type} {func_name}({params_raw})",
            "params": params,
            "return_type": ret_type,
            "description": "",
        })
    return funcs


def _parse_params(params_raw: str):
    if not params_raw or params_raw.strip() in ("void", ""):
        return []
    params = []
    for p in params_raw.split(","):
        p = p.strip()
        if not p:
            continue
        # 尝试分离类型和参数名
        tokens = p.rsplit(None, 1)
        if len(tokens) == 2:
            ptype, pname = tokens
            # 清理指针符号
            pname = pname.lstrip("*")
        else:
            ptype, pname = p, ""
        params.append({
            "name": pname,
            "type": ptype.strip(),
            "direction": "in",
        })
    return params


def extract_structs_enums(header: Path):
    """从头文件提取结构体、枚举、typedef 定义。"""
    text = header.read_text(errors="replace")
    contracts = []

    # struct / enum / union
    for kind in ("struct", "enum", "union"):
        pattern = re.compile(
            rf'{kind}\s+(\w+)\s*\{{([^}}]*)\}}\s*;',
            re.DOTALL
        )
        for m in pattern.finditer(text):
            contracts.append({
                "kind": kind,
                "name": f"{kind} {m.group(1)}",
                "definition": m.group(0).strip()[:300],  # 截断过长定义
            })

    # typedef struct/enum
    pattern = re.compile(
        r'typedef\s+(?:struct|enum|union)[^{]*\{[^}]*\}\s*(\w+)\s*;',
        re.DOTALL
    )
    for m in pattern.finditer(text):
        contracts.append({
            "kind": "typedef",
            "name": m.group(1),
            "definition": m.group(0).strip()[:300],
        })

    return contracts


def find_south_deps(src_files, all_module_names):
    """通过 #include 分析南向依赖。"""
    deps = set()
    ext_libs = set()
    for src in src_files:
        text = src.read_text(errors="replace")
        for inc in re.findall(r'#include\s+[<"]([^>"]+)[>"]', text):
            stem = Path(inc).stem
            if stem in all_module_names:
                deps.add(stem)
            elif inc.startswith(("<", '"')) or "/" in inc:
                # 可能是外部库
                ext_libs.add(inc.split("/")[0].split(".")[0])

    result = [{"module": d, "type": "internal"} for d in sorted(deps)]
    result += [{"module": l, "type": "external"} for l in sorted(ext_libs) if l]
    return result


def find_test_coverage(tests_dir: Path, module_name: str):
    """从测试文件中找出覆盖某模块的测试函数。"""
    if not tests_dir.exists():
        return []
    covered = []
    for tf in find_files(tests_dir, [".c"]):
        text = tf.read_text(errors="replace")
        if module_name not in text and module_name.replace("_", "") not in text:
            continue
        # 提取 void test_xxx 函数名
        for m in re.finditer(r'void\s+(test_\w+)\s*\(', text):
            covered.append(m.group(1))
    return list(dict.fromkeys(covered))  # 去重保序


def detect_build_system(c_dir: Path):
    if (c_dir / "CMakeLists.txt").exists():
        return "cmake", "cmake -B build && cmake --build build", "ctest --test-dir build"
    if (c_dir / "configure.ac").exists() or (c_dir / "configure").exists():
        return "autoconf", "./configure && make", "make check"
    if (c_dir / "Makefile").exists():
        return "make", "make", "make test"
    return "unknown", "make", "make test"


# ──────────────────────────────────────────────
# 主逻辑
# ──────────────────────────────────────────────

def analyze(c_dir: str):
    base = Path(c_dir).resolve()
    src_base = base / "src"
    inc_base = base / "include"
    tests_dir = base / "tests"

    if not base.exists():
        print(f"错误：目录不存在：{base}")
        sys.exit(1)

    # 收集头文件（优先 include/，其次 src/ 内的 .h）
    headers = find_files(inc_base, [".h"]) + find_files(src_base, [".h"])
    sources = find_files(src_base, [".c"])

    if not headers and not sources:
        print(f"警告：在 {base} 中未找到 .h 或 .c 文件。")

    # 所有模块名（以头文件为准）
    all_module_names = {h.stem for h in headers}

    build_system, build_cmd, test_cmd = detect_build_system(base)

    spec = {
        "project": {
            "name": base.parent.parent.name,  # c2rust-rs
            "version": "0.1.0",
            "build_system": build_system,
            "build_command": build_cmd,
            "test_command": test_cmd,
            "output_artifacts": []
        },
        "modules": []
    }

    # 为每个头文件生成一个模块条目
    for header in headers:
        mod_name = header.stem

        # 找到对应的源文件
        mod_sources = [s for s in sources if s.stem == mod_name or s.stem.startswith(mod_name)]

        north_ifaces = extract_functions_from_header(header)
        data_contracts = extract_structs_enums(header)
        south_deps = find_south_deps(mod_sources, all_module_names - {mod_name})
        test_cov = find_test_coverage(tests_dir, mod_name)

        spec["modules"].append({
            "name": mod_name,
            "header": str(header.relative_to(base)),
            "sources": [str(s.relative_to(base)) for s in mod_sources],
            "north_interfaces": north_ifaces,
            "south_deps": south_deps,
            "data_contracts": data_contracts,
            "test_coverage": test_cov,
        })

    # 写入 spec.json
    spec_path = base / "spec.json"
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    print(f"✓ 已生成 spec.json：{spec_path}")

    # 生成 interfaces.md
    md_lines = [
        f"# 接口清单：{spec['project']['name']}",
        f"\n生成时间：{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"来源：.c2rust/c/spec.json",
        "",
    ]

    for mod in spec["modules"]:
        md_lines += [
            f"## 模块：{mod['name']}",
            "",
            f"- **头文件**：`{mod['header']}`",
            f"- **源文件**：{', '.join(f'`{s}`' for s in mod['sources']) or '（无对应源文件）'}",
            "",
            "### 北向接口（对外 API）",
            "",
        ]
        if mod["north_interfaces"]:
            md_lines.append("| 函数 | 签名 | 返回值 |")
            md_lines.append("|------|------|--------|")
            for iface in mod["north_interfaces"]:
                md_lines.append(f"| `{iface['function']}` | `{iface['signature']}` | `{iface['return_type']}` |")
        else:
            md_lines.append("（未检测到公开函数声明）")

        md_lines += ["", "### 南向依赖", ""]
        if mod["south_deps"]:
            md_lines.append("| 依赖 | 类型 |")
            md_lines.append("|------|------|")
            for dep in mod["south_deps"]:
                md_lines.append(f"| `{dep['module']}` | {dep['type']} |")
        else:
            md_lines.append("（无依赖）")

        md_lines += ["", "### 数据契约", ""]
        for dc in mod["data_contracts"]:
            md_lines.append(f"```c\n{dc['definition']}\n```")

        md_lines += ["", "### C 测试覆盖", ""]
        if mod["test_coverage"]:
            for t in mod["test_coverage"]:
                md_lines.append(f"- `{t}`")
        else:
            md_lines.append("（无测试或测试文件未检测到）")

        md_lines.append("")

    iface_path = base / "interfaces.md"
    iface_path.write_text("\n".join(md_lines))
    print(f"✓ 已生成 interfaces.md：{iface_path}")

    print(f"\n共分析 {len(spec['modules'])} 个模块。")
    print("请人工审核 interfaces.md，修正误识别的签名后再进行 FFI 生成。")


def main():
    if len(sys.argv) != 2:
        print("用法：python scripts/analyze_c_project.py <c_dir>")
        sys.exit(1)
    analyze(sys.argv[1])


if __name__ == "__main__":
    main()
