// tests/integration_test.rs — Rust migration of .c2rust/c/tests/test_calc.c
//
// Each test function below corresponds to a C test function in test_calc.c.
// The inputs and expected values are identical to the C test suite so that
// a passing Rust test proves the FFI wrapper is functionally equivalent to
// the original C implementation.
//
// C source: examples/simple-calc/.c2rust/c/tests/test_calc.c

use simple_calc::{calc_add, calc_sub, calc_mul};

// ── test_add ──────────────────────────────────────────────────────────────
// Mirrors: static void test_add(void) in test_calc.c

#[test]
fn add_basic() {
    assert_eq!(calc_add(1, 2), 3);
}

#[test]
fn add_large() {
    assert_eq!(calc_add(1_000_000, 2_000_000), 3_000_000);
}

#[test]
fn add_with_negative() {
    assert_eq!(calc_add(-5, 3), -2);
}

#[test]
fn add_both_negative() {
    assert_eq!(calc_add(-5, -3), -8);
}

#[test]
fn add_zeros() {
    assert_eq!(calc_add(0, 0), 0);
}

// ── test_sub ──────────────────────────────────────────────────────────────
// Mirrors: static void test_sub(void) in test_calc.c

#[test]
fn sub_basic() {
    assert_eq!(calc_sub(10, 3), 7);
}

#[test]
fn sub_negative_result() {
    assert_eq!(calc_sub(3, 10), -7);
}

#[test]
fn sub_zeros() {
    assert_eq!(calc_sub(0, 0), 0);
}

#[test]
fn sub_equal_negatives() {
    assert_eq!(calc_sub(-1, -1), 0);
}

// ── test_mul ──────────────────────────────────────────────────────────────
// Mirrors: static void test_mul(void) in test_calc.c

#[test]
fn mul_basic() {
    assert_eq!(calc_mul(4, 5), 20);
}

#[test]
fn mul_by_zero() {
    assert_eq!(calc_mul(999, 0), 0);
}

#[test]
fn mul_negative() {
    assert_eq!(calc_mul(-3, 4), -12);
}

#[test]
fn mul_both_negative() {
    assert_eq!(calc_mul(-3, -4), 12);
}
