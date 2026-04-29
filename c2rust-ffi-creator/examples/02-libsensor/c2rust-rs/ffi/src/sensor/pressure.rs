//! FFI 封装：pressure 模块
//! 原 C 头文件：include/sensor/pressure.h
//! 生成时间：2026-04-29T07:39:17Z
//! 警告：此文件由 gen_rust_ffi.py 自动生成，请在人工审核后修改。

#![allow(non_camel_case_types, non_snake_case, dead_code)]

use std::ffi::{c_int, c_uint, c_long, c_char, c_void, c_float, c_double};

extern "C" {
    fn pressure_sensor_init(addr: u8) -> c_int;
    fn pressure_sensor_read(addr: u8, out: *mut PressureReadingT) -> c_int;
    fn pressure_sensor_shutdown(addr: u8) -> ();
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
#[no_mangle]
pub unsafe extern "C" fn pressure_sensor_init(addr: u8) -> c_int {
    pressure_sensor_init(addr)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
#[no_mangle]
pub unsafe extern "C" fn pressure_sensor_read(addr: u8, out: *mut PressureReadingT) -> c_int {
    pressure_sensor_read(addr, out)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
#[no_mangle]
pub unsafe extern "C" fn pressure_sensor_shutdown(addr: u8) -> () {
    pressure_sensor_shutdown(addr)
}
