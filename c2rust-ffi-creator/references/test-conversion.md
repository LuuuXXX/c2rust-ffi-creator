# C 测试到 Rust 测试转换规则

## 概述

将 C 测试文件（通常基于 assert、自定义 test runner 或 CUnit）转换为 Rust `#[test]` 函数。

---

## 文件命名映射

| C 测试文件 | Rust 测试文件 |
|-----------|--------------|
| `test_foo.c` | `tests/test_foo.rs` |
| `foo_test.c` | `tests/foo_test.rs` |
| `check_bar.c` | `tests/check_bar.rs` |

---

## 函数转换规则

### 测试函数声明

```c
// C
void test_foo_init_success(void) { ... }
```

```rust
// Rust
// 原 C 测试：test_foo_init_success
#[test]
fn test_foo_init_success() { ... }
```

### 断言转换

| C 断言 | Rust 断言 |
|--------|-----------|
| `assert(expr)` | `assert!(expr)` |
| `assert(a == b)` | `assert_eq!(a, b)` |
| `assert(a != b)` | `assert_ne!(a, b)` |
| `assert(ptr != NULL)` | `assert!(!ptr.is_null())` |
| `assert(ptr == NULL)` | `assert!(ptr.is_null())` |
| `assert(a > b)` | `assert!(a > b)` |
| `CU_ASSERT_EQUAL(a, b)` | `assert_eq!(a, b)` |
| `CU_ASSERT_STRING_EQUAL(a, b)` | `assert_eq!(CStr::from_ptr(a), CStr::from_ptr(b))` |

### 字符串处理

```c
// C
char *s = "hello";
foo_set_name(ctx, s);
```

```rust
// Rust
use std::ffi::CString;
let s = CString::new("hello").unwrap();
unsafe { foo_set_name(ctx, s.as_ptr()) };
```

### 内存分配

```c
// C
foo_t *ctx = malloc(sizeof(foo_t));
foo_init(ctx);
// ... test ...
foo_destroy(ctx);
free(ctx);
```

```rust
// Rust
use std::alloc::{alloc, dealloc, Layout};
use std::mem;

let layout = Layout::new::<FooCtx>();
let ctx = unsafe { alloc(layout) as *mut FooCtx };
assert!(!ctx.is_null());
unsafe { foo_init(ctx) };
// ... test ...
unsafe {
    foo_destroy(ctx);
    dealloc(ctx as *mut u8, layout);
}
```

**简化写法**（推荐，当 C 结构体支持零初始化时）：

```rust
let mut ctx = FooCtx { fd: 0, priv_: std::ptr::null_mut() };
unsafe { foo_init(&mut ctx) };
// ... test ...
unsafe { foo_destroy(&mut ctx) };
```

### 错误码检查

```c
// C
int ret = foo_init(ctx);
assert(ret == 0);
```

```rust
// Rust
let ret = unsafe { foo_init(&mut ctx) };
assert_eq!(ret, 0, "foo_init failed with code {}", ret);
```

### setup/teardown 模式

```c
// C（CUnit 风格）
static foo_t *g_ctx;
void setup(void)   { g_ctx = foo_create(); }
void teardown(void){ foo_destroy(g_ctx); }
```

```rust
// Rust（每个测试独立初始化，避免全局状态）
fn make_ctx() -> *mut FooCtx {
    let ctx = unsafe { foo_create() };
    assert!(!ctx.is_null());
    ctx
}

#[test]
fn test_something() {
    let ctx = make_ctx();
    // ... test ...
    unsafe { foo_destroy(ctx) };
}
```

---

## unsafe 使用规范

- 所有 FFI 调用须包裹在 `unsafe` 块中。
- `unsafe` 块应尽量小，仅包含直接的 FFI 调用。
- 每个 `unsafe` 块前添加注释，说明安全前提，例如：
  ```rust
  // Safety: ctx 由 foo_create() 返回，保证非空且已初始化。
  unsafe { foo_destroy(ctx) };
  ```

---

## 测试文件头部模板

```rust
//! 原 C 测试文件：.c2rust/c/tests/test_foo.c
//! 转换时间：<timestamp>

use std::ffi::{CStr, CString, c_int};
use c2rust_ffi::foo::{FooCtx, foo_init, foo_destroy};

// ... 测试函数 ...
```
