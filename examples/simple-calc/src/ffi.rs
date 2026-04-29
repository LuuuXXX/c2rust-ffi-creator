// src/ffi.rs — C++ adapter for the calc C library using hicc.
//
// Pattern: C library wrapped via hicc C++ adapter.
//
// hicc::cpp! embeds C++ adapter code inline in this file.
// hicc-build (in build.rs) extracts these blocks and compiles them as C++.
// The original C library (calc.c) is compiled by build.rs with the C compiler.
//
// The C++ adapter functions delegate to the original C functions, then
// hicc::import_lib! declares them as callable Rust functions.

use std::os::raw::c_int;

// C++ adapter — delegates to the original C calc functions.
// These blocks are extracted by hicc-build and compiled as C++.
hicc::cpp! {
    extern "C" {
        #include "calc.h"
    }

    int calc_add_adapter(int a, int b) {
        return calc_add(a, b);
    }

    int calc_sub_adapter(int a, int b) {
        return calc_sub(a, b);
    }

    int calc_mul_adapter(int a, int b) {
        return calc_mul(a, b);
    }
}

// Declare the C++ adapter functions as callable Rust functions.
// link_name must match the library name used in hicc_build::Build::compile().
hicc::import_lib! {
    #![link_name = "calc_adapter"]

    #[cpp(func = "int calc_add_adapter(int a, int b)")]
    pub fn calc_add_adapter(a: c_int, b: c_int) -> c_int;

    #[cpp(func = "int calc_sub_adapter(int a, int b)")]
    pub fn calc_sub_adapter(a: c_int, b: c_int) -> c_int;

    #[cpp(func = "int calc_mul_adapter(int a, int b)")]
    pub fn calc_mul_adapter(a: c_int, b: c_int) -> c_int;
}
