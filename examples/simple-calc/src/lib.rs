// src/lib.rs — Rust ABI replacement for the C calc library.
//
// Pattern: Pure Rust replacement.
//
// The original C source lives in .c2rust/c/ for reference only — it is NOT
// compiled into this crate.  Every public `#[no_mangle]` function below
// exports the exact same symbol name as the original C library, so this crate
// can be used as a drop-in replacement without relinking callers.
//
// Verify exported symbols:
//   nm -gD target/release/libsimple_calc.so | grep "T calc_"

use std::os::raw::c_int;

// ---------------------------------------------------------------------------
// C ABI exports  (#[no_mangle])
// ---------------------------------------------------------------------------

/// int32_t calc_add(int32_t a, int32_t b)
#[no_mangle]
pub extern "C" fn calc_add(a: i32, b: i32) -> c_int {
    a.wrapping_add(b)
}

/// int32_t calc_sub(int32_t a, int32_t b)
#[no_mangle]
pub extern "C" fn calc_sub(a: i32, b: i32) -> c_int {
    a.wrapping_sub(b)
}

/// int32_t calc_mul(int32_t a, int32_t b)
#[no_mangle]
pub extern "C" fn calc_mul(a: i32, b: i32) -> c_int {
    a.wrapping_mul(b)
}

// ---------------------------------------------------------------------------
// Unit tests — mirror the C test cases in .c2rust/c/tests/test_calc.c
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    // test_add
    #[test]
    fn add_basic() { assert_eq!(calc_add(1, 2), 3); }
    #[test]
    fn add_large() { assert_eq!(calc_add(1_000_000, 2_000_000), 3_000_000); }
    #[test]
    fn add_with_negative() { assert_eq!(calc_add(-5, 3), -2); }
    #[test]
    fn add_both_negative() { assert_eq!(calc_add(-5, -3), -8); }
    #[test]
    fn add_zeros() { assert_eq!(calc_add(0, 0), 0); }

    // test_sub
    #[test]
    fn sub_basic() { assert_eq!(calc_sub(10, 3), 7); }
    #[test]
    fn sub_negative_result() { assert_eq!(calc_sub(3, 10), -7); }
    #[test]
    fn sub_zeros() { assert_eq!(calc_sub(0, 0), 0); }
    #[test]
    fn sub_equal_negatives() { assert_eq!(calc_sub(-1, -1), 0); }

    // test_mul
    #[test]
    fn mul_basic() { assert_eq!(calc_mul(4, 5), 20); }
    #[test]
    fn mul_by_zero() { assert_eq!(calc_mul(999, 0), 0); }
    #[test]
    fn mul_negative() { assert_eq!(calc_mul(-3, 4), -12); }
    #[test]
    fn mul_both_negative() { assert_eq!(calc_mul(-3, -4), 12); }
}
