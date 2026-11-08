# 整数与有理数指数尾界比较

以下最优指本次实际搜索并通过精确验证的候选中的最优，不代表全局最优。
事件为 K>n，K 计完整循环轮数；表中浮点数仅作展示，精确值保存在 comparisons.json。
有理数集合包含整数；另列非整数候选，避免把整数结果误称为非整数改进。

| n | 直接多项式界 (k=1) | 最佳整数 k | 整数界 | 最佳有理数 k | 有理数界 | 整数界/有理数界 |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 0.03125 | 1 | 0.03125 | 1 | 0.03125 | 1 |
| 10 | 0.0009765625 | 1 | 0.0009765625 | 1 | 0.0009765625 | 1 |
| 20 | 9.53674316406e-07 | 1 | 9.53674316406e-07 | 1 | 9.53674316406e-07 | 1 |
| 50 | 8.881784197e-16 | 1 | 8.881784197e-16 | 1 | 8.881784197e-16 | 1 |
| 100 | 7.88860905221e-31 | 1 | 7.88860905221e-31 | 1 | 7.88860905221e-31 | 1 |
| 200 | 6.22301527786e-61 | 1 | 6.22301527786e-61 | 1 | 6.22301527786e-61 | 1 |
| 500 | 3.0549363635e-151 | 1 | 3.0549363635e-151 | 1 | 3.0549363635e-151 | 1 |
| 1000 | 9.33263618503e-302 | 1 | 9.33263618503e-302 | 1 | 9.33263618503e-302 | 1 |

每份候选的形式是 `min(1, C * rho**n)`，均对所有非负整数 n 有效。

## 在 n=5 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 545253866333/1000000000000
  - eta = 1

## 在 n=10 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 545253866333/1000000000000
  - eta = 1

## 在 n=20 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 545253866333/1000000000000
  - eta = 1

## 在 n=50 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 545253866333/1000000000000
  - eta = 1

## 在 n=100 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 545253866333/1000000000000
  - eta = 1

## 在 n=200 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 545253866333/1000000000000
  - eta = 1

## 在 n=500 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 545253866333/1000000000000
  - eta = 1

## 在 n=1000 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 1/2
  - eta = 1
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 1
  - 精确收缩上界 rho = 545253866333/1000000000000
  - eta = 1

## 正幂与倒数路线

| n | 正整数幂 | 正非整数幂 | 倒数幂 | 合并最优 |
|---|---:|---:|---:|---:|
| 5 | 0.03125 | 0.0481940882942 | 未找到 | 0.03125 |
| 10 | 0.0009765625 | 0.00232267014651 | 未找到 | 0.0009765625 |
| 20 | 9.53674316406e-07 | 5.39479660947e-06 | 未找到 | 9.53674316406e-07 |
| 50 | 8.881784197e-16 | 6.75985981527e-14 | 未找到 | 8.881784197e-16 |
| 100 | 7.88860905221e-31 | 4.5695704722e-27 | 未找到 | 7.88860905221e-31 |
| 200 | 6.22301527786e-61 | 2.08809743004e-53 | 未找到 | 6.22301527786e-61 |
| 500 | 3.0549363635e-151 | 1.99240167035e-132 | 未找到 | 3.0549363635e-151 |
| 1000 | 9.33263618503e-302 | 3.96966441602e-264 | 未找到 | 9.33263618503e-302 |
