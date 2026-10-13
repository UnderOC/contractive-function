# Contractive Function 框架：次数递增的多项式证书合成

更新日期：2026-10-14。本文与 0.4.0 实现同步；本轮修改前版本已备份为 `framework.md.bak.20261014_022326`。
Tail 后端已接入 CVXPY/MOSEK；assertion violation 当前仅生成约束，不调用后端。

## 1. 当前目标与默认行为

工具对支持的概率程序自动建立未知多项式，搜索其系数并验证概率上界。所有输入程序
的终止性默认未知，允许无限运行；不条件于终止，也不丢弃或重新归一化无限运行质量。

保留两个分析目标：

| Goal | 直接合成的多项式 | 输出 |
| --- | --- | --- |
| `tailbound` | 各位置的非负证书 V_l | 对全部允许整数 n 成立的 `A*c**n = A*exp(-lambda*n)` |
| `assertion_violation` | 各普通位置的非负证书 Theta_l | 当前生成约束；未来求最终 failure 概率上界 `Theta(initial)` |

现阶段采用整数幂对应的多项式路线：将原模板中的正整数 k 合并到最终证书的次数，
直接合成 V 或 Theta。不再枚举 k=1、2，不要求恢复低次 eta 的幂分解，不采用 L/U
比值包络。非整数 k 单独预留扩展接口，当前明确不支持，见第 7 节。

默认搜索流程：

1. 从最高总次数 D=2 的未知多项式模板开始。
2. 在当前 D 下，对固定参数点搜索系数，并有限尝试 positivity 策略和编码次数。
3. 若当前 D 没有已证明候选且还有预算，提高 D，默认步长为 1。
4. 在首个得到严格证书的 D 下，完成该次数计划内的候选比较，输出最佳已证明结果；
   默认不再提高 D。可选优化模式允许成功后继续提高次数。
5. 达到最大次数、轮数或时间预算即停止；没有证书时如实返回未找到。

“适用于任何问题”表示对能力范围内的输入统一尝试，不保证任意程序都有多项式证书。
增加次数也不保证一定成功。所有“最佳”均限定于已经尝试且严格验证的候选集合。

全流程使用 Python：前端、代数、证明义务、positivity、CVXPY、MOSEK、验证与报告。
指定 horizon 的独立时间层求解、特殊非多项式 Kelly scalar moment 求解均不属于当前
目标路径；n 只用于统一公式及其事后求值。

## 2. 整数幂如何合并到模板次数

### 2.1 从 eta 的幂转为最终多项式

原模板为 `V_l=eta_l**k`，若 eta 的最高总次数为 d、k 为正整数，则 V 的次数最多 kd。
当前直接使用：

```text
V_l(x; a_l) = sum_(|alpha|<=D) a_(l,alpha) * x**alpha
```

Assertion 同样直接设置未知多项式 Theta。所有系数由求解器决定，允许最高次系数为零。
默认使用全部程序变量；有依据的变量投影须显式配置并验证义务覆盖。

例如两个变量且 D=2 时：

```text
V_l(x,y) = a0 + a1*x + a2*y + a3*x*x + a4*x*y + a5*y*y
```

D 是最终证书的最高总次数。源模板 d=2、k=2 若按次数覆盖，对应 D=4，而不是再次
对合成出的四次多项式平方。无需按多个整数 k 反复生成同一个 D 的重复搜索。

### 2.2 候选族扩大，不是幂分解等价变换

任意 D 次多项式不一定是某个低次多项式的整数幂。例如 `x*x+1` 不是一次多项式的平方。
因此当前路线覆盖原整数幂族，并允许更多直接多项式证书。输出必须标记
`certificate_family=polynomial`，不能宣称恢复了一个并不存在的原始 eta 或 k。

若文档/显示层沿用 eta 名称，它指直接合成的最终 V，而非等待再次取幂的低次函数。
代码和产物优先使用 V/Theta，防止二次幂、前因子和收缩率被重复计算。

默认不再要求原低次 eta 的一阶收缩，同时也不尝试推导其 k 阶矩。最终证书自身满足：

```text
E[V_next | x] <= c*V_src(x)
```

这里 c 直接控制最终证书。旧版 c 与 rho_k 的区分不再出现在整数主流程中；若未来
恢复非整数幂模板，则由该扩展显式定义底层函数和最终证书的不同参数。

### 2.3 为什么内层可保持凸性

固定 c、程序更新、概率和分布矩后，V 及 E[V_next] 对未知系数 a 都是线性的。
`c*V-E[V_next]>=0` 的系数因此对 a 仿射，配合 SOS/Handelman 的系数匹配得到 LP/SDP。

c 与 V 系数不能在同一个内层模型中同时作为自由变量，否则 c*a 产生双线性。
所以保留外层 c 搜索、内层系数合成。

“直接多项式”不要求 V 自身是全空间 SOS；只要求在经过证明的程序域上非负。
Positivity 后端为这些域不等式寻找证书，不应额外限制 V 必须有某种低次幂分解。

## 3. 程序语义、全域证据与计时

### 3.1 前端和 grouped pCFG

复用现有 AST/pCFG，保留赋值、普通分支、prob、while、assume、assert、refute、随机
更新和 invariant annotation。更新采用 simultaneous substitution，保留源码和位置 ID。

一个概率选择的全部 branches 属于同一 transition group，期望必须按概率加权。
概率非负且和为 1、分布参数、fresh sampling、独立性及所需矩存在须有证明或明确假设。
支持域证据与有限阶矩是不同要求，不能互相替代。

正常终止 l_t 与 assertion failure l_f 分离。Assert 条件不成立进入 failure，refute 条件
成立进入 failure。Assume 的阻塞/拒绝语义须明确，不能自动条件化。未支持的程序语义
返回 unsupported。若支持同时启用的非确定性动作，逐个动作证明并注明 scheduler 范围。

### 3.2 全时域 invariant

位置域 I_l 来自源码 annotation；外部 provider 是后续扩展。验证初始覆盖、每条转移及随机支持下的归纳保持、
概率合法和期望存在。仅有假设而没有证明的 invariant 必须使结果明确带条件，不能
无条件标记原程序已证明。

不能使用某个有限 n 的可达域代替所有时间的 invariant，也不能为套用紧致域定理而
添加未证明的财富上界或球约束。无界域是正常输入，不保证能找到当前层级证书。

严格 guard 对多项式证明可取覆盖闭包；禁止用正 margin 缩域。析取完整拆分并限制
region 数量；仿射 equality 可消元，其余用 ideal multiplier。

整数路线证明 V>=0 即可，不需要为 log(V) 强加处处严格正性；坏集合归一化排除所需
位置上的无效零证书。用户选择严格正 margin 时须记录它是额外候选限制。未来非整数
路线的正性和奇点条件由其自身生成，不能倒灌到整数路线。

### 3.3 指数路径的时钟

当前固定使用从原程序入口开始的 pCFG transition 计数，普通转移增量为 1，终止后冻结。
因此局部规则是 `E[V_next] <= c*V_src`，不会对吸收 self-loop 强加严格收缩。

初值只来自源程序：执行控制流之前的确定性赋值/skip 前缀，检查其 invariant 和更新，
要求控制位置前所有程序变量都有精确有理初值。若消去的前缀有 p 步、控制位置为 s，
目标是 `A=c**(-p)*V_s(x0)`，不是直接使用 `V_s(x0)`。这样输出 n 仍以原入口计数，
对 n<p 也成立。程序无需传入 initial、initial_location、事件或 horizon 参数。

当前用精确 Farkas 恒等式验证闭包域的归纳保持与概率范围；无法证明则返回 unsupported。
随机赋值/声明 fresh sample 的支持域验证和 assume 的阻塞语义尚未接入此证书路径，
前端和矩计算保留对应能力；不能将“能计算随机矩”误当作已证明全时域支持域。

循环轮次、零增量边和宏步是未来扩展。届时须提供计数证据，并使用
`sum_j p_j*E[c**(-delta_j)*V_dst_j] <= V_src`。当前不接受这些未实现的时钟配置。

## 4. 统一指数尾界的证明规则

### 4.1 事件和边界

首版支持 `late_bad_exit`。T 表示原程序有限终止时刻（允许∞），N_T 表示其完成的
时钟计数（当前 N_T=T），B 是程序 assert/refute 定义的 failure terminal：

```text
Pr[T<infinity, N_T>n, terminal_state in B] <= A*c**n
for all integers n>=0
```

该事件不条件于终止，也不计入无限运行路径。累计“截至 n 已发生坏事件”的概率不能
使用趋于零的统一指数衰减规则。可能不终止时 `Pr[T>n]` 也不能默认满足该式。

每个需要模板的位置直接合成 V_l，要求：

```text
V_l >= 0 on its full invariant domain
V_terminal >= 1 on B
```

非 B terminal 可用非负多项式，或使用覆盖完整域的固定分片边界 V_bad=1、V_good=0。
固定分片由事件域决定，不含待合成参数。进入终止的概率分支必须参与局部期望，
终止之后不生成严格收缩义务。归一化阈值默认为最终 V 的 1，无需再引入未知 H 或 k。

### 4.2 固定次数、固定 c 的模型

在固定 D、c、invariant、clock 下，联合合成全部位置 V 的系数以及 positivity 乘子：

1. 非负性和 terminal event 归一化。
2. 第 3.3 节完整的加权局部收缩式。
3. 最小化原入口的 `A=V_initial(x0)`；消去 p 步确定性前缀时等价使用
   `A=c**(-p)*V_after_prefix(x0)`。该目标对决策变量线性。

每个 c 参数点单独求解，数值结果经过严格验证后才进入结果集。最终保留原程序事件、
时钟、位置多项式、A、c、lambda 和全部证明来源。

### 4.3 对全部 n 的结论

令 X_t 包括程序位置和状态。局部条件保证停止后的过程

```text
M_t = c**(-N_(t wedge T))*V(X_(t wedge T))
```

是非负超鞅。终止后 V 和时钟冻结，由有限截断及非负性/Fatou 得：

```text
Pr[T<infinity, N_T>n, terminal_state in B]
 <= V(initial)*c**n
 = A*exp(-lambda*n), lambda=-log(c)>0.
```

无需几乎处处终止。内部保存精确 A、c 及符号 `-log(c)`；浮点 lambda 仅作展示，
不可因舍入输出未经证明的更快衰减率。域、模板和参数搜索均与 n 无关。

## 5. Assertion Violation 的证明规则

当前只生成首个 D/c 参数点的直接多项式和严格前不动点义务，返回
`not_solved: assertion_backend_not_implemented`；以下概率界输出和模式选择属于后续实现。

目标保留为最终 failure 概率：

```text
Pr[exists finite t: location_t=l_f] <= Theta(initial)
```

普通位置直接合成非负多项式 Theta，边界为：

```text
Theta_normal = 0
Theta_failure = 1
E[Theta_next | location,x] <= Theta_src(location,x)
```

包含正常 0 和失败 1 的分支常数，不可漏掉进入终止的分支。由非负 pre-fixed-point
和有限步 failure 概率的递增极限得到最终上界，允许无限运行，不需要预先证明终止。

原 `Theta=q_l*eta_l**k` 中，正整数幂和正缩放统一包含在直接多项式族中。默认不再
搜索 q、低次 eta 或整数 k，也不宣称恢复 factorization。优化目标是线性的
`minimize Theta(initial)`，输出值不再取一次 k 次幂。

为延续用户要求的 c 搜索，默认 `synthesis_rule=contractive_prefixed_point`：对每个普通
源 transition group、固定 `0<c<1`，使用更强的

```text
E[Theta_next] <= c*Theta_src.
```

该条件蕴含原始前不动点；终止后不要求严格收缩。它是合成策略的附加限制，并不是
violation 上界定理的必要条件，失败时必须说明搜索使用了这一限制。

未来实现 assertion 后端时可增加 `synthesis_rule=prefixed_point`，直接使用系数 1 的原始条件，此时不搜索 c，
仍执行相同的次数递增、positivity 和严格验证流程。不得在严格模式失败后未经配置
自动切换规则。两种模式均只输出 violation 常数界，不把 c 宣称为终止时间衰减率。

Assertion 的规则覆盖所有原始 ordinary transitions；若使用宏步，须证明不会越过中间
failure 而遗漏概率。Tail 时钟规则不能自动替代 assertion 的全部前不动点义务。

## 6. 次数递增、预算与结果选择

### 6.1 两种次数及默认设置

| 参数 | 作用 | 默认/要求 |
| --- | --- | --- |
| `initial_degree` | 最终 V/Theta 的起始最高总次数 | 2 |
| `degree_step` | 无证书时的次数增量 | 1 |
| `max_degree` | 模板次数上限 | 默认 6，范围 0..10 |
| `c_values` | 每个次数使用的精确固定网格 | 1/2、9/10、99/100 |
| `max_parameter_points` | 总参数点预算 | 32 |
| `max_attempts_per_point` | 每个 D/c 的编码尝试上限 | 2 |
| SOS order r / Handelman degree | 非负性证明编码复杂度 | 与模板次数独立设置 |
| `continue_after_success` | 首个成功次数后是否继续升阶 | false |

当前模板次数不足与非负性编码能力不足是两种原因。固定 D 后先有限搜索 c 和策略/
编码次数；只有本次数预算内未得到已证明候选，才默认提高 D。

SOS 最小次数取决于实际 obligation，包括多项式更新的复合和概率乘积，不能简单设为
D/2。编码次数上限不够时报告诊断；不能静默生成缺少高次系数的模型。更高 D 通常
需要更高编码次数，配置冲突不能当成数学不可行。

D+1 的完整多项式族包含 D 的族，因为新增系数可以为零；但有限 c 网格、不同编码/
预算和数值结果不保证各次运行表现单调。不能由一次求解失败推断更高次数必失败。

### 6.2 有限搜索算法

```text
all_proved = []
for D in degree_schedule(initial_degree, max_degree, degree_step):
    current_proved = []
    for c in fixed_rational_grid within global parameter/time budgets:
        create all location polynomials of degree <= D
        build full goal obligations with fixed c
        try supported positivity strategies/orders within point budget
        if numerical candidate passes complete rigorous verification:
            save coefficients and recomputed bound
            add to current_proved and all_proved
        otherwise record failure/unknown without deleting proved results
    if current_proved and not continue_after_success:
        return select_best(all_proved), stop_reason="first_successful_degree"
    stop global search if time/model/global budget is exhausted
if all_proved:
    return select_best(all_proved), actual_stop_reason
else:
    return no_certificate_found, scope_and_failure_reasons
```

控制要求：

- 搜索轮数是外层调度轮数，不是程序执行次数 n，也不是 MOSEK 内部迭代次数。
- 当前 D 出现首个 proved 时，默认完成该次数计划内的候选搜索，或直到预算结束；
  不直接将第一个数值 optimal 当成最终结果。
- 默认在首个成功 D 停止升阶；`continue_after_success=true` 才继续更高 D，且保留旧证书。
- c 首版使用 (0,1) 内的精确有理网格，后续可扩展细化策略；禁止把失败/超时当作不可行证据
  做不可靠二分。Assertion 的纯 pre-fixed-point 模式只有一个系数 1 参数点。
- 对 infeasible relaxation、数值问题或验证失败可有限重试，随后报告其含义。
- 许可证缺失、语义不支持、配置/建模错误等无法通过升阶解决的问题，应停止受影响
  job 并报告原因，不盲目提高 D；其他独立 job 可以继续。
- 总预算到期立即在可中断边界停止；若已有证书仍返回它及实际覆盖范围。符号运算
  只有阶段边界检查时，须明确总时限是软预算。

### 6.3 “最佳”及无解报告

Assertion：选择所有已证明候选中最小的 Theta(initial)。

指数尾界：默认 `fastest_decay_then_prefactor`，先最小 c，再最小 A。同时保留相同事件/
时钟/初态下未被支配的 (A,c)，可输出下包络 `min_i A_i*c_i**n`。下包络不一定是
单一指数。只有 A 与 c 均不大于另一候选时，才可据此删除被支配者。

默认输出是首个成功次数内、实际搜索范围中的最佳已验证证书，不保证所有次数或
每个 n 的全局最优。可选继续升阶模式扩大搜索范围，也不改变这一限定。

状态包括 `proved`、`not_solved`、`solved_unverified`、`no_certificate_found`、
`unsupported` 以及 attempt 级建模/solver/验证失败。记录 max_degree、实际 degree 列表、
c 参数点、策略/编码次数和 stop_reason。只有独立证明才能声明某个候选族确实不存在；
“没有找到”不能变成“程序不 contractive”。

## 7. 非整数 k 的预留扩展

### 7.1 独立证书族与接口

当前 `certificate_families.py` 提供 PolynomialFamily 和显式拒绝的 FractionalPowerFamily。
非整数族不导入求解依赖。未来完整扩展接口如下：

```text
CertificateFamily:
    id
    available()
    supports(goal, program, spec)
    instantiate_template(spec)
    generate_obligations(goal, template, fixed_parameters)
    validate_candidate(candidate, evidence)

PolynomialFamily:            当前已实施的整数合并路线
FractionalPowerFamily:       预留，当前 available=false
FractionalKPolicy:           预留未来固定非整数候选/自动选择算法
```

非整数扩展与当前多项式模块隔离；完整 lazy registry 留待扩展实现。未实现时不影响多项式路径。
显式请求非整数族时给出 `fractional_k_not_implemented` 配置诊断（CLI 退出码 2）。不得取整 k、
自动换成多项式路线、用浮点接近整数来决定数学语义，或静默忽略该配置。

### 7.2 未来 spec 及待研究事项

预留 `FractionalPowerSpec`，记录正非整数 k 的精确表示或可靠数值规格、底层 eta 次数、
定义域、归一化和目标规则。未来的 `base_degree` 与当前最终多项式的 `degree` 是不同
含义；两种 spec 分开类型化，不在同一个配置中含混解释。

未来再分析：

- eta 的正性、非整数幂的实数定义域、零终止边界与奇点；
- 分数幂期望存在性及合适的前不动点条件；
- 0<k<1 与 k>1 非整数的不同凸凹性，禁止误用 Jensen；
- 候选生成、可靠凸界或非凸求解方法，以及最终严格验证；
- 底层 eta 的收缩率与最终幂证书速率是否需要分别搜索；
- 证书是否能进入现有 LP/SDP，或需要另行开发能力受控的 backend。

现在只预留职责和数据位置，不承诺算法，不默认启用包络、特殊矩捷径或非凸求解。
旧 `analysis/k_policy.py` 不能直接作为新多项式流程的 k={1,2} 调度器；后续将其解耦，
保留清晰的扩展接口或迁移诊断，不改变本轮源码。

## 8. Positivity 编码与 CVXPY/MOSEK

### 8.1 三种独立策略

每个策略消费固定半代数域 `g_i>=0,e_j=0` 上的 `h>=0`，输出后端无关 fragment。
系数对未知模板/乘子仿射，domain generators 不含待合成参数。

| 策略 | 非负性表示 | 模型 |
| --- | --- | --- |
| Putinar | `h=sigma0+sum sigma_i*g_i+sum tau_j*e_j` | SOS/SDP |
| Schmüdgen | SOS 乘平方自由 generator 产品，加 equality ideal | SDP |
| Handelman | 固定仿射 generators 的非负系数产品组合 | LP，首版仅识别出的有界域 |

先处理空域、常数、恒等式和可消元 equality。Auto 可在有界仿射域优先 Handelman，
其他域先 Putinar，再尝试 Schmüdgen。条件未知保持 unknown；缺失可选分析/排序模块
时使用保守静态顺序。只启用 Putinar 也可以运行其支持范围内的完整路径。

Registry 区分模块缺失、关闭和输入不支持，未知拼写报配置错误。失败 fragment 整体
丢弃；必须保证全部 obligations 由共享同一组模板系数的联合模型覆盖。

找到并严格验证的 SOS 表示在无界域上也可构成充分证明，但不因此声称满足相关定理
的 Archimedean/compactness 完备性条件。不得添加无证据的球约束，也不保证升阶成功。

### 8.2 建模与预算

复用 Gram 展开、系数匹配和 ConicModel。上三角非对角项乘 2，匹配包含零目标系数的
全部单项式；equality multipliers 自由，Handelman 系数非负且含空乘积。

CVXPY 只创建模板系数、乘子和 Gram 决策变量；程序状态只参与符号计算。检查 DCP，
MOSEK 解通过能力检查的模型。整数合并后的路线不需要 rank-one 约束、整数 k 平方
系数等式或 L/U 辅助搜索。

分别限制模板次数、SOS order、参数点、attempt、DNF/product 数、PSD dimension、
决策数和时间；符号展开前检查组合规模。编码 order 不足或资源上限阻止完整模型时，
报告能力/预算诊断，不能删除义务后求解。

环境沿用 README 的 `contractive-frontend-test-20260814`。现有 solver extra 为
CVXPY 1.9.3、NumPy 2.4.6、SciPy 1.17.1、MOSEK 11.2.6。Model-only 不求解且不依赖
许可证；日志保留 raw status、参数与数值目标，但不能仅以 optimal 标记 proved。

## 9. 严格验证与输出

验证层依次检查：

1. 初态覆盖、归纳域、概率/分布/矩、事件和时钟或宏步证据。
2. 当前 goal 的全部非负性、收缩/前不动点和边界约束，共享同一组系数。
3. 精确系数恒等式、非负系数和 PSD；数值候选可经有理重构后再验证。
4. Tail 的 c∈(0,1) 及停止论证，或 assertion 的两个边界和最终 failure 概率论证。
5. 从最终 V/Theta 系数直接计算 A/violation bound，验证选择比较、lambda 表达与求值。

当前不验证“V 是 eta 的整数幂”，因为那不是新模板的要求。输出系数就是最终证书
的系数。任何修改都须重新验证全部义务；旧时间层的倒序修正不能用于位置循环证书。

有限支持抽样不是全域证明。未经严格验证不能通过截断到 [0,1] 制造概率上界。
有证明的概率界可与 1 取最小值显示，同时保留原始公式与精确参数。

产物按 job -> degree -> parameter_point -> encoding_attempt 隔离，记录：

```text
source / pCFG / domain_evidence / clock_evidence
polynomial_template / obligations / encoding_plan / conic_model
solver.json / solver.log / certificate.json / verification.json
search_history / stop_reason / selected_bound / other_proved_candidates
optional evaluations / manifest with versions, assumptions and hashes
```

未知模板、最终系数、degree、c（适用时）、实际编码次数和原始义务映射均可追溯。
`evaluate` 只读取已验证公式代入 n，不修改域或模板、不调用 MOSEK。

## 10. 实际模块职责

| 模块 | 当前职责 |
| --- | --- |
| `frontend/`、`cfg/`、`algebra/`、`expectation.py`、`probability/` | 源码/pCFG、精确多项式及分组期望 |
| `analysis/semantics.py` | 源码初值、前缀轨迹、闭包域与归纳证明 |
| `analysis/templates.py` | 全变量最终多项式基与未知系数 |
| `analysis/degree_policy.py` | 次数范围、步长、成功后继续选项 |
| `analysis/parameter_search.py` | 有限精确 c 网格；未来可替换参数策略 |
| `analysis/certificate_families.py` | 直接多项式族与非整数族占位 |
| `analysis/goals.py` | Tail/assertion 边界、收缩/前不动点义务和目标 |
| `analysis_pipeline.py` | 有界调度、证明后选择、日志隔离和 manifest |
| `positivity/` | 可选策略 registry、域处理、SOS/LP 系数匹配 |
| `backends/cvxpy/` | DCP 建模、MOSEK、精确有理/PSD 验证 |
| `cli.py` | 仅源程序和目标必填；已证明公式求值 |

旧 finite_tail、reachability、k_policy、tail_pipeline、scalar goal、时间层修正模块已删除。
不会读取旧生成产物作为输入，也没有按文件名或 wealth 变量识别 Kelly 的分支。

## 11. 当前 CLI 和有限默认预算

```bash
contractive solve kelly_unbounded.pp --goal tailbound
contractive solve kelly_unbounded.pp --goal assertion_violation
contractive build-model kelly_unbounded.pp --goal tailbound --out-dir generated/model
contractive evaluate generated/solve --n 100
contractive strategies list --json
```

只有源程序与目标必填；默认输出路径为 `generated/<stem>_<goal>_<timestamp>/`。
`analyze` 与 `build-model` 都只生成模型，`solve` 执行 tail 搜索。显式输出目录须为空。
Assertion 的三种命令都只生成 polynomial_problem，不创建 conic 模型或调用 solver。

可选预算不改变输入事件/初态语义：

- `--initial-degree 2 --max-degree 6 --degree-step 1`；
- `--c-values 1/2 9/10 99/100 --max-parameter-points 32`；
- `--strategy auto --enabled-strategies putinar schmudgen handelman`；
- `--max-order 4 --max-attempts-per-point 2`，SOS order 至少覆盖实际 residual 次数；
- `--max-products 256 --max-psd-dimension 80 --max-decisions 20000`；
- `--total-seconds 300 --per-attempt-seconds 30`；
- `--continue-after-success` 可选；`--family fractional_power` 当前明确拒绝。

Auto 每条义务先尝试适用的 Handelman，再 Putinar/Schmüdgen；无界域不伪造紧致性。
同一 D/c 的重复计划去重；预算内可换策略或增加编码 order。模型/符号阶段间检查软时间
预算，MOSEK 有 optimizer 时间限制。所有数值未知/验证失败均记录，不能当作数学无解。
许可证/依赖错误停止搜索。退出码 0 表示完成（含 no_certificate_found/not_solved），
3 表示 solver 环境错误或语义不支持，2 表示配置/源程序错误。

`evaluate` 不求解，只代入已验证公式；数值 n 支持 0..10000，统一数学结论仍对所有
非负整数成立。浮点值仅展示，内部保留有理参数及精确求值；可与 1 取最小值。

## 12. 样例与验收标准

### 12.1 样例角色

Kelly 与其他程序一样，直接建立未知多项式，从 D=2 开始搜索 c，必要时升阶。
旧 `wealth**(-1/2)` 证书不作为 fallback；其存在不代表直接多项式族可行。

对 wealth-only、单循环头、完整无界域 w>=0.5 的非零非负多项式 V，若最高次系数
为 a_d>0，大 w 时两个分支都继续运行，收缩要求蕴含：

```text
0.6*1.2**d + 0.4*0.8**d <= c.
```

d=0 时左侧为 1；整数 d>=1 时至少为 `1.04**d>1`，所以这个限定候选族不存在 c<1
的证书。不能将此论证未经证明推广到多变量或不同域/规则，但它说明升阶不保证成功。
不得为了让样例成功而改变事件、使用有限时域包围域或换成固定非多项式证书。

验收需要具有已知多项式证书的正例、低次数失败但更高次数成功的例子，以及预算内
确实未找到的例子；不能只以 Kelly 是否成功判断实现正确性。

### 12.2 本轮范围与后续扩展

本轮完成直接多项式、次数/c 搜索、可选 positivity、真实 MOSEK、精确验证、公式求值、
新 CLI 和日志。Assertion 仅保留建模接口；非整数族、一般随机支持域验证、宏步时钟、
自动 c 网格细化与多 job 配置解析留待后续实现。真实测试和运行记录以 README 为准。

### 12.3 必需测试

- 默认 D=2、最高总次数、可配置步长/上限、允许高次系数为零；不把结果再次取幂。
- 原整数幂对应的 V 被次数族覆盖，但一般多项式不被误标为 eta**k 的因式分解。
- D 与 SOS order 独立，更新导致 residual 次数增长时匹配完整；编码不足明确诊断。
- 当前 D 无证书后升阶；首个成功 D 内比较后默认停止；继续优化模式保留旧证书。
- 最大次数/轮数/时间停止、部分候选失败、已有 proved 不被后续失败覆盖。
- 许可证/语义/配置错误不盲目升阶；数值失败不等于不存在证书。
- Tail c∈(0,1)、符号 lambda、初始化前缀计时、停止后冻结、统一所有 n。
- Assertion 正常 0/失败 1、严格前不动点义务、后端未实现时不调用 solver。
- 缺失可选策略、完整覆盖、Gram 因子、JSON 重建、精确 PSD 和原始义务验证。
- 真实 MOSEK LP/SDP 与无许可证 model-only；optimal 与 proved 分开。
- `evaluate_at` 不改变模型或搜索，不调用 solver；结论不依赖有限支持抽样。
- 显式非整数族返回未实现诊断，不取整、不降级、不强制加载缺失插件。
- 保留既有 parser/pCFG/expectation 回归；历史时间层专用测试随代码迁移单独处理。

## 13. 与理论文档的对应和后续边界

本设计将 `project_detail.md` 中正整数幂证书包含在直接多项式 V/Theta 的更大候选族中，
不再同时合成“底层 eta 的一阶收缩”与“eta**k 的矩收缩”。c 直接对应最终证书，
尾界 A 直接取 V(initial)，assertion 界直接取 Theta(initial)。

理论文档末尾 `Pr[violate by n]` 的指数衰减写法仍需在未来单独同步事件语义；当前采用
明确的 late_bad_exit 和独立的 eventual assertion violation 规则。终止性未知的处理
依靠非负停止/前不动点论证，不等于任意输入一定有有限次数的证书。

非整数 k 保留独立讨论和实现位置，其数学条件及求解算法尚未确定。未知 eta 的
非整数幂不能直接假装为多项式，也不默认恢复此前 L/U 包络或特殊 scalar 路线。

理论文档暂不改动；新实现的数学事件语义与能力边界以本文及实际产物为准。
