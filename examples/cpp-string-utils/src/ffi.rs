// src/ffi.rs — C++ adapter for the str_counter C library using hicc.
//
// Pattern: C library with C++ adapter via hicc.
//
// hicc::cpp! embeds C++ adapter code inline in this Rust file.
// hicc-build (in build.rs) extracts these blocks and compiles them.
//
// The original C library (str_counter.c) is compiled alongside by build.rs.
// The C++ adapter functions wrap the C API using void* for the opaque handle,
// then hicc::import_lib! declares them as callable Rust functions.

use std::os::raw::{c_char, c_int};

// C++ adapter functions wrapping the C str_counter API.
// These are extracted by hicc-build and compiled as C++.
hicc::cpp! {
    extern "C" {
        #include "str_counter.h"
    }

    void* sc_new() {
        return (void*)str_counter_new();
    }

    void sc_free(void* c) {
        str_counter_free((str_counter_t*)c);
    }

    int sc_add(void* c, const char* word) {
        return str_counter_add((str_counter_t*)c, word);
    }

    size_t sc_get(const void* c, const char* word) {
        return str_counter_get((const str_counter_t*)c, word);
    }

    size_t sc_total(const void* c) {
        return str_counter_total((const str_counter_t*)c);
    }
}

// Declare the C++ adapter functions as callable Rust functions.
// link_name must match the library name used in hicc_build::Build::compile().
hicc::import_lib! {
    #![link_name = "str_counter_adapter"]

    #[cpp(func = "void* sc_new()")]
    pub fn sc_new() -> *mut std::os::raw::c_void;

    #[cpp(func = "void sc_free(void* c)")]
    pub fn sc_free(c: *mut std::os::raw::c_void);

    #[cpp(func = "int sc_add(void* c, const char* word)")]
    pub fn sc_add(
        c:    *mut std::os::raw::c_void,
        word: *const c_char,
    ) -> c_int;

    #[cpp(func = "size_t sc_get(const void* c, const char* word)")]
    pub fn sc_get(
        c:    *const std::os::raw::c_void,
        word: *const c_char,
    ) -> usize;

    #[cpp(func = "size_t sc_total(const void* c)")]
    pub fn sc_total(c: *const std::os::raw::c_void) -> usize;
}
