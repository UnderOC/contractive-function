# 独立倒数幂尾界分析

本入口以一阶、二阶矩的充分条件构造倒数势函数。独立入口继续可用；现在也接入
`contractive solve --goal tailbound` 的符号轮级工作流，以独立预算搜索分母。
倒数模块本身不调用已有多项式/Cauchy 分析搜索，也不依赖它们先找到证书。
主流程配置及比较语义见 [符号工作流说明](symbolic_workflow.md)。
复用现有前端、不变量验证、有限随机宏步编译、标量及矩阵正性编码、MOSEK、
有理证书修复与精确验证，以及有理幂的向外包围运算。

## 数学规则与合成方式

在活动域 `I ∩ G` 上合成多项式分母 `eta`，归一化 `eta(initial)=1`。
实现采用更强的 `epsilon <= eta <= b`，默认 `epsilon=1/1000`；
它是严格正性的充分条件，可能漏掉只有 `eta>0`、没有统一正下界的解。
退出后势函数置零：

```text
V(x) = (b/eta(x))^k    当前仍在循环中
V(x) = 0              已经退出
```

逐一尝试 `c_seed>1, r_seed>0`，对多项式系数建立线性/SOS 义务：

```text
eta(initial) = 1
eta >= epsilon, b >= eta                 活动域上
E[eta'] >= c_seed*eta                    活动域上
eta' >= r_seed*eta                       每个正概率原始后继上
```

以最小化 `b` 为目标求解，并精确验证。固定所得 `eta` 后，分别最大化 `c`、
最大化 `r0`、最小化 `D`，证明：

```text
E[eta'] >= c*eta
eta' >= r0*eta
E[(eta')^2] <= D*eta^2, D >= c^2
```

以上是初始候选生成过程。2026-11-08 起，默认在此之后继续执行下述自适应 k 搜索
和有预算的矩阵约束反馈。这是一种分阶段、有预算的搜索，不是全局联合优化或完备算法。
默认增长参数为 `1+2^(-j), j=1..7`；可显式提供其他参数和模板次数、变量。

这些矩与支撑义务**包括终止后继**。零/负终止后继会使本充分条件失败，
但程序仍可能具有尾界；实现不会在这些后继上计算倒数。
本版没有实现 §3.1 的直接截断负阶矩认证，不能将充分条件失败解释为没有尾界。

状态条件分支由共享宏步编译器拆为覆盖区域，各区域保留完整原始后继分布。
分母、b、c、r0、D 在全部区域之间共享；增长、支撑、二阶矩以及固定 D 矩阵约束
分别在每个区域上编码后联合求解。反馈也重新构造所有区域约束。
已有 k 自适应优化和反馈参数规则不变，证书重放从源码重建区域及每个约束。

对每组已验证常数按原文计算：

```text
p = (D-c^2)/(D-2*r0*c+r0^2)
z = (D-r0*c)/(c-r0)
q(k) = p*r0^(-k) + (1-p)*z^(-k)
Pr(K>n) <= min(1, b^k*q(k)^n), n=0,1,2,...
```

这里只接受 `c>1, 0<r0<c, D>=c^2` 和经向上包围后仍严格小于 1 的 `q`。
若已证明的 `r0>=c`，先将支撑常数减弱为 `c/2`，避免公式奇点；
`D=c^2` 时自然得到 `p=0, z=c`。`K` 是完整循环体执行次数。
求值时按给定 `n` 选择所有已验证候选的最小上界，不预设终止性。

## 三阶段改进

### 1. 自适应指数搜索

固定分母和矩参数后，`q(k)` 及 `log(q(k))` 都是凸函数。新模块
`analysis/reciprocal_exponents.py` 二分搜索单调导数的零点：

- 衰减率目标：`d log(q(k))/dk = 0`。
- 完整尾界目标：`log(b) + n*d log(q(k))/dk = 0`，默认 `n=20,100,1000`。

先检查 `[0,1]`，必要时倍增右端点至 `--k-upper`（默认 8），然后最多二分 24 次。
单调下降或确定性退化情况选择有限上端点，初始导数非负时只记录搜索诊断。
导数和对数以 60 位精度用于提出候选，**不作为收缩或不可行性的证明**。
将候选转成有理数，并检查相邻有理点；默认分母预算 256，幂的分子/分母均不超过 2048。
旧网格候选始终保留；每个新 k 都重新经过精确整数根幂包围，只有认证的 `0<q<1` 才输出。
`--no-adaptive-k` 恢复原固定网格。`--target-ns` 改变优化关注的 n，
但得到的每条证书仍然对所有非负整数 n 成立。

### 2. 固定 D 的分母合成

可用 `--moment-values` 指定 D 网格，与增长、支撑参数组成三元组；过滤 `D<c_seed^2`。
在合成 eta 的同时增加 `E[eta'^2] <= D*eta^2`，以如下有理矩阵在整个活动域上的正性编码：

```text
M[0,0] = D*eta
M[0,j] = M[j,0] = p_j*eta'_j
M[j,j] = p_j*eta                     j=1,...,m
其他元素 = 0
```

零概率分支先移除；`eta>=epsilon>0` 独立证明。下方对角块为正定矩阵，
Schur 补乘 eta 恰好为 `D*eta^2-sum(p_j*eta_j'^2)`。
固定 D 时，矩阵元素对 eta 的未知系数仿射；由现有 matrix SOS 模块编码，
不使用概率平方根或有限状态采样替代全域证明。`--matrix-degree` 控制矩阵乘子的次数。

矩阵阶段成功后，seed 三元组本身即是完整矩证书。后续分别收紧 c/r0/D 时，
只选更强的已验证常数；遇到 unknown 或时间预算耗尽，保留有效 seed，而不丢弃整个候选。

### 3. 有预算的参数反馈

默认 `--feedback-points 12 --feedback-seconds 60 --feedback-step 1/4`。
反馈同时受总分析软预算（默认 120 秒）限制；零点数或零秒数关闭反馈。
固定 eta 对照不执行分母反馈。

以 `max(target_ns)` 下完整认证尾界最好的候选作为父候选，循环尝试三个方向：

1. 增加增长下界，同时适当放宽支撑和二阶矩目标。
2. 降低二阶矩目标，同时适当放宽增长和支撑目标。
3. 提高支撑目标，同时适当放宽增长和二阶矩目标。

每个方向允许 b 在父候选的 `b*(1+step)` 内增大，新模型仍最小化 b。
参数量化为有理数，避免系数不断膨胀；每次重新证明所有约束。
新 eta 再经过矩参数收紧及自适应 k 搜索，按完整尾界决定该方向是否改善。
未改善/unknown 时只将该方向步长减半，不声称获得了数学不可行区间。
不重复相同三元组与 b 上限；所有已认证候选保留，即使对当前目标 n 不占优。
没有收缩候选但有完整矩证书时，也会按数值评分尝试反馈；没有已验证父模型时停止。

`feedback_history` 记录父候选、方向、步长、目标 n、是否改善和终止原因。
独立验证重建父候选及每个新矩阵模型，检查参数确实由其父候选生成。
这是局部启发式搜索，不能保证每个样例改善，也没有自动升阶或全局最优保证。

## 使用

在项目目录中，使用已有环境：

```bash
conda activate contractive-frontend-test-20260814

python -m contractive_tool.reciprocal_cli run kelly_double_bound.pp \
  --out-dir generated/reciprocal_kelly_new

# 只在指定程序变量上合成二次分母
python -m contractive_tool.reciprocal_cli run kelly_double_bound.pp \
  --degree 2 --variables wealth --out-dir generated/reciprocal_kelly_d2_new

# 固定分母作为对照；b,c,D,r0 仍由求解器求出并认证
python -m contractive_tool.reciprocal_cli run kelly_double_bound.pp \
  --eta wealth --out-dir generated/reciprocal_kelly_fixed_new

python -m contractive_tool.reciprocal_cli verify generated/reciprocal_kelly_new

python -m contractive_tool.reciprocal_cli evaluate generated/reciprocal_kelly_new --n 1000

# 原始流程，作为同环境基线
python -m contractive_tool.reciprocal_cli run kelly_double_bound.pp \
  --no-adaptive-k --feedback-points 0 --out-dir generated/reciprocal_baseline_new

# 只启用阶段 1
python -m contractive_tool.reciprocal_cli run kelly_double_bound.pp \
  --feedback-points 0 --out-dir generated/reciprocal_stage1_new

# 阶段 2 的受控实验：指定矩参数，但 eta 的系数仍自动求解
python -m contractive_tool.reciprocal_cli run kelly_double_bound.pp \
  --growth-values 26/25 --support-values 4/5 --moment-values 28/25 \
  --feedback-points 0 --out-dir generated/reciprocal_stage2_new

# 增加全自动反馈预算，无需指定 eta 或矩参数
python -m contractive_tool.reciprocal_cli run kelly_double_bound.pp \
  --feedback-points 24 --out-dir generated/reciprocal_stage3_24_new
```

输出目录必须为空或不存在。`result.json` 保存源文件哈希与宏步证据、模板与配置、
所有尝试、各阶段的模型/数值求解状态/有理验证值，以及所有有效 `k` 的尾界。
`verify` 从当前源码重新编译并重建义务，核对精确系数等式、非负性、PSD、
矩常数、幂包围和最终公式，不调用求解器。`evaluate` 首先执行同样的验证。
新产物使用 schema_version=2；原 schema_version=1 的固定网格产物仍可独立重放。

状态为 `proved` 时退出码为 0；未找到证书或前端语义不支持时退出码为 3；
无效选项、输入/文件错误为 2。`no_certificate_found` 不是数学不可行证明，
`unknown`、数值失败和时间预算耗尽都不能当作不存在尾界。

为避免大整数文本展开，求值结果 `upper_bound_exact` 是向上取整后的精确有理上界
（默认粒度 `10^-12`），`upper_bound_approx` 是其浮点显示；
`exact_expression` 保留所选证书在该 `n` 下的幂表达式。求值支持 `0<=n<=10000`。

Python API：

```python
from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.reciprocal import ReciprocalOptions, search_reciprocal, evaluate
from contractive_tool.analysis.reciprocal_verification import verify_result

round_ = prepare_random_round('kelly_double_bound.pp')
result = search_reciprocal(round_, options=ReciprocalOptions(variables=('wealth',)))
if result['status'] == 'proved':
    assert verify_result(round_, result)['status'] == 'proved'
    print(evaluate(result, 100))
```

## 范围与复现实验

当前复用的宏步编译器支持确定初始化、非嵌套无环循环体、常数概率分支、状态条件分支及有限离散
独立采样；连续采样、随机初始化、轮内提前退出，以及现有内核不能处理的新采样值相关守卫仍不支持。
源码需具有现有前端要求的 `assert/refute` 标记和能验证的不变量。
证明域使用严格守卫的闭覆盖，因此可能保守。总时间预算为协作式检查，
优化器另有单次时间限制，不承诺抢占符号计算。

已有样例的批量复现入口：

```bash
conda run -n contractive-frontend-test-20260814 \
  python examples/run_reciprocal_suite.py --out-dir generated/reciprocal_suite_new

conda run -n contractive-frontend-test-20260814 \
  python -m pytest tests/unit/test_reciprocal.py tests/integration/test_reciprocal_search.py -q
```

批量脚本运行原始输入，不修改样例；每例 30 秒分析软预算和 90 秒外部超时保护。
实测结果见 [论文实验索引](../experiments/paper_tailbounds/README.md)。

三阶段实测与同环境基线对比见
[论文实验索引](../experiments/paper_tailbounds/README.md)。复现对比：

```bash
conda run -n contractive-frontend-test-20260814 \
  python examples/run_reciprocal_feedback_suite.py --out-dir generated/reciprocal_feedback_suite_new
```

该对比脚本每组给基线/新流程各 60 秒总软预算、10 秒单次 optimizer 时间、
新流程 40 秒反馈软预算，并提供 150 秒外部保护。额外记录未取整的尾界对数，
避免所有微小结果都显示为求值输出的 `10^-12` 舍入下限。
