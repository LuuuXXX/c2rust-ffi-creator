#!/usr/bin/env bash
# scripts/build_and_test.sh - Build and test both C and Rust versions
#
# This script is the main entry point for the full build+test+verify pipeline.
# Run from the c2rust-rs/ directory.
#
# Usage: ./scripts/build_and_test.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_SCRIPTS="$PROJECT_DIR/../r2rust-ffi-creator/scripts"

cd "$PROJECT_DIR"

echo "========================================"
echo " c2rust-rs: Full Build & Test Pipeline"
echo "========================================"
echo ""
echo " Project: $PROJECT_DIR"
echo ""

# ── Step 1: Build C version ──────────────────────────────────────────────────
echo "[1/5] Building C version..."
echo "----------------------------------------"
C_DIR=".c2rust/c"
BUILD_DIR="$C_DIR/_build"

mkdir -p "$BUILD_DIR"

if [[ -f "$C_DIR/CMakeLists.txt" ]]; then
    cmake -B "$BUILD_DIR" -S "$C_DIR" -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_VERBOSE_MAKEFILE=OFF -Wno-dev 2>&1 | tail -5
    cmake --build "$BUILD_DIR" 2>&1 | tail -5
else
    echo "  Warning: No CMakeLists.txt found, trying direct gcc compile..."
    gcc -shared -fPIC -O2 \
        -I"$C_DIR/include" \
        "$C_DIR/src/calc.c" \
        -lm \
        -o "$BUILD_DIR/libcalc.so"
fi

echo "  ✓ C version built"
echo ""

# ── Step 2: Run C tests ──────────────────────────────────────────────────────
echo "[2/5] Running C tests..."
echo "----------------------------------------"

if [[ -f "$BUILD_DIR/test_calc" ]]; then
    "$BUILD_DIR/test_calc"
elif command -v ctest &> /dev/null; then
    ctest --test-dir "$BUILD_DIR" --output-on-failure
else
    # Compile and run test directly
    gcc -O0 -g \
        -I"$C_DIR/include" \
        "$C_DIR/src/calc.c" \
        "$C_DIR/tests/test_calc.c" \
        -lm \
        -o "$BUILD_DIR/test_calc"
    "$BUILD_DIR/test_calc"
fi

echo "  ✓ C tests passed"
echo ""

# ── Step 3: Build Rust version ───────────────────────────────────────────────
echo "[3/5] Building Rust FFI version..."
echo "----------------------------------------"
cargo build --release 2>&1 | tail -10
echo "  ✓ Rust version built"
echo ""

# ── Step 4: Run Rust tests ───────────────────────────────────────────────────
echo "[4/5] Running Rust tests..."
echo "----------------------------------------"
cargo test 2>&1
echo "  ✓ Rust tests passed"
echo ""

# ── Step 5: Verify symbol consistency ────────────────────────────────────────
echo "[5/5] Verifying symbol consistency..."
echo "----------------------------------------"

# Find C library
C_LIB="$(find "$BUILD_DIR" -name "libcalc.so" -o -name "libcalc.dylib" 2>/dev/null | head -1)"
if [[ -z "$C_LIB" ]]; then
    C_LIB="$(find "$BUILD_DIR" -name "libcalc.a" 2>/dev/null | head -1)"
fi

# Find Rust library
RUST_LIB="$(find target/release -maxdepth 1 -name "libc2rust_rs.so" -o -name "libc2rust_rs.dylib" 2>/dev/null | head -1)"
if [[ -z "$RUST_LIB" ]]; then
    RUST_LIB="$(find target/release -maxdepth 1 -name "libc2rust_rs.a" 2>/dev/null | head -1)"
fi

if [[ -z "$C_LIB" || -z "$RUST_LIB" ]]; then
    echo "  Warning: Could not find library files for symbol comparison"
    echo "  C lib:    ${C_LIB:-NOT FOUND}"
    echo "  Rust lib: ${RUST_LIB:-NOT FOUND}"
else
    echo "  C lib:    $C_LIB"
    echo "  Rust lib: $RUST_LIB"
    echo ""

    # Extract symbols
    extract_symbols() {
        local lib="$1"
        nm -g --defined-only "$lib" 2>/dev/null \
            | grep " T \| W " \
            | awk '{print $3}' \
            | grep -v "^_" \
            | sort
    }

    C_SYMS="$(extract_symbols "$C_LIB")"
    RUST_SYMS="$(extract_symbols "$RUST_LIB")"

    MISSING="$(comm -23 <(echo "$C_SYMS") <(echo "$RUST_SYMS") || true)"

    if [[ -z "$MISSING" ]]; then
        echo "  ✓ All C exported symbols present in Rust version"
        echo ""
        echo "  Exported symbols:"
        echo "$C_SYMS" | sed 's/^/    /'
    else
        echo "  ✗ Missing symbols in Rust version:"
        echo "$MISSING" | sed 's/^/    - /'
        echo ""
        echo "  Fix: Add #[no_mangle] pub extern \"C\" fn <symbol> in src/lib.rs"
        exit 1
    fi
fi

echo ""
echo "========================================"
echo " All checks passed! ✓"
echo "========================================"
