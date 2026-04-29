// src/error.rs - C 错误码到 Rust 错误类型的转换
//
// 根据 .c2rust/c/INTERFACES.md 中记录的错误码填写此文件。

use std::fmt;
use std::os::raw::c_int;

/// Rust 版本的错误类型，对应 C 库的错误码
#[derive(Debug, Clone, PartialEq)]
pub enum Error {
    /// 无效参数（对应 C 中的 -EINVAL 或类似）
    InvalidArgument,
    /// 内存不足（对应 C 中的 -ENOMEM 或类似）
    OutOfMemory,
    /// 未知错误（带原始错误码）
    Unknown(i32),
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::InvalidArgument => write!(f, "无效参数"),
            Error::OutOfMemory => write!(f, "内存不足"),
            Error::Unknown(code) => write!(f, "未知错误: {}", code),
        }
    }
}

impl std::error::Error for Error {}

/// 将 C 函数返回的整数错误码转换为 Rust Result
///
/// # 约定
/// - 0 表示成功
/// - 负数表示错误
/// - 正数表示成功（可能带有附加信息）
pub fn c_result_to_rust(code: c_int) -> Result<c_int, Error> {
    // TODO: 根据实际 C 库的错误码映射调整
    match code {
        c if c >= 0 => Ok(c),
        -1 => Err(Error::InvalidArgument),   // TODO: 替换为实际错误码
        -2 => Err(Error::OutOfMemory),        // TODO: 替换为实际错误码
        c => Err(Error::Unknown(c)),
    }
}

/// 将 Rust 错误转换为 C 错误码（用于 #[no_mangle] 导出函数）
pub fn rust_error_to_c(err: &Error) -> c_int {
    match err {
        Error::InvalidArgument => -1,   // TODO: 替换为实际错误码
        Error::OutOfMemory => -2,        // TODO: 替换为实际错误码
        Error::Unknown(code) => *code,
    }
}
