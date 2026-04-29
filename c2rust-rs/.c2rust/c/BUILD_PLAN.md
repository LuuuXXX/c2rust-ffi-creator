# 构建方案（Build Plan）

## 构建系统

**CMake**（`CMakeLists.txt` 位于根目录）

```bash
# Release 构建
cmake -B _build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build _build

# 产物位于 _build/
#   Linux:  _build/libcalc.so  (动态库)
#           _build/libcalc.a   (静态库)
#   macOS:  _build/libcalc.dylib
```

## 编译器与标志

| 项目 | 值 |
|------|----|
| 编译器 | gcc / clang |
| C 标准 | `-std=c11` |
| 优化级别 | `-O2`（Release）/ `-O0 -g`（Debug） |
| 警告标志 | `-Wall -Wextra`（CMake 默认） |
| 额外链接 | `-lm`（数学库，用于 `sqrt`） |

## 构建产物

| 产物 | 路径 | 说明 |
|------|------|------|
| 动态库 | `_build/libcalc.so` | 供动态链接使用 |
| 静态库 | `_build/libcalc.a` | 供静态链接使用 |
| 测试程序 | `_build/test_calc` | 单元测试可执行文件 |

## 快速构建命令

```bash
# 在 .c2rust/c/ 目录下执行
cd .c2rust/c

# Release 构建
cmake -B _build -DCMAKE_BUILD_TYPE=Release && cmake --build _build

# Debug 构建（包含符号信息）
cmake -B _build_debug -DCMAKE_BUILD_TYPE=Debug && cmake --build _build_debug
```

## 平台注意事项

- **Linux**：需要安装 `cmake`、`gcc`/`clang`、`libm`（通常默认安装）
- **macOS**：需要安装 Xcode Command Line Tools（`xcode-select --install`）
- **Windows**：使用 MSYS2/MinGW 或 Visual Studio 构建（未测试）
