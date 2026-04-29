#!/usr/bin/env python3
"""
基于 spec.json（或 interfaces.md 兼容模式）生成 Rust FFI 骨架代码。

生成的 Rust 模块结构镜像原 C 项目的头文件目录层级，便于大型项目导航。

用法：
    python scripts/gen_rust_ffi.py <spec_json_or_interfaces_md> <output_src_dir>

示例（推荐，保留目录层级）：
    python scripts/gen_rust_ffi.py .c2rust/c/spec.json ffi/src

示例（兼容模式，平铺）：
    python scripts/gen_rust_ffi.py .c2rust/c/interfaces.md ffi/src
"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# 模块路径推导：从头文件路径映射到 Rust 模块层级
# ──────────────────────────────────────────────

# 仅作为"顶层前缀"剥离的目录名（不代表模块，只是放头文件用的）
_STRIP_TOPLEVEL = {"include", "includes", "inc", "headers", "header", "public", "pub", "api", "src"}


def header_to_module_path(header: str) -> list:
    """
    将头文件相对路径转换为 Rust 模块路径组件列表。

    规则：
    1. 剥离 .h 后缀
    2. 若第一个目录名是纯容器（include/src/inc/…），则剥离它
    3. 将路径中的连字符替换为下划线（Rust 标识符要求）

    示例：
      "include/foo.h"            → ["foo"]
      "include/crypto/aes.h"     → ["crypto", "aes"]
      "src/lib/net/tcp.h"        → ["lib", "net", "tcp"]
      "lib/platform/linux/io.h"  → ["lib", "platform", "linux", "io"]
      "utils.h"                  → ["utils"]
    """
    p = Path(header)
    parts = list(p.with_suffix("").parts)

    if parts and parts[0].lower() in _STRIP_TOPLEVEL:
        parts = parts[1:]

    parts = [re.sub(r"[^a-zA-Z0-9_]", "_", part) for part in parts if part]

    return parts if parts else [re.sub(r"[^a-zA-Z0-9_]", "_", p.stem)]


def build_module_tree(all_module_paths: list) -> dict:
    """
    构建层级树：parent_path_tuple → set(直接子模块名)

    用于生成 lib.rs 和各级 mod.rs 的 `pub mod` 声明。
    """
    tree = defaultdict(set)
    for parts in all_module_paths:
        for i in range(len(parts)):
            parent = tuple(parts[:i])
            tree[parent].add(parts[i])
    return tree


# ──────────────────────────────────────────────
# C 类型 → Rust 类型映射
# ──────────────────────────────────────────────

C_TO_RUST = {
    "int":           "c_int",
    "unsigned int":  "c_uint",
    "long":          "c_long",
    "unsigned long": "c_ulong",
    "short":         "c_short",
    "char":          "c_char",
    "float":         "c_float",
    "double":        "c_double",
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
    """将 C 类型字符串转换为 Rust 类型字符串（尽力而为）。

    支持多级指针（如 ``char **``），逐级生成 ``*mut``/``*const`` 链。
    """
    c_type = c_type.strip()
    ptr_depth = c_type.count("*")
    is_const = "const" in c_type

    base = c_type.replace("const", "").replace("*", "").strip()
    # Normalize multiple spaces
    base = re.sub(r'\s+', ' ', base)

    rust_base = C_TO_RUST.get(base)
    if rust_base is None:
        # 未知类型：生成占位名（PascalCase）
        rust_base = "".join(w.capitalize() for w in re.split(r'[\s_]+', base))

    if ptr_depth == 0:
        return rust_base

    # 最内层指针：用 const/mut 修饰 base
    innermost = "c_void" if rust_base == "()" else rust_base
    qualifier = "const" if is_const else "mut"
    result = f"*{qualifier} {innermost}"
    # 外层指针（多级时均为 *mut）
    for _ in range(ptr_depth - 1):
        result = f"*mut {result}"
    return result


def _is_placeholder_type(c_type: str) -> tuple:
    """
    如果 c_type 映射到一个占位名（未知 C 类型），返回 (True, placeholder_name)，
    否则返回 (False, "")。
    """
    base = c_type.replace("const", "").replace("*", "").strip()
    base = re.sub(r'\s+', ' ', base)
    if not base or C_TO_RUST.get(base) is not None:
        return False, ""
    name = "".join(w.capitalize() for w in re.split(r'[\s_]+', base))
    return (True, name) if name else (False, "")


def _collect_placeholder_types(interfaces: list) -> list:
    """从接口列表中收集所有占位 PascalCase 类型名（去重有序）。"""
    seen = {}
    for iface in interfaces:
        for p in iface.get("params", []):
            ok, name = _is_placeholder_type(p.get("type", ""))
            if ok and name not in seen:
                seen[name] = True
        ok, name = _is_placeholder_type(iface.get("return_type", ""))
        if ok and name not in seen:
            seen[name] = True
    return list(seen.keys())


def gen_module_rs(mod_name: str, interfaces: list, timestamp: str, original_header: str = "") -> str:
    """为一个 C 模块生成对应的 Rust FFI 模块文件内容。"""
    header_comment = f"//! 原 C 头文件：{original_header}" if original_header else f"//! 原 C 模块：{mod_name}"
    lines = [
        f"//! FFI 封装：{mod_name} 模块",
        header_comment,
        f"//! 生成时间：{timestamp}",
        f"//! 警告：此文件由 gen_rust_ffi.py 自动生成，请在人工审核后修改。",
        "",
        "#![allow(non_camel_case_types, non_snake_case, dead_code, unused_imports)]",
        "",
        "use std::ffi::{c_int, c_uint, c_long, c_ulong, c_short, c_char, c_void, c_float, c_double};",
        "",
    ]

    if not interfaces:
        lines += [
            "// TODO: 此模块未检测到北向接口，请人工填写。",
            "",
        ]
        return "\n".join(lines)

    # 占位类型：为未知 C struct/typedef 生成不透明 Rust 结构体
    placeholders = _collect_placeholder_types(interfaces)
    for ph in placeholders:
        lines += [
            f"/// 不透明 C 类型占位符，人工审核时请替换为真实的 `#[repr(C)]` 定义。",
            f"#[repr(C)]",
            f"pub struct {ph} {{",
            f"    _opaque: [u8; 0],",
            f"}}",
            "",
        ]

    # extern "C" 块（包裹在 mod sys 中）
    # 每个绑定用 #[link_name] 显式指定 C 符号名，Rust 侧使用 __c_ 前缀，
    # 避免 release 构建中公开 wrapper（同名 #[no_mangle]）与 extern 引用形成循环。
    lines += [
        "mod sys {",
        "    #[allow(unused_imports)]",
        "    use super::*;",
        "    extern \"C\" {",
    ]
    for iface in interfaces:
        params_str = _build_rust_params(iface.get("params", []))
        ret = map_c_type(iface.get("return_type", "int"))
        func = iface["function"]
        lines.append(f"        #[link_name = \"{func}\"]")
        lines.append(f"        pub(super) fn __c_{func}({params_str}) -> {ret};")
    lines += ["    }", "}", ""]

    # 公开封装函数（pub extern "C"），通过 sys::__c_ 调用原始 C 函数。
    # C 对象（由 build.rs 经 hicc-build 编译）直接导出同名符号，此处不加 #[no_mangle] 避免符号重复定义。
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
            f"pub unsafe extern \"C\" fn {func}({params_str}) -> {ret} {{",
            f"    sys::__c_{func}({params_call})",
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


def write_mod_rs_files(src_dir: Path, module_tree: dict, timestamp: str):
    """
    为每个中间层目录写入 mod.rs，声明其直接子模块。
    仅写入有子模块的中间层（叶子节点由调用方直接生成 .rs 文件）。
    """
    # tree 的 key 是 parent_tuple；() 表示顶层（对应 lib.rs，单独处理）
    for parent_tuple, children in sorted(module_tree.items()):
        if not parent_tuple:
            continue  # 顶层由 update_lib_rs 负责
        # 检查这个父目录是否真的需要 mod.rs
        # （当 children 集合非空，说明 parent_tuple 对应一个目录而非叶子）
        dir_path = src_dir / Path(*parent_tuple)
        dir_path.mkdir(parents=True, exist_ok=True)
        mod_decls = "\n".join(f"pub mod {c};" for c in sorted(children))
        mod_rs_content = (
            f"//! 子模块：{' > '.join(parent_tuple)}\n"
            f"//! 生成时间：{timestamp}\n"
            f"\n"
            f"{mod_decls}\n"
        )
        mod_rs_path = dir_path / "mod.rs"
        mod_rs_path.write_text(mod_rs_content, encoding="utf-8")
        try:
            display = mod_rs_path.relative_to(src_dir.parent.parent)
        except ValueError:
            display = mod_rs_path
        print(f"✓ 已生成 {display}")


def update_lib_rs(src_dir: Path, module_tree: dict, timestamp: str):
    """更新 lib.rs，仅声明顶层模块（由 build_module_tree 的 () key 给出）。"""
    lib_path = src_dir / "lib.rs"
    top_modules = sorted(module_tree.get((), set()))
    mod_decls = "\n".join(f"pub mod {m};" for m in top_modules)
    module_list = "\n".join(f"//! - `{m}`" for m in top_modules)
    content = (
        f"//! c2rust-rs FFI 封装层\n"
        f"//! 生成时间：{timestamp}\n"
        f"//!\n"
        f"//! # 顶层模块\n"
        f"{module_list}\n"
        f"//!\n"
        f"//! 模块结构镜像原 C 项目的头文件目录层级。\n"
        f"\n"
        f"{mod_decls}\n"
    )
    lib_path.write_text(content, encoding="utf-8")
    print(f"✓ 已更新 lib.rs")


# ──────────────────────────────────────────────
# 解析输入：spec.json（推荐）或 interfaces.md（兼容）
# ──────────────────────────────────────────────

def parse_spec_json(spec_path: Path) -> list:
    """
    从 spec.json 读取模块信息，保留 header 路径用于推导 Rust 模块层级。

    返回每个模块的 dict，包含 name、header、north_interfaces 字段。
    """
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    modules = []
    for mod in data.get("modules", []):
        modules.append({
            "name": mod.get("name", "unknown"),
            "header": mod.get("header", ""),
            "north_interfaces": mod.get("north_interfaces", []),
        })
    return modules


def parse_interfaces_md(md_path: Path) -> list:
    """从 interfaces.md 提取模块和接口信息（兼容模式，不含路径信息）。"""
    text = md_path.read_text(encoding="utf-8")
    modules = []
    current_mod = None

    for line in text.splitlines():
        # 模块标题
        m = re.match(r'^## 模块：(\S+)', line)
        if m:
            if current_mod:
                modules.append(current_mod)
            current_mod = {"name": m.group(1), "header": "", "north_interfaces": []}
            continue

        if current_mod is None:
            continue

        # 函数行（表格行）
        m = re.match(r'^\|\s*`(\w+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|', line)
        if m:
            func_name = m.group(1)
            sig = m.group(2)
            ret_type = m.group(3)
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
            # 指针符号可能附在变量名前（如 int *ptr）——将其归还给类型
            while pname.startswith("*"):
                ptype = ptype + " *"
                pname = pname[1:]
        else:
            ptype, pname = p, ""
        params.append({"name": pname, "type": ptype.strip(), "direction": "in"})
    return params


# ──────────────────────────────────────────────
# 主逻辑
# ──────────────────────────────────────────────

def gen_ffi(input_path: str, output_src_dir: str):
    in_path = Path(input_path).resolve()
    src_dir = Path(output_src_dir).resolve()

    if not in_path.exists():
        print(f"错误：输入文件不存在：{in_path}")
        sys.exit(1)

    src_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 选择解析器
    if in_path.suffix == ".json":
        modules = parse_spec_json(in_path)
        if not modules:
            print("警告：spec.json 中未找到任何模块（modules 为空）。")
            sys.exit(1)
        print(f"✓ 从 spec.json 读取 {len(modules)} 个模块（层级模式）")
    else:
        modules = parse_interfaces_md(in_path)
        if not modules:
            print("警告：未从 interfaces.md 中解析到任何模块，请检查文件格式。")
            sys.exit(1)
        print(f"✓ 从 interfaces.md 读取 {len(modules)} 个模块（兼容平铺模式）")

    # 为每个模块推导 Rust 模块路径
    module_paths = []
    for mod in modules:
        header = mod.get("header", "")
        if header:
            path = header_to_module_path(header)
        else:
            # 无路径信息时，按模块名平铺
            path = [re.sub(r"[^a-zA-Z0-9_]", "_", mod["name"])]
        mod["_rust_path"] = path
        module_paths.append(path)

    # 构建模块树（用于生成 lib.rs 和各级 mod.rs）
    module_tree = build_module_tree(module_paths)

    # 检测 leaf 名称与中间层目录名冲突（e.g. net/io.h + net/io/buffered.h）
    intermediate_paths = {parent for parent in module_tree if parent}
    for mod in modules:
        parts = mod["_rust_path"]
        if tuple(parts) in intermediate_paths:
            print(f"⚠ 警告：模块路径 {'/'.join(parts)} 既是叶子又是中间目录前缀，"
                  f"将生成冲突的 {'/'.join(parts)}.rs 与 {'/'.join(parts)}/mod.rs。"
                  f"请人工重命名对应 C 头文件或模块。")

    # 生成各叶子模块的 .rs 文件
    for mod in modules:
        parts = mod["_rust_path"]
        mod_name = parts[-1]
        # 叶子文件路径：src_dir / part0 / part1 / ... / leaf.rs
        out_file = src_dir / Path(*parts[:-1], f"{mod_name}.rs") if len(parts) > 1 else src_dir / f"{mod_name}.rs"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        content = gen_module_rs(mod_name, mod["north_interfaces"], timestamp, mod.get("header", ""))
        out_file.write_text(content, encoding="utf-8")
        rust_path = "::".join(parts)
        try:
            display = out_file.relative_to(src_dir.parent.parent)
        except ValueError:
            display = out_file
        print(f"✓ 已生成 {display}  （Rust 路径：{rust_path}）")

    # 生成中间层 mod.rs 文件
    write_mod_rs_files(src_dir, module_tree, timestamp)

    # 更新 lib.rs（仅顶层模块）
    update_lib_rs(src_dir, module_tree, timestamp)

    print(f"\n共生成 {len(modules)} 个叶子模块文件。")
    print("⚠ 请人工审核生成的 Rust 代码，特别是：")
    print("  - 不认识的 C 类型已被替换为 PascalCase 占位名，需手动补充 #[repr(C)] 定义")
    print("  - 函数封装层默认 1:1 透传，如需添加安全检查请手动修改")
    print("  - 运行 verify_symbols.sh 验证导出符号表")


def main():
    if len(sys.argv) != 3:
        print("用法：python scripts/gen_rust_ffi.py <spec_json_or_interfaces_md> <output_src_dir>")
        sys.exit(1)
    gen_ffi(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
