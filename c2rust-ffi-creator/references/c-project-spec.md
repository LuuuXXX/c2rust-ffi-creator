# C 项目规格模板

## 概述

`spec.json` 是 c2rust-ffi-creator 工作流的核心数据文件，由 `scripts/analyze_c_project.py` 自动生成，并可人工补充修正。

---

## spec.json 结构

```json
{
  "project": {
    "name": "string",            // 项目名称
    "version": "string",         // 版本号（从 Makefile 或 configure.ac 提取）
    "build_system": "make|cmake|autoconf",
    "build_command": ["make", "all"],  // 构建命令，JSON 数组（argv 形式）或字符串；
                                        // 数组格式（推荐）：["make", "all"] 或 ["cmake", "--build", "."]
                                        // 字符串格式（兼容）：含 && 的多步命令，如 "cmake -B build && cmake --build build"
    "test_command": ["make", "test"],   // 测试命令，同上：JSON 数组（推荐）或字符串，例如 ["make", "test"]
    "output_artifacts": [        // 构建产物路径列表（相对于 .c2rust/c/，由 verify_symbols.sh 读取）
      "libfoo.a",               // 例如静态库
      "libfoo.so"               // 例如动态库（可省略，脚本会自动扫描回退）
    ]
  },
  "modules": [
    {
      "name": "string",          // 模块逻辑名，对应头文件去掉 .h 后缀
      "header": "string",        // 北向接口头文件路径，例如 "include/foo.h"
      "sources": ["string"],     // 实现文件列表，例如 ["src/foo.c"]
      "north_interfaces": [      // 对外暴露的 API（北向）
        {
          "function": "string",  // 函数名
          "signature": "string", // 完整 C 签名，例如 "int foo_init(foo_t *ctx)"
          "params": [
            {"name": "string", "type": "string", "direction": "in|out|inout"}
          ],
          "return_type": "string",
          "description": "string"
        }
      ],
      "south_deps": [            // 依赖的其他模块或外部库（南向）
        {
          "module": "string",    // 依赖模块名或外部库名
          "type": "internal|external"
        }
      ],
      "data_contracts": [        // 关键数据结构
        {
          "kind": "struct|enum|typedef|macro",
          "name": "string",
          "definition": "string" // 完整 C 定义
        }
      ],
      "test_coverage": ["string"] // 已有 C 测试覆盖的函数列表
    }
  ]
}
```

---

## interfaces.md 结构

`interfaces.md` 是人类可读的接口清单，从 `spec.json` 导出，便于人工审核。

### 模板

```markdown
# 接口清单：<project_name>

生成时间：<timestamp>
来源：.c2rust/c/spec.json

## 模块：<module_name>

- **头文件**：`<header_path>`
- **源文件**：`<source_paths>`

### 北向接口（对外 API）

| 函数 | 签名 | 参数说明 | 返回值 |
|------|------|----------|--------|
| `foo_init` | `int foo_init(foo_t *ctx)` | ctx: 输出，初始化上下文 | 0=成功，<0=错误码 |

### 南向依赖

| 依赖模块/库 | 类型 | 说明 |
|------------|------|------|
| `bar` | internal | 内部工具模块 |
| `libssl` | external | TLS 加密 |

### 数据契约

```c
typedef struct {
    int   fd;
    void *priv;
} foo_t;
```

### C 测试覆盖

- `test_foo_init_success`
- `test_foo_init_null_ptr`
```

---

## 填写指南

1. **北向接口**：严格从 `.h` 文件提取，不得推断。若注释缺失，保留空 `description` 字段。
2. **南向依赖**：检查 `#include` 指令；外部库从链接标志（`-l`）提取。
3. **数据契约**：仅记录跨模块使用的类型，内部私有类型可省略。
4. **测试覆盖**：若 C 测试文件命名不规范，手动核对并填写函数名。
