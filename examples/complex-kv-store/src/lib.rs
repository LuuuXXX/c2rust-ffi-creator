// src/lib.rs — Safe Rust wrapper for the C kv_store library via hicc.
//
// Pattern: C library compiled in via hicc (C++ adapter layer).
//
// build.rs uses:
//   - cc::Build to compile kv.c with the C compiler
//   - hicc_build::Build to compile the C++ adapter extracted from src/ffi.rs
//
// hicc::import_lib! in src/ffi.rs declares safe Rust functions that call
// through the C++ adapter into the original C implementation.
//
// # Quick example
//
// ```rust
// use kv_store::KvStore;
//
// let mut store = KvStore::new(0).expect("allocation failed");
// store.set("lang", "Rust").unwrap();
// assert_eq!(store.get("lang").as_deref(), Some("Rust"));
// store.delete("lang").unwrap();
// assert_eq!(store.count(), 0);
// // store is automatically freed here (Drop impl calls kv_destroy_adapter)
// ```

pub mod error;
mod ffi;

use error::KvError;
use std::ffi::{CStr, CString};

// ---------------------------------------------------------------------------
// Helper: convert a raw C status code to Result<(), KvError>
// ---------------------------------------------------------------------------

fn check_status(code: i32) -> Result<(), KvError> {
    match code {
        c if c == ffi::KV_OK            => Ok(()),
        c if c == ffi::KV_ERR_NOT_FOUND => Err(KvError::NotFound),
        c if c == ffi::KV_ERR_NO_MEMORY => Err(KvError::NoMemory),
        c if c == ffi::KV_ERR_INVALID   => Err(KvError::InvalidArgument),
        other                           => Err(KvError::Unknown(other)),
    }
}

// ---------------------------------------------------------------------------
// KvStore — RAII wrapper around the opaque C handle
// ---------------------------------------------------------------------------

/// A safe, owning handle to an in-memory key-value store.
///
/// The underlying C store is automatically freed when this value is dropped.
pub struct KvStore {
    ptr: *mut std::os::raw::c_void,
}

impl KvStore {
    /// Create a new, empty KV store.
    ///
    /// `initial_capacity` is a pre-allocation hint; pass `0` for the default (16 slots).
    ///
    /// Returns `None` if the C library fails to allocate memory.
    pub fn new(initial_capacity: usize) -> Option<Self> {
        let ptr = ffi::kv_new_adapter(initial_capacity);
        if ptr.is_null() {
            None
        } else {
            Some(KvStore { ptr })
        }
    }

    /// Insert or update a key-value pair.
    ///
    /// Both `key` and `value` are copied inside the C library; the Rust strings
    /// may be dropped afterwards.
    ///
    /// # Errors
    /// Returns `KvError::InvalidArgument` if either string contains a null byte.
    /// Returns `KvError::NoMemory` if the C library cannot allocate memory.
    pub fn set(&mut self, key: &str, value: &str) -> Result<(), KvError> {
        let c_key   = CString::new(key).map_err(|_| KvError::InvalidArgument)?;
        let c_value = CString::new(value).map_err(|_| KvError::InvalidArgument)?;
        let status = ffi::kv_set_adapter(self.ptr, c_key.as_ptr(), c_value.as_ptr());
        check_status(status)
    }

    /// Look up the value for `key`.
    ///
    /// Returns an owned `String` copy of the value, or `None` if the key does
    /// not exist.  (The copy is necessary because the C memory can be
    /// invalidated by a subsequent `set` or `delete`.)
    pub fn get(&self, key: &str) -> Option<String> {
        let c_key = CString::new(key).ok()?;
        let ptr = ffi::kv_get_adapter(self.ptr, c_key.as_ptr());
        if ptr.is_null() {
            None
        } else {
            // Safety: the pointer is valid (owned by the C store) and
            // null-terminated.  We copy the data immediately.
            Some(unsafe { CStr::from_ptr(ptr).to_string_lossy().into_owned() })
        }
    }

    /// Remove the entry for `key`.
    ///
    /// # Errors
    /// Returns `KvError::NotFound` if the key does not exist.
    pub fn delete(&mut self, key: &str) -> Result<(), KvError> {
        let c_key = CString::new(key).map_err(|_| KvError::InvalidArgument)?;
        let status = ffi::kv_delete_adapter(self.ptr, c_key.as_ptr());
        check_status(status)
    }

    /// Return the number of entries currently in the store.
    pub fn count(&self) -> usize {
        ffi::kv_count_adapter(self.ptr)
    }
}

impl Drop for KvStore {
    fn drop(&mut self) {
        // Safety: ptr was allocated by kv_new_adapter and is not aliased anywhere.
        ffi::kv_destroy_adapter(self.ptr);
    }
}

// KvStore owns the C pointer and is the sole writer; do not derive Send/Sync
// without adding locking, since kv.c is not thread-safe.

