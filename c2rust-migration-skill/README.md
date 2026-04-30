---
name: c2rust-migration-skill
description: >
  使用此技能指导 C→Rust 两阶段迁移。
  使用 "c2rust-migration-skill translate" 触发第一阶段（位级兼容 Rust 替代：完整分析 C 项目构建/符号/测试/实现依赖、扫描头文件、生成 Spec v1 与迁移分析报告、识别风险信号、指导 ABI 冻结与 FFI 实现）；
  使用 "c2rust-migration-skill refactor" 触发第二阶段（可控优化：生成 Phase 2 变更提案模板、指导逐项变更审查与冻结、完成 Rust 惯用化重构）。
---

# c2rust-migration-skill

## 概述

本技能定义了一条以"规格驱动、测试保障、用户确认"为核心的两阶段 C→Rust 迁移路径：

- **第一阶段（Phase 1）** — `translate`：产出与原 C 实现位级兼容的 Rust 替代。C 侧测试全程保留并用于验证。
- **第二阶段（Phase 2）** — `refactor`：在 Phase 1 完全通过后，有序引入接口优化或破坏性变更（每项变更须经用户确认）。

> **核心原则**：转换过程必须参考 C 的完整实现，而非只针对接口签名。每个确认点均为阻断门——未签字完成之前，不得推进至下一步。

## 触发命令

安装后（将本目录整体复制到 Agent 配置的 `skills/` 目录下），支持以下两个命令触发对应阶段：

| 命令 | 阶段 | 说明 |
|---|---|---|
| `c2rust-migration-skill translate` | Phase 1 | 完整分析 C 项目（Step 0）→ 扫描头文件 → 生成 Spec v1 与迁移分析报告，指导位级兼容 Rust 替代 |
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
│   ├── c-project-analysis.md        ← C 项目完整分析模板（Step 0，新增）
│   ├── spec-v1-extraction.yml       ← Spec v1（as-is）提取模板
│   ├── compatibility-validation-plan.md ← 兼容性验证计划（含差分测试分级）
│   ├── abi-freeze-checklist.md      ← ABI 冻结检查清单
│   ├── phase1-acceptance-criteria.md    ← Phase 1 验收标准
│   └── phase2-change-proposal.md       ← Phase 2 变更提案 & 确认清单
├── scripts/
│   ├── translate.sh                 ← Phase 1 入口脚本（Step 0 分析 + 扫描 + 报告生成）
│   ├── refactor.sh                  ← Phase 2 入口脚本（变更提案准备）
│   ├── analyze_c_project.py         ← C 项目完整分析器（Step 0，新增）
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
- 现有 C 项目（含源文件 `.c` 与头文件 `.h`）
- 可访问构建工具（make / cmake 等）及已构建产物（用于符号提取）

### `translate` — Phase 1：完整分析与转换准备

```bash
# 方式一：直接运行 Phase 1 脚本（两步走）

# 第一步：Step 0 分析（会在确认点 0 暂停，等待人工审查签字）
bash scripts/translate.sh PROJECT=/path/to/c/project HEADERS=/path/to/c/headers

# 审查并补全 c-project-analysis.md，在文末签字后，继续第二步：
bash scripts/translate.sh PROJECT=/path/to/c/project HEADERS=/path/to/c/headers SKIP_STEP0=1

# 若已有构建好的二进制，可同时提取符号：
bash scripts/translate.sh PROJECT=/path/to/c/project HEADERS=/path/to/headers \
    BINARY=/path/to/libfoo.so

# 方式二：使用 Makefile
make translate PROJECT=/path/to/c/project HEADERS=/path/to/c/headers

# 方式三：分步手动运行
python scripts/analyze_c_project.py /path/to/c/project \
    --headers /path/to/c/headers --binary /path/to/libfoo.so \
    --output c-project-analysis.md
# → 人工审查 c-project-analysis.md 并签字（确认点 0）
python scripts/scan_headers.py /path/to/c/headers --output spec-v1.yml
python scripts/generate_report.py spec-v1.yml --output report.md
```

`translate` 完成后生成：
- `c-project-analysis.md`：C 项目完整分析（构建/符号/测试/实现依赖），须经人工签字确认
- `spec-v1.yml`：北向接口提取结果（函数 / 结构体 / 类型定义，含实现依赖节）
- `report.md`：迁移分析报告（风险信号 + 差分测试分级建议 + 优先级排序）

### `refactor` — Phase 2：变更提案与可控优化

> 前提：Phase 1 所有验收标准（`templates/phase1-acceptance-criteria.md`）已全部通过并签字。

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
│  Step 0: C 项目完整分析                                          │
│          （构建系统 / 实际导出符号 / 测试覆盖 / 实现依赖）          │
│       ↓                                      ← ⚠ 确认点 0【阻断门】│
│  Step 1: 头文件扫描 → Spec v1（as-is，含实现分析节）              │
│       ↓                                                         │
│  Step 2: 风险信号识别 → 手动确认列表           ← ⚠ 确认点 1【阻断门】│
│       ↓                                                         │
│  Step 3: ABI / FFI 设计 & 冻结               ← ⚠ 确认点 2【阻断门】│
│       ↓                                                         │
│  Step 4: 差分测试分级决策（Tier 0/1/2）        ← ⚠ 确认点 3【阻断门】│
│       ↓                                                         │
│  Step 5: Rust FFI 层实现（薄层，复用 C 测试）                     │
│       ↓                                                         │
│  Step 6: Phase 1 验收（测试全绿、无 UB、无泄漏）← ⚠ 确认点 4【阻断门】│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2：可控优化                              │
│                                                                 │
│  Step 7: 提出变更提案（每项 CHG-xxx）         ← ⚠ 确认点 5【阻断门】│
│       ↓                                                         │
│  Step 8: 变更冻结 & Spec v2 输出                                 │
│       ↓                                                         │
│  Step 9: v2 实现、测试更新、文档更新                               │
│       ↓                                                         │
│  Step 10: Phase 2 发布 & 迁移指南发布                             │
└─────────────────────────────────────────────────────────────────┘
```

> **阻断门说明**：每个「⚠ 确认点」均为硬性阻断门。
> 对应确认清单未完整打勾并经负责人签字之前，**不得推进至下一步**。
> 这不是建议性检查，而是强制性流程控制。

---

## 详细步骤

### Step 0：C 项目完整分析 → ⚠ 人工确认点 0【阻断门】

**目标**：在动手编写任何 Rust 代码之前，全面了解 C 项目的构建方式、实际导出符号、现有测试覆盖，以及每个北向函数的完整实现依赖（内部调用链、全局状态、数据类型）。

> **为什么必须做 Step 0？**
> - 仅凭头文件无法得知二进制实际导出哪些符号——符号集合需从已构建产物中提取。
> - 仅凭接口签名无法做出可靠的测试计划——需先了解哪些接口有测试覆盖、覆盖哪些路径。
> - 翻译不能只翻接口声明——必须理解实现内部的调用链、全局状态依赖、数据类型布局，才能确保行为等价。

**操作步骤**：

1. 运行 `scripts/analyze_c_project.py`，生成初始分析骨架：
   ```bash
   python scripts/analyze_c_project.py /path/to/c/project \
       --headers /path/to/include \
       # 若已构建，可提供已构建产物路径
       --binary /path/to/libfoo.so \
       --output c-project-analysis.md
   ```
2. 打开生成的 `c-project-analysis.md`，逐节补全所有 `TODO` 项：
   - **第 1 节**：确认构建命令、产物路径、目标平台
   - **第 2 节**：核查源文件/测试文件清单
   - **第 3 节**：确认北向接口范围（标注北向/内部）
   - **第 4 节**：**必须实际构建并运行 `nm`/`objdump`**，填入导出符号，核对与头文件声明的差异
   - **第 5 节**：**必须实际运行测试**，记录每个北向接口的覆盖情况
   - **第 6 节**：逐函数梳理实现逻辑、内部调用依赖、全局变量、数据类型
   - **第 7 节**：填写风险汇总
3. 在 `c-project-analysis.md` 文末的「⚠ 人工确认点 0」中完成所有勾选并签字。
4. 将签字完成的文件保存至项目文档目录（如 `docs/c-project-analysis.md`）。

**确认要求（必须全部完成，不得绕过）**：
- [ ] 构建命令已在干净环境中验证，产物可正常生成
- [ ] 已用 `nm`/`objdump` 从实际二进制提取导出符号，与头文件声明核对完毕
- [ ] 已运行现有 C 测试，每个北向接口的测试覆盖情况已逐一记录
- [ ] 每个北向函数的实现文件、内部调用链、数据类型依赖已梳理完毕
- [ ] 所有 `TODO` 项已填写（或标注"不适用"并说明原因）
- [ ] 负责人已签字

**输出物**：`c-project-analysis.md`（已签字）

> ⚠ **阻断门**：上述所有项未完成签字之前，**不得推进至 Step 1**。

---

### Step 1：头文件扫描 → Spec v1（as-is，含实现分析节）

**目标**：机器辅助提取北向接口信息，结合 Step 0 的实现分析，人工补全完整行为契约。

1. 运行 `scripts/scan_headers.py`，获得函数签名、结构体布局、类型定义的初始提取结果。
2. 参照 `templates/spec-v1-extraction.yml`，为每个接口补全以下字段：
   - 参数：是否可为 NULL、长度单位、所有权归属
   - 返回值：错误码全集与语义
   - 线程安全 / 重入性
   - 回调：调用时机、线程、生命周期
   - 全局状态依赖：初始化要求、配置项
   - **`implementation_analysis` 节**（来自 Step 0 的分析）：实现文件、内部调用依赖、全局变量、实现逻辑摘要、条件编译分支
3. 将已填写的 `spec-v1.yml` 保存到项目根目录（如 `docs/spec-v1.yml`）。

**输出物**：`spec-v1.yml`（含 `implementation_analysis` 节，所有 TODO 已清空）

---

### Step 2：风险信号识别 → ⚠ 人工确认点 1【阻断门】

`generate_report.py` 会自动标注以下风险信号，需人工逐项确认处置策略：

| 风险信号 | 默认标注 | 需确认的问题 |
|---|---|---|
| 回调函数指针 | `[RISK: CALLBACK]` | 调用线程？生命周期？重入？ |
| out buffer 参数 | `[RISK: OUT_BUF]` | 谁分配？最大长度？失败时是否写入？ |
| 全局 init/deinit | `[RISK: GLOBAL_STATE]` | 是否单例？多次调用行为？ |
| `void*` 不透明指针 | `[RISK: OPAQUE]` | 内部类型？生命周期？ |
| 可变长度参数（`...`） | `[RISK: VARARGS]` | 是否需要 Rust 侧镜像？ |
| 平台相关类型（`long`, `size_t`）| `[RISK: PLATFORM_TYPE]` | 64/32 位兼容策略？ |

**确认要求（必须全部完成，不得绕过）**：
- [ ] 每个风险信号已填写明确决策（接受 / 需额外封装 / 延迟到 Phase 2），不允许留空
- [ ] 每项"需额外封装"的风险信号已写出具体封装方案
- [ ] 报告中所有 `TODO` 项已清空
- [ ] 确认结果已反映到 `spec-v1.yml` 的对应函数条目中
- [ ] 负责人已签字（在报告末尾或 `spec-v1.yml` 的 `sign_off` 节）

> ⚠ **阻断门**：上述所有项未完成签字之前，**不得推进至 Step 3**。

---

### Step 3：ABI / FFI 设计 & 冻结 → ⚠ 人工确认点 2【阻断门】

参照 `templates/abi-freeze-checklist.md` 完成以下决策并冻结：

- [ ] 确定库产物形式（`staticlib` / `cdylib`）及命名
- [ ] 对每个 `#[repr(C)]` 结构体，验证字段偏移与 C 侧一致（须结合 Step 0 的数据类型清单）
- [ ] 确认调用约定（默认 C calling convention）
- [ ] 确认错误码策略（`i32` 返回码 + TLS `last_error`）
- [ ] 确认内存归属策略（handle 模式 / 调用者分配）
- [ ] 确认 `panic` 处理策略（FFI 边界 `catch_unwind`）
- [ ] 确认目标平台矩阵（与 Step 0 一致）
- [ ] 导出符号清单（来自 Step 0 第 4 节）与 `abi-freeze-checklist.md` 第 2 节逐一核对

**确认要求（必须全部完成，不得绕过）**：
- [ ] `templates/abi-freeze-checklist.md` 所有条目已逐项打勾
- [ ] 导出符号清单已填写（来自 Step 0 的实测 `nm`/`objdump` 结果）
- [ ] 结构体 `sizeof`/`offsetof` 对照表已填写
- [ ] 错误码对照表已填写
- [ ] 负责人已签字，ABI 进入冻结状态

> ⚠ **阻断门**：冻结签字完成之前，**不得推进至 Step 4**。Phase 1 期间 ABI 不允许修改；如需修改须重走此步骤。

---

### Step 4：差分测试分级决策 → ⚠ 人工确认点 3【阻断门】

根据 `generate_report.py` 输出的分级建议，人工确认采用哪个 Tier：

| Tier | 描述 | 适用场景 |
|---|---|---|
| **Tier 0** | 不额外增加差分测试；完全复用现有 C 测试 | 接口简单、无回调、输出确定性强 |
| **Tier 1** | 增加输入/输出 golden file 对比测试 | 有复杂输出结构或多返回路径 |
| **Tier 2** | 增加模糊测试 + 差分对比（C 实现 vs Rust 实现并行运行） | 高风险：回调密集、全局状态复杂、历史 bug 多 |

> Step 0 中标记的"无测试覆盖"接口，至少须选 Tier 1。

**确认要求（必须全部完成，不得绕过）**：
- [ ] `templates/compatibility-validation-plan.md` 中，每个北向接口已选定 Tier
- [ ] Step 0 中所有"无测试覆盖"接口已选 Tier 1 或 Tier 2，并说明补充测试方案
- [ ] 若选定 Tier 与建议 Tier 不同，已填写变更理由
- [ ] 测试覆盖目标已填写（覆盖率阈值、模糊测试时长等）
- [ ] 负责人已签字

> ⚠ **阻断门**：签字完成之前，**不得推进至 Step 5**。

---

### Step 5：Rust FFI 层实现

基于冻结的 ABI 设计和 Spec v1（含实现分析节），实现薄 FFI 层：

- 使用 `hicc::import_lib!` 或 `bindgen` 生成 C ABI 绑定（参见 `r2rust-ffi-creator` 技能）。
- 对每个北向接口，在 Rust 侧实现对应的 `extern "C"` 导出函数，内部调用 C 实现。
  - **实现时必须参考 `spec-v1.yml` 中的 `implementation_analysis` 节**，而非仅对照接口签名。
  - 确保内部调用链、全局状态初始化、数据类型布局均与 C 实现一致。
- 确保 `panic` 不跨越 FFI 边界（`std::panic::catch_unwind`）。
- 现有 C 测试通过链接 Rust 静态库运行，验证行为等价。

> 参见 `r2rust-ffi-creator/SKILL.md` 了解 hicc crate 的具体用法。

---

### Step 6：Phase 1 验收 → ⚠ 人工确认点 4【阻断门】

参照 `templates/phase1-acceptance-criteria.md`，逐项验证并人工确认：

- [ ] 所有现有 C 测试（或复用的测试向量）通过（须提供测试运行日志）
- [ ] Tier 1/2 差分测试（若适用）通过
- [ ] Valgrind / AddressSanitizer 无内存错误
- [ ] `cargo miri test` 无未定义行为（若适用）
- [ ] ABI 与冻结清单一致（`nm` 验证导出符号，须与 Step 0 第 4 节实测结果一致）
- [ ] `panic` 不跨越 FFI 边界（测试 edge case 触发 panic）
- [ ] 性能：关键路径无不可接受退化（基准测试对比）
- [ ] 文档：每个公开 FFI 函数有 `/// # Safety` 注释
- [ ] `spec-v1.yml` 中所有 `TODO` 已清空

**确认要求（必须全部完成，不得绕过）**：
- [ ] `templates/phase1-acceptance-criteria.md` 所有条目逐项打勾
- [ ] 测试运行日志已附上（链接或路径）
- [ ] `nm` 符号验证输出已附上
- [ ] 未解决问题已记录在清单末尾的表格中，并有 Issue 跟踪
- [ ] 负责人已签字

> ⚠ **阻断门**：签字完成之前，**不得推进至 Phase 2 的任何步骤**。

---

### Step 7：Phase 2 变更提案 → ⚠ 人工确认点 5【阻断门】

参照 `templates/phase2-change-proposal.md`，为每个计划变更创建提案（CHG-xxx）：

- 每项提案包含：变更动机、旧行为、新行为、破坏等级、迁移方式、验收测试。
- 所有提案汇总后，由用户/产品负责人逐项审查并决策（接受 / 拒绝 / 延后）。
- **确认要求（必须全部完成，不得绕过）**：
  - [ ] 每个 CHG-xxx 提案均有完整填写（无空白字段）
  - [ ] 每个 CHG-xxx 已有明确的接受/拒绝/延后决策
  - [ ] 被接受的 CHG-xxx 均有对应的验收测试描述
  - [ ] 产品/用户负责人已逐项签字确认

> ⚠ **阻断门**：签字完成之前，**不得开始 Phase 2 的任何实现工作**。

---

## 人工确认点汇总

| 编号 | 时机 | 确认内容（摘要） | 对应模板 | 阻断 |
|---|---|---|---|---|
| ⚠ 0 | Step 0 完成后 | C 项目构建/符号/测试/实现依赖分析 | `c-project-analysis.md` | **是** |
| ⚠ 1 | Step 2 完成后 | 风险信号处置策略（每项必填决策） | `generate_report.py` 输出 | **是** |
| ⚠ 2 | Step 3 完成后 | ABI / FFI 冻结（符号清单须来自实测） | `abi-freeze-checklist.md` | **是** |
| ⚠ 3 | Step 4 完成后 | 差分测试分级（无覆盖接口须选 Tier≥1） | `compatibility-validation-plan.md` | **是** |
| ⚠ 4 | Step 6 完成后 | Phase 1 验收（须附日志与符号验证） | `phase1-acceptance-criteria.md` | **是** |
| ⚠ 5 | Step 7 完成后 | Phase 2 变更逐项确认 | `phase2-change-proposal.md` | **是** |

> 所有确认点均为硬性阻断门。签字前不得跳步，签字后记录方具有约束力。

---

## 参考资料

- `templates/c-project-analysis.md`：C 项目完整分析模板（Step 0）
- `scripts/analyze_c_project.py`：C 项目完整分析器（Step 0 自动化工具）
- `r2rust-ffi-creator/SKILL.md`：hicc crate 驱动的 Rust FFI 适配层搭建指南
- `r2rust-ffi-creator/references/hicc.md`：hicc crate API 参考
- `templates/`：所有可用模板
- `scripts/`：自动化脚本
- `examples/`：示例输出
