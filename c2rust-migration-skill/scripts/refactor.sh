#!/usr/bin/env bash
# refactor.sh — Phase 2：可控优化（Rust 重构阶段）
#
# 执行 c2rust-migration-skill 的第二阶段工作流：
#   Step 7: 输出 Phase 2 变更提案模板，指导用户填写 CHG-xxx 提案
#
# 前提：Phase 1 所有验收标准（templates/phase1-acceptance-criteria.md）已全部通过。
#
# 使用方法：
#   bash refactor.sh
#   bash refactor.sh PROPOSAL_OUT=<提案输出路径>
#
# 环境变量（均可通过命令行 KEY=VALUE 传入）：
#   PROPOSAL_OUT   — Phase 2 变更提案输出路径（默认：phase2-change-proposal.md）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES_DIR="$(cd "$SCRIPT_DIR/../templates" && pwd)"
PROPOSAL_OUT="${PROPOSAL_OUT:-phase2-change-proposal.md}"

# 解析 KEY=VALUE 参数
for arg in "$@"; do
    case "$arg" in
        PROPOSAL_OUT=*) PROPOSAL_OUT="${arg#PROPOSAL_OUT=}" ;;
    esac
done

echo "=== c2rust-migration-skill refactor (Phase 2) ==="
echo ""

# 检查是否已存在提案文件
if [ -f "$PROPOSAL_OUT" ]; then
    echo "提案文件已存在：$PROPOSAL_OUT"
    echo "（如需重新生成，请先删除该文件后重新运行）"
    echo ""
else
    # 复制模板到工作目录
    if [ -f "$TEMPLATES_DIR/phase2-change-proposal.md" ]; then
        cp "$TEMPLATES_DIR/phase2-change-proposal.md" "$PROPOSAL_OUT"
        echo "Phase 2 变更提案模板已复制到：$PROPOSAL_OUT"
        echo ""
    else
        echo "警告：未找到模板文件 $TEMPLATES_DIR/phase2-change-proposal.md" >&2
        echo "请手动参照 templates/phase2-change-proposal.md 创建提案。" >&2
    fi
fi

echo "=== Phase 2 准备工作完成 ==="
echo ""
echo "后续步骤（详见 $PROPOSAL_OUT 与 README.md）："
echo "  ⚠ 确认点 5（Step 6a）：先完成接口重设计工作坊（$PROPOSAL_OUT 的「接口重设计工作坊」节）"
echo "  　　        → 层 1：数据类型层重审（跨 FFI 类型 → Rust 惯用类型）"
echo "  　　        → 层 2：实现依赖层重审（C 特有依赖 → Rust 惯用替代）"
echo "  　　        → 层 3：顶层接口架构重审（模块/Trait/API 粒度蓝图）"
echo "  　　        → 主导设计人与审查人签字后，方可开始填写 CHG-xxx 提案"
echo "  ⚠ 确认点 6（Step 7）：为每项计划变更填写 CHG-xxx 提案（变更动机、旧行为、新行为、破坏等级、迁移方式、验收测试）"
echo "  　　        → 所有 CHG-xxx 须与工作坊蓝图一致"
echo "  　　        → 由用户/产品负责人逐项审查并决策（接受 / 拒绝 / 延后）"
echo "  　　        → 完成后签字冻结，作为 Phase 2 实现的唯一依据"
echo ""
echo "  实施顺序："
echo "    Step 6a: 接口重设计工作坊（$PROPOSAL_OUT 工作坊节，⚠ 阻断门）"
echo "    Step 7:   填写并冻结变更提案（$PROPOSAL_OUT CHG-xxx 节，⚠ 阻断门）"
echo "    Step 8:   变更冻结 & 输出 Spec v2"
echo "    Step 9:   v2 实现、测试更新、文档更新"
echo "    Step 10:  Phase 2 发布 & 迁移指南发布"
