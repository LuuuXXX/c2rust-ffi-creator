#!/usr/bin/env bash
# build_rust.sh - 构建 Rust FFI 版本
# 用法: build_rust.sh [c2rust-rs 路径]

set -euo pipefail

PROJECT_DIR="$(realpath "${1:-.}")"

echo "=== 构建 Rust FFI 版本 ==="
echo "  项目目录: $PROJECT_DIR"
echo ""

cd "$PROJECT_DIR"

# 检查 Cargo.toml
if [[ ! -f "Cargo.toml" ]]; then
    echo "错误: 未找到 Cargo.toml，请确认在正确的目录下运行"
    exit 1
fi

# 检查 bindgen 依赖（build dependencies）
if grep -q "bindgen" Cargo.toml; then
    echo "[前置检查] 检测到 bindgen，验证 libclang..."
    if ! pkg-config --exists libclang 2>/dev/null && ! which llvm-config > /dev/null 2>&1; then
        echo "  警告: 未找到 libclang，bindgen 可能失败"
        echo "  Ubuntu/Debian: sudo apt install libclang-dev"
        echo "  macOS: brew install llvm"
        echo "  继续尝试构建..."
    else
        echo "  libclang 已安装 ✓"
    fi
fi

echo "[1/2] 构建 Release 版本..."
cargo build --release 2>&1

echo ""
echo "[2/2] 验证构建产物..."
RELEASE_DIR="$PROJECT_DIR/target/release"
SO_FILES=($(find "$RELEASE_DIR" -maxdepth 1 \( -name "*.so" -o -name "*.dylib" -o -name "*.a" \) 2>/dev/null || true))

if [[ ${#SO_FILES[@]} -eq 0 ]]; then
    echo "  警告: 未找到库文件，请检查 Cargo.toml 中 [lib] crate-type 配置"
    echo "  需要包含 cdylib 或 staticlib"
    exit 1
fi

for f in "${SO_FILES[@]}"; do
    SIZE=$(du -h "$f" | cut -f1)
    echo "  ✓ $(basename "$f") ($SIZE)"
done

echo ""
echo "=== Rust FFI 构建成功 ==="
echo ""
echo "下一步: 运行 verify_symbols.sh 验证符号一致性"
