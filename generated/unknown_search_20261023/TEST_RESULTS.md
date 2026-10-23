# unknown 恢复搜索测试（2026-10-23）

本次仅优化参数搜索对 unknown 的处理，不放宽精确证书验证。两个样例的默认自动流程均成功；之前的默认流程分别耗尽时间预算或触发外部超时，未返回证书。

## 搜索变化

- unknown 保持当前 lower、upper 不变，下一次探测 `(c+upper)/2`。
- 收到 proved 或 infeasible 后恢复区间二分；已测试的候选向 upper 折半跳过。
- 已验证证书始终保留，不会因后续 unknown 丢失。
- 所有探测计入原有预算：每个 D 最多 10 次，全局最多 32 次。当前次数尝试结束后，按既有升阶/成功停止规则处理。
- 日志记录候选来源及每次观察前后的端点。该策略是有预算的启发式，不保证找到所有可行模板或全局最优证书。

## 环境与命令

使用 README 的 conda 环境 `contractive-frontend-test-20260814` 和真实 MOSEK。没有指定次数、收缩参数、策略或模板系数。

```bash
python -m contractive_tool solve qlearning.pp --goal tailbound \
  --out-dir generated/unknown_search_20261023/qlearning
python -m contractive_tool solve kelly_double_bound.pp --goal tailbound \
  --out-dir generated/unknown_search_20261023/kelly_double_bound
python -m pytest -q
```

两个求解进程并行运行，各设置 360 秒外部保护时限，均自行返回 0，没有触发超时。耗时包含运行环境和并行资源竞争，不能作为严格性能基准。项目内部软预算机制此次未修改。

## 默认运行结果

| 样例 | 结果 | 搜索次数 | 选中 D | 选中 c | A | 墙钟时间 |
|---|---|---:|---:|---|---|---:|
| Q-learning | proved | 20 | 2 | 63/64 | 约 16.87335109 | 142.17 秒 |
| 双边 Kelly | proved | 10 | 1 | 505/512 | 407/127 | 25.91 秒 |

两者均输出对所有非负整数 n 成立的 `Pr(K>n) <= min(1,A*c^n)`，K 为完整循环轮数。
Q-learning 的精确 A 为 `2221361501727377849659376653/131649100964423727560295420`。
Kelly 合成的势函数为 `eta = (687 - 280*wealth)/127`，round 系数为零。
证书同时推出几乎处处终止。这里选择的是预算内证书，不代表全局最优；更小的 c 可能伴随更大的 A。

### Q-learning 轨迹

D=1 的 10 次探测均返回 infeasible，随后升至 D=2：

| 次序 | c | 反馈 |
|---:|---|---|
| 1 | 1/2 | infeasible |
| 2 | 3/4 | infeasible |
| 3 | 7/8 | infeasible |
| 4 | 15/16 | infeasible |
| 5 | 31/32 | unknown：数值候选未通过精确验证 |
| 6 | 63/64 | proved |
| 7 | 123/128 | unknown |
| 8 | 249/256 | unknown |
| 9 | 501/512 | unknown |
| 10 | 1005/1024 | unknown |

后续不确定结果不改变端点，也不撤销 63/64 的证书。原先 31/32 的重构问题仍存在，本次通过搜索其他参数取得证书。

### 双边 Kelly 轨迹

全部在 D=1 完成：

| 次序 | c | 反馈 |
|---:|---|---|
| 1 | 1/2 | infeasible |
| 2 | 3/4 | infeasible |
| 3 | 7/8 | infeasible |
| 4 | 15/16 | infeasible |
| 5 | 31/32 | infeasible |
| 6 | 63/64 | unknown |
| 7 | 127/128 | proved |
| 8 | 251/256 | infeasible |
| 9 | 505/512 | proved |
| 10 | 1007/1024 | infeasible |

## 验证与产物

完整回归：**118 passed in 23.56s**。测试覆盖 unknown 后继续找到可行点、端点保持、已有证书保留、全 unknown 耗尽预算及候选不重复。

独立读取最终证书，重新检查全部有理系数等式、标量非负性、精确 PSD、目标值及产物哈希：

| 样例 | 系数等式 | 非负标量 | PSD 块 | 结果 |
|---|---:|---:|---:|---|
| Q-learning | 204 | 329 | 34 | 全部通过 |
| 双边 Kelly | 66 | 77 | 11 | 全部通过 |

同时检查全部 unknown 均未更新端点、每个 D 的参数无重复且未超出 10 次。数值候选未通过精确验证的情况仍标记为 unknown，不报告为证明成功。

- [结果汇总](results.json)、[源文件哈希](source_hashes.json)、[回归日志](regression.log)
- Q-learning：[summary](qlearning/summary.json)、[执行记录](qlearning.execution.json)、[独立检查](qlearning.independent_check.json)、[精确证书](qlearning/analyses/tailbound/degrees/2/c-006/attempts/002/certificate.json)
- 双边 Kelly：[summary](kelly_double_bound/summary.json)、[执行记录](kelly_double_bound.execution.json)、[独立检查](kelly_double_bound.independent_check.json)、[精确证书](kelly_double_bound/analyses/tailbound/degrees/1/c-009/attempts/001/certificate.json)
