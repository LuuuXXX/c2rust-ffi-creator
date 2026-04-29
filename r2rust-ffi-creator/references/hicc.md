# hicc crate 参考文档

hicc（v0.2.3）是一个安全、高效的 Rust ↔ C/C++ FFI SDK，提供宏驱动的声明式绑定，显著降低手写 `unsafe` 代码量并提升接口的内存安全性。

## 依赖配置

```toml
# Cargo.toml
[dependencies]
hicc = "0.2"

[build-dependencies]
hicc-build = "0.2"
```

## 核心宏一览

| 宏 | 用途 |
|---|---|
| `hicc::cpp! { ... }` | 在 Rust 文件中内嵌 C/C++ 源代码片段 |
| `hicc::import_lib! { ... }` | 声明需要调用的 C/C++ 函数（含 C 函数） |
| `hicc::import_class! { ... }` | 将 C++ 类映射为 Rust struct / trait |

---

## `hicc::cpp!` ——内嵌 C/C++ 代码

将 C/C++ 代码嵌入 Rust 源文件，由 `hicc-build` 在构建时提取并编译。

```rust
hicc::cpp! {
    #include "my_module.h"    // 引入 C 头文件
    #include <stdio.h>

    // 可定义辅助函数或包装函数
    static void log_wrapper(const char* msg) {
        fprintf(stderr, "[C] %s\n", msg);
    }
}
```

---

## `hicc::import_lib!` ——声明 C/C++ 函数绑定

### 基本结构

```rust
hicc::import_lib! {
    #![link_name = "mylib"]    // 链接库名（对应 libmylib.a 或 libmylib.so）

    // C 函数声明
    #[cpp(func = "int foo(int, const char*)")]
    fn foo(x: i32, s: *const i8) -> i32;

    // 可忽略返回值
    #[cpp(func = "int bar(int)")]
    fn bar(x: i32);

    // 可将返回值包装在 hicc::Exception 中（捕获 C++ 异常，C 代码不需要）
    #[cpp(func = "int baz(int)")]
    fn baz(x: i32) -> hicc::Exception<i32>;
}
```

### 支持的参数类型映射

| C/C++ 类型 | Rust 类型 |
|---|---|
| `int`, `long`, `size_t` 等 | `i32`, `i64`, `usize` 等 |
| `const T*` | `*const T` |
| `T*` | `*mut T` |
| `const T&` | `*const T`（自动解引用） |
| `T&` | `*mut T`（自动解引用） |
| `T**` | `*mut *mut T` |
| `void*` | `*mut std::ffi::c_void` |

### 缺省参数（C++ 特性）

```rust
// C++ 函数: int foo(int v1, int v2 = 0)
hicc::import_lib! {
    #![link_name = "mylib"]

    // Rust 函数可以省略有缺省值的参数
    #[cpp(func = "int foo(int, int)")]
    fn foo(v: i32) -> i32;
}
```

### 引用 C++ 类（与 `import_class!` 配合使用）

```rust
hicc::import_lib! {
    #![link_name = "mylib"]

    class MyClass;      // 声明使用的 C++ 类（需先在 import_class! 中定义）

    #[cpp(func = "MyClass* create_instance()")]
    fn create_instance() -> MyClass;
}
```

---

## `hicc::import_class!` ——映射 C++ 类

### 普通类

```rust
hicc::import_class! {
    #[cpp(class = "MyClass")]
    class MyClass {
        // 映射成员函数
        #[cpp(method = "int get_value() const")]
        fn get_value(&self) -> i32;

        #[cpp(method = "void set_value(int)")]
        fn set_value(&mut self, v: i32);
    }
}
```

### 抽象类（接口）

```rust
hicc::import_class! {
    // #[interface] 使 C++ 抽象类映射为 Rust trait
    #[interface]
    class IFoo {
        #[cpp(method = "void foo() const")]
        fn foo(&self);
    }

    // 继承自接口的具体类
    #[cpp(class = "FooImpl", ctor = "FooImpl()")]
    class FooImpl: IFoo {
        #[cpp(method = "void extra()")]
        fn extra(&self);
    }
}
```

### 用 Rust 实现 C++ 接口（虚函数代理）

```rust
// 在 import_lib! 中用 @make_proxy 创建代理对象
hicc::import_lib! {
    #![link_name = "mylib"]
    class FooImpl;

    #[cpp(func = "FooImpl @make_proxy<FooImpl>()")]
    #[interface(name = "IFoo")]
    fn new_rust_foo(intf: hicc::Interface<FooImpl>) -> FooImpl;
}

// 用 Rust struct 实现 trait（即实现 C++ 虚函数）
struct RustFoo;
impl IFoo for RustFoo {
    fn foo(&self) { println!("Rust impl of foo"); }
}

// 使用
let obj = new_rust_foo(RustFoo);
obj.foo();
```

---

## `build.rs` 配置

```rust
// build.rs
fn main() {
    hicc_build::Build::new()
        .rust_file("src/main.rs")    // 包含 hicc::cpp! 的 Rust 源文件
        .compile("mylib");           // 生成的库名

    println!("cargo::rustc-link-lib=mylib");
    println!("cargo::rustc-link-lib=stdc++");    // 若涉及 C++ 代码
    println!("cargo::rerun-if-changed=src/main.rs");
}
```

**多文件项目**：

```rust
fn main() {
    hicc_build::Build::new()
        .rust_file("src/ffi/bindings.rs")
        .rust_file("src/ffi/classes.rs")
        .compile("mylib");

    println!("cargo::rustc-link-lib=mylib");
    println!("cargo::rustc-link-lib=stdc++");
    println!("cargo::rerun-if-changed=src/ffi/");
}
```

---

## 特殊类型

### `hicc::Exception<T>` ——捕获 C++ 异常

```rust
// 返回 Ok(T) 或 Err(hicc::CppException)
let result: hicc::Exception<i32> = unsafe { foo(1) };
match result.ok() {
    Ok(v) => println!("result = {v}"),
    Err(e) => println!("C++ exception: {e:?}"),
}
```

### `hicc::Interface<T>` ——传递 Rust 实现给 C++ 虚函数代理

传递给 `@make_proxy` 工厂函数，将 Rust struct 包装为 C++ 接口实现。

### `hicc::RustAny<T>` / `hicc::RustKey<T>` / `hicc::RustHashKey<T>`

用于将 Rust 数据存入 STL 容器（需引入 `hicc-std` crate）。

---

## 对齐要求

所有 C++ 对象须按 `size_t` 字节数对齐（64 位系统为 8 字节），未对齐的地址视为非法指针。

---

## 版本特性速查

| 版本 | 新增特性 |
|---|---|
| v0.2.0 | 自动生成 C++ 适配代码，仅需提供 `.rs` 文件 |
| v0.2.1 | `RustAny` 支持 STL 容器存储 Rust 数据 |
| v0.2.2 | 支持在 Rust 内存空间中构造 C++ 类对象（placement new） |
| v0.2.3 | 修正 `hicc-build` 版本号依赖错误 |

---

## 完整 hello_world 示例

```rust
// src/main.rs
hicc::cpp! {
    #include <stdio.h>
    static void hello_world() {
        printf("hello world!\n");
    }
}

hicc::import_lib! {
    #![link_name = "example"]

    #[cpp(func = "void hello_world()")]
    fn hello_world();
}

fn main() {
    hello_world();
}
```

```rust
// build.rs
fn main() {
    hicc_build::Build::new()
        .rust_file("src/main.rs")
        .compile("example");
    println!("cargo::rustc-link-lib=example");
    println!("cargo::rerun-if-changed=src/main.rs");
}
```

