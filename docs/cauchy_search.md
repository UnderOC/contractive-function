# Cauchy 非整数幂搜索：独立接口

实现位于 `analysis/cauchy.py`。两个独立搜索接口也已接入默认 `contractive solve`
的符号轮级尾界流程；布尔宏步保持原路径。组合调度和整数/有理数比较见
[符号完整流程](symbolic_workflow.md)。本文保留独立调用方式，便于单独分析固定 eta
和自定义模板。旧 CLI 的 `fractional_power` 占位不是组合流程入口。

## 复现笔记主例

从 `contractive_function/` 执行，输出目录必须是新的或空的：

```bash
conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool.cauchy_cli run examples/cauchy_notes.pp \
  --config examples/cauchy_notes.json --mode both \
  --out-dir generated/cauchy_example_run
```

两个子目录 `fixed/` 和 `template/` 分别包含 `result.json` 和
`independent_check.json`。前者保存完整状态模型、数值求解/修复记录、有理解、
分解、分布、逐个指数的认证结果和全部有效候选；后者报告独立复查结果。

```bash
conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool.cauchy_cli verify generated/cauchy_example_run/template

conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool.cauchy_cli evaluate generated/cauchy_example_run/fixed --n 20
```

复查从原始源码重新构造循环和证明义务，核对源码哈希、模型、全部有理系数等式、
非负标量、PSD 块、目标值、eta、B/t、非整数矩及最终公式，不调用求解器。
`evaluate` 先复查，再按该 n 对所有候选取最小界。精确上界是有理数；浮点值仅展示。
原始源码需要保留在产物记录的位置；若修改源码，复查会拒绝旧产物。

## 共享语义与随机展开

`prepare_random_round(source)` 从 `.pp` 构造已认证的不变量、活动域
`D = I and G`、确定性初态和完整循环更新 F。它保留随机变量，不调用期望引擎
消去整轮更新中的随机信息。

- 每个采样发生点使用新的随机符号；存入状态后再次使用同一个值不会重新采样。
- 顺序赋值按 CFG 顺序组合，单个 update 内仍使用 simultaneous substitution。
- 常数概率分支以有限选择变量及插值选择多项式表示；保留精确分支概率。
- 支持点是完整联合原子；矩计算不会错误地把相关基函数当成独立变量。
- 后继非负性逐个检查所有正概率支持点，包含退出循环的后继。
- 源码末尾使用 `refute true`，保留现有入口约束。事件是 `K > n`，K 计完整循环轮数。

对于非线性不变量的保持，入口通过 `prepare_certified_program` 注入精确认证器。
它新增二次半正定检查、已有约束加二次平方和余项，以及带精确恢复的 SOS 兜底；
证据保存与无求解器重放详见 [不变量认证](invariant_certification.md)。原有
非负生成元乘积规则仍保留：先尝试原有 Farkas 证明，
再尝试坐标下界平移后的非负单项式，最后尝试有界的生成元乘积。
底层 `semantics.prepare_program` 的默认调用者仍使用原证明器；尾界入口使用上述扩展。
没有增加未经证明的状态界，也没有将采样检查作为证明。

`round.decompose(eta, basis)` 通过随机单项式系数匹配精确得到
`eta(F) = sum(q[j]*basis[j])`，并重验恒等式。basis 可省略，此时取随机单项式基。

状态条件分支使用 `round.pieces` 保存精确守卫、闭覆盖证明域和区域更新。
`round.decompositions(eta, basis)` 逐区域构造分解，所有区域共享 eta、B/t 和随机基底。
编译器先组合完整区域后继分布，再取各区域有理 CDF 分点的并集构造公共有限分布；
不会把条件分支当成随机选择，也不会累加重叠 DNF 覆盖区域的概率。
默认使用公共支持点上的插值指示基；eta(F) 的分解在该有限支持上精确成立。
分区产物的 `q` 按 `round.pieces` 的区域顺序展开，每段长度等于公共 `basis` 长度；
范数约束逐段构造，不对全部区域的系数一起取范数。
每个区域分别证明后继非负和系数范数界，因此原整数/非整数 k 认证公式继续适用。
源码重放重建全部区域、概率、分解和锥约束；删除区域或改动边界会使认证失败。
自定义基须线性独立并完整覆盖展开式。笔记样例使用 `(1, 10*r)`，对应笔记的
`(1,Z)`；直接使用 `(1,r)` 是另一种 Cauchy 范数界，不能混用其 B 和 Gamma。

## 固定 eta：B → k

```python
import sympy as sp
from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.cauchy import search_fixed_eta

round_ = prepare_random_round("examples/cauchy_notes.pp")
x = sp.Symbol("x")
basis = (sp.Integer(1), 10*round_.law.symbols[0])
fixed = search_fixed_eta(round_, x, basis=basis)
```

合成器同时认证 `eta >= 1`、全部后继 `eta(F) >= 0`，并最小化 B：

```
B >= 0
B*eta**2 - sum(q[j]**2) >= 0 on D
```

状态模型完全不含 k。求解并精确验证后，所有指数候选共用同一个 B。
数值最优值不直接作为证明；若修复提高了 B，则使用修复后的有理 B。
若 B=0，单独输出至多一轮退出的结论，避免 log(0)。初态已退出时输出 K=0。

## 模板 eta：t → eta → k

```python
from contractive_tool.analysis.cauchy import EtaTemplate, search_template_eta

alpha, beta = sp.symbols("alpha beta")
template = EtaTemplate(
    alpha*x + beta,
    coefficients=(alpha, beta),
    nonnegative=(alpha, beta),
    equalities=(alpha+beta-1,),
)
joint = search_template_eta(
    round_, template, basis=basis,
    t_values=("21/50", "1/2", "3/5", "7/10"),
)
```

对每个固定有理数 t>0，构造矩阵 SOS：

```
M = [[t*eta, q.T], [q, t*eta*I]] >= 0 on D
```

内层同时认证归一化、后继非负性和模板系数约束，最小化 `eta(x0)`。
矩阵元素及系数匹配约束对决策变量都是仿射的。通过精确验证后，令 B=t²，
再调用与固定 eta 路径相同的指数搜索器。数值修复后的 eta/初值用于最终尾界。

`t_values` 省略时，从当前有限指数候选和认证的 Gamma 上界计算保守的可用 t
端点，在最大端点下生成最多 8 个等距正有理数。这是有限搜索，不是全局区间排除。
显式网格用于可复现运行；本版没有用求解器的 infeasible 状态进行严格二分剪枝。
后续 t 点超时或验证失败会记为 unknown，并保留已有证书。

## 状态正性编码

`CauchyOptions` 控制状态编码和预算：

- `scalar_strategy="constant_sos"`：默认使用非负常数 SOS 乘子乘以生成元及其
  有限个不同生成元的乘积；本例足以表示所需标量证书。
- `scalar_strategy="sos"`：调用现有完整标量 SOS 编码，`scalar_order` 指定阶数。
- `matrix_multiplier_degree=0`：每个矩阵 SOS 乘子使用常数 Gram 矩阵；可增加到
  更高的单项式基次数。矩阵 SOS 使用 `(m(x) tensor I).T Q (m(x) tensor I)`。
- `product_depth=2`：默认允许至多两个不同生成元的乘积，包括笔记中的
  `(x-1)*y` 与 `(x-1)*(1-y)`。这些乘积的非负性直接由原生成元保证。
- `limits`：沿用 `EncodingLimits` 的乘积数、PSD 维数、决策变量数量限制。

标量义务可消去所有项共同含有的偶次单项式，认证商非负即可保证原式非负；
仅用于这一充分证明方向。投影步骤只丢弃涉及无关变量的约束，扩大证明域。
这两项变换均记录在模型 coverage 中并由复查时重新构造。

默认低阶编码避免本例完整高阶 SOS 带来的大量奇异 Gram 块。两种编码都是
充分证书，不对无界域宣称有限阶完备性。样例矩阵的精确修复仍复用既有 repair.py，
最终接受标准没有放宽。

## 指数搜索、认证和比较

`ExponentOptions` 支持显式有理数 `values`，或 `interval=(lo,hi)`。
区间模式先产生 `coarse_points` 个点，再做最多 `refinements` 层全区间二分细化，
受 `max_candidates` 限制，不依赖浮点凸性假设。配置样例覆盖 [1/4,4]，最终 31 个点，
包括 k<1 和 k=3/2。`interval` 给出时优先于 `values`。

对 k=p/q，有限原子上的 h=||b||² 使用整数开根算法构造有理数上下界：

```
lower**(2*q) <= h**p <= upper**(2*q)
```

Gamma 的认证上界为各原子上界的概率加权和。随后分别认证 B^(k/2) 和 eta(x0)^k，
输出有理数 C、R，满足：

```
C >= eta(x0)**k
R >= Gamma(k)*B**(k/2), R <= 1-margin < 1
Pr(K > n) <= min(1, C*R**n), n = 0,1,2,...
```

默认不指定目标时间，也不自动把最小 R 当成最佳证书。可设置 `target_n`，
在全部已找到候选中按完整的 `C*R**target_n` 选择；每份证书仍对所有 n 有效。
`evaluate` 无论是否曾指定 target_n，都按当前 n 比较全部保留候选。

## 本版边界

- 源码支持确定性初始化、有限离散采样、常数概率分支及包含状态条件 if 的无环
  循环体；条件可位于概率分支之前或之后，赋值后的条件按原状态回代。
  依赖新采样值且现有符号内核不能处理的守卫、嵌套循环、连续采样和随机初始化仍显式拒绝。
  默认上限为 256 个覆盖区域、256 个公共随机原子、4096 个组合访问节点。
- `FiniteLaw` 可直接表示相关有限随机坐标；源码采样仍按原项目的独立采样语义。
- 模板系数可带仿射等式和非负约束，不支持对未知系数的非线性限制。
- 联合路径 t>0；B=0 的退化情形由固定 eta 路径处理。
- 时间预算在区域、矩阵乘子、系数匹配及模型序列化之间协作检查；构造超时记录
  `state_model_time_budget`，不把未完成模型送入求解器，并保留此前有效候选。
  单次符号操作仍不能被硬抢占，独立证书重放也可能增加总耗时。
- 默认符号轮级流程自动调度 Cauchy；若源码超出上述随机展开支持范围，则保留
  直接多项式阶段的结果，并在阶段记录中说明未执行 Cauchy 的原因。

测试及实测结果见 `generated/cauchy_search_20261031_verified/TEST_RESULTS.md`。
