// src/error.rs — Rust-idiomatic error type for the KV store.
//
// Maps the C library's `kv_status_t` integer codes to a Rust enum.

use std::fmt;

/// Errors that can be returned by [`KvStore`](crate::KvStore) operations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum KvError {
    /// The requested key was not found in the store.
    NotFound,
    /// A memory allocation inside the C library failed.
    NoMemory,
    /// A NULL or invalid argument was passed to the C library.
    InvalidArgument,
    /// Unexpected status code received from the C library.
    Unknown(i32),
}

impl fmt::Display for KvError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            KvError::NotFound        => write!(f, "key not found"),
            KvError::NoMemory        => write!(f, "out of memory"),
            KvError::InvalidArgument => write!(f, "invalid argument"),
            KvError::Unknown(code)   => write!(f, "unknown kv error code: {code}"),
        }
    }
}

impl std::error::Error for KvError {}
