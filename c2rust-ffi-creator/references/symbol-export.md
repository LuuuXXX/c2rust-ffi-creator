# 符号表导出与验证方法

## 目标

确保 Rust FFI crate 编译产物（`.so` / `.a`）导出的符号与原 C 项目产物完全一致。

---

## 提取符号表的方法

### 从 C 产物提取

```bash
# 动态库
nm -D --defined-only libfoo.so | awk '{print $3}' | sort > c_symbols.txt

# 静态库
nm --defined-only libfoo.a | awk '{print $3}' | grep -v '^$' | sort > c_symbols.txt

# macOS
nm -g libfoo.dylib | awk '{print $3}' | sort > c_symbols.txt
```

### 从 Rust 产物提取

```bash
# 动态库（Linux）
nm -D --defined-only target/release/libc2rust_ffi.so | awk '{print $3}' | sort > rust_symbols.txt

# 静态库
nm --defined-only target/release/libc2rust_ffi.a | awk '{print $3}' | grep -v '^$' | sort > rust_symbols.txt
```

---

## 符号过滤规则

以下前缀的符号为 Rust 内部符号，**不计入比较**：

```
__rust_
_rust_
rust_
std::
core::
alloc::
```

过滤命令：

```bash
grep -v -E '^(__rust_|_rust_|rust_|_ZN(3std|4core|5alloc))' rust_symbols.txt > rust_symbols_filtered.txt
```

---

## 差异对比

```bash
diff c_symbols.txt rust_symbols_filtered.txt
```

**预期输出**：无差异（空输出）。

**若有差异**：

- `< foo_bar`（仅在 C 中）：对应 Rust 函数缺少 `#[no_mangle]`，或函数名拼写有误。
- `> foo_bar`（仅在 Rust 中）：Rust 新增了 C 中不存在的导出符号，需检查是否合理。

---

## symbols_expected.txt 格式

最终验证通过后，将预期符号表写入 `.c2rust/c/symbols_expected.txt`：

```
# 格式：每行一个符号名（不含地址和类型）
# 生成时间：<timestamp>
# C 源产物：<path>

foo_init
foo_destroy
foo_get_version
bar_open
bar_close
bar_read
bar_write
```

CI 中可用此文件进行回归验证：

```bash
diff .c2rust/c/symbols_expected.txt <(nm -D --defined-only target/release/libc2rust_ffi.so | awk '{print $3}' | sort)
```

---

## 常见问题

### 符号被 Rust 混淆（mangled）

原因：未添加 `#[no_mangle]`。

修复：

```rust
#[no_mangle]
pub extern "C" fn foo_init(ctx: *mut FooCtx) -> std::ffi::c_int { ... }
```

### 符号可见性为 local（小写 `t`/`d`）

原因：函数未标记为 `pub`，或 crate-type 配置不正确。

修复：
1. 确认函数为 `pub extern "C"`。
2. 确认 `Cargo.toml` 中 `crate-type = ["cdylib", "staticlib"]`。

### C 使用了弱符号（weak symbol）

```c
__attribute__((weak)) int foo_optional(void) { return -1; }
```

Rust 暂不直接支持弱符号，可用以下方式模拟：

```rust
#[no_mangle]
#[linkage = "weak"]  // 需要 nightly 或 cfg(target_os = "linux")
pub extern "C" fn foo_optional() -> std::ffi::c_int { -1 }
```

若无法模拟，在 `symbols_expected.txt` 中注明并豁免该符号的比较。
