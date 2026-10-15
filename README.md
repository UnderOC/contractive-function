# Contractive Function 分析工具

本目录按 `framework.md` 实现直接多项式统一指数尾界合成。前端 `.pp -> pCFG`
接口和产物格式保持兼容；当前链路为：

```text
.pp 源文件 -> Lark lexer/parser -> 带 SourceSpan 的自定义 AST
            -> 符号绑定、语义检查和常量规范化
            -> continuation-passing grouped pCFG
            -> CFG 静态验证及 JSON / text / DOT 产物
            -> exact polynomial / moment / pre-expectation
            -> 源码初态 / 全时域归纳域 / 直接多项式义务
            -> 次数递增与 c 有界二分搜索 -> 可选 positivity 编码
            -> CVXPY / MOSEK -> 精确验证 -> 统一 A*c**n
```

当前版本为 `contractive-tool==0.4.0`，全部使用 Python。Assertion violation 暂时
只生成义务；非整数 k 保留扩展位置。求解不读取 `generated/` 中的历史产物。

## 阶段 2/3 实现日志（2026-09-01）

- 阶段 2：新增稳定的 `PolynomialService`/`Polynomial` 适配层。源码十进制数转为
  精确有理数，update 使用 simultaneous substitution；`ExpectationEngine` 保存
  destination、替换后/期望前、随机矩消元后和 branch 加权后的逐步 trace。
- 阶段 2：有限离散、Bernoulli、Uniform 和 Normal 提供 exact raw moments；
  `IndependentRandomModel` 对独立变量拆乘 raw moments，相关模型必须显式提供
  `JointMomentProvider`。
- 阶段 3B：Assertion 使用正常终端 0、失败终端 1，生成非负性和前不动点义务。
  当前接口已迁移为直接多项式 Theta，后端求解暂不实现。

旧 fixed-horizon、Kelly scalar moment 和固定幂模板的错误实现记录已移除。

## 支持的源语言

- `skip`、赋值、顺序组合；语句分号可写，也可在 `else`、`fi`、`od` 或文件结尾前省略。
- 确定性 `if E then ... else ... fi` 和概率 `if prob(p) then ... else ... fi`。
- `while E [invariant I] do ... od`。
- `assert E`、`refute E` 和 `assume E`。
- Hoare 风格 `{E}` 注释；它附着到紧随其后的 CFG location，作为该位置的 invariant。
- 算术 `+`、`-`、`*`、一元正负号，比较和 `not/and/or`（也接受常见 Unicode 逻辑/比较符号）。
- `r := Unif(a,b)` / `Uniform(a,b)`、`Normal(mu,sigma)`、`Bernoulli(p)` 随机赋值。
- 可选的 `random r ~ Distribution(...);` 声明。声明型随机变量在每条使用它的 transition 上 fresh sampling；所有 fresh samples 默认相互独立。

`prob(...)` 只能直接作为 `if` 条件。常数概率必须在 `[0,1]`；状态相关概率会在 `validation.json` 中留下范围证明义务。赋值 update 在单条 transition 内是 simultaneous 的，源程序的顺序赋值由不同 location 表示。

`assert E` 在 `not E` 时进入失败终端 `l_f`；`refute E` 在 `E` 时进入 `l_f`，这与两个随附样例“分析谓词事件”的写法一致。自然结束进入 `l_t`，`l_t` 和存在时的 `l_f` 均有吸收 self-loop。严格不等式在 pCFG 中原样保存；一般实数证明域采用覆盖闭包，已验证的布尔宏步域则精确判断原始严格守卫，不通过任意正 margin 缩域。源语言能解析的构造不一定已获统一证书后端支持，具体限制见下文。

## 已实际使用的测试环境

本任务创建且只使用了全新环境 `contractive-frontend-test-20260814`，没有复用或删除已有环境。实际解释器为 Python `3.11.15`。实际创建和安装命令（从本目录执行）是：

```bash
conda create -n contractive-frontend-test-20260814 python=3.11 pip -y
conda run -n contractive-frontend-test-20260814 python -m pip install -e '.[test]'
```

初次前端环境创建时的直接依赖及版本（当前后端版本见末尾日志）：

- `contractive-tool==0.2.0`（本目录 editable install）
- `lark==1.2.2`
- `sympy==1.14.0`
- `pytest==8.3.5`

测试环境中同时安装了 `mpmath==1.3.0`、`iniconfig==2.3.0`、`pluggy==1.6.0`
和 conda 提供的 `packaging==26.3`，以及 `pip==26.2.1`、`setuptools==84.0.0`、
`wheel==0.48.0`。可复现的直接依赖见 `requirements-test.txt`；也可以在本目录用
环境文件重新创建另一个环境（若要避免同名冲突，先修改其中的 `name`）：

```bash
conda env create -f environment.yml
```

## 命令行入口

只生成经过语义检查的 AST：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive parse kelly_simple.pp --out generated/kelly-ast.json
```

运行从源文件到已验证 pCFG 的完整链路：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive cfg kelly_simple.pp --out-dir generated/kelly_simple

conda run -n contractive-frontend-test-20260814 \
  contractive cfg uniform_multiplicative.pp \
  --out-dir generated/uniform_multiplicative
```

也可使用 `python -m contractive_tool` 代替 `contractive`。命令成功时向 stdout 输出一行 JSON 摘要；词法、语法、语义或 CFG 验证失败时向 stderr 输出带文件、行、列的诊断并以状态码 `2` 退出。

### 统一指数尾界与 assertion 建模

只需程序和目标；事件从 assert/refute 获得，初始状态或初始分布从源码直线初始化前缀获得：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive solve kelly_unbounded.pp --goal tailbound

conda run -n contractive-frontend-test-20260814 \
  contractive solve kelly_unbounded.pp --goal assertion_violation
```

第二条仅生成约束并返回 `not_solved: assertion_backend_not_implemented`。第一条默认从
D=1 搜索到 D=6；每个次数从区间 (0,1) 开始二分 c，默认最多 10 个参数点，
用 `--max-c-steps` 配置。只在没有已验证结果时继续升阶；全局参数点和时间预算仍生效。
首个成功次数内先选最小的已验证 c，再比较 A。`--continue-after-success` 可以继续升阶。
显式 `--c-values 1/2 9/10 99/100` 可复现旧网格，默认不使用该网格。
`analyze`/`build-model` 只生成模型，不调用 MOSEK。输出目录可用 `--out-dir` 指定，
缺省为 `generated/<stem>_<goal>_<timestamp>/`，必须是新的或空的目录。

Tail 默认 `--tail-rule auto`：依次尝试布尔有限域和符号实数域的一轮编译，成功时合成
`Pr[K>n] <= A*c**n`。K 按完整循环体轮数计数，未结束 eta>=1；eta 在整个入口
invariant 域上非负，退出后生存过程归零，不要求多项式 eta 在完成区域为零。
否则在摘要记录原因，并使用保留的 `late_bad_exit` 规则：
`Pr[T<∞, T>n, failure] <= A*c**n`，T 从入口按 pCFG 转移计数、包含初始化。
两种结论均对所有非负整数 n 成立，不把无限运行质量重新归一化。
可显式指定 `--tail-rule round_survival`，此时域/宏步不支持就返回 unsupported。
若没有通过精确验证的证书，输出 `no_certificate_found`，不伪造公式。

`contractive evaluate <已证明产物目录> --n 100` 只代入现有公式，不重新求解。
`contractive strategies list --json` 查看可选 positivity 模块；例如仅启用 Putinar
时可用 `--enabled-strategies putinar`，其他策略缺失不会丢弃义务。

Python API：

```python
from contractive_tool.algebra import PolynomialService
from contractive_tool.expectation import ExpectationEngine
from contractive_tool.probability import UniformDistribution, IndependentRandomModel
from contractive_tool.analysis_pipeline import SearchOptions, run_analysis

result = run_analysis("kelly_unbounded.pp", "tailbound")
```

`ExpectationEngine.trace_branch(...)` 继续返回完整 `ExpectationTrace`；整数 k 合并为
最终多项式次数，不再接受旧 event/horizon/initial、fixed-power 或 Kelly 专用参数。

## 输出

`cfg` 命令的每个 `--out-dir` 包含：

- `source.normalized.pp`：规范化并可重新解析的源程序；
- `ast.json`：不泄漏 Lark parse tree 的 Source AST；
- `cfg.json`：稳定的 grouped pCFG IR；
- `cfg.txt`：便于人工核查的 locations、guards、概率、updates 和 samples；
- `cfg.dot`：可用 Graphviz 查看；
- `validation.json`：结构验证结果及未消解的概率范围义务；
- `manifest.json`：输入/产物 SHA-256、工具/Python 版本、随机语义、统计和近似说明。

CFG JSON 中概率选择的多个 branches 保留在同一个 `transition_group`；确定性分支是两个互补 guard group。未写入 update mapping 的程序变量保持不变。

`solve`/`build-model` 的共享前端结果在 `shared/`，其余产物包括：

- `analyses/<goal>/goal.json`、`domain_evidence.json`；
- 轮次路径额外保存 `round_evidence.json`：布尔状态或符号 invariant 域、源转移及计时；
  符号版本的 polynomial_problem.json 包含 round_preexpectations；
- `analyses/<goal>/degrees/<D>/c-<id>/polynomial_problem.json`：模板、目标和全部原始义务；
- 各参数点 `attempts/<id>/` 下的 encoding_plan、conic_model、solver.json、solver.log；
- 候选的 verification.json；只有严格证明后才生成 certificate.json；
- `search_history.json`、顶层 summary.json 和包含版本/配置/SHA-256 的 manifest.json。

## 当前限制

- Tail 支持布尔/符号实数域的 round_survival 和原有 late_bad_exit；前者由证书推导几乎
  处处终止，后者不假定终止。不可把求解前的未知终止性当作已证明。
- 所有状态变量须在控制流之前由源码的直线赋值/采样前缀初始化。确定前缀使用精确
  有理值；随机前缀逐次 alpha-renaming，并以精确独立矩计算入口期望。Invariant 闭包
  须通过初始支持和归纳保持验证；当前检查器证不出即报告 unsupported。
- `Uniform` 使用精确闭区间支持，`Bernoulli` 使用精确有限支持，`Normal` 使用全实数
  支持；循环内 fresh sample 的归纳性在源域与完整支持域的乘积上证明，不作离散化。
  `assume` 阻塞语义仍未接入。符号宏步支持实数多项式、概率/确定分支和精确矩采样；
  当确定守卫依赖新样本时需截断矩积分，当前明确拒绝。嵌套循环、轮内提前退出
  暂不支持；最多 4096 个结构展开节点、256 个符号组合域（或布尔候选状态）。
- Assertion violation 只生成约束，不求解。非整数族请求明确报未实现；当前不枚举 k。
- c 默认使用有界有理二分；只有 proved 更新上端，当前编码均报告 infeasible 才更新
  下端，其他不确定结果停止本次数的 c 搜索且不移动端点。保留已有证书；搜索区间
  不表示数学最优值的严格包围。SOS/Schmüdgen/Handelman 是有限编码尝试，不保证完备。
  模板默认 D=1..6，编码 order 上限 4，每参数点最多 2 次，总时间软预算 300 秒，
  单次 MOSEK optimizer 上限 30 秒。可用 `solve --help` 查看可选预算。
- 数值 optimal 仍须有理恒等式、非负系数及精确 PSD 验证；未验证的不参与选择。
  `no_certificate_found` 仅表示本次搜索未找到，不证明不存在，也不证明程序不收缩。
- 命令退出码 0 表示完成（包括无证书和仅建模）；3 表示后端环境/语义不支持；2 为输入错误。

## 测试

```bash
conda run -n contractive-frontend-test-20260814 pytest -q
```

自动化测试保留 parser/pCFG、exact moments、joint moments、simultaneous substitution
和逐步 pre-expectation 回归，并验证次数递增、前缀计时、可选策略降级、真实 MOSEK、
精确 PSD、未知结果处理和只求值不求解。最新运行日志见下节；`TEST_RESULTS.md` 保留
前端历史测试记录，不作为当前后端的验收结论。

## 2026-10-14：统一指数尾界后端运行记录（0.4.0）

本节为布尔宏步修复前的历史运行记录，采用 pCFG 时钟和固定网格；现版复现时使用
`--tail-rule late_bad_exit --c-values 1/2 9/10 99/100`（原命令若已指定网格则沿用）。
默认 auto 和二分的新结果见文末。

沿用 `contractive-frontend-test-20260814`，实际解释器为
`/home/sunzhouyue/.conda/envs/contractive-frontend-test-20260814/bin/python`。
当前环境为 Python 3.11.15、CVXPY 1.9.3、MOSEK 11.2.6、NumPy 2.4.6、SciPy 1.17.1、
SymPy 1.14.0、Lark 1.2.2、pytest 8.3.5。安装入口为：

```bash
conda run -n contractive-frontend-test-20260814 python -m pip install -e '.[solver,test]'
```

本次将 editable 包更新为 0.4.0；已有 solver 依赖沿用。MOSEK 许可证探针
`min x, x>=1` 实际返回 `optimal, 1.0`，`pip check` 无依赖冲突。见
[环境与许可证验证记录](generated/uniform_backend_environment_20261014.json)，产物不包含许可证内容。

实际命令如下（从本目录、上述 conda 环境执行；归档目录已存在时须换新目录）：

```bash
python -m contractive_tool solve kelly_unbounded.pp --goal tailbound \
  --out-dir generated/kelly_unbounded_uniform_tail_20261014

python -m contractive_tool solve tests/fixtures/geometric_exit.pp --goal tailbound \
  --out-dir generated/geometric_uniform_tail_20261014

python -m contractive_tool solve tests/fixtures/halving.pp --goal tailbound \
  --initial-degree 0 --max-degree 2 --c-values 9/10 99/100 \
  --out-dir generated/halving_uniform_tail_20261014

python -m contractive_tool solve kelly_unbounded.pp --goal assertion_violation \
  --out-dir generated/kelly_assertion_model_20261014

python -m contractive_tool evaluate generated/geometric_uniform_tail_20261014 --n 50
pytest -q
```

| 输入/目标 | 实际结果 |
| --- | --- |
| Kelly / tailbound，默认搜索 | D=2..6、15 个 D/c 点、30 次真实求解；`no_certificate_found`，停止原因 `max_degree`，约 191.15 秒 |
| 几何退出概率程序 / tailbound，默认搜索 | D=2 找到精确证书，选择 c=9/10、A=9891655945000/3302641019601，约 2.99507451349 |
| 折半循环 / tailbound，测试从 D=0 开始 | 常数模板不可行，D=1 成功；比较当前次数的两种 c 后选 c=9/10、A=107000/22599 |
| Kelly / assertion_violation | `not_solved`，原因 `assertion_backend_not_implemented`；仅生成多项式义务，未调用后端 |
| 回归测试 | **64 passed in 10.81s**，包括真实 MOSEK LP/SDP，无跳过 |

Kelly 此次的 30 次尝试中，7 次数值状态为 infeasible，23 次为 numerical_issue
（MOSEK UNKNOWN 等，完整诊断保存在各次 solver.json/log）。没有已验证候选，故没有
A 或指数公式，也不能据此宣称所有多项式次数均无解。此程序按普通输入走相同流程，
没有文件名/变量名识别、非多项式特殊矩计算或有限 horizon 域。

几何退出样例的已证明统一公式为：

```text
Pr[T<∞, T>n, failure]
  <= (9891655945000/3302641019601) * (9/10)**n
   = (9891655945000/3302641019601) * exp(-(-log(9/10))*n), n>=0.
```

其 n=50 展示值约为 0.01543594077；这只是对已证明公式的求值，没有再次调用求解器。
精确参数、各位置多项式和有理 Gram/PSD 验证结果保存在证书目录。测试还用该程序
`T=3J+3, J~Geom(1/2)` 的精确尾概率核对公式，并验证初始化前缀计时。

运行日志与可复查产物：

- Kelly：[命令输出](generated/kelly_unbounded_uniform_tail_20261014.run.log)、[摘要](generated/kelly_unbounded_uniform_tail_20261014/summary.json)、[完整搜索记录](generated/kelly_unbounded_uniform_tail_20261014/analyses/tailbound/search_history.json)。
- 几何退出：[命令输出](generated/geometric_uniform_tail_20261014.run.log)、[精确证书](generated/geometric_uniform_tail_20261014/analyses/tailbound/degrees/2/c-002/attempts/001/certificate.json)、[验证证据](generated/geometric_uniform_tail_20261014/analyses/tailbound/degrees/2/c-002/attempts/001/verification.json)、[事后求值](generated/geometric_uniform_tail_20261014.evaluate.log)。
- 次数递增：[命令输出](generated/halving_uniform_tail_20261014.run.log)、[搜索记录](generated/halving_uniform_tail_20261014/analyses/tailbound/search_history.json)。
- Assertion：[命令输出](generated/kelly_assertion_model_20261014.run.log)、[约束](generated/kelly_assertion_model_20261014/analyses/assertion_violation/degrees/2/c-001/polynomial_problem.json)。
- [测试完整输出](generated/uniform_backend_tests_20261014.log)。

旧的 finite_tail、k_policy、reachability、tail_pipeline、Kelly scalar goal 及时间层
倒序修正代码已经删除。非整数 k 的接口单独保留，当前明确拒绝，不影响多项式路径。

## 2026-10-14：一轮计时、布尔循环域与生存证书边界修复

以下是历史实现记录；其中 completed eta=0 的要求已由 2026-10-15 的生存过程边界修复替代。

新增通用 `analysis/rounds.py`，从 CFG 验证完整一轮的路径、概率、顺序更新和域保持。
布尔性由初态及全部宏步更新证明；严格 guard 不再把已完成状态放入继续循环域。
循环入口使用未知多项式 eta：未完成 eta>=1，完成 eta=0，约束为
`Pre_round(eta)<=c*eta`，目标 A=eta(initial)。在完整有限布尔域上生成精确 LP，继续
使用原有 CVXPY/MOSEK 和有理数验证。这里枚举的是归纳状态域，不是有限 horizon。
未引入样例专用公式、文件名判断或变量名判断。

c 搜索保持 `1/2,9/10,99/100`；以下仅测试 D=1，没有引入 c=3/4 参数点。
继续使用本 README 的 conda 环境和已有 MOSEK 许可证。实际命令：

```bash
python -m contractive_tool solve tailbound_benchmark_pack/pp/01_coupon2.pp \
  --goal tailbound --initial-degree 1 --max-degree 1 \
  --out-dir tailbound_benchmark_pack/runs/round_d1_verified_20261014/01_coupon2
python -m contractive_tool solve tailbound_benchmark_pack/pp/02_coupon4.pp \
  --goal tailbound --initial-degree 1 --max-degree 1 \
  --out-dir tailbound_benchmark_pack/runs/round_d1_verified_20261014/02_coupon4
pytest -q
```

| 输入 | 已验证多项式 | 选择的 c | 全部轮次的尾界 | 求解耗时 |
| --- | --- | --- | --- | --- |
| 01_coupon2 | `2-c0-c1` | 1/2 | `Pr[K>n] <= min(1,2*(1/2)**n)` | 1.29 秒 |
| 02_coupon4 | `4-c0-c1-c2-c3` | 9/10 | `Pr[K>n] <= min(1,4*(9/10)**n)` | 3.39 秒 |

K 为完整抽取轮数；02 的 pCFG 时间另存为 `T=4+4*K+2`。02 在 c=1/2 时不可行，
c=9/10 和 99/100 均找到相同 eta，按现有选择规则选 9/10。独立有理数检查还验证了
该多项式确有 `Pre_round(eta)=3/4*eta`；这说明它有更紧的已知收缩率，但本次没有
改变搜索或将所选参数替换成 3/4。01 的对应精确比值为 1/2。

全量回归 **79 passed in 16.59s**，无跳过，包含真实 MOSEK、原有 pCFG 规则、
布尔域保持、严格边界、顺序更新、非终止反例、轮内提前退出拒绝、重命名通用性及
assertion 仍只建模等检查。较早的一次全量命令只指定了 conda 解释器而未设置 PATH，
导致 3 个 CLI 子进程找不到 `contractive`；在完整 conda PATH 下重跑后全部通过。

- [运行索引及命令输出](tailbound_benchmark_pack/runs/round_d1_verified_20261014/run_index.json)。
- [02 精确证书](tailbound_benchmark_pack/runs/round_d1_verified_20261014/02_coupon4/analyses/tailbound/degrees/1/c-002/attempts/001/certificate.json)。
- [02 独立检查](tailbound_benchmark_pack/runs/round_d1_verified_20261014/02_coupon4.independent_check.json)。
- [完整测试日志](generated/round_backend_regression_20261014.log)。

同步更新了 framework 的轮次规则及实现范围，修改前备份为
`framework.md.bak.20261014_round_fix`。一般连续域宏步仍未实现；auto 的回退原因与
最终采用的事件/时钟会明确写入产物，assertion violation 后端仍不启用。


## 2026-10-14：c 有界二分搜索与 D=1 复测

默认 c 选择已由固定网格改成 (0,1) 内的精确有理二分。每个 D 从 c=1/2 开始，
最多搜索 `--max-c-steps 10` 个参数点；每次只把固定 c 交给 CVXPY/MOSEK，仍保持
系数合成模型的凸性。每参数点最多 2 次编码尝试，整个任务最多 32 个参数点，
原有时间预算继续生效。显式 `--c-values` 仅用于复现旧网格结果。

proved 更新上端；已尝试编码全部报告 infeasible 才更新下端。数值未知、验证失败等
不确定状态不更新端点，停止当前次数的 c 搜索并保留已有证书。每次升阶重置区间。
完整反馈及停止原因保存在 summary.json 的 `contraction_searches`；初始端点 1 不被
当作已验证候选，下端也不是原始多项式不存在的数学证明。

在本 README 的 conda 环境中运行（复跑请换新的输出目录）：

```bash
python -m contractive_tool solve tailbound_benchmark_pack/pp/01_coupon2.pp \
  --goal tailbound --initial-degree 1 --max-degree 1 --max-c-steps 10 \
  --out-dir tailbound_benchmark_pack/runs/bisection_d1_20261014/01_coupon2
python -m contractive_tool solve tailbound_benchmark_pack/pp/02_coupon4.pp \
  --goal tailbound --initial-degree 1 --max-degree 1 --max-c-steps 10 \
  --out-dir tailbound_benchmark_pack/runs/bisection_d1_20261014/02_coupon4
pytest -q
```

| 输入 | 已验证 eta | 选中 c | 统一尾界（K 为抽取轮数） | 搜索点/实际求解次数 | 耗时 |
| --- | --- | --- | --- | --- | --- |
| 01_coupon2 | 2-c0-c1 | 1/2 | min(1,2*(1/2)^n) | 10 / 19 | 1.70 秒 |
| 02_coupon4 | 4-c0-c1-c2-c3 | 3/4 | min(1,4*(3/4)^n) | 10 / 19 | 4.68 秒 |

01 搜索顺序从 1/2、1/4、3/8 开始，最终区间为 [511/1024,1/2]；02 从 1/2、3/4、5/8
开始，最终为 [767/1024,3/4]。两者均完成 10 个参数点，以 `max_c_steps` 结束本次数
的 c 搜索，再以 `first_successful_degree` 停止整体搜索。02 的指数式已收紧为
`Pr[K>n] <= min(1,4*exp(-log(4/3)*n))`；3/4 是算法实际访问并验证的参数点，未硬编码。

独立有理数检查覆盖全部布尔入口状态：未完成 eta>=1，完成 eta=0，且这两个返回的
证书均精确满足 `Pre_round(eta)=c*eta`。运行产物 SHA-256 逐一核对通过。
完整回归 **90 passed in 18.47s**，包含搜索步数上限、每次升阶重置、未知不缩区间、
未知后保留证书、真实 MOSEK 与两个实例的精确尾概率核对。

- [运行索引和命令](tailbound_benchmark_pack/runs/bisection_d1_20261014/run_index.json)
- [01 独立验证](tailbound_benchmark_pack/runs/bisection_d1_20261014/01_coupon2.independent_check.json)
- [02 独立验证及逐步搜索区间](tailbound_benchmark_pack/runs/bisection_d1_20261014/02_coupon4.independent_check.json)
- [02 返回证书](tailbound_benchmark_pack/runs/bisection_d1_20261014/02_coupon4/analyses/tailbound/degrees/1/c-002/attempts/001/certificate.json)
- [完整回归日志](generated/bisection_regression_20261014.log)

framework 已同步搜索算法和预算，修改前另存 `framework.md.bak.20261014_bisection`。


## 2026-10-14：默认纳入 D=1，并测试其余 benchmark

framework 和运行默认值均已从 D=2 改为 **D=1..6**；一次模板无证书时继续升阶。
CLI、Python API 和批量驱动一致。批量脚本改为冻结当前 SearchOptions，避免继续
使用旧 D=2/固定网格。每个 D 仍最多 10 次 c 二分，全局最多 32 个参数点。
修改前框架保存在 `framework.md.bak.20261014_degree1`。

在本 README 的 conda 环境中运行：

```bash
python tailbound_benchmark_pack/run_tailbound_suite.py \
  --output-root tailbound_benchmark_pack/runs/default_d1_bisection_20261014 --jobs 3
pytest -q
```

12 个可运行实例均完成，无未处理异常，墙钟 195.32 秒：

- 01、02 在默认 D=1 下分别验证 `2*(1/2)^n`、`4*(3/4)^n` 的轮次尾界。
- 03、04、05 的 d=1/5/10/20、06、07、08、12 共 10 个其他实例全部实际尝试了 D=1，
  并继续搜索到次数上限或参数点预算；最终均为 no_certificate_found，不表示无解。
- 这些其他实例超出当前布尔宏步编译器的范围，auto 回退到 pCFG late_bad_exit，
  回退原因已逐例记录；没有将它们描述为已完成一般连续域宏步求解。
- 09、10、11 非确定性实例继续跳过并注明，未替换为随机分支。

全量回归 **90 passed in 19.26s**。批次共 280 个参数点、558 次尝试；全部进程返回 0，
stderr 为空，源码/产物哈希以及实际 D=1 solver 记录已核对。
详见 [完整测试报告](tailbound_benchmark_pack/TEST_RESULTS.md)、
[本批机器汇总](tailbound_benchmark_pack/runs/default_d1_bisection_20261014/results.json)、
[运行索引](tailbound_benchmark_pack/runs/default_d1_bisection_20261014/run_index.json) 和
[回归日志](generated/degree1_default_regression_20261014.log)。


## 2026-10-15：RCD_example.pp 新样例测试

新增 [RCD_example.pp](RCD_example.pp)，保留用户给定的初态 `x=-1/2,y=1`、
每轮独立 Bernoulli(1/2) 坐标选择和 `x=-y/2` / `y=-x/2` 更新。
由于当前语法没有除法，将原守卫 `(x*x+x*y+y*y)/2 > 3/8192` 精确等价改写为
`4096*(x*x+x*y+y*y)>3`；0.5 由前端转为精确有理数 1/2。
添加可由初态和两分支归纳验证的 box invariant：`-1/2<=x<=0, 0<=y<=1`，
不限制原程序的实际运行。末尾 `refute true` 标记所有有限退出供当前 tailbound 分析。

使用本 README 的 conda 环境和真实 MOSEK，运行：

```bash
python -m contractive_tool solve RCD_example.pp --goal tailbound \
  --out-dir generated/RCD_example_default_20261015
```

语法、CFG、初始化和归纳域检查通过。默认 D=1..6、每次数最多 10 个 c 二分点、
总参数点上限 32、每点最多 2 次编码尝试、总时间软预算 300 秒。实际耗时 80.36 秒，
进程返回 0，stderr 为空；没有改变后端求解逻辑或为此样例加入专用证书。

| 项目 | 实际结果 |
| --- | --- |
| 最终状态 | no_certificate_found |
| 实际次数 | D=1,2,3,4,5,6 |
| 参数点 / 后端尝试 | 13 / 26 |
| 尝试状态 | infeasible 15；numerical_issue 9；solved_unverified 2 |
| 总体停止原因 | max_degree |
| 已验证证书/尾界 | 无 |

各次数的 c 搜索因反馈不确定而停止，没有将数值失败作为不可行缩区间。
D=1 实际访问 1/2,3/4,7/8,15/16,31/32,63/64；D=2 访问 1/2,3/4,7/8；
D=3..6 各访问 1/2。数值候选未通过精确验证，故不能标记 proved。

由于初始 x=-1/2 不满足当前布尔宏步域要求，auto 使用 `late_bad_exit` 路径，
尝试的目标是 `Pr[T<infinity,T>n,failure]<=A*c^n`，T 按入口 pCFG 转移计数。
本例有限退出均进入 failure，且 T=3*K+4，K 是坐标更新轮数；本次没有合成一般实数域
的一轮生存证书。因此结果不证明原程序不存在多项式证书或指数尾界。

源码及产物 manifest 哈希核对通过。记录：

- [命令输出](generated/RCD_example_default_20261015.run.log)
- [结果摘要](generated/RCD_example_default_20261015/summary.json)
- [逐次搜索记录](generated/RCD_example_default_20261015/analyses/tailbound/search_history.json)
- [事件与计时](generated/RCD_example_default_20261015/analyses/tailbound/goal.json)
- 每参数点的 attempts 目录保留 solver.log、solver.json 和数值候选的 verification.json。


## 2026-10-15：RCD 改用位置等式标注和一般实数证明域

RCD_example.pp 已移除 box 区间与 while invariant 写法，在循环头、概率选择、
两个赋值和退出位置使用 `{(x+0.5*y)*(y+0.5*x)=0}` 标注。
变量为一般实数，证明域仅受该等式及各转移守卫限制；初态仍为 x=-1/2,y=1。

执行 `python -m contractive_tool analyze RCD_example.pp --goal tailbound
--out-dir generated/RCD_real_invariant_model_20261015`：解析、初态与归纳保持验证、
证明义务及 CVXPY 建模通过，返回 not_solved/model_only，没有调用 MOSEK。
循环入口域没有 box 不等式，11 条义务均保留该等式。
[检查产物](generated/RCD_real_invariant_model_20261015/summary.json)。

此处更改的是源标注和证明域，并未实现一般实数域宏步，也未修改证书边界；
当前 auto 建模仍回退至 late_bad_exit。前一节运行结果对应修改前的 box 版本，
不得作为现版输入的求解结果。


## 2026-10-15：符号宏步、生存边界修复及 RCD 成功求解

修改前仓库已提交并推送为 `4267406`，保留先前代码、样例及测试产物。
本次新增 `analysis/symbolic_rounds.py`，在实数符号域组合一轮的更新、分支概率及
精确随机矩；使用已有位置不变量作为经过验证的证明域。没有 RCD 文件名、变量名、
f 的公式或预设证书识别。auto 先尝试布尔编译，再尝试符号编译，均不支持才回退。

边界已改为：V 在整个入口 invariant 域非负、活动域 V>=1；退出后生存过程置零，
不再要求多项式本身在完成区域为零。布尔版本精确去除完成分支的期望贡献；符号
版本使用 raw round contraction 作为 killed contraction 的充分条件。二分 c 和
默认 D=1..6 不变，断言违例仍只建模。框架修改前备份为
`framework.md.bak.20261015_symbolic_rounds`。

使用 README 的 conda 环境及真实 MOSEK 执行：

```bash
python -m contractive_tool solve RCD_example.pp --goal tailbound \
  --out-dir generated/RCD_symbolic_round_20261015
pytest -q
```

| 项目 | 实际结果 |
| --- | --- |
| 路径 | round_survival，symbolic kernel，没有回退 |
| 次数 | D=1 未找到，D=2 成功；停止于首个成功次数 |
| 搜索 | 20 个参数点、38 次后端求解；36 infeasible、2 proved |
| 耗时 | 3.12 秒 |
| 选择证书 | V(x,y)=-2048*x*y，c=5/8，A=1024 |
| 统一尾界 | Pr[K>n] <= min(1,1024*(5/8)^n)，全部整数 n>=0 |
| 指数式 | min(1,1024*exp(-log(8/5)*n)) |
| 计时 | K 为坐标更新轮数；原入口 pCFG 时间 T=2+3*K+2 |
| 验证 | 精确有理系数恒等式、非负乘子与 PSD 均通过 |

令 `h=(x+y/2)*(y+x/2)`、`f=(x*x+x*y+y*y)/2`，独立核对得到：

```text
V - (8192/3)*f       = -(8192/3)*h
(5/8)*V - Pre(V)     = -1024*h
Pre(V)              = 512*x*x + 512*y*y
V(-1/2,1)           = 1024
V(-1/64,1/32)       = 1  # 此时 f=3/8192，已经退出
```

因此在已验证不变量 h=0 上，返回证书与笔记中 k=1 的归一化势函数完全等价。
无需强制找出同一个全空间多项式表达式。n=60 的已证明上界约为
`5.795634610449096e-10`；n 只用于事后求值，未逐 horizon 求解。
另一个已验证候选为 c=3/4、A=683，保留在 Pareto 集合中；按当前优先最小 c 的
策略选择 c=5/8。本次没有进行非整数 k 优化，也没有强制继续升至 D=4。

全量回归 **101 passed in 17.71s**，无跳过。覆盖 01/02、RCD 重命名、顺序更新、概率与确定分支组合、fresh sample
独立性、随机初值、非零完成态、非终止反例、拒绝样本相关守卫/嵌套循环/提前退出，
以及原有 late_bad_exit 和 assertion 建模接口。首次回归发现 4 个测试仍断言旧路径
或旧零边界，已分别更新为新语义或显式选择旧规则，没有放宽精确证明要求。

本次没有重跑其余整个 benchmark 包；以往其他例子的回退记录属于旧版本结果。
符号版本仍不支持轮内提前退出、嵌套循环、assume，以及需要截断矩的样本相关守卫。
这些情况会明确报告不支持，不使用无条件矩替代条件积分。

- [求解输出](generated/RCD_symbolic_round_20261015.run.log)
- [结果摘要及全部二分反馈](generated/RCD_symbolic_round_20261015/summary.json)
- [返回证书](generated/RCD_symbolic_round_20261015/analyses/tailbound/degrees/2/c-003/attempts/001/certificate.json)
- [精确验证](generated/RCD_symbolic_round_20261015/analyses/tailbound/degrees/2/c-003/attempts/001/verification.json)
- [独立恒等式/PSD/哈希及精确尾概率检查](generated/RCD_symbolic_round_20261015.independent_check.json)
- [完整回归日志](generated/symbolic_round_regression_20261015.log)
