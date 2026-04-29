// build.rs — 将 C 源码编译为静态库并链接到 Rust FFI crate
//
// 路径相对于此 build.rs 所在目录（ffi/），
// 与 spec.json sources[] 字段中的路径保持一致。

fn main() {
    hicc_build::Build::new()
        .file("../.c2rust/c/src/platform/linux/i2c.c")
        .file("../.c2rust/c/src/sensor/pressure.c")
        .file("../.c2rust/c/src/sensor/temperature.c")
        .include("../.c2rust/c/include")
        .compile("sensor");
}
