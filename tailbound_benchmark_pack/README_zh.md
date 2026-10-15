# Tail-bound 实验样例整理包

## 内容与来源状态

本包包含 **12 份按论文程序图/附录整理的中间伪代码规格**，不是作者原始复现包，不是 ginfer 或 OOPSLA 工具可直接解析的输入文件。本包未运行任何基线求解器。

程序来自三篇论文：PLDI 2021 的中心矩分析、其复用的 TACAS 2019 高阶矩基准，以及 OOPSLA 2024 的资源使用分析。`manifest.json` 记录每个样例的原编号、PDF页码、初值、分布、变换和分组。

公开入口已核实，但当前未成功取得 ginfer Bitbucket 分支或 OOPSLA source.zip 的内部文件；因此没有虚构原仓库文件名，也没有把以下重建代码标为作者源码。OOPSLA归档仍保留可供用户获取的 source.zip、image.tgz、README等入口。

## 首选实验组合

先用 `01`–`05` 建立共同的常规终止时间实验；`06` 是原论文的大初始值变体。`07` 是多项式尾概率边界，`08` 是非几乎必然终止边界。`09`–`11` 需要恶魔非确定性扩展，不能直接按用户当前语法输入。`12` 是终止输出成本的尾概率，不属于运行时间尾概率。

## 统一语义：务必先读

### 1. 计时口径

除 `12` 外，`C` 明确表示**循环体执行次数**，一次完整循环计一次。初始化、守卫判断、单独的分支选择与采样均不另行计入C。无限循环的总成本为正无穷。

`C` 是逻辑计数器/成本标注，不是为了复现原CFG而加入的有偿步骤。TACAS2019定义的到达时间是pCFG转移次数，PLDI2021比较中的程序计费也应按原输入核对。这里将 refute 目标转成while退出并统一计数，**没有保持原CFG步数**。因而本包参考曲线不能直接与原论文按CFG时间给出的数值并列。

针对用户原始目标 T_P（每条CFG边计一次），更合适的移植办法是：保留同一个原CFG，在所有工具中对每条原边赋单位成本。额外插入的监测操作不再次计时；若某工具必须为它们建立节点，应使用零成本边。不要假定“一个循环恒等于若干条CFG边”，有些程序的分支长度不同。

本包参考数据统一为 `P(C > n)`；不少论文写 `P(T >= d)`。C整数时，`P(C > n)=P(C >= n+1)`。`12`的成本为实值，不能用整数移位规则。

### 2. refute 与采样

TACAS2019附录中 `refute(phi)` 用于指定目标/终止配置，不是通常的“assert(phi)要求phi为真”。本包在phi满足时退出，不把终止事件颠倒。

所有 Uniform 都是**连续**均匀分布；每次采样均为新的独立样本。`prob(0.6)`等数值表示准确的概率常数，不应先经过浮点舍入再用于证书验证。

### 3. 非确定性

`if *` 表示恶魔非确定性。尾界应对所有允许的调度器成立，或取最坏调度器的上确界。将其替换成公平硬币会改变程序。

`10_rw_2d_demonic.ppl` 以实验附录Listing1.6为准：先选择坐标再采样。论文正文Figure1将抽样写在选择之前，可能改变调度器信息；本包不混用这两种版本。其他非确定性例子也保留原顺序。

论文输入中的不变量注释没有复制，也没有被本包重新证明。特别是带非确定性的程序，应重新检查不变量的归纳性；不能为了成功求解而把未经证明的可达范围当假设。

### 4. 递归改写

`05_rdwalk_uniform.ppl` 的原程序是 `更新x; call rdwalk; tick(1)`，**不是尾递归**。改成循环保留几乎必然终止执行中的随机更新序列与最终总tick数，不保留调用/返回开销、递归深度和中间时刻的成本轨迹。

### 5. 两个方法边界

`07` 满足 `P(C >= d)=1/(d+1)^2`（d为非负整数），故 `P(C > n)=1/(n+2)^2`。它没有对所有n成立的有限前因子严格指数尾界。应作为重尾边界，而不是要求统一严格收缩方法必然成功的正例。

`08` 具有正的不终止概率；无条件运行时间尾概率不会趋零。证明小阈值概率是有意义的，但不能要求一个始终衰减到0的全局指数界。可测试分区/随机不变量等更丰富分析，或标记超出当前方法覆盖范围。

## 样例目录

### 01_coupon2 — Two-coupon collector

- 分组：`core`。原编号：`(1-1)`。
- 来源：[Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments](https://arxiv.org/pdf/1811.06779v2)，Appendix E, Listing 1.1, PDF pp.34-35。
- 共同基准依据：W2021, Section 6 / Appendix H, (1-1)。
- 初始状态：`{"c0": 0, "c1": 0}`。
- 分布：Each coupon is selected with probability 1/2; fresh independent choices.
- 注：将 refute(c0+c1>1) 改成集齐后退出；删除输入不变量注释；计时改为抽取次数。

```text
c0 := 0;
c1 := 0;
C := 0;
while c0 + c1 < 2 do
    C := C + 1;
    if prob(0.5) then
        c0 := 1
    else
        c1 := 1
    fi
od
```

### 02_coupon4 — Four-coupon collector

- 分组：`core`。原编号：`(1-2)`。
- 来源：[Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments](https://arxiv.org/pdf/1811.06779v2)，Appendix E, Listing 1.2, PDF p.35。
- 共同基准依据：W2021, Section 6 / Appendix H, (1-2)。
- 初始状态：`{"c0": 0, "c1": 0, "c2": 0, "c3": 0}`。
- 分布：Two independent fair branches choose each of 4 coupons with probability 1/4.
- 注：保留四个标志位与嵌套概率分支；未改写成状态依赖概率。C 统计一次完整抽取，不统计抛硬币次数。

```text
c0 := 0;
c1 := 0;
c2 := 0;
c3 := 0;
C := 0;
while c0 + c1 + c2 + c3 < 4 do
    C := C + 1;
    if prob(0.5) then
        if prob(0.5) then
            c0 := 1
        else
            c1 := 1
        fi
    else
        if prob(0.5) then
            c2 := 1
        else
            c3 := 1
        fi
    fi
od
```

### 03_rw_int — Integer random walk

- 分组：`core`。原编号：`(2-1)`。
- 来源：[Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments](https://arxiv.org/pdf/1811.06779v2)，Appendix E, Listing 1.3, PDF p.35。
- 共同基准依据：W2021, Section 6 / Appendix H, (2-1)。
- 初始状态：`{"x": 1}`。
- 分布：Step -1 with probability 0.6; +1 with probability 0.4.
- 注：原目标为 refute(x<1)；本初值和整数更新下等于首次到达0。原文 CFG 时间与本文件 C 不同。

```text
x := 1;
C := 0;
while x >= 1 do
    C := C + 1;
    if prob(0.6) then
        x := x - 1
    else
        x := x + 1
    fi
od
```

### 04_rw_real — Real-valued random walk

- 分组：`core`。原编号：`(2-2)`。
- 来源：[Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments](https://arxiv.org/pdf/1811.06779v2)，Appendix E, Listing 1.4, PDF p.35。
- 共同基准依据：W2021, Section 6 / Appendix H, (2-2)。
- 初始状态：`{"x": 2}`。
- 分布：Probability 0.7: subtract continuous Uniform[0,1]; otherwise add independent Uniform[0,1].
- 注：保留先分支后抽样、目标 x<0 和 guard x>=0。Uniform 是连续分布。

```text
x := 2;
C := 0;
while x >= 0 do
    C := C + 1;
    if prob(0.7) then
        r ~ Uniform(0, 1);
        x := x - r
    else
        r ~ Uniform(0, 1);
        x := x + r
    fi
od
```

### 05_rdwalk_uniform — PLDI running example: uniform-increment walk

- 分组：`core`。原编号：`rdwalk / Figure 2`。
- 来源：[Central Moment Analysis for Cost Accumulators in Probabilistic Programs](https://arxiv.org/pdf/2001.10150)，Figure 2 / Example 2.1, PDF p.3。
- 初始状态：`{"x": 0, "d": "symbolic positive parameter"}`。
- 分布：Continuous Uniform[-1,2] increment on each update.
- 注：原程序递归调用后执行 tick(1)，不是尾递归；本循环保留终止执行上的更新序列与总 tick 数，未保留调用/返回 CFG 开销。建议 d=1,5,10,20 为新增实例，不冒充原实验参数。

```text
# Parameter: d > 0. Set d before running a concrete instance.
x := 0;
C := 0;
while x < d do
    C := C + 1;
    r ~ Uniform(-1, 2);
    x := x + r
od
```

### 06_rw_real_large — Large-initial-value real random walk

- 分组：`numerical_stress`。原编号：`Figure 4, variant of (2-2)`。
- 来源：[Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments](https://arxiv.org/pdf/1811.06779v2)，Figure 4, PDF p.12。
- 初始状态：`{"x": 200000000}`。
- 分布：Same distribution as (2-2).
- 注：这是论文确实给出的 (2-2) 参数变体，测试巨大初始数值下的数值/符号稳定性；不是新算法。

```text
x := 200000000;
C := 0;
while x >= 0 do
    C := C + 1;
    if prob(0.7) then
        r ~ Uniform(0, 1);
        x := x - r
    else
        r ~ Uniform(0, 1);
        x := x + r
    fi
od
```

### 07_polynomial_tail — Polynomially decreasing iteration tail

- 分组：`heavy_tail_boundary`。原编号：`Appendix G example`。
- 来源：[Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments](https://arxiv.org/pdf/1811.06779v2)，Appendix G, PDF p.38。
- 初始状态：`{"m": 1, "r": "initial fresh Uniform[0,1]"}`。
- 分布：Fresh continuous Uniform[0,1] per guard stage.
- 注：原变量 n 改名 m，避免与尾概率阈值混淆。准确公式 P(C>=d)=1/(d+1)^2；因此 P(C>n)=1/(n+2)^2。几乎必然终止但没有对所有 n 成立的有限前因子严格指数尾界。原文报告一次多项式模板一阶矩实验，而非完整中心矩曲线。

```text
m := 1;
C := 0;
r ~ Uniform(0, 1);
while r * (m + 1) * (m + 1) <= m * m do
    C := C + 1;
    r ~ Uniform(0, 1);
    m := m + 1
od
```

### 08_escape_200 — Random walk with a rare escape region

- 分组：`non_ast_boundary`。原编号：`Figure 3b`。
- 来源：[Quantitative Bounds on Resource Usage of Probabilistic Programs](https://research-explorer.ista.ac.at/download/17162/17182/2024_ProcACMProgLanguage_Chatterjee.pdf)，Figure 3b, PDF p.8; Table 2, PDF p.24。
- 初始状态：`{"x": 0}`。
- 分布：Always add Uniform[-1,0.5]; after this update, add Uniform[-1,2] only if x>=200.
- 注：以 Figure 3b 的代码为准；不是按旧 x 在两个分布中二选一。原 tick(1) 改记 C。存在不终止概率，C=+infinity on nonterminating runs。Table2 原文报告 P(C>=50)<=0.1 和 P(C>=90)<=0.05；并非真值，也非本包运行结果。

```text
x := 0;
C := 0;
while x >= 0 do
    C := C + 1;
    r1 ~ Uniform(-1, 0.5);
    x := x + r1;
    if x >= 200 then
        r2 ~ Uniform(-1, 2);
        x := x + r2
    else
        skip
    fi
od
```

### 09_rw_1d_demonic — Adversarial one-dimensional walk

- 分组：`nondeterminism_extension`。原编号：`(2-3)`。
- 来源：[Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments](https://arxiv.org/pdf/1811.06779v2)，Appendix E, Listing 1.5, PDF p.36。
- 共同基准依据：W2021, Appendix H, (2-3)。
- 初始状态：`{"x": 2}`。
- 分布：Demonic choice after an initial probabilistic update; branch probabilities match Listing 1.5.
- 注：以附录执行语句重建；原局部不变量注释未检查，未复制。调度器可以观察其选择前已发生的随机结果，不可把 * 换成 prob(0.5)。

```text
x := 2;
C := 0;
while x > 0 do
    C := C + 1;
    if prob(0.8) then
        skip
    else
        if prob(0.5) then
            x := x + 1
        else
            x := x + 2
        fi
    fi;
    if * then
        if prob(0.875) then
            x := x - 1
        else
            skip
        fi
    else
        if prob(0.8) then
            skip
        else
            if prob(0.5) then
                x := x + 1
            else
                x := x + 2
            fi
        fi;
        x := x - 1
    fi
od
```

### 10_rw_2d_demonic — Two-dimensional demonic walk

- 分组：`nondeterminism_extension`。原编号：`(2-4)`。
- 来源：[Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments](https://arxiv.org/pdf/1811.06779v2)，Appendix E, Listing 1.6, PDF p.36。
- 共同基准依据：W2021, Appendix H, (2-4)。
- 初始状态：`{"x": 2, "y": 2}`。
- 分布：Choose coordinate demonically, then sample continuous Uniform[-2,1].
- 注：依据实验附录 Listing1.6：先选择坐标，后抽样。正文 Figure1 的显示顺序不同，不把两者自动认作相同调度信息模型。两个 refute 目标转换为 x<=0 OR y<=0 时退出。

```text
x := 2;
y := 2;
C := 0;
while x > 0 and y > 0 do
    C := C + 1;
    if * then
        r ~ Uniform(-2, 1);
        x := x + r
    else
        r ~ Uniform(-2, 1);
        y := y + r
    fi
od
```

### 11_rw_2d_variant — Two-dimensional variant with probabilistic branches

- 分组：`nondeterminism_extension`。原编号：`(2-5)`。
- 来源：[Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments](https://arxiv.org/pdf/1811.06779v2)，Appendix E, Listing 1.7, PDF pp.36-37。
- 共同基准依据：W2021, Appendix H, (2-5)。
- 初始状态：`{"x": 3, "y": 2}`。
- 分布：Demonic choice, then probability 0.7/0.3, then a fresh continuous uniform sample.
- 注：目标为 x<=y。保持概率/非确定性/采样的原有顺序；去除未核验的不变量注释。

```text
x := 3;
y := 2;
C := 0;
while x > y do
    C := C + 1;
    if * then
        if prob(0.7) then
            r ~ Uniform(-2, 1);
            x := x + r
        else
            r ~ Uniform(-2, 1);
            y := y + r
        fi
    else
        if prob(0.7) then
            r ~ Uniform(-1, 2);
            y := y + r
        else
            r ~ Uniform(-1, 2);
            x := x + r
        fi
    fi
od
```

### 12_signed_cost_multiplicative — Multiplicative update with signed costs

- 分组：`output_cost_supplement`。原编号：`Figure 3a / Example 1 (not Example 1 Inf)`。
- 来源：[Quantitative Bounds on Resource Usage of Probabilistic Programs](https://research-explorer.ista.ac.at/download/17162/17182/2024_ProcACMProgLanguage_Chatterjee.pdf)，Figure 3a / Example 3.1, PDF pp.7-8; Table 1 Example 1。
- 初始状态：`{"x": 1, "y": 1}`。
- 分布：Continuous Uniform[-1,0.5] for x and an independent fair coin for the multiplier of y.
- 注：补充成本尾概率样例，不是 Table2 的 Example1Inf。原初始 tick(y) 与后续 tick(+-y/2) 改写为成本变量C；完整更新后C=y。查询终止输出成本，不查询循环次数。

```text
x := 1;
y := 1;
C := y;
while x >= 1 do
    r ~ Uniform(-1, 0.5);
    x := x + r;
    if prob(0.5) then
        C := C - 0.5 * y;
        y := 0.5 * y
    else
        C := C + 0.5 * y;
        y := 1.5 * y
    fi
od
```

## 严格参考尾概率：不依赖蒙特卡洛

`reference/reference_tails.py` 使用标准库整数/有理数递推，计算：

- 2/4类均匀集券：有限状态概率递推。
- 整数随机游走：有限步内所有未吸收状态的精确质量递推。
- 多项式尾样例：望远镜乘积公式。

脚本的“精确”针对本包**迭代次数**的数学模型，不针对作者CFG，也不是某个基线工具输出。分子和分母精确；十进制列只是显示近似。没有用浮点采样估计极小概率。

```bash
cd tailbound_benchmark_pack
python reference/reference_tails.py all --max-n 200 --output reference/tails_iteration_exact.csv
python -m unittest discover -s reference -p 'test_*.py' -v

# 以下是自行参数化的新增实例，不属于论文默认样例：
python reference/reference_tails.py coupon --coupons 8 --max-n 300 --output /tmp/cc8.csv
python reference/reference_tails.py walk --start 5 --down-prob 0.55 --max-n 300 --output /tmp/walk.csv
```

参考脚本已通过7项单元测试（含小规模路径穷举和闭式公式交叉核对），日志见 `reference/test_results.txt`。这些测试不代表基线工具已复现。

已附 `reference/tails_iteration_exact.csv`：默认4个实例在n=0..200的结果，共804行。大整数递推不是可扩展的无限状态模型检查器；对于大阈值/巨大初值，需另行考虑代数或经过认证的数值方法。

## OOPSLA2024 原文尾界列表

`oopsla2024_tail_inventory.json` 逐项列出Table2中的名字及两个已发表的阈值/概率对。此表**不是我们的实验结果，也不是精确概率**；仅 `Figure 3b` 对应的完整重建代码纳入本包。不能用Table1的`Example1`冒充Table2的`Example1Inf`。

Table2的 `P1/P5/P7/P8/P10/P11/P12/P17/P22` 对应CAV2022扩展版相应Figure编号；`Example1Inf`–`Example5Inf` 在OOPSLA2024扩展版Appendix I。区块链样例细节在Appendix J。本包未成功读取这些附录/归档代码，因此没有补写未经核验的程序。

可见Table2为5+10+2=17个命名条目；正文写18。本清单按表内可见条目转录，不虚构额外一行。

## 原始论文、代码与归档链接

### K2019: Tail Probabilities for Randomized Program Runtimes via Martingales for Higher Moments (TACAS 2019)

- [paper](https://doi.org/10.1007/978-3-030-17465-1_8)
- [pdf](https://arxiv.org/pdf/1811.06779v2)

### W2021: Central Moment Analysis for Cost Accumulators in Probabilistic Programs (PLDI 2021)

- [paper](https://doi.org/10.1145/3453483.3454062)
- [pdf](https://arxiv.org/pdf/2001.10150)
- [author_page](https://stonebuddha.github.io/publication/wanghr21a/)
- [code_entry](https://bitbucket.org/probabilistic/ginfer/src/pldi21/)

### C2024: Quantitative Bounds on Resource Usage of Probabilistic Programs (OOPSLA 2024)

- [paper](https://doi.org/10.1145/3649824)
- [pdf](https://research-explorer.ista.ac.at/download/17162/17182/2024_ProcACMProgLanguage_Chatterjee.pdf)
- [code_entry](https://github.com/djordjezikelic/prob-prog-quantitative-bounds)
- [artifact](https://zenodo.org/records/10457566)
- [extended_version](https://hal.science/hal-04491689)

### C2022: Sound and Complete Certificates for Quantitative Termination Analysis of Probabilistic Programs (CAV 2022)

- [paper](https://doi.org/10.1007/978-3-031-13185-1_4)
- [artifact](https://tobias.meggendorfer.de/assets/data/2022_cav_prob_program_termination_code.zip)
- [extended_version](https://hal.science/hal-03675086)

## 重现实验建议（本整理提出，非原论文设定）

先固定同一程序、同一初始状态、同一计时口径，再比较概率上界。推荐主组为CC2、CC4、整数/实数随机游走、rdwalk；大初值作为数值压力组；多项式尾和非终止分别独立报告；非确定性组等语言/语义支持后再加入。

既要报告上界，也要区分成功、证书未知、超时、语法不支持和理论假设不满足。重参数化后的实例必须标为扩展基准。参数搜索、阈值搜索和不变量生成的时间应计入各工具总成本。

如果势函数只允许有限次数多项式，整数随机游走在无界x区域上不一定满足统一严格乘性收缩：对于正的非零多项式V，`(0.6 V(x-1)+0.4 V(x+1))/V(x)` 随x趋于无穷接近1。这是证书表达能力问题，不应通过未经证明的x上界绕过。对集券，未收集数量本身可作为一步收缩势函数（完整抽取为一步）。这些是根据样例做的数学观察，而不是归因于原论文的新主张。
