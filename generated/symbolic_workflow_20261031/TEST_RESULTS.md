# 笔记样例：完整符号流程实测

输入 `examples/cauchy_notes.pp`；配置 `examples/cauchy_workflow.json`。配置未指定
eta、eta 模板或随机基；第一阶段实际合成的系数驱动后续两个搜索阶段。
复现命令（输出目录须新建或为空）：

```bash
conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool solve examples/cauchy_notes.pp --goal tailbound \
  --workflow-config examples/cauchy_workflow.json --comparison-n 5 20 100 \
  --max-degree 2 --max-c-steps 10 --total-seconds 180 \
  --per-attempt-seconds 10 --repair-seconds 5 \
  --out-dir generated/symbolic_workflow_reproduction
```

本次运行约 11.05 秒，三个阶段均成功。保留 5 个直接多项式候选、24 个固定 eta
Cauchy 候选、123 个联合搜索候选，共 152 个。一次状态证明在多个 k 下成立时，
每个 `(eta,B,k)` 是独立的尾界候选；联合搜索还会在不同 t 下产生不同 eta。

第一阶段 D=1 即成功，选出的种子为
`eta=471875*x/553952 + 3775*y/17311 + 82077/553952`，
初态值 `A=1025827/553952`，原方法 `c=105/256`。
固定路径精确证明 `B=17/100`；联合路径实际使用未知系数模板
`a0+a1*y+a2*x`，而非固定原有系数。

## n=5、20、100 的比较

事件为 `Pr(K>n)`，K 为完整循环轮数。以下数值仅作展示，排序使用有理数精确算术。

| n | 第一阶段直接多项式界 | 最佳整数 k | 整数界 | 最佳有理数 k | 有理数界 | 整数界/有理数界 |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 0.0214955548481 | 2 | 0.0155811162216 | 13/8 | 0.0115482902519 | 1.3492141 |
| 20 | 3.36192999602e-8 | 2 | 1.46144448482e-9 | 7/4 | 7.05302125433e-10 | 2.0720829 |
| 100 | 3.65203866380e-39 | 2 | 4.82053994608e-47 | 7/4 | 2.33701783418e-48 | 20.626886 |

所有这些最优证书均来自固定 eta 路径。联合路径产生了有效证书，但在这次搜索网格
内未超越表中结果。最优只指本次实际搜索且通过验证的候选，不是全局最优。

每份证书的形式为 `min(1,C*rho^n)`，对所有非负整数 n 成立：

| k | 精确 C | 精确 rho |
|---|---|---|
| 2 | 3429288174257/1000000000000 | 17/50 |
| 13/8 | 34022266979/12500000000 | 4192208788804647175773351/12500000000000000000000000 |
| 7/4 | 2939703192981/1000000000000 | 3303722684949888598653487/10000000000000000000000000 |

完整结果见 [comparison.md](analyses/tailbound/workflow/comparison.md)、
[comparisons.json](analyses/tailbound/workflow/comparisons.json) 和 [summary.json](summary.json)。

## 验证

独立运行 `python -m contractive_tool verify generated/symbolic_workflow_20261031`：
`status=proved`，重验 5 个直接证书、152 个组合候选及 3 项比较。该检查重新从源码
建立义务，检查精确等式、PSD、分数幂包围和排序，不调用求解器。

全量回归命令：

```bash
conda run --no-capture-output -n contractive-frontend-test-20260814 python -m pytest -q
```

结果：**170 passed in 53.72s**。新增测试覆盖真实第一阶段种子传递、两条 Cauchy
路径、第一阶段无证书直接联合、整数/有理数按轮数精确比较、独立验证和 evaluate
不调用求解器、候选/排序/选择/种子篡改拒绝、布尔路径保持原调度，以及 Cauchy
不支持或失败时保留原证书。完整回归日志见 [pytest.log](pytest.log)。
