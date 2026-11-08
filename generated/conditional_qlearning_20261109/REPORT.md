# contractive_examples：自动尾界分析实测（2026-11-09）

本报告覆盖本轮选择的 2 个 `.pp`，来源于 `contractive_examples`。
状态统计：`{'proved': 1, 'no_certificate_found': 1}`；有效候选按方法统计：`{'direct_polynomial': 3, 'positive_jensen': 18}`。
**这里只把本次自动合成并独立重放通过的证书计为有效结果。** 样例目录附带的手工证书未用于合成，
不能将“目录里已有证书”当成“本工具已经找到”。

## 测试规则

- 沿用此前 Kelly 报告：正幂总软预算 180 秒，倒数额外 120 秒；倒数反馈时间 90 秒、最多 24 次。
- 单次求解器 10 秒，修复 5 秒；正幂从二次模板开始、最高四次，c 最多 12 步，首个成功次数后停止升阶。
- 正幂指数区间 [1/4,4]，16 个粗点加一轮细化；Cauchy 二阶标量 SOS、一次矩阵乘子。
- 倒数保持一次分母、默认增长与支撑网格、自适应 k，指数优化目标 n=20,100,1000。
- 倒数初始 c 网格为 3/2、5/4、9/8、17/16、33/32、65/64、129/128，r_seed=1/2；反馈可调整参数。
- 比较 n=5,10,20,50,100,200,500,1000；逐个 n 比较完整 `min(1,A*q^n)`，保留所有有效候选。
- 各例使用全部程序状态变量。这些输入没有 Kelly 原例的额外 round 计数器，因此不需要排除它。
- 串行运行，避免不同实验之间的求解资源竞争。外层单例求解保护上限 600 秒、独立重放 180 秒；这不是额外搜索预算。
- 不修改输入、不固定 eta、不针对个别样例更改规则。配置见 [workflow.json](workflow.json)，全部命令见 [results.json](results.json)。
- `integer` 中直接多项式按 k=1 解释，多项式次数不等于 k；`noninteger` 区分 Cauchy 与 Jensen 派生。
- 退出时势函数为零，尾界事件统一为完整循环轮数 `K>n`；不混入其他时钟或断言失败概率。

## 总览

| 样例 | 主流程状态 | 整数正幂 | 非整数正幂来源 | 倒数 | 求解进程墙钟秒 | 独立重放 |
|---|---|---|---|---|---:|---|
| [Q1_biased_noisy_two_actions](#q1_biased_noisy_two_actions) | proved | 有 | positive_jensen | no_certificate_found | 190.01 | proved |
| [Q3_three_action_max](#q3_three_action_max) | no_certificate_found | 未找到/未进入 | — | no_certificate_found | 229.02 | — |

主流程状态统计：`{'proved': 1, 'no_certificate_found': 1}`。
独立重放通过：1 个样例。

主流程 `proved` 表示至少一条路线成功，不代表所有路线都找到证书。
数值 infeasible/unknown 不是数学不可行性证明；unsupported 表示未能完成所需编译/语义证明。
2 个求解进程累计墙钟 419.03 秒（不含后续独立验证与诊断）。

## 有效尾界摘要

| 样例 | n=20 | n=100 | n=1000 |
|---|---:|---:|---:|
| Q1_biased_noisy_two_actions | 0.909385099 | 0.000172893032 | 2.38155779e-46 |
| Q3_three_action_max | — | — | — |

## 分支时间与反馈预算

| 样例 | 直接多项式秒 | Cauchy 已记录秒 | 倒数搜索秒 | 反馈迭代数 | 倒数停止原因 |
|---|---:|---:|---:|---:|---|
| Q1_biased_noisy_two_actions | 93.392 | 79.786 | 6.246 | 0 | no_verified_moment_parent |
| Q3_three_action_max | 97.544 | 12.636 | 44.085 | 0 | no_verified_moment_parent |

阶段未记录的时间不能解释为零成本：异常阶段、共享编译和独立重放需结合日志与进程墙钟读取。
倒数搜索耗时不含外层独立验证；24 次反馈是上限，无初始矩候选时会提前停止。
未进入工作流的样例在此表中不会贡献有效的预算利用率数据。

以下各例给出完整的三路线比较、获选模板和诊断。小数仅展示，排序与证书验证使用精确有理数。
极小数用科学计数法显示，不把浮点下溢的 0 当作精确概率。

## 本次条件分支支持的实现与测试结论

开始实现前的本地改动已保存为提交 `fd0c5514aeaf11912b889ff97e60b7c963dca335`，并推送至 GitHub 的 `main`。本报告只使用随后新运行的 Q1、Q3 数据；没有从旧报告复制模板或把手工证书作为搜索输入。

**两条路线的条件分支编译支持已补齐，两个样例都不再返回 conditional body guards 的 unsupported。** 但在保持原配置和预算的本轮实验中，Cauchy 和倒数均未新增有效尾界。Q1 的有效结果来自直接多项式及其 Jensen 派生；Q3 仍没有通过完整认证的候选。

| 样例 | 分区覆盖 / 公共随机原子 | 直接多项式 | Cauchy | 倒数 | 主求解进程墙钟 |
|---|---|---|---|---|---:|
| Q1 | 2 / 4 | 3 个证书，另有 18 个 Jensen 派生候选；公共 verify 重放通过 | 固定模板精确恢复超时；联合模板构造预算耗尽 | 7 组初始分母尝试均返回 infeasible，无反馈父候选 | 190.009 秒 |
| Q3 | 5 / 3 | 存在 optimal 数值解，精确证书未恢复 | 二、三次模板触及矩阵 SOS 决策变量上限；四次模板构造预算耗尽 | 7 组初始分母尝试均返回 infeasible，无反馈父候选 | 229.017 秒 |

Q3 的五个分区是逻辑展开得到的覆盖域，允许重叠；不是五条随机路径。每个覆盖域内均有一个概率和精确等于 1 的完整后继分布。共同随机原子通过有理 CDF 分点合并构造，未将状态条件随机化。

### Q1 的有效界

| n | 整数正幂最优界 | 非整数正幂最优界 | 倒数 |
|---|---:|---:|---|
| 20 | 0.909385098782 | 0.920246881439 | 未找到 |
| 100 | 1.72893031799e-4 | 5.10570012680e-4 | 未找到 |
| 1000 | 2.38155779431e-46 | 1.20158219613e-40 | 未找到 |

在 n=1000 获选的直接多项式为 k=1、q=115/128、A≈7.744447133，对应

`eta ≈ 3.60465*q1^2 - 1.56159*q1*q2 - 6.08977*q1 + 12.2018*q2^2 - 16.5797*q2 + 9.40377`。

上式只用于阅读，不能将小数系数当作精确证书；完整有理系数及其他 n 的获选模板见下方逐例记录。非整数结果全是 Jensen 派生，不代表 Cauchy 成功。直接多项式算法本次未改变，Q1 相比先前运行找到证书，不能据此归因于新增加的条件分支编译。

Q1 的 Cauchy 固定模板已构造完整分区模型并调用求解器，但记录为 `reconstruction_time_budget`。联合模板记录为 `state_model_time_budget`，该参数点的模型未完成，没有送入求解器。这两个停止位置不同。

### Q3 的具体失败位置

直接多项式在 c=7/8、15/16、31/32 的 Putinar 编码中仍返回过 optimal，但均为 solved_unverified。c=7/8、15/16 各进行一次裕度修复，后续精确重构超时；最后一个参数点未能在剩余阶段预算内恢复证书。原有“浮点可行但精确认证未完成”的问题依然存在。

Cauchy 不再卡在源码编译。它对二、三、四次模板进行了构造尝试：前两者返回 `Matrix SOS decision count exceeds budget`（当前上限 20000），四次构造在剩余时间内停止。固定模板路径没有执行，是因为没有可用的直接多项式父证书；联合模板路径已独立执行，并不依赖父证书。

两个样例的倒数分支均实际进行了 7 次初始合成，耗时分别约 6.246 秒、44.085 秒。没有成功分母，所以反馈均为 0 次，停止原因为 `no_verified_moment_parent`。没有耗尽 120 秒时间上限；延长时间本身不会使这组已经完成的初始参数尝试产生新候选。指定编码返回 infeasible 也不能证明所有倒数模板均不可行。

### 实现范围与验证

- 公共编译器保留区域守卫、完整原始后继及精确概率，复用既有条件回代和严格边界处理。
- 各区域共用同一 eta。Cauchy 共用 B/t 和随机基底；倒数共用 b、c、r0、D，固定 D 矩阵约束及反馈也覆盖所有区域。
- 有限支持上的分解经过精确恒等式核对；原有无条件程序继续使用原表示和基底。
- 证书检查器从源码重新构造区域和约束。新增测试检查删除区域、修改概率/守卫、删除模型等式必须被拒绝，且重放不调用求解器。
- 新增独立源码解释器分布对照，覆盖 Q1、Q3 的相等边界、重叠区域和随机后再判断条件；另有退出后继不得错误置零、非收缩区域不得遗漏的反例检查。
- **最终全量回归：275 passed，0 failed，0 skipped。** 见 [tests.log](tests.log) 和 [validation.json](validation.json)。本次 Q1 的 21 个候选另经公共 verify 重放，以及有限轮精确概率核对；Q3 无候选，有限轮执行核对不算尾界认证成功。

最初一次 Q1 实验在联合模型构造阶段长时间未返回，已中断并保留在 [初次未完成实验](../conditional_qlearning_20261109_initial/interruption.json)。随后为 Cauchy 加入区域、矩阵乘子、系数匹配及序列化之间的协作预算检查，重新运行本报告的两例。超时仅记 unknown，保留已有证书并继续独立倒数分支；没有将不完整模型当作证明。单次符号操作和验证仍可能造成软预算超时。

下一步的瓶颈已经从条件分支支持转为模型规模、精确恢复以及倒数候选生成。应优先研究 Cauchy 基底/矩阵编码的规模和恢复预算，再研究倒数的模板次数与参数网格；本次未额外提高这些设置，也不宣称找到了 Cauchy 或倒数的全局最优界。


## Q1_biased_noisy_two_actions

源码：`contractive_examples/qlearning/Q1_biased_noisy_two_actions.pp`。SHA-256：`6bb3309f665f4f7ad40a35b127ab66399a925488f695f8aa18d0ec11765ed67b`。

状态 **proved**；求解进程墙钟 190.009 秒；工具记录耗时 188.91947465576231 秒。

有效候选数量（按方法）：`{'direct_polynomial': 3, 'positive_jensen': 18}`。

已尝试的多项式次数：`[2]`；主阶段停止原因：`time_budget`。

[原始日志](Q1_biased_noisy_two_actions/solve.log) / [测量数据](Q1_biased_noisy_two_actions/measurement.json) / [产物目录](Q1_biased_noisy_two_actions/run/)。

| 阶段 | 状态 | 阶段耗时秒 | 原因/停止信息 |
|---|---|---:|---|
| direct_polynomial | proved | 93.392 | time_budget |
| cauchy_fixed | no_certificate_found | 30.600 |  |
| cauchy_fixed | skipped | — | fixed_stage_budget |
| cauchy_joint | no_certificate_found | 49.186 |  |
| cauchy_joint | skipped | — | time_budget |
| positive_jensen | proved | — |  |
| reciprocal | no_certificate_found | 6.595 |  |

`cauchy_fixed` 内层诊断：`[{'stage': 'state_model', 'status': 'unknown', 'reason': 'reconstruction_time_budget', 'count': 1}]`。


`cauchy_joint` 内层诊断：`[{'stage': 'state_model', 'status': 'unknown', 'reason': 'state_model_time_budget', 'count': 1}]`。


`reciprocal` 内层诊断：`[{'stage': 'denominator', 'status': 'unknown', 'reason': 'infeasible', 'count': 7}]`。


倒数搜索统计：`{'stop_reason': None, 'feedback_stop_reason': 'no_verified_moment_parent', 'elapsed_seconds': 6.246323611121625, 'attempts': 7, 'feedback_iterations': 0, 'improved_iterations': []}`。


直接多项式编码/求解记录统计（状态、求解器原始状态）：`{('infeasible', 'infeasible'): 12, ('solved_unverified', 'optimal'): 2, ('proved', 'optimal'): 3}`。


精确证书恢复未通过的记录（未计为有效尾界）：

```json
[
  {
    "path": "run/analyses/tailbound/degrees/2/c-004/attempts/002/verification.json",
    "status": "solved_unverified",
    "reason": "No exact original-domain certificate recovered",
    "nonpsd_blocks": [
      "o18_s0",
      "o1_s0",
      "o21_s0",
      "o2_s0",
      "o6_s0"
    ],
    "repair_status": "solved_unverified",
    "repair_seconds": 5.090752235148102,
    "repair_solver_calls": 1
  },
  {
    "path": "run/analyses/tailbound/degrees/2/c-009/attempts/002/verification.json",
    "status": "solved_unverified",
    "reason": "No exact original-domain certificate recovered",
    "nonpsd_blocks": [
      "o18_s0",
      "o19_s0",
      "o1_s0",
      "o20_s0",
      "o2_s0",
      "o3_s0",
      "o4_s0"
    ],
    "repair_status": "solved_unverified",
    "repair_seconds": null,
    "repair_solver_calls": null
  }
]
```


| n | 整数正幂 | 非整数正幂 | 倒数 | 合并最优 | 合并证书 |
|---|---:|---:|---:|---:|---|
| 5 | 1.00000000 | 1.00000000 | — | 1.00000000 | C1 |
| 10 | 1.00000000 | 1.00000000 | — | 1.00000000 | C1 |
| 20 | 0.909385099 | 0.920246881 | — | 0.909385099 | C3 |
| 50 | 0.0365918153 | 0.0553300370 | — | 0.0365918153 | C3 |
| 100 | 0.000172893032 | 0.000510570013 | — | 0.000172893032 | C3 |
| 200 | 3.85979786e-9 | 4.34754405e-8 | — | 3.85979786e-9 | C3 |
| 500 | 4.29463019e-23 | 2.68417020e-20 | — | 4.29463019e-23 | C3 |
| 1000 | 2.38155779e-46 | 1.20158220e-40 | — | 2.38155779e-46 | C3 |

| n | 整数证书 | 非整数证书 | 倒数证书 |
|---|---|---|---|
| 5 | C1 | C2 | — |
| 10 | C1 | C2 | — |
| 20 | C3 | C4 | — |
| 50 | C3 | C4 | — |
| 100 | C3 | C4 | — |
| 200 | C3 | C4 | — |
| 500 | C3 | C4 | — |
| 1000 | C3 | C4 | — |

### 在比较表中获选的具体模板

全部候选见本例 summary.json；以下去重列出表中实际获选者。每个候选的界为 `min(1,A*q^n)`。

**C1：direct_polynomial，k=1**

`eta = 1628537083966405393928783810080*q1**2/1390005840973124678056097527469 - 792937889667647616639732534177252322499252*q1/296024914832070595412388765456867552117165 + 12752172519444748545831745*q2**2/6287424399901691985413904 - 301791497936296931547796324852617096730*q2/111910177986673913819766229697449497309 + 1809031860387468613739634623339402077440086279/538467601243640476907612627464334239160333028`

`A = 300794322932706054646109691505613199770665812288026333/95255969748757627951167597458289537287897753623270656`

`q = 31/32`

正幂势函数为 `V=eta^k`；活动域 eta 归一化下界为 1。

来源：`{'certificate': 'analyses/tailbound/degrees/2/c-005/attempts/001/certificate.json'}`。

**C2：positive_jensen，k=1/4**

`eta = 1628537083966405393928783810080*q1**2/1390005840973124678056097527469 - 792937889667647616639732534177252322499252*q1/296024914832070595412388765456867552117165 + 12752172519444748545831745*q2**2/6287424399901691985413904 - 301791497936296931547796324852617096730*q2/111910177986673913819766229697449497309 + 1809031860387468613739634623339402077440086279/538467601243640476907612627464334239160333028`

`A = 666521806123/500000000000`

`q = 496047120809/500000000000`

由直接多项式父证书 `direct:0` 派生 `V=eta^k`；不是 Cauchy 求解成功，且不会优于父证书。

来源：`{'rule': 'Jensen_on_killed_potential', 'seed': 'direct:0'}`。

**C3：direct_polynomial，k=1**

`eta = 237011840547316541572147568830816*q1**2/65751655789459520735138200923375 - 964585002127208192*q1*q2/617693494885264885 - 145921908616328033186573597601120155295297877*q1/23961802740384142325810649736390371575679125 + 106474791187919294946355331194442336*q2**2/8726134310508375401763314664938875 - 128540006700864122357665974820971733461226747536*q2/7752833127619212607805441896231688104291787375 + 3451014220684106077400410640622135521714/366981848979534974353973280450033596625`

`A = 21456321810465415166296150354764684140630964878745656/2770542743859616116351734062362309776051840960523375`

`q = 115/128`

正幂势函数为 `V=eta^k`；活动域 eta 归一化下界为 1。

来源：`{'certificate': 'analyses/tailbound/degrees/2/c-007/attempts/002/certificate.json'}`。

**C4：positive_jensen，k=7/8**

`eta = 237011840547316541572147568830816*q1**2/65751655789459520735138200923375 - 964585002127208192*q1*q2/617693494885264885 - 145921908616328033186573597601120155295297877*q1/23961802740384142325810649736390371575679125 + 106474791187919294946355331194442336*q2**2/8726134310508375401763314664938875 - 128540006700864122357665974820971733461226747536*q2/7752833127619212607805441896231688104291787375 + 3451014220684106077400410640622135521714/366981848979534974353973280450033596625`

`A = 5996068933041/1000000000000`

`q = 227636497903/250000000000`

由直接多项式父证书 `direct:2` 派生 `V=eta^k`；不是 Cauchy 求解成功，且不会优于父证书。

来源：`{'rule': 'Jensen_on_killed_potential', 'seed': 'direct:2'}`。

### 独立有限轮概率核对

状态 `passed`；完整核对轮数 `[0, 7]`；候选数 `21`；停止原因 `reference_state_budget`。

[详细概率记录](Q1_biased_noisy_two_actions/reference_check.json)。该检查独立读取源码，用精确分数传播全部存活路径；超过状态/算术/时间上限时只报告已完整算出的轮数。

## Q3_three_action_max

源码：`contractive_examples/qlearning/Q3_three_action_max.pp`。SHA-256：`246002661b900ce64300553042b37f9a84c05993997fccee4f55da5fa915510a`。

状态 **no_certificate_found**；求解进程墙钟 229.017 秒；工具记录耗时 228.42181425122544 秒。

有效候选数量（按方法）：`{}`。

已尝试的多项式次数：`[2]`；主阶段停止原因：`time_budget`。

[原始日志](Q3_three_action_max/solve.log) / [测量数据](Q3_three_action_max/measurement.json) / [产物目录](Q3_three_action_max/run/)。

| 阶段 | 状态 | 阶段耗时秒 | 原因/停止信息 |
|---|---|---:|---|
| direct_polynomial | no_certificate_found | 97.544 | time_budget |
| cauchy_fixed | skipped | — | no_polynomial_certificate |
| cauchy_joint | unknown | — | Matrix SOS decision count exceeds budget |
| cauchy_joint | unknown | — | Matrix SOS decision count exceeds budget |
| cauchy_joint | no_certificate_found | 12.636 |  |
| positive_jensen | skipped | — |  |
| reciprocal | no_certificate_found | 44.363 |  |

`cauchy_joint` 内层诊断：`[{'stage': 'state_model', 'status': 'unknown', 'reason': 'state_model_time_budget', 'count': 1}]`。


`reciprocal` 内层诊断：`[{'stage': 'denominator', 'status': 'unknown', 'reason': 'infeasible', 'count': 7}]`。


倒数搜索统计：`{'stop_reason': None, 'feedback_stop_reason': 'no_verified_moment_parent', 'elapsed_seconds': 44.085395054891706, 'attempts': 7, 'feedback_iterations': 0, 'improved_iterations': []}`。


直接多项式编码/求解记录统计（状态、求解器原始状态）：`{('infeasible', 'infeasible'): 6, ('solved_unverified', 'optimal'): 3, ('numerical_issue', None): 1}`。


精确证书恢复未通过的记录（未计为有效尾界）：

```json
[
  {
    "path": "run/analyses/tailbound/degrees/2/c-003/attempts/002/verification.json",
    "status": "solved_unverified",
    "reason": "No exact original-domain certificate recovered",
    "nonpsd_blocks": [
      "o1_s0",
      "o2_s0"
    ],
    "repair_status": "solved_unverified",
    "repair_seconds": 5.331099048256874,
    "repair_solver_calls": 1
  },
  {
    "path": "run/analyses/tailbound/degrees/2/c-004/attempts/002/verification.json",
    "status": "solved_unverified",
    "reason": "No exact original-domain certificate recovered",
    "nonpsd_blocks": [
      "o1_s0",
      "o2_s0"
    ],
    "repair_status": "solved_unverified",
    "repair_seconds": 5.189906466286629,
    "repair_solver_calls": 1
  },
  {
    "path": "run/analyses/tailbound/degrees/2/c-005/attempts/002/verification.json",
    "status": "solved_unverified",
    "reason": "No exact original-domain certificate recovered",
    "nonpsd_blocks": [
      "o1_s0",
      "o2_s0"
    ],
    "repair_status": "solved_unverified",
    "repair_seconds": null,
    "repair_solver_calls": null
  }
]
```


| n | 整数正幂 | 非整数正幂 | 倒数 | 合并最优 | 合并证书 |
|---|---:|---:|---:|---:|---|
| 5 | — | — | — | — | — |
| 10 | — | — | — | — | — |
| 20 | — | — | — | — | — |
| 50 | — | — | — | — | — |
| 100 | — | — | — | — | — |
| 200 | — | — | — | — | — |
| 500 | — | — | — | — | — |
| 1000 | — | — | — | — | — |

| n | 整数证书 | 非整数证书 | 倒数证书 |
|---|---|---|---|
| 5 | — | — | — |
| 10 | — | — | — |
| 20 | — | — | — |
| 50 | — | — | — |
| 100 | — | — | — |
| 200 | — | — | — |
| 500 | — | — | — |
| 1000 | — | — | — |

### 在比较表中获选的具体模板

全部候选见本例 summary.json；以下去重列出表中实际获选者。每个候选的界为 `min(1,A*q^n)`。

### 独立有限轮概率核对

状态 `passed`；完整核对轮数 `[0, 8]`；候选数 `0`；停止原因 `reference_state_budget`。

[详细概率记录](Q3_three_action_max/reference_check.json)。该检查独立读取源码，用精确分数传播全部存活路径；超过状态/算术/时间上限时只报告已完整算出的轮数。

本例没有自动合成候选，因此这里仅为源码有限前缀检查，不能算自动尾界验证通过。

## 复现

在项目目录激活原求解环境，输出目录应为新目录：

```bash
conda activate contractive-frontend-test-20260814
python examples/run_contractive_examples.py --out-dir generated/contractive_examples_reproduce --cases Q1_biased_noisy_two_actions Q3_three_action_max
python examples/check_contractive_examples.py generated/contractive_examples_reproduce
python examples/diagnose_contractive_examples.py generated/contractive_examples_reproduce
python examples/report_contractive_examples.py generated/contractive_examples_reproduce
```

样例输入哈希见逐例记录。全域有效性依赖精确证书重放，有限轮概率传播仅是额外回归核对。
