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
// Unit tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn add_two_positives() {
        assert_eq!(calc_add(2, 3), 5);
    }
    #[test]
    fn add_with_negative() {
        assert_eq!(calc_add(-4, 1), -3);
    }
    #[test]
    fn add_wraps_on_overflow() {
        assert_eq!(calc_add(i32::MAX, 1), i32::MIN);
    }
    #[test]
    fn sub_basic() {
        assert_eq!(calc_sub(10, 4), 6);
    }
    #[test]
    fn sub_negative_result() {
        assert_eq!(calc_sub(3, 10), -7);
    }
    #[test]
    fn mul_basic() {
        assert_eq!(calc_mul(3, 7), 21);
    }
    #[test]
    fn mul_by_zero() {
        assert_eq!(calc_mul(999, 0), 0);
    }
    #[test]
    fn mul_negative() {
        assert_eq!(calc_mul(-3, 4), -12);
    }
}
