//! FFI 封装：i2c 模块
//! 原 C 头文件：include/platform/linux/i2c.h
//! 生成时间：2026-04-29T08:01:08Z
//! 警告：此文件由 gen_rust_ffi.py 自动生成，请在人工审核后修改。

#![allow(non_camel_case_types, non_snake_case, dead_code, unused_imports)]

use std::ffi::{c_int, c_uint, c_long, c_char, c_void, c_float, c_double};

mod sys {
    #[allow(unused_imports)]
    use super::*;
    extern "C" {
        #[link_name = "i2c_open"]
        pub(super) fn __c_i2c_open(bus_path: *const c_char) -> c_int;
        #[link_name = "i2c_close"]
        pub(super) fn __c_i2c_close(fd: c_int) -> ();
        #[link_name = "i2c_write"]
        pub(super) fn __c_i2c_write(fd: c_int, addr: u8, data: *const u8, len: usize) -> c_int;
        #[link_name = "i2c_read"]
        pub(super) fn __c_i2c_read(fd: c_int, addr: u8, buf: *mut u8, len: usize) -> c_int;
    }
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
/// 注意：`#[no_mangle]` 仅在非测试模式下生效，以避免链接时符号冲突。
#[cfg_attr(not(test), no_mangle)]
pub unsafe extern "C" fn i2c_open(bus_path: *const c_char) -> c_int {
    sys::__c_i2c_open(bus_path)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
/// 注意：`#[no_mangle]` 仅在非测试模式下生效，以避免链接时符号冲突。
#[cfg_attr(not(test), no_mangle)]
pub unsafe extern "C" fn i2c_close(fd: c_int) -> () {
    sys::__c_i2c_close(fd)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
/// 注意：`#[no_mangle]` 仅在非测试模式下生效，以避免链接时符号冲突。
#[cfg_attr(not(test), no_mangle)]
pub unsafe extern "C" fn i2c_write(fd: c_int, addr: u8, data: *const u8, len: usize) -> c_int {
    sys::__c_i2c_write(fd, addr, data, len)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
/// 注意：`#[no_mangle]` 仅在非测试模式下生效，以避免链接时符号冲突。
#[cfg_attr(not(test), no_mangle)]
pub unsafe extern "C" fn i2c_read(fd: c_int, addr: u8, buf: *mut u8, len: usize) -> c_int {
    sys::__c_i2c_read(fd, addr, buf, len)
}
