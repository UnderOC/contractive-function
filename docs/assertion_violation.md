# Assertion violation：完整一阶矩收缩

实现范围是 `Assertion_Violation_Markov证明版.md` 的 §2.1–2.2，使用 §1 的证明。
§2.3 比较实验、倒数幂、c>1 和 q=1 模式不在本次范围内。

## 证明规则

归一化 H=1，在每个普通 pCFG 位置直接合成总次数不超过 D 的多项式 eta。
整数幂纳入一般多项式模板，不要求恢复完整幂分解。固定 c∈(0,1) 后，未知系数仍以
仿射方式进入正性编码，使用现有 CVXPY/MOSEK 后端。

```text
eta_l >= delta > 0                 （所有普通位置的不变量域）
eta_failure = 1
eta_normal = delta
E[eta_next] <= c * eta_l           （每个普通转移，包含所有终端后继）
minimize A = E[eta_after_initialization]
```

delta 默认是精确有理数 1/1000000，可用 `--assertion-margin` 设置，要求 0<delta<=1。
这是对 note 中逐点严格正性的充分条件，限制了搜索空间：例如带有可达永久自环的程序
可能不存在这一类证书，即使实际违规概率很低。失败只表示本轮未找到证书，不表示
违规必然发生或不存在其他证明。对固定 delta，两种终端取值是各自允许的最小值；
将更大的终端值降到这些常数只会放松普通状态的收缩义务。

这里的 eta 是**原始函数**；辅助证明中的 Theta 在正常终端为 0、失败终端为 1。
不得用 Theta_normal=0 替换完整一阶矩中的 eta_normal=delta。吸收自环不施加收缩。
一般实数守卫沿用现有闭包覆盖，所以例如 `<0.5` 的认证域可能包含边界 0.5，结果
可能更保守；没有改变源程序的严格比较语义。

最终违规概率界为 `min(1,A)`。若 n 从直线初始化之后开始计数，还可得到：

```text
Pr(n < tau_f < infinity) <= min(1, A*c**(n+1))
Pr(tau_f = n)           <= min(1, A*c**n)
```

输出不是累计违规概率的衰减界，也不是循环轮数尾界。初始化前缀长 L 时，入口时钟
使用 n-L；晚违规界在前缀区间保守截为 min(1,A)，前缀内单步违规概率为零。
原始输入允许随机直线初始化，此时 A 是初始分布上的精确期望，不是任意一个样本值。
不预设终止性，也不将概率条件化在终止事件上。

§2.2 的 Jensen 路线中，0<k<1 不改进 k=1 的截断界，因此没有指数搜索。

## 独立流程与模块复用

`assertion_pipeline.py` 独立管理 assertion 搜索、产物、候选选择及重放验证；
`analysis/assertion.py` 生成它的证明义务。公共入口只按 goal 分派，不调用 tail 的
round-survival 或 symbolic/Cauchy 工作流。复用已有 CFG、不变量检查、多项式模板、
期望引擎、正性编码、CVXPY/MOSEK、精确有理重构和修复模块。

原 tail 的证书恢复顺序原样抽取到 `backends/cvxpy/certification.py`，两种分析共用；
精确锥见证检查置于 `backends/cvxpy/verification.py`，Cauchy 和 assertion 共用。
Tail 的证明规则、搜索策略和终止结论保持原有逻辑。

## 搜索与验证

- 默认 D=1,...,6。每个 D 的 c 网格为 `1-2**(-(i+6))`，i=0,...,max_c_steps-1；
  选择接近 1 的点是为了优化初始概率，不执行最小可行 c 的二分。
- `--c-values` 可指定精确有理数网格；`--max-c-steps` 控制默认网格点数。
- `--assertion-variables wealth` 可将各位置的模板限制为指定程序变量的多项式；
  默认仍使用所有变量。原程序、初始化、转移和不变量验证均保留。
  编码时仅删去与收缩残差无关的独立约束分量，在投影的超集上证明非负。
  如果更新把其他变量带入残差，或域约束把它们与残差变量耦合，则这些变量仍保留在
  认证域中。因此这是一个保守的模板/编码选择，不是假设被省略的变量没有影响。
- 每个点最小化 A；首个产生非平凡上界（<1）的次数完成网格后停止。
  `--continue-after-success` 可继续升阶。次数、参数、编码和时间预算仍然生效。
- 最终按已验证的违规概率上界、A、c 排序；保留候选及 (A,c) Pareto 集。
  所有“最佳”仅针对实际找到并精确验证的候选。
- 求解器 optimal 只是数值候选。经精确有理重构、PSD 检查、修复或原域有理恒等式
  认证后才能标记 proved。数值 unknown/infeasible 不能用作概率结论。
- Assertion 的首次有理重构还检查目标值是否超过数值候选加
  `max(1e-4, abs(A)*repair_relative_gap)`：超过时继续更高精度重构或修复，
  避免过早接受有效但很松的证书。此限制仅影响搜索质量，不改变证明判据；
  公共重构器与 tailbound 的默认行为保持兼容。
- `verify` 从归档源码重新建立语义域、证明义务和锥模型，验证精确见证、原始 eta、
  初始目标及输出公式；`evaluate` 先执行这一验证，再对候选选择最好的界。
- `build-model`/`analyze` 输出多项式及锥模型，不调用求解器。

## 使用方式

从项目目录、现有 `contractive-frontend-test-20260814` 环境执行：

```bash
python -m contractive_tool solve kelly_double_bound.pp --goal assertion_violation \
  --out-dir generated/kelly_assertion_new
python -m contractive_tool verify generated/kelly_assertion_new
python -m contractive_tool evaluate generated/kelly_assertion_new
python -m contractive_tool evaluate generated/kelly_assertion_new \
  --event late_failure --n 100 --clock program_entry
```

输出目录必须是新的或空的。默认 evaluate 返回最终违规概率上界；
`--event point_failure` 对应单步事件，`--clock after_initialization` 是默认时钟。
CLI 的 tailbound evaluate 仍要求 `--n`，原命令保持兼容。

Kelly 的末尾已改为 `refute (wealth < 0.5);`。上界退出为正常终止，下界退出为失败。
同一文件的 tailbound 请使用 `--tail-rule round_survival`，这样上下界退出都计入终止。
`late_bad_exit` 对该文件只界定晚下界退出事件。

实际命令、证书结果、独立参考概率及回归记录见
[实验报告](../generated/assertion_kelly_20261102/RESULTS.md)。

## Kelly 更紧上界的配置（2026-11-03）

```bash
python -m contractive_tool solve kelly_double_bound.pp --goal assertion_violation \
  --assertion-variables wealth --initial-degree 7 --max-degree 7 \
  --c-values 999999/1000000 --strategy putinar --max-order 4 \
  --max-attempts-per-point 1 --repair-relative-gap 0.001 \
  --total-seconds 120 --out-dir generated/kelly_assertion_degree7_new
python -m contractive_tool verify generated/kelly_assertion_degree7_new
```

本次得到最终违规概率上界 **0.375083608**（向上取整），低于此前独立合成的
§5.2 ExpLinSyn 界约 0.602401499。仍使用 §2.2 完整一阶矩收缩、正终端原始势函数
以及 CVXPY/MOSEK；没有改为 §2.3，也不预设相同 eta。结果不是该方法的全局最优值。
详细比较、证书和未成功尝试见
[优化报告](../generated/assertion_kelly_optimization_20261103/RESULTS.md)。
