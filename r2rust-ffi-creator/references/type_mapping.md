# C 到 Rust 类型对照表（Type Mapping Reference）

将 C 函数签名转换为 Rust 类型时，参照此对照表。

---

## 基本数值类型

| C 类型 | Rust 类型 | 说明 |
|--------|-----------|------|
| `char` | `std::os::raw::c_char` | 8位字符 |
| `unsigned char` | `std::os::raw::c_uchar` | |
| `short` | `std::os::raw::c_short` | |
| `unsigned short` | `std::os::raw::c_ushort` | |
| `int` | `std::os::raw::c_int` | 通常为 i32 |
| `unsigned int` | `std::os::raw::c_uint` | |
| `long` | `std::os::raw::c_long` | 平台相关 |
| `unsigned long` | `std::os::raw::c_ulong` | |
| `long long` | `std::os::raw::c_longlong` | i64 |
| `unsigned long long` | `std::os::raw::c_ulonglong` | u64 |
| `float` | `std::os::raw::c_float` | f32 |
| `double` | `std::os::raw::c_double` | f64 |
| `size_t` | `libc::size_t` 或 `usize` | |
| `ssize_t` | `libc::ssize_t` 或 `isize` | |
| `int8_t` | `i8` | |
| `int16_t` | `i16` | |
| `int32_t` | `i32` | |
| `int64_t` | `i64` | |
| `uint8_t` | `u8` | |
| `uint16_t` | `u16` | |
| `uint32_t` | `u32` | |
| `uint64_t` | `u64` | |
| `bool` / `_Bool` | `bool` | 注意 C 中 bool 为 1 字节 |
| `void` | `()` | 仅用于返回值 |

---

## 指针类型

| C 类型 | Rust 类型 | 说明 |
|--------|-----------|------|
| `void *` | `*mut std::ffi::c_void` | 不透明指针 |
| `const void *` | `*const std::ffi::c_void` | |
| `char *` | `*mut std::os::raw::c_char` | C 字符串（可变） |
| `const char *` | `*const std::os::raw::c_char` | C 字符串（只读） |
| `int *` | `*mut std::os::raw::c_int` | 输出参数 |
| `T *` | `*mut T` | 任意类型指针 |
| `const T *` | `*const T` | 只读指针 |
| `T **` | `*mut *mut T` | 双重指针 |

---

## 字符串处理

### C `char *` → Rust `&str` / `String`

```rust
use std::ffi::{CStr, CString};

// 从 C 字符串创建 Rust 字符串切片（借用，不拷贝）
unsafe fn c_str_to_rust(s: *const std::os::raw::c_char) -> &'static str {
    CStr::from_ptr(s).to_str().unwrap_or("")
}

// 从 Rust 字符串创建 C 字符串（分配新内存）
fn rust_str_to_c(s: &str) -> CString {
    CString::new(s).expect("字符串包含 null 字节")
}
```

### 字符串参数约定

| 情形 | C 签名 | Rust 处理 |
|------|--------|-----------|
| 只读 C 字符串输入 | `const char *s` | `*const c_char`，用 `CStr::from_ptr` |
| 可变 C 字符串输入 | `char *s` | `*mut c_char` |
| 返回静态字符串 | `const char *` | `*const c_char`，无需释放 |
| 返回动态分配字符串 | `char *`（调用方释放） | 返回 `Box::into_raw(CString::into_raw())` |

---

## 结构体类型

### 基本规则

```rust
// C 结构体
// struct Point { int x; int y; };

// Rust 对应
#[repr(C)]  // 必须！保证内存布局与 C 一致
#[derive(Debug, Default, Clone, Copy)]
pub struct Point {
    pub x: std::os::raw::c_int,
    pub y: std::os::raw::c_int,
}
```

### 带位域的结构体（Bitfield）

bindgen 通常自动处理，但可能需要调整：

```rust
// C: struct Flags { unsigned int a:1; unsigned int b:3; };
// bindgen 生成的绑定可能需要手动验证对齐
```

### 不透明结构体（Opaque Struct）

```c
// C 中只有前向声明
typedef struct MyContext MyContext;
MyContext *mylib_create_context(void);
void mylib_destroy_context(MyContext *ctx);
```

```rust
// Rust 中使用枚举模拟不透明类型
pub enum MyContext {}

// 或使用 bindgen 生成的 opaque 类型
```

---

## 函数指针

| C 类型 | Rust 类型 |
|--------|-----------|
| `void (*callback)(int)` | `Option<unsafe extern "C" fn(c_int)>` |
| `int (*fn)(char *, size_t)` | `Option<unsafe extern "C" fn(*mut c_char, usize) -> c_int>` |

```rust
// C: void register_callback(void (*cb)(int data));
// Rust:
extern "C" {
    fn register_callback(cb: Option<unsafe extern "C" fn(data: c_int)>);
}
```

---

## NULL 与 Option

```rust
// C 中 NULL 指针返回
// int *find_item(int id);  // 返回 NULL 表示未找到

// Rust 中使用 Option
#[no_mangle]
pub extern "C" fn find_item(id: c_int) -> *mut c_int {
    match internal_find(id) {
        Some(val) => Box::into_raw(Box::new(val)),
        None => std::ptr::null_mut(),
    }
}
```

---

## 错误码

```rust
// C 中通常：负数 = 错误，0 = 成功，正数 = 成功（可能带值）
// Rust 内部使用 Result，但 C ABI 导出仍用 int

pub fn internal_init() -> Result<(), i32> {
    // 实现
    Ok(())
}

#[no_mangle]
pub extern "C" fn mylib_init() -> c_int {
    match internal_init() {
        Ok(()) => 0,
        Err(code) => code,
    }
}
```

---

## 常用宏对应

| C 宏/常量 | Rust 对应 |
|-----------|-----------|
| `NULL` | `std::ptr::null()` / `std::ptr::null_mut()` |
| `true` / `false` | `true` / `false` |
| `INT_MAX` | `i32::MAX` |
| `SIZE_MAX` | `usize::MAX` |
| `EINVAL` | `libc::EINVAL` 或自定义错误类型 |
| `errno` | `std::io::Error::last_os_error()` 或 `libc::errno()` |
