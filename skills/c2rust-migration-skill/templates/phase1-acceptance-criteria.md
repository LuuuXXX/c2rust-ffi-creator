# Phase 1 验收标准

> **使用说明**：本清单在 Phase 1 实现完成后（Step 6），由负责人逐项验证并签字。
> 所有条目通过后，Phase 1 正式完成，方可进入 Phase 2。

## 项目信息

| 字段 | 值 |
|---|---|
| 项目名称 | TODO |
| Phase 1 实现版本 / Commit | TODO |
| 验收人 | TODO |
| 验收日期 | TODO |

---

## 1. 功能等价性

### 1.1 现有 C 测试（必须全部通过）

- [ ] 现有 C 测试套件在链接 Rust 实现后全部通过（0 失败，0 跳过）
- [ ] 通过的测试数量：TODO / TODO（实际通过 / 总计）
- [ ] 测试运行日志已保存至：TODO（路径或链接）

### 1.2 差分测试（按选定 Tier 执行）

**选定 Tier**：TODO（Tier 0 / 1 / 2，来自 `compatibility-validation-plan.md`）

**Tier 1（若适用）**：
- [ ] Golden file 对比测试全部通过
- [ ] 所有返回路径（包括错误路径）均有 golden 覆盖
- [ ] 差异报告已审查，所有差异在 `compatibility-validation-plan.md` 中有记录

**Tier 2（若适用）**：
- [ ] 模糊测试已运行 ≥ TODO 小时
- [ ] C 实现与 Rust 实现差异数量：TODO（预期差异 / 意外差异各多少）
- [ ] 所有意外差异已修复或列入已知差异表
- [ ] 模糊测试未发现 Rust 侧崩溃或 panic

---

## 2. 内存安全

- [ ] 在 debug + ASAN 模式下运行全部测试：无内存错误报告
  ```bash
  RUSTFLAGS="-Z sanitizer=address" cargo test --target x86_64-unknown-linux-gnu
  ```
- [ ] 在 release + Valgrind 下运行关键测试：无内存泄漏
  ```bash
  valgrind --leak-check=full --error-exitcode=1 ./test_binary
  ```
- [ ] `cargo miri test` 通过（无未定义行为）（若适用）
- [ ] 无 `unsafe` 代码的 `// SAFETY:` 注释缺失

---

## 3. ABI 合规性

- [ ] 导出符号列表与 ABI 冻结清单完全一致
  ```bash
  nm -D lib<name>.so | grep " T " | sort > actual_symbols.txt
  diff actual_symbols.txt expected_symbols.txt
  ```
- [ ] 所有结构体的 `size_of` / `offset_of` 断言通过（已在测试中验证）
- [ ] 无额外导出符号（无私有实现泄露）
- [ ] 调用约定验证通过（可通过简单的 C 程序调用验证）

---

## 4. Panic 安全

- [ ] 已编写 panic 触发测试用例，验证其被 `catch_unwind` 捕获并转为错误码
- [ ] panic 测试在所有目标平台上通过
- [ ] 无已知的 panic 路径未被覆盖（代码审查确认）

---

## 5. 性能

> 若无性能要求，此节可标记为"不适用（N/A）"并注明原因。

- [ ] 基准测试已运行，关键路径性能与 C 实现对比
  ```bash
  cargo bench
  ```
- [ ] 性能退化在可接受范围内：TODO（填写具体阈值，如 "≤ 5%"）
- [ ] 性能对比报告已保存至：TODO

---

## 6. 文档

- [ ] 所有公开 `extern "C"` 函数均有 `/// # Safety` 注释
- [ ] 每个函数文档说明了与原 C 接口的对应关系
- [ ] `CHANGELOG` 或迁移说明已更新（记录 Phase 1 完成）
- [ ] `spec-v1-extraction.yml` 中所有 `TODO` 已清空或标记为"已确认"

---

## 7. 代码质量

- [ ] `cargo clippy -- -D warnings` 通过（无 clippy 警告）
- [ ] `cargo fmt --check` 通过（代码格式一致）
- [ ] 所有 `unsafe` 块均有注释说明安全前提
- [ ] 无未使用的导入或死代码（`#[allow(dead_code)]` 须有注释说明）

---

## 8. 集成验证

- [ ] 使用原 C 项目的构建系统链接 Rust 产物，编译通过（无链接错误）
- [ ] 端到端集成测试通过（原 C 调用方 → FFI → Rust 实现）
- [ ] 在所有目标平台上完成上述验证（见 ABI 冻结清单中的平台列表）

---

## 未解决问题

> 在此列出验收时发现但决定延迟处理的问题（必须有明确的 Issue 跟踪和负责人）。

| 问题描述 | 严重级别 | Issue 链接 | 负责人 | 计划解决版本 |
|---|---|---|---|---|
| （示例）`foo_parse()` 在极端长度输入时比 C 实现慢 15% | Low | #TODO | TODO | Phase 2 |

---

## 人工确认记录

> ⚠ **人工确认点 4**：以下签字表示 Phase 1 正式完成，允许进入 Phase 2。

| 字段 | 值 |
|---|---|
| 验收人 | TODO |
| 验收日期 | TODO |
| 未解决高优先级问题 | TODO（无则填"无"） |
| Phase 1 状态 | ☐ 未通过 / ☐ 有条件通过（见未解决问题）/ ☐ **完全通过** |

**签字意味着**：Rust 实现已达到 bit-level 兼容替代目标，可以在受控条件下进入 Phase 2 优化阶段。
