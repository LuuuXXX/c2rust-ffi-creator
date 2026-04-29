---
name: c2rust-ffi-creator
description: 此技能应在用户需要将 C 项目迁移为 Rust FFI 封装层时使用。基于 hicc crate 搭建 Rust 项目框架，分析 C 项目的模块依赖与南北向接口，生成可构建、可测试的 Rust FFI 封装，并验证导出符号表与原 C 项目一致。
---

# C to Rust FFI Creator

## 概述

将现有 C 项目转换为 Rust FFI 封装层（`c2rust-rs`），使用 [hicc](https://crates.io/crates/hicc) crate 作为 Rust 侧的 FFI 框架基础。转换后的 Rust 项目需可构建、可测试，且导出符号表与原 C 项目完全一致。

## 工作流程

按以下六个阶段严格顺序执行。

---

### 阶段一：创建 c2rust-rs 项目骨架

1. 在工作目录下创建名为 `c2rust-rs` 的新目录。
2. 运行 `scripts/init_rust_project.sh c2rust-rs` 生成标准目录结构：
   ```
   c2rust-rs/
   ├── Cargo.toml          # 工作空间 manifest
   ├── .c2rust/
   │   └── c/              # 存放原 C 项目代码和分析产物
   ├── ffi/                # Rust FFI 封装 crate
   │   ├── Cargo.toml
   │   └── src/
   │       └── lib.rs
   └── tests/              # 集成测试
       └── ffi_tests.rs
   ```
3. 在 `Cargo.toml` 中加入 `hicc` 依赖（见 `references/hicc-guide.md` §配置）。

---

### 阶段二：分析 C 项目，复制核心代码

1. 将原 C 项目的**核心源码**（`.c` / `.h`）复制到 `c2rust-rs/.c2rust/c/src/`。
2. 将原 C 项目的**测试代码**（`test_*.c` / `*_test.c`）复制到 `c2rust-rs/.c2rust/c/tests/`。
3. 运行 `scripts/analyze_c_project.py c2rust-rs/.c2rust/c` 自动提取：
   - 目录结构与模块划分
   - 公开头文件（北向接口）
   - 内部模块间调用（南向依赖）
   - Makefile / CMakeLists 中的构建目标与测试命令
4. 分析结果写入 `c2rust-rs/.c2rust/c/spec.json`（结构见 `references/c-project-spec.md`）。

---

### 阶段三：提取规格，建立接口清单

参考 `references/c-project-spec.md` 中的规格模板，基于 `spec.json` 补充以下内容并写入 `c2rust-rs/.c2rust/c/interfaces.md`：

| 字段 | 说明 |
|------|------|
| 模块名 | 与头文件对应的逻辑模块 |
| 北向接口 | 对外暴露的函数签名（含参数类型、返回值） |
| 南向依赖 | 该模块依赖的其他模块或外部库 |
| 数据契约 | 关键结构体、枚举、宏 |
| 测试覆盖 | 已有 C 测试所覆盖的函数列表 |

---

### 阶段四：使用 hicc 生成 Rust FFI 封装层

1. 运行 `scripts/gen_rust_ffi.py c2rust-rs/.c2rust/c/interfaces.md c2rust-rs/ffi/src` 生成：
   - `lib.rs`：模块入口，`#[no_mangle]` + `extern "C"` 函数声明
   - 每个模块对应一个 `<module>.rs` 文件
2. 按照 `references/hicc-guide.md` 中的规范编写每个 FFI 函数的 Rust 实现：
   - 使用 `hicc::bridge` 宏（或手动 `extern "C"` 块）包装 C 函数。
   - 所有裸指针操作须包裹在 `unsafe` 块中，并添加安全注释。
   - 结构体映射使用 `#[repr(C)]`。
3. 确认 `ffi/Cargo.toml` 中 `crate-type = ["cdylib", "staticlib"]`。

---

### 阶段五：转换 C 测试为 Rust 测试

1. 对照 `c2rust-rs/.c2rust/c/tests/` 中的每个 C 测试文件，在 `c2rust-rs/tests/` 下生成对应的 Rust 测试文件。
2. 遵循转换规则（详见 `references/test-conversion.md`）：
   - `assert(expr)` → `assert!(expr)`
   - `assert_eq(a, b)` → `assert_eq!(a, b)`
   - C 字符串字面量 → `CString::new(...).unwrap()`
   - 内存分配 / 释放 → Rust 所有权语义或 `unsafe` 块
3. 每个 Rust 测试函数保留原 C 测试函数名作为注释，便于追溯。

---

### 阶段六：验证构建与符号表

1. 执行构建验证：
   ```bash
   cargo build --release -p ffi
   ```
2. 运行测试：
   ```bash
   cargo test -p ffi
   ```
3. 运行 `scripts/verify_symbols.sh c2rust-rs` 比较 Rust 产物与原 C 产物的导出符号表：
   - 差异为零则通过，否则输出 diff 报告并修复。
4. 将最终符号表写入 `c2rust-rs/.c2rust/c/symbols_expected.txt`。

---

## 约束与质量门控

为减少大模型推断，执行过程中须遵守以下约束：

- **禁止推断未经验证的 C 函数签名**：所有函数签名须从头文件直接提取，不得凭经验填写。
- **禁止跳过符号验证步骤**：阶段六必须执行，符号差异必须修复后方可视为完成。
- **禁止删除 `unsafe` 块**：凡涉及裸指针或 FFI 调用，一律保留 `unsafe` 并添加安全注释。
- **crate-type 强制要求**：`ffi` crate 必须同时声明 `cdylib` 和 `staticlib`，确保动静态库均可导出。
- **测试覆盖率**：Rust 测试数量不得少于原 C 测试函数数量。

## 资源

- `scripts/init_rust_project.sh` — 初始化 c2rust-rs 项目目录结构
- `scripts/analyze_c_project.py` — 分析 C 项目，生成 spec.json
- `scripts/gen_rust_ffi.py` — 基于接口清单生成 Rust FFI 骨架代码
- `scripts/verify_symbols.sh` — 对比 C/Rust 导出符号表
- `references/c-project-spec.md` — C 项目规格模板与字段说明
- `references/hicc-guide.md` — hicc crate 配置与使用指南
- `references/test-conversion.md` — C 测试到 Rust 测试转换规则
- `references/symbol-export.md` — 符号表导出与验证方法
- `assets/Cargo.toml.template` — 工作空间 Cargo.toml 模板
- `assets/ffi-Cargo.toml.template` — ffi crate Cargo.toml 模板
