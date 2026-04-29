// build.rs — compile the C source and the hicc C++ adapter together.
//
// hicc_build reads src/ffi.rs, extracts hicc::cpp! blocks, generates a C++
// adapter, and compiles it (C++ only).  The original C source is compiled
// separately with cc so its C-specific void* casts are accepted.

fn main() {
    // 1. Compile the original C implementation with the C compiler.
    cc::Build::new()
        .file(".c2rust/c/src/str_counter.c")
        .include(".c2rust/c/include")
        .compile("str_counter_c");

    // 2. Compile the C++ adapter generated from hicc::cpp! blocks in src/ffi.rs.
    //    hicc-build uses the C++ compiler for the generated adapter code only.
    hicc_build::Build::new()
        .rust_file("src/ffi.rs")
        .include(".c2rust/c/include")
        .compile("str_counter_adapter");

    println!("cargo::rustc-link-lib=str_counter_c");
    println!("cargo::rustc-link-lib=str_counter_adapter");
    println!("cargo::rustc-link-lib=stdc++");
    println!("cargo::rerun-if-changed=src/ffi.rs");
    println!("cargo::rerun-if-changed=.c2rust/c/src/str_counter.c");
    println!("cargo::rerun-if-changed=.c2rust/c/include/str_counter.h");
}

