// build.rs — 将 C 源码编译为静态库并链接到 Rust FFI crate
//
// 路径相对于此 build.rs 所在目录（ffi/），
// 与 spec.json sources[] 字段中的路径保持一致。

fn main() {
    hicc_build::Build::new()
        .file("../.c2rust/c/src/strbuf.c")
        .include("../.c2rust/c/include")
        .compile("strbuf");
}
