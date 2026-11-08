# 符号轮级尾界的完整搜索流程

默认 `solve --goal tailbound` 在布尔宏步编译不适用、符号轮级编译成功时，进入
`analysis/symbolic_workflow.py`。布尔宏步继续原流程；显式 `late_bad_exit`、
仅建模和断言分析继续各自原入口。

## 正幂搜索阶段

1. **直接多项式搜索**：复用原来的次数递增、c 二分、positivity 编码、数值求解和
   有理证书验证。保留预算内全部已验证证书，默认分配总预算的 50%。旧方法搜索
   多项式 V，并没有显式的整数 k 参数；组合时解释为 eta=V、k=1，不能把次数 D
   当作 k。按各个目标 n 的完整 A*c^n 选种子，同时保留原来的最小 c 候选，去重后
   默认最多取三个 eta。
2. **固定 eta -> B -> k**：仅使用本轮第一阶段实际合成的 eta，不读取历史结果，
   也不注入笔记的 eta=x。先证明归一化、后继非负和 `sum(q_j^2)<=B*eta^2`，
   最小化 B；状态约束不含 k。随后在有限有理网格上认证 Gamma(k)、B^(k/2)
   和 eta(x0)^k，得到收缩率 R<1 和尾界 `min(1,C*R^n)`。
3. **t -> eta -> k**：把已有 eta 的单项式系数变为未知量，并保留常数项；固定 t
   后以矩阵 SOS 证明 `sum(q_j^2)<=t^2*eta^2`，最小化 eta(x0)，得到精确有理解
   后再搜索 k。t 同时包含由已验证 B 推导的附近点及预设粗网格。第一阶段没有
   证书时，跳过固定路径，直接生成逐次升阶的普通多项式模板做联合搜索。

固定阶段默认分配余下时间的 35%，联合阶段使用剩余时间。unknown 或数值失败不删除
已有证书，也不被解释为数学上不可行。总时间为协作检查的软预算，符号运算、验证和
求解器调用不受硬抢占。各阶段产物记录预算、状态、证明和失败原因。

默认随机基由整轮多项式展开生成，并用二阶矩的认证上界归一化；笔记例会自动得到
相当于 `(1,10*r)` 的基。不同基下的 B 不能直接比较，t 引导只复用相同基的证明。
联合搜索仍是有限 t 网格和有理 k 网格上的搜索，不是同时含未知 k 的非线性求解。

## 独立倒数分支与预算

正幂搜索之后，自动启动倒数分母合成、矩约束、指数优化和参数反馈。
分母系数独立求解，不使用正幂模板作为必需种子；正幂失败或耗尽预算也会启动。
倒数不支持、未知或验证失败时记录原因，保留正幂证书。

- `--total-seconds` 保持为原正幂流程的软预算。
- 新增 `--reciprocal-seconds` 是**额外的独立软预算**，默认 60 秒，0 表示关闭。
  例如 `--total-seconds 180 --reciprocal-seconds 120` 为两条线分别预留 180/120 秒。
  两条线顺序执行；符号构造和精确验证可能超出 optimizer 的时间限制。
- `workflow-config` 新增 `reciprocal` 对象，接受 `ReciprocalOptions` 的搜索设置，
  例如 `{"reciprocal":{"degree":1,"feedback_points":24,"feedback_seconds":90}}`。
  `total_seconds`、`limits`、`variables` 由主流程管理，不能在该对象中覆盖。
  默认倒数次数为 1；`--tail-variables` 同时限制两边的模板变量。
- 当前接入范围是符号轮级尾界工作流；布尔宏步、显式 `late_bad_exit`、断言分析、
  `--no-symbolic-workflow` 和仅建模入口维持各自入口。

正幂侧还将直接多项式证书 `E[V_next] <= c*V` 经 Jensen 推导为
`V**k` 的证书（配置网格中的 `0<k<1`）。退出后取零，故可对存活势函数应用 Jensen。
`positive_jensen` 明确记录父证书，采用精确有理幂向外包围，验证时重新推导。
它不是 Cauchy 成功记录，也不是新的状态模板求解；裁剪后的界不会优于父证书。
保留它用于如实展示有保证的非整数正幂结果。

## 比较规则

每份证书都有精确有理数 C、R，保证 `Pr(K>n)<=min(1,C*R^n)`，K 计完整循环轮数。
对每个指定 n，比较完整界而非只比较 R。分别输出：

- `direct_polynomial`：第一阶段原有方法的最好结果。
- `integer`：原方法及 Cauchy 的所有整数 k 候选。
- `rational`：全部候选，包含整数，因而不会比整数集合更差。
- `noninteger`：严格非整数**正幂**候选，包括明确标记的 Jensen 派生证书。
- `reciprocal`：倒数路线的全部指数候选，独立分类。
- `overall`：正幂与倒数全部已验证候选的最小界。

`integer`、`rational` 和 `noninteger` 始终只描述正幂；倒数的非整数指数不混入其中。

区间网格额外补齐其中的正整数 k，保证整数与有理数比较使用相同状态证明。
“最优”仅指本次搜索并通过精确验证的候选中的最优。根 `summary.json` 的 selection
对应第一个指定 n 的 `overall`；`evaluate --n N` 会重新比较全部候选。
比较先剔除同组中被其父证书全域支配的 Jensen 派生候选，
再使用未裁剪的精确有理 `C*R**n` 排序并裁剪到 1。非整数组仍保留 Jensen 候选。
大 n 的精确分数字段可能较长，采用无全局设置副作用的整数序列化，保留紧凑的 `expression`。

## 复现笔记例

在项目目录执行，输出目录应为新的或空的：

```bash
conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool solve examples/cauchy_notes.pp --goal tailbound \
  --workflow-config examples/cauchy_workflow.json --comparison-n 5 20 100 \
  --max-degree 2 --max-c-steps 10 --total-seconds 180 \
  --per-attempt-seconds 10 --repair-seconds 5 \
  --out-dir generated/symbolic_workflow_example

conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool verify generated/symbolic_workflow_example

conda run --no-capture-output -n contractive-frontend-test-20260814 \
  python -m contractive_tool evaluate generated/symbolic_workflow_example --n 20
```

配置文件可省略；示例配置只设搜索网格、编码和预算分配，未提供 eta、模板或随机基。
`--no-symbolic-workflow` 可单独复现旧方法。不要使用旧 `--family fractional_power`
占位；组合流程由默认 `--family polynomial` 的外层调度器执行。

结果保存在 `summary.json` 以及 `analyses/tailbound/workflow/` 下：原阶段快照、
固定/联合模型及证明、`comparisons.json` 和可读的 `comparison.md`。
`verify` 从源文件重建义务，检查有理系数等式、PSD、分数幂包围、种子来源和比较排序，
无需调用求解器。schema_version=2 还重放倒数矩证书、分母合成配置及 Jensen 父证书；
旧 schema_version=1 的产物继续按原分组语义验证。`evaluate` 在取出结果前也执行这一复查。

## 支持范围和回退

组合调度覆盖可编译的符号轮级分析。Cauchy 随机展开目前支持确定初始化、Bernoulli
采样、常数概率分支和无内部条件守卫的无环循环体。内部状态/采样守卫、连续分布、
随机初始化或嵌套循环仍可能不支持；会明确记录原因并保留第一阶段已经证明的界。
因此“进入完整调度”不等于所有旧方法支持的输入都能成功执行 Cauchy。

当前样例仍通过 `refute true` 满足既有终端接口，没有新增纯循环特殊分派。
实测结果及回归记录见
[TEST_RESULTS.md](../generated/symbolic_workflow_20261031/TEST_RESULTS.md)。
