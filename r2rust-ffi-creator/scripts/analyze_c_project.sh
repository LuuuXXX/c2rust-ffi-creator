#!/usr/bin/env bash
# analyze_c_project.sh - 分析 C 项目并生成元数据文档
# 用法: analyze_c_project.sh <.c2rust/c 路径>
# 示例: analyze_c_project.sh .c2rust/c

set -euo pipefail

usage() {
    echo "用法: $0 <.c2rust/c 路径>"
    echo ""
    echo "分析 C 项目结构，生成以下文档:"
    echo "  PROJECT_SPEC.md  - 项目规格"
    echo "  MODULE_DEPS.md   - 模块依赖关系"
    echo "  INTERFACES.md    - 南北向接口规格"
    echo "  BUILD_PLAN.md    - 构建方案"
    echo "  TEST_PLAN.md     - 测试方案"
    exit 1
}

[[ $# -lt 1 ]] && usage

C_DIR="$(realpath "$1")"

if [[ ! -d "$C_DIR" ]]; then
    echo "错误: 路径不存在: $C_DIR"
    exit 1
fi

echo "=== 分析 C 项目 ==="
echo "  目录: $C_DIR"
echo ""

# -------------------------------------------------------
# 辅助函数：统计文件
count_files() {
    find "$C_DIR" -type f -name "$1" | wc -l | tr -d ' '
}

# -------------------------------------------------------
# 生成 PROJECT_SPEC.md
echo "[1/5] 生成 PROJECT_SPEC.md..."
{
    echo "# 项目规格（Project Specification）"
    echo ""
    echo "## 基本信息"
    echo ""
    echo "- **分析时间**: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "- **C 源文件数**: $(count_files '*.c')"
    echo "- **头文件数**: $(count_files '*.h')"
    echo ""
    echo "## 对外暴露头文件"
    echo ""
    echo "以下头文件位于 \`include/\` 目录或项目根目录，推测为公开 API："
    echo ""
    # 查找 include/ 目录下的头文件
    if [[ -d "$C_DIR/include" ]]; then
        find "$C_DIR/include" -name "*.h" | sort | while read -r f; do
            echo "- \`${f#$C_DIR/}\`"
        done
    else
        # 根目录下的头文件
        find "$C_DIR" -maxdepth 1 -name "*.h" | sort | while read -r f; do
            echo "- \`${f#$C_DIR/}\`"
        done
    fi
    echo ""
    echo "## 编译产物类型"
    echo ""
    echo "请根据实际情况填写（删除不适用的项）："
    echo ""
    echo "- [ ] 动态库（.so / .dylib / .dll）"
    echo "- [ ] 静态库（.a / .lib）"
    echo "- [ ] 可执行文件"
    echo ""
    echo "## 外部依赖库"
    echo ""
    echo "> 待填写：通过 \`pkg-config --libs\` 或 CMakeLists.txt 中的 \`target_link_libraries\` 确认。"
    echo ""
    echo "## 功能描述"
    echo ""
    echo "> 待填写：简要描述该 C 库的功能与适用场景。"
} > "$C_DIR/PROJECT_SPEC.md"
echo "  已生成: $C_DIR/PROJECT_SPEC.md"

# -------------------------------------------------------
# 生成 MODULE_DEPS.md
echo "[2/5] 生成 MODULE_DEPS.md..."
{
    echo "# 模块划分与依赖关系（Module Dependency Map）"
    echo ""
    echo "## 源文件列表"
    echo ""
    find "$C_DIR" -name "*.c" | sort | while read -r f; do
        rel="${f#$C_DIR/}"
        echo "### \`$rel\`"
        echo ""
        echo "**直接包含的头文件：**"
        echo ""
        grep -E '#include\s*[<"]' "$f" 2>/dev/null | sed 's/^/- /' || echo "（无）"
        echo ""
    done
    echo ""
    echo "## 模块依赖图"
    echo ""
    echo "> 待填写：根据上述 #include 关系绘制模块依赖图（可用 ASCII 图或 mermaid）。"
    echo ""
    echo "\`\`\`"
    echo "示例（请替换为实际依赖）："
    echo "  main.c"
    echo "  ├── depends on: utils.h → utils.c"
    echo "  └── depends on: core.h  → core.c"
    echo "      └── depends on: types.h"
    echo "\`\`\`"
} > "$C_DIR/MODULE_DEPS.md"
echo "  已生成: $C_DIR/MODULE_DEPS.md"

# -------------------------------------------------------
# 生成 INTERFACES.md
echo "[3/5] 生成 INTERFACES.md..."
{
    echo "# 模块南北向接口规格（Interface Specifications）"
    echo ""
    echo "## 术语说明"
    echo ""
    echo "- **北向（Northbound）接口**：模块向上层（调用方）暴露的接口"
    echo "- **南向（Southbound）接口**：模块依赖下层（被调用方）的接口"
    echo ""
    echo "---"
    echo ""
    echo "## 公开函数列表"
    echo ""
    echo "以下函数从头文件中自动提取（需人工审核）："
    echo ""
    # 提取头文件中的函数声明
    find "$C_DIR" -name "*.h" | sort | while read -r f; do
        rel="${f#$C_DIR/}"
        echo "### \`$rel\`"
        echo ""
        # 提取非宏、非 static、非 inline 的函数声明
        grep -E '^[a-zA-Z_][a-zA-Z0-9_ *]+\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(' "$f" 2>/dev/null \
            | grep -v '//' | grep -v 'static ' | grep -v '#define' \
            | head -50 \
            | sed 's/^/```c\n/' \
            | sed 's/$/\n```\n/' \
            || echo "（未找到函数声明，请手动填写）"
        echo ""
    done
    echo ""
    echo "---"
    echo ""
    echo "## 接口规格模板（每个公开函数填写）"
    echo ""
    echo "使用 \`references/interface_template.md\` 中的模板为每个函数填写完整规格。"
    echo ""
    echo "重点关注："
    echo "- 参数类型与所有权语义（调用方/被调用方负责释放）"
    echo "- 返回值含义（成功/失败/错误码）"
    echo "- 线程安全性（是否依赖全局状态）"
    echo "- 内存分配行为（栈/堆，谁分配谁释放）"
    echo "- 副作用（修改全局状态/文件/网络等）"
} > "$C_DIR/INTERFACES.md"
echo "  已生成: $C_DIR/INTERFACES.md"

# -------------------------------------------------------
# 生成 BUILD_PLAN.md
echo "[4/5] 生成 BUILD_PLAN.md..."
{
    echo "# 构建方案（Build Plan）"
    echo ""
    echo "## 构建系统"
    echo ""
    if [[ -f "$C_DIR/CMakeLists.txt" ]]; then
        echo "**CMake** (检测到 CMakeLists.txt)"
        echo ""
        echo "\`\`\`bash"
        echo "cmake -B build -DCMAKE_BUILD_TYPE=Release"
        echo "cmake --build build"
        echo "\`\`\`"
        echo ""
        echo "### CMakeLists.txt 摘要"
        echo ""
        echo "\`\`\`cmake"
        head -50 "$C_DIR/CMakeLists.txt" 2>/dev/null || echo "（无法读取）"
        echo "\`\`\`"
    elif [[ -f "$C_DIR/Makefile" ]]; then
        echo "**Make** (检测到 Makefile)"
        echo ""
        echo "\`\`\`bash"
        echo "make"
        echo "\`\`\`"
        echo ""
        echo "### Makefile 摘要"
        echo ""
        echo "\`\`\`makefile"
        head -50 "$C_DIR/Makefile" 2>/dev/null || echo "（无法读取）"
        echo "\`\`\`"
    else
        echo "> 未检测到标准构建文件（CMakeLists.txt / Makefile），请手动填写。"
    fi
    echo ""
    echo "## 编译器与标志"
    echo ""
    echo "| 项目 | 值 |"
    echo "|------|----|"
    echo "| 编译器 | gcc / clang（请确认） |"
    echo "| C 标准 | -std=c11（请确认） |"
    echo "| 优化级别 | -O2（Release）|"
    echo "| 警告标志 | -Wall -Wextra（请确认）|"
    echo ""
    echo "## 构建产物路径"
    echo ""
    echo "> 待填写：例如 \`build/libXXX.so\` 或 \`build/libXXX.a\`"
} > "$C_DIR/BUILD_PLAN.md"
echo "  已生成: $C_DIR/BUILD_PLAN.md"

# -------------------------------------------------------
# 生成 TEST_PLAN.md
echo "[5/5] 生成 TEST_PLAN.md..."
{
    echo "# 测试方案（Test Plan）"
    echo ""
    echo "## 测试文件"
    echo ""
    echo "以下文件推测为测试代码："
    echo ""
    find "$C_DIR" -type f -name "*.c" | xargs grep -l "assert\|TEST\|test_\|suite\|check" 2>/dev/null \
        | sort | while read -r f; do
        echo "- \`${f#$C_DIR/}\`"
    done || echo "（未找到测试文件，请手动填写）"
    echo ""
    echo "## 运行测试"
    echo ""
    if [[ -f "$C_DIR/CMakeLists.txt" ]]; then
        echo "\`\`\`bash"
        echo "cmake -B build -DCMAKE_BUILD_TYPE=Debug"
        echo "cmake --build build"
        echo "ctest --test-dir build --output-on-failure"
        echo "\`\`\`"
    elif [[ -f "$C_DIR/Makefile" ]]; then
        echo "\`\`\`bash"
        echo "make test"
        echo "# 或"
        echo "make check"
        echo "\`\`\`"
    else
        echo "> 待填写：测试运行命令。"
    fi
    echo ""
    echo "## 预期结果"
    echo ""
    echo "> 待填写：运行测试后的预期输出，例如："
    echo ">"
    echo "> \`\`\`"
    echo "> Running test suite..."
    echo "> Tests passed: 42/42"
    echo "> \`\`\`"
    echo ""
    echo "## 测试覆盖范围"
    echo ""
    echo "| 模块 | 测试文件 | 覆盖函数 | 覆盖率 |"
    echo "|------|----------|----------|--------|"
    echo "| (待填写) | | | |"
} > "$C_DIR/TEST_PLAN.md"
echo "  已生成: $C_DIR/TEST_PLAN.md"

echo ""
echo "=== 分析完成 ==="
echo ""
echo "生成的文档（请人工审核并补充）："
echo "  $C_DIR/PROJECT_SPEC.md"
echo "  $C_DIR/MODULE_DEPS.md"
echo "  $C_DIR/INTERFACES.md"
echo "  $C_DIR/BUILD_PLAN.md"
echo "  $C_DIR/TEST_PLAN.md"
echo ""
echo "下一步: 人工审核文档后，运行 build_c.sh 构建 C 版本"
