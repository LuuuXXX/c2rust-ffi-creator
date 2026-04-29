# 常见问题诊断指南（Troubleshooting Guide）

---

## 问题一：`hicc` 命令不存在

**症状：** `cargo: no such subcommand: hicc`

**解决方案：**
```bash
# 重新安装
cargo install hicc

# 若 crates.io 中 hicc 不可用，使用备用方案
cargo new c2rust-rs --lib
# 然后从 assets/rust-ffi-template/ 复制模板文件
```

---

## 问题二：bindgen 构建失败（找不到 libclang）

**症状：** `error: failed to run custom build command for 'c2rust-rs'` + `libclang not found`

**解决方案：**
```bash
# Ubuntu/Debian
sudo apt install libclang-dev clang

# macOS
brew install llvm
export LIBCLANG_PATH=$(brew --prefix llvm)/lib

# CentOS/RHEL
sudo yum install clang-devel

# 设置环境变量
export LIBCLANG_PATH=/usr/lib/llvm-14/lib  # 按实际版本调整
export CLANG_PATH=/usr/bin/clang-14
```

---

## 问题三：`undefined reference` 链接错误

**症状：** `error[E0425]: cannot find function 'xxx' in this scope` 或链接器报 `undefined reference to 'xxx'`

**解决方案：**

1. **检查 Cargo.toml 链接配置：**
```toml
[lib]
crate-type = ["cdylib", "staticlib"]  # 确认包含这两种类型
```

2. **检查 build.rs 链接指令：**
```rust
// 若链接了外部 C 库
println!("cargo:rustc-link-lib=xxx");
println!("cargo:rustc-link-search=native=/path/to/lib");
```

3. **检查 extern "C" 声明是否正确：**
```rust
extern "C" {
    fn missing_function(arg: i32) -> i32;  // 确认函数名和签名
}
```

---

## 问题四：符号验证失败（缺少导出符号）

**症状：** `verify_symbols.sh` 报告 C 版本中有符号但 Rust 版本没有

**解决方案逐步检查：**

1. **确认函数有 `#[no_mangle]`：**
```rust
// 错误：缺少 #[no_mangle]
pub extern "C" fn mylib_init() -> i32 { ... }

// 正确：
#[no_mangle]
pub extern "C" fn mylib_init() -> i32 { ... }
```

2. **确认函数是 `pub`：**
```rust
// 错误：非 pub
extern "C" fn mylib_init() -> i32 { ... }

// 正确：
#[no_mangle]
pub extern "C" fn mylib_init() -> i32 { ... }
```

3. **确认 crate-type 包含 cdylib：**
```toml
# Cargo.toml
[lib]
crate-type = ["cdylib", "staticlib"]
```

4. **检查条件编译是否意外排除了函数：**
```rust
// 检查是否有 #[cfg(...)] 导致函数被排除
#[cfg(feature = "some-feature")]  // 确认 feature 已启用
#[no_mangle]
pub extern "C" fn mylib_init() -> i32 { ... }
```

---

## 问题五：类型不兼容

**症状：** `error[E0308]: mismatched types` 或 `expected c_int, found i32`

**解决方案：**

参考 `references/type_mapping.md` 中的对照表。

常见修复：
```rust
// 使用 std::os::raw 类型而非 Rust 原生类型
use std::os::raw::{c_int, c_char, c_void};

// 不要用 i32，要用 c_int（在大多数平台相同，但语义更准确）
#[no_mangle]
pub extern "C" fn mylib_get_value() -> c_int {
    42 as c_int
}
```

---

## 问题六：测试中出现内存问题（Segfault）

**症状：** Rust 测试运行时崩溃，`SIGSEGV`

**解决方案：**

1. **检查 unsafe 块中的指针使用：**
```rust
// 危险：未检查 NULL
unsafe {
    let val = *ptr;  // 若 ptr 为 NULL，崩溃
}

// 安全：先检查 NULL
unsafe {
    if !ptr.is_null() {
        let val = *ptr;
    }
}
```

2. **检查生命周期问题：**
```rust
// 危险：返回临时 CString 的指针
fn bad_function() -> *const c_char {
    let s = CString::new("hello").unwrap();
    s.as_ptr()  // s 在函数返回后被释放！
}

// 安全：使用 into_raw
fn safe_function() -> *mut c_char {
    let s = CString::new("hello").unwrap();
    s.into_raw()  // 转移所有权
}

// 调用方负责释放
#[no_mangle]
pub extern "C" fn free_string(s: *mut c_char) {
    if !s.is_null() {
        unsafe { drop(CString::from_raw(s)); }
    }
}
```

3. **使用 Valgrind 检测内存错误：**
```bash
valgrind --leak-check=full ./target/debug/c2rust-rs-test
```

---

## 问题七：C 测试构建失败

**症状：** `build_c.sh` 运行失败

**解决方案：**

1. 检查 C 编译器是否安装：`which gcc` 或 `which clang`
2. 检查头文件依赖：`apt install libXXX-dev`
3. 检查 `BUILD_PLAN.md` 中记录的依赖是否满足
4. 尝试手动编译验证错误信息：
```bash
gcc -I.c2rust/c -I.c2rust/c/include .c2rust/c/src/*.c -shared -fPIC -o /tmp/test.so
```

---

## 问题八：符号提取返回空

**症状：** `extract_symbols.sh` 输出为空

**原因排查：**
```bash
# 检查文件是否为有效库
file target/release/libc2rust_rs.so

# 检查是否有任何符号
nm -g target/release/libc2rust_rs.so

# 检查是否编译了正确的 crate-type
cargo metadata --format-version 1 | python3 -c "
import sys, json
meta = json.load(sys.stdin)
for pkg in meta['packages']:
    if pkg['name'] == 'c2rust-rs':
        for t in pkg['targets']:
            print(t['name'], t['kind'])
"
```
