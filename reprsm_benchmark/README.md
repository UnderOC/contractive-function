# Assertion-violation 论文 benchmark 输入

来源：项目上层的 `assertion_violation.pdf`，*Quantitative Analysis of Assertion Violations in Probabilistic Programs*，arXiv:2011.14617v2（2020-12-01）。
PDF SHA-256：`12c87ad78a0c818d2736d84674681a0e004f051ba299d5373da2a27925488336`。
依据正文图 1–3、附录 E.1 图 4–12，以及表 1、2 的参数。

按用户要求，只收录能从论文确定执行行为的版本。论文有 12 类、36 个表格参数实例；这里收录其中 9 类的 27 个实例，以及 1 个 RdAdder 原文核对样例，共 **28 个 `.pp` 文件**。其余 9 个表格实例没有用推测模型补齐，具体原因见 [SOURCE_NOTES.md](SOURCE_NOTES.md)。

## 输入索引

| 家族 | 目录/文件 | 参数 | 断言违反事件 |
|---|---|---|---|
| Race | `pp/race_*.pp` | 初始 x=40、35、45，y=0 | 循环退出时 x<100 |
| Rdwalk | `pp/rdwalk_*.pp` | T>400、500、600 | 到达 x=100 后，迭代计数超过阈值 |
| 1DWalk | `pp/1dwalk_*.pp` | 初始 x=10、50、100 | 循环内 x>1000 |
| 2DWalk | `pp/2dwalk_*.pp` | (1000,10)、(500,40)、(400,50) | 循环更新后 x<1 |
| 3DWalk | `pp/3dwalk_*.pp` | (100,100,100)、(100,150,200)、(300,100,150) | 循环内 x+y+z>1000 |
| Prspeed | `pp/prspeed_*.pp` | T>150、200、250 | 循环内迭代计数超过阈值 |
| M1DWalk | `pp/m1dwalk_*.pp` | p=10^-7、10^-5、10^-4 | 无硬件故障地完成计算 |
| Newton | `pp/newton_*.pp` | p=0.0005、0.001、0.0015 | 无硬件故障地完成 41 次抽象迭代 |
| Ref | `pp/ref_*.pp` | p=10^-7、10^-6、10^-5 | 无硬件故障地完成三层抽象循环 |
| RdAdder 原文 | `literal/rdadderliteral_figure4.pp` | 图 4 固定条件 | x>200；该事件实际不可达，不是表 1 的偏差实验 |

**Hardware 三类的方向区别：**论文表 2 求成功完成概率的**下界**，这里沿用该成功事件，但运行当前 assertion_violation 分支求它的**上界**。Newton、Ref 图中未打印最终断言；依据正文 Hardware 定义和图 3 的 `assert false`，在成功完成路径显式补上违反事件。没有把硬件失败概率误当作论文目标，也没有声称复现表 2 下界。

## 转换规则

- 使用项目已有 `assert` 语法；没有新增语言或求解器。与 `refute` 一样，它把相应条件的违反送到 failure terminal。
- `switch` 的有限离散选择展开成等价的嵌套 `if prob(...)`；每个分支概率使用精确有限小数。
- 元组赋值拆成顺序赋值，仅用于右侧互不交叉依赖的更新。计数器 `t` 仍计原论文的循环迭代，不计增加的 CFG 节点。
- `exit` 用 0/1 标志 `alive` 编码，并保留 `alive=0 or alive=1` 不变量及 0.5 分隔的条件；故障后跳过后续随机检查和更新，最终进入正常终端；成功完成进入 failure terminal。该转换保留事件概率，但改变 CFG 步数，不能直接比较转换前后的按步尾界。
- `{...}` 为保守的不变量注释；不把无限状态空间截断。Rdwalk 的 x 下界和 t 上界、2DWalk 的坐标上界、M1DWalk 的 x 下界均保持无界。
- 3DWalk 使用较简单的单侧界注释，原来的和断言完全保留。额外盒上界曾使 SymPy 精确 LP 检查长时间停留在单纯形迭代中，相关历史日志保存在 `runs/`。
- 生成器只负责语法转换和区间传播，所有不变量仍交给生产分析器检查。通过前端不意味着合成到证书。

## 复现

在 `contractive_function` 目录运行（已安装本项目且包含 MOSEK 的环境）：

```bash
export PATH=/home/sunzhouyue/.conda/envs/contractive-frontend-test-20260814/bin:$PATH
python reprsm_benchmark/generate.py
python reprsm_benchmark/preflight.py
python reprsm_benchmark/run_suite.py --profile baseline --jobs 2
# 针对一个家族加大搜索范围
python reprsm_benchmark/run_suite.py --profile retry --jobs 2 --only Race
```

`generate.py` 从结构化描述重新生成 `.pp` 和带 SHA-256 的 `inventory.json`。`preflight.py` 独立执行解析、CFG 构造和精确不变量检查。`summarize.py` 按当前源文件哈希汇总结果。`run_suite.py` 直接调用已有 `run_analysis(..., 'assertion_violation', ...)`；成功候选再经 `verify_assertion` 从源程序独立重放。输出保存在独立的 `runs/<label>/`，标签不能覆盖已有目录。

后端保持 **CVXPY + MOSEK + 有理数重建/精确证书复核**。为逐例诊断设置显式有限搜索预算：

| 配置 | η 次数 | c | 每点最多编码尝试 | 总搜索预算 | 每实例进程预算 |
|---|---|---|---|---|---|
| baseline | 1–2 | 9999/10000 | 1 | 25 s | 60 s |
| retry | 1–3 | 999/1000、99999/100000 | 2 | 75 s | 120 s |
| diagnostic | 1 | 9999/10000 | 1 | 25 s | 60 s |

预算是实验配置，不是项目默认参数，也不是完备搜索。外层进程预算覆盖前端、精确复核等阶段，因为内部时间预算不能中断所有 Python/SymPy 操作。各次运行的配置、源程序副本、搜索历史、求解日志、证书和独立复核结果均保留；按用户要求排除的推测实例不在交付目录中。`diagnostic` 配置仅运行一次模板并打开求解日志。

实测结果及失败原因见 [RESULTS.md](RESULTS.md)。这些是当前多项式一阶矩收缩分支的结果，并非重新实现论文的 RepRSM / ExpLinSyn 算法。
