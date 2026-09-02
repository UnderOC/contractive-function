# 阶段 1/2/3 测试结果

## 测试上下文

- 测试日期：2026-08-14（Asia/Taipei）
- 全新 conda 环境：`contractive-frontend-test-20260814`
- 环境路径：`/home/sunzhouyue/.conda/envs/contractive-frontend-test-20260814`
- Python：`3.11.15`
- 项目：`contractive-tool==0.1.0`（editable）
- 直接依赖：`lark==1.2.2`、`pytest==8.3.5`
- 实际 pytest 传递依赖：`iniconfig==2.3.0`、`pluggy==1.6.0`、`packaging==26.3`

环境由以下命令实际创建和安装；未复用或删除用户已有环境：

```bash
conda create -n contractive-frontend-test-20260814 python=3.11 pip -y
cd /ssd/ssd_backup/home/sunzhouyue/Probablistic_project/contractive_function
conda run -n contractive-frontend-test-20260814 \
  python -m pip install -e '.[test]'
```

## 最终自动化测试

最终复核在不读取 shell profile 的新 bash 中执行：

```bash
bash --noprofile --norc -c '
  cd /ssd/ssd_backup/home/sunzhouyue/Probablistic_project/contractive_function &&
  conda run -n contractive-frontend-test-20260814 pytest -q &&
  conda run -n contractive-frontend-test-20260814 \
    contractive cfg kelly_simple.pp --out-dir generated/kelly_simple &&
  conda run -n contractive-frontend-test-20260814 \
    contractive cfg uniform_multiplicative.pp \
    --out-dir generated/uniform_multiplicative
'
```

pytest 最终 stdout：

```text
..........................                                               [100%]
26 passed in 0.42s
```

26 个收集到的测试逐项结果如下，均为 `PASS`：

| # | 测试 | 结果 |
|---:|---|---|
| 1 | `test_actual_sample_runs_complete_cli_pipeline[kelly_simple.pp]` | PASS |
| 2 | `test_actual_sample_runs_complete_cli_pipeline[uniform_multiplicative.pp]` | PASS |
| 3 | `test_parse_subcommand_writes_semantically_checked_ast` | PASS |
| 4 | `test_sequence_updates_have_distinct_locations_and_continuation` | PASS |
| 5 | `test_deterministic_if_has_complementary_guard_groups` | PASS |
| 6 | `test_probability_choice_stays_in_one_transition_group` | PASS |
| 7 | `test_symbolic_probability_creates_a_range_obligation` | PASS |
| 8 | `test_while_body_returns_to_header_and_annotation_is_attached` | PASS |
| 9 | `test_assert_and_refute_edges_and_absorbing_terminals` | PASS |
| 10 | `test_distribution_assignment_records_fresh_sample_and_update` | PASS |
| 11 | `test_declared_random_is_sampled_on_each_using_transition` | PASS |
| 12 | `test_cfg_generation_is_stable_and_json_has_grouped_schema` | PASS |
| 13 | `test_arithmetic_and_boolean_precedence` | PASS |
| 14 | `test_control_statements_probability_and_optional_semicolons` | PASS |
| 15 | `test_source_spans_are_preserved` | PASS |
| 16 | `test_comments_and_unicode_operators` | PASS |
| 17 | `test_parse_error_reports_actual_location` | PASS |
| 18 | `test_symbols_are_bound_from_assignments` | PASS |
| 19 | `test_explicit_random_declaration_is_fresh_source` | PASS |
| 20 | `test_semantic_errors_are_actionable[unknown variable]` | PASS |
| 21 | `test_semantic_errors_are_actionable[illegal nested prob]` | PASS |
| 22 | `test_semantic_errors_are_actionable[probability out of range]` | PASS |
| 23 | `test_semantic_errors_are_actionable[invalid Uniform bounds]` | PASS |
| 24 | `test_semantic_errors_are_actionable[invalid Normal deviation]` | PASS |
| 25 | `test_semantic_errors_are_actionable[assignment to declared random]` | PASS |
| 26 | `test_distribution_alias_and_constants_are_normalized` | PASS |

集成测试还会检查每个输出目录中的七个产物、manifest 统计、终端 location、validation 状态，并把 `source.normalized.pp` 再次送入 parser 和 semantic checker，确认它不是不可重用的调试文本。

开发阶段第一次运行 25 项测试时结果为 `24 passed, 1 failed`；失败原因是测试错误依赖了 CPS builder 内部 transition 列表的生成顺序，而不是 CFG 错误。测试已改为通过 update 表达式定位 transition，随后测试通过。加入 symbolic probability 和规范化源文件复解析覆盖后，最终测试数为 26。

## 两个指定样例的端到端结果

两个样例均通过真实 CLI 执行了 `.pp -> AST -> semantic/normalize -> grouped pCFG -> validation -> artifacts`，未使用 mock。

### `kelly_simple.pp`

命令：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive cfg kelly_simple.pp --out-dir generated/kelly_simple
```

结果：状态码 `0`，stdout 状态 `ok`。CFG 统计：

- 10 个 locations；
- 12 个 transition groups；
- 13 个 branches；
- 2 个 program variables；
- 0 个连续分布 fresh samples；
- 0 个未消解 probability obligations；
- initial `L_assign_5`，normal terminal `l_t`，failure terminal `l_f`；
- `cfg.json` SHA-256：`ea4fada0f65a39b097056f83f3cd481a5df5e1fb9d96c1b8470616fb1f358446`。

输出目录：`generated/kelly_simple/`。

### `uniform_multiplicative.pp`

命令：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive cfg uniform_multiplicative.pp \
  --out-dir generated/uniform_multiplicative
```

结果：状态码 `0`，stdout 状态 `ok`。CFG 统计：

- 7 个 locations；
- 9 个 transition groups；
- 9 个 branches；
- 2 个 program variables；
- 1 个 `Uniform(0, 2)` fresh sample；
- 0 个未消解 probability obligations；
- initial `L_assign_2`，normal terminal `l_t`，failure terminal `l_f`；
- `cfg.json` SHA-256：`9a844d056ff4c5b6d6fa3f11fceace79cee8160c4b172f9597810921ccc239e1`。

输出目录：`generated/uniform_multiplicative/`。

每个输出目录均实际包含 `source.normalized.pp`、`ast.json`、`cfg.json`、`cfg.txt`、`cfg.dot`、`validation.json` 和 `manifest.json`。

## 阶段 2、阶段 3A、阶段 3B 实现与复核（2026-09-01）

本轮在用户指定的同一 conda 环境 `contractive-frontend-test-20260814` 中安装新增的
`sympy==1.14.0`（传递依赖 `mpmath==1.3.0`），并将 editable package 更新为
`contractive-tool==0.2.0`。未启动 MATLAB、SOSTOOLS 或任何 MATLAB solver。

### 实际安装和测试命令

```bash
cd /ssd/ssd_backup/home/sunzhouyue/Probablistic_project/contractive_function
conda run -n contractive-frontend-test-20260814 \
  python -m pip install -e '.[test]'
conda run -n contractive-frontend-test-20260814 pytest -q
```

最终 pytest stdout：

```text
......................................                                   [100%]
38 passed in 2.30s
```

新增 12 项测试，连同原有 26 项共 38 项：

- algebra/substitution：精确十进制与 simultaneous swap update；
- raw/joint moments：finite discrete、Bernoulli、Uniform、Normal、独立 joint product 和
  显式 correlated provider；
- pre-expectation：替换后/期望前 trace、Uniform 二阶矩消元、branch probability 加权；
- tail obligations：`at_horizon` 的 positivity/contraction/normalization tags、fixed
  horizon objective、所有 decision coefficients 仿射；
- Kelly：从真实 pCFG 自动识别 `0.6:1.2, 0.4:0.8` gains，fixed `lambda=1/2`
  scalar moment 和三轮 bound 均保留精确根式；
- assertion obligations：failure/normal/nonnegative/pre-fixed-point、随机 sample 消元、
  direct Theta、fixed-q factorization，以及 `k=2` 非凸配置拒绝；
- CLI 集成：两个指定 `.pp` 各自生成完整隔离的 analysis artifact tree。

### 两个样例的实际分析命令和结果

Kelly：

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

状态码 `0`，result status `proved`，backend route `exact_scalar_moment`。精确 moment 为：

```text
sqrt(5)/5 + sqrt(30)/10 = 0.9949361530051241...
```

三轮 `Pr[wealth_3 <= 0.6]` certificate bound expression 为：

```text
11*sqrt(3)/50 + 27*sqrt(2)/100 = 0.7628888395058887...
```

这是证书上界，不是事件的精确概率；样例注释给出的精确事件概率为三连败
`0.4^3=0.064`。`scalar_model.json` SHA-256：
`b94a24c6cbfc4d3a2c869391f76c219c290e812d5f9d0c69a9ccccaf58295f31`。

Uniform assertion：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive analyze uniform_multiplicative.pp \
  --out-dir generated/uniform_stage23 \
  --analysis-id uniform_assertion \
  --goal assertion_violation --certificate direct-theta \
  --degree 2 --initial x=1 --initial r=0
```

状态码 `0`，result status `not_solved`，backend route
`affine_polynomial_obligations`。共生成 18 条 obligations：1 条 failure boundary、1 条
normal boundary、7 条 nonnegativity、9 条 transition pre-fixed-point。随机赋值的
pre-expectation trace 显示 `E[r^2]=4/3`；artifact 声明所有 decision-variable
coefficients 仿射。`obligations.json` SHA-256：
`3fb128ef9da244e00fea8680ce900dc5986fd1fa99263bed1c16a3cb4a6aca56`。

### 已单独验证的 fixed factorization

实际额外执行：

```bash
conda run -n contractive-frontend-test-20260814 \
  contractive analyze uniform_multiplicative.pp \
  --out-dir /tmp/contractive-factorized-check \
  --analysis-id uniform_factorized \
  --goal assertion_violation --certificate factorized \
  --degree 1 --factor-q 2 --k 1 --initial x=1 --initial r=0
```

状态码 `0`，18 条 obligations，`decision_coefficients_affine=true`。单元测试同时确认
`k=2` 被 capability boundary 拒绝。

### 限制与结果解释

- `proved` 只用于 Kelly exact scalar moment constraint；普通浮点值仅为显示。
- Polynomial obligation 还没有经过 SOS/Putinar 求解，因此正确状态是 `not_solved`；
  不能把成功生成模型误报为概率 bound 已证明。
- 当前只实现 `at_horizon` tail 和 eventual assertion；`by_horizon`、bounded assertion、
  `k>1` unknown eta、unknown q 与 eta 同时合成均明确 unsupported。
- 本轮没有生成 `.m`，两个 analysis manifest 均记录 `matlab_invoked=false`。

## 结论

最终复核通过：指定 conda 环境可运行全部 38 项测试；阶段 1 的两个 `cfg` CLI 仍兼容，
阶段 2/3 的两个真实 `analyze` CLI 均生成可追溯产物。Kelly scalar model 由 exact
arithmetic 验证，polynomial 模型只报告 obligation generation，不越过尚未实现的
求解边界。README、环境依赖和本记录中的命令与实际执行一致。
