# RCD 不变量认证扩展与实测（2026-11-09）

## 结论

实现前的本地样例改动已提交为 `5805e4a`；认证器实现、文档和测试提交为 `131ce7e`。本次保存为本地提交。
五个 RCD 现均通过源程序不变量认证，并进入自动尾界搜索。沿用原配置的主实验中，五例均得到有效正幂界并通过公共 verify 重放：共 18 个直接多项式证书和 108 个 Jensen 派生候选。Cauchy 与默认一次倒数模板均未新增有效尾界。
另外，RCD-04 的二次倒数补充实验得到 120 个有效倒数候选，并通过独立命令从源码重放。这些界在所比较的 n 上均弱于本例的正幂界；不能把补充实验算入原配置的结果。

## 实现与证据

- 组件：[invariant_certification.py](../../src/contractive_tool/analysis/invariant_certification.py)；流程说明：[invariant_certification.md](../../docs/invariant_certification.md)。
- 保留原精确规则；新增二次多项式的有理矩阵 PSD 检查，以及减去已有约束非负常数倍后的二次余项检查。随后保留原单项式/生成元乘积规则，并用一、二阶 Putinar SOS 兜底。
- SOS 复用现有 MOSEK 后端及有理数证书恢复。数值 optimal 不能直接作为不变量证据，必须检查精确恒等式和半正定性。
- 新证据写入 domain_evidence.json；从源码重建义务后核对矩阵/模型及精确值。公共工作流和独立 Cauchy/倒数 verify/evaluate 均使用保存证据重放，不重新调用数值求解器。
- SOS 兜底采用每次准备 15 秒软期限、单次求解最多 3 秒，以及次数/矩阵规模限制；没有扩大后续尾界搜索预算。不能证明时保留 unknown/不支持诊断，不假设不变量成立。
- 本次五例全部由精确二次余项规则解决新增义务，不需要 SOS 数值兜底。一般 SOS 路径另有四次多项式及带区域乘子的集成测试。

| 样例 | 新增精确二次证据条数 | 不变量状态 |
|---|---:|---|
| rcd_01_biased_exact | 4 | proved |
| rcd_02_damped | 4 | proved |
| rcd_03_shifted_3d | 6 | proved |
| rcd_04_reciprocal_anisotropic | 4 | proved |
| rcd_05_reciprocal_random_step | 8 | proved |

条数按保存的转移义务统计，重复义务在认证时可命中局部缓存。具体表达式见 [invariant_summary.json](invariant_summary.json)。

## 主实验：保持原规则

正幂总软预算 180 秒，其中直接多项式占 50%；倒数独立 120 秒，反馈最多 24 次/90 秒。正幂模板二至四次，c 最多 12 步，单次求解 10 秒、修复 5 秒。Cauchy 使用原标量 SOS 二阶及矩阵乘子设置；倒数保持一次分母、constant_sos 及原参数网格。逐例串行运行，不导入样例自带 eta 或手工证书。
配置及命令：[protocol.json](protocol.json)、[workflow.json](workflow.json)、[results.json](results.json)。墙钟包含共享准备及分析阶段，预算为软限制。

| 样例 | 直接证书 | Jensen 候选 | 主求解墙钟秒 | 公共重放 |
|---|---:|---:|---:|---|
| [rcd_01_biased_exact](rcd_01_biased_exact/measurement.json) | 5 | 30 | 184.499 | proved |
| [rcd_02_damped](rcd_02_damped/measurement.json) | 5 | 30 | 114.781 | proved |
| [rcd_03_shifted_3d](rcd_03_shifted_3d/measurement.json) | 2 | 12 | 184.336 | proved |
| [rcd_04_reciprocal_anisotropic](rcd_04_reciprocal_anisotropic/measurement.json) | 1 | 6 | 11.831 | proved |
| [rcd_05_reciprocal_random_step](rcd_05_reciprocal_random_step/measurement.json) | 5 | 30 | 195.198 | proved |

### 有效尾界数值

下面为各 n 上完整界 min(1,A q^n) 的最优候选，均来自直接正幂。非整数候选来自 Jensen，未改善父证书；本轮 Cauchy 无有效指数候选。

| 样例 | n=20 | n=100 | n=1000 |
|---|---:|---:|---:|
| rcd_01_biased_exact | 0.303531006815 | 9.53328421318e-10 | 1.59556885838e-110 |
| rcd_02_damped | 1 | 6.65523304368e-09 | 2.67583572154e-110 |
| rcd_03_shifted_3d | 1 | 7.68116248394e-08 | 5.32671717025e-89 |
| rcd_04_reciprocal_anisotropic | 9.53674316406e-07 | 7.88860905221e-31 | 9.33263618503e-302 |
| rcd_05_reciprocal_random_step | 0.00370990501936 | 2.99205168098e-16 | 1.11835890744e-163 |

完整比较还包括 n=5,10,50,200,500，保存在逐例 measurement.json 和 run/summary.json；精确排序使用有理数。

### 各路线未新增结果的原因

- 默认倒数在五例上均实际完成 7 组初始分母搜索，求解编码均返回 infeasible，没有可供反馈的矩候选。因此反馈为 0，未耗尽 120 秒；不能据此断言所有二次倒数模板不可行。
- Cauchy 已进入模型构造和搜索。部分点得到范数证书但未得到有效的 q<1；另有编码 infeasible、数值问题及精确恢复失败。RCD-03 联合模型构造触及时间预算，RCD-05 的后续搜索也受时间预算限制。
- 以上均不是原来的不变量认证失败；源程序的二次义务已经得到精确证明。

### n=100 获选模板（精确系数）

**rcd_01_biased_exact**：k=1，A=1672219273386772348816/12205994752043756235，q=99/128。

`eta = 791325452749808*x**2/6526577521035 + 1506656128*x*y/5113493055 + 238386350127232*y**2/15498326827665 + 43084401895712/558455557972455`

[完整产物](rcd_01_biased_exact/run/summary.json)。

**rcd_02_damped**：k=1，A=118851133448022688/124268928933435，q=99/128。

`eta = 2930496537124352*x**2/19758495168555 - 196324508166318464*x*y/1843779575465685 + 3351725451430496*y**2/22318300210635 + 409192981568/167616325042335`

[完整产物](rcd_02_damped/run/summary.json)。

**rcd_03_shifted_3d**：k=1，A=80，q=13/16。

`eta = 24*x**2 - 48*x + 24*y**2 + 48*y + 32*z**2 - 32*z + 56`

[完整产物](rcd_03_shifted_3d/run/summary.json)。

**rcd_04_reciprocal_anisotropic**：k=1，A=1，q=1/2。

`eta = 1`

[完整产物](rcd_04_reciprocal_anisotropic/run/summary.json)。

**rcd_05_reciprocal_random_step**：k=1，A=640/89，q=2809/4096。

`eta = 249*x**2/89 - 142*x*y/89 + 249*y**2/89`

[完整产物](rcd_05_reciprocal_random_step/run/summary.json)。

## RCD-04 二次倒数补充实验

没有固定 eta，自动合成全部二次分母系数。与主实验的倒数配置相比有三项差异：分母次数 1→2，标量编码 constant_sos→sos，独立 CLI 默认修复预算为 10 秒（主实验为 5 秒）。总预算仍为 120 秒、反馈 24 次/90 秒、单次求解 10 秒。此项用于验证扩展后倒数链路确实能合成有效证书，不是只改变模板次数的控制变量实验。
搜索耗时 121.584 秒，12 次尝试，5 次反馈，反馈停止原因 `time_budget`。得到 120 个候选；独立重放验证了 24 份锥约束证书和 120 个尾界候选。
[命令及配置差异](rcd04_reciprocal_degree2/protocol.json) / [完整结果](rcd04_reciprocal_degree2/result.json) / [独立重放](rcd04_reciprocal_degree2/verify.json)。

| n | 二次倒数最优界 | 主实验正幂界 | 倒数更紧 |
|---|---:|---:|---|
| 5 | 0.936914305358 | 0.0312500000000 | 否 |
| 10 | 0.819141321193 | 0.000976562500000 | 否 |
| 20 | 0.528130495547 | 9.53674316406e-7 | 否 |
| 50 | 0.108626767538 | 8.88178419700e-16 | 否 |
| 100 | 0.00637523063401 | 7.88860905221e-31 | 否 |
| 200 | 1.98482417919e-5 | 6.22301527786e-61 | 否 |
| 500 | 4.95456979780e-13 | 3.05493636350e-151 | 否 |
| 1000 | 8.20372819666e-26 | 9.33263618503e-302 | 否 |

倒数在本次比较的所有 n 上均未改善正幂界。逐个 n 的获选分母、k、A、q 见 [comparisons.json](rcd04_reciprocal_degree2/comparisons.json)。

## 验证记录

- 全量回归 293 passed，0 failed；随后补充空目标区域诊断及区域依赖 SOS 两项测试，最终专项 20 passed。两批合计覆盖 295 个不同测试；最后的纯数值状态拒绝测试还单独通过。详见 [validation.json](validation.json)、[全量日志](tests_full.log)、[专项日志](tests_invariant.log)。
- 之前 Q1 的 21 个候选也在新实现下成功重放：[previous_q1_verify.json](previous_q1_verify.json)。
- 新测试覆盖奇异半正定矩阵、平移平方、约束缩放、等式回代、错误不变量、预算耗尽、纯数值成功不得作为证明，以及修改/删除证据后必须拒绝。
- 有限轮真实概率使用独立 Fraction 源码解释器核对；仅核对完整算出的轮数，不能代替全域精确证书。

| 样例 | 核对轮数 | 候选数 | 状态 | 停止原因 |
|---|---|---:|---|---|
| rcd_01_biased_exact | [0, 1000] | 35 | passed | horizon_limit |
| rcd_02_damped | [0, 10] | 35 | passed | reference_state_budget |
| rcd_03_shifted_3d | [0, 60] | 14 | passed | reference_time_budget |
| rcd_04_reciprocal_anisotropic | [0, 1000] | 7 | passed | horizon_limit |
| rcd_05_reciprocal_random_step | [0, 1000] | 35 | passed | horizon_limit |
| RCD-04 二次倒数补充 | [0, 173] | 120 | passed | reference_time_budget |

[主实验概率核对](reference_checks.json) / [补充倒数概率核对](rcd04_reciprocal_degree2/reference_check.json)。
