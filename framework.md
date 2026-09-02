# Contractive Function 工具框架设计

本文档给出一个以 Python 实现前端和部分后端的建议框架。目标流程是：

```text
概率程序源文件
  -> Lexer / Parser
  -> Source AST
  -> 语义检查与规范化
  -> pCFG
  -> AnalysisGoal 分流
       |-> TailBoundGoal
       |    -> contractive/moment 约束与 tail normalization
       |    -> SOS、scalar moment 或外层参数搜索后端
       |
       `-> AssertionViolationGoal
            -> failure boundary 与 pre-fixed-point 约束
            -> SOS 或其他可验证后端
  -> goal-specific 求解模型与结果
```

MATLAB 求解器不属于第一阶段实现范围。Python 端默认只生成模型文件，不执行 `sossolve`、SDPT3 或 SeDuMi。

## 1. 设计原则

### 1.1 分离语法、程序语义和证明方法

Parser 只负责把文本转换为 AST；CFG builder 只负责程序执行语义；tail bound 和 assertion violation 属于不同的分析目标；Contractive function 是分析目标可复用的证书机制；SOS 编码属于后端 lowering。各层不能直接互相拼接字符串。

例如，新增 piecewise-polynomial 模板时，不应修改 parser 或 CFG builder；新增 CVXPY 后端时，也不应修改 Contractive 约束生成逻辑。

“分析目标”和“证书/模板”是两个正交维度：`tail_bound` 与 `assertion_violation` 决定要证明的概率事件及边界条件；polynomial、multiplicative power 或 direct Theta 决定用什么候选函数证明。后端再根据最终约束能力选择，不能通过模板名称反推分析目标。

### 1.2 使用稳定的中间表示

建议至少保留以下中间表示：

```text
Source AST       保留源语言结构和源码位置
Program IR       完成变量绑定、类型检查和表达式规范化
pCFG IR          表示位置、transition group、更新和概率
Template IR      表示每个位置上的候选函数及未知参数
Obligation IR    表示带来源信息的数学证明义务
Goal Problem IR  区分 tail bound 与 assertion violation 的事件、边界和目标函数
Constraint IR    表示 SOS、scalar moment 或其他后端可消费的约束模型
```

每层都应能独立导出 JSON 或文本，便于检查错误发生在哪个阶段。

### 1.3 后端能力必须显式检查

SOSTOOLS 最终解决的是凸 SOS/SDP 问题。若模板产生未知系数之间的乘积、未知指数、一般有理函数或非多项式函数，不能直接假装成普通 SOS 问题。

约束 lowering 阶段应检查：

- 关于程序变量的表达式是否为多项式；
- 多项式系数是否对 SDP decision variables 保持仿射；
- 分母是否已经在严格正性条件下消除；
- `k`、概率和分布矩是否已经固定为常数；
- strict inequality 是否已根据配置转换为带 margin 的非严格不等式。

不满足能力要求时应返回明确的 `UnsupportedConstraintError`，并指出对应 transition 和源码位置。

## 2. 需要先固定的程序语义

`project_detail.md` 中的基本语法可以作为起点，但以下信息还需要在实现前明确。

### 2.1 随机变量声明

表达式允许随机变量 `r`，但目前没有说明 `r` 的分布和作用域。建议增加显式声明，例如：

```text
random r ~ Normal(0, 1);
random u ~ Uniform(-1, 1);
```

也可以将分布放在 TOML 配置中，但不能只保留一个没有分布信息的变量名。MVP 建议假设每次经过对应 transition 都进行一次 fresh sampling，并且不同随机变量相互独立。相关假设必须写入生成产物的 manifest。

### 2.2 概率分支与普通 guard 分离

虽然表面语法都写在 `E` 中，内部 AST 应使用两种不同节点：

```text
Guard(condition)
ProbChoice(probability_expression)
```

`prob(a)` 只能作为分支选择器，不能出现在 `not(prob(a))` 或 `prob(a) and E` 中。语义检查还应生成或要求 invariant 能推出 `0 <= a <= 1`。

### 2.3 正常终止和 assertion failure

Assertion-violation 分析需要区分：

```text
l_t: normal termination，证书值为 0
l_f: assertion violation，证书值为 1
```

当前语法没有 `assert`。建议加入：

```text
assert E
```

其 CFG 语义为：`E` 成立时进入 continuation，`E` 不成立时进入 `l_f`。程序自然结束进入 `l_t`。

### 2.4 Invariant 来源

第一版不建议实现 invariant 自动推断。可以支持：

```text
while E invariant I do P
```

CFG builder 将 `I` 挂到 loop header。未来再增加 sidecar invariant 文件或外部 invariant provider。

### 2.5 严格不等式

SOS 通常处理闭半代数集合。源语言中的 `a < b` 不能无说明地直接改成 `a <= b`。建议由配置指定：

```text
strict_inequality_margin = 1e-8
```

然后将 `a < b` lowering 为 `b - a - margin >= 0`，并在 manifest 中记录该近似。

## 3. 推荐目录结构

```text
contractive_function/
├── pyproject.toml
├── README.md
├── project_detail.md
├── framework.md
├── examples/
│   ├── simple_loop.cf
│   └── simple_loop.toml
├── src/
│   └── contractive_tool/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── errors.py
│       ├── diagnostics.py
│       ├── frontend/
│       │   ├── grammar.lark
│       │   ├── ast.py
│       │   ├── parser.py
│       │   ├── source.py
│       │   ├── symbols.py
│       │   ├── semantic.py
│       │   └── normalize.py
│       ├── algebra/
│       │   ├── expressions.py
│       │   ├── polynomials.py
│       │   ├── predicates.py
│       │   ├── substitution.py
│       │   └── moments.py
│       ├── ir/
│       │   ├── distributions.py
│       │   ├── updates.py
│       │   ├── cfg.py
│       │   ├── program.py
│       │   ├── templates.py
│       │   ├── goals.py
│       │   ├── obligations.py
│       │   └── constraints.py
│       ├── cfg/
│       │   ├── builder.py
│       │   ├── validation.py
│       │   ├── text_writer.py
│       │   ├── json_writer.py
│       │   └── dot_writer.py
│       ├── analysis/
│       │   ├── context.py
│       │   ├── expectation.py
│       │   ├── pipeline.py
│       │   ├── goals/
│       │   │   ├── base.py
│       │   │   ├── registry.py
│       │   │   ├── tail_bound.py
│       │   │   └── assertion_violation.py
│       │   ├── templates/
│       │   │   ├── base.py
│       │   │   ├── registry.py
│       │   │   ├── polynomial.py
│       │   │   ├── direct_certificate.py
│       │   │   └── multiplicative_power.py
│       │   ├── rules/
│       │   │   ├── base.py
│       │   │   ├── contraction.py
│       │   │   ├── tail_normalization.py
│       │   │   ├── prefixed_point.py
│       │   │   └── failure_boundary.py
│       │   ├── certificates/
│       │   │   ├── plan.py
│       │   │   ├── runner.py
│       │   │   ├── result.py
│       │   │   └── combiners.py
│       │   └── lowering/
│       │       ├── polynomial.py
│       │       ├── positivity.py
│       │       ├── scalar_moment.py
│       │       └── convexity.py
│       ├── backends/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── numeric/
│       │   │   └── scalar.py
│       │   └── matlab/
│       │       ├── sostools.py
│       │       ├── emitter.py
│       │       ├── names.py
│       │       └── validation.py
│       └── artifacts/
│           ├── manager.py
│           └── manifest.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── golden/
│   └── fixtures/
└── generated/
    └── .gitkeep
```

`generated/` 只放运行产物。源码模块不应读取该目录中的旧文件作为隐式输入。

## 4. 前端设计

### 4.1 Parser

建议使用 Lark 描述 grammar，输出自定义 dataclass AST，不让 Lark 的 parse tree 泄漏到后续模块。

AST 节点应带 `SourceSpan`：

```python
@dataclass(frozen=True)
class SourceSpan:
    file: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int

@dataclass(frozen=True)
class Assign(Stmt):
    target: str
    value: Expr
    span: SourceSpan

@dataclass(frozen=True)
class While(Stmt):
    guard: BoolExpr
    invariant: BoolExpr | None
    body: Stmt
    span: SourceSpan
```

建议的 statement AST：

```text
Skip
Assign
Sequence
IfGuard
IfProb
While
Assert
Assume（可选）
```

算术表达式至少包含：

```text
Constant, ProgramVariable, RandomVariable
Add, Subtract, Multiply, Negate
```

模板内部需要幂运算，但源程序是否允许 `a^n` 可以单独决定。不要因为模板需要幂，就强制扩展源语言表达式。

### 4.2 语义检查

`semantic.py` 负责：

- 建立 program variable 和 random variable symbol table；
- 检查未声明变量和重复声明；
- 检查赋值左侧只能是 program variable；
- 检查概率表达式的合法位置；
- 检查 distribution 参数；
- 检查 invariant 只依赖允许的状态变量；
- 为每个诊断附带源码位置。

### 4.3 规范化

不要在 parser 中直接展开逻辑否定或 DNF。`normalize.py` 可以按后续需要执行：

```text
constant folding
消除 Subtract / Negate
比较式统一为 polynomial >= 0
布尔表达式转 NNF
按需将 guard 拆成 basic semialgebraic regions
```

DNF 可能指数膨胀，因此应设置 region 数量上限并给出诊断。

## 5. pCFG 设计

### 5.1 为什么使用 transition group

`project_detail.md` 的 Moment-Contraction 对同一个 source location 的所有概率后继求和。因此内部最好直接保存 grouped transition，而不是生成约束时重新猜测哪些 flat edges 属于同一次概率选择。

```python
@dataclass(frozen=True)
class Branch:
    destination: LocationId
    probability: Polynomial
    update: Update

@dataclass(frozen=True)
class TransitionGroup:
    id: TransitionId
    source: LocationId
    guard: BoolExpr
    branches: tuple[Branch, ...]
    origin: SourceSpan

@dataclass(frozen=True)
class ProgramCFG:
    locations: Mapping[LocationId, Location]
    transitions: tuple[TransitionGroup, ...]
    initial_location: LocationId
    normal_terminal: LocationId
    failure_terminal: LocationId | None
```

确定赋值是只有一个 branch 且 probability 为 1 的 transition group；普通 `if` 产生两个 guard 不同的 transition group；概率 `if` 产生一个包含两个 branches 的 transition group。

### 5.2 Update

更新使用结构化映射：

```python
@dataclass(frozen=True)
class Update:
    assignments: Mapping[ProgramSymbol, PolynomialExpr]
    samples: tuple[RandomSymbol, ...]
```

未出现在 `assignments` 中的变量保持不变。必须明确 assignments 是 simultaneous update；源语言中的顺序赋值通过不同 location 表示。

### 5.3 CFG 构造算法

可以参考现有 OCaml 前端使用 continuation-passing 方式：

```text
build(stmt, continuation) -> entry_location
```

- `Sequence(s1, s2)`：先构造 `s2`，再把其入口作为 `s1` 的 continuation；
- `While`：先创建 loop header，body 的 continuation 指回 header；
- `IfGuard`：创建两个带互补 guard 的 transition group；
- `IfProb`：创建一个拥有两个概率 branches 的 transition group；
- `Assert`：按需创建 `l_f`，并创建通往 continuation 和 `l_f` 的两个 guarded transitions；
- 程序结束位置为 `l_t`，给 `l_t` 以及存在时的 `l_f` 添加吸收 self-loop。

Location ID 应稳定且可读，例如 `L_while_1`、`L_assign_4`。不要依赖全局可变计数器跨多次分析继续累加。

### 5.4 CFG 验证

`cfg/validation.py` 至少检查：

- initial 和 `l_t` 存在；若启用 assertion-violation goal，则 `l_f` 存在；
- 每个非终止位置有 outgoing transition；
- destination 均存在；
- 同一 probabilistic group 的概率和为 1，或生成对应证明义务；
- invariant map 覆盖需要分析的位置；
- 更新只修改已声明 program variables；
- random symbols 均有 moment provider。

### 5.5 pCFG 之后的 AnalysisGoal 分流

pCFG 是两个分析方向最后一个完全共享的语义层。CFG builder 完成后，pipeline 必须先读取显式 `AnalysisGoal`，再实例化模板和生成证明义务：

```python
class AnalysisGoal(Protocol):
    kind: str

    def validate(
        self,
        program: ProgramIR,
        options: GoalOptions,
    ) -> tuple[Diagnostic, ...]: ...

    def build_problem(
        self,
        program: ProgramIR,
        options: GoalOptions,
    ) -> "GoalProblem": ...

GoalProblem = TailBoundProblem | AssertionViolationProblem
```

整体分流为：

```text
ProgramIR + pCFG + invariant + random model
  -> GoalDispatcher
       |-> TailBoundProblem
       |    -> contractive template
       |    -> contraction + bad-set normalization obligations
       |    -> tail-bound objective
       |
       `-> AssertionViolationProblem
            -> direct/factorized certificate template
            -> failure boundary + pre-fixed-point obligations
            -> initial violation-bound objective
  -> capability lowering
  -> backend router
```

#### 5.5.1 TailBoundGoal

Tail bound 分析回答一个明确带时间和事件语义的问题，例如：

```text
at_horizon:  Pr[X_n in B]
by_horizon:  Pr[exists t <= n. X_t in B]
```

建议的 goal spec：

```python
@dataclass(frozen=True)
class TailBoundGoalSpec:
    event: BoolExpr
    horizon: int
    event_mode: Literal["at_horizon", "by_horizon"]
    locations: frozenset[LocationId] | None
    normalization: TailNormalization
    optimize: Literal["bound", "contraction_rate", "feasibility"]
```

必须显式给出 horizon 和 event mode。`Pr[X_n in B]` 与“在第 n 步之前曾进入 B”不是同一个事件，不能共用同一组边界义务。

对 `at_horizon`，可令非负证书：

```text
C_l(x) = (eta_l(x) / H)^k
```

并生成两类核心义务：

```text
local contraction:
    I(src) and guard
      => sum_j p_j E[C_dst_j(update_j(x,r))] <= rho * C_src(x)

tail normalization:
    I(l) and B_l
      => C_l(x) >= 1
```

在齐次、固定 `rho` 的有限 horizon 情形下得到：

```text
Pr[X_n in B] <= rho^n * C_init(x_init)
```

也可以使用 time-indexed `Phi_i`，此时每个时间层生成 `E[Phi_{i+1}] <= Phi_i`，最终目标为 `Phi_0(init)`。

`by_horizon` 建议先执行 goal-specific CFG augmentation：将满足 `B` 的状态转入一个新的 absorbing bad label，再生成 bounded reachability obligations。该 augmentation 产生派生 CFG，不能修改共享的原始 pCFG。

Tail-bound problem 至少包含：

```python
@dataclass(frozen=True)
class TailBoundProblem:
    analysis_id: str
    cfg: ProgramCFG
    initial: Config
    event: SemialgebraicEvent
    horizon: int
    event_mode: str
    normalization: TailNormalization
    optimize: str

@dataclass(frozen=True)
class TailBoundObligationSet:
    contraction_obligations: tuple[ProofObligation, ...]
    normalization_obligations: tuple[ProofObligation, ...]
    objective: Objective
```

`TailBoundProblem` 只保存事件语义；`TailBoundObligationSet` 在 template 实例化后由 tail rule 生成。

可能的 lowering/backend 路径：

```text
固定 Kelly gain + fixed lambda
    -> scalar moment constraint / exact or interval numeric backend

polynomial eta + universal polynomial inequalities
    -> SOS/Putinar `.m`

外层搜索 k、lambda 或 rho；每个参数点内部是凸 SOS
    -> parameter-search coordinator + SOS backend

未知参数乘积或一般有理函数
    -> nonlinear/BMI backend，或明确 unsupported
```

#### 5.5.2 AssertionViolationGoal

Assertion violation 分析回答 reachability 问题：

```text
Pr[exists t. location_t = l_f]
```

它依赖 CFG 中由 `assert` 产生的 failure location `l_f`，通常不要求有限 horizon。建议的 goal spec：

```python
@dataclass(frozen=True)
class AssertionViolationGoalSpec:
    failure_locations: frozenset[LocationId]
    normal_terminal: LocationId
    reachability_mode: Literal["eventual", "bounded"]
    horizon: int | None
    optimize: Literal["initial_bound", "feasibility"]
```

定义非负 certificate `Theta`，生成：

```text
failure boundary:
    I(l_f) => Theta(l_f, x) >= 1

normal boundary:
    Theta(l_t, x) = 0

nonnegativity:
    I(l) => Theta(l, x) >= 0

pre-fixed point:
    I(src) and guard
      => sum_j p_j E[Theta(dst_j, update_j(x,r))] <= Theta(src, x)
```

目标函数为：

```text
minimize Theta(l_init, x_init)
```

从而证明 eventual assertion violation probability 的上界。`Theta` 可以直接使用 polynomial template，也可以使用 contractive factorization：

```text
Theta_l(x) = exp(b_l) * eta_l(x)^k
```

factorization 只改变 certificate 的参数化和 lowering，不改变 assertion-violation goal 的 failure boundary 与 pre-fixed-point 语义。

Assertion-violation problem 至少包含：

```python
@dataclass(frozen=True)
class AssertionViolationProblem:
    analysis_id: str
    cfg: ProgramCFG
    initial: Config
    failure_locations: frozenset[LocationId]
    normal_terminal: LocationId
    reachability_mode: str
    horizon: int | None

@dataclass(frozen=True)
class AssertionViolationObligationSet:
    boundary_obligations: tuple[ProofObligation, ...]
    prefixed_obligations: tuple[ProofObligation, ...]
    nonnegativity_obligations: tuple[ProofObligation, ...]
    objective: Objective
```

`AssertionViolationProblem` 只保存 reachability 语义；`AssertionViolationObligationSet` 在 template 实例化后由 assertion rule 生成。

常见 backend 路径为：

```text
direct polynomial Theta
    -> SOS/Putinar `.m`

fixed k、fixed b 的 polynomial factorization，且系数保持仿射
    -> SOS/Putinar `.m`

同时合成 b、eta 或非整数 k
    -> outer search、alternating/nonlinear backend，或 unsupported
```

#### 5.5.3 两个方向的边界

| 项目 | Tail bound | Assertion violation |
|---|---|---|
| 概率事件 | `X_n in B` 或 `exists t<=n: X_t in B` | `exists t: location_t = l_f` |
| 必需输入 | tail event、horizon、event mode、normalization | failure location、normal terminal、reachability mode |
| 主要约束 | contraction、moment、tail normalization | failure boundary、nonnegativity、pre-fixed point |
| 典型目标 | 最小化 `rho^n C_init` | 最小化 `Theta_init` |
| 是否要求 `l_f` | 否 | 是 |
| 常见非 SOS 路径 | scalar moments、参数外层搜索 | 参数外层搜索、nonlinear/BMI |
| SOS 用途 | 证明全状态 contraction 和 bad-set normalization | 证明全状态 pre-fixed point 与边界条件 |

两个 goal 可以复用同一个 contractive template、expectation engine 和 SOS backend，但不能共享 goal-specific obligations，也不能直接比较它们的 bound。只有事件、horizon 和边界语义完全相同的结果才能进入同一个 selection policy。

## 6. 代数与期望计算

### 6.1 多项式封装

可以使用 SymPy 完成表达式展开、替换和 `Poly` 转换，但建议通过项目自己的薄封装访问，避免所有模块直接依赖 SymPy 类型：

```python
class PolynomialService(Protocol):
    def normalize(self, expr: AlgebraExpr) -> Polynomial: ...
    def substitute(self, poly: Polynomial, update: Update) -> Polynomial: ...
    def variables(self, poly: Polynomial) -> frozenset[Symbol]: ...
    def coefficients(self, poly: Polynomial) -> Mapping[Monomial, CoefficientExpr]: ...
```

这样未来可以更换为稀疏多项式实现，而不修改 CFG 或模板接口。

### 6.2 Distribution 与 moment 接口

```python
class Distribution(Protocol):
    def validate(self) -> None: ...
    def raw_moment(self, order: int) -> ExactOrFloat: ...

class JointMomentProvider(Protocol):
    def moment(self, powers: Mapping[RandomSymbol, int]) -> ExactOrFloat: ...
```

第一版可支持有限离散分布、Uniform 和 Normal。独立分布的 joint moment 等于各 raw moment 的乘积；相关随机变量必须使用单独的 joint provider，不能默认拆乘积。

### 6.3 Pre-expectation

```python
class ExpectationEngine:
    def branch_expectation(
        self,
        function: Polynomial,
        branch: Branch,
        random_model: RandomModel,
    ) -> Polynomial:
        ...
```

处理顺序：

1. 将 destination function 中的程序变量同时替换为 update RHS；
2. 展开为程序变量和随机变量上的多项式；
3. 用 raw/joint moments 消去随机变量；
4. 乘 branch probability；
5. 对同一 transition group 的 branches 求和。

每一步都应能保留一份调试表示，尤其要能查看“替换后、取期望前”和“取期望后”的表达式。

## 7. 模板扩展接口

AnalysisGoal、模板与 CertificateRule 应是三个独立接口。Goal 负责定义概率事件、horizon 和边界语义；模板负责声明未知函数；规则根据 `GoalProblem + TemplateInstance` 生成函数必须满足的条件。

```python
class FunctionTemplateFactory(Protocol):
    kind: str

    def instantiate(
        self,
        cfg: ProgramCFG,
        symbols: ProgramSymbols,
        options: TemplateOptions,
    ) -> "TemplateInstance": ...

class TemplateInstance(Protocol):
    def expression_at(self, location: LocationId) -> SymbolicFunction: ...
    def decision_variables(self) -> tuple[DecisionVariable, ...]: ...
    def intrinsic_obligations(self) -> tuple[ProofObligation, ...]: ...
    def metadata(self) -> Mapping[str, object]: ...
```

通过 registry 根据配置选择模板：

```python
template_registry.register("polynomial", PolynomialTemplateFactory())
template_registry.register("direct_certificate", DirectCertificateFactory())
template_registry.register("multiplicative_power", MultiplicativePowerFactory())
```

### 7.1 Polynomial contractive template

对每个普通位置生成：

```text
eta_l(x) = sum_{|alpha| <= d} c[l, alpha] x^alpha
```

可配置项包括：

```text
degree
monomial basis: total_degree / explicit_support
per-location degree
coefficient sharing policy
strict positivity margin
是否为特殊位置生成模板
```

其 intrinsic obligation 至少包括 invariant 上的严格正性近似：

```text
I(l) => eta_l(x) - epsilon_eta >= 0
```

### 7.2 后续模板

未来模板可以包括：

```text
PiecewisePolynomialTemplate
LocationSharedPolynomialTemplate
FixedBasisTemplate
DirectThetaCertificateTemplate
ExternallyProvidedTemplate
```

神经网络或包含 `log/exp` 的模板也可以接入 Template IR，但 SOSTOOLS backend 应通过 capability check 拒绝无法多项式化的实例，或交给其他 backend。

## 8. 证明规则与 Obligation IR

```python
class CertificateRule(Protocol):
    name: str
    supported_goals: frozenset[str]

    def generate(
        self,
        problem: GoalProblem,
        template: TemplateInstance,
        context: AnalysisContext,
    ) -> "GoalObligationSet": ...

GoalObligationSet = TailBoundObligationSet | AssertionViolationObligationSet
```

建议的通用 obligation：

```python
@dataclass(frozen=True)
class ProofObligation:
    id: str
    domain: SemialgebraicRegion
    relation: SymbolicRelation
    origin: ConstraintOrigin
    tags: frozenset[str]
```

`CertificateRule` 必须声明 `supported_goals`，不允许把只实现 assertion boundary 的规则用于 tail bound。`ProofObligation` 先保留后端无关的符号关系。Polynomial lowering 可以将其转为 `PolynomialRelation`；Kelly power 等特殊规则也可以先把比例化简为 scalar moment constraint。`ConstraintOrigin` 记录 analysis job、goal kind、source location、transition ID、模板类型和源码 span。MATLAB 生成器应把这些信息写成注释，便于从失败的 SOS 约束追溯到源程序。

初始 rule compatibility table：

| Rule | `tail_bound` | `assertion_violation` |
|---|---:|---:|
| `contractive_tail` | yes | no |
| `time_indexed_tail` | yes | no |
| `prefixed_point` | no | yes |
| `factorized_prefixed_point` | no | yes |

如果未来发现两个 goal 共享某个局部公式，应提取内部 helper，而不是把完整 rule 标为同时兼容；goal-specific boundary 和 objective 仍由各自 adapter 生成。

### 8.1 Assertion violation: Pre-fixed-point rule

该规则只接受 `AssertionViolationProblem`。定义统一的 certificate value：

```text
V(l_t, x) = 0
V(l_f, x) = 1
V(l, x)   = template.expression_at(l), otherwise
```

对每个 transition group 生成：

```text
I(src) and guard
  => V(src, x) - sum_j p_j E[V(dst_j, update_j(x,r))] >= 0
```

该规则直接对应 assertion-violation probability 的 pre-fixed-point 条件，建议作为第一条端到端跑通的规则。

### 8.2 共享的 Contractive/Moment rule

局部 contractive 内核对一个由 goal adapter 提供的非负 certificate `C` 生成：

```text
I(src) and guard
  => sum_j p_j E[C(dst_j, update_j(x,r))] <= rho * C(src, x)
```

它本身不能决定这是 tail bound 还是 assertion violation；两个 goal adapter 必须补充不同的事件语义和边界义务。

#### 8.2.1 Tail-bound adapter

`TailBoundProblem` 通常令：

```text
C_l(x) = (eta_l(x) / H)^k
```

并在局部 contraction 之外增加：

```text
I(l) and tail_event(l, x) => C_l(x) >= 1
```

随后由 horizon adapter 构造 `rho^n C_init`，或生成 time-indexed `Phi_i` obligations。这里没有 `Theta(l_f)=1` 的要求；只有 `by_horizon` augmentation 创建的 absorbing bad label 才使用 reachability 风格边界。

#### 8.2.2 Assertion-violation factorization adapter

`AssertionViolationProblem` 可以将普通位置上的 certificate 参数化为：

```text
Theta_l(x) = q_l * eta_l(x)^k,  q_l = exp(b_l)
```

将分母在 `eta_src > 0` 下消除后，普通 transition 的 MC 条件可写为：

```text
sum_{j: dst_j != l_t}
    p_j q_dst_j E[eta_dst_j(update_j)^k]
<= q_src eta_src(x)^k
```

failure destination 必须按 `Theta(l_f)=1` 特殊处理，不能当作普通未知 `eta_lf`；normal terminal 的贡献为 0。

无论使用 direct Theta 还是 factorized Theta，assertion adapter 都必须生成 failure boundary、normal boundary、nonnegativity 和 pre-fixed-point obligations。

#### 8.2.3 Convexity boundary

第一版建议只支持以下凸安全配置之一：

```text
A. k = 1，q_l 固定，eta_l 为未知 polynomial
B. 直接合成 V_l(x) = q_l eta_l(x)，不分别恢复 q_l 和 eta_l
C. eta_l 固定，只优化其余保持仿射的参数
```

以下组合会产生未知 decision variables 的乘积，一般不是标准凸 SOS/SDP：

```text
k > 1 且 eta_l 的系数未知
q_l 和 eta_l 的系数同时未知
k 本身作为未知连续变量
```

这些模式以后可以交给 alternating optimization、BMI/nonlinear solver 或外层参数搜索，但必须与标准 SOSTOOLS SDP 模式分开。

### 8.3 多证书计划、调度与组合

当前工具应区分两种“多证书”语义：

```text
independent candidates
    对同一个 AnalysisJob 分别运行多套模板、规则和后端，得到多个独立证明结果。

composite certificate
    按一条有数学闭包依据的组合规则，把多个证书组成一个新的证书。
```

第一阶段只实现 `independent candidates`。整个 `AnalysisPlan` 中的 tail-bound job 与 assertion-violation job 共享只读的 AST、Program IR、pCFG、invariant 和 random model；每个 job 拥有独立的 `GoalProblem`。同一 job 内的多个候选又分别拥有独立的模板参数、obligations、backend model 和输出目录。

建议增加类型化分析计划：

```python
@dataclass(frozen=True)
class CertificateSpec:
    id: str
    template_kind: str
    rule_name: str
    template_options: Mapping[str, object]
    rule_options: Mapping[str, object]
    backend_policy: str  # explicit backend name or "auto"

@dataclass(frozen=True)
class CertificatePortfolio:
    mode: Literal["independent", "composite"]
    certificates: tuple[CertificateSpec, ...]
    selection_policy: str

@dataclass(frozen=True)
class AnalysisJobSpec:
    id: str
    goal: TailBoundGoalSpec | AssertionViolationGoalSpec
    portfolio: CertificatePortfolio

@dataclass(frozen=True)
class AnalysisPlan:
    jobs: tuple[AnalysisJobSpec, ...]

@dataclass(frozen=True)
class CertificateRunResult:
    analysis_id: str
    goal_kind: Literal["tail_bound", "assertion_violation"]
    certificate_id: str
    status: Literal[
        "proved", "infeasible", "unsupported", "generation_failed", "not_solved"
    ]
    bound: float | None
    artifacts: tuple[GeneratedArtifact, ...]
    diagnostics: tuple[Diagnostic, ...]
```

`AnalysisRunner` 先对每个 job 调用 goal registry，再由 `CertificateRunner` 对该 job 的每个 certificate spec 执行：

```text
goal registry lookup
  -> GoalProblem
  -> template registry lookup
  -> TemplateInstance
  -> certificate rule lookup
  -> goal-specific GoalObligationSet
  -> rule-specific simplification
  -> capability analysis
  -> lowering route
  -> backend model / artifacts
  -> CertificateRunResult
```

命名空间至少包含 `analysis_id/certificate_id`，避免两个 goal 或两个证书都生成 `c_l0_0`、`seq_1` 或 `model.m` 后互相覆盖。

#### 8.3.1 Backend 自动路由

后端不应只根据模板名称选择，而应根据化简后的 obligation 能力选择：

```text
PolynomialTemplate + affine polynomial coefficients
    -> PolynomialImplication
    -> SOSTOOLS/Putinar backend

MultiplicativePowerTemplate + fixed lambda
    -> 先尝试 eta(update)/eta 的比例化简
    -> 若只剩离散 gain 的常数矩，交给 scalar numeric backend
    -> 若化简后成为仿射多项式约束，可交给 SOSTOOLS
    -> 否则返回 unsupported，并保留具体原因

DirectThetaCertificateTemplate
    -> polynomial capability check
    -> SOSTOOLS backend
```

因此需要显式 lowering 结果，而不是所有 obligation 都强制转成 `SOSModel`：

```python
LoweredModel = SOSModel | ScalarMomentModel | UnsupportedModel

class BackendRouter:
    def route(
        self,
        model: LoweredModel,
        requested_backend: str,
    ) -> Backend: ...
```

对 Kelly 的 tail-bound job，可以同时配置：

```text
kelly_power
    eta(W) = W^(-lambda)
    化简为 0.6 * 1.2^(-lambda) + 0.4 * 0.8^(-lambda) <= c
    使用 scalar backend 或 lambda 外层搜索

poly_tail
    直接合成 polynomial C(W, round)
    生成 Putinar SOS `.m`
```

两者使用同一个 `TailBoundProblem`，但不共享 decision variables，也不要求使用同一个 backend。另一个 assertion-violation job 可以在同一原始 pCFG 上配置 `DirectThetaCertificateTemplate -> SOSTOOLS`，但其 obligations 和结果不加入 tail job 的 selection。

#### 8.3.2 结果选择

若同一个 `AnalysisJob` 中的多个候选都对同一程序语义、初始状态、概率事件和 horizon 独立证明了上界 `B_i`，则：

```text
B_final = min { B_i | result_i.status == "proved" }
```

仍是合法上界。选择时只能使用已经完成证明验证的结果；`not_solved`、`unsupported` 或仅通过采样观察得到的数值不能参与 sound bound 的最小值。

在当前 model-only 阶段，SOSTOOLS 候选生成 `.m` 后状态应为 `not_solved`，`summary.selection` 保持 `pending`。以后只有在导入并校验 MATLAB solver result 后才能改为 `proved`。Scalar moment backend 也只有使用精确算术或带证明保证的区间计算时才能返回 `proved`；普通浮点计算只能用于筛选参数候选。

不要把多个候选的 obligations 简单合并成一个 SOS model。那表示要求同一组分析同时满足全部候选约束，通常比任一候选都强，也失去了“哪个证书能证明就使用哪个”的语义。

如果不同证书使用了不同的 invariant、strictness margin、浮点近似或随机独立性假设，summary 必须分别记录，只有假设兼容时才能比较其 bound。

Tail-bound job 的 `Pr[X_n in B]` 与 assertion-violation job 的 `Pr[exists t. location_t = l_f]` 是不同事件，即使数值都在 `[0,1]` 中也不能放入同一个 `min`。Selection policy 的作用域固定为单个 `analysis_id`；跨 goal 的顶层 summary 只并列报告结果。

#### 8.3.3 组合证书

后续若实现 composite mode，应只允许注册过并带有闭包说明的 combiner：

```python
class CertificateCombiner(Protocol):
    name: str

    def validate_inputs(
        self,
        certificates: tuple[CertificateInstance, ...],
    ) -> tuple[Diagnostic, ...]: ...

    def combine(
        self,
        certificates: tuple[CertificateInstance, ...],
    ) -> CertificateInstance: ...
```

例如，对具有相同 pre-fixed-point operator 和相同边界语义的非负证书，可以专门证明某种 convex combination 仍合法。`min`、`max`、乘积或分段拼接不能作为通用默认操作；piecewise certificate 还必须为区域覆盖、区域交界和跨区域 transition 生成额外 obligations。

MVP 中 `composite` 应返回明确的 `unsupported`，直到对应 combiner 和测试被实现，不能退化为字符串层面的公式拼接。

## 9. Backend Constraint IR

证明规则不应生成 MATLAB 字符串，而应先生成 goal-specific obligations，再 lowering 为后端无关模型：

```python
@dataclass(frozen=True)
class BasicSemialgebraicSet:
    generators: tuple[Polynomial, ...]  # 每项解释为 g_i(x) >= 0

@dataclass(frozen=True)
class PolynomialImplication:
    domain: BasicSemialgebraicSet
    conclusion: Polynomial             # 目标为 h(x) >= 0
    origin: ConstraintOrigin

@dataclass(frozen=True)
class SOSModel:
    analysis_id: str
    goal_kind: Literal["tail_bound", "assertion_violation"]
    state_symbols: tuple[Symbol, ...]
    decision_variables: tuple[DecisionVariable, ...]
    implications: tuple[PolynomialImplication, ...]
    objective: Objective | None

@dataclass(frozen=True)
class ScalarMomentConstraint:
    left: SymbolicScalarExpr
    relation: Literal["<=", ">=", "="]
    right: SymbolicScalarExpr
    origin: ConstraintOrigin

@dataclass(frozen=True)
class ScalarMomentModel:
    analysis_id: str
    goal_kind: Literal["tail_bound", "assertion_violation"]
    parameters: tuple[ScalarParameter, ...]
    constraints: tuple[ScalarMomentConstraint, ...]
    objective: Objective | None

LoweredModel = SOSModel | ScalarMomentModel | UnsupportedModel
```

Tail-bound lowering 必须保留 `contraction`、`tail_normalization` 和 horizon-bound objective 的 tags；assertion-violation lowering 必须保留 `failure_boundary`、`normal_boundary`、`nonnegative` 和 `prefixed_point` tags。静态验证器应检查对应 goal 的必需类别没有在 lowering 中丢失。

即使两个 goal 最终都得到 `SOSModel`，objective 仍不同：tail bound 通常最小化 `rho^n C_init` 或 time-indexed `Phi_0(init)`；assertion violation 最小化 `Theta(init)`。Emitter 只消费已经确定的 objective，不自行推断概率语义。

若一个 guard 是多个 basic regions 的析取，应为每个 region 单独生成 implication，而不是把析取硬塞进一个 Putinar certificate。

`lowering/convexity.py` 应检查 conclusion 和 domain generators 的系数对 decision variables 是否仿射。

## 10. MATLAB/SOSTOOLS 后端

### 10.1 Backend 接口

```python
class Backend(Protocol):
    name: str

    def capabilities(self) -> BackendCapabilities: ...
    def validate(self, model: LoweredModel) -> tuple[Diagnostic, ...]: ...
    def emit(self, model: LoweredModel, options: BackendOptions) -> GeneratedArtifact: ...
```

具体实现应进一步收窄类型：SOSTOOLS backend 只接受通过 convexity check 的 `SOSModel`；scalar numeric backend 只接受 `ScalarMomentModel`。

### 10.2 Putinar lowering

对于：

```text
g_1(x) >= 0, ..., g_m(x) >= 0 => h(x) >= 0
```

第一版只实现 Putinar 形式：

```text
h(x) - sum_i sigma_i(x) g_i(x) is SOS
sigma_i(x) is SOS
```

Schmüdgen 会为 generator 子集乘积生成 multiplier，规模增长很快，建议以后作为另一种 lowering strategy 加入。

### 10.3 `.m` emitter

emitter 负责：

```text
稳定且合法的 MATLAB identifier
syms 声明去重
sosprogram 初始化
monomial basis
sossosvar multiplier 声明
sosineq 约束
sossetobj 目标函数
来源注释和 constraint ID
```

不要让各分析模块自行拼接 MATLAB 语句。`names.py` 统一处理变量名转义、去重和稳定编号。

建议提供两个输出模式：

```text
model_only（默认）: 生成到 sossetobj 为止，不调用求解器
executable_script: 追加 my_sossolve/sossolve 和 sosgetsol
```

本项目第一阶段固定使用 `model_only`。即使配置中记录了目标 solver，也只写入 metadata，不追加 solver 调用。

### 10.4 静态验证

在没有 MATLAB 的机器上仍可检查：

- symbol 声明无重复；
- 所有使用的 symbol 均已声明；
- MATLAB identifier 合法；
- 括号和方括号平衡；
- 每个 obligation 都对应至少一条 `sosineq`；
- model-only 文件不包含 `sossolve`、`my_sossolve`、`sosgetsol`；
- 输出顺序和命名具有确定性。

## 11. 配置与 CLI

建议使用 TOML 配置：

```toml
[frontend]
strict_inequality_margin = 1e-8

[analysis]
id = "assertion_main"
goal = "assertion_violation"
reachability_mode = "eventual"
rule = "prefixed_point"
k = 1

[template]
kind = "polynomial"
degree = 2
positivity_margin = 1e-6
monomial_basis = "total_degree"

[backend]
kind = "sostools"
positivstellensatz = "putinar"
sos_multiplier_degree = 2
emit_solver_call = false

[artifacts]
emit_ast = true
emit_cfg_text = true
emit_cfg_json = true
emit_cfg_dot = true
emit_obligations = true
```

上面的配置是“单 analysis job + 单 certificate”的简写。需要在同一个 pCFG 上同时生成 tail-bound 和 assertion-violation 约束时，使用 job 列表；每个 job 内再声明自己的证书候选：

```toml
[[analysis_jobs]]
id = "kelly_tail_3"
goal = "tail_bound"
mode = "independent"
selection_policy = "smallest_proved_bound"
horizon = 3
event_mode = "at_horizon"
event = "wealth <= 0.6"
normalization = "certificate_geq_one_on_event"

[[analysis_jobs.certificates]]
id = "poly_tail"
template_kind = "polynomial"
rule = "contractive_tail"
backend = "sostools"
degree = 2
positivity_margin = 1e-6
sos_multiplier_degree = 2

[[analysis_jobs.certificates]]
id = "kelly_power_l05"
template_kind = "multiplicative_power"
rule = "contractive_tail"
backend = "auto"
base = "wealth"
lambda = 0.5

[[analysis_jobs]]
id = "assertion_eventual"
goal = "assertion_violation"
mode = "independent"
selection_policy = "smallest_proved_bound"
reachability_mode = "eventual"
failure_locations = ["l_f"]

[[analysis_jobs.certificates]]
id = "direct_theta"
template_kind = "direct_certificate"
rule = "prefixed_point"
backend = "sostools"
degree = 2
positivity_margin = 0.0
sos_multiplier_degree = 2
```

配置解析后应统一转换为 `AnalysisPlan.jobs`；pipeline 内部不保留“单/多 goal”或“单/多 certificate”两套执行逻辑。`rule` 必须与 goal compatibility table 匹配，例如 `prefixed_point` 不能绑定到 `tail_bound`。

CLI 建议按阶段暴露：

```bash
contractive parse example.cf --out generated/example/ast.json
contractive cfg example.cf --out-dir generated/example
contractive obligations example.cf --config example.toml --analysis-id kelly_tail_3 --out-dir generated/example
contractive emit-matlab example.cf --config example.toml --analysis-id kelly_tail_3 --certificate-id poly_tail --out-dir generated/example
contractive analyze example.cf --config example.toml --out-dir generated/example
```

`analyze` 默认执行配置中的全部 jobs；阶段命令必须通过 `analysis-id` 定位 goal，必要时再通过 `certificate-id` 定位候选，避免意外把 assertion obligations 写入 tail model。

第一阶段不要提供 `solve` 命令，避免“生成模型”和“执行外部求解器”的权限边界混在一起。

## 12. 运行产物

一次完整分析建议生成：

```text
generated/<run-name>/
├── source.normalized.cf
├── ast.json
├── cfg.json
├── cfg.txt
├── cfg.dot
├── templates.json
├── obligations.json
├── obligations.txt
├── model.m
└── manifest.json
```

多 goal、多证书运行使用两级隔离目录：

```text
generated/<run-name>/
├── shared/
│   ├── ast.json
│   ├── cfg.json
│   ├── cfg.txt
│   └── cfg.dot
├── analyses/
│   ├── kelly_tail_3/
│   │   ├── goal.json
│   │   ├── certificates/
│   │   │   ├── poly_tail/
│   │   │   │   ├── obligations.json
│   │   │   │   ├── model.m
│   │   │   │   └── result.json
│   │   │   └── kelly_power_l05/
│   │   │       ├── obligations.json
│   │   │       ├── scalar_model.json
│   │   │       └── result.json
│   │   └── summary.json
│   └── assertion_eventual/
│       ├── goal.json
│       ├── certificates/
│       │   └── direct_theta/
│       │       ├── obligations.json
│       │       ├── model.m
│       │       └── result.json
│       └── summary.json
├── summary.json
└── manifest.json
```

每个 analysis 目录内的 `summary.json` 记录该 goal 下每个候选的状态、bound、假设、backend route 和 selection。顶层 `summary.json` 只并列 tail-bound 与 assertion-violation 的结果，不跨 goal 选择；一个 job 或候选失败不能删除其他已生成结果。

`manifest.json` 至少记录：

```text
工具版本和 Python 版本
输入文件及 SHA-256
配置文件及 SHA-256
随机变量分布和独立性假设
analysis goal、概率事件、horizon 和 event/reachability mode
模板类型与 degree
k、q/b 和 positivity margin
使用的 proof rule
Putinar/Schmüdgen strategy
所有近似和 capability warnings
各产物 SHA-256
```

## 13. 测试策略

### 13.1 Parser 测试

- 每类 statement 和表达式的最小样例；
- precedence：乘法高于加减，逻辑非高于与，逻辑与高于或；
- 非法 `prob` 嵌套；
- 错误位置和错误消息；
- AST golden JSON。

### 13.2 CFG 测试

- sequence continuation；
- deterministic if 的互补 guard；
- probabilistic branches 保持在同一 transition group；
- while body 回到 header；
- assert false edge 到 `l_f`；
- `l_t`、`l_f` 吸收；
- location ID 在重复运行中稳定。

### 13.3 Expectation 测试

- deterministic substitution；
- simultaneous update；
- 离散、Uniform、Normal 的低阶 moments；
- 多个独立随机变量的 joint moment；
- 概率 branches 加权求和；
- 不支持的相关分布给出错误。

### 13.4 AnalysisGoal 分流测试

- 同一个 pCFG 可以构造独立的 `TailBoundProblem` 和 `AssertionViolationProblem`；
- tail-bound job 缺少 horizon、event 或 event mode 时失败；
- `at_horizon` 与 `by_horizon` 生成不同的 goal-specific obligations；
- assertion-violation job 缺少 failure location 时失败；
- tail-bound obligations 包含 contraction 和 tail normalization；
- assertion-violation obligations 包含 failure boundary 和 pre-fixed point；
- `prefixed_point` 绑定到 `tail_bound` 时被 compatibility check 拒绝；
- goal-specific CFG augmentation 不修改共享原始 pCFG；
- 两种 goal 的 bound 不进入同一个 selection policy。

### 13.5 Template 与 obligation 测试

- `n` 个变量、degree `d` 时 monomial 数量正确；
- 每个普通 location 有独立模板参数；
- `l_t=0`、`l_f=1`；
- 手工小程序的 pre-fixed-point 约束与推导一致；
- `eta > 0` obligation 覆盖所有需要的位置；
- 非凸参数组合被 capability check 拒绝。

### 13.6 MATLAB emitter 测试

- golden `.m` 文件；
- symbol 去重；
- constraint ID 和源码注释；
- model-only 模式不含 solver 调用；
- 相同输入重复生成完全相同的文件和 hash。

### 13.7 多证书调度测试

- 多个候选共享同一个不可变 pCFG；
- 各候选 decision variable 和 artifact 命名空间隔离；
- polynomial 和 scalar moment obligation 路由到不同 backend；
- 一个候选 `unsupported` 不影响其他候选生成；
- 只在 `proved` 结果中选择最小 bound；
- 不兼容假设的 bound 不进行比较；
- composite mode 在没有已注册 combiner 时明确失败；
- summary 和 manifest 可以追溯每个结果的配置及产物 hash。

## 14. 推荐实施顺序

### 阶段 0：固定语义

确定 random declaration、assert、invariant、strict inequality、fresh sampling 和初始状态的输入方式，并补充一到两个手工推导样例。

### 阶段 1：前端与可观察 pCFG

实现 grammar、AST、语义检查、continuation-based CFG builder，以及 AST/CFG 的 JSON、文本和 DOT 导出。此时不实现模板。

验收标准：包含赋值、顺序、普通分支、概率分支、while、assert 和随机 RHS 的程序都能生成稳定 pCFG。

### 阶段 2：多项式与 pre-expectation

实现 polynomial adapter、substitution、distribution moments 和 branch expectation。

验收标准：对小程序能输出每个 transition 的人工可核对 pre-expectation。

### 阶段 3A：Tail-bound 最小流程

实现 `TailBoundGoal`、`at_horizon` 事件、固定 horizon、contractive obligation、bad-set normalization 和 bound expression。先支持固定 `lambda` 的 Kelly scalar moment certificate，再支持 `k=1` polynomial `eta_l` 生成 polynomial obligations。

验收标准：Kelly 三轮样例可以生成独立的 scalar moment model；polynomial tail certificate 的 Obligation IR 中所有系数对 decision variables 仿射。

### 阶段 3B：Assertion-violation 最小流程

实现 `AssertionViolationGoal`、failure/normal boundary、nonnegativity 和 pre-fixed-point obligations。优先实现 direct polynomial `Theta`，再接入 fixed-parameter contractive factorization。

验收标准：带 `assert` 的程序可以生成 `Theta(l_f)>=1`、`Theta(l_t)=0`、transition pre-fixed-point 约束和初始 bound objective。

### 阶段 3.5：Independent 多证书 runner

实现 `AnalysisPlan.jobs`、`GoalDispatcher`、`CertificateRunner`、backend auto-routing、两级结果隔离和 job-local `smallest_proved_bound` selection。

验收标准：同一 pCFG 可以同时建立 tail-bound 与 assertion-violation jobs；tail job 可同时生成 polynomial SOSTOOLS 模型和 power-template scalar model；任一 job 或候选不支持时，其他任务仍能独立完成。

### 阶段 4：SOSTOOLS model-only emitter

只实现 Putinar，分别消费 tail-bound 和 assertion-violation lowering 后的 `SOSModel`，生成不含 solver 调用的 `.m`，同时生成 goal-aware manifest 和静态验证报告。

验收标准：Python 端从源程序到 `.m` 全流程通过；在有 MATLAB 的环境中可单独加载并继续添加求解调用。

### 阶段 5：扩展模板和求解策略

再考虑 composite certificate、piecewise polynomial、固定整数 `k>1`、外层参数搜索、alternating optimization、Schmüdgen 和其他 backend。只有实现并测试了对应闭包规则后才启用 combiner；非凸模式与标准 SDP 模式应使用不同的配置类型和结果状态。

## 15. `project_detail.md` 中已修正及仍需补充的数学说明

`project_detail.md` 中的两处凸凹性描述已修正，正确关系如下：

- 当 `0 < k <= 1` 时，`r -> r^k` 是 concave，不是 convex；此时 Jensen 给出 `E[R^k] <= E[R]^k`，文档中的不等式方向是正确的。
- 当 `k > 1` 时，`r -> r^k` 是 convex，不是 concave；仅由 `E[R] <= c` 不能得到所需的高阶矩上界。

还需要明确：

- `eta_l(x)` 的严格正性区域及统一 margin；
- `k` 是固定参数、离散搜索参数还是待优化变量；
- `b_l/q_l` 是固定、外层搜索还是同时合成；
- Hoeffding 所需的 log-ratio 上下界如何获得和验证；
- assertion bad set 是由程序中的 `assert` 产生，还是由外部 predicate 指定；
- 最终优化目标是初始 violation bound、contraction rate，还是 feasibility。

这些选择会直接决定问题能否降低为凸 SOS/SDP，因此应进入类型化配置和 manifest，而不是仅作为注释保留。
