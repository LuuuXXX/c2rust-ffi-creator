# simple-calc

**Pattern: C→Rust ABI replacement (minimal)**

The simplest possible FFI migration: a C library that provides 3 arithmetic
functions is replaced by a Rust crate that exports the exact same symbols.

## Original C API (`.c2rust/c/`)

```c
int32_t calc_add(int32_t a, int32_t b);
int32_t calc_sub(int32_t a, int32_t b);
int32_t calc_mul(int32_t a, int32_t b);
```

## What this example shows

- **No build.rs needed**: the C code is not compiled into the Rust binary.
- **Pure Rust implementation**: all logic lives in `src/lib.rs`.
- **ABI compatibility**: `#[no_mangle] pub extern "C"` exports preserve the
  original C symbol names so drop-in replacement works without relinking.
- **Symbol verification**: `nm -gD target/release/libsimple_calc.so` confirms
  `calc_add`, `calc_sub`, and `calc_mul` are exported.

## Build & test

```bash
cargo build --release
cargo test
nm -gD target/release/libsimple_calc.so | grep "^[0-9a-f]* T calc_"
```
