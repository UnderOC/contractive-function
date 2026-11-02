# Cauchy 两条独立搜索路径实测（2026-10-31）

输入：`examples/cauchy_notes.pp`；配置：`examples/cauchy_notes.json`。
初态 x=2、y=0、z=0。源码使用 Bernoulli(1/100) 生成 Z=0/10，x 更新使用旧 y，
循环后追加 `refute true`。随机基为 (1,Z)。事件是 K>n，K 为完整循环轮数。

## 实际运行

工作目录为 `contractive_function/`，使用环境
`contractive-frontend-test-20260814` 的 Python、CVXPY 1.9.3 与真实 MOSEK。
此次运行没有模拟求解结果，也没有把笔记的 B 或 eta 系数写入求解约束。

```bash
conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool.cauchy_cli run examples/cauchy_notes.pp \
  --config examples/cauchy_notes.json --mode both \
  --out-dir generated/cauchy_search_reproduce
```

`generated/cauchy_search_20261031_verified/` 是本次已保存的产物。
输出目录不能覆盖已有非空目录；上面的复现命令使用另一目录。

## 固定 eta 路径

固定 eta=x。状态范数 LP（常数 SOS 乘子的特例）得到精确 B=17/100，
无需数值修复；全部有理系数等式和非负约束通过。
测试另检查 y=1 时范数比恰为 17/100，因此这是本例固定 eta/随机基的最优 B。

指数在 [1/4,4] 内进行有理网格粗搜和一次细化，共检查 31 个候选，
其中 24 个通过收缩裕量 1/100 和精确非整数矩认证。

- k=3/2：认证的 rho 上界约 0.346451505343，小于笔记的 7/20。
- n=20 时，在此次候选集合中选择 k=7/4；rho 上界约 0.330372268495。
- 对应 Pr(K>20) 的认证上界约 8.07001237898e-10。
- 状态求解及指数搜索耗时约 0.70 秒，不含源码准备和独立复查。

完整结果：[`fixed/result.json`](fixed/result.json)。
独立复查：[`fixed/independent_check.json`](fixed/independent_check.json)。

## 未知 eta 的联合路径

模板 eta=alpha*x+beta，alpha,beta>=0，alpha+beta=1。
固定四个有理 t，分别通过矩阵 SOS 自动合成系数；每个状态模型都不含 k。
下表为最终已验证有理系数的显示近似：

| t | alpha | beta | eta(x0) | 状态认证 |
|---|---:|---:|---:|---|
| 21/50 | 0.997356234813 | 0.002643765187 | 1.997356234813 | proved |
| 1/2 | 0.925845580716 | 0.074154419284 | 1.925845580716 | proved |
| 3/5 | 0.741877731415 | 0.258122268585 | 1.741877731415 | proved |
| 7/10 | 0.564931227793 | 0.435068772207 | 1.564931227793 | proved |

四个数值最优候选均经过已有 margin repair，再通过精确有理重构。
没有放宽系数匹配或 PSD 接受标准；最终 eta 和初值使用修复后的有理解，
不把数值最小目标冒充精确最优值。

四份状态证书共得到 76 个有效的 (t,eta,k) 尾界候选。
状态求解、修复及指数搜索共约 2.23 秒，不含源码准备和独立复查。

在 n=20 的比较中，本次联合网格选 t=21/50、k=7/4，尾界约
1.53722672100e-9；它没有优于固定 eta=x 路径。两条路径均保留各自候选，
不据此声称联合搜索必然改善或此次有限搜索达到全局最优。

完整结果：[`template/result.json`](template/result.json)。
独立复查：[`template/independent_check.json`](template/independent_check.json)。

## 独立验证与回归

```bash
conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool.cauchy_cli verify generated/cauchy_search_20261031_verified/fixed
conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool.cauchy_cli verify generated/cauchy_search_20261031_verified/template
conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool.cauchy_cli evaluate generated/cauchy_search_20261031_verified/fixed --n 20
conda run --no-capture-output -n contractive-frontend-test-20260814 python -m pytest -q
```

完整回归：**159 passed in 26.54s**。
日志：[`regression.log`](regression.log)。新增 32 项测试覆盖：

- 旧 y、顺序赋值、重复使用同一次采样与不同采样发生点的独立性；
- 常数概率分支、相关有限联合分布、精确分解及错误随机基拒绝；
- 状态模型对 k 独立，模板模型对未知系数保持仿射；
- 两条路径的真实 MOSEK 求解、精确矩阵证书和独立复查；
- k<1 能收缩但一阶矩不收缩的稀有大跳跃例子；
- 负后继不能只凭范数约束被误报为有效非整数幂证书；
- B=0、初态已退出的轮数边界；
- 后续 unknown 保留已有证书；
- 修改 eta、B、矩上界、模型、概率或展示公式会被复查拒绝；
- 复查和评估不调用求解器，CLI 完整运行。

最初直接调用环境解释器运行全量测试时，有 3 项既有 CLI 测试因 PATH 中没有
`contractive` 命令失败；通过 `conda run` 激活正确环境后完整回归全部通过。
本次没有为此修改测试或生产 CLI。

## 集成边界

默认 solve、布尔宏步分析和 fractional_power 自动分派未改变。
新接口为 `search_fixed_eta` 与 `search_template_eta`；后续调度器可直接调用。
本版源码随机轮编译暂不支持连续采样、随机初始化、内部条件守卫或嵌套循环。
完整使用说明见 [`../../docs/cauchy_search.md`](../../docs/cauchy_search.md)。
