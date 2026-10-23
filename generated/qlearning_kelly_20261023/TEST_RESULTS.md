# Q-learning 与双边 Kelly 的现有框架测试（2026-10-23）

本次新增 `qlearning.pp`，未修改后端、模板族或搜索算法。使用 README 指定的
`contractive-frontend-test-20260814` conda 环境和真实 CVXPY/MOSEK。
各 `.execution.json` 保存命令、返回码、时限与运行状态；默认运行另加 360 秒
外部硬超时，仅作为测试资源保护，不改变框架内部默认的 300 秒软预算。

## 输入转换

初值 `(q1,q2)=(0,2)`，守卫为平方误差大于 `1/16`。`max(q1,q2)` 展开为确定分支，
动作选择和两点奖励各使用一个独立 `prob(0.5)`。奖励已代入更新常数，不引入 m、r
额外状态；所有源十进制数均为精确有理数。位置不变量为 `[0,2]^2`，末尾
`refute true` 标记所有有限退出。输入中没有给定势函数系数、c 或 horizon。

不变量及宏步构造通过：2 个状态变量、D=2 时 6 个未知系数、32 个精确域、34 条
义务，模式 `exact_piecewise_survival`。时钟关系 `T=2+5*K+2`，K 是学习更新次数。
对 76 个活动测试点（包括 max 相等的情况）逐点以有理数比较程序前期望与原始
四结果更新，全部一致；还检查目标区域不执行循环。
见 [源转换检查](source_check.json)。该有限检查用于回归，不代替证书的全域证明。

## 固定参数的自动系数合成

| 运行 | 结果 |
|---|---|
| D=2，c=31/32 | no_certificate_found；一个编码报告 infeasible，另一个得到数值 optimal（目标约 48.105619），但精确重构失败 |
| D=2，c=99/100 | proved；框架自行合成 6 个系数并输出证书，全程未注入笔记中的势函数 |

c=31/32 的失败发生在两个接近秩 1 的 Gram 块；重构后的系数等式成立、标量乘子
非负，但 PSD 未获精确验证。当前零对角面猜测不能充分恢复这种具有非零对角元的
低秩面。此结果不是原数学问题不可行，也不推翻笔记里的解析证书。

c=99/100 成功证书的显示近似为（实际文件中保存精确有理数）：

```text
eta(q1,q2) = 4.386726*q1^2 + 1.242120*q1*q2 + 1.902219*q2^2
             - 13.84009*q1 - 5.667618*q2 + 13.73957
```

精确前因子与尾界为：

```text
A = 187835106097679903628187 / 18758731802776406477344
  ≈ 10.013209212249581
Pr(K>n) <= min(1, A*(99/100)^n),  n=0,1,2,...
```

向上取整前因子为 10.01321 后仍是有效上界。证书给出的 99% 首次命中预算是 688
次更新；不是持续保持精度的保证，也不是数学最优预算。它比笔记 270 次的有理
证书更保守，尽管 A 更小，因为 c 更接近 1。

独立读回产物，检查 204 条精确系数等式、329 个非负标量、34 个有理 PSD 块、
初态目标值和 manifest 哈希，全部通过。

- [成功合成摘要](qlearning_fixed_c099/summary.json)
- [返回证书](qlearning_fixed_c099/analyses/tailbound/degrees/2/c-001/attempts/002/certificate.json)
- [独立精确检查](qlearning_fixed_c099.independent_check.json)
- [31/32 测试摘要](qlearning_fixed/summary.json)

## 默认自动搜索

Q-learning 和双边 Kelly 均执行不指定 D、c、strategy 的默认 `solve` 命令。
Q-learning 在 D=1 检查 10 个 c 点未找到证书；D=2 在 c=31/32 处出现
solved_unverified，二分因此以 unknown 停止，未继续检查更靠近 1 的 c。
双边 Kelly 在 D=1 的 c=63/64、D=2 的 c=31/32 处出现数值不确定结果，也停止
当前次数搜索并升阶。这重现了之前的问题，而不是默认流程自动找到固定参数证书。

Q-learning 默认运行最终返回 `no_certificate_found / time_budget`，进程返回码 0，
墙钟约 326 秒；框架尚未在默认预算中实现该例的自动参数选择和验证闭环。
双边 Kelly 默认运行在 360 秒触发外部硬时限并终止，未生成最终 summary 或证书；
已保留部分模型及 solver 日志。外部超时不是求解器不可行结论。
双边 Kelly 另外以 D=1、c=99/100 做控制复测，约 2.52 秒返回 proved，
`A=113003675/59825304`，独立读回精确系数等式、非负性和 PSD 检查也通过。
见 [Kelly 控制复测](kelly_fixed_control/summary.json) 和
[独立检查](kelly_fixed_control.independent_check.json)。

精确验证是接受条件，不能将数值 optimal 或 unknown 当作 proved。后续改进应分别
针对低秩 Gram 的有理重构、unknown 后的参数探索以及符号处理的硬时间预算，不能
通过放宽验证容差来伪造通过。本次保留现有算法，只测试并记录其能力边界。

- [Q-learning 默认命令与最终执行状态](qlearning_auto.execution.json)
- [Kelly 默认命令与最终执行状态](kelly_auto.execution.json)
- [Q-learning 默认日志](qlearning_auto.log)
- [Kelly 默认日志](kelly_auto.log)
- [本次被测源码哈希](tested_source_hashes.json)

## 复现

从 `contractive_function` 目录、在上述 conda 环境下执行，使用新的输出目录：

```bash
python -m contractive_tool solve qlearning.pp --goal tailbound \
  --initial-degree 2 --max-degree 2 --c-values 99/100 --out-dir generated/qlearning_new_fixed
python -m contractive_tool solve qlearning.pp --goal tailbound --out-dir generated/qlearning_new_auto
python -m contractive_tool solve kelly_double_bound.pp --goal tailbound --out-dir generated/kelly_new_auto
```

默认流程建议使用外部进程时限，因为目前软预算不覆盖单个长时间符号阶段。
