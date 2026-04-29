# c2rust-rs

Rust FFI wrapper for the `calc` C library, demonstrating the **r2rust-ffi-creator** workflow.

## What this is

This project was created using the `r2rust-ffi-creator` SKILL. It provides:

1. **A copy of the original C library** in `.c2rust/c/` (with analysis documents)
2. **Rust FFI bindings** that exactly mirror the C library's exported symbols
3. **Integration tests** covering the same cases as the C test suite
4. **Build and verification scripts** in `scripts/`

## Quick Start

### Prerequisites

```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install build tools (Ubuntu/Debian)
sudo apt install cmake gcc libclang-dev

# macOS
xcode-select --install
brew install llvm
```

### Build and test everything

```bash
cd c2rust-rs
./scripts/build_and_test.sh
```

This script:
1. Builds the C version (`cmake` + `make`)
2. Runs C tests
3. Builds the Rust FFI version (`cargo build --release`)
4. Runs Rust tests (`cargo test`)
5. Verifies exported symbols match between C and Rust

### Individual commands

```bash
# Build Rust only
cargo build --release

# Run Rust tests
cargo test

# Run C tests only
cmake -B .c2rust/c/_build -S .c2rust/c && cmake --build .c2rust/c/_build
.c2rust/c/_build/test_calc
```

## Project Structure

```
c2rust-rs/
├── Cargo.toml              # Rust crate (cdylib + staticlib)
├── build.rs                # bindgen: generates src/ffi bindings from calc.h
├── src/
│   ├── lib.rs              # Public API + #[no_mangle] C ABI exports
│   ├── ffi.rs              # Raw extern "C" declarations (bindgen output)
│   └── error.rs            # CalcError type mapping C error codes
├── tests/
│   └── integration_test.rs # Mirrors .c2rust/c/tests/test_calc.c
├── scripts/
│   └── build_and_test.sh   # Full pipeline: build C + Rust, run tests, verify symbols
└── .c2rust/
    └── c/
        ├── include/calc.h  # Original C API header
        ├── src/calc.c      # Original C implementation
        ├── tests/          # Original C tests
        ├── CMakeLists.txt  # C build system
        ├── PROJECT_SPEC.md # Project specification
        ├── MODULE_DEPS.md  # Module dependency analysis
        ├── INTERFACES.md   # Northbound/Southbound interface specs
        ├── BUILD_PLAN.md   # Build instructions
        └── TEST_PLAN.md    # Test plan and expected output
```

## Exported Symbols

The following symbols are exported by both the C and Rust versions:

| Symbol | Signature |
|--------|-----------|
| `calc_version` | `const char *calc_version(void)` |
| `calc_add` | `int calc_add(int32_t, int32_t, int32_t *)` |
| `calc_sub` | `int calc_sub(int32_t, int32_t, int32_t *)` |
| `calc_mul` | `int calc_mul(int32_t, int32_t, int32_t *)` |
| `calc_div` | `int calc_div(int32_t, int32_t, int32_t *)` |
| `calc_abs` | `int calc_abs(int32_t, int32_t *)` |
| `calc_sqrt` | `int calc_sqrt(double, double *)` |

## Troubleshooting

See `../r2rust-ffi-creator/references/troubleshooting.md` for common issues and solutions.
