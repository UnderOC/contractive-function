# 整数与有理数指数尾界比较

以下最优指本次实际搜索并通过精确验证的候选中的最优，不代表全局最优。
事件为 K>n，K 计完整循环轮数；表中浮点数仅作展示，精确值保存在 comparisons.json。
有理数集合包含整数；另列非整数候选，避免把整数结果误称为非整数改进。

| n | 直接多项式界 (k=1) | 最佳整数 k | 整数界 | 最佳有理数 k | 有理数界 | 整数界/有理数界 |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 1 | 1 | 1 | 1 | 1 | 1 |
| 10 | 0.838870001529 | 1 | 0.838870001529 | 1 | 0.838870001529 | 1 |
| 20 | 0.205414654841 | 1 | 0.205414654841 | 1 | 0.205414654841 | 1 |
| 50 | 0.00262820738265 | 1 | 0.00262820738265 | 1 | 0.00262820738265 | 1 |
| 100 | 1.68762149992e-06 | 1 | 1.68762149992e-06 | 1 | 1.68762149992e-06 | 1 |
| 200 | 6.95834386712e-13 | 1 | 6.95834386712e-13 | 1 | 6.95834386712e-13 | 1 |
| 500 | 4.36008760737e-32 | 1 | 4.36008760737e-32 | 1 | 4.36008760737e-32 | 1 |
| 1000 | 1.67420818824e-64 | 1 | 1.67420818824e-64 | 1 | 1.67420818824e-64 | 1 |

每份候选的形式是 `min(1, C * rho**n)`，均对所有非负整数 n 有效。

## 在 n=5 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 2484/779
  - 精确收缩上界 rho = 7/8
  - eta = 1600*wealth**2/7011 - 13115*wealth/7011 + 33871/7011
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 2484/779
  - 精确收缩上界 rho = 7/8
  - eta = 1600*wealth**2/7011 - 13115*wealth/7011 + 33871/7011
- noninteger: k=1/4, method=positive_jensen, id=positive_jensen:direct:0:1/4
  - 精确前因子 C = 334074665421/250000000000
  - 精确收缩上界 rho = 483584105067/500000000000
  - eta = 1600*wealth**2/7011 - 13115*wealth/7011 + 33871/7011

## 在 n=10 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 2484/779
  - 精确收缩上界 rho = 7/8
  - eta = 1600*wealth**2/7011 - 13115*wealth/7011 + 33871/7011
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 2484/779
  - 精确收缩上界 rho = 7/8
  - eta = 1600*wealth**2/7011 - 13115*wealth/7011 + 33871/7011
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 275843253841/100000000000
  - 精确收缩上界 rho = 889727566167/1000000000000
  - eta = 1600*wealth**2/7011 - 13115*wealth/7011 + 33871/7011

## 在 n=20 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 240304/67669
  - 精确收缩上界 rho = 111/128
  - eta = 167450*wealth**2/609021 - 1355155*wealth/609021 + 3350441/609021
- rational: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 240304/67669
  - 精确收缩上界 rho = 111/128
  - eta = 167450*wealth**2/609021 - 1355155*wealth/609021 + 3350441/609021
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:1:7/8
  - 精确前因子 C = 1515461265617/500000000000
  - 精确收缩上界 rho = 882772677603/1000000000000
  - eta = 167450*wealth**2/609021 - 1355155*wealth/609021 + 3350441/609021

## 在 n=50 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 176/43
  - 精确收缩上界 rho = 221/256
  - eta = 41*wealth**2/129 - 338*wealth/129 + 275/43
- rational: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 176/43
  - 精确收缩上界 rho = 221/256
  - eta = 41*wealth**2/129 - 338*wealth/129 + 275/43
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:2:7/8
  - 精确前因子 C = 686386418201/200000000000
  - 精确收缩上界 rho = 879292299569/1000000000000
  - eta = 41*wealth**2/129 - 338*wealth/129 + 275/43

## 在 n=100 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 176/43
  - 精确收缩上界 rho = 221/256
  - eta = 41*wealth**2/129 - 338*wealth/129 + 275/43
- rational: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 176/43
  - 精确收缩上界 rho = 221/256
  - eta = 41*wealth**2/129 - 338*wealth/129 + 275/43
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:2:7/8
  - 精确前因子 C = 686386418201/200000000000
  - 精确收缩上界 rho = 879292299569/1000000000000
  - eta = 41*wealth**2/129 - 338*wealth/129 + 275/43

## 在 n=200 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 176/43
  - 精确收缩上界 rho = 221/256
  - eta = 41*wealth**2/129 - 338*wealth/129 + 275/43
- rational: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 176/43
  - 精确收缩上界 rho = 221/256
  - eta = 41*wealth**2/129 - 338*wealth/129 + 275/43
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:2:7/8
  - 精确前因子 C = 686386418201/200000000000
  - 精确收缩上界 rho = 879292299569/1000000000000
  - eta = 41*wealth**2/129 - 338*wealth/129 + 275/43

## 在 n=500 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:3
  - 精确前因子 C = 352/31
  - 精确收缩上界 rho = 441/512
  - eta = 191*wealth**2/279 - 1918*wealth/279 + 4895/279
- rational: k=1, method=direct_polynomial, id=direct:3
  - 精确前因子 C = 352/31
  - 精确收缩上界 rho = 441/512
  - eta = 191*wealth**2/279 - 1918*wealth/279 + 4895/279
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:3:7/8
  - 精确前因子 C = 838075892909/100000000000
  - 精确收缩上界 rho = 438775686383/500000000000
  - eta = 191*wealth**2/279 - 1918*wealth/279 + 4895/279

## 在 n=1000 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:3
  - 精确前因子 C = 352/31
  - 精确收缩上界 rho = 441/512
  - eta = 191*wealth**2/279 - 1918*wealth/279 + 4895/279
- rational: k=1, method=direct_polynomial, id=direct:3
  - 精确前因子 C = 352/31
  - 精确收缩上界 rho = 441/512
  - eta = 191*wealth**2/279 - 1918*wealth/279 + 4895/279
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:3:7/8
  - 精确前因子 C = 838075892909/100000000000
  - 精确收缩上界 rho = 438775686383/500000000000
  - eta = 191*wealth**2/279 - 1918*wealth/279 + 4895/279

## 正幂与倒数路线

| n | 正整数幂 | 正非整数幂 | 倒数幂 | 合并最优 |
|---|---:|---:|---:|---:|
| 5 | 1 | 1 | 1 | 1 |
| 10 | 0.838870001529 | 0.857497437807 | 0.469585435869 | 0.469585435869 |
| 20 | 0.205414654841 | 0.250352824847 | 0.00257689466063 | 0.00257689466063 |
| 50 | 0.00262820738265 | 0.00552334507631 | 3.87539385422e-11 | 3.87539385422e-11 |
| 100 | 1.68762149992e-06 | 8.88926121586e-06 | 9.21409488255e-25 | 9.21409488255e-25 |
| 200 | 6.95834386712e-13 | 2.30246295289e-11 | 4.93075121485e-52 | 4.93075121485e-52 |
| 500 | 4.36008760737e-32 | 3.62708984809e-28 | 3.88483768236e-134 | 3.88483768236e-134 |
| 1000 | 1.67420818824e-64 | 1.56976007513e-56 | 5.62343494624e-271 | 5.62343494624e-271 |
