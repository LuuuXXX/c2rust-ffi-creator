# c2rust-ffi-creator

> **用途**：一套结构化的 C→Rust 迁移技能（Skill）集合，提供可操作的工作流、模板和脚本，
> 帮助团队将既有 C 项目安全、可验证地迁移到 Rust。

---

## 技能目录

| 技能 | 说明 | 入口 |
|---|---|---|
| **r2rust-ffi-creator** | 基于 `hicc` crate，为已有 C 项目搭建 Rust FFI 适配层（渐进式重构） | [SKILL.md](r2rust-ffi-creator/SKILL.md) |
| **c2rust-migration-skill translate** | Phase 1：扫描 C 头文件、生成 Spec v1 与迁移分析报告、指导位级兼容 Rust 替代 | [README.md](c2rust-migration-skill/README.md) |
| **c2rust-migration-skill refactor** | Phase 2：生成变更提案模板，指导可控优化与 Rust 惯用化重构（须先完成 Phase 1） | [README.md](c2rust-migration-skill/README.md) |

---

## c2rust-migration-skill 快速开始

```bash
# Phase 1：扫描 C 头文件并生成迁移分析报告
make translate HEADERS=/path/to/your/c/headers

# Phase 2：生成 Phase 2 变更提案模板（须先完成 Phase 1）
make refactor

# 仅运行脚本冒烟测试
make test
```

详见：[c2rust-migration-skill/README.md](c2rust-migration-skill/README.md)

---

## 仓库结构

```
c2rust-ffi-creator/
├── README.md                            ← 本文件（总索引）
├── Makefile                             ← 顶层 make 命令
├── r2rust-ffi-creator/                  ← 技能：FFI 适配层搭建
│   ├── SKILL.md
│   └── references/
│       └── hicc.md
├── c2rust-migration-skill/              ← 技能：两阶段完全替代迁移
│   ├── README.md
│   ├── templates/
│   │   ├── spec-v1-extraction.yml
│   │   ├── compatibility-validation-plan.md
│   │   ├── abi-freeze-checklist.md
│   │   ├── phase1-acceptance-criteria.md
│   │   └── phase2-change-proposal.md
│   ├── scripts/
│   │   ├── translate.sh
│   │   ├── refactor.sh
│   │   ├── scan_headers.py
│   │   ├── generate_report.py
│   │   └── smoke_test.sh
│   └── examples/
│       ├── sample-spec-v1.yml
│       └── sample-report.md
└── dist/
    └── r2rust-ffi-creator.zip
```
