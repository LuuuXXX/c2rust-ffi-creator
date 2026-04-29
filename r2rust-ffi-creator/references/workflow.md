# 完整工作流程指南（Workflow Guide）

本文档是 `r2rust-ffi-creator` SKILL 工作流程的详细说明。

---

## 工作流程总览

```
原 C 项目
    │
    ▼
[第一步] 初始化 c2rust-rs（cargo hicc new 或 cargo new）
    │
    ▼
[第二步] 复制 C 源码到 .c2rust/c/（copy_c_sources.sh）
    │
    ▼
[第三步] 分析 C 项目（analyze_c_project.sh）
    │    生成：PROJECT_SPEC.md / MODULE_DEPS.md / INTERFACES.md / BUILD_PLAN.md / TEST_PLAN.md
    ▼
[第四步] 构建并测试 C 版本（build_c.sh + test_c.sh）
    │    提取：symbols_c.txt
    ▼
[第五步] 生成 Rust FFI 绑定（cargo hicc bind 或 bindgen）
    │
    ▼
[第六步] 实现 Rust FFI 封装层（src/lib.rs / src/ffi.rs / src/error.rs）
    │
    ▼
[第七步] 构建 Rust 版本（build_rust.sh）
    │
    ▼
[第八步] 验证符号一致性（verify_symbols.sh）
    │    对比：symbols_c.txt vs symbols_rust.txt
    ▼
[第九步] 运行 Rust 测试（test_rust.sh）
    │
    ▼
全部通过 ✓
```

---

## 第一步详解：初始化 c2rust-rs

### 使用 hicc

`hicc` 是 crates.io 上的 Rust FFI 脚手架工具，专为 C-to-Rust 迁移设计。

```bash
# 安装 hicc
cargo install hicc

# 创建项目
cargo hicc new c2rust-rs --lib

# 查看可用子命令
cargo hicc --help
```

hicc 会生成包含以下内容的 Rust 项目：
- `Cargo.toml`（预配置 `cdylib` 和 `staticlib` 输出类型）
- `build.rs`（预配置 bindgen 调用框架）
- `src/lib.rs`（FFI 导出模板）
- `src/ffi.rs`（`extern "C"` 声明占位符）
- `.cargo/config.toml`（平台特定链接配置）

### 备用方案（hicc 不可用时）

```bash
cargo new c2rust-rs --lib
```

然后将 `assets/rust-ffi-template/` 中的文件覆盖 `c2rust-rs/` 对应位置。

---

## 第二步详解：C 源码复制规范

**目录结构约定：**

```
c2rust-rs/
└── .c2rust/
    └── c/
        ├── include/          # 公开头文件（若原项目有 include/ 目录）
        ├── src/              # 实现文件（若原项目有 src/ 目录）
        ├── tests/            # 测试代码
        ├── CMakeLists.txt    # 或 Makefile
        ├── MANIFEST.txt      # 复制清单（自动生成）
        ├── PROJECT_SPEC.md   # 项目规格（分析生成）
        ├── MODULE_DEPS.md    # 模块依赖（分析生成）
        ├── INTERFACES.md     # 接口规格（分析生成）
        ├── BUILD_PLAN.md     # 构建方案（分析生成）
        ├── TEST_PLAN.md      # 测试方案（分析生成）
        ├── symbols_c.txt     # C 版本符号表（构建后生成）
        └── _build/           # C 版本构建产物（构建后生成）
```

**重要约束：**
- `.c2rust/c/` 中的 C 文件**只读**——不能修改原始 C 代码
- 如需修改 C 代码行为，在 Rust 层实现适配，不要改 C 源码
- `_build/` 和 `symbols_c.txt` 应加入 `.gitignore`

---

## 第三步详解：接口分析关键点

### 识别公开 API

通常公开 API 的标志：
1. 函数声明在 `include/` 目录的头文件中
2. 函数没有 `static` 关键字
3. 使用了 `__attribute__((visibility("default")))` 或 `EXPORT`/`PUBLIC` 宏
4. 在 `.def` 或 `.map` 文件中明确列出

### INTERFACES.md 必须包含的信息

对每个公开函数，必须记录：

```markdown
### `function_name`

**签名：**
```c
return_type function_name(param1_type param1, param2_type param2);
```

**参数：**
- `param1`：含义，取值范围，NULL 是否合法
- `param2`：含义，取值范围，NULL 是否合法

**返回值：**
- 成功：返回值含义
- 失败：返回值（通常为负数或 NULL），errno 变化

**内存所有权：**
- 调用方 / 被调用方负责释放（明确说明）

**线程安全：**
- 是 / 否 / 需要外部锁保护

**副作用：**
- 无 / 修改全局状态 / 文件 IO / 网络 IO
```

---

## 第五步详解：bindgen 使用

### 在 build.rs 中配置 bindgen

```rust
// build.rs
use std::path::PathBuf;

fn main() {
    let c_dir = ".c2rust/c";
    
    // 告诉 Cargo：如果 C 头文件变化，重新运行 build.rs
    println!("cargo:rerun-if-changed={}/include/", c_dir);
    
    let bindings = bindgen::Builder::default()
        // 主头文件（包含所有公开 API）
        .header(format!("{}/include/mylib.h", c_dir))
        // 仅生成公开函数和类型的绑定
        .allowlist_function("mylib_.*")
        .allowlist_type("MyLib.*")
        .allowlist_var("MYLIB_.*")
        // 生成 #[repr(C)] 结构体
        .derive_default(true)
        .derive_debug(true)
        .generate()
        .expect("无法生成 bindgen 绑定");
    
    let out_path = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("无法写入 bindings.rs");
}
```

### 在 src/ffi.rs 中引用生成的绑定

```rust
// src/ffi.rs
#![allow(non_upper_case_globals)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(dead_code)]

include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
```

---

## 第六步详解：Rust 封装层实现模式

### 模式一：透传（Pass-through）

直接将 C 函数导出为 Rust 函数，无额外逻辑：

```rust
// src/lib.rs
use crate::ffi;

#[no_mangle]
pub extern "C" fn mylib_init() -> i32 {
    unsafe { ffi::mylib_init() }
}
```

### 模式二：安全封装（Safe Wrapper）

在 Rust 中提供安全接口，但同时保留 C ABI：

```rust
// Rust 安全接口（供 Rust 调用者使用）
pub fn init() -> Result<(), i32> {
    let ret = unsafe { ffi::mylib_init() };
    if ret < 0 { Err(ret) } else { Ok(()) }
}

// C ABI 导出（供 C 调用者使用，保持符号一致）
#[no_mangle]
pub extern "C" fn mylib_init() -> i32 {
    match init() {
        Ok(()) => 0,
        Err(code) => code,
    }
}
```

### 模式三：状态管理（State Management）

C 库使用全局状态，Rust 使用 Mutex 保护：

```rust
use std::sync::Mutex;
use once_cell::sync::Lazy;

static STATE: Lazy<Mutex<MyState>> = Lazy::new(|| {
    Mutex::new(MyState::default())
});

#[no_mangle]
pub extern "C" fn mylib_set_value(val: i32) {
    STATE.lock().unwrap().value = val;
}
```

---

## 验证步骤详解

### 符号提取命令参考

```bash
# Linux 动态库
nm -gD --defined-only libfoo.so | grep " T " | awk '{print $3}' | sort

# Linux 静态库
nm -g --defined-only libfoo.a | grep " T " | awk '{print $3}' | sort

# macOS 动态库
nm -gU libfoo.dylib | grep " T " | awk '{print $3}' | sed 's/^_//' | sort

# 使用 objdump（更详细）
objdump -T libfoo.so | grep " DF " | awk '{print $NF}' | sort
```

### CI 集成示例（GitHub Actions）

```yaml
# .github/workflows/symbol-check.yml
name: Symbol Consistency Check
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - name: Build C version
        run: scripts/build_c.sh c2rust-rs/.c2rust/c
      - name: Build Rust version
        run: cd c2rust-rs && cargo build --release
      - name: Verify symbols
        run: cd c2rust-rs && ../r2rust-ffi-creator/scripts/verify_symbols.sh .
```
