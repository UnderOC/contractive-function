# 精确分段生存前期望测试（2026-10-19）

环境：README 指定的 conda 环境，真实 CVXPY/MOSEK。
预算：D=1..2，每个 D 最多 10 次 c 二分，每点最多 2 次编码，总软预算 120 秒。
完整 pytest：115 passed in 23.32s；见 [日志](../piecewise_survival_regression_20261019.log)。

| 输入 | 模式 | 状态 | A | c | 耗时（秒） |
|---|---|---|---|---|---|
| `RCD_example.pp` | exact_piecewise_survival | [proved](RCD_example/summary.json) | 1024 | 5/8 | 7.33 |
| `tailbound_benchmark_pack/pp/01_coupon2.pp` | finite_boolean_survival | [proved](01_coupon2/summary.json) | 2 | 1/2 | 1.105 |
| `tailbound_benchmark_pack/pp/02_coupon4.pp` | finite_boolean_survival | [proved](02_coupon4/summary.json) | 4 | 3/4 | 4.229 |
| `kelly_unbounded.pp` | exact_piecewise_survival | [no_certificate_found](kelly_unbounded/summary.json) | — | — | 6.852 |
| `tailbound_benchmark_pack/pp/03_rw_int.pp` | exact_piecewise_survival | [no_certificate_found](03_rw_int/summary.json) | — | — | 2.463 |
| `tests/fixtures/halving.pp` | exact_piecewise_survival | [proved](halving/summary.json) | 4 | 1/2 | 0.925 |
| `tests/fixtures/geometric_exit.pp` | finite_boolean_survival | [proved](geometric_exit/summary.json) | 1 | 1/2 | 0.296 |
| `kelly_simple.pp` | 未进入后端 | [unsupported](kelly_simple/summary.json) | — | — | 0.65 |

说明：
- 符号模式在每个 exact_domain 上计算精确生存期望；用于 SOS 的 domain 是闭合覆盖，仍可能带来保守性。
- RCD 产生四个后继存活组合域，收缩义务中的退出分支贡献为零。
- 01/02 和 geometric 的布尔宏步继续使用原来的精确有限状态规则。
- Kelly 无界样例与 03_rw_int 的无证书结论只涉及本轮搜索，不是无解证明。
- kelly_simple 的退出标注 round=3 不能由现有实数域归纳验证器推出；此检查早于宏步构造，未更改样例或绕过验证。
- 连续采样实例未纳入本轮精确处理测试表；已有采样单元回归通过，保留显式标记的 raw_round_moments 规则。
- 新增下一轮必定退出的边界集成测试，验证常数 eta=1 可被精确规则合成，而旧普通期望规则不能接受该证书。
- 对表中每个运行检查 manifest 文件哈希；对已证明的 Gram 证书另读回有理值，重查全部原始等式、非负性、PSD 及目标值。

[独立检查记录](independent_check.json)；[完整机器可读结果](results.json)。
