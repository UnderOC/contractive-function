# 整数与有理数指数尾界比较

以下最优指本次实际搜索并通过精确验证的候选中的最优，不代表全局最优。
事件为 K>n，K 计完整循环轮数；表中浮点数仅作展示，精确值保存在 comparisons.json。
有理数集合包含整数；另列非整数候选，避免把整数结果误称为非整数改进。

| n | 直接多项式界 (k=1) | 最佳整数 k | 整数界 | 最佳有理数 k | 有理数界 | 整数界/有理数界 |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 1 | 1 | 1 | 1 | 1 | 1 |
| 10 | 1 | 1 | 1 | 1 | 1 | 1 |
| 20 | 1 | 1 | 1 | 1 | 1 | 1 |
| 50 | 0.34486665227 | 1 | 0.34486665227 | 1 | 0.34486665227 | 1 |
| 100 | 0.0312711787877 | 1 | 0.0312711787877 | 1 | 0.0312711787877 | 1 |
| 200 | 0.00013745021952 | 1 | 0.00013745021952 | 1 | 0.00013745021952 | 1 |
| 500 | 6.46793487458e-12 | 1 | 6.46793487458e-12 | 1 | 6.46793487458e-12 | 1 |
| 1000 | 3.96703445655e-24 | 1 | 3.96703445655e-24 | 1 | 3.96703445655e-24 | 1 |

每份候选的形式是 `min(1, C * rho**n)`，均对所有非负整数 n 有效。

## 在 n=5 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 88/31
  - 精确收缩上界 rho = 31/32
  - eta = 38*x/31 + 38*y/31 + 12/31
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 88/31
  - 精确收缩上界 rho = 31/32
  - eta = 38*x/31 + 38*y/31 + 12/31
- noninteger: k=1/4, method=positive_jensen, id=positive_jensen:direct:0:1/4
  - 精确前因子 C = 1298016594019/1000000000000
  - 精确收缩上界 rho = 496047120809/500000000000
  - eta = 38*x/31 + 38*y/31 + 12/31

## 在 n=10 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 88/31
  - 精确收缩上界 rho = 31/32
  - eta = 38*x/31 + 38*y/31 + 12/31
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 88/31
  - 精确收缩上界 rho = 31/32
  - eta = 38*x/31 + 38*y/31 + 12/31
- noninteger: k=1/4, method=positive_jensen, id=positive_jensen:direct:0:1/4
  - 精确前因子 C = 1298016594019/1000000000000
  - 精确收缩上界 rho = 496047120809/500000000000
  - eta = 38*x/31 + 38*y/31 + 12/31

## 在 n=20 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 232/61
  - 精确收缩上界 rho = 61/64
  - eta = 114*x/61 + 114*y/61 + 4/61
- rational: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 232/61
  - 精确收缩上界 rho = 61/64
  - eta = 114*x/61 + 114*y/61 + 4/61
- noninteger: k=1/4, method=positive_jensen, id=positive_jensen:direct:1:1/4
  - 精确前因子 C = 1396495489969/1000000000000
  - 精确收缩上界 rho = 988069435561/1000000000000
  - eta = 114*x/61 + 114*y/61 + 4/61

## 在 n=50 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 232/61
  - 精确收缩上界 rho = 61/64
  - eta = 114*x/61 + 114*y/61 + 4/61
- rational: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 232/61
  - 精确收缩上界 rho = 61/64
  - eta = 114*x/61 + 114*y/61 + 4/61
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:1:7/8
  - 精确前因子 C = 3218387858297/1000000000000
  - 精确收缩上界 rho = 191772409121/200000000000
  - eta = 114*x/61 + 114*y/61 + 4/61

## 在 n=100 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 232/61
  - 精确收缩上界 rho = 61/64
  - eta = 114*x/61 + 114*y/61 + 4/61
- rational: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 232/61
  - 精确收缩上界 rho = 61/64
  - eta = 114*x/61 + 114*y/61 + 4/61
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:1:7/8
  - 精确前因子 C = 3218387858297/1000000000000
  - 精确收缩上界 rho = 191772409121/200000000000
  - eta = 114*x/61 + 114*y/61 + 4/61

## 在 n=200 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 116/11
  - 精确收缩上界 rho = 121/128
  - eta = 70*x/11 + 70*y/11 - 24/11
- rational: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 116/11
  - 精确收缩上界 rho = 121/128
  - eta = 70*x/11 + 70*y/11 - 24/11
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:2:7/8
  - 精确前因子 C = 245489071189/31250000000
  - 精确收缩上界 rho = 118997678411/125000000000
  - eta = 70*x/11 + 70*y/11 - 24/11

## 在 n=500 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 116/11
  - 精确收缩上界 rho = 121/128
  - eta = 70*x/11 + 70*y/11 - 24/11
- rational: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 116/11
  - 精确收缩上界 rho = 121/128
  - eta = 70*x/11 + 70*y/11 - 24/11
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:2:7/8
  - 精确前因子 C = 245489071189/31250000000
  - 精确收缩上界 rho = 118997678411/125000000000
  - eta = 70*x/11 + 70*y/11 - 24/11

## 在 n=1000 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 116/11
  - 精确收缩上界 rho = 121/128
  - eta = 70*x/11 + 70*y/11 - 24/11
- rational: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 116/11
  - 精确收缩上界 rho = 121/128
  - eta = 70*x/11 + 70*y/11 - 24/11
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:2:7/8
  - 精确前因子 C = 245489071189/31250000000
  - 精确收缩上界 rho = 118997678411/125000000000
  - eta = 70*x/11 + 70*y/11 - 24/11

## 正幂与倒数路线

| n | 正整数幂 | 正非整数幂 | 倒数幂 | 合并最优 |
|---|---:|---:|---:|---:|
| 5 | 1 | 1 | 未找到 | 1 |
| 10 | 1 | 1 | 未找到 | 1 |
| 20 | 1 | 1 | 未找到 | 1 |
| 50 | 0.34486665227 | 0.393953352913 | 未找到 | 0.34486665227 |
| 100 | 0.0312711787877 | 0.0482226664731 | 未找到 | 0.0312711787877 |
| 200 | 0.00013745021952 | 0.000417712294559 | 未找到 | 0.00013745021952 |
| 500 | 6.46793487458e-12 | 1.61964536906e-10 | 未找到 | 6.46793487458e-12 |
| 1000 | 3.96703445655e-24 | 3.33931759773e-21 | 未找到 | 3.96703445655e-24 |
