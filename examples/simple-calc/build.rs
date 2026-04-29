// build.rs — compile the C calc source and the hicc C++ adapter.
//
// The C source (calc.c) is compiled by cc (C compiler) so that C-specific
// implicit casts are accepted.  hicc-build compiles only the C++ adapter code
// that is extracted from the hicc::cpp! blocks in src/ffi.rs.

fn main() {
    // 1. Compile the original C implementation with the C compiler.
    cc::Build::new()
        .file(".c2rust/c/calc.c")
        .include(".c2rust/c")
        .compile("calc_c");

    // 2. Extract hicc::cpp! blocks from src/ffi.rs and compile them as C++.
    hicc_build::Build::new()
        .rust_file("src/ffi.rs")
        .include(".c2rust/c")
        .compile("calc_adapter");

    println!("cargo::rustc-link-lib=calc_c");
    println!("cargo::rustc-link-lib=calc_adapter");
    println!("cargo::rustc-link-lib=stdc++");
    println!("cargo::rerun-if-changed=src/ffi.rs");
    println!("cargo::rerun-if-changed=.c2rust/c/calc.c");
    println!("cargo::rerun-if-changed=.c2rust/c/calc.h");
}
