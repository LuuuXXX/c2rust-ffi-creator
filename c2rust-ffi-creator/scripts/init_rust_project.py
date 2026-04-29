#!/usr/bin/env python3
"""
init_rust_project.sh 的 Python 替代实现
在指定目录下创建标准的 c2rust-rs 项目骨架。

用法：
    python scripts/init_rust_project.py <output_dir>

示例：
    python scripts/init_rust_project.py ./c2rust-rs
"""

import sys
from pathlib import Path

WORKSPACE_CARGO_TOML = """\
[workspace]
members = ["ffi"]
resolver = "2"

[workspace.dependencies]
hicc = "0.2"
libc = "0.2"

[profile.release]
opt-level = 3
lto = true
"""

FFI_CARGO_TOML = """\
[package]
name = "ffi"
version = "0.1.0"
edition = "2021"

[lib]
name = "c2rust_ffi"
crate-type = ["cdylib", "staticlib"]

[dependencies]
hicc = { workspace = true }
libc = { workspace = true }

# [build-dependencies]
# hicc-build = "0.2"  # 取消注释以在 build.rs 中编译 C 代码
"""

FFI_LIB_RS = """\
//! c2rust-rs FFI 封装层
//!
//! 本 crate 由 c2rust-ffi-creator 技能生成。
//! 每个子模块对应原 C 项目的一个逻辑模块。
//!
//! # 安全性说明
//! 所有 `extern "C"` 函数均标注 `unsafe`，调用方须保证指针有效性。

// TODO: 为每个 C 模块添加对应的 mod 声明
// pub mod foo;
// pub mod bar;
"""

BUILD_RS = """\
// build.rs — 按需启用以在 Rust crate 中编译 C 源码
//
// 启用步骤：
//   1. 在 ffi/Cargo.toml 的 [build-dependencies] 中添加：
//          hicc-build = "0.2"
//   2. 将下方占位路径替换为 spec.json sources[] 中的实际路径
//      （禁止假设 src/ / include/ 等固定层级；路径须与原 C 项目目录树一致）
//   3. 删除外层 /* ... */ 注释，使代码生效
//
// /*
// fn main() {
//     hicc_build::Build::new()
//         .file("../.c2rust/c/<path/to/foo.c>")   // 替换为实际源文件路径
//         .include("../.c2rust/c/<path/to/includes>")
//         .compile("c2rust_c_core");
// }
// */

fn main() {
    // 占位实现：当前不编译任何 C 源码。
    // 启用 C 编译时请按上方注释操作，并将此空 main 替换为实际编译逻辑。
}
"""

FFI_TEST_RS = """\
//! 集成测试入口
//!
//! 在 tests/ 目录下添加与原 C 测试对应的 Rust 测试文件。

// 示例：
// mod test_foo;
// mod test_bar;
"""

GITIGNORE = """\
/target
Cargo.lock
*.so
*.a
*.dylib
.c2rust/c/spec.json.bak
"""

def create_project(output_dir: str):
    root = Path(output_dir).resolve()

    if root.exists():
        print(f"错误：目录已存在：{root}")
        sys.exit(1)

    print(f"正在创建 c2rust-rs 项目：{root}\n")

    dirs = [
        root,
        root / ".c2rust" / "c",   # 仅创建空目录；原 C 项目将以 cp -r 保留结构复制进来
        root / "ffi" / "src",
        root / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  创建目录：{d.relative_to(root)}")

    files = {
        root / "Cargo.toml": WORKSPACE_CARGO_TOML,
        root / ".gitignore": GITIGNORE,
        root / "ffi" / "Cargo.toml": FFI_CARGO_TOML,
        root / "ffi" / "src" / "lib.rs": FFI_LIB_RS,
        root / "ffi" / "build.rs": BUILD_RS,
        root / "tests" / "lib.rs": FFI_TEST_RS,
    }
    for path, content in files.items():
        path.write_text(content)
        print(f"  创建文件：{path.relative_to(root)}")

    # 创建 .c2rust/c/README.md 说明
    readme = root / ".c2rust" / "c" / "README.md"
    readme.write_text(
        "# 原始 C 项目代码\n\n"
        "此目录通过 `cp -r <原C项目根目录>/. .c2rust/c/` 完整复制，保留原始目录结构。\n\n"
        "**禁止**手动重组此目录结构，否则将破坏 `#include` 相对路径，\n"
        "导致无法在此目录内复现原 C 项目的构建与测试。\n\n"
        "## 分析产物（由工具自动生成）\n\n"
        "- `spec.json`：由 analyze_c_project.py 生成的项目规格\n"
        "- `interfaces.md`：人工可读的接口清单\n"
        "- `symbols_expected.txt`：从原 C 构建产物提取的预期导出符号表\n"
    )
    print(f"  创建文件：.c2rust/c/README.md")

    print(f"\n✓ 项目初始化完成：{root}")
    print("\n后续步骤：")
    print("  1. cp -r <原C项目根目录>/. .c2rust/c/  （保留完整目录结构）")
    print("  2. 在 .c2rust/c 内验证原 C 项目可以正常构建")
    print("  3. 运行 analyze_c_project.py 生成 spec.json")
    print("  4. 运行 gen_rust_ffi.py 生成 Rust FFI 骨架")

def main():
    if len(sys.argv) != 2:
        print("用法：python scripts/init_rust_project.py <output_dir>")
        sys.exit(1)
    create_project(sys.argv[1])

if __name__ == "__main__":
    main()
