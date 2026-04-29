// build.rs — compile the C kv_store source and the hicc C++ adapter.
//
// The C source (kv.c) is compiled by cc (C compiler) so that C-specific
// implicit casts are accepted.  hicc-build compiles only the C++ adapter code
// that is extracted from the hicc::cpp! blocks in src/ffi.rs.

fn main() {
    // 1. Compile the original C implementation with the C compiler.
    cc::Build::new()
        .file(".c2rust/c/src/kv.c")
        .include(".c2rust/c/include")
        .compile("kv_c");

    // 2. Extract hicc::cpp! blocks from src/ffi.rs and compile them as C++.
    hicc_build::Build::new()
        .rust_file("src/ffi.rs")
        .include(".c2rust/c/include")
        .compile("kv_adapter");

    println!("cargo::rustc-link-lib=kv_c");
    println!("cargo::rustc-link-lib=kv_adapter");
    println!("cargo::rustc-link-lib=stdc++");
    println!("cargo::rerun-if-changed=src/ffi.rs");
    println!("cargo::rerun-if-changed=.c2rust/c/src/kv.c");
    println!("cargo::rerun-if-changed=.c2rust/c/include/kv.h");
}

