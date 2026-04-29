# 接口清单：c2rust-rs

生成时间：2026-04-29T07:39:17Z
来源：.c2rust/c/spec.json

## 模块：strbuf

- **头文件**：`include/strbuf.h`
- **源文件**：`src/strbuf.c`

### 北向接口（对外 API）

| 函数 | 签名 | 返回值 |
|------|------|--------|
| `strbuf_init` | `int strbuf_init(strbuf_t *buf, size_t initial_cap)` | `int` |
| `strbuf_append` | `int strbuf_append(strbuf_t *buf, const char *str)` | `int` |
| `strbuf_append_len` | `int strbuf_append_len(strbuf_t *buf, const char *data, size_t len)` | `int` |
| `strbuf_reset` | `void strbuf_reset(strbuf_t *buf)` | `void` |
| `strbuf_free` | `void strbuf_free(strbuf_t *buf)` | `void` |

### 南向依赖

（无依赖）

### 数据契约

```c
typedef struct {
    char   *data;   /**< null-terminated character data */
    size_t  len;    /**< current length (bytes, excluding NUL) */
    size_t  cap;    /**< allocated capacity (bytes) */
} strbuf_t;
```

### C 测试覆盖

- `test_strbuf_init_success`
- `test_strbuf_append`
- `test_strbuf_append_grows`
- `test_strbuf_reset`
