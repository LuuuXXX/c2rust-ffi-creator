// src/lib.rs — Safe Rust wrapper for the C calc library via hicc.
//
// Pattern: C library compiled in via hicc (C++ adapter layer).
//
// build.rs uses:
//   - cc::Build to compile calc.c with the C compiler
//   - hicc_build::Build to compile the C++ adapter extracted from src/ffi.rs
//
// hicc::import_lib! in src/ffi.rs declares safe Rust functions that call
// through the C++ adapter into the original C implementation.

mod ffi;

use std::os::raw::c_int;

/// int32_t calc_add(int32_t a, int32_t b) — add two integers.
pub fn calc_add(a: i32, b: i32) -> i32 {
    ffi::calc_add_adapter(a as c_int, b as c_int) as i32
}

/// int32_t calc_sub(int32_t a, int32_t b) — subtract b from a.
pub fn calc_sub(a: i32, b: i32) -> i32 {
    ffi::calc_sub_adapter(a as c_int, b as c_int) as i32
}

/// int32_t calc_mul(int32_t a, int32_t b) — multiply two integers.
pub fn calc_mul(a: i32, b: i32) -> i32 {
    ffi::calc_mul_adapter(a as c_int, b as c_int) as i32
}

