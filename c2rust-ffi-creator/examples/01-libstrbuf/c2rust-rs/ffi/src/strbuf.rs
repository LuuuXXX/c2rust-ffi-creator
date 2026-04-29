//! FFI 封装：strbuf 模块
//! 原 C 头文件：include/strbuf.h
//! 警告：此文件由 gen_rust_ffi.py 自动生成，并经人工审核补充了 #[repr(C)] 结构体定义与测试。

#![allow(non_camel_case_types, non_snake_case, dead_code, unused_imports)]

use std::ffi::{c_int, c_uint, c_long, c_char, c_void, c_float, c_double};

/// 对应 C 的 `strbuf_t`，内存布局与 C 端完全一致。
/// 经人工审核确认（替换了自动生成的不透明占位符）。
#[repr(C)]
pub struct StrbufT {
    /// null 终止的字符数据指针
    pub data: *mut c_char,
    /// 当前长度（字节数，不含 NUL）
    pub len: usize,
    /// 已分配容量（字节数）
    pub cap: usize,
}

mod sys {
    #[allow(unused_imports)]
    use super::*;
    extern "C" {
        #[link_name = "strbuf_init"]
        pub(super) fn __c_strbuf_init(buf: *mut StrbufT, initial_cap: usize) -> c_int;
        #[link_name = "strbuf_append"]
        pub(super) fn __c_strbuf_append(buf: *mut StrbufT, str: *const c_char) -> c_int;
        #[link_name = "strbuf_append_len"]
        pub(super) fn __c_strbuf_append_len(buf: *mut StrbufT, data: *const c_char, len: usize) -> c_int;
        #[link_name = "strbuf_reset"]
        pub(super) fn __c_strbuf_reset(buf: *mut StrbufT) -> ();
        #[link_name = "strbuf_free"]
        pub(super) fn __c_strbuf_free(buf: *mut StrbufT) -> ();
    }
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
/// 注意：`#[no_mangle]` 仅在非测试模式下生效，以避免链接时符号冲突。
#[cfg_attr(not(test), no_mangle)]
pub unsafe extern "C" fn strbuf_init(buf: *mut StrbufT, initial_cap: usize) -> c_int {
    sys::__c_strbuf_init(buf, initial_cap)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
/// 注意：`#[no_mangle]` 仅在非测试模式下生效，以避免链接时符号冲突。
#[cfg_attr(not(test), no_mangle)]
pub unsafe extern "C" fn strbuf_append(buf: *mut StrbufT, str: *const c_char) -> c_int {
    sys::__c_strbuf_append(buf, str)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
/// 注意：`#[no_mangle]` 仅在非测试模式下生效，以避免链接时符号冲突。
#[cfg_attr(not(test), no_mangle)]
pub unsafe extern "C" fn strbuf_append_len(
    buf: *mut StrbufT,
    data: *const c_char,
    len: usize,
) -> c_int {
    sys::__c_strbuf_append_len(buf, data, len)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
/// 注意：`#[no_mangle]` 仅在非测试模式下生效，以避免链接时符号冲突。
#[cfg_attr(not(test), no_mangle)]
pub unsafe extern "C" fn strbuf_reset(buf: *mut StrbufT) {
    sys::__c_strbuf_reset(buf)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
/// 注意：`#[no_mangle]` 仅在非测试模式下生效，以避免链接时符号冲突。
#[cfg_attr(not(test), no_mangle)]
pub unsafe extern "C" fn strbuf_free(buf: *mut StrbufT) {
    sys::__c_strbuf_free(buf)
}

// ── Rust 测试（对应 C 测试文件 tests/test_strbuf.c）─────────────────────────
#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::{CStr, CString};

    /// 创建一个零初始化的 StrbufT，供 strbuf_init 填充。
    fn make_buf() -> StrbufT {
        // Safety: StrbufT 是 C struct，strbuf_init 调用前零值合法。
        unsafe { std::mem::zeroed() }
    }

    // 对应 C 测试 test_strbuf_init_success
    #[test]
    fn test_strbuf_init_success() {
        let mut buf = make_buf();
        let ret = unsafe { strbuf_init(&mut buf, 16) };
        assert_eq!(ret, 0);
        assert_eq!(buf.len, 0);
        assert_eq!(buf.cap, 16);
        unsafe { strbuf_free(&mut buf) };
    }

    // 对应 C 测试 test_strbuf_append
    #[test]
    fn test_strbuf_append() {
        let mut buf = make_buf();
        unsafe {
            strbuf_init(&mut buf, 8);
            let hello = CString::new("hello").unwrap();
            let ret = strbuf_append(&mut buf, hello.as_ptr());
            assert_eq!(ret, 0);
            assert_eq!(buf.len, 5);
            let s = CStr::from_ptr(buf.data).to_str().unwrap();
            assert_eq!(s, "hello");
            strbuf_free(&mut buf);
        }
    }

    // 对应 C 测试 test_strbuf_append_grows
    #[test]
    fn test_strbuf_append_grows() {
        let mut buf = make_buf();
        unsafe {
            strbuf_init(&mut buf, 4);
            let s = CString::new("hello world").unwrap();
            let ret = strbuf_append(&mut buf, s.as_ptr());
            assert_eq!(ret, 0);
            assert_eq!(buf.len, 11);
            strbuf_free(&mut buf);
        }
    }

    // 对应 C 测试 test_strbuf_reset
    #[test]
    fn test_strbuf_reset() {
        let mut buf = make_buf();
        unsafe {
            strbuf_init(&mut buf, 16);
            let hi = CString::new("hi").unwrap();
            strbuf_append(&mut buf, hi.as_ptr());
            strbuf_reset(&mut buf);
            assert_eq!(buf.len, 0);
            assert_eq!(*buf.data, 0); // data should be NUL after reset
            strbuf_free(&mut buf);
        }
    }
}
