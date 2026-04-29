# hicc Crate 使用指南

crates.io：https://crates.io/crates/hicc  
最新版本：0.2.3  
用途：Safe, efficient, full-featured FFI between Rust and C++

---

## 配置

### 工作空间 Cargo.toml

```toml
[workspace]
members = ["ffi"]

[workspace.dependencies]
hicc = "0.2"
```

### ffi/Cargo.toml

```toml
[package]
name = "ffi"
version = "0.1.0"
edition = "2021"

[lib]
name = "c2rust_ffi"         # 对应产物：libc2rust_ffi.so / libc2rust_ffi.a
crate-type = ["cdylib", "staticlib"]

[dependencies]
hicc = { workspace = true }

[build-dependencies]
hicc-build = "0.2"          # 用于在 build.rs 中编译 C/C++ 代码
```

### ffi/build.rs（可选，当需要将 C 代码编译进 Rust 产物时）

```rust
fn main() {
    hicc_build::Build::new()
        .file("../.c2rust/c/src/foo.c")
        .include("../.c2rust/c/include")
        .compile("c2rust_c_core");
}
```

---

## 核心用法模式

### 模式 A：Rust 调用 C 函数（最常见）

适用于保留 C 实现、用 Rust 封装对外接口的场景。

```rust
// ffi/src/foo.rs
use std::ffi::c_int;

// 声明 C 函数（须与 C 头文件签名完全匹配）
extern "C" {
    fn foo_init(ctx: *mut FooCtx) -> c_int;
    fn foo_destroy(ctx: *mut FooCtx);
}

/// # Safety
/// ctx 必须是有效的、未经初始化的 FooCtx 指针。
#[no_mangle]
pub unsafe extern "C" fn c2rust_foo_init(ctx: *mut FooCtx) -> c_int {
    foo_init(ctx)
}
```

### 模式 B：使用 hicc::bridge 宏（适用于 C++ 互操作）

```rust
use hicc::bridge;

#[bridge]
mod ffi {
    extern "C" {
        fn cpp_widget_new() -> *mut CppWidget;
        fn cpp_widget_destroy(w: *mut CppWidget);
    }
}
```

### 模式 C：结构体映射

```rust
/// 必须与 C 中的 foo_t 内存布局完全一致
#[repr(C)]
pub struct FooCtx {
    pub fd:   std::ffi::c_int,
    pub priv_: *mut std::ffi::c_void,
}
```

---

## #[repr(C)] 映射规则

| C 类型 | Rust 类型 |
|--------|-----------|
| `int` | `std::ffi::c_int` |
| `unsigned int` | `std::ffi::c_uint` |
| `long` | `std::ffi::c_long` |
| `size_t` | `libc::size_t` 或 `usize` |
| `char *` | `*const std::ffi::c_char` |
| `void *` | `*mut std::ffi::c_void` |
| `uint8_t` | `u8` |
| `int32_t` | `i32` |
| `struct foo_t *` | `*mut FooCtx` |
| `enum foo_e` | `#[repr(C)] pub enum FooEnum` |

---

## 导出符号命名规范

- 原 C 函数 `foo_init` → Rust 导出函数 `foo_init`（保持名称一致，使用 `#[no_mangle]`）
- 若需要命名空间隔离，可添加前缀：`c2rust_foo_init`，并在 `symbols_expected.txt` 中注明映射关系。

---

## 常见问题

### Q：编译时出现 "undefined reference to `foo_init`"
A：确认 `build.rs` 已将对应 `.c` 文件编译为静态库，或在 `Cargo.toml` 中通过 `links` 字段链接外部库。

### Q：`#[repr(C)]` 结构体大小与 C 不一致
A：检查对齐（`#[repr(C, packed)]`）和填充。使用 `std::mem::size_of::<FooCtx>()` 与 C 侧 `sizeof(foo_t)` 对比。

### Q：hicc-build 找不到头文件
A：在 `hicc_build::Build::new()` 调用中添加 `.include("path/to/include")`。
