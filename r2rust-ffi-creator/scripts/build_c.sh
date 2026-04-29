#!/usr/bin/env bash
# build_c.sh - 构建 C 版本库
# 用法: build_c.sh <.c2rust/c 路径>
# 示例: build_c.sh .c2rust/c

set -euo pipefail

usage() {
    echo "用法: $0 <.c2rust/c 路径>"
    exit 1
}

[[ $# -lt 1 ]] && usage

C_DIR="$(realpath "$1")"
BUILD_DIR="$C_DIR/_build"

if [[ ! -d "$C_DIR" ]]; then
    echo "错误: 路径不存在: $C_DIR"
    exit 1
fi

echo "=== 构建 C 版本 ==="
echo "  目录: $C_DIR"
echo "  构建目录: $BUILD_DIR"
echo ""

mkdir -p "$BUILD_DIR"

if [[ -f "$C_DIR/CMakeLists.txt" ]]; then
    echo "[CMake 构建]"
    cmake -B "$BUILD_DIR" -S "$C_DIR" -DCMAKE_BUILD_TYPE=Release
    cmake --build "$BUILD_DIR"
elif [[ -f "$C_DIR/Makefile" ]]; then
    echo "[Make 构建]"
    make -C "$C_DIR" BUILD_DIR="$BUILD_DIR"
else
    # 回退：直接用 gcc 编译所有 .c 文件为动态库
    echo "[回退构建：直接 gcc 编译]"
    LIB_NAME="$(basename "$C_DIR/../..")"
    C_FILES=($(find "$C_DIR" -name "*.c" -not -path "*/tests/*" -not -path "*/test/*"))
    
    if [[ ${#C_FILES[@]} -eq 0 ]]; then
        echo "错误: 未找到 C 源文件"
        exit 1
    fi
    
    echo "  编译文件: ${C_FILES[*]}"
    
    # 编译动态库
    gcc -shared -fPIC -O2 -Wall \
        -I"$C_DIR" -I"$C_DIR/include" \
        "${C_FILES[@]}" \
        -o "$BUILD_DIR/lib${LIB_NAME}.so" 2>&1
    
    # 编译静态库
    gcc -c -O2 -Wall \
        -I"$C_DIR" -I"$C_DIR/include" \
        "${C_FILES[@]}"
    OBJ_FILES=($(ls ./*.o 2>/dev/null || true))
    if [[ ${#OBJ_FILES[@]} -gt 0 ]]; then
        ar rcs "$BUILD_DIR/lib${LIB_NAME}.a" "${OBJ_FILES[@]}"
        rm -f "${OBJ_FILES[@]}"
    fi
    
    echo ""
    echo "  构建产物: $BUILD_DIR/"
    ls -la "$BUILD_DIR/"
fi

echo ""
echo "=== 构建成功 ==="
echo ""
echo "下一步: 运行 test_c.sh $C_DIR 验证 C 版本测试"
