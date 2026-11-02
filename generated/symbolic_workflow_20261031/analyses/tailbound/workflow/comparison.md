# 整数与有理数指数尾界比较

以下最优指本次实际搜索并通过精确验证的候选中的最优，不代表全局最优。
事件为 K>n，K 计完整循环轮数；表中浮点数仅作展示，精确值保存在 comparisons.json。
有理数集合包含整数；另列非整数候选，避免把整数结果误称为非整数改进。

| n | 直接多项式界 (k=1) | 最佳整数 k | 整数界 | 最佳有理数 k | 有理数界 | 整数界/有理数界 |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 0.0214955548481 | 2 | 0.0155811162216 | 13/8 | 0.0115482902519 | 1.3492141 |
| 20 | 3.36192999602e-08 | 2 | 1.46144448482e-09 | 7/4 | 7.05302125433e-10 | 2.0720829 |
| 100 | 3.6520386638e-39 | 2 | 4.82053994608e-47 | 7/4 | 2.33701783418e-48 | 20.626886 |

每份候选的形式是 `min(1, C * rho**n)`，均对所有非负整数 n 有效。

## 在 n=5 选择的证书

- integer: k=2, method=cauchy_fixed, id=cauchy_fixed:analyses/tailbound/workflow/fixed_000/result.json:14
  - 精确前因子 C = 3429288174257/1000000000000
  - 精确收缩上界 rho = 17/50
  - eta = 471875*x/553952 + 3775*y/17311 + 82077/553952
- rational: k=13/8, method=cauchy_fixed, id=cauchy_fixed:analyses/tailbound/workflow/fixed_000/result.json:11
  - 精确前因子 C = 34022266979/12500000000
  - 精确收缩上界 rho = 4192208788804647175773351/12500000000000000000000000
  - eta = 471875*x/553952 + 3775*y/17311 + 82077/553952
- noninteger: k=13/8, method=cauchy_fixed, id=cauchy_fixed:analyses/tailbound/workflow/fixed_000/result.json:11
  - 精确前因子 C = 34022266979/12500000000
  - 精确收缩上界 rho = 4192208788804647175773351/12500000000000000000000000
  - eta = 471875*x/553952 + 3775*y/17311 + 82077/553952

## 在 n=20 选择的证书

- integer: k=2, method=cauchy_fixed, id=cauchy_fixed:analyses/tailbound/workflow/fixed_000/result.json:14
  - 精确前因子 C = 3429288174257/1000000000000
  - 精确收缩上界 rho = 17/50
  - eta = 471875*x/553952 + 3775*y/17311 + 82077/553952
- rational: k=7/4, method=cauchy_fixed, id=cauchy_fixed:analyses/tailbound/workflow/fixed_000/result.json:12
  - 精确前因子 C = 2939703192981/1000000000000
  - 精确收缩上界 rho = 3303722684949888598653487/10000000000000000000000000
  - eta = 471875*x/553952 + 3775*y/17311 + 82077/553952
- noninteger: k=7/4, method=cauchy_fixed, id=cauchy_fixed:analyses/tailbound/workflow/fixed_000/result.json:12
  - 精确前因子 C = 2939703192981/1000000000000
  - 精确收缩上界 rho = 3303722684949888598653487/10000000000000000000000000
  - eta = 471875*x/553952 + 3775*y/17311 + 82077/553952

## 在 n=100 选择的证书

- integer: k=2, method=cauchy_fixed, id=cauchy_fixed:analyses/tailbound/workflow/fixed_000/result.json:14
  - 精确前因子 C = 3429288174257/1000000000000
  - 精确收缩上界 rho = 17/50
  - eta = 471875*x/553952 + 3775*y/17311 + 82077/553952
- rational: k=7/4, method=cauchy_fixed, id=cauchy_fixed:analyses/tailbound/workflow/fixed_000/result.json:12
  - 精确前因子 C = 2939703192981/1000000000000
  - 精确收缩上界 rho = 3303722684949888598653487/10000000000000000000000000
  - eta = 471875*x/553952 + 3775*y/17311 + 82077/553952
- noninteger: k=7/4, method=cauchy_fixed, id=cauchy_fixed:analyses/tailbound/workflow/fixed_000/result.json:12
  - 精确前因子 C = 2939703192981/1000000000000
  - 精确收缩上界 rho = 3303722684949888598653487/10000000000000000000000000
  - eta = 471875*x/553952 + 3775*y/17311 + 82077/553952

