# 实验结果（2026-11-03）

后续四次/六次模板及精细 c 实验见 [2026-11-09 增量结果](refinement_20261109/RESULTS.md)。下文保留原始基线记录。

最终交付 28 个输入（27 个论文参数实例 + 1 个原文核对样例），全部通过解析、CFG 构造和精确归纳不变量检查。

只汇总与当前 `.pp` 的 SHA-256 一致的运行；已修改注释/标志编码的历史结果不混入最终计数。多个当前源程序结果中，优先选最好的精确验证界，否则展示最充分的搜索。

状态统计：精确验证成功：仅得到 1（2 个）；进程预算耗尽（4 个）；未找到可验证证书（13 个）；精确验证成功：非平凡上界（9 个）。

| 输入 | 结果 | 违反概率上界 | η 次数 / c | 证据 |
|---|---|---|---|---|
| [race_x40_y0](pp/race_x40_y0.pp) | 精确验证成功：仅得到 1 | 1 | 1 / 999/1000 | [运行记录](runs/retry_20261103/race_x40_y0/summary.json) |
| [race_x35_y0](pp/race_x35_y0.pp) | 精确验证成功：仅得到 1 | 1 | 1 / 999/1000 | [运行记录](runs/retry_20261103/race_x35_y0/summary.json) |
| [race_x45_y0](pp/race_x45_y0.pp) | 进程预算耗尽 | — | — | [运行记录](runs/retry_20261103/race_x45_y0) |
| [rdwalk_t400](pp/rdwalk_t400.pp) | 未找到可验证证书 | — | — | [运行记录](runs/retry_20261103/rdwalk_t400/summary.json) |
| [rdwalk_t500](pp/rdwalk_t500.pp) | 未找到可验证证书 | — | — | [运行记录](runs/baseline_20261103/rdwalk_t500/summary.json) |
| [rdwalk_t600](pp/rdwalk_t600.pp) | 未找到可验证证书 | — | — | [运行记录](runs/baseline_20261103/rdwalk_t600/summary.json) |
| [1dwalk_x10](pp/1dwalk_x10.pp) | 精确验证成功：非平凡上界 | 0.0125660611511 | 1 / 9999/10000 | [运行记录](runs/baseline_20261103/1dwalk_x10/summary.json) |
| [1dwalk_x50](pp/1dwalk_x50.pp) | 精确验证成功：非平凡上界 | 0.0544410827715 | 1 / 9999/10000 | [运行记录](runs/baseline_20261103/1dwalk_x50/summary.json) |
| [1dwalk_x100](pp/1dwalk_x100.pp) | 精确验证成功：非平凡上界 | 0.106824506668 | 1 / 9999/10000 | [运行记录](runs/baseline_20261103/1dwalk_x100/summary.json) |
| [2dwalk_x1000_y10](pp/2dwalk_x1000_y10.pp) | 未找到可验证证书 | — | — | [运行记录](runs/retry_20261103/2dwalk_x1000_y10/summary.json) |
| [2dwalk_x500_y40](pp/2dwalk_x500_y40.pp) | 未找到可验证证书 | — | — | [运行记录](runs/baseline_20261103/2dwalk_x500_y40/summary.json) |
| [2dwalk_x400_y50](pp/2dwalk_x400_y50.pp) | 未找到可验证证书 | — | — | [运行记录](runs/baseline_20261103/2dwalk_x400_y50/summary.json) |
| [3dwalk_x100_y100_z100](pp/3dwalk_x100_y100_z100.pp) | 精确验证成功：非平凡上界 | 0.316250344538 | 1 / 9999/10000 | [运行记录](runs/simpler_domains_20261103/3dwalk_x100_y100_z100/summary.json) |
| [3dwalk_x100_y150_z200](pp/3dwalk_x100_y150_z200.pp) | 精确验证成功：非平凡上界 | 0.472563055761 | 1 / 9999/10000 | [运行记录](runs/simpler_domains_20261103/3dwalk_x100_y150_z200/summary.json) |
| [3dwalk_x300_y100_z150](pp/3dwalk_x300_y100_z150.pp) | 精确验证成功：非平凡上界 | 0.551626441972 | 1 / 9999/10000 | [运行记录](runs/simpler_domains_20261103/3dwalk_x300_y100_z150/summary.json) |
| [prspeed_t150](pp/prspeed_t150.pp) | 进程预算耗尽 | — | — | [运行记录](runs/retry_20261103/prspeed_t150) |
| [prspeed_t200](pp/prspeed_t200.pp) | 未找到可验证证书 | — | — | [运行记录](runs/retry_20261103/prspeed_t200/summary.json) |
| [prspeed_t250](pp/prspeed_t250.pp) | 进程预算耗尽 | — | — | [运行记录](runs/retry_20261103/prspeed_t250) |
| [m1dwalk_p0.0000001](pp/m1dwalk_p0.0000001.pp) | 未找到可验证证书 | — | — | [运行记录](runs/boolean_domains_20261103/m1dwalk_p0.0000001/summary.json) |
| [m1dwalk_p0.00001](pp/m1dwalk_p0.00001.pp) | 未找到可验证证书 | — | — | [运行记录](runs/boolean_domains_20261103/m1dwalk_p0.00001/summary.json) |
| [m1dwalk_p0.0001](pp/m1dwalk_p0.0001.pp) | 未找到可验证证书 | — | — | [运行记录](runs/retry_boolean_20261103/m1dwalk_p0.0001/summary.json) |
| [newton_p0.0005](pp/newton_p0.0005.pp) | 精确验证成功：非平凡上界 | 0.847310706751 | 2 / 9999/10000 | [运行记录](runs/boolean_empty_domains_20261103/newton_p0.0005/summary.json) |
| [newton_p0.001](pp/newton_p0.001.pp) | 精确验证成功：非平凡上界 | 0.648476702754 | 2 / 9999/10000 | [运行记录](runs/boolean_empty_domains_20261103/newton_p0.001/summary.json) |
| [newton_p0.0015](pp/newton_p0.0015.pp) | 精确验证成功：非平凡上界 | 0.505473069984 | 2 / 9999/10000 | [运行记录](runs/boolean_empty_domains_20261103/newton_p0.0015/summary.json) |
| [ref_p0.0000001](pp/ref_p0.0000001.pp) | 未找到可验证证书 | — | — | [运行记录](runs/boolean_domains_20261103/ref_p0.0000001/summary.json) |
| [ref_p0.000001](pp/ref_p0.000001.pp) | 未找到可验证证书 | — | — | [运行记录](runs/boolean_domains_20261103/ref_p0.000001/summary.json) |
| [ref_p0.00001](pp/ref_p0.00001.pp) | 进程预算耗尽 | — | — | [运行记录](runs/retry_boolean_20261103/ref_p0.00001) |
| [rdadderliteral_figure4](literal/rdadderliteral_figure4.pp) | 未找到可验证证书 | — | — | [运行记录](runs/simpler_domains_20261103/rdadderliteral_figure4/summary.json) |

所有表中成功结果均已通过 `verify_assertion` 独立源程序重放及精确有理数证书复核；近似小数仅用于展示，精确分数在运行记录中。概率界为 1 的两个实例没有提供有用的概率收紧。

失败定位和实验限制见 [DIAGNOSTICS.md](DIAGNOSTICS.md)。完整逐例机器可读结果见 [results.json](results.json)，源程序检查见 [preflight.json](preflight.json)。

现有 assertion 分支回归测试：`pytest -q tests/unit/test_assertion.py tests/integration/test_assertion_backend.py`，14 passed。本次没有修改 `src/` 或已有测试。
