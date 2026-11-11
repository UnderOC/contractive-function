# main / develop 整理记录（2026-11-12）

## 完整快照

先将已有 3 个本地提交及全部工作区修改同步到 GitHub main，保存提交为 `9515985b`。
随后从同一提交建立并推送 develop。develop 保留清理前的实现、全部实验和备份文档；
清理不会改写其历史，也不会修改上级项目中的论文及其他复现工具。

## main 的范围

- 保留 tailbound 的直接多项式、Cauchy、Jensen、倒数幂、前端和共享证明后端。
- 移除 assertion violation 专属模块、CLI 参数、说明和测试；增加入口拒绝回归。
- 源语言 `assert/refute` 的控制流语义保留；`late_bad_exit` 是独立的兼容尾界事件。
- 保留 25 个规范样例、论文表格使用的 24 个最终结果及 Q6 的已有结果。
- 保留每个最终运行的完整尝试与证书，以及论文引用的 Q3 修复对照；按哈希补存原输入供跨路径复核。
- 旧 reprsm benchmark、旧 tailbound benchmark 批次、过期诊断、assertion 产物、
  framework 备份及旧开发综述从 main 移除。两个 coupon 输入迁入 tests/fixtures 用于回归。
- 根目录少量 `.pp` 兼容输入继续供历史 manifest 或测试使用，规范论文名称以 benchmark_index 为准。
- 新增实验索引和统一 report / verify / ablate 命令，不重跑合成或改变已有概率结果。

原始记录可能仍包含已停用字段或旧绝对路径，这是历史证据；不批量改写它们。
需要旧分析时切换到 develop，或使用 `git show develop:<path>` 查看单个文件。
