// build.rs - 自动生成 C 头文件的 Rust 绑定
//
// 此文件由 r2rust-ffi-creator SKILL 生成，请根据实际项目调整。
//
// 工作原理：
//   1. 读取 .c2rust/c/include/ 下的头文件
//   2. 使用 bindgen 生成 Rust 类型和函数声明
//   3. 将生成的绑定写入 $OUT_DIR/bindings.rs
//   4. src/ffi.rs 通过 include!() 宏引入这些绑定

use std::path::PathBuf;

fn main() {
    // C 源码目录（相对于 Cargo.toml 所在目录）
    let c_dir = PathBuf::from(".c2rust/c");
    let include_dir = c_dir.join("include");

    // 若 include/ 目录不存在，使用 c 目录自身
    let actual_include = if include_dir.exists() {
        include_dir
    } else {
        c_dir.clone()
    };

    // 告诉 Cargo：如果头文件变化，重新运行 build.rs
    println!("cargo:rerun-if-changed={}", c_dir.display());
    println!("cargo:rerun-if-changed=build.rs");

    // 查找主公开头文件
    // TODO: 将 "mylib.h" 替换为实际的公开头文件名
    let main_header = actual_include.join("mylib.h");

    if !main_header.exists() {
        // 若头文件不存在，跳过 bindgen（适用于手动编写 ffi.rs 的场景）
        eprintln!("cargo:warning=未找到头文件 {}，跳过 bindgen 自动生成", main_header.display());
        eprintln!("cargo:warning=请手动编辑 src/ffi.rs 添加 extern \"C\" 声明");
        return;
    }

    // 配置 bindgen
    let bindings = bindgen::Builder::default()
        .header(main_header.to_str().unwrap())
        // 添加头文件搜索路径
        .clang_arg(format!("-I{}", actual_include.display()))
        // 仅生成白名单中的符号（根据实际项目修改前缀）
        // TODO: 将 "mylib_" 替换为实际的函数前缀
        .allowlist_function("mylib_.*")
        .allowlist_type("MyLib.*")
        .allowlist_var("MYLIB_.*")
        // 为结构体生成 Debug、Default 等 trait
        .derive_debug(true)
        .derive_default(true)
        .derive_copy(true)
        // 生成 #[repr(C)] 标注
        .generate_comments(true)
        // 使用 core 而非 std（可选，用于 no_std 环境）
        // .use_core()
        .generate()
        .expect("bindgen 无法生成绑定，请检查头文件路径和 libclang 安装");

    // 写入生成文件
    let out_path = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("无法写入 bindings.rs");

    println!("cargo:warning=bindgen 绑定已生成到 {}/bindings.rs", out_path.display());
}
