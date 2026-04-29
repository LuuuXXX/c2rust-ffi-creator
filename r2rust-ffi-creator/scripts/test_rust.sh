#!/usr/bin/env bash
# test_rust.sh - 运行 Rust FFI 版本测试
# 用法: test_rust.sh [c2rust-rs 路径]

set -euo pipefail

PROJECT_DIR="$(realpath "${1:-.}")"

echo "=== 运行 Rust 版本测试 ==="
echo "  项目目录: $PROJECT_DIR"
echo ""

cd "$PROJECT_DIR"

if [[ ! -f "Cargo.toml" ]]; then
    echo "错误: 未找到 Cargo.toml"
    exit 1
fi

cargo test -- --test-output immediate 2>&1

echo ""
echo "=== Rust 版本测试通过 ==="
