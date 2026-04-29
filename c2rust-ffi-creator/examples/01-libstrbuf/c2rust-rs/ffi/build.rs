// build.rs — 按需启用以编译 C 源码
//
// fn main() {
//     // 路径应与原 C 项目实际目录结构一致（禁止假设 src/ / include/ 等固定层级）
//     hicc_build::Build::new()
//         .file("../.c2rust/c/<path/to/foo.c>")   // 实际路径以 spec.json sources[] 为准
//         .include("../.c2rust/c/<path/to/includes>")
//         .compile("c2rust_c_core");
// }
