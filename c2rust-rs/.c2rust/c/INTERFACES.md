# 模块南北向接口规格（Interface Specifications）

## 术语说明

- **北向（Northbound）接口**：模块向上层（调用方）暴露的接口
- **南向（Southbound）接口**：模块依赖下层（被调用方）的接口

---

## `calc` 模块北向接口（对外暴露）

### `calc_version`

**签名：**
```c
const char *calc_version(void);
```

**功能：** 返回库版本字符串。

**参数：** 无

**返回值：**
- 始终返回非 NULL 的静态字符串（格式 `"major.minor.patch"`）

**内存所有权：** 静态字符串，调用方不得释放

**线程安全：** ✓（返回静态常量，无全局状态）

**副作用：** 无

---

### `calc_add`

**签名：**
```c
int calc_add(int32_t a, int32_t b, int32_t *result);
```

**功能：** 计算两个 32 位整数之和，检测溢出。

**参数：**

| 参数 | 类型 | 可 NULL | 范围 | 含义 |
|------|------|---------|------|------|
| `a` | `int32_t` | N/A | `[INT32_MIN, INT32_MAX]` | 被加数 |
| `b` | `int32_t` | N/A | `[INT32_MIN, INT32_MAX]` | 加数 |
| `result` | `int32_t *` | 否 | N/A | 输出：`a + b` |

**返回值：**

| 值 | 含义 |
|----|------|
| `CALC_OK (0)` | 成功，`*result` 已写入 |
| `CALC_ERR_INVALID (-1)` | `result` 为 NULL |
| `CALC_ERR_OVERFLOW (-2)` | 结果超出 `int32_t` 范围 |

**内存所有权：** `result` 由调用方提供和拥有

**线程安全：** ✓（纯函数，无全局状态）

**副作用：** 无

---

### `calc_sub`

**签名：**
```c
int calc_sub(int32_t a, int32_t b, int32_t *result);
```

**功能：** 计算 `a - b`，检测溢出。

**参数/返回值：** 同 `calc_add`（参见 `calc_add` 规格）

**特殊情形：** `calc_sub(INT32_MIN, 1, &r)` 返回 `CALC_ERR_OVERFLOW`（无法表示 `INT32_MIN - 1`）

---

### `calc_mul`

**签名：**
```c
int calc_mul(int32_t a, int32_t b, int32_t *result);
```

**功能：** 计算 `a * b`，使用 64 位中间值检测溢出。

**参数/返回值：** 同 `calc_add`

**实现细节：** 使用 `int64_t tmp = (int64_t)a * b` 检测溢出，不发生 UB

---

### `calc_div`

**签名：**
```c
int calc_div(int32_t a, int32_t b, int32_t *result);
```

**功能：** 整数除法（向零截断，即 `C` 标准行为）。

**参数：**

| 参数 | 含义 |
|------|------|
| `a` | 被除数 |
| `b` | 除数，**不能为 0** |
| `result` | 输出：`a / b` |

**返回值：**

| 值 | 含义 |
|----|------|
| `CALC_OK (0)` | 成功 |
| `CALC_ERR_INVALID (-1)` | `result` 为 NULL |
| `CALC_ERR_DIV_ZERO (-3)` | `b == 0` |

---

### `calc_abs`

**签名：**
```c
int calc_abs(int32_t a, int32_t *result);
```

**功能：** 计算绝对值 `|a|`。

**特殊情形：** `calc_abs(INT32_MIN, &r)` 返回 `CALC_ERR_OVERFLOW`（`-INT32_MIN` 无法用 `int32_t` 表示）

---

### `calc_sqrt`

**签名：**
```c
int calc_sqrt(double x, double *result);
```

**功能：** 计算浮点数平方根。

**参数：**

| 参数 | 类型 | 可 NULL | 约束 |
|------|------|---------|------|
| `x` | `double` | N/A | `x >= 0.0` |
| `result` | `double *` | 否 | N/A |

**返回值：**

| 值 | 含义 |
|----|------|
| `CALC_OK (0)` | 成功 |
| `CALC_ERR_INVALID (-1)` | `result` 为 NULL 或 `x < 0.0` |

**南向依赖：** 调用 `libm` 的 `sqrt()`

---

## `calc` 模块南向接口（依赖下层）

### `sqrt`（来自 `libm`）

**使用场景：** 仅在 `calc_sqrt` 中调用

**约束：**
- 在调用前已验证 `x >= 0.0`（不会触发 `sqrt` 的 domain error）
- 链接时需要 `-lm`

---

## 错误码汇总

| 错误码 | 值 | 含义 | 触发函数 |
|--------|-----|------|----------|
| `CALC_OK` | 0 | 成功 | 所有函数 |
| `CALC_ERR_INVALID` | -1 | NULL 指针或无效参数 | 所有函数 |
| `CALC_ERR_OVERFLOW` | -2 | 整数溢出 | `calc_add`, `calc_sub`, `calc_mul`, `calc_abs` |
| `CALC_ERR_DIV_ZERO` | -3 | 除以零 | `calc_div` |
