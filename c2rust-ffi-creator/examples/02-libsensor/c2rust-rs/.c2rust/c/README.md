# 原始 C 项目代码

此目录通过 `cp -r <原C项目根目录>/. .c2rust/c/` 完整复制，保留原始目录结构。

**禁止**手动重组此目录结构，否则将破坏 `#include` 相对路径，
导致无法在此目录内复现原 C 项目的构建与测试。

## 分析产物（由工具自动生成）

- `spec.json`：由 analyze_c_project.py 生成的项目规格
- `interfaces.md`：人工可读的接口清单
- `symbols_expected.txt`：从原 C 构建产物提取的预期导出符号表
