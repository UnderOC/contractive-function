# Contractive：论文尾界分析工具

`main` 保留论文 termination-tail 分支分析的实现、样例、最终实验结果和复核工具。
清理前的完整项目（含 assertion violation、旧 benchmark 和开发记录）保存在
[`develop`](https://github.com/UnderOC/contractive-function/tree/develop)，初始快照为 `9515985b`。
本次整理不改变保存的尾界数值或证书内容。分支范围见 [整理记录](docs/repository_layout.md)。

## 实现与分析范围

工具使用 Python、Lark 和 SymPy 构建源程序的精确符号转移，以 CVXPY/MOSEK 合成候选，
再用有理数恒等式、非负性、精确 PSD 和有理幂向外包围检查证书。默认符号轮级流程包括：

1. 直接多项式收缩势函数（P）。
2. Cauchy 正幂：固定基函数及联合基函数搜索，支持有理指数。
3. Jensen 派生正幂（J），独立标记其来源。
4. 倒数幂（R）：独立分母合成、矩证书、指数搜索及参数反馈。

按每个迭代阈值比较完整的 `min(1, A*q**n)`，而非只比较收缩率。
“最佳”指已找到并通过验证的有限候选集中的最小值，不是全局最优性结论。

主分支只接受 `--goal tailbound`。`assertion_violation` 求解和专属参数已移除；
其代码、测试和历史结果在 `develop`。源语言的 `assert` / `refute` 仍用于定义控制流
和终端；轮级尾界把正常退出和失败退出都视为循环终止，不等同于断言违规概率。
`late_bad_exit` 保留为尾界兼容模式，其事件是晚发生的失败退出，不是论文表格的事件。

## 安装与运行

需要 Python >= 3.10。推荐创建独立环境，并安装求解与测试依赖：

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[solver,test]'
```

数值合成需要有效的 MOSEK 许可。保存证书的复核不运行数值求解器。
版本约束见 [pyproject.toml](pyproject.toml)。

```bash
python -m contractive_tool solve contractive_examples/kelly/K4_periodic_contribution_reciprocal.pp \
  --goal tailbound --initial-degree 2 --max-degree 4 --max-c-steps 12 \
  --total-seconds 180 --reciprocal-seconds 120 --per-attempt-seconds 10 \
  --repair-seconds 5 --comparison-n 10 50 100 \
  --workflow-config examples/tailbound_comparison.json --out-dir generated/local/K4
python -m contractive_tool verify generated/local/K4
python -m contractive_tool evaluate generated/local/K4 --n 100
```

输出目录必须为新建或空目录。`--total-seconds` 和 `--reciprocal-seconds` 是分开的软预算；
符号构造与精确验证可能超过预算。`analyze` / `build-model` 只生成义务和模型。
`parse` / `cfg` 提供前端接口；`solve --help` 列出合成配置。

## 论文样例与结果

- [统一样例索引](contractive_examples/benchmark_index.json)：K1--K6、R1--R6、Q1--Q6、S1--S7，共 25 个。
- [论文结果与复核入口](experiments/paper_tailbounds/README.md)：25 个最终工作流；表格暂不展示 Q6。
- [机器可读结果索引](experiments/paper_tailbounds/manifest.json)：规范源文件、历史运行路径、输入哈希、耗时和配置。
- [保留的原始产物](generated/README.md)：证书、求解日志、失败尝试、配置和计时记录；不用于向新合成注入答案。

```bash
python examples/paper_tailbounds.py report
python examples/paper_tailbounds.py verify --out /tmp/contractive-paper-replay.json
python examples/paper_tailbounds.py ablate
```

结果索引中的运行路径保持原样，避免破坏论文工程的引用。旧运行 ID `kelly_double_bound`
和 `original` 分别映射到 K6 和 S6。S4/S5 使用初始化临时变量后的等价输入；
S7 使用仿射基函数，并非所有样例都采用同一搜索预算。运行时间是已有单次记录，
不能据此作严格的工具速度排名。pRSM/ExpLinSyn 的独立复现仍位于上级项目各自仓库，
本仓库不复制其实现与实验。

## 证明语义与使用限制

- 论文目标 `Pr(T>n)` 的 T 计完整循环迭代；已验证收缩证书同时推导几乎处处终止。
- 支持精确多项式矩、有限离散/Bernoulli/Uniform/Normal 等前端构造，但各合成分支的支持范围不同。
- 源码提供候选不变量；初态和归纳性必须被验证。人工附带证书不作为自动合成结果。
- 不支持的域、采样或嵌套循环会明确返回状态。`no_certificate_found` 不表示数学上不存在证书。
- `verify` 从原输入重建义务；原输入路径不存在时可使用产物中哈希匹配的 `shared/source.pp`。
  已存在但哈希不一致的原输入仍会被拒绝。
- 保留的历史 tailbound 元数据可能含 `assertion_margin` / `assertion_variables`；读取时仅忽略这两个无关字段。

详细说明：
[符号完整流程](docs/symbolic_workflow.md)、[Cauchy](docs/cauchy_search.md)、
[倒数幂](docs/reciprocal_tailbound.md)、[不变量认证](docs/invariant_certification.md)、
[模板变量选择](docs/tail_variable_selection.md)。

## 测试

```bash
python -m pytest -q
```

覆盖解析与 pCFG、精确矩、不变量、正性证书、直接/Cauchy/倒数合成、历史证书复核和入口拒绝行为。
两个 coupon collector 程序只作为 [回归测试输入](tests/fixtures)，不计入论文 benchmark。
