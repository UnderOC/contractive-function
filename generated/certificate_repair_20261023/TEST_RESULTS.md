# 有预算的证书修复测试（2026-10-23）

修改前版本已提交并推送到 origin/main：`6ae8d92e4c5b1fadfd051201e54d594fa8412c7e`。
本报告对应其后的证书修复实现；框架修改前备份为 `framework.md.bak.20261023_certificate_repair`。

## 实现与边界

新增通用模块 `backends/cvxpy/repair.py`：原始有理重构失败 → 带目标余量的 PSD margin
求解 → 一般有理零空间恢复 → 必要时在低秩面内重新求解 → 全部原模型精确验证。
修复失败仍为 unknown，由外层继续搜索 c。没有修改样例、模板次数或固定参数 c。

默认允许 A 比原数值目标增加 `max(1e-4,0.05*abs(A_num))`；每个候选修复最多
20 秒（阶段边界的软限制）、两次额外 MOSEK 调用、两组零空间猜测，并受全局剩余时间限制。
可通过 `--repair-seconds`、`--repair-relative-gap`、`--repair-max-solves` 设置预算，
时间或求解次数为零时禁用。额外模型保留原模型所有等式与锥约束；数值谱只用于猜测，
接受标准仍是精确有理等式、非负标量和 PSD。最终输出使用恢复后的精确 A。

这仍是有预算的启发式，不能保证修复任意奇异 SDP。结构性奇异块可能阻止全空间
严格余量，低秩面猜测也可能不一致。修复模型 infeasible 不代表原模型不可行。

## 运行命令与结果

使用 README 的 `contractive-frontend-test-20260814` conda 环境和真实 MOSEK。

```bash
python -m contractive_tool solve qlearning.pp --goal tailbound \
  --initial-degree 2 --max-degree 2 --c-values 31/32 \
  --out-dir generated/certificate_repair_20261023/qlearning_fixed
python -m contractive_tool solve qlearning.pp --goal tailbound \
  --out-dir generated/certificate_repair_20261023/qlearning_auto
python -m contractive_tool solve kelly_double_bound.pp --goal tailbound \
  --out-dir generated/certificate_repair_20261023/kelly_auto
python -m pytest -q
python generated/certificate_repair_20261023/check_certificates.py
```

| 测试 | 结果 | D | c | A（近似） | 墙钟 |
|---|---|---:|---|---:|---:|
| Q-learning 原失败参数 | proved | 2 | 31/32 | 50.51089999 | 16.04 秒 |
| Q-learning 默认自动搜索 | proved | 2 | 491/512 | 87.53753623 | 139.29 秒 |
| 双边 Kelly 默认自动搜索 | proved | 1 | 505/512 | 3.20472441 | 25.97 秒 |

三个进程均返回 0，未触发 360 秒外部保护时限。作业以最多两个并发进程运行，耗时不作
严格性能比较。两项默认自动搜索没有指定 D、c、strategy 或模板系数。

所有结果均为 `Pr(K>n) <= min(1,A*c^n)`，K 为完整循环轮数，n 为非负整数。

- 固定 Q-learning 精确 A：`55591690253289625915134632023215992269560321667630/1100587997051823975250764244449544310508252109767`。
- 自动 Q-learning 精确 A：`47034092480298427695128850068691848716452701056/537301990711504173734282032148149719438587769`。
- Kelly 精确 A：`407/127`。

原失败参数的数值最小目标约 48.10561905，修复后的 A 约 50.51089999，在 5% 余量内。
它通过 margin 求解成功，不需要低秩面恢复；单独重放旧模型的修复时间约 4.40 秒。

自动 Q-learning 先在 D=1 完成 10 次无证书探测，再于 D=2 分别在 31/32、123/128、
491/512 经 margin 修复获证。最后的 981/1024 是求解器 numerical_issue、没有可供修复
的数值候选；保留已有证书，且不把该点作为不可行点更新区间。
选择仍按原有的 c 优先规则；c 更小伴随 A 更大，不意味着所有 n 上界都更优或达到全局最优。

## 验证

最终完整回归：**127 passed in 20.75s**。
新增测试覆盖：一般非零对角低秩结构恢复、真实 MOSEK 的 margin 修复和低秩面求解、
错误零空间不能绕过原始约束、修复求解次数上限、时间耗尽/关闭修复、不合法配置。
其中低秩面求解测试先模拟 margin 失败，再使用真实 MOSEK 在恢复的秩 1 面内求解。

独立检查脚本不调用 CVXPY 或修复模块；它以所有主子式精确非负验证 PSD，独立于
生产验证器的 Schur 补算法，并核对目标、模板、约束覆盖、修复上限和全部产物哈希：

| 证书 | 系数等式 | 非负标量 | Gram 块 | 精确主子式 | 结果 |
|---|---:|---:|---:|---:|---|
| Q-learning 固定参数 | 204 | 329 | 34 | 238 | passed |
| Q-learning 自动搜索 | 204 | 329 | 34 | 238 | passed |
| Kelly 自动搜索 | 66 | 77 | 11 | 77 | passed |

首次全量测试因未将 conda bin 加入 PATH，三个 CLI 子进程无法找到 `contractive`；
使用完整 conda PATH 后全部通过，没有为此修改产品代码。

## 产物

- [执行汇总](results.json)、[全量回归](regression.log)、[独立检查脚本](check_certificates.py)
- 固定 Q-learning：[结果](qlearning_fixed/summary.json)、[修复记录](qlearning_fixed/analyses/tailbound/degrees/2/c-001/attempts/002/repair.json)、[独立检查](qlearning_fixed.independent_check.json)
- 自动 Q-learning：[结果](qlearning_auto/summary.json)、[最终证书](qlearning_auto/analyses/tailbound/degrees/2/c-009/attempts/002/certificate.json)、[独立检查](qlearning_auto.independent_check.json)
- 自动 Kelly：[结果](kelly_auto/summary.json)、[独立检查](kelly_auto.independent_check.json)
