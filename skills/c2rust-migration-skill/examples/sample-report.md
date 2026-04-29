# C→Rust 迁移分析报告：libfoo

> **生成时间**：2024-03-15 10:00 UTC（示例，手工编写）
> **输入文件**：`examples/sample-spec-v1.yml`
> **测试覆盖率输入**：45%（用户提供的估算值）
> **注意**：本报告为示例文件，展示 generate_report.py 的典型输出格式。

## 摘要

| 指标 | 数量 |
|---|---|
| 北向函数 | 4 |
| 类型定义（struct/enum/typedef）| 3 |
| 风险信号（需人工确认） | 5 |
| 建议 Tier 0 接口数 | 1 |
| 建议 Tier 1 接口数 | 2 |
| 建议 Tier 2 接口数 | 1 |

---

## 北向接口清单

| 函数名 | 参数数 | 风险信号 | 建议 Tier | 建议优先级 |
|---|---|---|---|---|
| `foo_version` | 0 | 无 | Tier 1 | #1 |
| `foo_destroy` | 1 | 无 | Tier 1 | #2 |
| `foo_init` | 2 | OUT_BUF, GLOBAL_STATE | Tier 2 | #3 |
| `foo_async_op` | 3 | CALLBACK, OPAQUE | Tier 2 | #4 |

---

## ⚠ 风险信号清单（需人工确认）

> 每个风险信号代表一个潜在的迁移难点，需要在 Phase 1 实施前明确处置策略。

### `foo_init`

**[ TODO-001 ]** `[RISK: OUT_BUF]` 函数包含 out buffer 参数（FooCtx**）

需确认以下问题：
- [x] 谁负责分配 out buffer？  
  → **Rust 侧（foo_init 内部分配，foo_destroy 释放）**
- [x] buffer 最大长度单位？  
  → **单个 FooCtx 对象**
- [x] 失败时是否写入 buffer？  
  → **不写入（*ctx 保持 NULL）**

**处置决策**：接受：使用 Handle 模式，foo_init 负责分配，foo_destroy 负责释放

---

**[ TODO-002 ]** `[RISK: GLOBAL_STATE]` 函数依赖全局 init/deinit 状态

需确认以下问题：
- [x] 是否为单例？  
  → **是，foo_global_init() 只能调用一次**
- [x] init/deinit 的线程安全性？  
  → **非线程安全，需外部同步**
- [x] Rust 侧是否需要 `std::sync::Once`？  
  → **是**

**处置决策**：接受：Rust 侧使用 std::sync::Once 保护全局初始化

---

### `foo_async_op`

**[ TODO-003 ]** `[RISK: CALLBACK]` 函数包含回调函数指针参数

需确认以下问题：
- [x] 回调在哪个线程调用？  
  → **内部线程池的后台线程**
- [x] 是否允许重入？  
  → **否**
- [x] 回调函数指针的生命周期？  
  → **仅在操作完成时调用一次，之后不再持有**
- [x] user_data 如何传递与释放？  
  → **调用方保证 user_data 在 on_done 触发前有效；触发后可释放**

**处置决策**：接受：在 Rust FFI 层使用 Box<dyn FnOnce> + into_raw 桥接

---

**[ TODO-004 ]** `[RISK: OPAQUE]` user_data 为 void* 不透明指针

需确认以下问题：
- [x] void* 指向的实际类型？  
  → **由调用方决定（通常是 Box<T> 的原始指针）**
- [x] 生命周期由谁管理？  
  → **调用方**
- [x] Rust 侧如何映射？  
  → **Phase 1：保持 *mut c_void；Phase 2 考虑泛型**

**处置决策**：接受：Phase 1 保持 void* 语义，Phase 2 考虑泛型化

---

## 差分测试分级建议

> ⚠ **人工确认点 3**：下表的「选定 Tier」栏由负责人填写并签字后，填入 `templates/compatibility-validation-plan.md`。

| 函数名 | 建议 Tier | 建议理由摘要 | 选定 Tier（人工填写） |
|---|---|---|---|
| `foo_version` | **Tier 0** | 纯函数，无副作用，无风险信号 | Tier 0 ✓ |
| `foo_destroy` | **Tier 1** | 测试覆盖率中等（45%）| Tier 1 ✓ |
| `foo_init` | **Tier 2** | 检测到全局状态 + out buffer + 覆盖率不足 | Tier 2 ✓ |
| `foo_async_op` | **Tier 2** | 检测到回调 + void* + 后台线程 | Tier 2 ✓ |

---

## Phase 1 实施顺序建议

> 按风险从低到高排序；建议优先实现低风险接口，建立信心后再攻关高风险接口。

### #1. `foo_version`（Tier 0）

**风险摘要**：无风险信号

- 测试覆盖率尚可（45%）
- 纯函数，无副作用
- **推荐首个实现**，用于验证构建链路、符号导出、类型映射

---

### #2. `foo_destroy`（Tier 1）

**风险摘要**：无风险信号

- 测试覆盖率中等
- 需验证 NULL 传参行为（no-op）
- 实现 Rust `Drop` trait 的 `impl Drop for Foo`

---

### #3. `foo_init`（Tier 2）

**风险摘要**：2 个风险信号（OUT_BUF, GLOBAL_STATE）

- 依赖全局初始化（需先解决 foo_global_init/deinit）
- out 指针参数需要 Handle 模式封装
- 建议与 foo_destroy 配对测试（init → use → destroy 完整生命周期）

---

### #4. `foo_async_op`（Tier 2）

**风险摘要**：2 个风险信号（CALLBACK, OPAQUE）

- 最复杂接口，留至最后
- 需要设计回调桥接层（FFI 回调 → Rust 闭包）
- 建议使用 Tier 2 模糊测试验证回调时序

---

## 类型定义清单

| 类型名 | Kind | 需 `#[repr(C)]` |
|---|---|---|
| `FooCtx` | struct | ✓ |
| `FooError` | enum | — |
| `FooConfig` | struct | ✓ |

---

## 建议的后续步骤

1. **[ ⚠ 人工确认点 1 ]** 审查上方风险信号清单 ✅（示例中已全部确认）
2. 基于确认结果，补全 `spec-v1.yml` 中各函数的行为契约字段 ✅
3. **[ ⚠ 人工确认点 2 ]** 完成 `templates/abi-freeze-checklist.md` 并签字冻结
4. **[ ⚠ 人工确认点 3 ]** 确认差分测试分级表，填入 `templates/compatibility-validation-plan.md`
5. 按 `README.md` Step 5 开始 Rust FFI 层实现（参考 `r2rust-ffi-creator/SKILL.md`）
6. 实现完成后，执行 `templates/phase1-acceptance-criteria.md` 验收检查
