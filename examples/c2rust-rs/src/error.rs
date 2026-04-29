// src/error.rs - Error type for the calc library
//
// Maps C error codes from calc_error_t to a Rust error type.

use std::fmt;
use std::os::raw::c_int;

/// Rust representation of calc_error_t
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum CalcError {
    /// Invalid argument: NULL pointer or out-of-range input
    /// Corresponds to CALC_ERR_INVALID (-1)
    InvalidArgument,
    /// Integer overflow
    /// Corresponds to CALC_ERR_OVERFLOW (-2)
    Overflow,
    /// Division by zero
    /// Corresponds to CALC_ERR_DIV_ZERO (-3)
    DivisionByZero,
    /// Unknown error with raw C error code
    Unknown(i32),
}

impl fmt::Display for CalcError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CalcError::InvalidArgument => write!(f, "invalid argument"),
            CalcError::Overflow => write!(f, "integer overflow"),
            CalcError::DivisionByZero => write!(f, "division by zero"),
            CalcError::Unknown(code) => write!(f, "unknown error: {}", code),
        }
    }
}

impl std::error::Error for CalcError {}

/// Convert a C return code to a Rust Result.
///
/// By convention:
/// - 0  => Ok(())
/// - <0 => Err(CalcError)
#[allow(dead_code)]
pub(crate) fn code_to_result(code: c_int) -> Result<(), CalcError> {
    match code {
        0 => Ok(()),
        -1 => Err(CalcError::InvalidArgument),
        -2 => Err(CalcError::Overflow),
        -3 => Err(CalcError::DivisionByZero),
        c => Err(CalcError::Unknown(c)),
    }
}

/// Convert a Rust CalcError back to a C error code.
/// Used in #[no_mangle] export functions.
pub(crate) fn error_to_code(err: &CalcError) -> c_int {
    match err {
        CalcError::InvalidArgument => -1,
        CalcError::Overflow => -2,
        CalcError::DivisionByZero => -3,
        CalcError::Unknown(code) => *code,
    }
}
