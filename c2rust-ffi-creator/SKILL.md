---
name: r2rust-ffi-creator
description: 此技能应在需要将 C/C++ 项目迁移至 Rust FFI 封装层时使用。它提供结构化的分析、代码提取、Rust 骨架生成（纯 C 库使用 bindgen，C++ 库使用 hicc 宏）、FFI 封装实现和符号一致性验证全流程指南，通过显式约束与脚本自动化减少对大模型即兴能力的依赖。
---

# R2Rust FFI Creator

## 概述

将 C/C++ 项目迁移为 Rust FFI 封装层的完整工作流程。通过结构化分析、模板化脚手架和自动验证脚本，确保转换前后的二进制导出符号一致，并生成可维护的 Rust crate。

**核心原则：** 通过工具化、模板化、约束化减少对大模型自由发挥的依赖——每一步都有明确的输入、输出和验证标准。

---

## 工具选择

根据被封装库的语言选择不同的 FFI 工具：

| 原始库语言 | 推荐工具 | crate 来源 |
|------------|----------|------------|
| 纯 C 库（`.c`/`.h`）| `bindgen` + `cc` | `[build-dependencies]` |
| C++ 库（`.cpp`/`.hpp`，含类/模板/虚函数）| `hicc` + `hicc-build` | `[dependencies]` + `[build-dependencies]` |

---

## 前置要求检查

在开始前，验证以下工具已安装：

```bash
cargo --version          # Rust 工具链 (>= 1.70)
nm --version             # 符号表工具 (binutils)
gcc --version            # C 编译器
g++ --version            # C++ 编译器（迁移 C++ 库时需要）
python3 --version        # Python 3 (>= 3.8)
# 若迁移 C++ 库，还需安装 hicc 的 C++ 运行时头文件：
# cargo add hicc          # 运行时依赖（提供宏）
# cargo add --build hicc-build  # 构建依赖（编译 C++ 适配代码）
```

---

## 工作流程（按顺序执行，勿跳过）

### 第一步：初始化 c2rust-rs 项目骨架

使用标准 Cargo 并应用 FFI 约定布局：

```bash
# 在目标目录下执行
cargo new c2rust-rs --lib
cd c2rust-rs
# 然后手动应用 assets/rust-ffi-template/ 中的目录布局
```

**预期产物：** `c2rust-rs/` 目录，包含 `Cargo.toml`、`src/lib.rs`、`build.rs`（初始）。

---

### 第二步：复制 C 源代码并保持目录结构

将原 C 项目的核心代码和测试代码复制到 `c2rust-rs/.c2rust/c/`：

```bash
# 从原 C 项目根目录执行
scripts/copy_c_sources.sh <原C项目路径> <c2rust-rs路径>
```

该脚本将：
1. 复制所有 `.c`、`.h`（或 `.cpp`、`.hpp`）文件到 `c2rust-rs/.c2rust/c/`，**保持原目录结构**
2. 复制测试目录（通常为 `tests/`、`test/`、`*_test.c`）
3. 复制构建文件（`CMakeLists.txt`、`Makefile`、`meson.build` 等）
4. 生成复制清单 `c2rust-rs/.c2rust/c/MANIFEST.txt`

**严格约束：**
- 不修改任何 C/C++ 源文件
- 保留原始注释和许可证头
- 目录层级与原项目完全一致

---

### 第三步：分析 C/C++ 项目并生成元数据

运行分析脚本提取项目规格：

```bash
cd c2rust-rs
scripts/analyze_c_project.sh .c2rust/c
```

该脚本生成以下文件（写入 `.c2rust/c/`）：

| 文件 | 内容 |
|------|------|
| `PROJECT_SPEC.md` | 项目规格（功能/产物类型/依赖库） |
| `MODULE_DEPS.md` | 模块划分与依赖关系图 |
| `INTERFACES.md` | 各模块南北向接口规格 |
| `BUILD_PLAN.md` | 构建方案（编译器/flags/步骤） |
| `TEST_PLAN.md` | 测试方案（测试入口/预期输出） |

**分析要点（逐文件检查）：**
- 识别对外导出头文件（通常在 `include/` 或项目根目录）
- 识别 `__attribute__((visibility("default")))` 或无 `static` 的全局函数
- 分析 `#include` 依赖图，确定模块边界
- 记录函数签名：参数类型/返回值/错误码/内存所有权/线程安全标注

**南北向接口定义：**
- **北向（Northbound）**：模块向上层暴露的接口（调用方视角）
- **南向（Southbound）**：模块依赖下层的接口（被调用方视角）

若分析脚本无法自动提取，手动补充 `INTERFACES.md`，格式见 `references/interface_template.md`。

---

### 第四步：构建并验证原 C/C++ 版本

在开始 Rust 转换前，先确保 C/C++ 版本可以正常构建和测试：

```bash
cd c2rust-rs
scripts/build_c.sh .c2rust/c
scripts/test_c.sh .c2rust/c
```

**预期输出：**
- 构建成功，生成动态库或静态库（`.so`/`.a`/`.dylib`）
- 所有 C/C++ 测试通过
- 生成 `c2rust-rs/.c2rust/c/symbols_c.txt`（原版本导出符号表）

提取原版本符号表（用于后续对比）：

```bash
scripts/extract_symbols.sh .c2rust/c/libXXX.so > .c2rust/c/symbols_c.txt
```

---

### 第五步：生成 Rust FFI 封装层

根据原始库语言选择工具：

#### 方案 A：纯 C 库 → 使用 `bindgen` + `cc`

`bindgen` 从 C 头文件自动生成 Rust 的 `extern "C"` 绑定；`cc` 将 C 源码编译为静态库。

**`Cargo.toml` 构建依赖：**

```toml
[build-dependencies]
bindgen = "0.69"   # 从 C 头文件生成 Rust 类型和 extern "C" 声明
cc = "1.0"         # 将 C 源码编译为静态库
```

**`build.rs` 示例：**

```rust
use std::path::PathBuf;

fn main() {
    // 1. 编译 C 源码
    cc::Build::new()
        .file(".c2rust/c/src/library.c")
        .include(".c2rust/c/include")
        .compile("mylib");

    // 2. 生成 Rust 绑定
    let bindings = bindgen::Builder::default()
        .header(".c2rust/c/include/api.h")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    let out_dir = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_dir.join("bindings.rs"))
        .expect("Couldn't write bindings!");
}
```

**`src/lib.rs` 中引入绑定：**

```rust
mod sys {
    #![allow(non_upper_case_globals, non_camel_case_types, non_snake_case, dead_code)]
    include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
}
```

---

#### 方案 B：C++ 库 → 使用 `hicc` + `hicc-build`

`hicc` 是专为 C++ FFI 设计的 Rust crate，通过过程宏实现安全、高效的 Rust ↔ C++ 互调。它支持 C++ 类、模板、函数重载、虚函数等特性。

**工作原理：**
1. 在 Rust 源文件中用 `hicc::cpp!` 宏嵌入 C++ 适配代码
2. 用 `hicc::import_lib!` / `hicc::import_class!` 声明 Rust 调用的 C++ API
3. `build.rs` 中用 `hicc_build::Build` 从 Rust 文件提取 `hicc::cpp!` 块，自动生成并编译 C++ 适配代码

**`Cargo.toml` 依赖：**

```toml
[dependencies]
hicc = "0.2"           # 运行时：提供 hicc::cpp! / hicc::import_lib! 宏

[build-dependencies]
hicc-build = "0.2"     # 构建时：从 Rust 文件提取 cpp! 块并编译 C++
cc = "1.0"             # 编译 C++ 源码（hicc-build 内部使用）
```

**`src/ffi.rs` 示例（函数级 C++ API）：**

```rust
use std::os::raw::{c_char, c_int};

// hicc::cpp! 宏中的 C++ 代码会被 hicc-build 提取并编译。
// extern "C" 块让 C++ 编译器识别 C 头文件中的函数。
hicc::cpp! {
    extern "C" {
        #include "api.h"
    }

    // C++ 适配函数：封装 C 或 C++ 接口供 hicc::import_lib! 声明
    int adapter_set(void* store, const char* key, const char* value) {
        return library_set((handle_t*)store, key, value);
    }
}

// import_lib! 声明 Rust 端可调用的 C++ 函数；
// link_name 对应 hicc_build::Build::compile("...") 的库名。
hicc::import_lib! {
    #![link_name = "my_adapter"]

    #[cpp(func = "int adapter_set(void* store, const char* key, const char* value)")]
    pub fn adapter_set(
        store: *mut std::os::raw::c_void,
        key:   *const c_char,
        value: *const c_char,
    ) -> c_int;
}
```

**`src/ffi.rs` 示例（C++ 类）：**

```rust
hicc::import_class! {
    #[cpp(class = "MyClass")]
    struct MyClass {
        #[cpp(method = "int get_value() const")]
        fn get_value(&self) -> i32;

        #[cpp(method = "void set_value(int v)")]
        fn set_value(&mut self, v: i32);
    }
}
```

**`build.rs` 示例：**

```rust
fn main() {
    // hicc_build 解析 src/ffi.rs 中的 hicc::cpp! 块，生成 C++ 适配代码并编译
    hicc_build::Build::new()
        .rust_file("src/ffi.rs")
        .include(".c2rust/c/include")    // C/C++ 头文件路径
        .file(".c2rust/c/src/impl.cpp")  // 需要链接的 C++ 源文件
        .compile("my_adapter");

    println!("cargo::rustc-link-lib=my_adapter");
    println!("cargo::rustc-link-lib=stdc++");
    println!("cargo::rerun-if-changed=src/ffi.rs");
}
```

**参考示例：** `examples/complex-kv-store/` 展示了纯 C 库用 `bindgen` 封装的完整流程。

---

**Rust crate 布局约定（必须遵守）：**

```
c2rust-rs/
├── Cargo.toml              # crate 元数据，cdylib/staticlib 类型
├── build.rs                # bindgen/hicc-build 调用及 C/C++ 编译
├── src/
│   ├── lib.rs              # 公开 API，安全封装 ffi/sys 模块
│   ├── ffi.rs              # hicc 宏（C++ 库）或 bindgen 生成（C 库）
│   └── error.rs            # 错误码转换（C errno / C++ exception → Rust Result）
├── tests/
│   └── integration_test.rs # 集成测试，对应原版本测试用例（1:1 迁移）
└── .c2rust/
    └── c/                  # C/C++ 源码副本与分析产物（原文件不得修改）
```

---

### 第六步：实现 Rust FFI 绑定

逐函数实现 Rust 版本，遵循以下约束：

**内存所有权规则：**
- C 分配的内存由 C 负责释放（通过对应的 `*_free` 函数）
- 若 C API 文档说"调用方负责释放"，在 Rust 中使用 `Box::into_raw` + drop 实现
- 使用 `std::ffi::CStr` / `CString` 处理字符串
- C++ 对象生命周期通过 `hicc::AbiClass` 和 Rust `Drop` 管理

**错误处理规则：**
- C 的负数返回值 → Rust `Result<T, i32>`
- C 的 NULL 指针返回 → Rust `Option<T>` 或 `Result<T, Error>`
- 保留原始错误码，不静默忽略

**线程安全标注：**
- 若 C 函数文档标注非线程安全，在 Rust 中用 `Mutex`/`RwLock` 包装
- 若 C 使用全局状态，在 Rust 中用 `lazy_static!` 或 `once_cell` 管理

---

### 第七步：构建 Rust 版本

```bash
cd c2rust-rs
cargo build --release
```

**构建失败诊断（见 `references/troubleshooting.md`）：**
- `undefined reference`：检查 `build.rs` 链接配置
- `type mismatch`：检查 C 类型与 Rust 类型对应（见 `references/type_mapping.md`）
- `bindgen` 失败：检查 `libclang` 是否安装（`apt install libclang-dev`）
- `hicc-build` 失败：检查 `g++` 是否安装，以及 C++ 头文件路径是否正确

---

### 第八步：验证符号一致性

```bash
cd c2rust-rs
scripts/verify_symbols.sh
```

该脚本执行：
1. 从 C/C++ 版本库提取导出符号 → `symbols_c.txt`
2. 从 Rust 版本库提取导出符号 → `symbols_rust.txt`
3. 对比两个符号表，输出差异报告

**通过标准：**
- `symbols_c.txt` 中所有公开符号必须在 `symbols_rust.txt` 中存在
- 符号名称完全匹配（注意：Rust 使用 `#[no_mangle]` 禁止名称改写）
- 若存在差异，脚本返回非零退出码，CI 将失败

---

### 第九步：运行 Rust 测试

```bash
cd c2rust-rs
cargo test
```

**测试覆盖要求：**
- `tests/integration_test.rs` 中每个原版本测试用例都应有对应的 Rust 测试（1:1 迁移）
- 使用相同的输入数据，对比输出结果
- 边界条件（NULL 输入、空字符串、整数溢出）必须覆盖

---

## 失败诊断指南

**问题：符号名称不匹配**
- 检查 C 函数是否使用了 `__attribute__((visibility("hidden")))`
- 确认 Rust 函数使用了 `#[no_mangle]` 和 `pub extern "C"`
- 检查是否存在名称改写（name mangling）：`nm -gD libXXX.so | grep FUNC`

**问题：链接错误**
- 确认 `Cargo.toml` 中 `crate-type` 包含 `cdylib` 或 `staticlib`
- 检查 `build.rs` 中 `println!("cargo:rustc-link-lib=...")` 配置
- 使用 `hicc` 时：确认 `println!("cargo::rustc-link-lib=stdc++")` 已添加

**问题：类型不兼容**
- 参考 `references/type_mapping.md` 中的 C 到 Rust 类型对照表
- 对复杂结构体使用 `#[repr(C)]`
- 使用 `hicc` 时：参考 `hicc` 文档中的 C++ ↔ Rust 类型映射表

**问题：hicc-build 编译失败**
- 确认 `g++` 已安装（`apt install g++`）
- 确认 `hicc-build` 中 `.include(path)` 包含所有必要头文件路径
- 检查 `hicc::cpp!` 块中的 C++ 语法（需 C++11 或更高版本）

---

## 资源

此技能包含以下支持资源：

### scripts/（脚本）
- `copy_c_sources.sh` - 将 C 源码复制到 `.c2rust/c/`
- `analyze_c_project.sh` - 分析 C 项目并生成元数据文档
- `build_c.sh` - 构建 C 版本库
- `test_c.sh` - 运行 C 测试
- `build_rust.sh` - 构建 Rust FFI 库
- `test_rust.sh` - 运行 Rust 测试
- `extract_symbols.sh` - 提取库文件导出符号
- `verify_symbols.sh` - 对比 C 和 Rust 版本导出符号

### references/（参考资料）
- `workflow.md` - 完整工作流程详细说明
- `type_mapping.md` - C 到 Rust 类型对照表
- `interface_template.md` - 南北向接口文档模板
- `troubleshooting.md` - 常见问题诊断指南

### assets/（素材）
- `rust-ffi-template/` - Rust FFI crate 目录模板（含 Cargo.toml、build.rs、src/）
- `c-demo/` - 示例 C 库（演示工作流程用）
