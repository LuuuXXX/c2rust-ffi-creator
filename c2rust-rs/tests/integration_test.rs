// tests/integration_test.rs - Integration tests mirroring the C test suite
//
// Each test here corresponds to a test in .c2rust/c/tests/test_calc.c.
// The intent is to verify that the Rust FFI layer produces identical
// results to the original C implementation.
//
// Test naming convention: test_<c_test_name> (matching C test names).

use c2rust_rs::{add, sub, mul, div, abs_val, sqrt_val, version, CalcError};

// ── version ──────────────────────────────────────────────────────────────────

#[test]
fn test_version() {
    let v = version();
    assert!(!v.is_empty(), "version string must not be empty");
}

// ── add ──────────────────────────────────────────────────────────────────────

#[test]
fn test_add_basic() {
    assert_eq!(add(2, 3), Ok(5));
}

#[test]
fn test_add_negative() {
    assert_eq!(add(-10, 4), Ok(-6));
}

#[test]
fn test_add_overflow() {
    assert_eq!(add(i32::MAX, 1), Err(CalcError::Overflow));
}

// (NULL check is tested via the C ABI export below)

// ── sub ──────────────────────────────────────────────────────────────────────

#[test]
fn test_sub_basic() {
    assert_eq!(sub(10, 3), Ok(7));
}

#[test]
fn test_sub_overflow() {
    assert_eq!(sub(i32::MIN, 1), Err(CalcError::Overflow));
}

// ── mul ──────────────────────────────────────────────────────────────────────

#[test]
fn test_mul_basic() {
    assert_eq!(mul(6, 7), Ok(42));
}

#[test]
fn test_mul_overflow() {
    assert_eq!(mul(i32::MAX, 2), Err(CalcError::Overflow));
}

// ── div ──────────────────────────────────────────────────────────────────────

#[test]
fn test_div_basic() {
    // Integer division: 10 / 3 = 3 (truncation toward zero)
    assert_eq!(div(10, 3), Ok(3));
}

#[test]
fn test_div_by_zero() {
    assert_eq!(div(5, 0), Err(CalcError::DivisionByZero));
}

// ── abs ──────────────────────────────────────────────────────────────────────

#[test]
fn test_abs_positive() {
    assert_eq!(abs_val(42), Ok(42));
}

#[test]
fn test_abs_negative() {
    assert_eq!(abs_val(-42), Ok(42));
}

#[test]
fn test_abs_zero() {
    assert_eq!(abs_val(0), Ok(0));
}

#[test]
fn test_abs_overflow() {
    // i32::MIN has no positive representation in i32
    assert_eq!(abs_val(i32::MIN), Err(CalcError::Overflow));
}

// ── sqrt ─────────────────────────────────────────────────────────────────────

#[test]
fn test_sqrt_basic() {
    let r = sqrt_val(9.0).expect("sqrt(9.0) should succeed");
    assert!((r - 3.0).abs() < 1e-10, "sqrt(9.0) ≈ 3.0, got {}", r);
}

#[test]
fn test_sqrt_zero() {
    assert_eq!(sqrt_val(0.0), Ok(0.0));
}

#[test]
fn test_sqrt_negative() {
    assert_eq!(sqrt_val(-1.0), Err(CalcError::InvalidArgument));
}

// ── C ABI NULL-pointer checks (via raw FFI) ───────────────────────────────────

#[test]
fn test_add_null_result() {
    // Safety: we are deliberately passing NULL to test error handling
    let ret = unsafe { c2rust_rs::ffi::calc_add(1, 2, std::ptr::null_mut()) };
    assert_eq!(ret, -1, "calc_add with NULL result should return CALC_ERR_INVALID");
}

#[test]
fn test_sqrt_null_result() {
    let ret = unsafe { c2rust_rs::ffi::calc_sqrt(4.0, std::ptr::null_mut()) };
    assert_eq!(ret, -1, "calc_sqrt with NULL result should return CALC_ERR_INVALID");
}

// ── Verify #[no_mangle] exports via ffi module ───────────────────────────────

#[test]
fn test_ffi_add_matches_safe() {
    let mut c_result: i32 = 0;
    let ret = unsafe { c2rust_rs::ffi::calc_add(100, 200, &mut c_result) };
    assert_eq!(ret, 0);
    assert_eq!(c_result, 300);
    assert_eq!(add(100, 200), Ok(300));
}

#[test]
fn test_ffi_div_zero_via_export() {
    let mut result: i32 = 0;
    // Safety: valid pointers, testing error path
    let ret = unsafe { c2rust_rs::ffi::calc_div(10, 0, &mut result) };
    assert_eq!(ret, -3, "should return CALC_ERR_DIV_ZERO");
}
