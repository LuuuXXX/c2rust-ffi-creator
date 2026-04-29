//! FFI 封装：strbuf 模块
//! 原 C 头文件：include/strbuf.h
//! 生成时间：2026-04-29T07:39:17Z
//! 警告：此文件由 gen_rust_ffi.py 自动生成，请在人工审核后修改。

#![allow(non_camel_case_types, non_snake_case, dead_code)]

use std::ffi::{c_int, c_uint, c_long, c_char, c_void, c_float, c_double};

extern "C" {
    fn strbuf_init(buf: *mut StrbufT, initial_cap: usize) -> c_int;
    fn strbuf_append(buf: *mut StrbufT, str: *const c_char) -> c_int;
    fn strbuf_append_len(buf: *mut StrbufT, data: *const c_char, len: usize) -> c_int;
    fn strbuf_reset(buf: *mut StrbufT) -> ();
    fn strbuf_free(buf: *mut StrbufT) -> ();
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
#[no_mangle]
pub unsafe extern "C" fn strbuf_init(buf: *mut StrbufT, initial_cap: usize) -> c_int {
    strbuf_init(buf, initial_cap)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
#[no_mangle]
pub unsafe extern "C" fn strbuf_append(buf: *mut StrbufT, str: *const c_char) -> c_int {
    strbuf_append(buf, str)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
#[no_mangle]
pub unsafe extern "C" fn strbuf_append_len(buf: *mut StrbufT, data: *const c_char, len: usize) -> c_int {
    strbuf_append_len(buf, data, len)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
#[no_mangle]
pub unsafe extern "C" fn strbuf_reset(buf: *mut StrbufT) -> () {
    strbuf_reset(buf)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
#[no_mangle]
pub unsafe extern "C" fn strbuf_free(buf: *mut StrbufT) -> () {
    strbuf_free(buf)
}
