# c2rust-ffi-creator

> **用途**：一套结构化的 C→Rust 迁移技能（Skill）集合，提供可操作的工作流、模板和脚本，
> 帮助团队将既有 C 项目安全、可验证地迁移到 Rust。

---

## 技能目录

| 技能 | 说明 | 入口 |
|---|---|---|
| **r2rust-ffi-creator** | 基于 `hicc` crate，为已有 C 项目搭建 Rust FFI 适配层（渐进式重构） | [SKILL.md](r2rust-ffi-creator/SKILL.md) |
| **c2rust-migration-skill** | 两阶段 C→Rust 完全替代迁移（Phase 1：位级兼容替代；Phase 2：可控优化） | [README.md](skills/c2rust-migration-skill/README.md) |

---

## c2rust-migration-skill 快速开始

```bash
# 扫描 C 头文件并生成迁移分析报告
make report HEADERS=/path/to/your/c/headers

# 仅运行脚本冒烟测试
make test
```

详见：[skills/c2rust-migration-skill/README.md](skills/c2rust-migration-skill/README.md)

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
├── skills/
│   └── c2rust-migration-skill/          ← 技能：两阶段完全替代迁移
│       ├── README.md
│       ├── templates/
│       │   ├── spec-v1-extraction.yml
│       │   ├── compatibility-validation-plan.md
│       │   ├── abi-freeze-checklist.md
│       │   ├── phase1-acceptance-criteria.md
│       │   └── phase2-change-proposal.md
│       ├── scripts/
│       │   ├── scan_headers.py
│       │   ├── generate_report.py
│       │   └── smoke_test.sh
│       └── examples/
│           ├── sample-spec-v1.yml
│           └── sample-report.md
└── dist/
    └── r2rust-ffi-creator.zip
```
