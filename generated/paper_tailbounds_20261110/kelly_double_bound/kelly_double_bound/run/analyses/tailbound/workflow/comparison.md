# 整数与有理数指数尾界比较

以下最优指本次实际搜索并通过精确验证的候选中的最优，不代表全局最优。
事件为 K>n，K 计完整循环轮数；表中浮点数仅作展示，精确值保存在 comparisons.json。
有理数集合包含整数；另列非整数候选，避免把整数结果误称为非整数改进。

| n | 直接多项式界 (k=1) | 最佳整数 k | 整数界 | 最佳有理数 k | 有理数界 | 整数界/有理数界 |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 1 | 1 | 1 | 1 | 1 | 1 |
| 10 | 1 | 1 | 1 | 1 | 1 | 1 |
| 20 | 1 | 1 | 1 | 1 | 1 | 1 |
| 50 | 1 | 1 | 1 | 1 | 1 | 1 |
| 100 | 0.494054043884 | 1 | 0.494054043884 | 1 | 0.494054043884 | 1 |
| 200 | 0.0849968340866 | 1 | 0.0849968340866 | 1 | 0.0849968340866 | 1 |
| 500 | 0.000180514329187 | 1 | 0.000180514329187 | 1 | 0.000180514329187 | 1 |
| 1000 | 5.71478468386e-09 | 1 | 5.71478468386e-09 | 1 | 5.71478468386e-09 | 1 |

每份候选的形式是 `min(1, C * rho**n)`，均对所有非负整数 n 有效。

## 在 n=5 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- noninteger: k=1/4, method=positive_jensen, id=positive_jensen:direct:0:1/4
  - 精确前因子 C = 1242880080989/1000000000000
  - 精确收缩上界 rho = 996070650933/1000000000000
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987

## 在 n=10 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- noninteger: k=1/4, method=positive_jensen, id=positive_jensen:direct:0:1/4
  - 精确前因子 C = 1242880080989/1000000000000
  - 精确收缩上界 rho = 996070650933/1000000000000
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987

## 在 n=20 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- noninteger: k=1/4, method=positive_jensen, id=positive_jensen:direct:0:1/4
  - 精确前因子 C = 1242880080989/1000000000000
  - 精确收缩上界 rho = 996070650933/1000000000000
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987

## 在 n=50 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- noninteger: k=1/4, method=positive_jensen, id=positive_jensen:direct:0:1/4
  - 精确前因子 C = 1242880080989/1000000000000
  - 精确收缩上界 rho = 996070650933/1000000000000
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987

## 在 n=100 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- rational: k=1, method=direct_polynomial, id=direct:0
  - 精确前因子 C = 9514/3987
  - 精确收缩上界 rho = 63/64
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:0:7/8
  - 精确前因子 C = 267554531253/125000000000
  - 精确收缩上界 rho = 986314694673/1000000000000
  - eta = 712*wealth**2/1329 - 11935*wealth/3987 + 19313/3987

## 在 n=200 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 140378/31963
  - 精确收缩上界 rho = 251/256
  - eta = 45720*wealth**2/31963 - 245575*wealth/31963 + 340233/31963
- rational: k=1, method=direct_polynomial, id=direct:1
  - 精确前因子 C = 140378/31963
  - 精确收缩上界 rho = 251/256
  - eta = 45720*wealth**2/31963 - 245575*wealth/31963 + 340233/31963
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:1:7/8
  - 精确前因子 C = 14600914831/4000000000
  - 精确收缩上界 rho = 39315565609/40000000000
  - eta = 45720*wealth**2/31963 - 245575*wealth/31963 + 340233/31963

## 在 n=500 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 732638/128489
  - 精确收缩上界 rho = 1003/1024
  - eta = 260232*wealth**2/128489 - 1384845*wealth/128489 + 1857251/128489
- rational: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 732638/128489
  - 精确收缩上界 rho = 1003/1024
  - eta = 260232*wealth**2/128489 - 1384845*wealth/128489 + 1857251/128489
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:2:7/8
  - 精确前因子 C = 573364193813/125000000000
  - 精确收缩上界 rho = 982032485289/1000000000000
  - eta = 260232*wealth**2/128489 - 1384845*wealth/128489 + 1857251/128489

## 在 n=1000 选择的证书

- integer: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 732638/128489
  - 精确收缩上界 rho = 1003/1024
  - eta = 260232*wealth**2/128489 - 1384845*wealth/128489 + 1857251/128489
- rational: k=1, method=direct_polynomial, id=direct:2
  - 精确前因子 C = 732638/128489
  - 精确收缩上界 rho = 1003/1024
  - eta = 260232*wealth**2/128489 - 1384845*wealth/128489 + 1857251/128489
- noninteger: k=7/8, method=positive_jensen, id=positive_jensen:direct:2:7/8
  - 精确前因子 C = 573364193813/125000000000
  - 精确收缩上界 rho = 982032485289/1000000000000
  - eta = 260232*wealth**2/128489 - 1384845*wealth/128489 + 1857251/128489

## 正幂与倒数路线

| n | 正整数幂 | 正非整数幂 | 倒数幂 | 合并最优 |
|---|---:|---:|---:|---:|
| 5 | 1 | 1 | 1 | 1 |
| 10 | 1 | 1 | 1 | 1 |
| 20 | 1 | 1 | 1 | 1 |
| 50 | 1 | 1 | 0.976697656311 | 0.976697656311 |
| 100 | 0.494054043884 | 0.539576033323 | 0.803992308901 | 0.494054043884 |
| 200 | 0.0849968340866 | 0.11567177662 | 0.506843169331 | 0.0849968340866 |
| 500 | 0.000180514329187 | 0.000530209764616 | 0.111437525801 | 0.000180514329187 |
| 1000 | 5.71478468386e-09 | 6.12879208205e-08 | 0.00891594632911 | 5.71478468386e-09 |
