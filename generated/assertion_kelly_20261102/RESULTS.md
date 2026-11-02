# Kelly 双边退出：Assertion violation 实验

日期：2026-11-02（Asia/Shanghai）。实现前仓库已提交并推送到 GitHub main，
备份提交 `c1bfcbe`。本报告中的概率均不条件化于终止。

## 程序与目标

`kelly_double_bound.pp` 保持初值 wealth=1、round=0，每轮以 0.6 概率乘 1.2，
以 0.4 概率乘 0.8；守卫为 `wealth >= 0.5 and wealth < 2`。
只把末尾事件标记改为 `refute (wealth < 0.5);`：下界退出失败，上界退出正常。
首次跌破下界就会退出，所以目标等于“最终从下界退出”的概率。

主体求解执行 note §2.2 的完整一阶矩收缩路线，H=1、k=1、delta=1/1000000。
搜索一般多项式的次数和系数，不保留整数幂分解；不执行 §2.3 比较实验。

## 环境

- Python：3.11.15；环境 `contractive-frontend-test-20260814`。
- Python 路径：`/home/sunzhouyue/.conda/envs/contractive-frontend-test-20260814/bin/python`。
- CVXPY 1.9.3、MOSEK 11.2.6、NumPy 2.4.6、SciPy 1.17.1。
- 真实 MOSEK 求解，沿用原有单线程、容差、时间限制、精确重构及修复配置。

以下命令从项目目录执行，PATH 指向该环境；复跑需使用新的输出目录。

## 合成结果

仅指定源码和目标的默认流程：

```bash
python -m contractive_tool solve kelly_double_bound.pp --goal assertion_violation \
  --out-dir generated/assertion_kelly_20261102/default
```

结果 `proved`，68.18 秒，尝试 D=1、2，共 20 个参数点、40 次求解尝试。
得到 6 份已验证证书，最终选择 D=2、c=511/512：

```text
Pr(finite exit with wealth < 0.5) <= 0.622866785
```

上面的十进制数向上取整；精确有理数保存在 [默认结果](default/summary.json)。
[默认结果独立重放](default_check.json) 为 proved。

进一步显式指定参数，并尝试三次模板：

```bash
python -m contractive_tool solve kelly_double_bound.pp --goal assertion_violation \
  --initial-degree 2 --max-degree 3 --c-values 999/1000 9999/10000 \
  --continue-after-success --max-attempts-per-point 3 --total-seconds 300 \
  --out-dir generated/assertion_kelly_20261102/search
```

| 次数 | c | 精确验证后的 A（近似显示） | 状态 |
|---|---|---|---|
| 2 | 999/1000 | 0.6204868461709707 | proved |
| 2 | 9999/10000 | 0.6183411806246991 | proved，最终选择 |
| 3 | 999/1000 | 无 | numerical_issue |
| 3 | 9999/10000 | 无 | numerical_issue |

总耗时 53.50 秒，4 个参数点、10 次求解尝试。两份成功证书均通过
`rational_affine_reconstruction_exact_psd` 验证，成功编码为 Schmüdgen。
三次模板没有产生通过验证的结果，不能据此断言不存在更紧的高次证书。

**本次主体合成给出的已认证上界（向上取整）是：**

```text
Pr(finite exit with wealth < 0.5) <= 0.618341181
```

最佳证书的循环头多项式近似为：

```text
eta(wealth, round) = 0.169637712819*wealth^2
                    - 1.01837064378*wealth + 1.46707411159
```

round 的系数为零。这个显示值经过舍入，不能替代精确证明；所有位置的精确有理
多项式、Gram 见证、原始终端 eta_normal=1/1000000 和 eta_failure=1 见
[证书](search/analyses/assertion_violation/degrees/2/c-002/attempts/002/certificate.json)。

单独的一次 Putinar 尝试也被归档在 [d2](d2/summary.json)：数值求解成功但未恢复
精确证书，因此正确返回 no_certificate_found，并未作为概率结论使用。

## 独立重放和事后求值

```bash
python -m contractive_tool verify generated/assertion_kelly_20261102/search
python -m contractive_tool evaluate generated/assertion_kelly_20261102/search
python -m contractive_tool evaluate generated/assertion_kelly_20261102/search \
  --event late_failure --clock program_entry --n 100
```

- [独立重放](independent_check.json)：proved，重新认证 2 份证书。
- [最终违规概率](eventual.json)：上界约 0.6183411806246991。
- [入口第 100 步之后才违规](late_100.json)：上界约 0.5619735994022484。
  后者选择 c=999/1000 的另一份证书，按 2 步初始化前缀修正，指数为 99。
  这里计的是 pCFG 转移，不是循环轮数；它也不是累计违规概率。

重放从归档源码重新建立语义域、原始矩义务及锥模型，检查精确见证和输出公式，
不调用求解器，不只检查 solver status 或文件哈希。

## 独立参考概率

为区分“合成上界”和“实际概率”，额外执行与主体分析独立的精确整数路径递推：

```bash
python examples/kelly_exit_reference.py --rounds 1000 \
  --out generated/assertion_kelly_20261102/reference.json
```

在第 n 轮，以赢的次数 u 聚合仍处于循环内的路径：
wealth=`6**u * 4**(n-u) / 5**n`，路径质量用分母 `5**n` 的整数表示。
每次精确判断 `<1/2` 和 `>=2`，吸收已退出路径，只传播存活质量。

“已下界退出的质量”给出下界；加上全部存活质量给出最终下界退出概率的上界。
不需要假设终止，也不依赖 Monte Carlo 或浮点比较。
1000 轮后剩余质量约 `1.96130273626654e-39`；将精确区间向外舍入得到：

```text
0.311575478865929 <= Pr(finite exit with wealth < 0.5)
                <= 0.311575478865930
```

因此该例实际概率约 **31.1575478866%**；主体多项式证书上界约 **61.8341181%**。
主体证书是保守上界，不是精确概率估计。独立递推只针对这个固定 Kelly 例子，
不是通用 assertion 分支的特殊求解路径，也没有把 1000 轮设成原程序 horizon。
精确分数见 [reference.json](reference.json)。

## Tailbound 回归与测试

同一份改写后的源码仍可以分析完整循环的终止尾界：

```bash
python -m contractive_tool solve kelly_double_bound.pp --goal tailbound \
  --initial-degree 1 --max-degree 1 --c-values 99/100 \
  --tail-rule round_survival --no-symbolic-workflow --total-seconds 60 \
  --out-dir generated/assertion_kelly_20261102/tail_regression
```

结果 `proved`，1.98 秒：

```text
Pr(K > n) <= min(1, (113003675/59825304)*(99/100)^n)
```

K 计完整循环轮数，上下界退出均结束生存过程。见
[tailbound 结果](tail_regression/summary.json)。

全量回归命令：

```bash
PATH=/home/sunzhouyue/.conda/envs/contractive-frontend-test-20260814/bin:$PATH \
  python -m pytest -q
```

新增测试覆盖原始正常终端贡献、所有中间失败转移、正性参数、随机初始化、时间前缀、
真实后端求解、独立重放、篡改拒绝、未知数值状态、非终止自环、目标排序和独立概率
递推的显式路径核对。最终全量回归结果为 **185 passed in 56.93s**，无失败、无跳过；
输出见 [regression.log](regression.log)。

实现前在正确 PATH 下的基线为 170 passed；首次只指定 Python 路径时有 3 个 CLI
测试因找不到 `contractive` 可执行文件失败，修正 PATH 后全部通过。这不是代码回归。
