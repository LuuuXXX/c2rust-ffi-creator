#!/usr/bin/env python3
"""
基于 interfaces.md（或 spec.json）生成 Rust FFI 骨架代码。

用法：
    python scripts/gen_rust_ffi.py <interfaces_md> <output_src_dir>

示例：
    python scripts/gen_rust_ffi.py .c2rust/c/interfaces.md ffi/src
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# C 类型 → Rust 类型映射
# ──────────────────────────────────────────────

C_TO_RUST = {
    "int":           "std::ffi::c_int",
    "unsigned int":  "std::ffi::c_uint",
    "long":          "std::ffi::c_long",
    "unsigned long": "std::ffi::c_ulong",
    "short":         "std::ffi::c_short",
    "char":          "std::ffi::c_char",
    "float":         "std::ffi::c_float",
    "double":        "std::ffi::c_double",
    "void":          "()",
    "size_t":        "usize",
    "ssize_t":       "isize",
    "uint8_t":       "u8",
    "uint16_t":      "u16",
    "uint32_t":      "u32",
    "uint64_t":      "u64",
    "int8_t":        "i8",
    "int16_t":       "i16",
    "int32_t":       "i32",
    "int64_t":       "i64",
    "bool":          "bool",
    "intptr_t":      "isize",
    "uintptr_t":     "usize",
}


def map_c_type(c_type: str) -> str:
    """将 C 类型字符串转换为 Rust 类型字符串（尽力而为）。"""
    c_type = c_type.strip()
    is_ptr = "*" in c_type
    is_const = "const" in c_type

    base = c_type.replace("const", "").replace("*", "").replace("unsigned", "unsigned ").strip()
    base = re.sub(r'\s+', ' ', base)

    rust_base = C_TO_RUST.get(base)
    if rust_base is None:
        # 未知类型：生成占位名（PascalCase）
        rust_base = "".join(w.capitalize() for w in re.split(r'[\s_]+', base))

    if is_ptr:
        if is_const:
            return f"*const {rust_base}" if rust_base != "()" else "*const std::ffi::c_void"
        else:
            return f"*mut {rust_base}" if rust_base != "()" else "*mut std::ffi::c_void"
    return rust_base


def gen_module_rs(mod_name: str, interfaces: list, timestamp: str) -> str:
    """为一个 C 模块生成对应的 Rust FFI 模块文件内容。"""
    lines = [
        f"//! FFI 封装：{mod_name} 模块",
        f"//! 原 C 头文件：<模块目录>/include/{mod_name}.h",
        f"//! 生成时间：{timestamp}",
        f"//! 警告：此文件由 gen_rust_ffi.py 自动生成，请在人工审核后修改。",
        "",
        "#![allow(non_camel_case_types, non_snake_case, dead_code)]",
        "",
        "use std::ffi::{c_int, c_uint, c_long, c_char, c_void, c_float, c_double};",
        "",
    ]

    if not interfaces:
        lines += [
            "// TODO: 此模块未检测到北向接口，请人工填写。",
            "",
        ]
        return "\n".join(lines)

    # extern "C" 块（声明原始 C 函数）
    lines += [
        "extern \"C\" {",
    ]
    for iface in interfaces:
        params_str = _build_rust_params(iface.get("params", []))
        ret = map_c_type(iface.get("return_type", "int"))
        lines.append(f"    fn {iface['function']}({params_str}) -> {ret};")
    lines += ["}", ""]

    # 公开封装函数（#[no_mangle] + pub extern "C"）
    for iface in interfaces:
        func = iface["function"]
        params_str = _build_rust_params(iface.get("params", []))
        ret = map_c_type(iface.get("return_type", "int"))
        params_call = ", ".join(
            p["name"] if p["name"] else f"_p{i}"
            for i, p in enumerate(iface.get("params", []))
        )

        lines += [
            "/// # Safety",
            f"/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。",
            "#[no_mangle]",
            f"pub unsafe extern \"C\" fn {func}({params_str}) -> {ret} {{",
            f"    {func}({params_call})",
            "}",
            "",
        ]

    return "\n".join(lines)


def _build_rust_params(params: list) -> str:
    parts = []
    for i, p in enumerate(params):
        name = p.get("name") or f"_p{i}"
        rtype = map_c_type(p.get("type", "void *"))
        parts.append(f"{name}: {rtype}")
    return ", ".join(parts)


def update_lib_rs(src_dir: Path, module_names: list, timestamp: str):
    """更新 lib.rs，添加模块声明。"""
    lib_path = src_dir / "lib.rs"
    mod_decls = "\n".join(f"pub mod {m};" for m in module_names)
    content = (
        f"//! c2rust-rs FFI 封装层\n"
        f"//! 生成时间：{timestamp}\n"
        f"//!\n"
        f"//! # 模块列表\n"
        f"{chr(10).join('//! - ' + m for m in module_names)}\n"
        f"\n"
        f"{mod_decls}\n"
    )
    lib_path.write_text(content)
    print(f"✓ 已更新 lib.rs")


# ──────────────────────────────────────────────
# 解析 interfaces.md
# ──────────────────────────────────────────────

def parse_interfaces_md(md_path: Path) -> list:
    """从 interfaces.md 提取模块和接口信息（简单解析）。"""
    text = md_path.read_text()
    modules = []
    current_mod = None

    for line in text.splitlines():
        # 模块标题
        m = re.match(r'^## 模块：(\S+)', line)
        if m:
            if current_mod:
                modules.append(current_mod)
            current_mod = {"name": m.group(1), "north_interfaces": []}
            continue

        if current_mod is None:
            continue

        # 函数行（表格行）
        m = re.match(r'^\|\s*`(\w+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|', line)
        if m:
            func_name = m.group(1)
            sig = m.group(2)
            ret_type = m.group(3)
            # 解析参数（从签名中提取括号内内容）
            pm = re.search(r'\(([^)]*)\)', sig)
            params_raw = pm.group(1) if pm else ""
            params = _parse_params_simple(params_raw)
            current_mod["north_interfaces"].append({
                "function": func_name,
                "signature": sig,
                "params": params,
                "return_type": ret_type,
            })

    if current_mod:
        modules.append(current_mod)
    return modules


def _parse_params_simple(params_raw: str) -> list:
    if not params_raw.strip() or params_raw.strip() == "void":
        return []
    params = []
    for p in params_raw.split(","):
        p = p.strip()
        if not p:
            continue
        tokens = p.rsplit(None, 1)
        if len(tokens) == 2:
            ptype, pname = tokens
            pname = pname.lstrip("*")
        else:
            ptype, pname = p, ""
        params.append({"name": pname, "type": ptype.strip(), "direction": "in"})
    return params


# ──────────────────────────────────────────────
# 主逻辑
# ──────────────────────────────────────────────

def gen_ffi(interfaces_md: str, output_src_dir: str):
    md_path = Path(interfaces_md).resolve()
    src_dir = Path(output_src_dir).resolve()

    if not md_path.exists():
        print(f"错误：interfaces.md 不存在：{md_path}")
        sys.exit(1)

    src_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    modules = parse_interfaces_md(md_path)
    if not modules:
        print("警告：未从 interfaces.md 中解析到任何模块，请检查文件格式。")
        sys.exit(1)

    module_names = []
    for mod in modules:
        mod_name = mod["name"]
        module_names.append(mod_name)
        content = gen_module_rs(mod_name, mod["north_interfaces"], timestamp)
        out_file = src_dir / f"{mod_name}.rs"
        out_file.write_text(content)
        print(f"✓ 已生成 {out_file.relative_to(src_dir.parent.parent) if src_dir.parent.parent.exists() else out_file}")

    update_lib_rs(src_dir, module_names, timestamp)

    print(f"\n共生成 {len(modules)} 个模块文件。")
    print("⚠ 请人工审核生成的 Rust 代码，特别是：")
    print("  - 不认识的 C 类型已被替换为 PascalCase 占位名，需手动补充 #[repr(C)] 定义")
    print("  - 函数封装层默认 1:1 透传，如需添加安全检查请手动修改")
    print("  - 运行 verify_symbols.sh 验证导出符号表")


def main():
    if len(sys.argv) != 3:
        print("用法：python scripts/gen_rust_ffi.py <interfaces_md> <output_src_dir>")
        sys.exit(1)
    gen_ffi(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
