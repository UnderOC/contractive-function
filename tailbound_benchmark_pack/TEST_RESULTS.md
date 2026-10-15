# Tailbound benchmark 转换与测试结果

最新默认设置测试已完成：从 **D=1** 开始，使用有界 c 二分搜索；12 个可运行实例中
**2 个 proved、10 个 no_certificate_found**，09–11 非确定性实例跳过。完整记录见本文末尾
“默认 D=1 与剩余 benchmark 测试”，机器汇总见
[runs/default_d1_bisection_20261014/results.json](runs/default_d1_bisection_20261014/results.json)。
下文首批数据及旧时钟说明属于历史记录，各追加批次使用其明确标注的配置。

## 首批历史结论

冻结范围为 `manifest.json` 中的 12 个 benchmark。`09_rw_1d_demonic`、`10_rw_2d_demonic`、`11_rw_2d_variant` 含恶魔非确定分支，按要求跳过，且没有把 `if *` 改成随机分支。其余 9 个 benchmark 共生成并实际运行 12 个 `.pp` 实例（`05_rdwalk_uniform` 取 `d=1,5,10,20`）。12 个进程均返回 0，均正常完成 tailbound 有限搜索，最终状态均为 `no_certificate_found`，没有未处理异常。

本批次没有任何 `proved` 实例，因此没有可报告的已证明指数公式。`no_certificate_found` 只表示在下述有限次数、次数上限和时间预算内没有恢复出精确证书，不表示尾界不存在或程序不可能终止。MOSEK 报告的数值 `optimal` 也只有通过精确验证后才可称为 `proved`；本批次的数值候选均未通过该验证。

机器可核对入口为 [results.json](results.json)，批次索引为 [run_index.json](runs/final_20261014/run_index.json)，完整回归结果为 [regression.log](runs/final_20261014/regression.log)。所有 `.ppl` 原件、来源资料和 reference 文件均保留未覆盖。

## 事件语义与时钟

当前后端的 `tailbound` 是 `late_bad_exit`：对所有非负整数 `n`，若证书成立，其结论形式才是

```text
Pr[T < ∞, T > n, failure] <= A * c^n
```

其中 `T` 从原程序入口开始按生成的 pCFG 转移计数，终止位置吸收后不继续计时；后端不假设程序终止。转换文件在正常循环退出后使用 `refute true`，所以每个有限退出都进入 `failure`。因此本次测试的是“有限但较晚的退出”，不是在终止性未知时擅自使用的无条件 `Pr[T>n]`。

为避免 ghost counter 本身增加 pCFG 步数，`01`–`08` 的源循环计数器没有放入 `.pp`。令 `K` 表示一次有限运行实际执行的循环体次数（在 `01`–`08` 中也就是源规格的 ghost `C`），从最终产物的 `shared/cfg.json` 可逐边得到：

| ID / 实例 | 当前时钟与循环次数的精确关系 | 每轮 pCFG 构成 |
|---|---:|---|
| `01_coupon2` | `T = 3K + 4` | 守卫、概率选择、赋值各 1 步；另有 2 个初始化和 2 个退出步 |
| `02_coupon4` | `T = 4K + 6` | 守卫、外层硬币、内层硬币、赋值各 1 步；另有 4 个初始化和 2 个退出步 |
| `03_rw_int` | `T = 3K + 3` | 守卫、概率选择、赋值各 1 步；另有 1 个初始化和 2 个退出步 |
| `04_rw_real` | `T = 3K + 3` | 守卫、概率选择、采样并更新各 1 步；另有 1 个初始化和 2 个退出步 |
| `05_rdwalk_uniform_d{1,5,10,20}` | `T = 2K + 3` | 守卫、采样并更新各 1 步；另有 1 个初始化和 2 个退出步 |
| `06_rw_real_large` | `T = 3K + 3` | 与 `04` 相同 |
| `07_polynomial_tail` | `T = 3K + 4` | 守卫、显式采样、`m` 更新各 1 步；另有 `m` 初始化、初始采样和 2 个退出步 |
| `08_escape_200` | `T = 4K + 3` | 守卫、首次采样并更新、确定分支、分支动作各 1 步；另有 1 个初始化和 2 个退出步 |
| `12_signed_cost_multiplicative` | `T = 5K + 5` | 守卫、采样并更新 `x`、概率选择、更新 `C`、更新 `y` 各 1 步；另有 3 个初始化和 2 个退出步 |

这里的 `T` 是这些转换后 `.pp` 的 pCFG 时钟，不冒充原论文 CFG 的到达时间。尤其是语法顶层的 `random r ~ Distribution(...)` 是随机变量声明，本身不产生 CFG 转移；每次在赋值右侧使用它时才取一个新的独立样本，并把“采样 + 状态更新”合并为同一个转移。因此：

- `04`、`06` 保留“先选择加/减分支，再采样”的概率顺序，但源伪代码中的单独采样与赋值在当前 CFG 中合并。
- `05` 每轮的连续采样和 `x` 更新合并；保留终止执行的更新序列和最终 tick 总数，但不保留原非尾递归的调用/返回开销、递归深度或中间成本轨迹。
- `08` 先完成 `Uniform[-1,0.5]` 的采样更新，再检查更新后的 `x>=200`；只有真分支才使用独立的 `Uniform[-1,2]`。两个样本各与对应更新合并。
- `12` 的 `Uniform[-1,0.5]` 与 `x` 更新合并；原 signed cost 的 `C` 更新仍作为真实程序步骤保留。
- `07` 使用的是显式 `r := Uniform(0,1)`，所以初始采样和每轮采样各自仍占一个转移。

## 转换对应关系与参数

这些 `.ppl` 是依据论文程序图/附录独立规范化的重建规格，并非作者工具的原始输入。转换保留概率常数、连续分布和采样顺序；没有把连续分布离散化，也没有为了求解加入无依据的可达边界。

| ID | 原规格 → 当前输入 | 参数与分布 | 原目标 / 当前测试目标 |
|---|---|---|---|
| `01_coupon2` | `benchmarks/01_coupon2.ppl` → [pp/01_coupon2.pp](pp/01_coupon2.pp) | `c0=c1=0`；每轮独立公平选券 | 原目标为集齐两券的循环次数；当前为集齐后的全部有限退出，入口 pCFG 时钟 |
| `02_coupon4` | `benchmarks/02_coupon4.ppl` → [pp/02_coupon4.pp](pp/02_coupon4.pp) | 四标志初值 0；两层独立公平分支 | 原目标为集齐四券的完整抽取次数；当前为有限退出的 pCFG 时钟，未把两次抛币算作一次 |
| `03_rw_int` | `benchmarks/03_rw_int.ppl` → [pp/03_rw_int.pp](pp/03_rw_int.pp) | `x0=1`；`-1` 概率 `3/5`、`+1` 概率 `2/5` | 原 `refute(x<1)` 在整数状态下等价于首次到达 0；当前以 `refute true` 标记该有限退出 |
| `04_rw_real` | `benchmarks/04_rw_real.ppl` → [pp/04_rw_real.pp](pp/04_rw_real.pp) | `x0=2`；`7/10` 减、`3/10` 加；连续 `Uniform[0,1]` | 原目标首次 `x<0`；当前同一有限退出事件，但换成转换后 pCFG 时钟 |
| `05_rdwalk_uniform` | `benchmarks/05_rdwalk_uniform.ppl` → [d=1](pp/05_rdwalk_uniform_d1.pp)、[d=5](pp/05_rdwalk_uniform_d5.pp)、[d=10](pp/05_rdwalk_uniform_d10.pp)、[d=20](pp/05_rdwalk_uniform_d20.pp) | `x0=0`；每轮连续 `Uniform[-1,2]`；`d=1,5,10,20` 是本包具体实例，不冒充论文实验参数 | 原递归返回后 `tick(1)` 的最终总成本；循环转换保留终止运行的更新次数，当前实际分析的是 pCFG 运行时间 |
| `06_rw_real_large` | `benchmarks/06_rw_real_large.ppl` → [pp/06_rw_real_large.pp](pp/06_rw_real_large.pp) | 论文变体 `x0=200000000`；其余同 `04` | 原目标首次 `x<0`；当前为有限退出的 pCFG 时钟，用于数值压力测试 |
| `07_polynomial_tail` | `benchmarks/07_polynomial_tail.ppl` → [pp/07_polynomial_tail.pp](pp/07_polynomial_tail.pp) | `m0=1`；守卫前初始连续样本及每轮新 `Uniform[0,1]` | 原循环次数满足 `Pr[K>n]=1/(n+2)^2`；当前换成仿射 pCFG 时钟，仍是重尾边界，不应产生虚假的统一严格指数证明 |
| `08_escape_200` | `benchmarks/08_escape_200.ppl` → [pp/08_escape_200.pp](pp/08_escape_200.pp) | `x0=0`；先 `Uniform[-1,0.5]` 更新，更新后 `x>=200` 才加独立 `Uniform[-1,2]` | 原无条件 runtime 在不终止轨迹取 `+∞`；当前事件显式带 `T<∞`，排除不终止轨迹，不能与论文 Table 2 的界直接比较 |
| `09_rw_1d_demonic` | `benchmarks/09_rw_1d_demonic.ppl` → 未转换、未运行 | `x0=2`；先概率更新，后恶魔选择 | 跳过：调度器可观察此前随机结果；不能用随机分支替代 `if *` |
| `10_rw_2d_demonic` | `benchmarks/10_rw_2d_demonic.ppl` → 未转换、未运行 | `x0=y0=2`；先恶魔选坐标，后连续 `Uniform[-2,1]` | 跳过：当前语法/后端不支持对所有调度器的尾界；保留附录的选择/采样顺序 |
| `11_rw_2d_variant` | `benchmarks/11_rw_2d_variant.ppl` → 未转换、未运行 | `x0=3,y0=2`；恶魔选择后才有 `7/10,3/10` 分支与连续采样 | 跳过：未把恶魔选择替换为公平硬币或其他概率选择 |
| `12_signed_cost_multiplicative` | `benchmarks/12_signed_cost_multiplicative.ppl` → [pp/12_signed_cost_multiplicative.pp](pp/12_signed_cost_multiplicative.pp) | `x0=y0=1,C0=y`；连续 `Uniform[-1,0.5]` 和公平乘子 | 原目标是终止输出 signed accumulated cost `C`（且源计算保留、终态 `C=y`）；当前只测试运行时间，后端尚不支持 cost tail，结果不是原成本界 |

## 环境、命令与搜索预算

- Python：`3.11.15`，解释器为 `/home/sunzhouyue/.conda/envs/contractive-frontend-test-20260814/bin/python`。
- 工具版本：`contractive_tool 0.4.0`；后端 `CVXPY 1.9.3`；求解器 `MOSEK 11.2.6`；`SymPy 1.14.0`；`NumPy 2.4.6`；`SciPy 1.17.1`；`Lark 1.2.2`；`pytest 8.3.5`。
- MOSEK 许可证位于 `/home/sunzhouyue/mosek/mosek.lic`，本报告和日志未输出许可证内容。
- `matlab_invoked=false`；没有调用 MATLAB，也没有启用固定 horizon、Kelly 特殊矩或非多项式捷径。
- 批次并发数为 3；从 `2026-10-13T20:11:11.493681Z` 到 `2026-10-13T20:20:05.506673Z`，墙钟 `534.012984` 秒。

批次驱动的复现形式如下；输出根必须在启动时不存在或为空，若复跑应换成新的目录：

```bash
MOSEKLM_LICENSE_FILE=/home/sunzhouyue/mosek/mosek.lic \
PYTHONDONTWRITEBYTECODE=1 \
/home/sunzhouyue/.conda/envs/contractive-frontend-test-20260814/bin/python \
  tailbound_benchmark_pack/run_tailbound_suite.py \
  --output-root tailbound_benchmark_pack/runs/final_20261014 \
  --jobs 3
```

驱动为每个实例实际执行的命令模板如下；`run_index.json` 与每个 `run.log` 保存了展开后的绝对输入、输出路径和完整命令：

```bash
/home/sunzhouyue/.conda/envs/contractive-frontend-test-20260814/bin/python \
  -m contractive_tool solve <input.pp> \
  --goal tailbound --out-dir <new-output-dir> \
  --initial-degree 2 --max-degree 6 --degree-step 1 \
  --c-values 1/2 9/10 99/100 \
  --max-order 4 --max-attempts-per-point 2 --max-parameter-points 32 \
  --strategy auto --enabled-strategies putinar schmudgen handelman \
  --max-products 256 --max-psd-dimension 80 --max-decisions 20000 \
  --total-seconds 300 --per-attempt-seconds 30 \
  --family polynomial
```

`c` 使用上述精确有理数网格。每个 `(D,c)` 点最多 2 次策略尝试；模板次数 `D=2..6`，SOS/乘子阶数实际为 1、2、3。总时限是在符号阶段之间进行软检查，求解器 optimizer 时限是硬限制，因此单个完整进程可能在已开始的符号/求解阶段结束后超过 300 秒；`02_coupon4` 的 413 秒属于这一已记录预算语义，不是未处理超时。

## 实际求解与验证结果

“点”是实际访问的 `(D,c)` 参数点；“尝试分类”来自对应 `search_history.json`。`solved_unverified` 表示 MOSEK 原始状态为数值 `optimal`，但精确原域证书恢复失败；它不是证明。所有 summary 的 `termination` 均为 `unknown`，本批次没有偷偷加入终止性前提。

全批次共实际访问 169 个 `(D,c)` 点、执行 338 次求解尝试；合计分类为 infeasible 168、numerical_issue 142、solved_unverified 16、unbounded 12，四类之和与 338 次尝试一致。12 份进程日志的 stderr 均为空。

| 实例 | D；点；尝试 | 实际 c / 尝试次数 | 尝试分类 | 停止原因 | summary / 进程耗时（秒） | 状态与证据 |
|---|---|---|---|---|---:|---|
| `01_coupon2` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 16；numerical_issue 14 | max_degree | 238.288988 / 238.773745 | `no_certificate_found`；[summary](runs/final_20261014/01_coupon2/summary.json)；[log](runs/final_20261014/logs/01_coupon2.run.log) |
| `02_coupon4` | `2,3`；4；8 | `1/2×4, 9/10×2, 99/100×2` | infeasible 6；numerical_issue 2 | time_budget | 413.102915 / 413.835734 | `no_certificate_found`；[summary](runs/final_20261014/02_coupon4/summary.json)；[log](runs/final_20261014/logs/02_coupon4.run.log) |
| `03_rw_int` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 23；numerical_issue 7 | max_degree | 14.591092 / 15.026424 | `no_certificate_found`；[summary](runs/final_20261014/03_rw_int/summary.json)；[log](runs/final_20261014/logs/03_rw_int.run.log) |
| `04_rw_real` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 24；numerical_issue 6 | max_degree | 14.350352 / 14.788107 | `no_certificate_found`；[summary](runs/final_20261014/04_rw_real/summary.json)；[log](runs/final_20261014/logs/04_rw_real.run.log) |
| `05_rdwalk_uniform_d1` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 22；numerical_issue 3；solved_unverified 5 | max_degree | 11.395137 / 11.832560 | `no_certificate_found`；[summary](runs/final_20261014/05_rdwalk_uniform_d1/summary.json)；[log](runs/final_20261014/logs/05_rdwalk_uniform_d1.run.log) |
| `05_rdwalk_uniform_d5` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 14；numerical_issue 16 | max_degree | 10.860291 / 11.295270 | `no_certificate_found`；[summary](runs/final_20261014/05_rdwalk_uniform_d5/summary.json)；[log](runs/final_20261014/logs/05_rdwalk_uniform_d5.run.log) |
| `05_rdwalk_uniform_d10` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 9；numerical_issue 21 | max_degree | 10.989096 / 11.428106 | `no_certificate_found`；[summary](runs/final_20261014/05_rdwalk_uniform_d10/summary.json)；[log](runs/final_20261014/logs/05_rdwalk_uniform_d10.run.log) |
| `05_rdwalk_uniform_d20` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 6；numerical_issue 15；solved_unverified 9 | max_degree | 12.521656 / 12.966052 | `no_certificate_found`；[summary](runs/final_20261014/05_rdwalk_uniform_d20/summary.json)；[log](runs/final_20261014/logs/05_rdwalk_uniform_d20.run.log) |
| `06_rw_real_large` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | numerical_issue 18；unbounded 12 | max_degree | 14.137592 / 14.570490 | `no_certificate_found`；[summary](runs/final_20261014/06_rw_real_large/summary.json)；[log](runs/final_20261014/logs/06_rw_real_large.run.log) |
| `07_polynomial_tail` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 17；numerical_issue 13 | max_degree | 167.112885 / 167.608987 | `no_certificate_found`；[summary](runs/final_20261014/07_polynomial_tail/summary.json)；[log](runs/final_20261014/logs/07_polynomial_tail.run.log) |
| `08_escape_200` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 9；numerical_issue 19；solved_unverified 2 | max_degree | 25.450519 / 25.900019 | `no_certificate_found`；[summary](runs/final_20261014/08_escape_200/summary.json)；[log](runs/final_20261014/logs/08_escape_200.run.log) |
| `12_signed_cost_multiplicative` | `2,3,4,5,6`；15；30 | `1/2×10, 9/10×10, 99/100×10` | infeasible 22；numerical_issue 8 | max_degree | 273.983352 / 274.491833 | `no_certificate_found`；[summary](runs/final_20261014/12_signed_cost_multiplicative/summary.json)；[log](runs/final_20261014/logs/12_signed_cost_multiplicative.run.log) |

三个跳过项没有伪造 summary 或日志：

- `09_rw_1d_demonic`：`skipped_nondeterministic`。
- `10_rw_2d_demonic`：`skipped_nondeterministic`。
- `11_rw_2d_variant`：`skipped_nondeterministic`。

总计出现 16 次 `solved_unverified`（`05/d1` 5 次、`05/d20` 9 次、`08` 2 次）；每份相应 `verification.json` 的结论均为 `No exact original-domain certificate recovered`。因此 `proved_candidates=[]`、`selection=null`，没有 `A`、`c` 或 `lambda=-log(c)` 的完整已证明指数式可以填写，也没有把数值解冒充证明。

`02_coupon4` 的最后一个 `D=3,c=1/2` Schmüdgen 尝试自身约用 279.953 秒；由于总预算只在阶段边界做软检查，该阶段完成后 summary 才以 413.102915 秒和 `stop_reason=time_budget` 正常结束。这是预算策略的预期表现，不是崩溃、悬挂或未捕获超时。

## 边界样例解释

`07_polynomial_tail` 的已知循环次数尾是多项式 `1/(n+2)^2`。把 `K` 换成仿射时钟 `T=3K+4` 不会把它变成对所有 `n` 成立的严格指数尾。因此本次 `no_certificate_found` 与这个方法边界一致，但有限搜索结果本身并不是“不存在证书”的机器证明。

`08_escape_200` 有正的不终止概率。源无条件成本尾把不终止运行的成本记为 `+∞`，所以不会衰减到 0；当前后端的事件却显式要求 `T<∞`。论文 Table 2 的 `P(C>=50)<=0.1`、`P(C>=90)<=0.05` 既不是本次求解结果，也不是用当前事件/时钟复现的数值。

`12_signed_cost_multiplicative` 保留原 `C := C ± 0.5*y` 与 `y := (0.5 或 1.5)*y`，因此终态仍有 `C=y`；但当前 tailbound 后端只对到达 failure 的 pCFG 时间建模。这里报告的 `no_certificate_found` 仅是 runtime 适配测试，不能声称已经支持或分析了 signed output cost tail。

## 报错来源、通用修正与回归

最初的实际兼容性缺口在分析语义层，而不是这些 benchmark 的文件名：旧实现会以 `Random initialization is not implemented` 或 `Random assignments require support-invariance certificates; not implemented` 拒绝随机初始化/循环内连续采样；确定性 `if` 生成的 `branch` CFG kind 也未列入可分析节点。只改输入绕过这些错误会改变概率语义，因此做了通用后端修正：

1. 为有限离散、Bernoulli、连续 Uniform 和 Normal 分布提供数学上的精确支持域；Uniform 使用闭区间多项式约束，没有离散化。每次采样分配独立的新符号，并在“源域 × 样本支持域”上证明目标不变量。
2. 直线初始化前缀现在允许随机赋值；对整个支持域验证初始化不变量，并以精确独立矩计算 `E[V_after_prefix]`，同时保留从程序入口开始的 `c^(-prefix_steps)` 时钟校正。`07` 的初始 `Uniform[0,1]` 因此不是被替换成常数。
3. 支持确定性 `branch` 节点，使 `08` 能按更新后状态进行分支；修正域相交时的变量合并，并对仿射等式做精确消元后再验证非负性。
4. 新增分布支持域、随机初始化期望、连续/离散随机更新不变量和确定性分支回归测试。修复后重新生成本报告引用的整套最终产物，避免沿用旧 `.pp` 的陈旧结果。

最终全量回归日志为 [runs/final_20261014/regression.log](runs/final_20261014/regression.log)：

```text
69 passed in 10.88s
```

最终批次每个非跳过实例均可解析、构建 CFG，并运行 tailbound 到 `proved` 或 `no_certificate_found` 这一正常终态；本批次实际均为后者。尝试级 `numerical_issue`、`unbounded` 和精确验证拒绝已由搜索流程记录并继续处理，不是未捕获异常；机器汇总中的 `unresolved_errors` 为空。

## 2026-10-14 补测：前两个例子仅搜索 D=1

按用户要求，仅对 `01_coupon2`、`02_coupon4` 补测，使用原 `.pp` 和现有后端，
指定 `--initial-degree 1 --max-degree 1`。其他参数沿用上面的默认预算和
`c∈{1/2,9/10,99/100}`；没有升到 D=2，没有改动输入或求解器代码。

```bash
python -m contractive_tool solve tailbound_benchmark_pack/pp/01_coupon2.pp \
  --goal tailbound --initial-degree 1 --max-degree 1 \
  --out-dir tailbound_benchmark_pack/runs/d1_20261014_0759/01_coupon2
python -m contractive_tool solve tailbound_benchmark_pack/pp/02_coupon4.pp \
  --goal tailbound --initial-degree 1 --max-degree 1 \
  --out-dir tailbound_benchmark_pack/runs/d1_20261014_0759/02_coupon4
```

解释器仍为 `contractive-frontend-test-20260814/bin/python`；许可证环境变量仍指向
`/home/sunzhouyue/mosek/mosek.lic`。以上命令须在该环境执行，复跑时换新输出目录。

| 实例 | 实际 D | c 参数点 | 求解尝试 | 结果 | 耗时 |
| --- | --- | --- | --- | --- | --- |
| `01_coupon2` | 1 | 3 | 6 | 6 次均为 infeasible；最终 no_certificate_found | 3.52 秒 |
| `02_coupon4` | 1 | 3 | 6 | 6 次均为 infeasible；最终 no_certificate_found | 15.39 秒 |

两个进程均返回 0，stderr 为空，停止原因均为 `max_degree`。没有数值候选、没有通过
验证的证书，因此不能输出 A 或指数尾界。每个 c 都尝试了 auto（本次使用 Handelman）
和 Putinar 编码，order=1。产物及源码 SHA-256 均已核对。

证据：[补测索引](runs/d1_20261014_0759/run_index.json)、
[两券 summary](runs/d1_20261014_0759/01_coupon2/summary.json)、
[四券 summary](runs/d1_20261014_0759/02_coupon4/summary.json)。
对应目录的 `analyses/tailbound/search_history.json` 和各次 `solver.log` 保存完整过程。

### 定位到的建模原因：完成收集的边界状态仍被包含在循环证明域

这次不只是观察 solver 状态，还检查了生成的原始多项式义务。当前转换只保留
`0<=c_i<=1` 的 box invariant，严格循环守卫 `sum(c_i)<m` 在 positivity 域处理中
变成覆盖域 `sum(c_i)<=m`。因此所有 `c_i=1` 的状态也必须满足循环内的收缩约束。
原程序在这个状态应立即退出，实际不会再抽券；但放宽后的证明域允许它进入循环，
且所有“将某个 c_i 设为 1”的更新均保持这个状态。

设 W 为循环头证书在全 1 状态的值，收缩因子为 c。沿两券的 3 条或四券的 4 条
循环边组合收缩条件，分别得到 `W<=c^3 W` 或 `W<=c^4 W`。由于 `0<c<1`，这要求
`W<=0`。与此同时，循环退出边和 `refute true` 边的条件要求 `W>=1/c^2>0`，直接矛盾。
这一矛盾与多项式次数无关；因此仅改变 D 无法修复当前证明域的问题。

对本次 `c=9/10` 的实际生成义务，已将全 1 状态代入，并用精确有理线性代数构造了
非负乘子，使收缩残差的加权和严格等于 `-1`。这独立确认了当前约束在该边界状态的
不可行性，不依赖 MOSEK 的数值判断。精确乘子和残差见
[两券诊断](runs/d1_20261014_0759/01_coupon2.boundary_diagnostic.json)、
[四券诊断](runs/d1_20261014_0759/02_coupon4.boundary_diagnostic.json)。

这是当前域近似过于保守造成的不可行，不是原程序没有指数尾界的证明。后续应在
证明变量始终只取 0/1 的基础上，正确编码离散循环域，例如将本例的继续条件等价为
`sum(c_i)<=m-1`，并保证各位置域归纳保持；不能对任意实数严格不等式直接减去 1。
本次没有实施这项域建模修改，也未声称修改后 D=1 已求解成功。


## 2026-10-14 修复复测：D=1 的一轮生存尾界

本节取代前面 D=1 补测的“修复尚未实施”状态，旧结果保留为问题定位历史。
修复了一轮计时、布尔循环域及生存证书边界，未改 c 网格、输入 `.pp` 或次数。
新通用编译器证明布尔域归纳保持，并检查一轮所有可行路径、精确概率及更新；
未完成 eta>=1，完成 eta=0。在完整有限状态域上建立 LP，由 CVXPY/MOSEK 合成并
精确验证多项式，结论对所有 n 成立，不是有限 horizon 求解。

| 例子 | D | c 参数点结果 | 已验证 eta | 选择的尾界 | 耗时 |
| --- | --- | --- | --- | --- | --- |
| 01_coupon2 | 1 | 1/2、9/10、99/100 均 proved | 2-c0-c1 | min(1,2*(1/2)^n) | 1.29 秒 |
| 02_coupon4 | 1 | 1/2 infeasible；9/10、99/100 proved | 4-c0-c1-c2-c3 | min(1,4*(9/10)^n) | 3.39 秒 |

两次进程均返回 0，stderr 为空。01 实际 3 次求解，02 实际 4 次求解（1/2 下有
两次编码尝试）；两者均比较完本次数的全部 3 个 c 后停止。使用 README 指定的
conda 环境与真实 MOSEK；可复现命令、源码/产物 SHA-256 和所有 solver 日志都已保存。

这里事件为 Pr[K>n]，K 为完整抽取轮数。01 的原始 pCFG 计数 T=2+3*K+2，02 为
T=4+4*K+2。终止性没有预先假定；生存证书推出几乎处处终止。该界也覆盖晚 failure，
但不替代 eventual assertion violation 求解。

独立精确检查枚举全部已验证布尔域（01 为 4 个状态，02 为 16 个状态），核对
归一化、完成态零值和所选 c 的收缩残差，并核对了全部 manifest 文件哈希。
01 的最大实际期望比值为 1/2；02 为 3/4，且所有未完成状态都有相同比值。
本次没有把 3/4 加入搜索网格，因此 02 正式搜索输出仍为 4*(9/10)^n。

- [运行索引](runs/round_d1_verified_20261014/run_index.json)
- [01 摘要](runs/round_d1_verified_20261014/01_coupon2/summary.json)、[01 独立检查](runs/round_d1_verified_20261014/01_coupon2.independent_check.json)
- [02 摘要](runs/round_d1_verified_20261014/02_coupon4/summary.json)、[02 独立检查](runs/round_d1_verified_20261014/02_coupon4.independent_check.json)
- [02 证书](runs/round_d1_verified_20261014/02_coupon4/analyses/tailbound/degrees/1/c-002/attempts/001/certificate.json)
- [全量回归日志：79 passed in 16.59s](../generated/round_backend_regression_20261014.log)

当前宏步编译器适用范围为已验证布尔入口域、无轮内采样/循环/提前退出；一般连续域
宏步尚未实现。auto 模式记录不支持原因后保留原 pCFG late_bad_exit 路径；显式
round_survival 模式会直接报告 unsupported，不会静默更换事件。此次未重跑其余 benchmark。


## 2026-10-14：改用 c 二分搜索后的 D=1 复测

默认使用 (0,1) 有理二分，每个次数最多 10 个参数点，未传入固定 c 网格。
其他设置和两个 `.pp` 均保持不变；仍使用一轮计时、已验证布尔域和生存证书边界。

| 例子 | D | 参数点 / 后端调用 | 已验证多项式 | 选择 c | 统一轮次尾界 | 耗时 |
| --- | --- | --- | --- | --- | --- | --- |
| 01_coupon2 | 1 | 10 / 19 | 2-c0-c1 | 1/2 | min(1,2*(1/2)^n) | 1.70 秒 |
| 02_coupon4 | 1 | 10 / 19 | 4-c0-c1-c2-c3 | 3/4 | min(1,4*(3/4)^n) | 4.68 秒 |

两次运行均为 proved，进程返回 0，stderr 为空。01 在首点 1/2 找到证书，后续更小
参数均报告不可行；02 在第 2 点 3/4 找到证书，其他更小参数报告不可行。
各自的最终搜索区间为 [511/1024,1/2]、[767/1024,3/4]。上端均已验证，下端仅由
当前编码的 solver infeasible 反馈维护，不宣称是原始多项式可行性的严格下界。

次数内搜索停止原因为 max_c_steps，任务停止原因为 first_successful_degree。
独立精确检查验证归一化、完成态零值、所有活动状态的 Pre_round(eta)=c*eta，
以及运行产物 manifest 哈希。两个例子均不需要增至 D=2。

- [命令及运行索引](runs/bisection_d1_20261014/run_index.json)
- [01 摘要](runs/bisection_d1_20261014/01_coupon2/summary.json)、[独立检查](runs/bisection_d1_20261014/01_coupon2.independent_check.json)
- [02 摘要](runs/bisection_d1_20261014/02_coupon4/summary.json)、[独立检查](runs/bisection_d1_20261014/02_coupon4.independent_check.json)
- [02 证书](runs/bisection_d1_20261014/02_coupon4/analyses/tailbound/degrees/1/c-002/attempts/001/certificate.json)
- [全量回归：90 passed in 18.47s](../generated/bisection_regression_20261014.log)

最大二分步数可通过 --max-c-steps 配置，原有全局参数点/时间预算仍可提前终止。
本次没有重跑其余 benchmark，assertion violation 仍只建模。


## 2026-10-14：默认 D=1 与剩余 benchmark 测试

测试前已将 framework、DegreePolicy、SearchOptions、CLI 和批量驱动统一为默认
D=1..6。批量驱动从当前 SearchOptions 获取并冻结配置，消除了原来硬编码 D=2 和
固定 c 网格的偏差。未修改任何输入 `.pp`；没有为其他例子添加专用证书或域假设。

使用 README 的 conda 环境、真实 CVXPY/MOSEK，执行：

```bash
python tailbound_benchmark_pack/run_tailbound_suite.py \
  --output-root tailbound_benchmark_pack/runs/default_d1_bisection_20261014 --jobs 3
pytest -q
```

每个实例默认 D=1..6；每个 D 最多 10 个 c 二分参数点，每点最多 2 次编码尝试；
每实例总参数点上限 32，总时间软预算 300 秒，单次 solver 时间上限 30 秒。
全局参数点预算可使搜索在 D=6 之前结束，不能把这些行理解为已完整排除 D<=6。
下表次数来自实际 search_history，而不只是配置上限。

| 实例 | 实际 D | 参数点 / 求解次数 | 状态 | 停止原因 | 耗时（秒） |
| --- | --- | --- | --- | --- | --- |
| [01_coupon2](runs/default_d1_bisection_20261014/01_coupon2/summary.json) | 1 | 10 / 19 | proved | first_successful_degree | 1.75 |
| [02_coupon4](runs/default_d1_bisection_20261014/02_coupon4/summary.json) | 1 | 10 / 19 | proved | first_successful_degree | 5.04 |
| [03_rw_int](runs/default_d1_bisection_20261014/03_rw_int/summary.json) | 1–5 | 32 / 64 | no_certificate_found | parameter_budget | 17.58 |
| [04_rw_real](runs/default_d1_bisection_20261014/04_rw_real/summary.json) | 1–5 | 32 / 64 | no_certificate_found | parameter_budget | 18.09 |
| [05_rdwalk_uniform_d1](runs/default_d1_bisection_20261014/05_rdwalk_uniform_d1/summary.json) | 1–6 | 32 / 64 | no_certificate_found | parameter_budget | 16.37 |
| [05_rdwalk_uniform_d5](runs/default_d1_bisection_20261014/05_rdwalk_uniform_d5/summary.json) | 1–6 | 28 / 56 | no_certificate_found | max_degree | 11.23 |
| [05_rdwalk_uniform_d10](runs/default_d1_bisection_20261014/05_rdwalk_uniform_d10/summary.json) | 1–6 | 21 / 42 | no_certificate_found | max_degree | 7.25 |
| [05_rdwalk_uniform_d20](runs/default_d1_bisection_20261014/05_rdwalk_uniform_d20/summary.json) | 1–6 | 21 / 42 | no_certificate_found | max_degree | 7.21 |
| [06_rw_real_large](runs/default_d1_bisection_20261014/06_rw_real_large/summary.json) | 1–6 | 14 / 28 | no_certificate_found | max_degree | 7.73 |
| [07_polynomial_tail](runs/default_d1_bisection_20261014/07_polynomial_tail/summary.json) | 1–6 | 28 / 56 | no_certificate_found | max_degree | 114.01 |
| [08_escape_200](runs/default_d1_bisection_20261014/08_escape_200/summary.json) | 1–6 | 20 / 40 | no_certificate_found | max_degree | 14.45 |
| [12_signed_cost_multiplicative](runs/default_d1_bisection_20261014/12_signed_cost_multiplicative/summary.json) | 1–4 | 32 / 64 | no_certificate_found | parameter_budget | 158.33 |

01、02 作为默认配置对照重测，D=1 分别恢复 `eta=2-c0-c1,c=1/2` 和
`eta=4-c0-c1-c2-c3,c=3/4`；它们的轮次尾界仍为 `min(1,2*(1/2)^n)` 和
`min(1,4*(3/4)^n)`。对返回证书逐一核对了全部布尔入口状态上的正性、零边界、
收缩条件和初值，没有依据数值 optimal 就直接宣告 proved。

其余 10 个实例均实际进入 D=1 求解并按预算升阶，但没有得到已验证证书。
它们均不满足当前布尔宏步编译器的适用条件，所以 auto 使用的是保留的
`late_bad_exit`（入口 pCFG 时钟）路径，不是已实现一般实数/整数域的一轮生存尾界。
具体原因也存入各 summary 的 round_compilation_diagnostic：

- 03：一轮更新不能保持布尔入口域；它的整数随机游走状态并不限于 0/1。
- 04、06：初态为 2、200000000，不符合当前布尔宏步初始化条件。
- 05 的四个参数实例、08、12：存在轮内采样，当前宏步编译器尚不支持。
- 07：初始连续随机样本不符合确定布尔初始化条件。

因此这些结果不能解读为“正确一般宏步模型已经证明多项式无解”。12 原规格的
signed accumulated cost 也仍不是本次 runtime tail 的求解对象；其原成本问题未求解。

全批共 280 个参数点、558 次后端尝试：proved 2，infeasible 473，numerical_issue 77，
solved_unverified 1，unbounded 5。数值未知和精确验证未通过不会作为 proved，也不会
被二分算法当作不可行反馈缩区间。所有进程返回 0，stderr 为空，无未处理异常。
09_rw_1d_demonic、10_rw_2d_demonic、11_rw_2d_variant 继续因非确定性跳过。

批次墙钟 195.32 秒，完整回归 **90 passed in 19.26s**。源码 SHA-256、全部产物哈希、
配置一致性以及每个实例确有 D=1 solver attempt 均已核对。

- [批次命令/时间/退出码索引](runs/default_d1_bisection_20261014/run_index.json)
- [汇总及独立核查结果](runs/default_d1_bisection_20261014/results.json)
- [全量回归日志](../generated/degree1_default_regression_20261014.log)

各实例目录内保留 search_history.json、逐 D 二分反馈、solver.json、solver.log 和
精确验证文件；logs/ 下保存每个进程的完整 stdout/stderr。历史结果均保留。
