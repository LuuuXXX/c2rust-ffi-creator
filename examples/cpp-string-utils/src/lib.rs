// src/lib.rs — Safe Rust wrapper for the str_counter C library.
//
// Pattern: C library compiled in via hicc (C++ adapter layer).
//
// build.rs uses hicc-build to compile:
//   1. The C++ adapter extracted from src/ffi.rs (hicc::cpp! blocks)
//   2. The original C implementation (str_counter.c) via cc
//
// hicc::import_lib! in src/ffi.rs declares safe Rust functions that call
// through the C++ adapter.

mod ffi;

use std::ffi::CString;

/// A safe, owning handle to the string frequency counter.
///
/// Automatically frees the underlying C store when dropped.
pub struct StrCounter {
    ptr: *mut std::os::raw::c_void,
}

impl StrCounter {
    /// Create a new, empty counter.
    ///
    /// Returns `None` if the C library fails to allocate.
    pub fn new() -> Option<Self> {
        let ptr = ffi::sc_new();
        if ptr.is_null() {
            None
        } else {
            Some(StrCounter { ptr })
        }
    }

    /// Increment the count for `word`.
    ///
    /// # Errors
    /// Returns `Err(())` if `word` contains a null byte or the C library
    /// cannot allocate memory.
    pub fn add(&mut self, word: &str) -> Result<(), ()> {
        let c_word = CString::new(word).map_err(|_| ())?;
        let rc = ffi::sc_add(self.ptr, c_word.as_ptr());
        if rc == 0 { Ok(()) } else { Err(()) }
    }

    /// Return the frequency of `word` (0 if not present).
    pub fn get(&self, word: &str) -> usize {
        let c_word = match CString::new(word) {
            Ok(s) => s,
            Err(_) => return 0,
        };
        ffi::sc_get(self.ptr, c_word.as_ptr())
    }

    /// Return the total number of words added (including repetitions).
    pub fn total(&self) -> usize {
        ffi::sc_total(self.ptr)
    }
}

impl Drop for StrCounter {
    fn drop(&mut self) {
        // Safety: ptr was returned by sc_new and is not aliased.
        ffi::sc_free(self.ptr);
    }
}

