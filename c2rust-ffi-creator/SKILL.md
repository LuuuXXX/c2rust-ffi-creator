---
name: c2rust-ffi-creator
description: 此技能应在需要将 C/C++ 项目迁移至 Rust FFI 封装层时使用。以 hicc 框架为核心工具，提供结构化的分析、代码提取、Rust 封装生成（通过 hicc::cpp! + hicc::import_lib! + hicc-build）、FFI 实现和符号一致性验证全流程指南，通过显式约束与脚本自动化减少对大模型即兴能力的依赖。
---

# C2Rust FFI Creator

## 概述

将 C/C++ 项目迁移为 Rust FFI 封装层的完整工作流程，以 **hicc** 框架为核心。通过结构化分析、模板化脚手架和自动验证脚本，确保迁移前后功能等价，并生成可维护的 Rust crate。

**核心原则：** 通过工具化、模板化、约束化减少对大模型自由发挥的依赖——每一步都有明确的输入、输出和验证标准。

---

## hicc 框架介绍

[hicc](https://crates.io/crates/hicc) 是专为 **Rust ↔ C/C++ FFI** 设计的 crate，通过过程宏实现安全高效的互调。

### 核心组件

| 组件 | 用途 |
|------|------|
| `hicc = "0.2"` | 运行时依赖（`[dependencies]`）：提供 `hicc::cpp!` / `hicc::import_lib!` 宏 |
| `hicc-build = "0.2"` | 构建时依赖（`[build-dependencies]`）：从 Rust 文件提取 `cpp!` 块并编译 C++ 适配代码 |
| `cc = "1.0"` | 构建时依赖（`[build-dependencies]`）：用 C 编译器编译原始 C 源码 |

### 三个核心宏

#### `hicc::cpp!` — 嵌入 C++ 适配代码

在 Rust 文件中嵌入 C++ 代码块。`hicc-build` 会提取这些块、生成 C++ 适配文件并编译：

```rust
hicc::cpp! {
    extern "C" {
        #include "mylib.h"   // 包含原始 C/C++ 头文件
    }

    // C++ 适配函数，将 C/C++ API 转换为 void* 接口供 Rust 调用
    void* lib_new_adapter() {
        return (void*)lib_new();
    }

    int lib_do_something_adapter(void* handle, const char* input) {
        return lib_do_something((lib_handle_t*)handle, input);
    }
}
```

#### `hicc::import_lib!` — 声明 Rust 可调用的适配函数

声明 `hicc::cpp!` 中定义的 C++ 适配函数为 Rust 可调用：

```rust
hicc::import_lib! {
    #![link_name = "lib_adapter"]   // 与 hicc_build::Build::compile("lib_adapter") 一致

    #[cpp(func = "void* lib_new_adapter()")]
    pub fn lib_new_adapter() -> *mut std::os::raw::c_void;

    #[cpp(func = "int lib_do_something_adapter(void* handle, const char* input)")]
    pub fn lib_do_something_adapter(
        handle: *mut std::os::raw::c_void,
        input:  *const std::os::raw::c_char,
    ) -> std::os::raw::c_int;
}
```

#### `hicc::import_class!` — 声明 C++ 类（仅 C++ 库）

直接封装 C++ 类（含虚函数、模板等），无需手写适配函数：

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

---

## 前置要求检查

```bash
cargo --version          # Rust 工具链 (>= 1.70)
nm --version             # 符号表工具 (binutils)
gcc --version            # C 编译器
g++ --version            # C++ 编译器（hicc-build 需要）
cmake --version          # 构建工具（用于运行原 C 测试套件）
python3 --version        # Python 3 (>= 3.8)
```

---

## 工作流程（按顺序执行，勿跳过）

### 第一步：初始化 Rust 项目骨架

```bash
cargo new c2rust-rs --lib
cd c2rust-rs
```

编辑 `Cargo.toml`，添加 hicc 依赖：

```toml
[dependencies]
hicc = "0.2"           # 运行时：提供 hicc::cpp! / hicc::import_lib! 宏

[build-dependencies]
hicc-build = "0.2"     # 构建时：从 Rust 文件提取 cpp! 块并编译 C++ 适配代码
cc = "1.0"             # 构建时：用 C 编译器编译原始 C 源码
```

**预期产物：** `c2rust-rs/` 目录，包含 `Cargo.toml`（含 hicc 依赖）、`src/lib.rs`。

---

### 第二步：复制 C 源代码并保持目录结构

将原 C 项目的核心代码和测试代码复制到 `c2rust-rs/.c2rust/c/`：

```bash
scripts/copy_c_sources.sh <原C项目路径> <c2rust-rs路径>
```

该脚本将：
1. 复制所有 `.c`、`.h`（或 `.cpp`、`.hpp`）文件到 `c2rust-rs/.c2rust/c/`，**保持原目录结构**
2. 复制测试目录和构建文件（`CMakeLists.txt`、`Makefile` 等）
3. 生成复制清单 `MANIFEST.txt`

**严格约束：不修改任何 C/C++ 源文件，保留原始注释和许可证头。**

---

### 第三步：分析 C/C++ 项目并生成元数据

```bash
cd c2rust-rs
scripts/analyze_c_project.sh .c2rust/c
```

该脚本生成以下文件（写入 `.c2rust/c/`）：

| 文件 | 内容 |
|------|------|
| `PROJECT_SPEC.md` | 项目规格（功能/产物类型/依赖库） |
| `INTERFACES.md` | 各模块南北向接口规格（函数签名/参数类型/返回值/内存所有权） |
| `BUILD_PLAN.md` | 构建方案 |
| `TEST_PLAN.md` | 测试方案 |

**分析要点：**
- 识别对外导出头文件（通常在 `include/` 或项目根目录）
- 记录函数签名：参数类型/返回值/错误码/内存所有权/线程安全标注
- 识别不透明指针（opaque handle）模式：`typedef struct Foo Foo_t;`

---

### 第四步：构建并验证原 C/C++ 版本

在开始 Rust 转换前，先确保原版本可以正常构建和测试：

```bash
cd c2rust-rs
scripts/build_c.sh .c2rust/c
scripts/test_c.sh .c2rust/c
```

**预期输出：**
- 构建成功
- 所有 C/C++ 测试通过
- 生成 `symbols_c.txt`（原版本导出符号表）

---

### 第五步：编写 hicc FFI 适配层（`src/ffi.rs`）

创建 `src/ffi.rs`，包含 `hicc::cpp!` 适配代码和 `hicc::import_lib!` 声明。

**通用模式（C 库）：**

```rust
// src/ffi.rs
use std::os::raw::{c_char, c_int};

// C++ 适配层：用 void* 封装不透明 C 句柄，避免 Rust 侧依赖具体类型定义。
hicc::cpp! {
    extern "C" {
        #include "mylib.h"
    }

    void* lib_new_adapter(int cap) {
        return (void*)lib_new(cap);
    }

    void lib_free_adapter(void* h) {
        lib_free((lib_t*)h);
    }

    int lib_set_adapter(void* h, const char* k, const char* v) {
        return lib_set((lib_t*)h, k, v);
    }
}

hicc::import_lib! {
    #![link_name = "lib_adapter"]

    #[cpp(func = "void* lib_new_adapter(int cap)")]
    pub fn lib_new_adapter(cap: c_int) -> *mut std::os::raw::c_void;

    #[cpp(func = "void lib_free_adapter(void* h)")]
    pub fn lib_free_adapter(h: *mut std::os::raw::c_void);

    #[cpp(func = "int lib_set_adapter(void* h, const char* k, const char* v)")]
    pub fn lib_set_adapter(
        h: *mut std::os::raw::c_void,
        k: *const c_char,
        v: *const c_char,
    ) -> c_int;
}

// 状态码常量（与 C 头文件中的枚举对应）
pub const LIB_OK: c_int      =  0;
pub const LIB_ERR_FAIL: c_int = -1;
```

**C++ 类模式（直接使用 `import_class!`）：**

```rust
// src/ffi.rs
hicc::import_class! {
    #[cpp(class = "MyClass")]
    struct MyClass {
        #[cpp(constructor = "MyClass()")]
        fn new() -> MyClass;

        #[cpp(method = "int getValue() const")]
        fn get_value(&self) -> i32;

        #[cpp(method = "void setValue(int v)")]
        fn set_value(&mut self, v: i32);
    }
}
```

---

### 第六步：编写 `build.rs`

```rust
// build.rs
fn main() {
    // 1. 用 C 编译器编译原始 C 源码
    cc::Build::new()
        .file(".c2rust/c/src/mylib.c")
        .include(".c2rust/c/include")
        .compile("mylib_c");

    // 2. 用 hicc-build 从 src/ffi.rs 提取 cpp! 块并以 C++ 编译
    hicc_build::Build::new()
        .rust_file("src/ffi.rs")
        .include(".c2rust/c/include")
        .compile("lib_adapter");

    println!("cargo::rustc-link-lib=mylib_c");
    println!("cargo::rustc-link-lib=lib_adapter");
    println!("cargo::rustc-link-lib=stdc++");
    println!("cargo::rerun-if-changed=src/ffi.rs");
    println!("cargo::rerun-if-changed=.c2rust/c/src/mylib.c");
}
```

**关键点：**
- C 源码必须用 `cc::Build`（C 编译器）编译，不能混入 hicc-build（C++ 编译器），因为 C 代码中的隐式 `void*` 转换在 C++ 编译器下会报错
- `hicc_build::Build::compile("lib_adapter")` 的参数必须与 `hicc::import_lib!` 中的 `#![link_name = "lib_adapter"]` 完全一致
- 始终添加 `println!("cargo::rustc-link-lib=stdc++")` 链接 C++ 标准库

---

### 第七步：编写安全 Rust 封装层（`src/lib.rs`）

```rust
// src/lib.rs
mod ffi;

use std::ffi::{CStr, CString};

pub struct MyLib {
    ptr: *mut std::os::raw::c_void,
}

impl MyLib {
    pub fn new(cap: i32) -> Option<Self> {
        let ptr = ffi::lib_new_adapter(cap);
        if ptr.is_null() { None } else { Some(MyLib { ptr }) }
    }

    pub fn set(&mut self, key: &str, value: &str) -> Result<(), i32> {
        let k = CString::new(key).map_err(|_| -1)?;
        let v = CString::new(value).map_err(|_| -1)?;
        let rc = ffi::lib_set_adapter(self.ptr, k.as_ptr(), v.as_ptr());
        if rc == ffi::LIB_OK { Ok(()) } else { Err(rc) }
    }
}

impl Drop for MyLib {
    fn drop(&mut self) {
        ffi::lib_free_adapter(self.ptr);
    }
}
```

**安全封装原则：**
- 使用 `CString::new(s)?` 处理字符串转换，拒绝含 `\0` 的输入
- 使用 `unsafe { CStr::from_ptr(ptr).to_string_lossy().into_owned() }` 复制 C 返回的字符串
- 实现 `Drop`，在析构时调用对应的 `*_free_adapter` 函数
- 将 C 错误码映射为 Rust `Result` 或自定义 `Error` 枚举

---

### 第八步：构建 Rust 版本

```bash
cd c2rust-rs
cargo build --release
```

**构建失败诊断（见 `references/troubleshooting.md`）：**
- `undefined reference`：检查 `build.rs` 链接配置及 `link_name` 是否与 `compile()` 参数一致
- `type mismatch`：检查 C 类型与 Rust 类型对应（见 `references/type_mapping.md`）
- `hicc-build` 失败：检查 `g++` 是否安装，以及 C++ 头文件路径是否正确
- C 源码用 C++ 编译出错：确认 C 源码用 `cc::Build` 单独编译，不混入 `hicc_build::Build`

---

### 第九步：运行 Rust 测试（1:1 对应 C 测试）

```bash
cd c2rust-rs
cargo test
```

**测试覆盖要求：**
- `tests/integration_test.rs` 中每个原版本 C 测试用例都应有对应的 Rust 测试（1:1 迁移）
- 使用完全相同的输入数据，对比输出结果
- 边界条件（NULL 输入、空字符串、内存分配失败）必须覆盖

---

## Rust crate 布局约定

```
c2rust-rs/
├── Cargo.toml              # hicc + hicc-build + cc 依赖
├── build.rs                # cc::Build (C源码) + hicc_build::Build (C++适配层)
├── src/
│   ├── lib.rs              # 公开的安全 Rust API（RAII 封装、错误类型）
│   ├── ffi.rs              # hicc::cpp! 适配代码 + hicc::import_lib! 声明
│   └── error.rs            # 错误码映射（C 状态码 → Rust Result/Error）
├── tests/
│   └── integration_test.rs # 集成测试（1:1 对应 C 测试用例）
└── .c2rust/
    └── c/                  # C/C++ 源码副本（原文件不得修改）
        ├── include/        # 头文件
        ├── src/            # 实现文件
        └── tests/          # 原 C/C++ 测试套件
```

---

## 失败诊断指南

**问题：`link_name` 不匹配**
- 确认 `hicc::import_lib!` 中的 `#![link_name = "xxx"]` 与 `build.rs` 中 `hicc_build::Build::compile("xxx")` 完全一致

**问题：C 源码用 C++ 编译报隐式转换错误**
- 将 C 源码用 `cc::Build`（C 编译器）单独编译，`hicc_build::Build` 只编译 C++ 适配文件

**问题：`stdc++` 链接失败**
- 确认 `build.rs` 中包含 `println!("cargo::rustc-link-lib=stdc++")`
- 确认 `g++` 已安装（`apt install g++`）

**问题：`void*` 转换失败**
- 在 `hicc::cpp!` 的 C++ 适配函数中使用显式强制转换：`(lib_t*)handle`
- 不要在 Rust 侧使用具体的 C 结构体类型，统一用 `*mut std::os::raw::c_void`

**问题：类型不兼容**
- 参考 `references/type_mapping.md` 中的 C 到 Rust 类型对照表
- 对需要 C 布局的结构体使用 `#[repr(C)]`

---

## 资源

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
