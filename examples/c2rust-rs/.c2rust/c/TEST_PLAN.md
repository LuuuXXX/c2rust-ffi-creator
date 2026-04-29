# 测试方案（Test Plan）

## 测试文件

| 文件 | 说明 |
|------|------|
| `tests/test_calc.c` | 主测试程序，包含所有单元测试 |

## 运行测试

```bash
# 在 .c2rust/c/ 目录下执行
cd .c2rust/c

# 使用 CMake + CTest
cmake -B _build -DCMAKE_BUILD_TYPE=Debug
cmake --build _build
ctest --test-dir _build --output-on-failure

# 或直接运行测试程序
_build/test_calc
```

## 预期输出

```
calc library test suite
========================
  [TEST] version ... PASS
  [TEST] add_basic ... PASS
  [TEST] add_negative ... PASS
  [TEST] add_overflow ... PASS
  [TEST] add_null ... PASS
  [TEST] sub_basic ... PASS
  [TEST] sub_overflow ... PASS
  [TEST] mul_basic ... PASS
  [TEST] mul_overflow ... PASS
  [TEST] div_basic ... PASS
  [TEST] div_by_zero ... PASS
  [TEST] abs_positive ... PASS
  [TEST] abs_negative ... PASS
  [TEST] abs_zero ... PASS
  [TEST] abs_overflow ... PASS
  [TEST] sqrt_basic ... PASS
  [TEST] sqrt_zero ... PASS
  [TEST] sqrt_negative ... PASS
  [TEST] sqrt_null ... PASS
========================
All tests passed!
```

## 测试覆盖范围

| 函数 | 测试用例 | 覆盖情形 |
|------|----------|----------|
| `calc_version` | `test_version` | 返回非 NULL，非空字符串 |
| `calc_add` | `test_add_basic`, `test_add_negative`, `test_add_overflow`, `test_add_null` | 正常值、负数、溢出、NULL |
| `calc_sub` | `test_sub_basic`, `test_sub_overflow` | 正常值、溢出 |
| `calc_mul` | `test_mul_basic`, `test_mul_overflow` | 正常值、溢出 |
| `calc_div` | `test_div_basic`, `test_div_by_zero` | 正常值（截断）、除零 |
| `calc_abs` | `test_abs_positive`, `test_abs_negative`, `test_abs_zero`, `test_abs_overflow` | 正数、负数、零、INT32_MIN |
| `calc_sqrt` | `test_sqrt_basic`, `test_sqrt_zero`, `test_sqrt_negative`, `test_sqrt_null` | 正数、零、负数、NULL |

## Rust 版本测试策略

Rust 版本测试应覆盖完全相同的测试用例，位于 `tests/integration_test.rs`。

每个 C 测试用例对应一个 Rust 测试函数，使用相同的输入和预期输出，确保行为一致。
