# c2rust-migration-skill Makefile
#
# 用法：
#   make translate HEADERS=/path/to/include  # Phase 1：扫描头文件并生成迁移分析报告
#   make refactor                            # Phase 2：生成变更提案模板
#   make scan      HEADERS=/path/to/include  # 仅扫描头文件
#   make report    HEADERS=/path/to/include  # 扫描头文件并生成报告（同 translate）
#   make test                                # 运行脚本冒烟测试
#   make help                                # 显示帮助

PYTHON    ?= python3
SKILL_DIR := c2rust-migration-skill
SCRIPTS   := $(SKILL_DIR)/scripts

# 输出文件路径（可通过命令行覆盖）
SPEC_OUT      ?= spec-v1.yml
REPORT_OUT    ?= report.md
PROPOSAL_OUT  ?= phase2-change-proposal.md

# 测试覆盖率估算（0.0~1.0），影响差分测试分级建议
TEST_COVERAGE ?= 0.5

.PHONY: help scan report translate refactor test

help:
	@echo "c2rust-migration-skill — C→Rust 迁移辅助工具"
	@echo ""
	@echo "目标："
	@echo "  translate HEADERS=<目录>  Phase 1：扫描 C 头文件并生成完整迁移分析报告"
	@echo "  refactor                  Phase 2：生成 Phase 2 变更提案模板"
	@echo "  scan      HEADERS=<目录>  仅扫描 C 头文件，生成 Spec v1 YAML 骨架"
	@echo "  report    HEADERS=<目录>  扫描头文件并生成完整迁移分析报告（同 translate）"
	@echo "  test                      运行脚本冒烟测试"
	@echo ""
	@echo "可选变量（make 命令行传入）："
	@echo "  HEADERS=<路径>            头文件目录或单个 .h 文件"
	@echo "  SPEC_OUT=<路径>           Spec v1 输出路径（默认：spec-v1.yml）"
	@echo "  REPORT_OUT=<路径>         报告输出路径（默认：report.md）"
	@echo "  PROPOSAL_OUT=<路径>       Phase 2 提案输出路径（默认：phase2-change-proposal.md）"
	@echo "  TEST_COVERAGE=<比例>      测试覆盖率估算（默认：0.5）"
	@echo "  PYTHON=<命令>             Python 解释器（默认：python3）"
	@echo ""
	@echo "示例："
	@echo "  make translate HEADERS=my_project/include TEST_COVERAGE=0.7"
	@echo "  make refactor"

translate:
ifndef HEADERS
	$(error 请指定头文件目录：make translate HEADERS=/path/to/include)
endif
	PYTHON="$(PYTHON)" SPEC_OUT="$(SPEC_OUT)" REPORT_OUT="$(REPORT_OUT)" \
	TEST_COVERAGE="$(TEST_COVERAGE)" \
	bash $(SCRIPTS)/translate.sh HEADERS="$(HEADERS)"

refactor:
	PROPOSAL_OUT="$(PROPOSAL_OUT)" \
	bash $(SCRIPTS)/refactor.sh

scan:
ifndef HEADERS
	$(error 请指定头文件目录：make scan HEADERS=/path/to/include)
endif
	$(PYTHON) $(SCRIPTS)/scan_headers.py \
		"$(HEADERS)" \
		--recursive \
		--output "$(SPEC_OUT)"
	@echo "Spec v1 已写入：$(SPEC_OUT)"

report: scan
	$(PYTHON) $(SCRIPTS)/generate_report.py \
		"$(SPEC_OUT)" \
		--output "$(REPORT_OUT)" \
		--test-coverage "$(TEST_COVERAGE)"
	@echo "报告已写入：$(REPORT_OUT)"

test:
	bash $(SCRIPTS)/smoke_test.sh
