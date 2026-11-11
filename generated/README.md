# 论文 tailbound 原始产物

这里仅保留论文样例的最终运行、必要的配置/输入适配，以及 K4 的分支复核记录。
论文 provenance 引用的 Q3 修复前/仅扩预算对照及回归日志也保留，用于解释最终修复。
每个最终 `run/` 保留完整求解尝试、证明及失败状态，不只保留成功候选。
历史批次、assertion violation 实验和开发诊断保存在 `develop` 的 `9515985b` 快照。

统一的样例、运行路径、哈希和耗时见 [结果索引](../experiments/paper_tailbounds/manifest.json)，
操作说明见 [论文实验](../experiments/paper_tailbounds/README.md)。目录名含日期及历史 ID，
为保持论文工程路径引用而保留；K6 对应 `kelly_double_bound`，S6 对应 `original`。

25 个最终工作流的原始 `summary.json` 与证书未修改；新增的 `shared/source.pp` 是
按原 manifest 哈希校验的逐字节输入快照，供路径变化后的独立复核使用。
历史 manifest 未重新写入，不能将新增的快照误认为原运行时额外生成的证明。
新实验推荐写入被 Git 忽略的 `generated/local/`，明确挑选后再纳入版本控制。
