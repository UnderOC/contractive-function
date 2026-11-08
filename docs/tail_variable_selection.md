# Tailbound 模板变量筛选

`--tail-variables wealth` 将 tailbound 的待合成函数限制为所列程序变量的多项式。
默认仍使用全部程序变量；这个选项目前是显式选择，不会自动猜测哪些变量无关。
与 `--assertion-variables` 相互独立。

```bash
python -m contractive_tool solve kelly_double_bound.pp --goal tailbound \
  --tail-rule round_survival --tail-variables wealth \
  --initial-degree 2 --max-degree 8 --degree-step 2 --continue-after-success \
  --c-values 47/50 19/20 97/100 99/100 --max-attempts-per-point 3 \
  --total-seconds 300 --comparison-n 5 20 50 100 \
  --out-dir generated/kelly_tail_selected_new
python -m contractive_tool verify generated/kelly_tail_selected_new
python -m contractive_tool evaluate generated/kelly_tail_selected_new --n 100
```

输出目录需为空或不存在。次数及 c 的选择影响数值求解结果；以上是使用示例，
本次实验的确切命令见下方报告。仍使用 CVXPY/MOSEK。

## 覆盖范围和证明含义

- 直接逐转移 `late_bad_exit`、Boolean 整轮、symbolic 整轮模板均支持变量筛选。
- 后续 Cauchy 联合搜索在有种子和无种子时都遵守选择；固定模板阶段继承直接阶段的函数。
  显式 workflow 配置若含被排除的变量，该联合阶段报告冲突，不会悄悄加入这些变量。
- 源程序、初始化、不变量、转移、随机分布、存活守卫及循环时钟均保留。
  变量筛选仅限制函数的形式，不是删除源程序语句。
- 直接多项式正性编码复用 assertion 的域约简：对每条证明义务，保留残差涉及的变量
  以及由域约束与之相连的全部变量。仅删除断开的约束分量，在投影的超集上证明。
  比如 `wealth := round` 会让 round 重新出现在残差和认证域中。
  因而用户即使省略一个真正影响行为的变量，也不会因此得到不健全的证明。
- 变量选择写入 manifest、直接多项式问题及证书上下文。symbolic workflow 的 `verify`
  重建相同的模板和证明义务，检查精确见证与最终候选的变量范围。
  原有非 symbolic 路径的 CLI 重放覆盖范围没有在此次扩展。

对于 Kelly，循环中的 round 仅计数，因此可以只合成 eta(wealth)。尾界中的 n 是外部
查询的循环轮数，不要求 eta 含 round。最终比较应按 `min(1,A*c**n)`；只比较 c
或只比较 A 都不足以判断某个查询点的优劣。

模板变量减少在数学上缩小了函数搜索空间。实际改善来自降低数值问题维度、启用
现有一维区间编码及更容易搜索高次模板，不意味着受限模板在理论上比全变量模板更强。

[Kelly 实验结果和重现命令](../generated/tail_kelly_variables_20261104/RESULTS.md)
