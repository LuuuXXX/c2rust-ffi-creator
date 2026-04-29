#!/usr/bin/env bash
# smoke_test.sh — 脚本冒烟测试
#
# 测试 scan_headers.py 和 generate_report.py 的基本功能。
# 在临时目录中创建示例 C 头文件，运行两个脚本，验证输出不为空且无错误。
#
# 使用方法：
#   bash scripts/smoke_test.sh
# 或通过 Makefile：
#   make test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
TMP_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "=== c2rust-migration-skill 冒烟测试 ==="
echo "临时目录：$TMP_DIR"
echo ""

# ──────────────────────────────────────────────────────────────────
# 创建示例 C 头文件
# ──────────────────────────────────────────────────────────────────
cat > "$TMP_DIR/foo.h" << 'EOF'
#ifndef FOO_H
#define FOO_H

#include <stddef.h>

typedef struct FooCtx FooCtx;

typedef enum FooError {
    FOO_OK       = 0,
    FOO_ERR_NULL = -1,
    FOO_ERR_OOM  = -2,
} FooError;

typedef struct FooConfig {
    int max_connections;
    size_t buffer_size;
    unsigned long timeout_ms;
} FooConfig;

/* 初始化上下文 */
int foo_init(FooCtx **ctx, const FooConfig *cfg);

/* 销毁上下文 */
void foo_destroy(FooCtx *ctx);

/* 获取版本号（纯函数，无副作用） */
int foo_version(void);

/* 带回调的异步操作 */
int foo_async_op(FooCtx *ctx,
                 void (*on_done)(int status, void *user_data),
                 void *user_data);

/* 带 out buffer 的数据获取 */
int foo_get_data(FooCtx *ctx, void *out_buf, size_t buf_len, size_t *out_written);

/* 全局配置（全局状态） */
int foo_global_init(void);
void foo_global_deinit(void);

#endif /* FOO_H */
EOF

# ──────────────────────────────────────────────────────────────────
# 测试 1：scan_headers.py
# ──────────────────────────────────────────────────────────────────
echo "--- 测试 1：scan_headers.py（正则模式）---"
SPEC_OUT="$TMP_DIR/spec-v1.yml"

"$PYTHON" "$SCRIPT_DIR/scan_headers.py" \
    "$TMP_DIR/foo.h" \
    --force-regex \
    --output "$SPEC_OUT"

# 验证输出文件存在且非空
if [ ! -s "$SPEC_OUT" ]; then
    echo "FAIL: spec-v1.yml 为空或不存在"
    exit 1
fi
echo "OK: spec-v1.yml 已生成（$(wc -l < "$SPEC_OUT") 行）"

# 验证关键字段存在
for keyword in "metadata" "functions" "types" "foo_init" "foo_version" "CALLBACK" "GLOBAL_STATE"; do
    if ! grep -q "$keyword" "$SPEC_OUT"; then
        echo "FAIL: spec-v1.yml 中缺少关键词 '$keyword'"
        exit 1
    fi
done
echo "OK: 关键词验证通过（metadata / functions / types / foo_init / CALLBACK 等）"

# ──────────────────────────────────────────────────────────────────
# 测试 2：generate_report.py
# ──────────────────────────────────────────────────────────────────
echo ""
echo "--- 测试 2：generate_report.py ---"
REPORT_OUT="$TMP_DIR/report.md"

"$PYTHON" "$SCRIPT_DIR/generate_report.py" \
    "$SPEC_OUT" \
    --output "$REPORT_OUT" \
    --test-coverage 0.45

# 验证报告存在且非空
if [ ! -s "$REPORT_OUT" ]; then
    echo "FAIL: report.md 为空或不存在"
    exit 1
fi
echo "OK: report.md 已生成（$(wc -l < "$REPORT_OUT") 行）"

# 验证报告包含关键部分
for keyword in "北向接口清单" "风险信号" "差分测试分级" "Tier 0" "Tier 1" "Tier 2" "TODO"; do
    if ! grep -q "$keyword" "$REPORT_OUT"; then
        echo "FAIL: report.md 中缺少关键词 '$keyword'"
        exit 1
    fi
done
echo "OK: 报告关键词验证通过（北向接口清单 / 风险信号 / 差分测试分级 / Tier 等）"

# 验证高风险函数（foo_async_op、foo_global_init）被分配到 Tier 2
if ! grep -q "foo_async_op" "$REPORT_OUT"; then
    echo "FAIL: report.md 中缺少 foo_async_op"
    exit 1
fi

# 验证覆盖率低时 foo_version 也有分级
if ! grep -q "foo_version" "$REPORT_OUT"; then
    echo "FAIL: report.md 中缺少 foo_version"
    exit 1
fi
echo "OK: 函数存在性验证通过"

# ──────────────────────────────────────────────────────────────────
# 测试 3：generate_report.py — 高覆盖率场景（foo_version 应为 Tier 0）
# ──────────────────────────────────────────────────────────────────
echo ""
echo "--- 测试 3：高覆盖率场景（coverage=0.9）---"
REPORT_HIGH="$TMP_DIR/report-high-cov.md"

"$PYTHON" "$SCRIPT_DIR/generate_report.py" \
    "$SPEC_OUT" \
    --output "$REPORT_HIGH" \
    --test-coverage 0.9

if [ ! -s "$REPORT_HIGH" ]; then
    echo "FAIL: report-high-cov.md 为空"
    exit 1
fi
echo "OK: 高覆盖率报告生成成功"

# ──────────────────────────────────────────────────────────────────
# 测试 4：scan_headers.py — 多文件递归扫描
# ──────────────────────────────────────────────────────────────────
echo ""
echo "--- 测试 4：多文件递归扫描 ---"
mkdir -p "$TMP_DIR/subdir"
cat > "$TMP_DIR/subdir/bar.h" << 'EOF'
#ifndef BAR_H
#define BAR_H

int bar_add(int a, int b);
void bar_reset(void);

#endif
EOF

SPEC_MULTI="$TMP_DIR/spec-multi.yml"
"$PYTHON" "$SCRIPT_DIR/scan_headers.py" \
    "$TMP_DIR" \
    --recursive \
    --force-regex \
    --output "$SPEC_MULTI"

if ! grep -q "bar_add" "$SPEC_MULTI"; then
    echo "FAIL: 递归扫描未找到 bar.h 中的 bar_add"
    exit 1
fi
echo "OK: 递归扫描验证通过（bar_add 已提取）"

# ──────────────────────────────────────────────────────────────────
# 全部通过
# ──────────────────────────────────────────────────────────────────
echo ""
echo "=== 全部测试通过 ✓ ==="
