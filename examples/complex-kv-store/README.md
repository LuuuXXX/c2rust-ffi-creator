# complex-kv-store

**Pattern: C→Rust safe wrapper (with cc + bindgen, RAII, error handling)**

A realistic FFI migration example: a C key-value store library with dynamic
memory allocation, error codes, and an opaque handle pattern is wrapped by a
safe Rust API.

## Original C API (`.c2rust/c/include/kv.h`)

```c
typedef enum kv_status { KV_OK=0, KV_ERR_NOT_FOUND=-1,
                          KV_ERR_NO_MEMORY=-2, KV_ERR_INVALID=-3 } kv_status_t;
typedef struct kv_store kv_store_t;   /* opaque handle */

kv_store_t *kv_new(size_t initial_capacity);
void        kv_destroy(kv_store_t *store);
kv_status_t kv_set(kv_store_t *store, const char *key, const char *value);
const char *kv_get(const kv_store_t *store, const char *key);
kv_status_t kv_delete(kv_store_t *store, const char *key);
size_t      kv_count(const kv_store_t *store);
```

## What this example shows

- **`build.rs`**: compiles C via `cc` crate and generates bindings with
  `bindgen` — the full automated FFI pipeline.
- **Safe `KvStore` struct**: a RAII wrapper with `Drop` that automatically
  calls `kv_destroy`; no manual memory management in Rust callers.
- **`KvError` enum**: Rust-idiomatic error type mapped from C status codes.
- **Memory safety**: `CString` / `CStr` handle null-termination at the FFI
  boundary; `get()` returns an owned `String` to avoid C-lifetime issues.
- **C tests independent of Rust**: the C test suite in `.c2rust/c/tests/` can
  be compiled and run with CMake to baseline the C implementation.

## Project layout

```
complex-kv-store/
├── Cargo.toml
├── build.rs                  ← cc (compile C) + bindgen (generate types)
├── .c2rust/c/
│   ├── CMakeLists.txt        ← C-only build (for reference/CI C tests)
│   ├── include/kv.h          ← public API header
│   ├── src/kv.c              ← C implementation
│   └── tests/test_kv.c       ← standalone C tests
├── src/
│   ├── lib.rs                ← KvStore RAII wrapper + public API
│   └── error.rs              ← KvError type
└── tests/
    └── integration_test.rs   ← Rust integration tests
```

## Build & test

```bash
# Rust build + tests (compiles C automatically via build.rs)
cargo build --release
cargo test

# C-only build and test (CMake)
cmake -B .c2rust/c/_build -S .c2rust/c -DCMAKE_BUILD_TYPE=Release
cmake --build .c2rust/c/_build
.c2rust/c/_build/test_kv
```
