# 整数与有理数指数尾界比较

以下最优指本次实际搜索并通过精确验证的候选中的最优，不代表全局最优。
事件为 K>n，K 计完整循环轮数；表中浮点数仅作展示，精确值保存在 comparisons.json。
有理数集合包含整数；另列非整数候选，避免把整数结果误称为非整数改进。

| n | 直接多项式界 (k=1) | 最佳整数 k | 整数界 | 最佳有理数 k | 有理数界 | 整数界/有理数界 |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 0.0214955548481 | 2 | 0.0155811162216 | 13/8 | 0.0115482902519 | 1.3492141 |
| 10 | 0.000249514235551 | 2 | 7.0793462192e-05 | 7/4 | 4.55343706463e-05 | 1.5547258 |
| 20 | 3.36192999602e-08 | 2 | 1.46144448482e-09 | 7/4 | 7.05302125433e-10 | 2.0720829 |
| 50 | 8.22372688715e-20 | 2 | 1.28573016728e-23 | 7/4 | 2.62109495997e-24 | 4.905317 |
| 100 | 3.6520386638e-39 | 2 | 4.82053994608e-47 | 7/4 | 2.33701783418e-48 | 20.626886 |
| 200 | 7.20225912568e-78 | 2 | 6.77621832606e-94 | 7/4 | 1.85789244653e-96 | 364.72608 |
| 500 | 5.52419334014e-194 | 2 | 1.88218584491e-234 | 7/4 | 9.33461040104e-241 | 2016351.8 |
| 1000 | 0 | 2 | 0 | 7/4 | 0 | 3.4852354e+12 |

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

## 在 n=10 选择的证书

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

## 在 n=50 选择的证书

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

## 在 n=200 选择的证书

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

## 在 n=500 选择的证书

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

## 在 n=1000 选择的证书

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

## 正幂与倒数路线

| n | 正整数幂 | 正非整数幂 | 倒数幂 | 合并最优 |
|---|---:|---:|---:|---:|
| 5 | 0.0155811162216 | 0.0115482902519 | 未找到 | 0.0115482902519 |
| 10 | 7.0793462192e-05 | 4.55343706463e-05 | 未找到 | 4.55343706463e-05 |
| 20 | 1.46144448482e-09 | 7.05302125433e-10 | 未找到 | 7.05302125433e-10 |
| 50 | 1.28573016728e-23 | 2.62109495997e-24 | 未找到 | 2.62109495997e-24 |
| 100 | 4.82053994608e-47 | 2.33701783418e-48 | 未找到 | 2.33701783418e-48 |
| 200 | 6.77621832606e-94 | 1.85789244653e-96 | 未找到 | 1.85789244653e-96 |
| 500 | 1.88218584491e-234 | 9.33461040104e-241 | 未找到 | 9.33461040104e-241 |
| 1000 | 0 | 0 | 未找到 | 0 |
