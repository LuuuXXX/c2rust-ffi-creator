#!/usr/bin/env bash
# test_c.sh - 运行 C 版本测试
# 用法: test_c.sh <.c2rust/c 路径>
# 示例: test_c.sh .c2rust/c

set -euo pipefail

usage() {
    echo "用法: $0 <.c2rust/c 路径>"
    exit 1
}

[[ $# -lt 1 ]] && usage

C_DIR="$(realpath "$1")"
BUILD_DIR="$C_DIR/_build"

echo "=== 运行 C 版本测试 ==="
echo "  目录: $C_DIR"
echo ""

if [[ -f "$C_DIR/CMakeLists.txt" ]]; then
    echo "[CMake CTest]"
    if [[ ! -d "$BUILD_DIR" ]]; then
        echo "  提示：先运行 build_c.sh 构建项目"
        cmake -B "$BUILD_DIR" -S "$C_DIR" -DCMAKE_BUILD_TYPE=Debug
        cmake --build "$BUILD_DIR"
    fi
    ctest --test-dir "$BUILD_DIR" --output-on-failure
elif [[ -f "$C_DIR/Makefile" ]]; then
    echo "[Make test]"
    make -C "$C_DIR" test BUILD_DIR="$BUILD_DIR" || \
    make -C "$C_DIR" check BUILD_DIR="$BUILD_DIR"
else
    # 回退：编译并运行测试文件
    echo "[回退测试：编译并运行测试文件]"
    TEST_FILES=($(find "$C_DIR" -name "*.c" -path "*/test*"))
    
    if [[ ${#TEST_FILES[@]} -eq 0 ]]; then
        echo "  警告：未找到测试文件，跳过测试"
        exit 0
    fi
    
    PASS=0
    FAIL=0
    
    for test_file in "${TEST_FILES[@]}"; do
        test_name="$(basename "${test_file%.c}")"
        test_bin="$BUILD_DIR/$test_name"
        
        echo "  运行测试: $test_name"
        
        # 查找非测试 .c 文件作为库源码
        SRC_FILES=($(find "$C_DIR" -name "*.c" -not -path "*/test*" 2>/dev/null || true))
        
        gcc -O0 -g \
            -I"$C_DIR" -I"$C_DIR/include" \
            "${SRC_FILES[@]}" "$test_file" \
            -o "$test_bin" 2>&1
        
        if "$test_bin"; then
            echo "    PASS: $test_name"
            PASS=$((PASS + 1))
        else
            echo "    FAIL: $test_name (退出码: $?)"
            FAIL=$((FAIL + 1))
        fi
    done
    
    echo ""
    echo "  结果: $PASS 通过 / $FAIL 失败"
    
    if [[ $FAIL -gt 0 ]]; then
        echo "=== 测试失败 ==="
        exit 1
    fi
fi

echo ""
echo "=== C 版本测试通过 ==="
