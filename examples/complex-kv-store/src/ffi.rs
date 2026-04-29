// src/ffi.rs — C++ adapter for the kv_store C library using hicc.
//
// Pattern: C library with C++ adapter via hicc.
//
// hicc::cpp! embeds C++ adapter code inline in this Rust file.
// hicc-build (in build.rs) extracts these blocks and compiles them as C++.
//
// The original C library (kv.c) is compiled with the C compiler in build.rs.
// The C++ adapter functions bridge the opaque `kv_store_t*` type using void*,
// then hicc::import_lib! declares them as callable Rust functions.

use std::os::raw::{c_char, c_int};

// C++ adapter functions wrapping the C kv_store API.
// These are extracted by hicc-build and compiled as C++.
hicc::cpp! {
    extern "C" {
        #include "kv.h"
    }

    // Opaque handle is passed as void* so the Rust side does not need kv_store_t.

    void* kv_new_adapter(size_t initial_capacity) {
        return (void*)kv_new(initial_capacity);
    }

    void kv_destroy_adapter(void* store) {
        kv_destroy((kv_store_t*)store);
    }

    int kv_set_adapter(void* store, const char* key, const char* value) {
        return (int)kv_set((kv_store_t*)store, key, value);
    }

    const char* kv_get_adapter(const void* store, const char* key) {
        return kv_get((const kv_store_t*)store, key);
    }

    int kv_delete_adapter(void* store, const char* key) {
        return (int)kv_delete((kv_store_t*)store, key);
    }

    size_t kv_count_adapter(const void* store) {
        return kv_count((const kv_store_t*)store);
    }
}

// Declare the C++ adapter functions as callable Rust functions.
// link_name must match the library name used in hicc_build::Build::compile().
hicc::import_lib! {
    #![link_name = "kv_adapter"]

    #[cpp(func = "void* kv_new_adapter(size_t initial_capacity)")]
    pub fn kv_new_adapter(initial_capacity: usize) -> *mut std::os::raw::c_void;

    #[cpp(func = "void kv_destroy_adapter(void* store)")]
    pub fn kv_destroy_adapter(store: *mut std::os::raw::c_void);

    #[cpp(func = "int kv_set_adapter(void* store, const char* key, const char* value)")]
    pub fn kv_set_adapter(
        store: *mut std::os::raw::c_void,
        key:   *const c_char,
        value: *const c_char,
    ) -> c_int;

    #[cpp(func = "const char* kv_get_adapter(const void* store, const char* key)")]
    pub fn kv_get_adapter(
        store: *const std::os::raw::c_void,
        key:   *const c_char,
    ) -> *const c_char;

    #[cpp(func = "int kv_delete_adapter(void* store, const char* key)")]
    pub fn kv_delete_adapter(
        store: *mut std::os::raw::c_void,
        key:   *const c_char,
    ) -> c_int;

    #[cpp(func = "size_t kv_count_adapter(const void* store)")]
    pub fn kv_count_adapter(store: *const std::os::raw::c_void) -> usize;
}

// Status code constants matching kv_status_t in kv.h
pub const KV_OK: c_int            =  0;
pub const KV_ERR_NOT_FOUND: c_int = -1;
pub const KV_ERR_NO_MEMORY: c_int = -2;
pub const KV_ERR_INVALID: c_int   = -3;
