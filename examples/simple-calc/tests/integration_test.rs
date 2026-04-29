// Integration tests for simple-calc.
//
// These call the #[no_mangle] extern "C" functions through the rlib crate type,
// mirroring what a C caller would see at the ABI level.

use simple_calc::{calc_add, calc_sub, calc_mul};

#[test]
fn add_basic() {
    assert_eq!(calc_add(1, 2), 3);
}

#[test]
fn add_large_numbers() {
    assert_eq!(calc_add(1_000_000, 2_000_000), 3_000_000);
}

#[test]
fn add_negative() {
    assert_eq!(calc_add(-5, 3), -2);
}

#[test]
fn add_both_negative() {
    assert_eq!(calc_add(-5, -3), -8);
}

#[test]
fn add_wraps_max() {
    assert_eq!(calc_add(i32::MAX, 1), i32::MIN);
}

#[test]
fn sub_basic() {
    assert_eq!(calc_sub(10, 3), 7);
}

#[test]
fn sub_negative_result() {
    assert_eq!(calc_sub(3, 10), -7);
}

#[test]
fn sub_wraps_min() {
    assert_eq!(calc_sub(i32::MIN, 1), i32::MAX);
}

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
