# c2rust-migration-skill Makefile
#
# 用法：
#   make analyze  PROJECT=<根目录> HEADERS=<头文件目录>  # Step 0：C 项目完整分析
#   make translate PROJECT=<根目录> HEADERS=<头文件目录>  # Phase 1：Step 0 分析（暂停等待签字）
#   make translate PROJECT=<根目录> HEADERS=<路径> SKIP_STEP0=1  # Phase 1：Step 1+2（Step 0 已签字）
#   make refactor                            # Phase 2：生成变更提案模板
#   make scan      HEADERS=/path/to/include  # 仅扫描头文件
#   make report    HEADERS=/path/to/include  # 扫描头文件并生成报告
#   make test                                # 运行脚本冒烟测试
#   make help                                # 显示帮助

PYTHON    ?= python3
SKILL_DIR := c2rust-migration-skill
SCRIPTS   := $(SKILL_DIR)/scripts

# 输出文件路径（可通过命令行覆盖）
ANALYSIS_OUT  ?= c-project-analysis.md
SPEC_OUT      ?= spec-v1.yml
REPORT_OUT    ?= report.md
PROPOSAL_OUT  ?= phase2-change-proposal.md

# 测试覆盖率估算（0.0~1.0），影响差分测试分级建议；建议从 Step 0 结果中获取
TEST_COVERAGE ?= 0.5

# Step 0 控制：设为 1 可跳过（仅在已有签字确认的 c-project-analysis.md 时使用）
SKIP_STEP0 ?= 0

.PHONY: help analyze scan report translate refactor test

help:
	@echo "c2rust-migration-skill — C→Rust 迁移辅助工具"
	@echo ""
	@echo "目标："
	@echo "  analyze   PROJECT=<根目录> HEADERS=<目录>  Step 0：C 项目完整分析（构建/符号/测试/实现依赖）"
	@echo "  translate PROJECT=<根目录> HEADERS=<目录>  Phase 1：运行 Step 0 后暂停，等待人工签字"
	@echo "            （加 SKIP_STEP0=1 可跳过 Step 0，直接执行 Step 1+2）"
	@echo "  refactor                                  Phase 2：生成 Phase 2 变更提案模板"
	@echo "  scan      HEADERS=<目录>                  仅扫描 C 头文件，生成 Spec v1 YAML 骨架"
	@echo "  report    HEADERS=<目录>                  扫描头文件并生成完整迁移分析报告"
	@echo "  test                                      运行脚本冒烟测试"
	@echo ""
	@echo "可选变量（make 命令行传入）："
	@echo "  PROJECT=<路径>            C 项目根目录（Step 0 必须）"
	@echo "  HEADERS=<路径>            头文件目录或单个 .h 文件"
	@echo "  BINARY=<路径>             已构建的 C 库文件（Step 0 符号提取，可选）"
	@echo "  ANALYSIS_OUT=<路径>       Step 0 分析报告输出路径（默认：c-project-analysis.md）"
	@echo "  SPEC_OUT=<路径>           Spec v1 输出路径（默认：spec-v1.yml）"
	@echo "  REPORT_OUT=<路径>         报告输出路径（默认：report.md）"
	@echo "  PROPOSAL_OUT=<路径>       Phase 2 提案输出路径（默认：phase2-change-proposal.md）"
	@echo "  TEST_COVERAGE=<比例>      测试覆盖率估算（默认：0.5，建议从 Step 0 结果获取）"
	@echo "  SKIP_STEP0=1              跳过 Step 0（仅在已有签字 c-project-analysis.md 时使用）"
	@echo "  PYTHON=<命令>             Python 解释器（默认：python3）"
	@echo ""
	@echo "典型用法："
	@echo "  # 第一步：运行 Step 0 分析，生成 c-project-analysis.md"
	@echo "  make translate PROJECT=my_project HEADERS=my_project/include"
	@echo "  # 审查 c-project-analysis.md，补全 TODO，签字"
	@echo "  # 第二步：签字后继续 Step 1+2"
	@echo "  make translate PROJECT=my_project HEADERS=my_project/include SKIP_STEP0=1"
	@echo "  make refactor"

analyze:
ifndef HEADERS
	$(error 请指定头文件目录：make analyze PROJECT=<根目录> HEADERS=/path/to/include)
endif
	$(PYTHON) $(SCRIPTS)/analyze_c_project.py \
		"$(or $(PROJECT),$(HEADERS))" \
		--headers "$(HEADERS)" \
		$(if $(BINARY),--binary "$(BINARY)",) \
		--output "$(ANALYSIS_OUT)"
	@echo ""
	@echo "Step 0 分析报告已写入：$(ANALYSIS_OUT)"
	@echo "请审查并补全所有 TODO 项，在文末签字后再继续 Step 1。"

translate:
ifndef HEADERS
	$(error 请指定头文件目录：make translate PROJECT=<根目录> HEADERS=/path/to/include)
endif
	PYTHON="$(PYTHON)" \
	ANALYSIS_OUT="$(ANALYSIS_OUT)" \
	SPEC_OUT="$(SPEC_OUT)" \
	REPORT_OUT="$(REPORT_OUT)" \
	TEST_COVERAGE="$(TEST_COVERAGE)" \
	SKIP_STEP0="$(SKIP_STEP0)" \
	bash $(SCRIPTS)/translate.sh \
		PROJECT="$(or $(PROJECT),$(HEADERS))" \
		HEADERS="$(HEADERS)" \
		$(if $(BINARY),BINARY="$(BINARY)",)

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
