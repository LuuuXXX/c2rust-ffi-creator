use std::path::PathBuf;

fn main() {
    let c_root = PathBuf::from(".c2rust/c");
    let c_include = c_root.join("include");
    let c_src = c_root.join("src");

    // Compile the C implementation into a static archive.
    cc::Build::new()
        .file(c_src.join("kv.c"))
        .include(&c_include)
        .compile("kv");

    // Re-run this script if the C sources change.
    println!("cargo:rerun-if-changed={}", c_src.join("kv.c").display());
    println!("cargo:rerun-if-changed={}", c_include.join("kv.h").display());

    // Generate Rust bindings from kv.h (types + extern "C" function declarations).
    // The actual function bodies come from the static archive compiled above.
    let bindings = bindgen::Builder::default()
        .header(c_include.join("kv.h").to_str().unwrap())
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings for kv.h");

    let out_path = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings!");
}
