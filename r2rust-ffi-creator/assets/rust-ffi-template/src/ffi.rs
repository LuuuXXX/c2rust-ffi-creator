// src/ffi.rs - C 函数的 extern "C" 声明
//
// 此文件可以是：
//   (a) 由 bindgen 自动生成（推荐）：通过 build.rs 中的 include!() 宏引入
//   (b) 手动编写：直接在此声明 extern "C" 函数
//
// 当使用 bindgen 自动生成时，取消注释下面的 include!() 行，
// 并删除手动声明部分。

// === 方案 A：bindgen 自动生成（推荐）===
// 取消注释以使用 bindgen 生成的绑定：
//
// #![allow(non_upper_case_globals)]
// #![allow(non_camel_case_types)]
// #![allow(non_snake_case)]
// #![allow(dead_code)]
// include!(concat!(env!("OUT_DIR"), "/bindings.rs"));

// === 方案 B：手动声明（小型项目适用）===
// 当函数较少时，手动声明更简洁。
//
// 根据 .c2rust/c/INTERFACES.md 中记录的函数签名逐一填写：

use std::os::raw::{c_int, c_uint, c_char, c_void, c_double};

// TODO: 将以下声明替换为实际 C 函数签名
// 参考 .c2rust/c/INTERFACES.md 和 references/type_mapping.md

extern "C" {
    // 示例函数声明（请替换为实际函数）
    // pub fn mylib_init() -> c_int;
    // pub fn mylib_cleanup();
    // pub fn mylib_get_version() -> *const c_char;
    // pub fn mylib_process(input: *const c_char, output: *mut c_char, len: c_uint) -> c_int;
}

// 如果 C 库定义了常量，在此声明对应的 Rust 常量
// pub const MYLIB_VERSION_MAJOR: u32 = 1;
// pub const MYLIB_VERSION_MINOR: u32 = 0;
// pub const MYLIB_OK: i32 = 0;
// pub const MYLIB_ERR_INVALID: i32 = -1;
// pub const MYLIB_ERR_NOMEM: i32 = -2;
