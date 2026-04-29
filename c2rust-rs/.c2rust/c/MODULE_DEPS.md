# 模块划分与依赖关系（Module Dependency Map）

## 模块划分

本项目结构简单，仅有一个核心模块：

| 模块 | 文件 | 功能 |
|------|------|------|
| `calc` | `src/calc.c` + `include/calc.h` | 算术运算核心实现 |
| `test_calc` | `tests/test_calc.c` | 测试驱动程序（不打包到库） |

## 源文件依赖

```
test_calc.c
├── #include "calc.h"    → include/calc.h
└── #include <assert.h>  → 系统头文件
└── #include <stdio.h>   → 系统头文件

src/calc.c
├── #include "calc.h"    → include/calc.h
├── #include <stdint.h>  → 系统头文件
└── #include <math.h>    → 系统头文件 (sqrt)
```

## 模块依赖图

```
┌──────────────────────┐
│     调用方（用户）   │
└──────────┬───────────┘
           │  #include "calc.h"
           ▼
┌──────────────────────┐
│   calc 模块（北向）  │
│   include/calc.h     │
│   src/calc.c         │
└──────────┬───────────┘
           │  #include <math.h>
           ▼
┌──────────────────────┐
│    libm（南向）       │
│    sqrt()            │
└──────────────────────┘
```

## 模块职责

### `calc` 模块

**北向接口（对调用方）：**
- 提供 `calc_add`, `calc_sub`, `calc_mul`, `calc_div`, `calc_abs`, `calc_sqrt`
- 通过 `calc_version()` 暴露版本信息
- 通过 `calc_error_t` 枚举定义统一错误码

**南向接口（依赖方）：**
- 依赖 `libm` 的 `sqrt()` 函数
- 依赖 C 标准库的 `stdint.h` 类型定义

**内部不对外暴露：**
- 无内部辅助函数（所有实现均为公开函数的直接实现）
