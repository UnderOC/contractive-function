# Contractive Function 分析工具

本目录实现 `framework.md` 阶段 1、阶段 2、阶段 3A 和阶段 3B。阶段 1 的
`.pp -> pCFG` 接口和产物格式保持兼容；新增链路为：

```text
.pp 源文件 -> Lark lexer/parser -> 带 SourceSpan 的自定义 AST
            -> 符号绑定、语义检查和常量规范化
            -> continuation-passing grouped pCFG
            -> CFG 静态验证及 JSON / text / DOT 产物
            -> exact polynomial / moment / pre-expectation
            -> TailBoundGoal 或 AssertionViolationGoal
            -> goal-specific obligation / scalar moment artifacts
```

当前版本为 `contractive-tool==0.2.0`。它生成后端无关的阶段 2/3 模型，不生成或
调用 MATLAB 求解器，也不会把 `generated/` 中的旧文件当作输入。

## 阶段 2/3 实现日志（2026-09-01）

- 阶段 2：新增稳定的 `PolynomialService`/`Polynomial` 适配层。源码十进制数转为
  精确有理数，update 使用 simultaneous substitution；`ExpectationEngine` 保存
  destination、替换后/期望前、随机矩消元后和 branch 加权后的逐步 trace。
- 阶段 2：有限离散、Bernoulli、Uniform 和 Normal 提供 exact raw moments；
  `IndependentRandomModel` 对独立变量拆乘 raw moments，相关模型必须显式提供
  `JointMomentProvider`。
- 阶段 3A：`TailBoundGoal` 支持 `at_horizon`、固定 horizon、事件区域、
  bad-set normalization、局部 contraction 和 `rho^n C(initial)`。Kelly power 支持
  固定正 `lambda`，自动识别样例的 grouped iid multiplicative gains，并生成精确
  scalar moment model。`k=1` polynomial eta 路径生成 positivity、contraction 与
  normalization obligations，并在写出前检查所有结论对 decision variables 仿射。
- 阶段 3B：`AssertionViolationGoal` 使用 `V(l_f)=1`、`V(l_t)=0`，生成 failure、
  normal、nonnegativity、pre-fixed-point 和 `Theta(initial)` objective。支持 direct
  polynomial Theta，以及固定正 `q`、`k=1` 的 factorized `Theta=q*eta`；会拒绝
  `k>1` 或含 decision symbol 的 `q`。

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

`assert E` 在 `not E` 时进入失败终端 `l_f`；`refute E` 在 `E` 时进入 `l_f`，这与两个随附样例“分析谓词事件”的写法一致。自然结束进入 `l_t`，`l_t` 和存在时的 `l_f` 均有吸收 self-loop。严格不等式在 pCFG 中原样保存；这里只生成 CFG，尚不执行带 margin 的 SOS lowering。

## 已实际使用的测试环境

本任务创建且只使用了全新环境 `contractive-frontend-test-20260814`，没有复用或删除已有环境。实际解释器为 Python `3.11.15`。实际创建和安装命令（从本目录执行）是：

```bash
conda create -n contractive-frontend-test-20260814 python=3.11 pip -y
conda run -n contractive-frontend-test-20260814 python -m pip install -e '.[test]'
```

直接 Python 依赖及实际版本：

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

### 阶段 3 分析命令

Kelly 三轮固定 horizon tail certificate（`lambda=1/2`）：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive analyze kelly_simple.pp \
  --out-dir generated/kelly_stage23 \
  --analysis-id kelly_tail_3 \
  --goal tail_bound --certificate kelly \
  --event 'wealth <= 0.6' --horizon 3 \
  --base wealth --lambda 1/2 --threshold 0.6 \
  --initial wealth=1 --initial round=0
```

Uniform 样例的 eventual assertion violation direct-Theta obligations：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive analyze uniform_multiplicative.pp \
  --out-dir generated/uniform_stage23 \
  --analysis-id uniform_assertion \
  --goal assertion_violation --certificate direct-theta \
  --degree 2 --initial x=1 --initial r=0
```

将第二条命令的 certificate 改成 `factorized --factor-q 2 --k 1` 可生成固定参数
contractive factorization。Polynomial tail 可使用 `--goal tail_bound --certificate
polynomial-eta --event ... --horizon ... --rho ... --degree ...`。初始 valuation 必须
恰好覆盖 pCFG 的全部 program variables；Kelly 未指定 `--initial-location` 时，单个
while header 自动作为三轮乘法过程的初始位置。

Python API 的稳定入口分层如下：

```python
from contractive_tool.algebra import PolynomialService
from contractive_tool.expectation import ExpectationEngine
from contractive_tool.probability import UniformDistribution, IndependentRandomModel
from contractive_tool.analysis import TailBoundGoal, AssertionViolationGoal
```

`ExpectationEngine.trace_branch(...)` 返回完整 `ExpectationTrace`；goal API 接受类型化
spec、pCFG 和 `PolynomialTemplateFactory` 的实例，返回 `PolynomialObligationModel` 或
`ScalarMomentModel`。

## 输出

每个 `--out-dir` 包含：

- `source.normalized.pp`：规范化并可重新解析的源程序；
- `ast.json`：不泄漏 Lark parse tree 的 Source AST；
- `cfg.json`：稳定的 grouped pCFG IR；
- `cfg.txt`：便于人工核查的 locations、guards、概率、updates 和 samples；
- `cfg.dot`：可用 Graphviz 查看；
- `validation.json`：结构验证结果及未消解的概率范围义务；
- `manifest.json`：输入/产物 SHA-256、工具/Python 版本、随机语义、统计和近似说明。

CFG JSON 中概率选择的多个 branches 保留在同一个 `transition_group`；确定性分支是两个互补 guard group。未写入 update mapping 的程序变量保持不变。

`analyze` 使用隔离产物树：共享的阶段 1 结果在 `shared/`，goal 在
`analyses/<analysis-id>/goal.json`，certificate 结果在
`analyses/<analysis-id>/certificates/<certificate>/`。Polynomial 路径写出
`template.json`、`obligations.json`、`obligations.txt`、`polynomial_model.json` 和
`result.json`；Kelly 路径写出 `scalar_model.json`。顶层 `manifest.json` 记录 exact
arithmetic、随机独立性假设、backend route、所有产物 hash 以及 `matlab_invoked=false`。

## 当前限制

- Tail 仅支持 `at_horizon`；`by_horizon` 会明确报错，因为尚未实现 absorbing-bad
  派生 CFG。Assertion 仅支持 `eventual`。
- Polynomial 结果是通过 affine capability check 的后端无关 Obligation IR，状态为
  `not_solved`；Putinar/SOSTOOLS lowering 属于阶段 4，本版本不声称这些模型已证明。
- Kelly 的 `proved` 仅用于由精确符号算术验证的 fixed-lambda scalar moment model；
  自动识别器当前要求唯一的 grouped probability choice，其每个 destination 紧接
  `base := base * positive_constant`。
- 第一版 polynomial/factorized synthesis 只开放 `k=1` 和固定 `rho/q`；未知参数乘积、
  `k>1` 未知 eta、BMI/nonlinear 模式会被拒绝。
- Guard/invariant/event 在本阶段保留为可追溯 predicate domain；析取拆分和 Putinar
  basic-set lowering留给阶段 4。

## 测试

```bash
conda run -n contractive-frontend-test-20260814 pytest -q
```

自动化测试还覆盖 exact moments、joint moments、simultaneous substitution、逐步
pre-expectation、tail/assertion obligation tags、affine capability、非凸拒绝，以及
两个真实 `.pp` 的 `analyze` CLI。实际测试记录见 `TEST_RESULTS.md`。
