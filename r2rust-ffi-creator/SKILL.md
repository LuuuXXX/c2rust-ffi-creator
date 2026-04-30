---
name: r2rust-ffi-creator
description: 此技能应在需要为已有 C 项目搭建 Rust FFI 适配层时使用，基于 hicc crate 完成 C 模块的渐进式 Rust 化重构。具体触发场景：用户希望将某个 C 模块的北向接口替换为 Rust 原生接口，同时保留原有 C 实现不动，通过 FFI 桥接过渡，最终实现安全的 Rust 接口对外暴露。
---

# r2rust-ffi-creator

## 前置条件

在开始本技能的任何步骤之前，须确认以下分析已完成：

1. **C 项目完整分析**（对应 `c2rust-migration-skill` 的 Step 0）：
   - 已识别所有北向接口（来自头文件 + 已构建二进制导出符号双重确认）
   - 每个北向函数的实现文件、内部调用链、全局变量依赖、数据类型已梳理
   - 现有 C 测试覆盖情况已确认（哪些接口有测试、哪些没有）
   - 上述结果已记录于 `c-project-analysis.md` 并经负责人签字

2. **ABI 冻结**（对应 `c2rust-migration-skill` 的 Step 3）：
   - 导出符号清单已最终确认（来自实测 `nm`/`objdump`）
   - 产物形式（staticlib / cdylib）和命名已确定

> 未完成上述前置条件时，不应开始搭建 FFI 脚手架层，否则可能因接口范围不清或实现依赖不明而导致翻译错误。

---

## 概述

基于 `hicc` crate，为已有 C 项目搭建 Rust FFI 适配层，采用"北向 FFI 脚手架 → Rust 接口设计 → FFI 驱动实现"三步渐进式重构策略，使 C 模块在不修改内部实现的前提下对外暴露符合 Rust 惯用法的安全接口。

## 工作流程

```
识别北向接口
     ↓
添加 C-ABI FFI 脚手架层（临时）
     ↓
设计 Rust 惯用接口
     ↓
用 FFI 调用 C 实现来实现 Rust 接口
     ↓
验证接口等价性 → 迭代优化
```

## 第一步：识别北向接口

**目标**：找出待重构 C 模块对外暴露的全部接口（即"北向接口"——模块提供给上层调用方的 API）。

> 若已完成 `c2rust-migration-skill` 的 Step 0，直接使用 `c-project-analysis.md` 第 3-4 节的结果，
> 以及 `spec-v1.yml` 的 `implementation_analysis` 节，无需重复分析。

执行以下分析：

1. 定位模块的公开头文件（`.h`），提取所有 `extern` 声明的函数签名。
2. **对照已构建二进制的 `nm`/`objdump` 导出符号**，确认北向接口范围（头文件声明 ≠ 实际导出符号，必须以实测为准）。
3. 区分北向接口（对外暴露）与南向接口（模块内部调用下层依赖）：仅针对北向接口建立 FFI 层。
4. 对每个北向函数，记录：
   - 函数签名（参数类型、返回值类型）
   - **实现依赖**（内部调用链、依赖的全局变量、使用的数据类型）
   - 内存所有权语义（谁分配、谁释放）
   - 错误处理惯例（返回码、errno、输出参数）
   - 线程安全性声明

**输出**：一份北向接口清单，格式如下：

```
函数名: foo_init
C 签名: int foo_init(FooCtx **ctx, const FooConfig *cfg)
语义: 分配并初始化上下文，调用方负责通过 foo_destroy() 释放
错误处理: 返回 0 表示成功，负值表示错误码
线程安全: 非线程安全，每个线程独立上下文
```

## 第二步：添加 C-ABI FFI 脚手架层

**目标**：为北向接口建立一层 C 风格的 FFI 绑定（最终将被移除的脚手架）。

在 Rust 侧使用 `hicc::import_lib!` 宏声明 C 函数绑定，参考 `references/hicc.md` 中的 API 使用指南。

**典型模式**：

```rust
// ffi/mod.rs —— FFI 脚手架层（临时，最终移除）
hicc::import_lib! {
    #![link_name = "foo"]          // 对应 C 库名（libfoo.a / libfoo.so）

    // 简单值类型函数
    #[cpp(func = "int foo_version()")]
    fn foo_version() -> i32;

    // 带指针参数的函数（注意所有权语义）
    #[cpp(func = "int foo_init(FooCtx**, const FooConfig*)")]
    fn foo_init(ctx: *mut *mut FooCtx, cfg: *const FooConfig) -> i32;

    #[cpp(func = "void foo_destroy(FooCtx*)")]
    fn foo_destroy(ctx: *mut FooCtx);
}

// 若 C 模块含 C++ 代码，可用 hicc::cpp! 嵌入必要的 C++ 适配代码
hicc::cpp! {
    extern "C" {
        // C 头文件包含（在 hicc 的 C++ 编译单元中引入）
    }
    #include "foo.h"
}
```

**注意事项**：
- 所有 `*mut` / `*const` 原始指针操作须在 `unsafe` 块中进行。
- 用 `#[repr(C)]` 修饰与 C 结构体对应的 Rust 结构体。
- 在 `build.rs` 中使用 `hicc_build::Build` 配置编译，参见 `references/hicc.md`。

## 第三步：设计 Rust 惯用接口

**目标**：基于北向接口语义，设计符合 Rust 所有权、错误处理和安全性惯用法的新接口。

对每个北向接口，确定：

| C 惯用法 | Rust 惯用法 |
|---|---|
| 返回错误码（int） | `Result<T, E>`，自定义错误枚举 |
| 输出参数（`T**`） | 直接作为函数返回值 |
| 手动内存管理 | RAII（实现 `Drop`） |
| 可空指针（nullable pointer） | `Option<T>` 或 `NonNull<T>` |
| 不透明句柄（opaque handle） | newtype 包装或 `struct Foo(NonNull<FooCtx>)` |
| 回调函数（函数指针） | 闭包 trait（`Fn`/`FnMut`）或 trait object |
| 线程不安全 | 在类型系统中编码（`!Send`/`!Sync`） |

**示例**：

```rust
// 原 C 接口：int foo_init(FooCtx **ctx, const FooConfig *cfg)
// 设计为 Rust 接口：
pub struct Foo(NonNull<FooCtx>);          // RAII 句柄
pub struct FooConfig { /* 字段 */ }       // 安全配置类型

impl Foo {
    pub fn new(cfg: &FooConfig) -> Result<Self, FooError> { todo!() }
}

impl Drop for Foo {
    fn drop(&mut self) { /* 调用 foo_destroy */ }
}
```

## 第四步：用 FFI 实现 Rust 接口

**目标**：在 Rust 接口实现体内，通过第二步的 FFI 脚手架调用原有 C 实现。

**关键原则**：

1. 将所有 `unsafe` FFI 调用封装在最小范围的 `unsafe` 块内，不向上层接口暴露 unsafe。
2. 在 FFI 调用边界完成类型转换（C 原始类型 ↔ Rust 安全类型）。
3. 将 C 错误码映射为 Rust `Result`/`Error`。

**实现模板**：

```rust
impl Foo {
    pub fn new(cfg: &FooConfig) -> Result<Self, FooError> {
        let c_cfg: ffi::FooConfig = cfg.into();   // 安全类型 → C 类型
        let mut raw_ctx: *mut ffi::FooCtx = std::ptr::null_mut();
        let ret = unsafe { ffi::foo_init(&mut raw_ctx, &c_cfg) };
        if ret != 0 {
            return Err(FooError::from_code(ret));
        }
        // SAFETY: foo_init 成功时 raw_ctx 非空且有效
        Ok(Foo(unsafe { NonNull::new_unchecked(raw_ctx) }))
    }
}

impl Drop for Foo {
    fn drop(&mut self) {
        // SAFETY: self.0 是通过 foo_init 获得的有效指针
        unsafe { ffi::foo_destroy(self.0.as_ptr()) }
    }
}
```

## 第五步：验证与迭代

执行以下验证：

1. **等价性测试**：为 Rust 接口编写单元测试，与原 C 接口的测试用例对比输出。
2. **内存安全检查**：在 `--release` 和 `--debug` 模式下使用 Valgrind 或 AddressSanitizer 检测内存泄漏。
3. **Miri 测试**：在 `cargo miri test` 下运行，确保无未定义行为。
4. **文档注释**：为每个公开 Rust 接口补充 `///` 文档，说明与原 C 接口的对应关系及 Safety 契约。

待 Rust 接口验证通过后，移除第二步中的 FFI 脚手架层，替换为直接的 Rust 实现（若有）或将 FFI 层内化为模块私有。

## 参考资料

- `references/hicc.md`：hicc crate API 参考，包含 `import_lib!`、`import_class!`、`cpp!` 宏详细用法及 `build.rs` 配置示例。
