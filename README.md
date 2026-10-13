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
            -> 次数与 c 网格搜索 -> 可选 positivity 编码
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

`assert E` 在 `not E` 时进入失败终端 `l_f`；`refute E` 在 `E` 时进入 `l_f`，这与两个随附样例“分析谓词事件”的写法一致。自然结束进入 `l_t`，`l_t` 和存在时的 `l_f` 均有吸收 self-loop。严格不等式在 pCFG 中原样保存；证明域采用覆盖闭包，不通过正 margin 缩域。源语言能解析的构造不一定已获统一证书后端支持，具体限制见下文。

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

只需程序和目标；事件从 assert/refute 获得，初值从源码确定性初始化获得：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive solve kelly_unbounded.pp --goal tailbound

conda run -n contractive-frontend-test-20260814 \
  contractive solve kelly_unbounded.pp --goal assertion_violation
```

第二条仅生成约束并返回 `not_solved: assertion_backend_not_implemented`。第一条默认从
D=2 搜索到 D=6；每个次数尝试 c∈{1/2,9/10,99/100}，只在没有已验证结果时继续升阶。
首个成功次数内比较 c，再比较 A。`--continue-after-success` 可以继续升阶。
`analyze`/`build-model` 只生成模型，不调用 MOSEK。输出目录可用 `--out-dir` 指定，
缺省为 `generated/<stem>_<goal>_<timestamp>/`，必须是新的或空的目录。

Tail 结论是 `Pr[T<∞, T>n, failure] <= A*c**n`，对所有非负整数 n 统一成立。
T 从程序入口按 pCFG 转移计数，包含初始化；不把无限运行质量重新归一化。
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
- `analyses/<goal>/degrees/<D>/c-<id>/polynomial_problem.json`：模板、目标和全部原始义务；
- 各参数点 `attempts/<id>/` 下的 encoding_plan、conic_model、solver.json、solver.log；
- 候选的 verification.json；只有严格证明后才生成 certificate.json；
- `search_history.json`、顶层 summary.json 和包含版本/配置/SHA-256 的 manifest.json。

## 当前限制

- Tail 当前只支持 late_bad_exit；不把未知终止程序的 `Pr[T>n]` 当作指数衰减事件。
- 所有状态变量须在控制流之前由源码确定性初始化。Invariant 闭包须通过精确初态与
  归纳保持验证；当前检查器使用有理 Farkas 恒等式，证不出即报告 unsupported。
- 源码随机赋值/声明 fresh sampling 的支持域证据、assume 阻塞语义、循环宏步时钟
  尚未接入统一后端；前端及精确随机矩模块保留，不代表这些程序已可生成证书。
- Assertion violation 只生成约束，不求解。非整数族请求明确报未实现；当前不枚举 k。
- c 是有限有理网格；SOS/Schmüdgen/Handelman 是有限编码尝试，不保证完备。
  模板默认 D=2..6，编码 order 上限 4，每参数点最多 2 次，总时间软预算 300 秒，
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
