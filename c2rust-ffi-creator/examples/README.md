# c2rust-ffi-creator 示例

本目录包含两个端到端示例，展示 c2rust-ffi-creator 工作流的完整输出。
每个示例包含原始 C 项目和经过脚本处理后生成的 `c2rust-rs/` Rust 项目。

---

## 示例列表

### 01-libstrbuf — 单模块，平铺结构

**场景**：一个小型 C 字符串缓冲区库，所有头文件直接放在 `include/` 下。

**C 项目结构**：
```
c_project/
├── include/
│   └── strbuf.h          ← 唯一的头文件（公开 API）
├── src/
│   └── strbuf.c          ← 实现
├── tests/
│   └── test_strbuf.c     ← C 测试
└── Makefile
```

**生成的 Rust FFI 结构**：
```
c2rust-rs/ffi/src/
├── lib.rs                # pub mod strbuf;
└── strbuf.rs             # extern "C" FFI 绑定
```

由于 `include/strbuf.h` 的路径只有一层（剥离 `include/` 前缀后为 `strbuf`），
Rust 侧也是平铺的单模块，`lib.rs` 只有一行 `pub mod strbuf;`。

---

### 02-libsensor — 多模块，三层层级结构

**场景**：一个嵌入式传感器库，头文件按功能分组到多级子目录。

**C 项目结构**：
```
c_project/
├── include/
│   ├── sensor/
│   │   ├── temperature.h   ← 温度传感器 API
│   │   └── pressure.h      ← 气压传感器 API
│   └── platform/
│       └── linux/
│           └── i2c.h       ← Linux I2C 总线抽象
├── src/
│   ├── sensor/
│   │   ├── temperature.c
│   │   └── pressure.c
│   └── platform/
│       └── linux/
│           └── i2c.c
├── tests/
│   ├── test_temperature.c
│   └── test_pressure.c
└── Makefile
```

**生成的 Rust FFI 结构**：
```
c2rust-rs/ffi/src/
├── lib.rs                    # pub mod platform; pub mod sensor;
├── sensor/
│   ├── mod.rs                # pub mod pressure; pub mod temperature;
│   ├── temperature.rs        # FFI 封装：temp_sensor_*
│   └── pressure.rs           # FFI 封装：pressure_sensor_*
└── platform/
    ├── mod.rs                # pub mod linux;
    └── linux/
        ├── mod.rs            # pub mod i2c;
        └── i2c.rs            # FFI 封装：i2c_open/close/read/write
```

Rust 侧模块层级**完整镜像**原 C 头文件目录。`lib.rs` 只声明两个顶层模块；
无论 C 项目有多少头文件，`lib.rs` 的行数只与顶层目录数相关。

---

## 如何复现

进入任意示例目录，按以下顺序执行（从仓库根目录运行）：

```bash
# 以 02-libsensor 为例
EXAMPLE=examples/02-libsensor
SCRIPTS=scripts

# 阶段一：初始化 Rust 项目骨架
python3 $SCRIPTS/init_rust_project.py $EXAMPLE/c2rust-rs

# 阶段二：复制 C 项目，保留目录结构
cp -r $EXAMPLE/c_project/. $EXAMPLE/c2rust-rs/.c2rust/c/

# 阶段三：分析 C 项目，生成 spec.json 和 interfaces.md
python3 $SCRIPTS/analyze_c_project.py $EXAMPLE/c2rust-rs/.c2rust/c

# 阶段四：生成 Rust FFI 骨架（镜像 C 头文件目录层级）
python3 $SCRIPTS/gen_rust_ffi.py \
    $EXAMPLE/c2rust-rs/.c2rust/c/spec.json \
    $EXAMPLE/c2rust-rs/ffi/src
```

阶段五（测试转换）和阶段六（符号验证）需要 Rust 工具链，请参考 `../SKILL.md`。

---

## 关键设计说明

| | 01-libstrbuf（平铺） | 02-libsensor（层级） |
|---|---|---|
| C 头文件层级 | 1 层 | 3 层 |
| Rust `lib.rs` 行数 | 1 个 mod | 2 个 mod |
| 模块文件数 | 1 | 7（含 mod.rs） |
| `StrbufT` 等占位类型 | ✓ 需人工补充 `#[repr(C)]` | ✓ 需人工补充 `#[repr(C)]` |

> 占位类型（如 `StrbufT`、`TempReadingT`）由 `gen_rust_ffi.py` 在遇到未知 C 类型时
> 自动生成 PascalCase 名称。人工审核时需为这些类型添加 `#[repr(C)]` 结构体定义。
