---
name: c2rust-migration-skill
description: >
  使用此技能指导 C→Rust 两阶段迁移。
  使用 "c2rust-migration-skill translate" 触发第一阶段（位级兼容 Rust 替代：扫描头文件、生成 Spec v1 与迁移分析报告、识别风险信号、指导 ABI 冻结与 FFI 实现）；
  使用 "c2rust-migration-skill refactor" 触发第二阶段（可控优化：生成 Phase 2 变更提案模板、指导逐项变更审查与冻结、完成 Rust 惯用化重构）。
---

# c2rust-migration-skill

## 概述

本技能定义了一条以"规格驱动、测试保障、用户确认"为核心的两阶段 C→Rust 迁移路径：

- **第一阶段（Phase 1）** — `translate`：产出与原 C 实现位级兼容的 Rust 替代。C 侧测试全程保留并用于验证。
- **第二阶段（Phase 2）** — `refactor`：在 Phase 1 完全通过后，有序引入接口优化或破坏性变更（每项变更须经用户确认）。

## 触发命令

安装后（将本目录整体复制到 Agent 配置的 `skills/` 目录下），支持以下两个命令触发对应阶段：

| 命令 | 阶段 | 说明 |
|---|---|---|
| `c2rust-migration-skill translate` | Phase 1 | 扫描 C 头文件、生成 Spec v1 与迁移分析报告，指导位级兼容 Rust 替代 |
| `c2rust-migration-skill refactor` | Phase 2 | 生成 Phase 2 变更提案模板，指导可控优化与 Rust 惯用化重构 |

> 两个命令属于同一技能包，手动安装时只需复制一次目录即可获得两个触发。

## 安装

将 `c2rust-migration-skill/` 整个目录复制到 Agent 配置的 `skills/` 目录下：

```bash
cp -r c2rust-migration-skill /path/to/agent/config/skills/
```

## 目录结构

```
c2rust-migration-skill/
├── README.md                        ← 本文件（入口与工作流说明）
├── templates/
│   ├── spec-v1-extraction.yml       ← Spec v1（as-is）提取模板
│   ├── compatibility-validation-plan.md ← 兼容性验证计划（含差分测试分级）
│   ├── abi-freeze-checklist.md      ← ABI 冻结检查清单
│   ├── phase1-acceptance-criteria.md    ← Phase 1 验收标准
│   └── phase2-change-proposal.md       ← Phase 2 变更提案 & 确认清单
├── scripts/
│   ├── translate.sh                 ← Phase 1 入口脚本（扫描 + 报告生成）
│   ├── refactor.sh                  ← Phase 2 入口脚本（变更提案准备）
│   ├── scan_headers.py              ← C 头文件扫描器（libclang / 正则回退）
│   ├── generate_report.py           ← 报告生成器（含差分测试分级建议）
│   └── smoke_test.sh                ← 脚本冒烟测试
└── examples/
    ├── sample-spec-v1.yml           ← 示例 Spec v1 提取结果
    └── sample-report.md             ← 示例生成报告
```

## 快速开始

### 前置条件

- Python 3.8+
- （可选）`libclang` Python 绑定：`pip install libclang`，可获得更精准的解析
- 现有 C 项目（含头文件 `.h`）

### `translate` — Phase 1：扫描与报告

```bash
# 方式一：直接运行 Phase 1 脚本
bash scripts/translate.sh HEADERS=/path/to/c/headers

# 方式二：使用 Makefile
make translate HEADERS=/path/to/c/headers

# 方式三：分步手动运行
python scripts/scan_headers.py /path/to/c/headers --output spec-v1.yml
python scripts/generate_report.py spec-v1.yml --output report.md
```

`translate` 完成后生成：
- `spec-v1.yml`：北向接口提取结果（函数 / 结构体 / 类型定义）
- `report.md`：迁移分析报告（风险信号 + 差分测试分级建议 + 优先级排序）

### `refactor` — Phase 2：变更提案与可控优化

> 前提：Phase 1 所有验收标准（`templates/phase1-acceptance-criteria.md`）已全部通过。

```bash
# 方式一：直接运行 Phase 2 脚本
bash scripts/refactor.sh

# 方式二：使用 Makefile
make refactor
```

`refactor` 完成后生成：
- `phase2-change-proposal.md`：Phase 2 变更提案模板（请按 CHG-xxx 逐项填写）

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1：位级兼容 Rust 替代                    │
│                                                                 │
│  Step 1: 头文件扫描 → Spec v1（as-is）                           │
│       ↓                                                         │
│  Step 2: 风险信号识别 → 手动确认列表           ← ⚠ 人工确认点 1   │
│       ↓                                                         │
│  Step 3: ABI / FFI 设计 & 冻结               ← ⚠ 人工确认点 2   │
│       ↓                                                         │
│  Step 4: 差分测试分级决策（Tier 0/1/2）        ← ⚠ 人工确认点 3   │
│       ↓                                                         │
│  Step 5: Rust FFI 层实现（薄层，复用 C 测试）                     │
│       ↓                                                         │
│  Step 6: Phase 1 验收（测试全绿、无 UB、无泄漏）  ← ⚠ 人工确认点 4 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2：可控优化                              │
│                                                                 │
│  Step 7: 提出变更提案（每项 CHG-xxx）         ← ⚠ 人工确认点 5   │
│       ↓                                                         │
│  Step 8: 变更冻结 & Spec v2 输出                                 │
│       ↓                                                         │
│  Step 9: v2 实现、测试更新、文档更新                               │
│       ↓                                                         │
│  Step 10: Phase 2 发布 & 迁移指南发布                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 详细步骤

### Step 1：头文件扫描 → Spec v1（as-is）

**目标**：机器辅助提取北向接口信息，人工补全行为契约。

1. 运行 `scripts/scan_headers.py`，获得函数签名、结构体布局、类型定义的初始提取结果。
2. 参照 `templates/spec-v1-extraction.yml`，为每个接口补全以下字段：
   - 参数：是否可为 NULL、长度单位、所有权归属
   - 返回值：错误码全集与语义
   - 线程安全 / 重入性
   - 回调：调用时机、线程、生命周期
   - 全局状态依赖：初始化要求、配置项
3. 将已填写的 `spec-v1.yml` 保存到项目根目录（如 `docs/spec-v1.yml`）。

**输出物**：`spec-v1.yml`

---

### Step 2：风险信号识别 → ⚠ 人工确认点 1

`generate_report.py` 会自动标注以下风险信号，需人工逐项确认处置策略：

| 风险信号 | 默认标注 | 需确认的问题 |
|---|---|---|
| 回调函数指针 | `[RISK: CALLBACK]` | 调用线程？生命周期？重入？ |
| out buffer 参数 | `[RISK: OUT_BUF]` | 谁分配？最大长度？失败时是否写入？ |
| 全局 init/deinit | `[RISK: GLOBAL_STATE]` | 是否单例？多次调用行为？ |
| `void*` 不透明指针 | `[RISK: OPAQUE]` | 内部类型？生命周期？ |
| 可变长度参数（`...`） | `[RISK: VARARGS]` | 是否需要 Rust 侧镜像？ |
| 平台相关类型（`long`, `size_t`）| `[RISK: PLATFORM_TYPE]` | 64/32 位兼容策略？ |

**确认动作**：
- 在报告的 `TODO` 列表中，为每个风险信号填写决策（接受 / 需额外封装 / 延迟到 Phase 2）。
- **完成后签字确认**，作为 Phase 1 实现的输入约束。

---

### Step 3：ABI / FFI 设计 & 冻结 → ⚠ 人工确认点 2

参照 `templates/abi-freeze-checklist.md` 完成以下决策并冻结：

- [ ] 确定库产物形式（`staticlib` / `cdylib`）及命名
- [ ] 对每个 `#[repr(C)]` 结构体，验证字段偏移与 C 侧一致
- [ ] 确认调用约定（默认 C calling convention）
- [ ] 确认错误码策略（`i32` 返回码 + TLS `last_error`）
- [ ] 确认内存归属策略（handle 模式 / 调用者分配）
- [ ] 确认 `panic` 处理策略（FFI 边界 `catch_unwind`）

**确认动作**：在清单上逐项打勾并签字，之后 ABI 定义进入冻结状态，Phase 1 期间不允许修改。

---

### Step 4：差分测试分级决策 → ⚠ 人工确认点 3

根据 `generate_report.py` 输出的分级建议，人工确认采用哪个 Tier：

| Tier | 描述 | 适用场景 |
|---|---|---|
| **Tier 0** | 不额外增加差分测试；完全复用现有 C 测试 | 接口简单、无回调、输出确定性强 |
| **Tier 1** | 增加输入/输出 golden file 对比测试 | 有复杂输出结构或多返回路径 |
| **Tier 2** | 增加模糊测试 + 差分对比（C 实现 vs Rust 实现并行运行） | 高风险：回调密集、全局状态复杂、历史 bug 多 |

**确认动作**：
- 在 `templates/compatibility-validation-plan.md` 中记录选定的 Tier 及理由。
- **完成后签字确认**。

---

### Step 5：Rust FFI 层实现

基于冻结的 ABI 设计，实现薄 FFI 层：

- 使用 `hicc::import_lib!` 或 `bindgen` 生成 C ABI 绑定（参见 `r2rust-ffi-creator` 技能）。
- 对每个北向接口，在 Rust 侧实现对应的 `extern "C"` 导出函数，内部调用 C 实现。
- 确保 `panic` 不跨越 FFI 边界（`std::panic::catch_unwind`）。
- 现有 C 测试通过链接 Rust 静态库运行，验证行为等价。

> 参见 `r2rust-ffi-creator/SKILL.md` 了解 hicc crate 的具体用法。

---

### Step 6：Phase 1 验收 → ⚠ 人工确认点 4

参照 `templates/phase1-acceptance-criteria.md`，逐项验证并人工确认：

- [ ] 所有现有 C 测试（或复用的测试向量）通过
- [ ] Tier 1/2 差分测试（若适用）通过
- [ ] Valgrind / AddressSanitizer 无内存错误
- [ ] `cargo miri test` 无未定义行为（若适用）
- [ ] ABI 与冻结清单一致（符号检查 / `nm` 验证）
- [ ] `panic` 不跨越 FFI 边界（测试 edge case 触发 panic）
- [ ] 性能：关键路径无不可接受退化（基准测试对比）
- [ ] 文档：每个公开 FFI 函数有 `/// # Safety` 注释

**Phase 1 完成标志**：以上全部打勾，由负责人签字。之后方可进入 Phase 2。

---

### Step 7：Phase 2 变更提案 → ⚠ 人工确认点 5

参照 `templates/phase2-change-proposal.md`，为每个计划变更创建提案（CHG-xxx）：

- 每项提案包含：变更动机、旧行为、新行为、破坏等级、迁移方式、验收测试。
- 所有提案汇总后，由用户/产品负责人逐项审查并决策（接受 / 拒绝 / 延后）。
- **完成后签字冻结**，作为 Phase 2 实现的唯一依据。

---

## 人工确认点汇总

| 编号 | 时机 | 确认内容 | 对应模板 |
|---|---|---|---|
| ⚠ 1 | Step 2 完成后 | 风险信号处置策略 | `generate_report.py` 输出 |
| ⚠ 2 | Step 3 完成后 | ABI / FFI 冻结 | `abi-freeze-checklist.md` |
| ⚠ 3 | Step 4 完成后 | 差分测试分级 | `compatibility-validation-plan.md` |
| ⚠ 4 | Step 6 完成后 | Phase 1 验收 | `phase1-acceptance-criteria.md` |
| ⚠ 5 | Step 7 完成后 | Phase 2 变更逐项确认 | `phase2-change-proposal.md` |

---

## 参考资料

- `r2rust-ffi-creator/SKILL.md`：hicc crate 驱动的 Rust FFI 适配层搭建指南
- `r2rust-ffi-creator/references/hicc.md`：hicc crate API 参考
- `templates/`：所有可用模板
- `scripts/`：自动化脚本
- `examples/`：示例输出
